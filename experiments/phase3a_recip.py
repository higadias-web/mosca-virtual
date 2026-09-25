"""Fase 3a, Sessão 2: teste FUNCIONAL de inibição recíproca (hipótese da coativação).

Malha aberta, sinais "verified", vnc_scale 1. Para cada perna e junta (CTr, FTi):
  - fundo: G3 a 200 Hz o tempo todo (flexores e extensores coativos, como na Sessão 1);
  - de 1000 a 2000 ms, Poisson a 100 Hz nos 20 pré-motores excitatórios mais SELETIVOS para os
    flexores (entrada em F > 0 e em E = 0, ordenados por wF);
  - mede a taxa dos MNs extensores antes (250–1000) e durante (1000–2000), 5 sementes.
Se a inibição recíproca funciona no modelo, acionar o lado flexor deve REDUZIR os extensores.
Saída: results/phase3a/s2_reciprocal_inhibition.csv

Sessão 3, T2 (pré-registro FASE3_PLANO §7.4.4): `--direction E2F` espelha o teste. Estímulo nos 20
pré-motores excitatórios mais seletivos para os EXTENSORES (entrada em E > 0 e em F = 0, ordenados por
wE) e medida nos FLEXORES; mesmas sementes. As colunas flex_*/ext_* guardam os valores de cada lado.
Critério: flexores caem ≥ 25 % (média das 5 sementes) em ≥ 9 dos 12 pares, com extensores subindo;
flexores em 0 Hz antes = não avaliável (conta contra).
Saída: results/phase3a/s3_reciprocal_inhibition_E2F.csv
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT
from terrario.brain import hybrid
from terrario.brain.lif import ShiuLIF
from terrario.vnc.motor_map import ANTAGONISTS, LEGS

_S = {}


def _init():
    _S["c"] = hybrid.load(1.0, sign_mode="verified")


def targets(c, mnt, leg, jn, k=20, direction="F2E"):
    W = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n)).T.tocsr()
    a, b = ANTAGONISTS[jn]
    mem = mnt[(mnt.leg == leg) & (mnt.joint == jn)]
    F, E = mem[mem.role == a].h.to_numpy(), mem[mem.role == b].h.to_numpy()
    wF, wE = np.asarray(W[F].sum(0)).ravel(), np.asarray(W[E].sum(0)).ravel()
    if direction == "E2F":  # seletivos para os extensores
        wF, wE = wE, wF
    cand = np.flatnonzero((wF > 0) & (wE == 0))
    cand = cand[np.argsort(-wF[cand])][:k]
    return cand.tolist(), F.tolist(), E.tolist()


def _job(job):
    leg, jn, pm, F, E, g3, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    m.set_poisson(np.array(g3), 200.0)
    sl = m.poisson_slots(np.array(pm))
    i1, t1 = m.run(10000)
    m.set_rates(sl, 100.0)
    i2, t2 = m.run(10000)
    i = np.concatenate([i1, i2])
    t = np.concatenate([t1, t2]) * m.dt

    def rate(pop, w):
        s = np.isin(i, pop) & (t >= w[0]) & (t < w[1])
        return s.sum() / len(pop) / ((w[1] - w[0]) / 1000)
    return dict(leg=leg, joint=jn, seed=seed, flex_before=rate(F, (250, 1000)),
                flex_during=rate(F, (1000, 2000)), ext_before=rate(E, (250, 1000)),
                ext_during=rate(E, (1000, 2000)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", choices=["F2E", "E2F"], default="F2E")
    direction = ap.parse_args().direction
    c = hybrid.load(1.0, sign_mode="verified")
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    g3 = json.load(open(ROOT / "runs/phase3a/s1/dn_groups.json"))["G3_top20_drive"]
    jobs = []
    for leg in LEGS:
        for jn in ("CTr", "FTi"):
            pm, F, E = targets(c, mnt, leg, jn, direction=direction)
            jobs += [(leg, jn, pm, F, E, g3, 9000 + s) for s in range(5)]
    with ProcessPoolExecutor(4, initializer=_init) as ex:
        rows = list(ex.map(_job, jobs))
    df = pd.DataFrame(rows)
    out = "s2_reciprocal_inhibition.csv" if direction == "F2E" else "s3_reciprocal_inhibition_E2F.csv"
    df.to_csv(ROOT / "results/phase3a" / out, index=False)
    s = df.groupby(["leg", "joint"])[["flex_before", "flex_during", "ext_before", "ext_during"]].mean()
    s["ext_change_%"] = 100 * (s.ext_during - s.ext_before) / s.ext_before.replace(0, np.nan)
    s["flex_change_%"] = 100 * (s.flex_during - s.flex_before) / s.flex_before.replace(0, np.nan)
    print(s.round(2).to_string())
    if direction == "E2F":
        ok = (s["flex_change_%"] <= -25) & (s.ext_during > s.ext_before)
        print(f"pares com flexores −≥25 % e extensores subindo: {int(ok.sum())} de {len(s)} "
              f"(critério: ≥ 9) → {'FUNCIONA' if ok.sum() >= 9 else 'NÃO FUNCIONA'}")


if __name__ == "__main__":
    main()
