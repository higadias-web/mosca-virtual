"""Auditoria: DNg100 e DNb08 ISOLADOS no híbrido FlyWire 783 + cordão BANC (LIF do Shiu), malha aberta.

Pugliese et al. 2025 (bioRxiv 10.1101/2025.09.12.675944) obtêm ritmo nos MNs de perna estimulando SÓ o
DNg100 (e o DNb08) num modelo de TAXA (tanh) do cordão, sem propriocepção. No Terrário Virtual, o DNg100
e o DNb08 só foram estimulados junto com outros DNs (G3: 20 DNs; G4: 159 DNs).

Mesmo protocolo da Sessão 1 v2 (experiments/phase3a_s1.py:main_v2): sinais `verified`, 3,25 s,
5 sementes (5000–5004), métrica de ritmo v2 congelada (terrario/vnc/rhythm.py:rhythm_v2), janela 0,25–3,25 s.
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/dados/terrario-virtual")
from terrario import ROOT  # noqa: E402

T_MS, T0_MS, MODE = 3250.0, 250.0, "verified"
_C = {}


def _init():
    from terrario.brain import hybrid
    _C["c"] = hybrid.load(1.0, sign_mode=MODE)


def _run(job):
    from terrario.brain.lif import ShiuLIF
    g, idx, rate, seed = job
    m = ShiuLIF(_C["c"], seed=seed)
    m.set_poisson(np.array(idx), rate)
    i, t = m.run(int(T_MS / m.dt), cap=1 << 24)
    return g, rate, seed, i, t * m.dt, len(np.unique(i))


def groups():
    from terrario.brain import banc, hybrid
    from terrario.brain import flywire
    c0 = hybrid.load(1.0)
    m = banc.load_meta()
    br = m[m["super_class"].isin(hybrid.BRIDGE)]
    b2fw = hybrid.match_bridges(br, fw := flywire.load("783"))
    dn = m[m["super_class"] == "descending"]
    out = {}
    for ct in ("DNg100", "DNb08"):
        ids = []
        for b in dn[dn.cell_type == ct].banc_888_id:
            b = int(b)
            ids.append(b2fw[b] if b in b2fw else c0.flyid2i[b])
        out[ct] = sorted(set(ids))
    return out


if __name__ == "__main__":
    from terrario.vnc.motor_map import LEGS
    from terrario.vnc.rhythm import rhythm_v2
    g = groups()
    print("grupos:", {k: len(v) for k, v in g.items()}, flush=True)
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    mn_all = mnt.h.to_numpy()
    rates = [float(r) for r in sys.argv[1:]] or [100.0, 200.0]
    jobs = [(k, v, r, 5000 + s) for k, v in g.items() for r in rates for s in range(5)]
    runs, act = {}, {}
    with ProcessPoolExecutor(4, initializer=_init) as ex:
        for k, rate, seed, i, t, nact in ex.map(_run, jobs):
            keep = np.isin(i, mn_all)
            runs.setdefault((k, rate), []).append((i[keep], t[keep]))
            act.setdefault((k, rate), []).append(nact)
    for (k, rate), rr in runs.items():
        mn_act = np.mean([len(np.unique(i)) for i, _ in rr])
        mn_rate = np.mean([len(i) for i, _ in rr]) / len(mn_all) / (T_MS / 1000)
        legs = {leg: rhythm_v2(rr, mnt[mnt.leg == leg].h.to_numpy(), T0_MS, T_MS) for leg in LEGS}
        print(json.dumps(dict(dn=k, rate_hz=rate, mn_active_of_391=round(float(mn_act), 1),
                              mn_mean_rate_hz=round(float(mn_rate), 3),
                              neurons_active=int(np.median(act[(k, rate)])),
                              legs_rhythmic_v2=sum(v["rhythmic"] for v in legs.values()),
                              peak_hz={l: v["peak_hz"] for l, v in legs.items()},
                              seeds_ok={l: v["n_seeds_ok"] for l, v in legs.items()},
                              max_prominence={l: round(max((p["prominence"] or 0) for p in v["per_seed"]), 2)
                                              for l, v in legs.items()})), flush=True)
