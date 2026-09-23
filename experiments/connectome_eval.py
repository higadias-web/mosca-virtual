"""D-105: comparação dos três conectomas candidatos para a Fase 3.

Subcomandos:
  bench   custo nesta máquina: RAM por processo, tempo por trial de 1 s (açúcar a 200 Hz),
          quantos processos cabem na RAM
  fig1d   Fig. 1D do Shiu (GRNs de açúcar 10..200 Hz, 30 trials) no conectoma escolhido
  probe   sonda exploratória de locomoção: Poisson em DNs de marcha → taxa dos motoneurônios de perna

Conectomas (terrario/brain/connectomes.py): 783, banc888, banc888v3, fw783+bancvnc.

Estímulo de açúcar por conectoma (lados das anotações: os 21 GRNs do Shiu são 'left' e o MN9
dele, 720575940660219265, é 'right' em flywire_annotations/Supplemental_file1; no BANC o MN9
direito, 720575941623285450, tem fafb_match = 720575940660219265):
  783, fw783+bancvnc  os 20 IDs do Shiu que existem na v783 (experiments/shiu_repro.SUGAR)
  banc888*  --sugar match  neurônios do BANC cujo fafb_match é um dos 21 IDs do Shiu
            --sugar type   GRNs do labelo, lado esquerdo, tipos LB3b + LB3c (anotados no BANC
                           como "sugar, Gr64f" / "sugar, low_salt, Gr64f, Ir56b")

Uso (da raiz):
  uv run python -m experiments.connectome_eval bench --version banc888
  uv run python -m experiments.connectome_eval fig1d --version banc888 --sugar type --workers 10
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from terrario import ROOT, THIRD_PARTY
from terrario.brain import connectomes
from terrario.brain.lif import SHIU_PARAMS, ShiuLIF
from experiments.shiu_repro import N_RUN, SUGAR, T_MS, _seed

OUT = ROOT / "runs" / "d105"
MN9_FW = 720575940660219265
MN9_BANC = 720575941623285450
BANC_SUGAR_TYPES = ["LB3b", "LB3c"]


def sugar_ids(version: str, how: str) -> list[int]:
    if not version.startswith("banc"):
        return SUGAR
    from terrario.brain import banc
    m = banc.load_meta()
    if how == "match":
        s = set(map(str, SUGAR))
        return m.loc[m["fafb_match"].astype(str).isin(s), "banc_888_id"].tolist()
    lab = m[(m["cell_sub_class"] == "labellum_taste_bristle_gustatory_neuron")
            & (m["side"] == "left") & m["cell_type"].isin(BANC_SUGAR_TYPES)]
    return lab["banc_888_id"].tolist()


def mn9_id(version: str) -> int:
    return MN9_BANC if version.startswith("banc") else MN9_FW


# ------------------------------------------------------------------ trials em paralelo
_C = None
_P = None


def _init(version, params):
    global _C, _P
    _C = connectomes.load(version)
    _P = params


def _trial(job):
    name, trial, ids, rate = job
    m = ShiuLIF(_C, params=_P, seed=_seed(_C.version, name, trial))
    m.set_poisson(_C.idx(ids), rate)
    t0 = time.perf_counter()
    i, _ = m.run(int(round(T_MS / m.dt)))
    wall = time.perf_counter() - t0
    u, n = np.unique(i, return_counts=True)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return name, trial, u.astype(np.int32), n.astype(np.int32), wall, rss


def run(version, jobs, workers, params=None):
    counts, walls, rss = {}, [], 0.0
    t0 = time.time()
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(version, params)) as ex:
        for k, (name, trial, u, n, w, r) in enumerate(ex.map(_trial, jobs, chunksize=2)):
            d = counts.setdefault(name, {})
            for ui, ni in zip(u.tolist(), n.tolist()):
                d.setdefault(ui, np.zeros(N_RUN))[trial] = ni
            walls.append(w)
            rss = max(rss, r)
            if (k + 1) % 100 == 0:
                print(f"  {k+1}/{len(jobs)} ({time.time()-t0:.0f} s)", flush=True)
    flyids = connectomes.load(version).flyids
    rows = [(name, int(flyids[i]), (arr / (T_MS / 1000)).mean(), (arr / (T_MS / 1000)).std())
            for name, d in counts.items() for i, arr in d.items()]
    df = pd.DataFrame(rows, columns=["exp_name", "flyid", "rate", "std"])
    return df, dict(total_s=time.time() - t0, trial_wall_mean=float(np.mean(walls)),
                    worker_peak_rss_mb=rss, workers=workers, n_trials=len(jobs))


# ------------------------------------------------------------------ subcomandos
def cmd_bench(args):
    """Um processo: carga, RAM e custo por 1 s com açúcar a 200 Hz (como no BENCHMARK §1)."""
    import subprocess
    import sys
    # IDs obtidos noutro processo: ru_maxrss sobrevive ao execve no Linux, e os metadados do
    # BANC (~0,7 GB no pandas) inflariam a RAM medida
    ids = json.loads(subprocess.run(
        [sys.executable, "-c", "import json; from experiments.connectome_eval import sugar_ids; "
         f"print(json.dumps(sugar_ids({args.version!r}, {args.sugar!r})))"],
        capture_output=True, text=True, cwd=ROOT, check=True).stdout)
    code = f"""
