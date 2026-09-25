"""Fase 3b, Etapa D: figura de diagnóstico (só dados salvos). Saída: results/phase3b/s1/diagnostico_etapaD.png
(1) spikes da rede por 10 ms (mediana de 10 sementes), vinagre 5 % por 200 ms: intacto, A, B, C;
(2) fração ativa por classe durante o odor (0–200 ms), vinagre 5 %."""
from __future__ import annotations
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from terrario import ROOT
R = ROOT / "results/phase3b"
COL = {"intacto": "#2a78d6", "A: sem eLN→PN": "#eb6834", "B: sem exc. nos ORNs": "#1baf7a", "C: A+B": "#e87ba4"}
PATHS = {"intacto": ROOT / "runs/phase3b/regime/real_persist_vin5_s{}.npz", "A: sem eLN→PN": ROOT / "runs/phase3b/ablation/A_vin5_s{}.npz",
         "B: sem exc. nos ORNs": ROOT / "runs/phase3b/ablation/B_vin5_s{}.npz", "C: A+B": ROOT / "runs/phase3b/ablation/C_vin5_s{}.npz"}


def main():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "axes.grid": True,
                         "grid.color": "#e6e6e3", "grid.linewidth": 0.6, "axes.edgecolor": "#8a8a85"})
    r = json.load(open(R / "ablation.json"))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    x = np.arange(100) * 10 + 5
    for k, p in PATHS.items():
        h = np.median([np.histogram(np.load(str(p).format(s))["t"] * 0.1, bins=100, range=(0, 1000))[0] for s in range(1000, 1010)], axis=0)
        ax[0].plot(x, h + 1, color=COL[k], lw=2, label=k)
    ax[0].axvspan(0, 200, color="#8a8a85", alpha=0.12, lw=0)
    ax[0].set_yscale("log"); ax[0].set_xlabel("tempo (ms)"); ax[0].set_ylabel("spikes da rede por 10 ms (+1)")
    ax[0].legend(frameon=False, loc="lower right"); ax[0].set_title("Nenhuma ablação volta ao basal (vinagre 5 %, 200 ms)", loc="left")
    keys = {"intacto": "intact", "A: sem eLN→PN": "A", "B: sem exc. nos ORNs": "B", "C: A+B": "C"}
    cls = ["KC", "PN", "LN"]
    w = 0.2
    for j, (k, kk) in enumerate(keys.items()):
        v = [100 * r["conditions"][kk]["vin5"]["frac_active_by_class_0_200"][c] for c in cls]
        ax[1].bar(np.arange(3) + (j - 1.5) * w, v, w, color=COL[k], label=k)
    ax[1].set_xticks(range(3), ["células de Kenyon", "PNs", "LNs"]); ax[1].set_ylabel("% ativos durante o odor (0–200 ms)")
    ax[1].legend(frameon=False, loc="upper left"); ax[1].set_title("Com A, KCs e PNs se apagam; LNs seguem ativos", loc="left")
    fig.savefig(R / "s1/diagnostico_etapaD.png", dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
