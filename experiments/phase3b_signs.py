"""Fase 3b: sinais do modelo × anotação no lobo antenal (só grafo + spikes salvos; sem simulação).
Sinal do modelo = coluna Excitatory do Connectivity_783.parquet do Shiu (por neurônio). Saída: results/phase3b/signs_AL.json"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import scipy.sparse as sp
from terrario import ROOT
from terrario.brain import connectomes
from experiments.phase3b_ablation import ablated

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_class", "cell_type", "top_nt", "known_nt", "super_class"])
    a["root_id"] = a.root_id.astype("int64")
    a = a.set_index("root_id").reindex(c.flyids)
    pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
    sign = np.zeros(c.n)
    sign[pre[c.syn_count > 0]] = 1
    sign[pre[c.syn_count < 0]] = -1
    # known_nt: lista separada por ";" ou ","; "X-negative" significa NÃO X (ex.: "acetylcholine; gaba-negative")
    def positives(v):
        if not isinstance(v, str):
            return set()
        toks = [t.strip().lower() for t in v.replace(";", ",").split(",")]
        return {t.split()[0] for t in toks if t and not t.endswith("-negative")}
    pos = a.known_nt.map(positives)
    known_inh = pos.map(lambda p: bool(p & {"gaba", "glutamate"})).to_numpy()
    known_exc = pos.map(lambda p: "acetylcholine" in p).to_numpy()
    known_other = pos.map(lambda p: "octopamine" in p).to_numpy()
    ln = (a.cell_class == "ALLN").to_numpy()
    kbad = known_inh | known_other
    eln148 = ln & (sign > 0) & ~kbad
    div18 = ln & (sign > 0) & kbad
    res = dict(n_eLN148=int(eln148.sum()), n_div18=int(div18.sum()), div18_in_eLN148=int((eln148 & div18).sum()),
               div18_types=a.cell_type[div18].value_counts().to_dict(), div18_known=a.known_nt[div18].value_counts().to_dict())
    # fração da excitação que chega aos 148 eLNs vinda dos 18, na janela tardia (900–1000 ms)
    for label, cc, fmt in [("intacto", c, "runs/phase3b/regime/real_persist_vin5_s{}.npz"),
                           ("A", ablated(c, "A"), "runs/phase3b/ablation/A_vin5_s{}.npz")]:
        cnt = np.zeros(c.n)
        for s in range(1000, 1010):
            z = np.load(ROOT / fmt.format(s)); t = z["t"] * 0.1
            cnt += np.bincount(z["i"][(t >= 900) & (t < 1000)], minlength=c.n)
        rate = cnt / 10 / 0.1
        W = sp.csr_matrix((cc.syn_count, cc.indices, cc.indptr), shape=(c.n, c.n))
        E = (sp.diags(rate) @ W)[:, np.flatnonzero(eln148)].maximum(0)
        tot = E.sum()
        res[f"excitation_onto_eLN148_{label}"] = dict(total=float(tot), from_eLN148=float(E[np.flatnonzero(eln148)].sum() / tot),
                                                      from_div18=float(E[np.flatnonzero(div18)].sum() / tot),
                                                      div18_rates_Hz=[float(x) for x in rate[div18]])
    # divergências no lobo antenal: sinal do modelo × known_nt (onde conhecido) e × top_nt da anotação
    al = ln | (a.cell_class == "ALPN").to_numpy() | a.cell_type.astype(str).str.startswith("ORN_").to_numpy() | (a.cell_class == "ALON").to_numpy()
    tn = a.top_nt.astype(str)
    top_inh = tn.isin(["gaba", "glutamate"]).to_numpy()
    rows = []
    for cls in ["ALLN", "ALPN", "ALON", "ORN"]:
        m = al & ((a.cell_type.astype(str).str.startswith("ORN_")).to_numpy() if cls == "ORN" else (a.cell_class == cls).to_numpy()) & (sign != 0)
        rows.append(dict(cls=cls, n=int(m.sum()),
                         model_exc_known_inh=int((m & (sign > 0) & known_inh).sum()),
                         model_inh_known_exc=int((m & (sign < 0) & known_exc).sum()),
                         model_exc_top_inh=int((m & (sign > 0) & top_inh).sum()),
                         model_inh_top_exc=int((m & (sign < 0) & ~top_inh & (tn != "nan").to_numpy()).sum()),
                         n_known=int((m & (known_inh | known_exc | known_other)).sum())))
    res["AL_divergences"] = rows
    mi = al & (sign < 0) & known_exc
    res["AL_model_inh_known_exc_types"] = a.cell_type[mi].value_counts().head(10).to_dict()
    me = al & (sign > 0) & top_inh
    res["AL_model_exc_top_inh_types"] = a.cell_type[me].value_counts().head(10).to_dict()
    json.dump(res, open(ROOT / "results/phase3b/signs_AL.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
