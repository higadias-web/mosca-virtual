"""Motor LIF do modelo de Shiu et al. 2024, com integração só do conjunto ativo.

Reproduz a semântica de third_party/Drosophila_brain_model/model.py (Brian2):

  dv/dt = (v_0 - v + g) / t_mbr   (unless refractory)
  dg/dt = -g / tau                 (unless refractory)
  limiar v > v_th; reset v = v_rst, g = 0; refratário t_rfc
  sinapse on_pre 'g += w' com atraso t_dly, w = (Excitatory x Connectivity) * w_syn
  PoissonInput(target_var='v', N=1, rate, weight=w_syn*f_poi); rfc = 0 nos alvos (model.py:poi)
  silêncio: pesos de SAÍDA do neurônio = 0 (model.py:silence)

Ordem por passo = escalonamento padrão do Brian2 (groups, thresholds, synapses, resets).

Escrita condicional (brian2/groups/neurongroup.py, set_conditional_write): com
"(unless refractory)", as escritas em v e g feitas por on_pre e PoissonInput só acontecem se
o neurônio não está refratário. Entradas durante o refratário, inclusive no passo do próprio
spike, são DESCARTADAS. Isso foi verificado empiricamente (tests/test_lif.py).

Conjunto ativo: como v_rst == v_0 e não há corrente de fundo, um neurônio com v == v_0 e
g == 0 continua exatamente assim até receber entrada. Integrar só os demais é exato,
bit a bit (tests/test_lif.py::test_active_equals_dense).
"""

from __future__ import annotations

import math

import numba as nb
import numpy as np

from terrario.brain.flywire import FlyWireConnectome

# model.py:default_params (Shiu et al.), em ms, mV, Hz. As fontes estão no próprio model.py:
# Kakaria & de Bivort 2017 (v_0, v_rst, v_th, t_mbr); Jürgensen et al. (tau);
# Lazar et al. (t_rfc); Paul et al. 2015 (t_dly); w_syn é parâmetro livre; f_poi = 250.
SHIU_PARAMS = dict(
    v_0=-52.0, v_rst=-52.0, v_th=-45.0, t_mbr=20.0, tau=5.0,
    t_rfc=2.2, t_dly=1.8, w_syn=0.275, f_poi=250.0,
)
DT_MS = 0.1  # dt padrão do Brian2, usado pelo Shiu


@nb.njit(cache=True)
def _can_write(s, last_i, rfc_i):
    # not_refractory do Brian2, já atualizado pelo limiar deste passo
    return s - last_i >= rfc_i and last_i != s


@nb.njit(cache=True)
def _step_kernel(nsteps, step0, v, g, last, gbuf, tlist, tlen, act, flag, nact_arr,
                 rfc_steps, tgt, p_tgt, u, out_i, out_t, indptr, indices, w,
                 a, b, c, v0, vth, w_poi, D, dense, tcap):
    nout = 0
    cap = out_i.shape[0]
    nn = v.shape[0]
    nact = nact_arr[0]
    spk = np.empty(nn, dtype=np.int32)
    for k in range(nsteps):
        s = step0 + k
        # 1+2. groups + thresholds (só nos ativos; 'dense' força todos, para teste)
        m = 0
        nloop = nn if dense else nact
        for q in range(nloop):
            i = q if dense else act[q]
            if s - last[i] >= rfc_steps[i]:
                vi = v[i]
                gi = g[i]
                v[i] = v0 + (vi - v0) * a + gi * c
                g[i] = gi * b
                if v[i] > vth:
                    spk[m] = i
                    m += 1
                    last[i] = s
        # 3a. synapses: entrega do anel (spikes de s - D)
        slot = s % D
        row = gbuf[slot]
        # tlen == -1: a lista de índices estourou; varre a linha inteira (exato, mais lento)
        ntouch = nn if tlen[slot] < 0 else tlen[slot]
        for q in range(ntouch):
            j = q if tlen[slot] < 0 else tlist[slot, q]
            if row[j] != 0.0:
                ok = _can_write(s, last[j], rfc_steps[j])
                if ok:
                    g[j] += row[j]
                row[j] = 0.0
                if ok and flag[j] == 0:
                    flag[j] = 1
                    act[nact] = j
                    nact += 1
        tlen[slot] = 0
        for q in range(m):
            i = spk[q]
            for jj in range(indptr[i], indptr[i + 1]):
                j = indices[jj]
                row[j] += w[jj]
                if tlen[slot] >= 0:
                    if tlen[slot] < tcap:
                        tlist[slot, tlen[slot]] = j
                        tlen[slot] += 1
                    else:
                        tlen[slot] = -1
            if nout < cap:
                out_i[nout] = i
                out_t[nout] = s
            nout += 1
        # 3b. PoissonInput (N=1 => Bernoulli com p = rate * dt)
        for e in range(tgt.shape[0]):
            if u[k, e] < p_tgt[e]:
                j = tgt[e]
                if _can_write(s, last[j], rfc_steps[j]):
                    v[j] += w_poi
                    if flag[j] == 0:
                        flag[j] = 1
                        act[nact] = j
                        nact += 1
        # 4. resets (v_rst == v_0)
        for q in range(m):
            i = spk[q]
            v[i] = v0
            g[i] = 0.0
        # compacta o conjunto ativo
        wq = 0
        for q in range(nact):
            i = act[q]
            if v[i] != v0 or g[i] != 0.0:
                act[wq] = i
                wq += 1
            else:
                flag[i] = 0
        nact = wq
    nact_arr[0] = nact
    return nout


