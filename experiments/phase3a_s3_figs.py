"""Fase 3a, Sessão 3: figura de diagnóstico (não conta no prazo). Lê só resultados já gravados.

Painéis: (1) checagem da unidade (altura do tórax × multiplicador da rigidez); (2) limites nas 3 tentativas
(violação no teste (c), lida a 1 kHz, por grupo); (3) "direct_dt": pico no impacto × média na sustentação;
(4) inibição recíproca nos dois sentidos (variação do lado antagonista, média de 5 sementes).
Saída: results/phase3a/s3/diagnostico_s3.png
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from terrario import ROOT

R = ROOT / "results/phase3a"
C1, C2, INK, MUTED = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
Y = 0.05


def main():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                         "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK,
                         "ytick.color": INK, "axes.grid": True, "grid.color": "#e6e6e3", "grid.linewidth": 0.6})
    fig, ax = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)

    u = json.load(open(R / "s3_unitcheck.json"))
    g = pd.DataFrame(u["grid"])
    a = ax[0, 0]
    a.plot(g.m, g.thorax_z1, "-o", color=C1, lw=2, ms=6)
    for _, r in g[~g.supports].iterrows():
        a.annotate("corpo toca o chão", (r.m, r.thorax_z1), xytext=(6, -12), textcoords="offset points", color=INK)
    a.axvspan(10, 160, color=MUTED, alpha=0.12, lw=0)
    a.axvline(40, color=MUTED, ls="--", lw=1)
    a.text(42, g.thorax_z1.min(), "×40 do artigo", color=INK)
    a.text(11, g.thorax_z1.max(), "faixa pré-registrada\n[10, 160]", color=INK, va="top")
    a.set_xscale("log"); a.set_xlabel("multiplicador da rigidez de Wang et al. (m)")
    a.set_ylabel("altura do tórax em 1 s (mm)")
    a.set_title(f"Checagem da unidade: m* = {u['m_star']:g} (leitura mN·m/° caiu)", loc="left")

    a = ax[0, 1]
    tries = [("padrão (0,02 s)", R / "s3_validation_cd.csv"),
             ("std2dt (0,2 ms)", R / "s3_validation_std2dt/s3_validation_cd.csv"),
             ("direct_dt", R / "s3_validation_direct_dt/s3_validation_cd.csv")]
    rng = np.random.default_rng(0)
    for k, (lab, f) in enumerate(tries):
        v = pd.read_csv(f).viol_act1.to_numpy()
        a.scatter(k + rng.uniform(-0.15, 0.15, len(v)), v, s=14, color=C1, alpha=0.7, lw=0)
        a.text(k, v.max() * 1.25, f"{(v > Y).sum()}/66 > Y", ha="center", color=INK)
    a.axhline(Y, color=C2, lw=1.5); a.text(0.5, Y * 1.15, "Y = 0,05 rad", color=INK, ha="center")
    a.set_yscale("log"); a.set_xticks(range(3), [t[0] for t in tries])
    a.set_ylabel("violação do limite, ativação 1 (rad, 1 kHz)")
    a.set_title("Teste (c) nas 3 tentativas", loc="left")

    a = ax[1, 0]
    d = pd.read_csv(R / "s3_validation_direct_dt/s3_validation_cd.csv")
    x = np.arange(len(d)); o = np.argsort(d.impact_peak_act1.to_numpy())
    a.bar(x - 0.2, d.impact_peak_act1.to_numpy()[o], 0.4, color=C1, label="pico no impacto (0–50 ms)")
    a.bar(x + 0.2, d.sustain_mean_act1.to_numpy()[o], 0.4, color=C2, label="média na sustentação (100–200 ms)")
    a.axhline(Y, color=INK, lw=1, ls="--"); a.text(1, Y * 1.05, "Y", color=INK)
    a.set_xlabel("grupo muscular (ordenado pelo pico)"); a.set_xticks([])
    a.set_ylabel("violação do limite (rad, por passo)")
    a.legend(frameon=False, loc="upper left")
    a.set_title("direct_dt: o batente segura; o impacto passa de Y", loc="left")

    a = ax[1, 1]
    f2e = pd.read_csv(R / "s2_reciprocal_inhibition.csv").groupby(["leg", "joint"]).mean(numeric_only=True)
    e2f = pd.read_csv(R / "s3_reciprocal_inhibition_E2F.csv").groupby(["leg", "joint"]).mean(numeric_only=True)
    ch1 = 100 * (f2e.ext_during - f2e.ext_before) / f2e.ext_before
    ch2 = 100 * (e2f.flex_during - e2f.flex_before) / e2f.flex_before
    lab = [f"{l.upper()} {j}" for l, j in ch1.index]
    x = np.arange(len(lab))
    a.bar(x - 0.2, ch1.to_numpy(), 0.4, color=C1, label="flexores acionados → extensores (S2)")
    a.bar(x + 0.2, ch2.reindex(ch1.index).to_numpy(), 0.4, color=C2, label="extensores acionados → flexores (S3)")
    a.axhline(-25, color=INK, lw=1, ls="--"); a.text(-0.6, -23, "critério −25 %", ha="left", color=INK, fontsize=8)
    a.set_xticks(x, lab, rotation=45, ha="right"); a.set_ylabel("variação do antagonista (%)")
    a.legend(frameon=False, loc="lower left")
    a.set_title("Inibição recíproca nos dois sentidos", loc="left")
    fig.savefig(R / "s3/diagnostico_s3.png", dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
