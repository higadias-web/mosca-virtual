"""Fase 3b: PN de DM1 × curva de Olsen, Bhandawat & Wilson 2010 (só spikes salvos; sem simulação).
Curva (Neuron 66:287, Eq. 1, s = 0 por ser estímulo de 1–2 glomérulos): PN = Rmax·ORN^1.5/(ORN^1.5 + σ^1.5),
DM1: Rmax = 144, σ = 44,8 spikes/s; ORN e PN como AUMENTO sobre o basal (média nos 500 ms de odor menos os 500 ms
anteriores). No modelo: basal = 0 (sem atividade de fundo) e janela = os 200 ms de odor (0–200 ms).
Entradas: intacto 0,1 % e 0,5 % (runs/phase3b/ablation/intact_*), 5 % (runs/phase3b/regime/real_persist_*);
ablação A (runs/phase3b/ablation/A_*). Saída: results/phase3b/olsen_compare.json"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from terrario import ROOT
from terrario.brain import connectomes

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
ORN_HZ = {"vin0.1": 7.0, "vin0.5": 16.0, "vin5": 42.0}
RMAX, SIGMA = 144.0, 44.8


def olsen(orn):
    return RMAX * orn ** 1.5 / (orn ** 1.5 + SIGMA ** 1.5)


def main():
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type"])
    a["root_id"] = a.root_id.astype("int64")
    pn = c.idx(a[a.cell_type == "DM1_lPN"].root_id)
    orn = c.idx(a[a.cell_type == "ORN_DM1"].root_id)
    res = dict(equation="PN = Rmax*ORN^1.5/(ORN^1.5 + sigma^1.5 + s^1.5), s=0; Rmax=144, sigma=44.8 (DM1)", conditions={})
    for cond, fmt in [("intacto", {"vin0.1": "ablation/intact_vin0.1_s{}", "vin0.5": "ablation/intact_vin0.5_s{}", "vin5": "regime/real_persist_vin5_s{}"}),
                      ("A", {d: f"ablation/A_{d}_s{{}}" for d in ORN_HZ})]:
        out = {}
        for d, f in fmt.items():
            pr, orr = [], []
            for s in range(1000, 1010):
                z = np.load(ROOT / "runs/phase3b" / (f.format(s) + ".npz"))
                t = z["t"] * 0.1
                i = z["i"][t < 200]
                pr.append(float(np.isin(i, pn).sum() / len(pn) / 0.2))
                orr.append(float(np.isin(i, orn).sum() / len(orn) / 0.2))
            out[d] = dict(ORN_DM1_measured=float(np.median(orr)), PN_DM1_model=float(np.median(pr)),
                          PN_DM1_model_min_max=(float(np.min(pr)), float(np.max(pr))),
                          PN_Olsen_predicted_at_nominal=olsen(ORN_HZ[d]), PN_Olsen_predicted_at_measured=olsen(float(np.median(orr))))
        res["conditions"][cond] = out
    json.dump(res, open(ROOT / "results/phase3b/olsen_compare.json", "w"), indent=1, ensure_ascii=False)
    for cond, out in res["conditions"].items():
        for d, v in out.items():
            print(f"{cond:8s} {d:7s} ORN medido {v['ORN_DM1_measured']:5.1f} Hz | PN modelo {v['PN_DM1_model']:6.1f} Hz "
                  f"({v['PN_DM1_model_min_max'][0]:.0f}–{v['PN_DM1_model_min_max'][1]:.0f}) | Olsen {v['PN_Olsen_predicted_at_measured']:5.1f} Hz")


if __name__ == "__main__":
    main()