import time, resource, json, numpy as np
t0 = time.perf_counter()
from terrario.brain import connectomes
c = connectomes.load({args.version!r})
tl = time.perf_counter() - t0
rss_load = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from terrario.brain.lif import ShiuLIF, SHIU_PARAMS
walls = []
for trial in range({args.trials}):
    m = ShiuLIF(c, params=dict(SHIU_PARAMS, w_syn=SHIU_PARAMS['w_syn'] * {args.wscale}), seed=trial)
    m.set_poisson(c.idx([x for x in {ids!r} if x in c.flyid2i]), 200.0)
    m.run(10)  # compila / aquece
    t1 = time.perf_counter()
    nsp = 0
    for _ in range(1000):          # 1 s em chamadas de 1 ms (sincronização D-006)
        i, _t = m.run(10)
        nsp += len(i)
    walls.append(time.perf_counter() - t1)
print(json.dumps(dict(version={args.version!r}, wscale={args.wscale}, sugar={args.sugar!r}, n=int(c.n), edges=int(len(c.indices)),
    load_s=tl, rss_load_mb=rss_load, wall_per_sim_s=float(np.median(walls)),
    wall_all=walls, spikes_per_s=nsp, n_active_end=m.n_active,
    peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)))
"""
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    if out.returncode:
        raise SystemExit(out.stderr)
    r = json.loads(out.stdout.strip().splitlines()[-1])
    avail = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**20
    r["workers_fit_ram"] = int((avail - 3000) // r["peak_rss_mb"])  # 3 GB para SO + sessão
    print(json.dumps(r))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "bench.jsonl", "a") as f:
        f.write(json.dumps(r) + "\n")


def cmd_fig1d(args):
    ids = sugar_ids(args.version, args.sugar)
    c = connectomes.load(args.version)
    ids = [i for i in ids if i in c.flyid2i]
    params = dict(SHIU_PARAMS, w_syn=SHIU_PARAMS["w_syn"] * args.wscale)
    jobs = [(f"sugar_{f}Hz", t, ids, f) for f in range(10, 201, 10) for t in range(N_RUN)]
    tag = f"{args.version}_{args.sugar}" + (f"_w{args.wscale:g}" if args.wscale != 1 else "")
    print(f"fig1d {tag}: {len(ids)} GRNs, {len(jobs)} trials, {args.workers} processos", flush=True)
    df, info = run(args.version, jobs, args.workers, params)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / f"fig1d_{tag}.parquet")
    mn = df[df.flyid == mn9_id(args.version)].set_index("exp_name")["rate"]
    info.update(tag=tag, n_grn=len(ids), wscale=args.wscale,
                mn9={f: float(mn.get(f"sugar_{f}Hz", 0.0)) for f in range(10, 201, 10)},
                n_active_200=int((df[df.exp_name == "sugar_200Hz"].rate > 0).sum()))
    with open(OUT / f"fig1d_{tag}.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info))


def cmd_probe(args):
    """Poisson em DNs anotados (tipo, os dois lados) e taxa média por classe de motoneurônio.

    Exploratório: sem propriocepção, sem corpo. Pergunta só se o sinal chega aos MNs de perna e
    se há alguma estrutura temporal (espectro da taxa populacional por perna).
    """
    from terrario.brain import banc
    m = banc.load_meta()
    c = connectomes.load(args.version)
    if args.version.startswith("banc"):
        dn = m[(m.super_class == "descending") & m.cell_type.isin(args.dn)]["banc_888_id"].tolist()
    else:  # híbrido: DNs pareados têm o ID do FlyWire (tipo pelas anotações v783)
        a = pd.read_csv(THIRD_PARTY / "flywire_annotations/supplemental_files/"
                        "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False,
                        usecols=["root_id", "cell_type", "super_class"])
        dn = a[(a.super_class == "descending") & a.cell_type.isin(args.dn)].root_id.tolist()
    dn = [d for d in dn if d in c.flyid2i]
    lmn = m[(m.cell_class == "leg_motor_neuron") & m.banc_888_id.isin(set(c.flyid2i))]
    idx = {k: c.idx(g["banc_888_id"]) for k, g in lmn.groupby("cell_sub_class")}
    res = {}
    for rate in args.rates:
        mdl = ShiuLIF(c, params=dict(SHIU_PARAMS, w_syn=SHIU_PARAMS["w_syn"] * args.wscale),
                      seed=int(rate))
        mdl.set_poisson(c.idx(dn), rate)
        i, t = mdl.run(int(args.ms / mdl.dt))
        r = {}
        for k, ii in idx.items():
            sel = np.isin(i, ii)
            r[k] = dict(n=len(ii), active=int(len(np.unique(i[sel]))),
                        mean_rate_hz=float(sel.sum() / len(ii) / (args.ms / 1000)))
            # periodicidade: pico do espectro da taxa populacional (bins de 5 ms)
            if sel.sum() > 20:
                h, _ = np.histogram(t[sel] * mdl.dt, bins=int(args.ms / 5), range=(0, args.ms))
                h = h - h.mean()
                sp_ = np.abs(np.fft.rfft(h)) ** 2
                fr = np.fft.rfftfreq(len(h), d=0.005)
                k0 = 1 + int(np.argmax(sp_[1:]))
                r[k]["peak_hz"] = float(fr[k0])
                r[k]["peak_power_ratio"] = float(sp_[k0] / sp_[1:].mean())
        res[rate] = dict(dn_n=len(dn), total_spikes=int(len(i)), n_active_end=mdl.n_active, mn=r)
        print(rate, json.dumps(res[rate]), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"probe_{args.version}_{'-'.join(args.dn)}_w{args.wscale:g}.json", "w") as f:
        json.dump(res, f, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["bench", "fig1d", "probe"])
    ap.add_argument("--version", default="banc888")
    ap.add_argument("--sugar", default="type", choices=["type", "match"])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--wscale", type=float, default=1.0)
    ap.add_argument("--dn", nargs="*", default=["DNp09"])
    ap.add_argument("--rates", type=float, nargs="*", default=[50, 100, 200])
    ap.add_argument("--ms", type=float, default=1000.0)
    args = ap.parse_args()
    {"bench": cmd_bench, "fig1d": cmd_fig1d, "probe": cmd_probe}[args.cmd](args)


if __name__ == "__main__":
    main()
