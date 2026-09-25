"""Protótipos de motor LIF para o BENCHMARK da Fase 0 (não é o motor final).

Reproduzem a semântica do modelo de Shiu et al. 2024 como implementado em
third_party/Drosophila_brain_model/model.py (default_params, create_model, poi):

  dv/dt = (v_0 - v + g) / t_mbr   (unless refractory)
  dg/dt = -g / tau                 (unless refractory)
  limiar v > v_th; reset v = v_rst, g = 0; refratário t_rfc = 2.2 ms
  sinapse: on_pre 'g += w', atraso t_dly = 1.8 ms, w = (Excitatory x Connectivity) * w_syn
  PoissonInput(target_var='v', N=1, rate=r_poi, weight=w_syn*f_poi); rfc = 0 nos alvos

Ordem de atualização por passo, seguindo o escalonamento padrão do Brian2
(start, groups, thresholds, synapses, resets, end):
  1. groups:     integração exata (método 'linear') dos neurônios fora do refratário
  2. thresholds: spike se v > v_th e não refratário
  3. synapses:   entrega dos spikes emitidos há D = t_dly/dt passos (g += w) e
                 entradas de Poisson (v += w_poi)
  4. resets:     v = v_rst, g = 0 nos neurônios que dispararam neste passo

Escrita condicional (Brian2, groups/neurongroup.py: set_conditional_write): com
"unless refractory", TODA escrita em v e g, inclusive on_pre das sinapses e PoissonInput,
só acontece se not_refractory. Entradas durante o refratário são DESCARTADAS
(verificado empiricamente). O reset não é afetado.

Refratariedade (Brian2): o neurônio fica congelado enquanto
timestep(t - lastspike) < timestep(t_rfc), ou seja, por 22 passos, incluindo o do spike.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.sparse as sp

# Parâmetros copiados de model.py:default_params (Shiu et al.), em ms / mV / Hz
PARAMS = dict(
    v_0=-52.0, v_rst=-52.0, v_th=-45.0, t_mbr=20.0, tau=5.0,
    t_rfc=2.2, t_dly=1.8, w_syn=0.275, r_poi=150.0, f_poi=250.0,
)


@dataclass
class Connectome:
    n: int
    W: sp.csr_matrix  # linhas = pré, colunas = pós, valores em mV
    flyid2i: dict


def load_connectome(path_comp: str, path_con: str, w_syn: float = PARAMS["w_syn"]) -> Connectome:
    # Mesmo carregamento de model.py:create_model
    df_comp = pd.read_csv(path_comp, index_col=0)
    df_con = pd.read_parquet(path_con)
    n = len(df_comp)
    pre = df_con["Presynaptic_Index"].to_numpy()
    post = df_con["Postsynaptic_Index"].to_numpy()
    w = df_con["Excitatory x Connectivity"].to_numpy(dtype=np.float64) * w_syn
    W = sp.csr_matrix((w, (pre, post)), shape=(n, n))
    W.sum_duplicates()
    flyid2i = {j: i for i, j in enumerate(df_comp.index)}
    return Connectome(n, W, flyid2i)


def _coeffs(dt, p):
    a = math.exp(-dt / p["t_mbr"])
    b = math.exp(-dt / p["tau"])
    # solução exata do sistema linear: coeficiente de g(t) em v(t+dt)
    c = p["tau"] / (p["tau"] - p["t_mbr"]) * (b - a)
    return a, b, c


# ---------------------------------------------------------------- numba
_DENSE = {}


def _dense_kernel(parallel):
    import numba as nb
    if parallel in _DENSE:
        return _DENSE[parallel]

    @nb.njit(parallel=parallel, cache=True)
    def _kern(nsteps, step0, v, g, last, gbuf, rfc_steps, exc, u, out_i, out_t, indptr, indices, data,
          a, b, c, v0, vr, vth, p_poi, w_poi, D):
        nout = 0
        cap = out_i.shape[0]
        nn = v.shape[0]
        spk = np.empty(nn, dtype=np.int32)
        for k in range(nsteps):
            s = step0 + k
            # 1. groups
            for i in nb.prange(nn):
                if s - last[i] >= rfc_steps[i]:
                    vi = v[i]
                    gi = g[i]
                    v[i] = v0 + (vi - v0) * a + gi * c
                    g[i] = gi * b
            # 2. thresholds
            m = 0
            for i in range(nn):
                if v[i] > vth and s - last[i] >= rfc_steps[i]:
                    spk[m] = i
                    m += 1
                    last[i] = s
            # 3a. synapses: entrega de g acumulado para este passo
            slot = s % D
            row = gbuf[slot]
            for i in nb.prange(nn):
                if row[i] != 0.0:
                    # Brian2: 'unless refractory' torna condicional TODA escrita em g
                    # (inclusive on_pre); entrada durante o refratário é descartada
                    if s - last[i] >= rfc_steps[i] and last[i] != s:
                        g[i] += row[i]
                    row[i] = 0.0
            # novos spikes -> chegam em s + D (mesmo slot, já esvaziado)
            for q in range(m):
                i = spk[q]
                for jj in range(indptr[i], indptr[i + 1]):
                    row[indices[jj]] += data[jj]
                if nout < cap:
                    out_i[nout] = i
                    out_t[nout] = s
                nout += 1
            # 3b. Poisson (v += w_poi com prob. r*dt)
            for e in range(exc.shape[0]):
                if u[k, e] < p_poi:
                    j = exc[e]
                    if s - last[j] >= rfc_steps[j] and last[j] != s:
                        v[j] += w_poi
            # 4. resets
            for q in range(m):
                i = spk[q]
                v[i] = vr
                g[i] = 0.0
        return nout

    _DENSE[parallel] = _kern
    return _kern


def make_numba_engine(conn: Connectome, exc_idx, dt=0.1, p=PARAMS, seed=0, dtype=np.float64,
                      parallel=False):
    import numba as nb

    a, b, c = _coeffs(dt, p)
    D = int(round(p["t_dly"] / dt))
    R = int(round(p["t_rfc"] / dt))
    n = conn.n
    indptr = conn.W.indptr.astype(np.int64)
    indices = conn.W.indices.astype(np.int32)
    data = conn.W.data.astype(dtype)
    exc = np.asarray(exc_idx, dtype=np.int64)
    rfc_steps = np.full(n, R, dtype=np.int32)
    rfc_steps[exc] = 0
    p_poi = p["r_poi"] * dt * 1e-3
    w_poi = p["w_syn"] * p["f_poi"]
    v0, vr, vth = p["v_0"], p["v_rst"], p["v_th"]

    # buffer em anel com o g acumulado a entregar em cada passo futuro (atraso D)
    _run2 = _dense_kernel(parallel)

    class Engine:
        name = f"numba{'-par' if parallel else ''}-{np.dtype(dtype).name}"

        def __init__(self):
            self.rng = np.random.default_rng(seed)
            self.v = np.full(n, v0, dtype=dtype)
            self.g = np.zeros(n, dtype=dtype)
            self.last = np.full(n, -10**9, dtype=np.int64)
            self.gbuf = np.zeros((D, n), dtype=dtype)
            self.step = 0

        def run(self, nsteps, cap=5_000_000):
            u = self.rng.random((nsteps, len(exc)))
            out_i = np.empty(cap, np.int32)
            out_t = np.empty(cap, np.int64)
            nout = _run2(nsteps, self.step, self.v, self.g, self.last, self.gbuf,
                         rfc_steps, exc, u, out_i, out_t, indptr, indices, data,
                         a, b, c, v0, vr, vth, p_poi, w_poi, D)
            self.step += nsteps
            k = min(nout, cap)
            return out_i[:k], out_t[:k] * dt  # ms

    return Engine()


# ---------------------------------------------------------------- numpy/scipy
def make_numpy_engine(conn: Connectome, exc_idx, dt=0.1, p=PARAMS, seed=0, dtype=np.float64):
    a, b, c = _coeffs(dt, p)
    D = int(round(p["t_dly"] / dt))
    R = int(round(p["t_rfc"] / dt))
    n = conn.n
    W = conn.W.astype(dtype)
    exc = np.asarray(exc_idx, dtype=np.int64)
    rfc_steps = np.full(n, R, dtype=np.int64)
    rfc_steps[exc] = 0
    p_poi = p["r_poi"] * dt * 1e-3
    w_poi = p["w_syn"] * p["f_poi"]

    class Engine:
        name = f"numpy-scipy-{np.dtype(dtype).name}"

        def __init__(self):
            self.rng = np.random.default_rng(seed)
            self.v = np.full(n, p["v_0"], dtype=dtype)
            self.g = np.zeros(n, dtype=dtype)
            self.last = np.full(n, -10**9, dtype=np.int64)
            self.gbuf = np.zeros((D, n), dtype=dtype)
            self.step = 0

        def run(self, nsteps):
            v, g, last, gbuf = self.v, self.g, self.last, self.gbuf
            ids, ts = [], []
            for k in range(nsteps):
                s = self.step + k
                act = (s - last) >= rfc_steps
                vn = p["v_0"] + (v - p["v_0"]) * a + g * c
                np.copyto(v, vn, where=act)
                np.multiply(g, b, out=g, where=act)
                spk = np.flatnonzero((v > p["v_th"]) & act)
                last[spk] = s
                slot = s % D
                # escrita condicional (Brian2 'unless refractory'): inclui quem disparou agora
                wr = ((s - last) >= rfc_steps) & (last != s)
                g += np.where(wr, gbuf[slot], 0)
                gbuf[slot] = 0
                if spk.size:
                    gbuf[slot] += np.asarray(W[spk].sum(axis=0)).ravel()
                    ids.append(spk)
                    ts.append(np.full(spk.size, s))
                hit = exc[self.rng.random(exc.size) < p_poi]
                v[hit[wr[hit]]] += w_poi
                v[spk] = p["v_rst"]
                g[spk] = 0
            self.step += nsteps
            if ids:
                return np.concatenate(ids), np.concatenate(ts) * dt
            return np.empty(0, int), np.empty(0)

    return Engine()


# ---------------------------------------------------------------- torch
def make_torch_engine(conn: Connectome, exc_idx, dt=0.1, p=PARAMS, seed=0, dtype="float64",
                      threads=None):
    import torch

    if threads:
        torch.set_num_threads(threads)
    tdt = getattr(torch, dtype)
    a, b, c = _coeffs(dt, p)
    D = int(round(p["t_dly"] / dt))
    R = int(round(p["t_rfc"] / dt))
    n = conn.n
    indptr = torch.from_numpy(conn.W.indptr.astype(np.int64))
    indices = torch.from_numpy(conn.W.indices.astype(np.int64))
    data = torch.from_numpy(conn.W.data).to(tdt)
    exc = torch.from_numpy(np.asarray(exc_idx, dtype=np.int64))
    rfc_steps = torch.full((n,), R, dtype=torch.int64)
    rfc_steps[exc] = 0
    p_poi = p["r_poi"] * dt * 1e-3
    w_poi = p["w_syn"] * p["f_poi"]

    class Engine:
        name = f"torch-{dtype}-t{torch.get_num_threads()}"

        def __init__(self):
            self.gen = torch.Generator().manual_seed(seed)
            self.v = torch.full((n,), p["v_0"], dtype=tdt)
            self.g = torch.zeros(n, dtype=tdt)
            self.last = torch.full((n,), -10**9, dtype=torch.int64)
            self.gbuf = torch.zeros((D, n), dtype=tdt)
            self.step = 0

        @torch.no_grad()
        def run(self, nsteps):
            v, g, last, gbuf = self.v, self.g, self.last, self.gbuf
            ids, ts = [], []
            for k in range(nsteps):
                s = self.step + k
                act = (s - last) >= rfc_steps
                vn = p["v_0"] + (v - p["v_0"]) * a + g * c
                v = torch.where(act, vn, v)
                g = torch.where(act, g * b, g)
                spk = torch.nonzero((v > p["v_th"]) & act).flatten()
                slot = s % D
                if spk.numel():
                    last[spk] = s
                wr = ((s - last) >= rfc_steps) & (last != s)
                g += torch.where(wr, gbuf[slot], 0)
                gbuf[slot].zero_()
                if spk.numel():
                    st, en = indptr[spk], indptr[spk + 1]
                    cnt = en - st
                    base = torch.repeat_interleave(st - torch.cumsum(cnt, 0) + cnt, cnt)
                    pos = torch.arange(int(cnt.sum())) + base
                    gbuf[slot].index_add_(0, indices[pos], data[pos])
                    ids.append(spk.clone())
                    ts.append(torch.full((spk.numel(),), s))
                hit = exc[torch.rand(exc.numel(), generator=self.gen) < p_poi]
                v[hit[wr[hit]]] += w_poi
                v[spk] = p["v_rst"]
                g[spk] = 0
            self.v, self.g = v, g
            self.step += nsteps
            if ids:
                return torch.cat(ids).numpy(), torch.cat(ts).numpy() * dt
            return np.empty(0, int), np.empty(0)

    return Engine()


# ---------------------------------------------------------------- numba, conjunto ativo
def make_numba_active_engine(conn: Connectome, exc_idx, dt=0.1, p=PARAMS, seed=0,
                             dtype=np.float64):
    """Mesma semântica de make_numba_engine, mas só integra neurônios fora do repouso.

    Exato (bit a bit): com v_rst == v_0 e sem corrente de fundo, um neurônio com
    v == v_0 e g == 0 continua exatamente assim até receber entrada, pois
    v_0 + 0*a + 0*c == v_0 e 0*b == 0. Pular esses neurônios não altera nada.
    """
    import numba as nb

    assert p["v_rst"] == p["v_0"]
    a, b, c = _coeffs(dt, p)
    D = int(round(p["t_dly"] / dt))
    R = int(round(p["t_rfc"] / dt))
    n = conn.n
    indptr = conn.W.indptr.astype(np.int64)
    indices = conn.W.indices.astype(np.int32)
    data = conn.W.data.astype(dtype)
    exc = np.asarray(exc_idx, dtype=np.int64)
    rfc_steps = np.full(n, R, dtype=np.int32)
    rfc_steps[exc] = 0
    p_poi = p["r_poi"] * dt * 1e-3
    w_poi = p["w_syn"] * p["f_poi"]
    v0, vth = p["v_0"], p["v_th"]
    maxdeg = int(np.diff(indptr).max())

    class Engine:
        name = f"numba-active-{np.dtype(dtype).name}"

        def __init__(self, tcap=4_000_000):
            self.rng = np.random.default_rng(seed)
            self.v = np.full(n, v0, dtype=dtype)
            self.g = np.zeros(n, dtype=dtype)
            self.last = np.full(n, -10**9, dtype=np.int64)
            self.gbuf = np.zeros((D, n), dtype=dtype)
            self.tlist = np.zeros((D, tcap), dtype=np.int32)
            self.tlen = np.zeros(D, dtype=np.int64)
            self.act = np.zeros(n, dtype=np.int32)
            self.flag = np.zeros(n, dtype=np.uint8)
            self.nact = np.zeros(1, dtype=np.int64)
            self.step = 0

        @property
        def n_active(self):
            return int(self.nact[0])

        def run(self, nsteps, cap=5_000_000):
            u = self.rng.random((nsteps, len(exc)))
            out_i = np.empty(cap, np.int32)
            out_t = np.empty(cap, np.int64)
            nout = _active_kernel(nsteps, self.step, self.v, self.g, self.last, self.gbuf,
                                  self.tlist, self.tlen, self.act, self.flag, self.nact,
                                  rfc_steps, exc, u, out_i, out_t, indptr, indices, data,
                                  a, b, c, v0, vth, p_poi, w_poi, D)
            self.step += nsteps
            k = min(nout, cap)
            return out_i[:k], out_t[:k] * dt

    return Engine()


import numba as _nb  # noqa: E402


@_nb.njit(cache=True)
def _active_kernel(nsteps, step0, v, g, last, gbuf, tlist, tlen, act, flag, nact_arr,
                   rfc_steps, exc, u, out_i, out_t, indptr, indices, data,
                   a, b, c, v0, vth, p_poi, w_poi, D):
    nout = 0
    cap = out_i.shape[0]
    nact = nact_arr[0]
    spk = np.empty(v.shape[0], dtype=np.int32)
    for k in range(nsteps):
        s = step0 + k
        # 1+2. integra e testa limiar só nos ativos
        m = 0
        for q in range(nact):
            i = act[q]
            if s - last[i] >= rfc_steps[i]:
                vi = v[i]
                gi = g[i]
                v[i] = v0 + (vi - v0) * a + gi * c
                g[i] = gi * b
                if v[i] > vth:
                    spk[m] = i
                    m += 1
                    last[i] = s
        # 3a. entrega do slot (só índices tocados)
        slot = s % D
        row = gbuf[slot]
        for q in range(tlen[slot]):
            j = tlist[slot, q]
            if row[j] != 0.0:
                wrj = s - last[j] >= rfc_steps[j] and last[j] != s
                if wrj:  # Brian2: entrada durante o refratário é descartada
                    g[j] += row[j]
                row[j] = 0.0
                if wrj and flag[j] == 0:
                    flag[j] = 1
                    act[nact] = j
                    nact += 1
        tlen[slot] = 0
        for q in range(m):
            i = spk[q]
            for jj in range(indptr[i], indptr[i + 1]):
                j = indices[jj]
                row[j] += data[jj]
                tlist[slot, tlen[slot]] = j
                tlen[slot] += 1
            if nout < cap:
                out_i[nout] = i
                out_t[nout] = s
            nout += 1
        # 3b. Poisson
        for e in range(exc.shape[0]):
            if u[k, e] < p_poi:
                j = exc[e]
                if not (s - last[j] >= rfc_steps[j] and last[j] != s):
                    continue
                v[j] += w_poi
                if flag[j] == 0:
                    flag[j] = 1
                    act[nact] = j
                    nact += 1
        # 4. reset (v_rst == v_0)
        for q in range(m):
            i = spk[q]
            v[i] = v0
            g[i] = 0.0
        # compacta: remove quem voltou exatamente ao repouso
        w = 0
        for q in range(nact):
            i = act[q]
            if v[i] != v0 or g[i] != 0.0:
                act[w] = i
                w += 1
            else:
                flag[i] = 0
        nact = w
    nact_arr[0] = nact
    return nout

