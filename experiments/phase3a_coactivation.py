"""Fase 3a: base estrutural da coativação flexor × extensor (hipótese registrada na Sessão 2).

No híbrido (sinais "verified", vnc_scale 1), para cada perna e junta (CTr, FTi):
  F, E = MNs flexores e extensores (terrario/vnc/motor_map.py).
  Pré-motores = neurônios com sinapse direta em F ∪ E.
  - compartilhamento excitatório: Σ_p min(wF⁺, wE⁺) / Σ_p wF⁺, sobre os pré-motores excitatórios.
    1 = toda a excitação dos flexores vem de neurônios que excitam igualmente os extensores;
  - seletividade inibitória: média ponderada de |wF − wE| / (wF + wE) nos inibitórios.
    1 = cada inibitório inibe só um dos lados (substrato de inibição recíproca);
  - acionamento pelos DNs de G3 em 2 sinapses excitatórias: D_F e D_E; razão D_F / D_E.
Saída: results/phase3a/s2_coactivation_structure.csv
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT
from terrario.brain import hybrid
from terrario.vnc.motor_map import ANTAGONISTS, LEGS


def main():
    c = hybrid.load(1.0, sign_mode="verified")
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    g3 = json.load(open(ROOT / "runs/phase3a/s1/dn_groups.json"))["G3_top20_drive"]
    W = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n))
    Wp = W.maximum(0)
    Wt = W.T.tocsr()  # linhas = pós
    rows = []
    for leg in LEGS:
        for jn in ("CTr", "FTi"):
            a, b = ANTAGONISTS[jn]
            mem = mnt[(mnt.leg == leg) & (mnt.joint == jn)]
            F = mem[mem.role == a].h.to_numpy()
            E = mem[mem.role == b].h.to_numpy()
            wF = np.asarray(Wt[F].sum(0)).ravel()   # entrada total de cada pré em F (com sinal)
            wE = np.asarray(Wt[E].sum(0)).ravel()
            pre = np.flatnonzero((wF != 0) | (wE != 0))
            exc = pre[(wF[pre] > 0) | (wE[pre] > 0)]
            inh = pre[(wF[pre] < 0) | (wE[pre] < 0)]
            fp, ep = np.clip(wF[exc], 0, None), np.clip(wE[exc], 0, None)
            share = float(np.minimum(fp, ep).sum() / fp.sum()) if fp.sum() else None
            fi, ei = -np.clip(wF[inh], None, 0), -np.clip(wE[inh], None, 0)
            tot = fi + ei
            sel = float((np.abs(fi - ei)).sum() / tot.sum()) if tot.sum() else None
            dF = float((Wp[g3][:, F].sum() + (Wp[g3] @ Wp[:, F]).sum() / 100))
            dE = float((Wp[g3][:, E].sum() + (Wp[g3] @ Wp[:, E]).sum() / 100))
            rows.append(dict(leg=leg, joint=jn, n_flex=len(F), n_ext=len(E), n_premotor=len(pre),
                             n_exc=len(exc), n_inh=len(inh), exc_sharing=share,
                             inh_selectivity=sel, g3_drive_flex=dF, g3_drive_ext=dE,
                             g3_flex_over_ext=dF / dE if dE else None))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results/phase3a/s2_coactivation_structure.csv", index=False)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
