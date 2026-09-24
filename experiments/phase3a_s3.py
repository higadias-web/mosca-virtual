"""Fase 3a, Sessão 3: loop fechado com o aparato validado (FASE3_PLANO §7.6, §7.8, §7.10).

Só roda se a validação (a)–(e) passar com o limite escolhido (única tentativa restante: "direct_dt").
Corpo: passive="wang2025" (A2'), limites do MuJoCo pelo modo validado.

Tipos:
  closed      principal (decide o marco): G2, G3, G4 × vnc_scale 1 e 2 × 4 combinações × 5 sementes = 120
  closed_k16  sensibilidade: rigidez k/16, só G3, escala 1, 4 combinações × 5 sementes = 20 (só hipótese)
Protocolo idêntico ao da Sessão 2 (experiments/phase3a_s2.py): DNs a 200 Hz em [200, 3450) ms; pulso A7
200–250 ms; janela A = 450–3450; janela B = 3700–5700 (DNs desligados); sinais "verified"; F_SAT 200 Hz.
Ritmo que conta numa combinação (como na Sessão 2): v2 congelada na janela A (≥ 3/5 sementes) E não em B.
Regra do marco (só "closed"), por condição (grupo × escala) e perna, nº de combinações com ritmo que conta:
  0/4 em tudo → ausência; ≥ 3/4 em alguma → ritmo (ainda sujeito à ablação, §1b.2);
  1–2/4 (sem nenhum ≥ 3/4) → ausência para o marco, registrada como hipótese (direção por tipo não verificada).
Para k/16 vale a mesma regra das 4 combinações, mas o resultado é só hipótese.
Diagnóstico (não decide): taxa dos MNs, ativação dos grupos, fração do tempo de cada DOF ativo a ≤ 0,02 rad
de um limite (ou além); ritmo numa perna com algum DOF ativo no limite > 50 % do tempo = suspeito de artefato.

Uso (execução separada da análise):
  uv run python -m experiments.phase3a_s3 closed --workers 10
  uv run python -m experiments.phase3a_s3 closed_k16 --workers 10
  uv run python -m experiments.phase3a_s3 --check          # conta os .npz por tipo e grava FILA_OK
  uv run python -m experiments.phase3a_s3 --analyze        # exige FILA_OK com as contagens completas
"""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from terrario import ROOT
from terrario.vnc.motor_map import LEGS
from terrario.vnc.rhythm import rhythm_v2

S1 = ROOT / "runs" / "phase3a" / "s1"
OUT = ROOT / "runs" / "phase3a" / "s3"
RES = ROOT / "results" / "phase3a"
COMBOS = [(0, 0), (0, 1), (1, 0), (1, 1)]
SEEDS = range(7000, 7005)
A, B = (450.0, 3450.0), (3700.0, 5700.0)
LIMIT = "direct_dt"   # único modo que resta (§7.8); a fila só roda se a validação dele passar
AT_LIMIT_RAD, SUSPECT_FRAC = 0.02, 0.5
KINDS = {
    "closed": dict(groups=["G2_DNp09_DNa01_DNa02", "G3_top20_drive", "G4_walking_cluster"],
                   scales=[1.0, 2.0], k_scale=1.0),
    "closed_k16": dict(groups=["G3_top20_drive"], scales=[1.0], k_scale=1.0 / 16),
}
TAG_RE = {k: re.compile(rf"^{k}_G\d_.+_s[\d.]+_c\d\d_\d+\.npz$") for k in KINDS}

_ST = {}


def expected(kind):
    k = KINDS[kind]
    return len(k["groups"]) * len(k["scales"]) * len(COMBOS) * len(SEEDS)


def _init(scales):
    from terrario.brain import banc, hybrid
    m = banc.load_meta()
    _ST["m"] = m
    _ST["mnt"] = pd.read_csv(S1 / "leg_mn_table.csv")
    _ST["c"] = {s: hybrid.load(s, sign_mode="verified") for s in scales}
    _ST["hidx"] = {s: hybrid.banc_index(c, m) for s, c in _ST["c"].items()}


def _job(job):
    from terrario.vnc.loop import run_loop
    kind, group, dn_idx, scale, combo, seed = job
    r = run_loop(_ST["c"][scale], _ST["m"], _ST["mnt"], _ST["hidx"][scale], dn_idx=dn_idx, dn_rate=200.0,
                 t_on_ms=200, t_off_ms=3450, total_ms=5700, seed=seed, proprio_seed=seed, combo=combo,
                 passive="wang2025", k_scale=KINDS[kind]["k_scale"], limit=LIMIT)
    tag = f"{kind}_{group}_s{scale:g}_c{combo[0]}{combo[1]}_{seed}"
    np.savez_compressed(OUT / f"{tag}.npz", i=r["i"], t=r["t"], ball=r["ball"], q=r["q"],
                        jdofs=np.array(r["jdofs"]), wall_s=r["wall_s"])
    return tag


def jobs_of(kind):
    groups = json.load(open(S1 / "dn_groups.json"))
    k = KINDS[kind]
    return [(kind, g, groups[g], s, cb, sd) for s in k["scales"] for g in k["groups"]
            for cb in COMBOS for sd in SEEDS]


def check():
    counts = {k: sum(1 for f in OUT.glob("*.npz") if TAG_RE[k].match(f.name)) for k in KINDS}
    full = all(counts[k] == expected(k) for k in KINDS)
    txt = "\n".join(f"{k} {counts[k]}/{expected(k)}" for k in KINDS) + ("\nCOMPLETA\n" if full else "\nINCOMPLETA\n")
    (OUT / "FILA_OK").write_text(txt)
    print(txt)


