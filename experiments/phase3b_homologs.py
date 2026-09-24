"""Fase 3b, Etapa B: homólogos e entradas do DNa02 (só grafo + spikes já salvos; nenhuma simulação).

1. Pesos diretos (contagem com sinal, a do LIF) de PS013, DNae005 e LAL081 (E e D) em DNa02 E e D.
2. Com os spikes salvos do odor bilateral a 100 Hz (runs/phase3b/backtrace/odor_s*.npz, 5 sementes): as
   entradas ativas sobre DNa02 D e DNa02 E, com contribuição peso × taxa; soma excitatória e inibitória
   e as 10 maiores inibitórias sobre o DNa02 D.
Saída: results/phase3b/homologs_weights.json
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import scipy.sparse as sp

from terrario import ROOT
from terrario.brain import connectomes

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side", "top_nt"])
    a["root_id"] = a.root_id.astype("int64")
    ai = a.set_index("root_id")

    def one(t, sd):
        return int(c.idx(a[(a.cell_type == t) & (a.side == sd)].root_id)[0])

    Wt = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n)).T.tocsr()  # linhas = pós
    dn = {sd: one("DNa02", sd) for sd in ("left", "right")}
    w = {}
    for t in ("PS013", "DNae005", "LAL081"):
        for s_src in ("left", "right"):
            for s_dn in ("left", "right"):
                w[f"{t}_{s_src}->DNa02_{s_dn}"] = float(Wt[dn[s_dn], one(t, s_src)])
    rate = np.zeros(c.n)
    for s in range(1000, 1005):
        rate += np.bincount(np.load(ROOT / f"runs/phase3b/backtrace/odor_s{s}.npz")["i"], minlength=c.n)
    rate /= 5.0
    inputs = {}
    for sd, k in dn.items():
        row = Wt.getrow(k)
        contrib = row.data * rate[row.indices]
        e, i = contrib[contrib > 0].sum(), -contrib[contrib < 0].sum()
        inh = sorted([(int(j), float(wt), float(x)) for j, wt, x in zip(row.indices, row.data, contrib) if x < 0],
                     key=lambda z: z[2])[:10]

        def lab(j):
            f = int(c.flyids[j])
            return (str(ai.loc[f].cell_type), str(ai.loc[f].side), str(ai.loc[f].top_nt)) if f in ai.index else (None,) * 3

        inputs[f"DNa02_{sd}"] = dict(rate=float(rate[k]), n_presyn=int(len(row.indices)),
                                     n_presyn_active=int((rate[row.indices] > 0).sum()),
                                     E_total=float(e), I_total=float(i), net=float(e - i),
                                     top_inhibitory=[dict(type=lab(j)[0], side=lab(j)[1], nt=lab(j)[2],
                                                          rate=float(rate[j]), weight=wt, contribution=x)
                                                     for j, wt, x in inh])
    res = dict(direct_weights=w, active_inputs_odor100=inputs)
    json.dump(res, open(ROOT / "results/phase3b/homologs_weights.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(w, indent=1))
    for k, v in inputs.items():
        print(k, {kk: v[kk] for kk in ("rate", "n_presyn", "n_presyn_active", "E_total", "I_total", "net")})
        for x in v["top_inhibitory"]:
            print("   ", x)


if __name__ == "__main__":
    main()
