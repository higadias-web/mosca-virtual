"""Benchmark do cérebro da mosca (Shiu et al. 2024, FlyWire v783), isolado.

Uso: uv run python bench/bench_brain.py --engine numba --sim-ms 1000 --trials 1

Engines:
  brian2-runtime     código original (third_party/Drosophila_brain_model/model.py:run_trial),
                     alvo de codegen padrão do Brian2 (cython)
  brian2-cpp         mesmo modelo, com brian2.set_device('cpp_standalone')
  numba, numba-par   protótipos em bench/lif_engines.py (float64)
  numba-f32          idem, em float32
  numpy, torch       protótipos em bench/lif_engines.py

Estímulo: os 20 GRNs de açúcar do example.ipynb do Shiu que existem na v783, a 150 Hz.
Imprime uma linha JSON com os tempos, a RAM de pico (ru_maxrss) e as contagens de spikes
por neurônio (para a comparação numérica entre motores).
"""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHIU = ROOT / "third_party" / "Drosophila_brain_model"
PATH_COMP = SHIU / "Completeness_783.csv"
PATH_CON = SHIU / "Connectivity_783.parquet"

# example.ipynb (Shiu): GRNs de açúcar do hemisfério direito (IDs da v630)
SUGAR_630 = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]
MN9 = 720575940660219265  # example.ipynb


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def run_brian(args, standalone):
    sys.path.insert(0, str(SHIU))
    import pandas as pd
    import brian2
    from brian2 import ms, Network
    import model as shiu  # third_party/Drosophila_brain_model/model.py

    params = dict(shiu.default_params)
    params["t_run"] = args.sim_ms * ms
    df_comp = pd.read_csv(PATH_COMP, index_col=0)
    flyid2i = {j: i for i, j in enumerate(df_comp.index)}
    exc = [flyid2i[n] for n in SUGAR_630 if n in flyid2i]
    if standalone:
        outdir = ROOT / "bench" / "results" / "raw" / f"brian2_cpp_{os.getpid()}"
        brian2.set_device("cpp_standalone", directory=str(outdir), build_on_run=False)
        if args.threads > 1:
            brian2.prefs.devices.cpp_standalone.openmp_threads = args.threads
    t0 = time.perf_counter()
    counts = None
    walls = []
    for trial in range(args.trials):
        # replica model.py:run_trial, separando construção e execução
        tb = time.perf_counter()
        neu, syn, spk_mon = shiu.create_model(PATH_COMP, PATH_CON, params)
        poi_inp, neu = shiu.poi(neu, exc, [], params)
        net = Network(neu, syn, spk_mon, *poi_inp)
        tbuild = time.perf_counter() - tb
        tr = time.perf_counter()
        net.run(duration=params["t_run"])
        if standalone:
            tc = time.perf_counter()
            brian2.device.build(directory=str(outdir), run=False, compile=True)
            tcompile = time.perf_counter() - tc
            tr = time.perf_counter()
            brian2.device.run()
        trun = time.perf_counter() - tr
        i = np.asarray(spk_mon.i[:])
        c = np.bincount(i, minlength=len(df_comp))
        counts = c if counts is None else counts + c
        walls.append(dict(build_s=tbuild, run_s=trun,
                          **({"compile_s": tcompile} if standalone else {})))
        if standalone:
            break  # standalone: um único build por processo
    return walls, counts, flyid2i, exc


def run_proto(args):
    sys.path.insert(0, str(ROOT / "bench"))
    import lif_engines as le

    tl = time.perf_counter()
    conn = le.load_connectome(str(PATH_COMP), str(PATH_CON))
    tload = time.perf_counter() - tl
    exc = [conn.flyid2i[n] for n in SUGAR_630 if n in conn.flyid2i]
    nsteps = int(round(args.sim_ms / 0.1))
    walls, counts = [], None
    for trial in range(args.trials):
        e = args.engine
        tb = time.perf_counter()
        if e == "numba-active":
            eng = le.make_numba_active_engine(conn, exc, seed=trial)
            if trial == 0:
                le.make_numba_active_engine(conn, exc, seed=999).run(10)
        elif e.startswith("numba"):
            if e == "numba-par":
                import numba
                numba.set_num_threads(args.threads)
            eng = le.make_numba_engine(conn, exc, seed=trial, parallel=(e == "numba-par"),
                                       dtype=np.float32 if e == "numba-f32" else np.float64)
            if trial == 0:  # compilação JIT (cache em disco) fora da medição
                w = le.make_numba_engine(conn, exc, seed=999, parallel=(e == "numba-par"),
                                         dtype=np.float32 if e == "numba-f32" else np.float64)
                w.run(10)
        elif e == "numpy":
            eng = le.make_numpy_engine(conn, exc, seed=trial)
        elif e == "torch":
            eng = le.make_torch_engine(conn, exc, seed=trial, threads=args.threads)
        else:
            raise SystemExit(f"engine desconhecido: {e}")
        tbuild = time.perf_counter() - tb
        tr = time.perf_counter()
        # passo de sincronização típico da co-simulação: 1 ms (10 passos de 0,1 ms)
        ids = []
        for _ in range(nsteps // args.chunk):
            i, _t = eng.run(args.chunk)
            ids.append(np.asarray(i))
        trun = time.perf_counter() - tr
        c = np.bincount(np.concatenate(ids).astype(np.int64), minlength=conn.n)
        counts = c if counts is None else counts + c
        walls.append(dict(build_s=tbuild, run_s=trun, load_s=tload))
    return walls, counts, conn.flyid2i, exc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--sim-ms", type=float, default=1000.0)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--chunk", type=int, default=10, help="passos por chamada (10 = 1 ms)")
    ap.add_argument("--counts-out", type=Path, default=None)
    args = ap.parse_args()

    t0 = time.perf_counter()
    if args.engine == "brian2-runtime":
        walls, counts, flyid2i, exc = run_brian(args, standalone=False)
    elif args.engine == "brian2-cpp":
        walls, counts, flyid2i, exc = run_brian(args, standalone=True)
    else:
        walls, counts, flyid2i, exc = run_proto(args)
    total = time.perf_counter() - t0
    ntr = len(walls)
    run_s = [w["run_s"] for w in walls]
    if args.counts_out:
        np.save(args.counts_out, counts)
    out = dict(
        engine=args.engine, threads=args.threads, sim_ms=args.sim_ms, trials=ntr,
        n_exc=len(exc),
        run_s_mean=float(np.mean(run_s)),
        wall_per_sim_s=float(np.mean(run_s) / (args.sim_ms / 1000)),
        build_s_mean=float(np.mean([w["build_s"] for w in walls])),
        extra={k: float(np.mean([w[k] for w in walls])) for k in walls[0] if k not in ("run_s", "build_s")},
        total_s=total,
        peak_rss_mb=peak_rss_mb(),
        spikes_per_trial=float(counts.sum() / ntr),
        active_neurons=int((counts > 0).sum()),
        mn9_rate_hz=float(counts[flyid2i[MN9]] / ntr / (args.sim_ms / 1000)),
    )
    print(json.dumps(out))


if __name__ == "__main__":
    main()
