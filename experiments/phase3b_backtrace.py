"""Fase 3b, S1: de onde vem a ativação do DNa02 esquerdo pelo odor? (FASE3B_PLANO §K; pré-registrado)

Sem corpo. FlyWire 783, LIF do Shiu, odor bilateral (ORNs de DM1+VA2, 100 Hz), 5 sementes (1000–1004), 1 s.
Etapas (cada uma exige a anterior completa):
  odor      roda e salva os spikes de TODOS os neurônios (runs/phase3b/backtrace/odor_s*.npz)
  tree      taxa média r_j (5 sementes); contribuição de j para k = W(j→k) · r_j (W = contagem com sinal);
            a partir do DNa02 esquerdo, os 3 pré-sinápticos de maior contribuição POSITIVA, e recua assim até
            3 níveis (≤ 3 + 9 + 27 nós). Também lista os 3 maiores inibitórios de cada nó (só descritivo)
  silence   silencia (sinapses de saída zeradas, como model.py:silence do Shiu) os 1, 2 e 3 principais do
            nível 1, cumulativo (top1; top1+2; top1+2+3), mesmo odor e mesmas sementes
  evaluate  queda do DNa02 esquerdo contra o intacto (mesma semente). Critério: QUEDA se a mediana da queda
            relativa for ≥ 50 % E houver queda ≥ 50 % em ≥ 4 de 5 sementes
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
RUNS = ROOT / "runs/phase3b/backtrace"
OUT = ROOT / "results/phase3b"
SEEDS, RATE_HZ, T_MS = list(range(1000, 1005)), 100.0, 1000
K, LEVELS = 3, 3
DROP, MIN_SEEDS = 0.5, 4
WATCH = [("DNa02", "left"), ("DNa02", "right"), ("DNa01", "left"), ("DNa01", "right")]
_S = {}


def _ann():
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side", "super_class", "top_nt"])
    a["root_id"] = a.root_id.astype("int64")
    return a


def _init():
    from terrario.brain import connectomes
    c = connectomes.load("783")
    a = _ann()
    _S["c"] = c
    _S["orn"] = c.idx(a[a.cell_type.isin(["ORN_DM1", "ORN_VA2"])].root_id)
    _S["watch"] = {f"{t}_{s}": int(c.idx(a[(a.cell_type == t) & (a.side == s)].root_id)[0]) for t, s in WATCH}


def _run(job):
    from terrario.brain.lif import ShiuLIF
    tag, seed, sil = job
    m = ShiuLIF(_S["c"], seed=seed)
    if sil:
        m.silence(np.array(sil, dtype=np.int64))
    m.set_poisson(_S["orn"], RATE_HZ)
    i, t = m.run(int(T_MS / m.dt))
    np.savez_compressed(RUNS / f"{tag}_s{seed}.npz", i=i.astype(np.int32), t=t)
    return tag, seed


def odor():
    RUNS.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(5, initializer=_init) as ex:
        list(ex.map(_run, [("odor", s, []) for s in SEEDS]))
    (RUNS / "ODOR_OK").write_text(f"{len(list(RUNS.glob('odor_s*.npz')))}/{len(SEEDS)}\n")


def tree():
    if (RUNS / "ODOR_OK").read_text().strip() != f"{len(SEEDS)}/{len(SEEDS)}":
        raise SystemExit("odor incompleto")
    _init()
    c, a = _S["c"], _ann().set_index("root_id")
    rate = np.zeros(c.n)
    for s in SEEDS:
        rate += np.bincount(np.load(RUNS / f"odor_s{s}.npz")["i"], minlength=c.n)
    rate /= len(SEEDS) * T_MS / 1000
    Wt = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n)).T.tocsr()  # linhas = pós

    def info(j):
        fid = int(c.flyids[j])
        r = a.loc[fid] if fid in a.index else None
        return dict(idx=int(j), root_id=fid, cell_type=None if r is None else str(r.cell_type),
                    side=None if r is None else str(r.side), super_class=None if r is None else str(r.super_class),
                    top_nt=None if r is None else str(r.top_nt), rate=float(rate[j]))

    def pres(k):
        row = Wt.getrow(k)
        contrib = row.data * rate[row.indices]
        exc = [(int(j), float(w), float(x)) for j, w, x in zip(row.indices, row.data, contrib) if x > 0]
        inh = [(int(j), float(w), float(x)) for j, w, x in zip(row.indices, row.data, contrib) if x < 0]
        exc.sort(key=lambda z: -z[2]); inh.sort(key=lambda z: z[2])
        return exc[:K], inh[:K]

    root = _S["watch"]["DNa02_left"]

    def node(k, level):
        exc, inh = pres(k)
        d = info(k)
        d["top_inhibitory"] = [dict(info(j), weight=w, contribution=x) for j, w, x in inh]
        d["inputs"] = [dict(node(j, level + 1) if level < LEVELS else info(j), weight=w, contribution=x)
                       for j, w, x in exc]
        return d

    t = node(root, 1)
    json.dump(t, open(OUT / "backtrace_tree.json", "w"), indent=1, ensure_ascii=False)
    lvl1 = [n["idx"] for n in t["inputs"]]
    json.dump(dict(level1=lvl1), open(RUNS / "tree_OK.json", "w"))
    print(json.dumps(t, indent=1, ensure_ascii=False)[:6000])


def silence():
    lvl1 = json.load(open(RUNS / "tree_OK.json"))["level1"]
    jobs = [(f"sil{n}", s, lvl1[:n]) for n in range(1, len(lvl1) + 1) for s in SEEDS]
    with ProcessPoolExecutor(5, initializer=_init) as ex:
        list(ex.map(_run, jobs))
    n = len(list(RUNS.glob("sil*_s*.npz")))
    (RUNS / "SIL_OK").write_text(f"{n}/{len(jobs)}\n")


def evaluate():
    lvl1 = json.load(open(RUNS / "tree_OK.json"))["level1"]
    exp = len(lvl1) * len(SEEDS)
    if (RUNS / "SIL_OK").read_text().strip() != f"{exp}/{exp}":
        raise SystemExit("silenciamento incompleto")
    _init()
    w = _S["watch"]

    def rates(tag, s):
        i = np.load(RUNS / f"{tag}_s{s}.npz")["i"]
        return {k: float((i == v).sum() / (T_MS / 1000)) for k, v in w.items()} | {"total_spikes": int(len(i))}

    base = {s: rates("odor", s) for s in SEEDS}
    res = dict(level1=lvl1, intact={s: base[s] for s in SEEDS}, conditions={})
    for n in range(1, len(lvl1) + 1):
        per = {s: rates(f"sil{n}", s) for s in SEEDS}
        rel = [1 - per[s]["DNa02_left"] / base[s]["DNa02_left"] if base[s]["DNa02_left"] > 0 else np.nan for s in SEEDS]
        med = float(np.nanmedian(rel))
        nseeds = int(np.sum(np.array(rel) >= DROP))
        res["conditions"][f"top1..{n}"] = dict(silenced=lvl1[:n], per_seed=per, rel_drop=rel, rel_drop_median=med,
                                               n_seeds_drop50=nseeds, QUEDA=bool(med >= DROP and nseeds >= MIN_SEEDS))
    json.dump(res, open(OUT / "backtrace_silence.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: {kk: v[kk] for kk in ("silenced", "rel_drop_median", "n_seeds_drop50", "QUEDA")}
                      for k, v in res["conditions"].items()}, indent=1))


if __name__ == "__main__":
    {"odor": odor, "tree": tree, "silence": silence, "evaluate": evaluate}[sys.argv[1]]()
