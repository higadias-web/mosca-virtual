"""Fase 3a, Sessão 2: diagnóstico SEM AJUSTE do loop fechado (pré-registro 2, commit 87ef624).

Janela A (450–3450 ms, DNs ligados), todas as execuções de um tipo (padrão: closed, 120):
  - taxa por MN de perna;
  - ativação muscular por grupo (perna × junta × papel), recalculada dos spikes com a dinâmica de
    terrario/vnc/apparatus.py:MotorDrive (τ = 20 ms, passo de 1 ms, u = spikes/(n·dt·F_SAT) ∈ [0, 1]);
  - amplitude das juntas (p95 − p5) em ThC pitch, CTr e FTi, contra a marcha real gravada
    (flygym_demo MotionSnippet, mesma medida).
Regra (fixada antes): inconclusivo se a mediana (entre execuções) da ativação média dos grupos
for < 0,05, OU se mais da metade dos grupos ficar ≥ 0,95 em mais da metade do tempo.
"""

from __future__ import annotations

import argparse
import glob
import json

import numpy as np
import pandas as pd

from terrario import ROOT
from terrario.vnc.apparatus import MotorDrive, dof_name
from terrario.vnc.motor_map import LEGS

S2 = ROOT / "runs/phase3a/s2"
A = (450.0, 3450.0)


def activation(i, t, mnt, f_sat, tau=MotorDrive.TAU_MS):
    groups = list(mnt.groupby(["leg", "joint", "role"]))
    n_ms = int(A[1])
    a = np.zeros(len(groups))
    rec = np.zeros((n_ms, len(groups)))
    ms = np.floor(t).astype(int)
    for k, (_, g) in enumerate(groups):
        sel = np.isin(i, g.h.to_numpy())
        cnt = np.bincount(ms[sel], minlength=n_ms)[:n_ms]
        u = np.clip(cnt / (len(g) * 1e-3 * f_sat), 0, 1)
        x = 0.0
        for s in range(n_ms):
            x += (u[s] - x) / tau
            rec[s, k] = x
    return rec[int(A[0]):], [k for k, _ in groups]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="closed")
    ap.add_argument("--f-sat", type=float, default=200.0)
    args = ap.parse_args()
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    from experiments.phase3a_s2 import imposed_angles
    from terrario.vnc.apparatus import make_neuromuscular_fly
    jd = [d.name for d in make_neuromuscular_fly().get_jointdofs_order()]
    qreal, _ = imposed_angles(jd)
    qreal = qreal[: len(qreal) // 2]
    keys = {"ThC": "thc_pitch", "CTr": "ctr_pitch", "FTi": "fti_pitch"}
    real_amp = {(leg, j): float(np.ptp(np.percentile(qreal[:, jd.index(dof_name(leg, k))], [5, 95])))
                for leg in LEGS for j, k in keys.items()}
    files = sorted(glob.glob(str(S2 / f"{args.kind}_G*.npz")))
    rows, rates_all, act_rows = [], [], []
    for f in files:
        z = np.load(f)
        i, t, q = z["i"], z["t"], z["q"]
        sel = (t >= A[0]) & (t < A[1])
        cnt = pd.Series(i[sel]).value_counts().reindex(mnt.h, fill_value=0).to_numpy()
        rate = cnt / ((A[1] - A[0]) / 1000)
        rates_all.append(rate)
        rec, gnames = activation(i, t, mnt, args.f_sat)
        mean_a = rec.mean(0)
        frac_sat = (rec >= 0.95).mean(0)
        tag = f.split("/")[-1][:-4]
        act_rows += [dict(run=tag, group=g, mean_act=float(ma), frac_sat=float(fs))
                     for g, ma, fs in zip(gnames, mean_a, frac_sat)]
        qa = q[int(A[0] / 5):int(A[1] / 5)]  # q gravado a 200 Hz
        row = dict(run=tag, mn_rate_median=float(np.median(rate)), mn_rate_p90=float(np.percentile(rate, 90)),
                   mn_frac_active=float((rate > 0).mean()), act_group_mean_median=float(np.median(mean_a)),
                   frac_groups_saturated=float((frac_sat > 0.5).mean()))
        for leg in LEGS:
            for j, k in keys.items():
                amp = float(np.ptp(np.percentile(qa[:, jd.index(dof_name(leg, k))], [5, 95])))
                row[f"{leg}_{j}_amp_ratio"] = amp / real_amp[(leg, j)]
        rows.append(row)
    df = pd.DataFrame(rows)
    out = ROOT / "results/phase3a"
    tag = args.kind if args.f_sat == 200 else f"{args.kind}_fsat{args.f_sat:g}"
    df.to_csv(out / f"s2_diag_{tag}.csv", index=False)
    pd.DataFrame(act_rows).to_csv(out / f"s2_diag_{tag}_activation.csv", index=False)
    np.save(S2 / f"diag_rates_{tag}.npy", np.array(rates_all))
    near0 = float(df.act_group_mean_median.median()) < 0.05
    sat = float(df.frac_groups_saturated.median()) > 0.5
    amp_cols = [c for c in df.columns if c.endswith("_amp_ratio")]
    summ = dict(kind=args.kind, f_sat=args.f_sat, n_runs=len(df),
                mn_rate_median=float(df.mn_rate_median.median()),
                mn_rate_p90_median=float(df.mn_rate_p90.median()),
                mn_frac_active=float(df.mn_frac_active.median()),
                activation_group_mean_median=float(df.act_group_mean_median.median()),
                activation_group_mean_p90=float(np.percentile(pd.DataFrame(act_rows).mean_act, 90)),
                frac_groups_saturated_median=float(df.frac_groups_saturated.median()),
                amp_ratio_median={j: float(df[[c for c in amp_cols if f"_{j}_" in c]].stack().median())
                                  for j in keys},
                near_zero=near0, saturated=sat,
                verdict="INCONCLUSIVO" if (near0 or sat) else "diagnóstico válido (negativo não é por ativação nula ou saturada)")
    json.dump(summ, open(out / f"s2_diag_{tag}.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
