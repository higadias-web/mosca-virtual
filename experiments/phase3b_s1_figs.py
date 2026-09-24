"""Fase 3b, S1: figura de diagnóstico (só dados já salvos; não conta no prazo).
Painéis: (1) especificidade: DNa01/02 simétrico − controle, real × 5 embaralhados; (2) taxa por célula de
DNa01/DNa02 (E/D) por condição, conectoma real; (3) queda do DNa02 E no silenciamento cumulativo.
Saída: results/phase3b/s1/diagnostico_s1.png
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from terrario import ROOT

R = ROOT / "results/phase3b"
C1, C2, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"


def main():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                         "axes.grid": True, "grid.color": "#e6e6e3", "grid.linewidth": 0.6,
                         "axes.edgecolor": MUTED})
    lat = json.load(open(R / "laterality.json"))
    sil = json.load(open(R / "backtrace_silence.json"))
    fig, ax = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)

    a = ax[0]
    v1 = lat["V1"]
    vals = [v1["effect_real"]] + v1["effect_shuffled_each"]
    a.bar(range(6), vals, color=[C1] + [MUTED] * 5, width=0.6)
    a.axhline(0.5 * v1["effect_real"], color=C2, ls="--", lw=1.2)
    a.text(5.4, 0.5 * v1["effect_real"] + 0.6, "limite: 50 % do real", color=INK, ha="right")
    a.set_xticks(range(6), ["real"] + [f"emb{k}" for k in range(5)])
    a.set_ylabel("DNa01/02: odor − controle (Hz, mediana)")
    a.set_title("V1: especificidade (passa)", loc="left")

    a = ax[1]
    real = lat["per_connectome"]["real"]
    conds, lab = ["control", "sim", "esq", "dir"], ["controle", "simétrico", "só esq.", "só dir."]
    x = np.arange(len(conds))
    for k, (t, side, col, ls) in enumerate([("DNa02", "left", C1, "-"), ("DNa02", "right", C1, ":"),
                                            ("DNa01", "left", C2, "-"), ("DNa01", "right", C2, ":")]):
        y = [real[t][f"{c}_{side}"] for c in conds]
        a.plot(x, y, ls, marker="o", color=col, lw=2, ms=6, label=f"{t} {'E' if side == 'left' else 'D'}")
    a.set_xticks(x, lab); a.set_ylabel("taxa por célula (Hz, mediana)")
    a.legend(frameon=False, loc="upper left")
    a.set_title("V2: nenhum DN carrega o lado", loc="left")

    a = ax[2]
    base = np.median([sil["intact"][s]["DNa02_left"] for s in sil["intact"]])
    names = ["intacto", "PS013 E", "+ DNae005 E", "+ LAL081 E"]
    meds = [base] + [np.median([v["per_seed"][s]["DNa02_left"] for s in v["per_seed"]]) for v in sil["conditions"].values()]
    a.bar(range(4), meds, color=[C1, MUTED, MUTED, C2], width=0.6)
    a.axhline(0.5 * base, color=INK, ls="--", lw=1)
    a.text(3.4, 0.5 * base + 1, "−50 %", color=INK, ha="right")
    a.set_xticks(range(4), names); a.set_ylabel("DNa02 E (Hz, mediana de 5 sementes)")
    a.set_title("Silenciamento cumulativo: só as três juntas passam", loc="left")
    fig.savefig(R / "s1/diagnostico_s1.png", dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
