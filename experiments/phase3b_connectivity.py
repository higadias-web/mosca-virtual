"""Fase 3b, S1: conectividade de DM1/VA2 (ORN e PN) até DNa01/DNa02, esquerdo × direito (só grafo, sem simulação).

Pesos com sinal do conectoma usado no LIF (FlyWire 783, `syn_count` = Excitatory × Connectivity; sinal do pré).
Direto: Σ W(fonte→DN). 2 saltos: por intermediário k, E2 = Σ W⁺W⁺ + |W⁻||W⁻|, I2 = Σ W⁺|W⁻| + |W⁻|W⁺
(desinibição como +, linearização). Também confere o que o embaralhamento preservou.
Saída: results/phase3b/connectivity.json, connectivity.csv
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT
from terrario.brain import connectomes
from terrario.brain.shuffle import shuffled

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
SRC = ["ORN_DM1", "ORN_VA2", "DM1_lPN", "VA2_adPN"]
DST = ["DNa01", "DNa02"]


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    W = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n))  # linhas = pré
    Wp, Wn = W.maximum(0).tocsr(), (-W.minimum(0)).tocsr()
    rows, top = [], {}
    for dt in DST:
        for dside in ("left", "right"):
            d = c.idx(a[(a.cell_type == dt) & (a.side == dside)].root_id)
            vp = np.asarray(Wp[:, d].sum(1)).ravel()
            vn = np.asarray(Wn[:, d].sum(1)).ravel()
            for st in SRC:
                for sside in ("left", "right"):
                    s = c.idx(a[(a.cell_type == st) & (a.side == sside)].root_id)
                    e1, i1 = float(vp[s].sum()), float(vn[s].sum())
                    ep = np.asarray(Wp[s].sum(0)).ravel()   # saída excitatória somada das fontes, por k
                    en = np.asarray(Wn[s].sum(0)).ravel()
                    e2k = ep * vp + en * vn
                    i2k = ep * vn + en * vp
                    rows.append(dict(dn=dt, dn_side=dside, src=st, src_side=sside, n_src=len(s),
                                     direct_E=e1, direct_I=i1, hop2_E=float(e2k.sum()), hop2_I=float(i2k.sum()),
                                     n_intermediates=int(((e2k + i2k) > 0).sum())))
                    if st in ("DM1_lPN", "VA2_adPN"):
                        k = np.argsort(-(e2k + i2k))[:3]
                        top[f"{st}_{sside}->{dt}_{dside}"] = [(int(c.flyids[j]), float(e2k[j]), float(i2k[j])) for j in k if e2k[j] + i2k[j] > 0]
    df = pd.DataFrame(rows)
    df["hop2_net"] = df.hop2_E - df.hop2_I
    df.to_csv(ROOT / "results/phase3b/connectivity.csv", index=False)
    # soma por DN (todas as fontes de um tipo, os dois lados)
    summ = df.groupby(["dn", "dn_side", "src"])[["direct_E", "direct_I", "hop2_E", "hop2_I", "hop2_net"]].sum()
    print(summ.round(1).to_string())
    # embaralhamento: o que foi preservado
    chk = {}
    for sd in range(5):
        s = shuffled(c, sd)
        pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
        in_E0 = np.bincount(c.indices, weights=np.clip(c.syn_count, 0, None), minlength=c.n)
        in_E1 = np.bincount(s.indices, weights=np.clip(s.syn_count, 0, None), minlength=c.n)
        in_I0 = np.bincount(c.indices, weights=np.clip(-c.syn_count, 0, None), minlength=c.n)
        in_I1 = np.bincount(s.indices, weights=np.clip(-s.syn_count, 0, None), minlength=c.n)
        chk[f"emb{sd}"] = dict(
            weights_multiset_identical=bool(np.array_equal(np.sort(s.syn_count), np.sort(c.syn_count))),
            frac_inhibitory_edges=(float((c.syn_count < 0).mean()), float((s.syn_count < 0).mean())),
            out_degree_identical=bool(np.array_equal(np.diff(s.indptr), np.diff(c.indptr))),
            out_strength_signed_identical=bool(np.allclose(np.add.reduceat(s.syn_count, s.indptr[:-1]),
                                                           np.add.reduceat(c.syn_count, c.indptr[:-1]))),
            in_degree_identical=bool(np.array_equal(np.bincount(s.indices, minlength=c.n), np.bincount(c.indices, minlength=c.n))),
            in_E_strength_corr=float(np.corrcoef(in_E0, in_E1)[0, 1]),
            in_I_strength_corr=float(np.corrcoef(in_I0, in_I1)[0, 1]),
            edges_unchanged_frac=float((s.indices == c.indices).mean()))
    res = dict(summary=summ.reset_index().to_dict("records"), top_intermediates_PN=top, shuffle_check=chk)
    json.dump(res, open(ROOT / "results/phase3b/connectivity.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(chk, indent=1))
    print(json.dumps(top, indent=1))


if __name__ == "__main__":
    main()
