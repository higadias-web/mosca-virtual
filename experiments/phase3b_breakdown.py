"""Fase 3b: quebra dos neurônios ativos por classe (só spikes salvos; vinagre 5 %, bilateral, conectoma real).
Entrada: runs/phase3b/rates/real_vin5_sim_s*.npz (10 sementes). Saída: results/phase3b/breakdown_vin5.json/.csv"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from terrario import ROOT
from terrario.brain import connectomes

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"


def group(r):
    ct, cc, sc = str(r.cell_type), str(r.cell_class), str(r.super_class)
    if cc == "Kenyon_Cell" or ct.startswith("KC"):
        return "células de Kenyon"
    if ct == "APL":
        return "APL"
    if cc == "MBON" or ct.startswith("MBON"):
        return "MBON"
    if cc == "DAN":
        return "DAN"
    if cc.startswith("LH") or ct.startswith("LH"):
        return "corno lateral (LH*)"
    if ct.startswith("LAL") or ct.startswith("AOTU"):
        return "LAL/AOTU"
    if cc == "ALPN":
        return "PNs do lobo antenal"
    if cc == "ALLN":
        return "LNs do lobo antenal"
    if sc == "sensory":
        return "sensoriais"
    if sc == "descending":
        return "descendentes"
    return f"demais ({sc})"


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "super_class", "cell_class", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    a = a.set_index("root_id").reindex(c.flyids)
    grp = np.array([group(r) for r in a.itertuples()])
    cnt = np.zeros(c.n)
    for s in range(1000, 1010):
        cnt += np.bincount(np.load(ROOT / f"runs/phase3b/rates/real_vin5_sim_s{s}.npz")["i"], minlength=c.n)
    rate = cnt / 10.0
    df = pd.DataFrame(dict(group=grp, rate=rate, active=rate > 0))
    tab = df.groupby("group").agg(n_total=("rate", "size"), n_active=("active", "sum"),
                                  rate_mean_active=("rate", lambda x: x[x > 0].mean() if (x > 0).any() else 0.0),
                                  spikes_per_s=("rate", "sum")).sort_values("spikes_per_s", ascending=False)
    tab["frac_active"] = tab.n_active / tab.n_total
    tab["share_of_spikes"] = tab.spikes_per_s / tab.spikes_per_s.sum()
    tab.to_csv(ROOT / "results/phase3b/breakdown_vin5.csv")
    ids = {k: [int(i) for i in np.flatnonzero((a.cell_type == t).to_numpy() & (a.side == sd).to_numpy())]
           for k, (t, sd) in {"APL_left": ("APL", "left"), "APL_right": ("APL", "right"),
                              "AOTU019_left": ("AOTU019", "left"), "AOTU019_right": ("AOTU019", "right")}.items()}
    special = {k: [float(rate[i]) for i in v] for k, v in ids.items()}
    json.dump(dict(table=tab.reset_index().to_dict("records"), special=special,
                   total_active=int((rate > 0).sum()), total_spikes_per_s=float(rate.sum())),
              open(ROOT / "results/phase3b/breakdown_vin5.json", "w"), indent=1, ensure_ascii=False)
    pd.set_option("display.width", 200)
    print(tab.round(3).to_string()); print(special)


if __name__ == "__main__":
    main()