def _limit_frac(q, jdofs, kscale):
    """Fração do tempo (janela A, q a 200 Hz) de cada DOF ativo a ≤ AT_LIMIT_RAD de um limite ou além."""
    import mujoco as mj
    from terrario.vnc.apparatus import build_ball_scene, passive_params
    key = ("rng", kscale)
    if key not in _ST:
        m = build_ball_scene(passive="wang2025", k_scale=kscale, limit=LIMIT).sim.mj_model
        _ST[key] = {n: tuple(m.jnt_range[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"fly/{n}")])
                    for n in passive_params()}
    rng = _ST[key]
    qa = q[int(A[0] / 5):int(A[1] / 5)]
    out = {}
    for n, (lo, hi) in rng.items():
        x = qa[:, list(jdofs).index(n)]
        out[n] = float(((x <= lo + AT_LIMIT_RAD) | (x >= hi - AT_LIMIT_RAD)).mean())
    return out


def analyze():
    ok = OUT / "FILA_OK"
    if not ok.exists():
        raise SystemExit("FILA_OK ausente: não analisar resultados parciais")
    lines = dict(l.split() for l in ok.read_text().splitlines() if l and l[0] != "C" and l[0] != "I")
    for k in KINDS:
        n = sum(1 for f in OUT.glob("*.npz") if TAG_RE[k].match(f.name))
        if lines.get(k) != f"{expected(k)}/{expected(k)}" or n != expected(k):
            raise SystemExit(f"FILA_OK incompleta para {k} ({lines.get(k)}, {n} arquivos): não analisar")
    from experiments.phase3a_s2_diag import activation
    mnt = pd.read_csv(S1 / "leg_mn_table.csv")
    summary = {}
    for kind in KINDS:
        res = {}
        for _, g, _, s, cb, sd in jobs_of(kind):
            z = np.load(OUT / f"{kind}_{g}_s{s:g}_c{cb[0]}{cb[1]}_{sd}.npz")
            res.setdefault((g, s, cb), []).append(z)
        rows = []
        for (g, s, cb), zz in sorted(res.items()):
            runs = [(z["i"], z["t"]) for z in zz]
            lf = [_limit_frac(z["q"], z["jdofs"], KINDS[kind]["k_scale"]) for z in zz]
            lfm = {n: float(np.mean([x[n] for x in lf])) for n in lf[0]}
            rates, acts = [], []
            for i, t in runs:
                sel = (t >= A[0]) & (t < A[1])
                cnt = pd.Series(i[sel]).value_counts().reindex(mnt.h, fill_value=0).to_numpy()
                rates.append(cnt / ((A[1] - A[0]) / 1000))
                rec, _ = activation(i, t, mnt, 200.0)
                acts.append(float(np.median(rec.mean(0))))
            row = dict(kind=kind, group=g, vnc_scale=s, combo=f"{cb[0]}{cb[1]}",
                       mn_rate_median=float(np.median(np.concatenate(rates))),
                       mn_rate_mean=float(np.mean(np.concatenate(rates))),
                       mn_frac_active=float(np.mean(np.concatenate(rates) > 0)),
                       act_group_mean_median=float(np.median(acts)),
                       ball_speed=float(np.mean([np.abs(z["ball"]).mean() for z in zz])))
            for leg in LEGS:
                mem = mnt[mnt.leg == leg].h.to_numpy()
                va, vb = rhythm_v2(runs, mem, *A), rhythm_v2(runs, mem, *B)
                row[f"{leg}_A"], row[f"{leg}_B"], row[f"{leg}_A_hz"] = va["rhythmic"], vb["rhythmic"], va["peak_hz"]
                row[f"{leg}_counts"] = bool(va["rhythmic"] and not vb["rhythmic"])
                legdofs = [n for n in lfm if f"{leg}_" in n]
                row[f"{leg}_max_limit_frac"] = max(lfm[n] for n in legdofs)
                row[f"{leg}_suspect"] = bool(row[f"{leg}_counts"] and row[f"{leg}_max_limit_frac"] > SUSPECT_FRAC)
            rows.append(row)
            for n, v in lfm.items():
                row[f"limfrac_{n}"] = v
        df = pd.DataFrame(rows)
        df.to_csv(RES / f"s3_{kind}.csv", index=False)
        cond = []
        for (g, s), d in df.groupby(["group", "vnc_scale"]):
            for leg in LEGS:
                n = int(d[f"{leg}_counts"].sum())
                cond.append(dict(group=g, vnc_scale=s, leg=leg, n_combos=n,
                                 suspect=bool(d[f"{leg}_suspect"].any())))
        cd = pd.DataFrame(cond)
        mx = int(cd.n_combos.max())
        verdict = ("ritmo" if mx >= 3 else "ausência (1–2/4 registrado como hipótese)" if mx >= 1 else "ausência")
        summary[kind] = dict(n_runs=expected(kind), max_combos=mx, verdict=verdict,
                             role="decide o marco" if kind == "closed" else "só hipótese",
                             conditions_with_1plus=cd[cd.n_combos >= 1].to_dict("records"),
                             any_suspect=bool(cd.suspect.any()),
                             mn_rate_median=float(df.mn_rate_median.median()),
                             act_group_mean_median=float(df.act_group_mean_median.median()))
        cd.to_csv(RES / f"s3_{kind}_conditions.csv", index=False)
    json.dump(summary, open(RES / "s3_closed_summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", nargs="?", choices=list(KINDS))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.check:
        return check()
    if args.analyze:
        return analyze()
    jobs = jobs_of(args.kind)
    print(f"{args.kind}: {len(jobs)} execuções", flush=True)
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(KINDS[args.kind]["scales"],)) as ex:
        for tag in ex.map(_job, jobs):
            print("ok", tag, flush=True)  # cada execução grava o seu .npz; NENHUMA análise aqui


if __name__ == "__main__":
    main()
