"""Fase 3a, Sessão 1: H2 (tamanho da população de DNs) × H6 (sinais no cordão), em malha aberta.

Cérebro FlyWire 783 + cordão do BANC (D-105 (c), `terrario/brain/hybrid.py`), vnc_scale = 1
(a escala é a H3, na Sessão 2). Poisson nos DNs de cada grupo; 1,5 s; métrica de ritmo nos MNs de
cada perna em 0,25–1,5 s (`terrario/vnc/rhythm.py`).

H6 (a), sinais DENTRO do cordão (`banc.neuron_signs`): predicted | verified | verified_gluexc.
H6 (b), saída MN → músculo: excitatória por construção no aparato (terrario/vnc/motor_map.py),
independente do transmissor previsto; aqui só entra como leitura dos MNs.

Grupos de DNs (IDs do BANC; os pareados viram o nó do FlyWire no híbrido):
  G1  DNp09 (par)                         marcha para a frente (Bidaye et al. 2020)
  G2  DNp09 + DNa01 + DNa02               + virada (Rayshubskiy et al. 2025)
  G3  20 DNs com maior acionamento excitatório de MNs de perna em 1–2 sinapses (calculado no grafo)
  G4  cluster "walking (DN)" do BANC (banc_neck_functional_classes.csv, 159 DNs)

Uso: uv run python -m experiments.phase3a_s1 --workers 10
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from terrario import ROOT, THIRD_PARTY
from terrario.brain import banc, flywire, hybrid
from terrario.brain.lif import ShiuLIF
from terrario.vnc.motor_map import LEGS, leg_mn_table
from terrario.vnc.rhythm import rhythm_test

OUT = ROOT / "runs" / "phase3a" / "s1"
RES = ROOT / "results" / "phase3a"
T_MS, T0_MS = 1500.0, 250.0
MODES = ["predicted", "verified", "verified_gluexc"]


def dn_groups(m, c):
    """Grupos de DNs como índices do híbrido `c`."""
    fw = flywire.load("783")
    br = m[m["super_class"].isin(hybrid.BRIDGE)]
    b2fw = hybrid.match_bridges(br, fw)

    def to_h(bids):
        out = []
        for b in bids:
            b = int(b)
            if b in b2fw:
                out.append(b2fw[b])
            elif b in c.flyid2i:
                out.append(c.flyid2i[b])
        return sorted(set(out))

    dn = m[m["super_class"] == "descending"]
    g = {"G1_DNp09": to_h(dn[dn.cell_type == "DNp09"].banc_888_id),
         "G2_DNp09_DNa01_DNa02": to_h(dn[dn.cell_type.isin(["DNp09", "DNa01", "DNa02"])].banc_888_id)}
    # G3: acionamento excitatório de MNs de perna em 1–2 sinapses (pesos positivos)
    import scipy.sparse as sp
    W = sp.csr_matrix((np.clip(c.syn_count, 0, None), c.indices, c.indptr), shape=(c.n, c.n))
    mn = c.idx(leg_mn_table(m).banc_888_id)
    alldn = to_h(dn.banc_888_id)
    Wd = W[alldn]
    drive = np.asarray(Wd[:, mn].sum(1)).ravel() + np.asarray((Wd @ W[:, mn]).sum(1)).ravel() / 100.0
    g["G3_top20_drive"] = [alldn[k] for k in np.argsort(-drive)[:20]]
    fc = pd.read_csv(THIRD_PARTY / "BANC-project/data/banc_annotations/v888/banc_neck_functional_classes.csv",
                     usecols=["id", "super_class", "super_cluster"])
    walk = fc[(fc.super_class == "descending") & (fc.super_cluster == "walking")].id
    g["G4_walking_cluster"] = to_h(walk)
    return g


_C = {}


def _init(modes):
    for md in modes:
        _C[md] = hybrid.load(1.0, sign_mode=md)


def _run(job):
    mode, gname, idx, rate, seed, t_ms = job
    c = _C[mode]
    mdl = ShiuLIF(c, seed=seed)
    mdl.set_poisson(np.array(idx), rate)
    t0 = time.perf_counter()
    i, t = mdl.run(int(t_ms / mdl.dt), cap=1 << 24)
    return mode, gname, rate, seed, i, t * mdl.dt, time.perf_counter() - t0


def main_v2(args):
    """Métrica v2 (terrario/vnc/rhythm.py): 3,25 s, 5 sementes por condição."""
    from terrario.vnc.rhythm import rhythm_v2
    m = banc.load_meta()
    c0 = hybrid.load(1.0)
    groups = dn_groups(m, c0)
    mnt = pd.read_csv(OUT / "leg_mn_table.csv")
    mn_all = mnt.h.to_numpy()
    conds = [(md, g, r) for md in args.modes for g in args.groups for r in args.rates]
    jobs = [(md, g, groups[g], r, 5000 + sd, args.t_ms) for md, g, r in conds for sd in range(args.seeds)]
    print(f"v2: {len(conds)} condições × {args.seeds} sementes = {len(jobs)} execuções", flush=True)
    runs = {}
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.modes,)) as ex:
        for mode, g, rate, seed, i, t, wall in ex.map(_run, jobs):
            keep = np.isin(i, mn_all)
            runs.setdefault((mode, g, rate), []).append((i[keep], t[keep]))
            np.savez_compressed(OUT / f"v2_{mode}_{g}_{int(rate)}_s{seed}.npz", i=i[keep], t=t[keep])
    rows = []
    for (mode, g, rate), rr in runs.items():
        row = dict(sign_mode=mode, group=g, rate_hz=rate, seeds=len(rr),
                   mn_active_mean=float(np.mean([len(np.unique(i)) for i, _ in rr])))
        nl = 0
        for leg in LEGS:
            v = rhythm_v2(rr, mnt[mnt.leg == leg].h.to_numpy(), T0_MS, args.t_ms)
            row[f"{leg}_v2"] = v["rhythmic"]
            row[f"{leg}_seeds_ok"] = v["n_seeds_ok"]
            row[f"{leg}_v1_seeds"] = sum(p["v1"] for p in v["per_seed"])
            row[f"{leg}_peak_hz"] = v["peak_hz"]
            nl += v["rhythmic"]
        row["legs_rhythmic_v2"] = nl
        rows.append(row)
        print(f"{mode:16s} {g:22s} {rate:4.0f} Hz  MNs ativos {row['mn_active_mean']:5.1f}  "
              f"pernas rítmicas v2: {nl}  (v1 por perna: "
              f"{[row[f'{l}_v1_seeds'] for l in LEGS]}/5)", flush=True)
    pd.DataFrame(rows).to_csv(RES / "s1_h2_h6_v2.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--rates", type=float, nargs="*", default=[100.0, 200.0])
    ap.add_argument("--v2", action="store_true", help="métrica v2: 3,25 s × 5 sementes")
    ap.add_argument("--t-ms", type=float, default=3250.0)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--modes", nargs="*", default=MODES)
    ap.add_argument("--groups", nargs="*", default=["G2_DNp09_DNa01_DNa02", "G3_top20_drive",
                                                    "G4_walking_cluster"])
    args = ap.parse_args()
    if args.v2:
        return main_v2(args)
    m = banc.load_meta()
    c0 = hybrid.load(1.0)
    groups = dn_groups(m, c0)
    mnt = leg_mn_table(m)
    mnt["h"] = c0.idx(mnt.banc_888_id)  # MNs do VNC têm o mesmo índice em todos os modos
    OUT.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    mnt.to_csv(OUT / "leg_mn_table.csv", index=False)
    jobs = [(md, g, idx, r, 1000 + k, T_MS) for k, (md, (g, idx), r) in enumerate(
        (md, gi, r) for md in MODES for gi in groups.items() for r in args.rates)]
    print(f"{len(jobs)} execuções; grupos: {{ {', '.join(f'{k}: {len(v)}' for k, v in groups.items())} }}", flush=True)
    rows = []
    mn_all = mnt.h.to_numpy()
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(MODES,)) as ex:
        for mode, g, rate, _seed, i, t, wall in ex.map(_run, jobs):
            keep = np.isin(i, mn_all)
            np.savez_compressed(OUT / f"{mode}_{g}_{int(rate)}.npz", i=i[keep], t=t[keep],
                                n_spk_total=len(i), n_active_total=len(np.unique(i)))
            row = dict(sign_mode=mode, group=g, n_dn=len(groups[g]), rate_hz=rate, wall_s=wall,
                       spikes_total=int(len(i)), active_total=int(len(np.unique(i))),
                       mn_active=int(len(np.unique(i[keep]))),
                       mn_rate_hz=float(keep.sum() / len(mn_all) / (T_MS / 1000)))
            nr = 0
            for leg in LEGS:
                r = rhythm_test(i, t, mnt[mnt.leg == leg].h.to_numpy(), T0_MS, T_MS)
                row[f"{leg}_rhythmic"] = r["rhythmic"]
                row[f"{leg}_peak_hz"] = r["peak_hz"]
                row[f"{leg}_ratio"] = r["ratio"]
                nr += r["rhythmic"]
            row["legs_rhythmic"] = nr
            rows.append(row)
            print(f"{mode:16s} {g:22s} {rate:5.0f} Hz  MNs ativos {row['mn_active']:3d}/391  "
                  f"taxa {row['mn_rate_hz']:.2f} Hz  pernas rítmicas {nr}  ({wall:.1f} s)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(RES / "s1_h2_h6.csv", index=False)
    json.dump({k: [int(x) for x in v] for k, v in groups.items()}, open(OUT / "dn_groups.json", "w"))


if __name__ == "__main__":
    main()
