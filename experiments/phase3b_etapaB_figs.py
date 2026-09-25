"""Fase 3b, Etapa B: figura de diagnóstico (só resultados salvos). Saída: results/phase3b/s1/diagnostico_etapaB.png
(1) fração de neurônios ativos × taxa dos ORNs, real × embaralhados, com o limite (d) sem fonte;
(2) DNa02 E e D e DNa01 E e D (bilateral) × taxa, conectoma real."""
from __future__ import annotations
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from terrario import ROOT
R = ROOT / "results/phase3b"
C1, C2, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
ORDER, LAB = ["r20", "vin5", "r50", "r100"], ["20 Hz", "vinagre 5 %\n(42/22 Hz)", "50 Hz", "100 Hz"]


def main():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "axes.grid": True,
                         "grid.color": "#e6e6e3", "grid.linewidth": 0.6, "axes.edgecolor": MUTED})
    r = json.load(open(R / "rates.json"))
    a = pd.DataFrame(r["activity"])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    x = np.arange(4)
    s = a[(a.cond == "sim")]
    real = s[s.conn == "real"].set_index("rate").frac_active.reindex(ORDER) * 100
    ax[0].plot(x, real, "-o", color=C1, lw=2, ms=6, label="conectoma real")
    for k, e in enumerate(sorted(s[s.conn != "real"].conn.unique())):
        y = s[s.conn == e].set_index("rate").frac_active.reindex(ORDER) * 100
        ax[0].plot(x, y, "-o", color=MUTED, lw=1, ms=4, label="embaralhados (5)" if k == 0 else None)
    ax[0].axhline(100 * r["criteria"]["d_regime_limit_frac_active"], color=C2, ls="--", lw=1.2)
    ax[0].text(3.2, 100 * r["criteria"]["d_regime_limit_frac_active"] * 1.25, "limite (d), sem fonte", color=INK, ha="right")
    ax[0].set_yscale("log"); ax[0].set_xticks(x, LAB); ax[0].set_ylabel("neurônios ativos em 1 s (%)")
    ax[0].legend(frameon=False, loc="center right"); ax[0].set_title("Regime de atividade (bilateral)", loc="left")
    pr = r["per_rate"]
    for t, col in (("DNa02", C1), ("DNa01", C2)):
        ax[1].plot(x, [pr[k][f"sim_{t}_L_R"][0] for k in ORDER], "-o", color=col, lw=2, ms=6, label=f"{t} E")
        ax[1].plot(x, [pr[k][f"sim_{t}_L_R"][1] for k in ORDER], ":o", color=col, lw=2, ms=6, label=f"{t} D")
    ax[1].set_xticks(x, LAB); ax[1].set_ylabel("taxa por célula (Hz, mediana)")
    ax[1].legend(frameon=False, loc="center left", bbox_to_anchor=(1.0, 0.5)); ax[1].set_title("Viés do DNa02 esquerdo em todas as taxas; DNp09 e MDN = 0", loc="left")
    fig.savefig(R / "s1/diagnostico_etapaB.png", dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
