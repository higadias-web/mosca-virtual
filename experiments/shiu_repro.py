"""Fase 1: reprodução de Shiu et al. 2024 (figures.ipynb) com o motor terrario.brain.lif.

Experimentos (mesmos parâmetros de third_party/Drosophila_brain_model/figures.ipynb):
  fig1d  GRNs de açúcar (lábelo dir.) a 10..200 Hz -> taxa de todos os neurônios
  fig1e  ativação individual de cada um dos top-200 da Fig. 1D -> taxa do MN9
  fig1f  açúcar + silenciamento individual de cada um dos top-200 -> taxa do MN9
  fig3a  açúcar (0..200 Hz) x amargo (0..200 Hz) -> taxa do MN9

30 trials de 1 s por condição (default_params: n_run=30, t_run=1000 ms). Os trials rodam
em paralelo em processos separados; cada condição/trial tem semente determinística.
Saída: runs/phase1/<versão>/<exp>.parquet com colunas (exp_name, flyid, rate, std),
na mesma convenção de utils.get_rate (média e desvio populacional sobre os trials).

Uso: uv run python -m experiments.shiu_repro fig1d --version 630 --workers 10
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from terrario import DATA, ROOT
from terrario.brain import flywire
from terrario.brain.lif import ShiuLIF

N_RUN, T_MS = 30, 1000.0
MN9_L = 720575940660219265  # figures.ipynb, Fig. 1E / 3A ('left')
PUB = DATA / "shiu_published" / "results"

# figures.ipynb (células da Fig. 1D e 3A)
SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345, 720575940617000768,
    720575940630797113, 720575940632889389, 720575940621754367, 720575940621502051, 720575940640649691,
    720575940639332736, 720575940616885538, 720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]
BITTER = [
    720575940621778381, 720575940602353632, 720575940617094208, 720575940619197093, 720575940626287336,
    720575940618600651, 720575940627692048, 720575940630195909, 720575940646212996, 720575940610483162,
    720575940645743412, 720575940627578156, 720575940622298631, 720575940621008895, 720575940629146711,
    720575940610259370, 720575940610481370, 720575940619028208, 720575940614281266, 720575940613061118,
    720575940604027168,
]

_CONN = None


def _init(version):
    global _CONN
    _CONN = flywire.load(version)


def _seed(*key) -> int:
    return int.from_bytes(hashlib.sha256(repr(key).encode()).digest()[:8], "little")


def _one_trial(job):
    """job = (exp_name, trial, exc, rate, exc2, rate2, silence). Retorna contagens esparsas."""
    exp_name, trial, exc, rate, exc2, rate2, silence = job
    c = _CONN
    m = ShiuLIF(c, seed=_seed(c.version, exp_name, trial))
    # model.py:poi define os alvos dos dois grupos, mesmo com taxa 0 (rfc = 0 em todos)
    m.set_poisson(c.idx(exc), rate)
    if exc2:
        m.set_poisson(c.idx(exc2), rate2)
    if silence:
        m.silence(c.idx(silence))
    i, _ = m.run(int(round(T_MS / m.dt)))
    u, n = np.unique(i, return_counts=True)
    return exp_name, trial, u.astype(np.int32), n.astype(np.int32)


def run_jobs(version, jobs, workers):
    """Executa jobs; devolve DataFrame (exp_name, flyid, rate, std) como utils.get_rate."""
    counts: dict[str, dict[int, np.ndarray]] = {}
    t0 = time.time()
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(version,)) as ex:
        for k, (exp_name, trial, u, n) in enumerate(ex.map(_one_trial, jobs, chunksize=4)):
            d = counts.setdefault(exp_name, {})
            for ui, ni in zip(u.tolist(), n.tolist()):
                d.setdefault(ui, np.zeros(N_RUN))[trial] = ni
            if (k + 1) % 200 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(jobs)} trials, {el:.0f} s "
                      f"(restam ~{el/(k+1)*(len(jobs)-k-1)/60:.1f} min)", flush=True)
    flyids = flywire.load(version).flyids
    rows = []
    for exp_name, d in counts.items():
        for i, arr in d.items():
            r = arr / (T_MS / 1000)
            rows.append((exp_name, int(flyids[i]), r.mean(), r.std()))
    return pd.DataFrame(rows, columns=["exp_name", "flyid", "rate", "std"])


def jobs_fig1d(version):
    return [(f"sugarR_{f}Hz", t, SUGAR, f, [], 0, []) for f in range(10, 201, 10) for t in range(N_RUN)]


class _OldPandasUnpickler(pickle.Unpickler):
    """Os pickles publicados usam pandas.core.indexes.numeric.Int64Index (pandas < 2)."""

    def find_class(self, module, name):
        if module == "pandas.core.indexes.numeric":
            return pd.Index  # Int64Index/Float64Index viraram pd.Index no pandas 2
        return super().find_class(module, name)


def load_pub_pickle(path):
    with open(path, "rb") as f:
        return _OldPandasUnpickler(f).load()


def _top200():
    """Top-200 da Fig. 1D publicada (figures.ipynb: ordenado por sugarR_200Hz)."""
    return [int(x) for x in load_pub_pickle(PUB / "figure_1" / "fig_1d_id_top200.pickle")]


def jobs_fig1e(version, freqs):
    return [(f"{f}_Hz_{i}", t, [i], f, [], 0, []) for f in freqs for i in _top200()
            for t in range(N_RUN)]


def jobs_fig1f(version, freqs):
    return [(f"sugarR-silencing{i}_{f}_Hz", t, SUGAR, f, [], 0, [i]) for f in freqs
            for i in _top200() for t in range(N_RUN)]


def jobs_fig3a(version):
    fr = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
    return [(f"Sugar_Bitter_{s}_Hz_{b}_Hz", t, SUGAR, s, BITTER, b, []) for s in fr for b in fr
            for t in range(N_RUN)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["fig1d", "fig1e", "fig1f", "fig3a"])
    ap.add_argument("--version", default="630")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--freqs", type=int, nargs="*", default=None)
    args = ap.parse_args()

    if args.exp == "fig1d":
        jobs = jobs_fig1d(args.version)
    elif args.exp == "fig1e":
        jobs = jobs_fig1e(args.version, args.freqs or [25, 50, 75, 100, 125, 150, 175, 200])
    elif args.exp == "fig1f":
        jobs = jobs_fig1f(args.version, args.freqs or [50, 60, 70, 80, 90, 100, 110, 120])
    else:
        jobs = jobs_fig3a(args.version)
    c = flywire.load(args.version)
    missing = {f for j in jobs for f in (*j[2], *j[4], *j[6]) if f not in c.flyid2i}
    if missing:
        print(f"AVISO: {len(missing)} IDs não existem na v{args.version} e foram removidos: "
              f"{sorted(missing)[:5]}...")
        jobs = [(j[0], j[1], [f for f in j[2] if f not in missing], j[3],
                 [f for f in j[4] if f not in missing], j[5],
                 [f for f in j[6] if f not in missing]) for j in jobs]
        jobs = [j for j in jobs if j[2]]
    print(f"{args.exp} v{args.version}: {len(jobs)} trials, {args.workers} processos", flush=True)
    t0 = time.time()
    df = run_jobs(args.version, jobs, args.workers)
    # com --freqs, um arquivo por lote (checkpoint: execuções longas salvam por partes)
    suffix = "_" + "-".join(map(str, args.freqs)) if args.freqs else ""
    out = ROOT / "runs" / "phase1" / args.version / f"{args.exp}{suffix}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    print(f"ok: {out} ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
