"""Fase 3b, Etapa C: figura de diagnóstico (só dados salvos). Saída: results/phase3b/s1/diagnostico_etapaC.png
(1) persistência: spikes da rede por 10 ms, real × embaralhados (mediana de 10 sementes); (2) dose com fonte:
fração ativa; (3) causal: DNa02 E/D com e sem o AOTU019 E."""
from __future__ import annotations
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from terrario import ROOT
R, RUNS = ROOT / "results/phase3b", ROOT / "runs/phase3b/regime"
C1, C2, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"


def trace(prefix):
    hs = []
    for s in range(1000, 1010):
        t = np.load(RUNS / f"{prefix}_persist_vin5_s{s}.npz")["t"] * 0.1
        hs.append(np.histogram(t, bins=100, range=(0, 1000))[0])
    return np.median(hs, axis=0)


def main():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "axes.grid": True,
                         "grid.color": "#e6e6e3", "grid.linewidth": 0.6, "axes.edgecolor": MUTED})
    r = json.load(open(R / "regime.json"))
    fig, ax = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    x = np.arange(100) * 10 + 5
    ax[0].plot(x, trace("real") + 1, color=C1, lw=2, label="conectoma real")
    for k in range(5):
        ax[0].plot(x, trace(f"emb{k}") + 1, color=MUTED, lw=1, label="embaralhados (5)" if k == 0 else None)
    ax[0].axvspan(0, 200, color=C2, alpha=0.12, lw=0); ax[0].text(100, 2, "odor\n(vinagre 5 %)", ha="center", color=INK)
    ax[0].set_yscale("log"); ax[0].set_xlabel("tempo (ms)"); ax[0].set_ylabel("spikes da rede por 10 ms (+1)")
    ax[0].legend(frameon=False, loc="center right"); ax[0].set_title("Persistência: a rede real não desliga", loc="left")
    doses = ["vin0.1", "vin0.5", "vin5"]; lab = ["0,1 %\n(7/0 Hz)", "0,5 %\n(16/11 Hz)", "5 %\n(42/22 Hz)"]
    xd = np.arange(3)
    ax[1].plot(xd, [100 * r["dose"]["real"][d]["frac_active_median"] for d in doses], "-o", color=C1, lw=2, ms=6, label="real")
    for k in range(5):
        ax[1].plot(xd, [100 * r["dose"][f"emb{k}"][d]["frac_active_median"] for d in doses], "-o", color=MUTED, lw=1, ms=4,
                   label="embaralhados" if k == 0 else None)
    ax[1].axhline(3.14, color=C2, ls="--", lw=1.2); ax[1].text(2.1, 3.6, "estado alto (≥ 3,14 %)", color=INK, ha="right")
    ax[1].set_yscale("log"); ax[1].set_xticks(xd, lab); ax[1].set_ylabel("neurônios ativos (%)")
    ax[1].legend(frameon=False, loc="center right"); ax[1].set_title("Dose (vinagre, Faucher 2013): sem limiar", loc="left")
    cz = r["causal"]
    ax[2].bar([0, 1], [cz["DNa02_left_intact"], cz["DNa02_right_intact"]], 0.35, color=[C1, C1], label="intacto")
    ax[2].bar([0.4, 1.4], [cz["DNa02_left_silenced"], cz["DNa02_right_silenced"]], 0.35, color=[C2, C2], label="AOTU019 E silenciado")
    ax[2].set_xticks([0.2, 1.2], ["DNa02 E", "DNa02 D"]); ax[2].set_ylabel("taxa (Hz, mediana de 10 sementes)")
    ax[2].legend(frameon=False, loc="upper right"); ax[2].set_title("Causal: AOTU019 E cala o DNa02 D", loc="left")
    fig.savefig(R / "s1/diagnostico_etapaC.png", dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
