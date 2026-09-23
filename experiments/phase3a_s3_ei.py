"""Fase 3a, Sessão 3, T1: saldo excitação/inibição do caminho proprioceptor → MN (pré-registro §7.4.4).

Grafo do híbrido (vnc_scale 1), sinais "verified" e "verified_gluexc" (H6-g). Para cada perna e classe
proprioceptiva (claw, hook, club, placas de pelos, campaniformes; mesma seleção de
terrario/vnc/proprio.py) → MNs da MESMA perna (runs/phase3a/s1/leg_mn_table.csv):
  1 sinapse:  E1 = Σ W⁺(S→M), I1 = Σ |W⁻(S→M)|
  2 sinapses: produto dos pesos com sinal, por qualquer intermediário k:
              E2 = Σ W⁺(S→k)·W⁺(k→M) + |W⁻(S→k)|·|W⁻(k→M)|   (desinibição conta como +; linearização)
              I2 = Σ W⁺(S→k)·|W⁻(k→M)| + |W⁻(S→k)|·W⁺(k→M)
  saldo = (E − I)/(E + I). Alvos: todos os MNs da perna, e só flexores / só extensores da FTi.
Leitura pré-registrada: saldo de 2 sinapses de claw/hook passando de negativo (verified) a positivo
(gluexc) é coerente com a elevação da H6-g na Sessão 2; gera só hipótese (H6-g não tem base documentada).
Saída: results/phase3a/s3_ei_balance.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT
from terrario.brain import banc, hybrid
from terrario.vnc.motor_map import LEGS


def main():
    meta = banc.load_meta()
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    rows = []
    for mode in ("verified", "verified_gluexc"):
        c = hybrid.load(1.0, sign_mode=mode)
        hidx = hybrid.banc_index(c, meta)
        pr = _sensors(meta, hidx)  # só classe e perna; direções/limiares não entram no grafo
        W = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n))  # linhas = pré
        Wp, Wn = W.maximum(0).tocsr(), (-W.minimum(0)).tocsr()
        for leg in LEGS:
            m_leg = mnt[mnt.leg == leg]
            targets = {"all": m_leg.h.to_numpy(),
                       "FTi_flexor": m_leg[(m_leg.joint == "FTi") & (m_leg.role == "flexor")].h.to_numpy(),
                       "FTi_extensor": m_leg[(m_leg.joint == "FTi") & (m_leg.role == "extensor")].h.to_numpy()}
            for kind in ("claw", "hook", "club", "hair", "cs"):
                S = pr.h[(pr.kind == kind) & (pr.leg == leg)]
                if not len(S):
                    continue
                for tname, M in targets.items():
                    vp = np.asarray(Wp[:, M].sum(1)).ravel()
                    vn = np.asarray(Wn[:, M].sum(1)).ravel()
                    e1, i1 = float(vp[S].sum()), float(vn[S].sum())
                    e2 = float((Wp[S] @ vp).sum() + (Wn[S] @ vn).sum())
                    i2 = float((Wp[S] @ vn).sum() + (Wn[S] @ vp).sum())
                    rows.append(dict(mode=mode, leg=leg, kind=kind, target=tname, n_sensors=len(S),
                                     n_mn=len(M), E1=e1, I1=i1,
                                     bal1=(e1 - i1) / (e1 + i1) if e1 + i1 else np.nan,
                                     E2=e2, I2=i2, bal2=(e2 - i2) / (e2 + i2) if e2 + i2 else np.nan))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results/phase3a/s3_ei_balance.csv", index=False)
    piv = df[df.target == "all"].pivot_table(index=["kind", "leg"], columns="mode", values=["bal1", "bal2"])
    print(piv.round(3).to_string())
    print()
    agg = df.groupby(["mode", "kind", "target"])[["E1", "I1", "E2", "I2"]].sum()
    agg["bal1"] = (agg.E1 - agg.I1) / (agg.E1 + agg.I1)
    agg["bal2"] = (agg.E2 - agg.I2) / (agg.E2 + agg.I2)
    print(agg.round(3).to_string())


class _Sel:
    pass


def _sensors(meta, hidx):
    """Mesma seleção de proprioceptores de Proprioception.__init__ (classe e perna), sem direções."""
    from terrario.vnc.proprio import _leg
    sub = meta["cell_sub_class"].astype(str)
    rows = []
    for kind, pat in [("claw", "_claw_chordotonal_organ_neuron"), ("hook", "_hook_chordotonal_organ_neuron"),
                      ("club", "_club_chordotonal_organ_neuron"), ("hair", "_hair_plate_neuron"),
                      ("cs", "campaniform_sensillum_neuron")]:
        x = meta[sub.str.endswith(pat) & sub.str.contains("_leg_")]
        for bid, s, side in zip(x["banc_888_id"], sub[x.index], x["side"]):
            leg = _leg(s, side)
            if leg:
                rows.append((int(bid), kind, leg))
    h = hidx([r[0] for r in rows])
    keep = [k for k, v in enumerate(h) if v >= 0]
    o = _Sel()
    o.h = np.array([h[k] for k in keep], dtype=np.int64)
    o.kind = np.array([rows[k][1] for k in keep])
    o.leg = np.array([rows[k][2] for k in keep])
    return o


if __name__ == "__main__":
    main()