class ShiuLIF:
    """Cérebro inteiro da mosca (Shiu et al. 2024) com passo de 0,1 ms.

    Uso típico (co-simulação): chamar `run(10)` a cada 1 ms de física (D-006).
    """

    def __init__(self, conn: FlyWireConnectome, params: dict | None = None,
                 dt: float = DT_MS, seed: int = 0, dense: bool = False):
        p = dict(SHIU_PARAMS, **(params or {}))
        if p["v_rst"] != p["v_0"]:
            raise ValueError("o conjunto ativo exige v_rst == v_0 (vale para o modelo de Shiu)")
        self.p, self.dt, self.conn, self.dense = p, dt, conn, dense
        self.a = math.exp(-dt / p["t_mbr"])
        self.b = math.exp(-dt / p["tau"])
        # solução exata (método 'linear' do Brian2): coeficiente de g(t) em v(t+dt)
        self.c = p["tau"] / (p["tau"] - p["t_mbr"]) * (self.b - self.a)
        self.D = int(round(p["t_dly"] / dt))
        self.R = int(round(p["t_rfc"] / dt))
        self.w_poi = p["w_syn"] * p["f_poi"]
        n = conn.n
        self.w = conn.syn_count * p["w_syn"]
        self.rfc_steps = np.full(n, self.R, dtype=np.int32)
        self.tgt = np.empty(0, dtype=np.int64)     # alvos de Poisson (rfc = 0)
        self.rate_hz = np.empty(0, dtype=np.float64)
        self.silenced = np.empty(0, dtype=np.int64)
        self.rng = np.random.default_rng(seed)
        self.v = np.full(n, p["v_0"])
        self.g = np.zeros(n)
        self.last = np.full(n, -(10**9), dtype=np.int64)
        self.gbuf = np.zeros((self.D, n))
        maxdeg = int(np.diff(conn.indptr).max())
        self._tcap = max(maxdeg * 64, 1 << 20)
        self.tlist = np.zeros((self.D, self._tcap), dtype=np.int32)
        self.tlen = np.zeros(self.D, dtype=np.int64)
        self.act = np.zeros(n, dtype=np.int32)
        self.flag = np.zeros(n, dtype=np.uint8)
        self.nact = np.zeros(1, dtype=np.int64)
        self.step = 0

    # ------------------------------------------------------------------ entradas
    def set_poisson(self, idx, rate_hz) -> None:
        """Define entrada de Poisson (model.py:poi) nos neurônios `idx`.

        Como no original, todo alvo de Poisson tem refratário 0, mesmo com taxa 0.
        Chamar de novo atualiza a taxa (útil para o acoplamento sensorial).
        """
        idx = np.atleast_1d(np.asarray(idx, dtype=np.int64))
        rate = np.broadcast_to(np.asarray(rate_hz, dtype=np.float64), idx.shape)
        pos = {int(t): k for k, t in enumerate(self.tgt)}
        new_i, new_r = [], []
        for i, r in zip(idx, rate):
            if int(i) in pos:
                self.rate_hz[pos[int(i)]] = r
            else:
                new_i.append(i)
                new_r.append(r)
        if new_i:
            self.tgt = np.concatenate([self.tgt, np.array(new_i, dtype=np.int64)])
            self.rate_hz = np.concatenate([self.rate_hz, np.array(new_r)])
        self.rfc_steps[self.tgt] = 0

    def silence(self, idx) -> None:
        """model.py:silence: zera todas as sinapses de SAÍDA dos neurônios `idx`."""
        idx = np.atleast_1d(np.asarray(idx, dtype=np.int64))
        for i in idx:
            self.w[self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0
        self.silenced = np.union1d(self.silenced, idx)

    # ------------------------------------------------------------------ execução
    @property
    def n_active(self) -> int:
        return int(self.nact[0])

    @property
    def t_ms(self) -> float:
        return self.step * self.dt

    def run(self, nsteps: int, cap: int = 1 << 22):
        """Avança `nsteps` passos. Retorna (índices dos neurônios, passo de cada spike)."""
        p_tgt = self.rate_hz * self.dt * 1e-3
        u = self.rng.random((nsteps, len(self.tgt)))
        out_i = np.empty(cap, np.int32)
        out_t = np.empty(cap, np.int64)
        nout = _step_kernel(nsteps, self.step, self.v, self.g, self.last, self.gbuf, self.tlist,
                            self.tlen, self.act, self.flag, self.nact, self.rfc_steps,
                            self.tgt, p_tgt, u, out_i, out_t, self.conn.indptr,
                            self.conn.indices, self.w, self.a, self.b, self.c, self.p["v_0"],
                            self.p["v_th"], self.w_poi, self.D, self.dense, self._tcap)
        if nout > cap:
            raise RuntimeError(f"mais de {cap} spikes em {nsteps} passos; aumente `cap`")
        self.step += nsteps
        return out_i[:nout].copy(), out_t[:nout].copy()

    # ------------------------------------------------------------------ checkpoint
    _STATE = ("v", "g", "last", "gbuf", "tlist", "tlen", "act", "flag", "nact", "w",
              "rfc_steps", "tgt", "rate_hz", "silenced")

    def get_state(self) -> dict:
        st = {k: np.array(getattr(self, k), copy=True) for k in self._STATE}
        st["step"] = self.step
        st["rng"] = self.rng.bit_generator.state
        return st

    def set_state(self, st: dict) -> None:
        for k in self._STATE:
            setattr(self, k, np.array(st[k], copy=True))
        self.step = int(st["step"])
        self.rng.bit_generator.state = st["rng"]
