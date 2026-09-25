"""Conectoma embaralhado com graus preservados (controle da Fase 3b; FASE3B_PLANO §F3).

NON-CONNECTOME (controle, não modelo; docs/NON_CONNECTOME.md B-shuf). Trocas duplas de arestas:
(a→b, c→d) ⇒ (a→d, c→b), rejeitando autolaços novos e arestas repetidas. O pré-sináptico de cada aresta
nunca muda, então o grau de saída e a força de saída (com sinal) de cada neurônio ficam iguais; o
pós-sináptico só troca entre arestas, então o grau de entrada também fica igual. O peso e o sinal viajam
com a aresta (o sinal continua o do pré-sináptico, como na regra do Shiu). Trocas bem-sucedidas: 10 × E.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numba import njit

from terrario import ROOT
from terrario.brain.flywire import FlyWireConnectome

CACHE = ROOT / "data" / "cache"
EMPTY, TOMB = np.int64(-1), np.int64(-2)


@njit(cache=True)
def _h(key, bits):
    return np.int64((np.uint64(key) * np.uint64(0x9E3779B97F4A7C15)) >> np.uint64(64 - bits))


@njit(cache=True)
def _find(tab, key, bits):
    m = (1 << bits) - 1
    i = _h(key, bits)
    while True:
        v = tab[i]
        if v == key:
            return i
        if v == -1:
            return -1
        i = (i + 1) & m


@njit(cache=True)
def _insert(tab, key, bits):
    m = (1 << bits) - 1
    i = _h(key, bits)
    while tab[i] != -1 and tab[i] != -2:
        i = (i + 1) & m
    tab[i] = key


@njit(cache=True)
def _swap_kernel(pre, post, n, n_swaps, seed, bits):
    np.random.seed(seed)
    E = len(pre)
    tab = np.full(1 << bits, -1, dtype=np.int64)
    for e in range(E):
        _insert(tab, pre[e] * n + post[e], bits)
    done, att = 0, 0
    while done < n_swaps and att < 20 * n_swaps:
        att += 1
        i = np.random.randint(E)
        j = np.random.randint(E)
        a, b, c, d = pre[i], post[i], pre[j], post[j]
        if i == j or b == d or a == d or c == b:
            continue
        k1, k2 = a * n + d, c * n + b
        if _find(tab, k1, bits) >= 0 or _find(tab, k2, bits) >= 0:
            continue
        tab[_find(tab, a * n + b, bits)] = -2
        tab[_find(tab, c * n + d, bits)] = -2
        _insert(tab, k1, bits)
        _insert(tab, k2, bits)
        post[i], post[j] = d, b
        done += 1
    return done, att


def shuffled(conn: FlyWireConnectome, seed: int, swaps_per_edge: int = 10) -> FlyWireConnectome:
    path = CACHE / f"shuffle_{conn.version}_s{seed}_x{swaps_per_edge}.npz"
    pre = np.repeat(np.arange(conn.n, dtype=np.int64), np.diff(conn.indptr))
    if path.exists():
        post = np.load(path)["post"]
    else:
        post = conn.indices.astype(np.int64).copy()
        E = len(pre)
        bits = int(np.ceil(np.log2(E))) + 2
        done, att = _swap_kernel(pre, post, np.int64(conn.n), np.int64(swaps_per_edge * E), seed, bits)
        if done < swaps_per_edge * E:
            raise RuntimeError(f"só {done} trocas em {att} tentativas")
        # verificações: grau de entrada igual, sem arestas repetidas, sem autolaços novos
        n0 = np.bincount(conn.indices, minlength=conn.n)
        n1 = np.bincount(post, minlength=conn.n)
        assert np.array_equal(n0, n1), "grau de entrada mudou"
        assert len(np.unique(pre * conn.n + post)) == E, "aresta repetida"
        assert (pre == post).sum() <= (pre == conn.indices).sum(), "autolaço novo"
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, post=post)
    return FlyWireConnectome(version=f"{conn.version}-shuf{seed}", flyids=conn.flyids, indptr=conn.indptr,
                             indices=post.astype(conn.indices.dtype), syn_count=conn.syn_count)
