"""Fase 3b, Etapa C: quem sustenta a atividade depois do odor (só spikes salvos; sem simulação).
Janela tardia [900, 1000) ms das execuções de persistência (conectoma real, 10 sementes): atividade por classe
e, para cada classe, de que classes vem a excitação (peso × taxa na janela), e a fração da inibição.
Saída: results/phase3b/loop_late.json"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import scipy.sparse as sp
from terrario import ROOT
from terrario.brain import connectomes
from experiments.phase3b_breakdown import group, ANN


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "super_class", "cell_class", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    a = a.set_index("root_id").reindex(c.flyids)
    g = np.array([group(r) for r in a.itertuples()])
    cnt = np.zeros(c.n)
    for s in range(1000, 1010):
        z = np.load(ROOT / f"runs/phase3b/regime/real_persist_vin5_s{s}.npz")
        t = z["t"] * 0.1
        cnt += np.bincount(z["i"][(t >= 900) & (t < 1000)], minlength=c.n)
    rate = cnt / 10 / 0.1  # Hz na janela de 100 ms
    W = sp.csr_matrix((c.syn_count, c.indices, c.indptr), shape=(c.n, c.n))  # linhas = pré
    Wr = sp.diags(rate) @ W                                                    # peso × taxa do pré
    groups = sorted(set(g))
    gi = {k: np.flatnonzero(g == k) for k in groups}
    act = {k: dict(n_active=int((rate[v] > 0).sum()), n=int(len(v)), rate_mean_active=float(rate[v][rate[v] > 0].mean()) if (rate[v] > 0).any() else 0.0)
           for k, v in gi.items()}
    drive = {}
    for post in groups:
        if act[post]["n_active"] == 0:
            continue
        col = Wr[:, gi[post]]
        tot_e = col.maximum(0).sum(); tot_i = -col.minimum(0).sum()
        src = {pre: float(col[gi[pre]].maximum(0).sum() / tot_e) for pre in groups if tot_e > 0}
        top = sorted(src.items(), key=lambda x: -x[1])[:4]
        drive[post] = dict(E=float(tot_e), I=float(tot_i), top_excitatory_sources=top)
    kc = gi["células de Kenyon"]
    json.dump(dict(activity_900_1000=act, drive=drive), open(ROOT / "results/phase3b/loop_late.json", "w"), indent=1, ensure_ascii=False)
    for k in sorted(act, key=lambda k: -act[k]["n_active"] * act[k]["rate_mean_active"])[:10]:
        d = drive.get(k, {})
        print(f"{k:28s} ativos {act[k]['n_active']:5d}/{act[k]['n']:6d} taxa {act[k]['rate_mean_active']:6.1f} Hz | E/I {d.get('E',0):.0f}/{d.get('I',0):.0f} | fontes E: " +
              ", ".join(f"{s} {f:.2f}" for s, f in d.get("top_excitatory_sources", [])))
    # KC → KC: fração da excitação dos KCs que vem de KCs
    print("KC→KC sinapses (contagem, só E):", int(W[kc][:, kc].maximum(0).sum()), " KC→KC arestas:", int((W[kc][:, kc] > 0).sum()))


if __name__ == "__main__":
    main()
