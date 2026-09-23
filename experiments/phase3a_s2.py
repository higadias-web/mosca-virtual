"""Fase 3a, Sessão 2: H1 (propriocepção) e H3 (escala do cordão), com a métrica v2 CONGELADA.

Critérios desta sessão (usuário, 2026-09-23):
  - direção dos proprioceptores por tipo celular, com as 4 combinações dos tipos principais de
    claw/hook (terrario/vnc/proprio.py); um ritmo só conta se aparecer na MAIORIA delas (≥ 3 de 4);
  - aferência imposta (marcha gravada): ritmo na frequência imposta (±1 Hz) NÃO conta como
    geração (pode ser reflexo);
  - loop fechado: o ritmo precisa se sustentar sozinho depois do impulso inicial (janela A,
    após o pulso de 50 ms) e SUMIR quando o estímulo dos DNs é desligado (janela B).

Subcomandos:
  imposed   H1-i: ângulos gravados (flygym_demo MotionSnippet, 2 s a 330 fps, tocado 2×) → só a
            transdução; DNs desligados ou G3 a 200 Hz.
  closed    H1-ii + H3: loop fechado na bola; grupos G2/G3/G4 a 200 Hz; vnc_scale 1 e 2.
Protocolo do loop fechado (ms): DNs ligados em [200, 3450); pulso de flexão 200–250 no trípode
L1-R2-L3; janela A = 450–3450 (3 s); janela B = 3700–5700 (2 s, DNs desligados).
Sinais: modo "verified" (Sessão 1). Sementes: 5 por condição (métrica v2).

Uso: uv run python -m experiments.phase3a_s2 closed --workers 10
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from terrario import ROOT
from terrario.vnc.motor_map import ANTAGONISTS, LEGS
from terrario.vnc.rhythm import rhythm_v2

S1 = ROOT / "runs" / "phase3a" / "s1"
OUT = ROOT / "runs" / "phase3a" / "s2"
RES = ROOT / "results" / "phase3a"
COMBOS = [(0, 0), (0, 1), (1, 0), (1, 1)]
SEEDS = range(7000, 7005)
A, B = (450.0, 3450.0), (3700.0, 5700.0)

_ST = {}


KIND_MODE = {"imposed": "verified", "closed": "verified", "imposed_h5": "verified",
             "control_h5": "verified", "imposed_gluexc": "verified_gluexc",
             "closed_fsat100": "verified", "closed_fsat400": "verified"}
F_SAT_OF = {"closed_fsat100": 100.0, "closed_fsat400": 400.0}  # pré-registro 2 (sensibilidade)
BG_RATE = 5.0  # H5 (docs/NON_CONNECTOME.md, H5-bg), fixado antes de rodar


def _init(keys):
    from terrario.brain import banc, hybrid
    m = banc.load_meta()
    _ST["m"] = m
    _ST["mnt"] = pd.read_csv(S1 / "leg_mn_table.csv")
    _ST["c"] = {k: hybrid.load(k[0], sign_mode=k[1]) for k in keys}
    _ST["hidx"] = {k: hybrid.banc_index(c, m) for k, c in _ST["c"].items()}
    _ST["bg"] = np.concatenate([np.load(S1 / "premotor_idx.npy"), _ST["mnt"].h.to_numpy()])


def imposed_angles(jdofs):
    """MotionSnippet → ângulos a 1 kHz na ordem `jdofs` (passivos no neutro), tocado 2×."""
    from flygym_demo.spotlight_data import MotionSnippet
    from terrario.vnc.apparatus import make_neuromuscular_fly
    from flygym.compose import ActuatorType
    sn = MotionSnippet()
    fly = make_neuromuscular_fly()
    adofs = fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)
    a = sn.get_joint_angles(output_timestep=1e-3, output_dof_order=adofs)
    names = [d.name for d in adofs]
    q = np.zeros((len(a), len(jdofs)))
    for k, n in enumerate(names):
        q[:, jdofs.index(n)] = a[:, k]
    return np.concatenate([q, q]), sn


def imposed_freqs():
    """Frequência de passada imposta por perna (pico do ângulo FTi, 2–25 Hz)."""
    from terrario.vnc.apparatus import dof_name, make_neuromuscular_fly
    jd = [d.name for d in make_neuromuscular_fly().get_jointdofs_order()]
    q, _ = imposed_angles(jd)
    q = q[: len(q) // 2]
    out = {}
    for leg in LEGS:
        x = q[:, jd.index(dof_name(leg, "fti_pitch"))]
        p = np.abs(np.fft.rfft(x - x.mean())) ** 2
        f = np.fft.rfftfreq(len(x), 1e-3)
        sel = (f >= 2) & (f <= 25)
        out[leg] = float(f[sel][np.argmax(p[sel])])
    return out


def _job(job):
    from terrario.vnc.loop import run_loop
    kind, group, dn_idx, rate, scale, combo, seed = job
    key = (scale, KIND_MODE[kind])
    c = _ST["c"][key]
    kw = dict(dn_idx=dn_idx, dn_rate=rate, seed=seed, proprio_seed=seed, combo=combo)
    if kind in ("imposed_h5", "control_h5"):
        kw.update(bg_idx=_ST["bg"], bg_rate=BG_RATE, sensory=(kind == "imposed_h5"))
    if kind in F_SAT_OF:
        kw.update(f_sat=F_SAT_OF[kind])
    if not kind.startswith("closed"):
        from terrario.vnc.apparatus import make_neuromuscular_fly
        jd = [d.name for d in make_neuromuscular_fly().get_jointdofs_order()]
        q, _ = imposed_angles(jd)
        r = run_loop(c, _ST["m"], _ST["mnt"], _ST["hidx"][key], t_on_ms=0, t_off_ms=len(q),
                     total_ms=len(q), imposed=q, kick_ms=0, **kw)
    else:
        r = run_loop(c, _ST["m"], _ST["mnt"], _ST["hidx"][key], t_on_ms=200, t_off_ms=3450,
                     total_ms=5700, **kw)
    tag = f"{kind}_{group}_s{scale:g}_c{combo[0]}{combo[1]}_{seed}"
    np.savez_compressed(OUT / f"{tag}.npz", i=r["i"], t=r["t"], ball=r["ball"], q=r["q"])
    return kind, group, scale, combo, seed, r["i"], r["t"], r["ball"], r["wall_s"]


def flex_ext_r(i, t, mnt, leg, win):
    out = {}
    for jn in ("CTr", "FTi"):
        a, b = ANTAGONISTS[jn]
        mem = mnt[mnt.leg == leg]
        ha = mem[(mem.joint == jn) & (mem.role == a)].h
        hb = mem[(mem.joint == jn) & (mem.role == b)].h
        bins = int((win[1] - win[0]) / 10)
        ca, _ = np.histogram(t[np.isin(i, ha)], bins=bins, range=win)
        cb, _ = np.histogram(t[np.isin(i, hb)], bins=bins, range=win)
        out[jn] = float(np.corrcoef(ca, cb)[0, 1]) if ca.std() > 0 and cb.std() > 0 else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=list(KIND_MODE))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--groups", nargs="*", default=None)
    ap.add_argument("--scales", type=float, nargs="*", default=None)
    ap.add_argument("--analyze", action="store_true",
                    help="só analisa os .npz salvos; exige runs/phase3a/s2/FILA_OK completo")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    groups = json.load(open(S1 / "dn_groups.json"))
    groups["none"] = []
    combos = COMBOS
    if args.kind in F_SAT_OF:
        combos = [(0, 0)]
    if not args.kind.startswith("closed"):
        gsel = args.groups or ["none", "G3_top20_drive"]
        scales = args.scales or [1.0]
        if args.kind == "control_h5":
            combos = [(0, 0)]  # sem aferência, a atribuição dos proprioceptores não importa
    else:
        gsel = args.groups or ["G2_DNp09_DNa01_DNa02", "G3_top20_drive", "G4_walking_cluster"]
        scales = args.scales or [1.0, 2.0]
    jobs = [(args.kind, g, groups[g], 200.0, s, cb, sd)
            for s in scales for g in gsel for cb in combos for sd in SEEDS]
    if not args.analyze:
        print(f"{args.kind}: {len(jobs)} execuções", flush=True)
        keys = [(s, KIND_MODE[args.kind]) for s in scales]
        with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(keys,)) as ex:
            for _ in ex.map(_job, jobs):
                pass  # cada execução grava o seu .npz; NENHUMA análise aqui
        return
    ok = OUT / "FILA_OK"
    if not ok.exists() or "INCOMPLETA" in ok.read_text():
        raise SystemExit("FILA_OK ausente ou incompleta: não analisar resultados parciais")
    res = {}
    for kind, g, _, rate, s, cb, sd in jobs:
        z = np.load(OUT / f"{kind}_{g}_s{s:g}_c{cb[0]}{cb[1]}_{sd}.npz")
        res.setdefault((g, s, cb), []).append((z["i"], z["t"], z["ball"]))
    mnt = pd.read_csv(S1 / "leg_mn_table.csv")
    imp = not args.kind.startswith("closed")
    fimp = imposed_freqs() if imp else {}
    win_a = (250.0, 4000.0) if imp else A
    rows = []
    for (g, s, cb), rr in sorted(res.items()):
        runs = [(i, t) for i, t, _ in rr]
        row = dict(kind=args.kind, group=g, vnc_scale=s, combo=f"{cb[0]}{cb[1]}",
                   mn_active=float(np.mean([len(np.unique(i[(t >= win_a[0]) & (t < win_a[1])]))
                                            for i, t in runs])),
                   ball_speed=float(np.mean([np.abs(b).mean() for _, _, b in rr])))
        for leg in LEGS:
            mem = mnt[mnt.leg == leg].h.to_numpy()
            va = rhythm_v2(runs, mem, *win_a)
            row[f"{leg}_A"] = va["rhythmic"]
            row[f"{leg}_A_hz"] = va["peak_hz"]
            if imp:
                row[f"{leg}_imposed_hz"] = fimp[leg]
                row[f"{leg}_reflex"] = bool(va["rhythmic"] and abs(va["peak_hz"] - fimp[leg]) <= 1.0)
            else:
                vb = rhythm_v2(runs, mem, *B)
                row[f"{leg}_B"] = vb["rhythmic"]
            r = [flex_ext_r(i, t, mnt, leg, win_a) for i, t in runs]
            for jn in ("CTr", "FTi"):
                v = [x[jn] for x in r if x[jn] is not None]
                row[f"{leg}_{jn}_r"] = float(np.mean(v)) if v else None
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(RES / f"s2_{args.kind}.csv", index=False)
    # resumo por condição: pernas com ritmo que conta, em quantas combinações
    for (g, s), d in df.groupby(["group", "vnc_scale"]):
        for leg in LEGS:
            if imp:
                gen = (d[f"{leg}_A"] & ~d[f"{leg}_reflex"]).sum()
                refl = d[f"{leg}_reflex"].sum()
                print(f"{g:22s} x{s:g} {leg}: geração em {gen}/4 combinações, reflexo em {refl}/4")
            else:
                ok = (d[f"{leg}_A"] & ~d[f"{leg}_B"]).sum()
                print(f"{g:22s} x{s:g} {leg}: ritmo que conta (A sim, B não) em {ok}/4 combinações; "
                      f"A em {d[f'{leg}_A'].sum()}/4; r flex×ext FTi médio "
                      f"{np.nanmean(d[f'{leg}_FTi_r'].astype(float)):.2f}")


if __name__ == "__main__":
    main()
