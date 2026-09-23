"""Fase 3a: figuras de diagnóstico por sessão e verificações que acompanham a métrica de ritmo.

Para cada execução escolhida (runs/phase3a/<sessão>/<modo>_<grupo>_<taxa>.npz):
  - raster dos MNs de perna agrupados por perna e por junta (cor = junta);
  - espectro da taxa populacional de cada perna, com o nível p99 dos surrogados na banda 3–20 Hz.
Verificações (em results/phase3a/<sessão>_checks.csv):
  - excesso de banda larga: potência observada / média dos surrogados, dentro da banda (3–20 Hz)
    e fora dela (25–100 Hz). Se o excesso é igual dentro e fora, é correlação comum de banda
    larga (entrada compartilhada), não um ritmo;
  - antifase: correlação (bins de 10 ms) entre as taxas de MNs flexores e extensores da mesma
    junta (CTr, FTi) de cada perna. Marcha exige r < 0 (alternância).

Paleta: slots 1–5 da paleta de referência da skill dataviz (validada: CVD e visão normal passam;
contraste < 3:1 em 3 cores, por isso cada grupo tem rótulo de texto no eixo).

Uso: uv run python -m experiments.phase3a_figs --session s1 --runs predicted_G3_top20_drive_200 ...
"""

from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from terrario import ROOT
from terrario.vnc.motor_map import ANTAGONISTS, JOINTS, LEGS
from terrario.vnc.rhythm import BAND_HZ, rhythm_test

JOINT_COLOR = dict(zip(JOINTS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
T_MS, T0_MS = 1500.0, 250.0


def _style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)


def raster(run, mnt, out):
    z = np.load(run)
    T = max(T_MS, float(np.ceil(z["t"].max() / 250.0) * 250.0)) if len(z["t"]) else T_MS
    pos = {h: k for k, h in enumerate(mnt.h)}
    y = np.array([pos[i] for i in z["i"]])
    col = [JOINT_COLOR.get(j, INK2) for j in mnt.joint.to_numpy()[y]]
    fig, ax = plt.subplots(figsize=(11, 7), facecolor=SURF)
    _style(ax)
    ax.axvspan(0, T, color=GRID, alpha=0.35, lw=0)
    ax.scatter(z["t"], y, s=2.5, c=col, marker="|", linewidths=0.8)
    # separadores e rótulos por perna e junta
    for leg in LEGS:
        rows = np.where(mnt.leg.to_numpy() == leg)[0]
        ax.axhline(rows.min() - 0.5, color=INK2, lw=0.6)
        ax.text(-40, rows.mean(), leg.upper(), ha="right", va="center", fontsize=10, color=INK,
                fontweight="bold")
        for jn in JOINTS:
            r = rows[mnt.joint.to_numpy()[rows] == jn]
            if len(r):
                ax.text(T + 10, r.mean(), jn, ha="left", va="center", fontsize=6.5, color=INK2)
    ax.set_xlim(-5, T + 60)
    ax.set_ylim(len(mnt), -1)
    ax.set_yticks([])
    ax.set_xlabel("tempo (ms) — estímulo Poisson nos DNs durante todo o intervalo", color=INK2, fontsize=9)
    handles = [plt.Line2D([], [], color=c, marker="|", ls="", markersize=10, label=j)
               for j, c in JOINT_COLOR.items()]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=5, frameon=False,
              fontsize=8, labelcolor=INK2)
    ax.set_title(f"MNs de perna (391): {run.stem}", loc="left", color=INK, fontsize=11, pad=22)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def spectra(run, mnt, out):
    z = np.load(run)
    fig, axs = plt.subplots(2, 3, figsize=(11, 5.5), sharex=True, facecolor=SURF)
    for ax, leg in zip(axs.T.ravel(), LEGS):
        _style(ax)
        r = rhythm_test(z["i"], z["t"], mnt[mnt.leg == leg].h.to_numpy(), T0_MS, T_MS)
        ax.set_title(f"{leg.upper()}  ({r['n_active']}/{r['n']} MNs, {r['n_spikes']} spikes)",
                     loc="left", fontsize=9, color=INK)
        if r.get("freqs") is None:
            ax.text(0.5, 0.5, "< 20 spikes", transform=ax.transAxes, ha="center", color=INK2, fontsize=9)
            continue
        f, p = r["freqs"], r["spectrum"]
        ax.axvspan(*BAND_HZ, color=GRID, alpha=0.5, lw=0)
        ax.plot(f[1:], p[1:], color="#2a78d6", lw=1.5)
        ax.axhline(r["p99"], xmin=0, xmax=1, color=INK2, ls="--", lw=1)
        ax.plot([r["peak_hz"]], [r["power"]], "o", color="#eb6834", ms=6, mec=SURF, mew=1.5)
        verdict = "rítmico" if r["rhythmic"] else "não rítmico"
        ax.text(0.98, 0.92, f"pico {r['peak_hz']:.1f} Hz · {r['ratio']:.2f}× p99 · {verdict}",
                transform=ax.transAxes, ha="right", fontsize=7.5, color=INK2)
        ax.set_xlim(0, 60)
        ax.set_yscale("log")
    for ax in axs[-1]:
        ax.set_xlabel("frequência (Hz); faixa cinza = banda de passada 3–20 Hz", fontsize=8, color=INK2)
    fig.suptitle(f"Espectro da taxa populacional por perna (linha tracejada = p99 de 200 surrogados): "
                 f"{run.stem}", x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def checks(run, mnt):
    z = np.load(run)
    i, t = z["i"], z["t"]
    rows = []
    for leg in LEGS:
        mem = mnt[mnt.leg == leg]
        # banda larga: observado / média dos surrogados, dentro e fora da banda
        sel = np.isin(i, mem.h) & (t >= T0_MS)
        if sel.sum() < 20:
            rows.append(dict(run=run.stem, leg=leg, n_spikes=int(sel.sum())))
            continue
        tt, ii = t[sel] - T0_MS, i[sel]
        T = T_MS - T0_MS
        nb = int(T / 5)
        rng = np.random.default_rng(0)
        c, _ = np.histogram(tt, bins=nb, range=(0, T))
        f = np.fft.rfftfreq(nb, 0.005)
        po = np.abs(np.fft.rfft(c - c.mean())) ** 2
        u, inv = np.unique(ii, return_inverse=True)
        ps = np.zeros_like(po)
        for _ in range(100):
            cs, _ = np.histogram((tt + rng.uniform(0, T, len(u))[inv]) % T, bins=nb, range=(0, T))
            ps += np.abs(np.fft.rfft(cs - cs.mean())) ** 2 / 100
        inb = (f >= BAND_HZ[0]) & (f <= BAND_HZ[1])
        outb = (f >= 25) & (f <= 100)
        row = dict(run=run.stem, leg=leg, n_spikes=int(sel.sum()),
                   excess_in_band=float(po[inb].mean() / ps[inb].mean()),
                   excess_out_band=float(po[outb].mean() / ps[outb].mean()))
        # antifase flexor × extensor (bins de 10 ms)
        for jn in ("CTr", "FTi"):
            a, b = ANTAGONISTS[jn]
            ha = mem[(mem.joint == jn) & (mem.role == a)].h
            hb = mem[(mem.joint == jn) & (mem.role == b)].h
            ca, _ = np.histogram(t[np.isin(i, ha) & (t >= T0_MS)], bins=int(T / 10), range=(T0_MS, T_MS))
            cb, _ = np.histogram(t[np.isin(i, hb) & (t >= T0_MS)], bins=int(T / 10), range=(T0_MS, T_MS))
            row[f"{jn}_flex_ext_r"] = float(np.corrcoef(ca, cb)[0, 1]) if ca.std() > 0 and cb.std() > 0 else None
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s1")
    ap.add_argument("--runs", nargs="+", required=True)
    args = ap.parse_args()
    d = ROOT / "runs" / "phase3a" / args.session
    res = ROOT / "results" / "phase3a" / args.session
    res.mkdir(parents=True, exist_ok=True)
    mnt = pd.read_csv(d / "leg_mn_table.csv")
    allrows = []
    for name in args.runs:
        run = d / f"{name}.npz"
        raster(run, mnt, res / f"raster_{name}.png")
        spectra(run, mnt, res / f"spectrum_{name}.png")
        allrows += checks(run, mnt)
    df = pd.DataFrame(allrows)
    df.to_csv(res / "checks.csv", index=False)
    print(df.round(2).to_string())


if __name__ == "__main__":
    main()


def spectra_v2(cond: str, session: str = "s1", seeds=range(5000, 5005), t_ms: float = 3250.0):
    """Espectros de Welch (métrica v2) de uma condição: 5 sementes por perna, com a proeminência."""
    from terrario.vnc.rhythm import PROMINENCE, welch_peak
    d = ROOT / "runs" / "phase3a" / session
    res = ROOT / "results" / "phase3a" / session
    mnt = pd.read_csv(d / "leg_mn_table.csv")
    runs = [np.load(d / f"v2_{cond}_s{s}.npz") for s in seeds]
    fig, axs = plt.subplots(2, 3, figsize=(11, 5.5), sharex=True, facecolor=SURF)
    out = []
    for ax, leg in zip(axs.T.ravel(), LEGS):
        _style(ax)
        mem = mnt[mnt.leg == leg].h.to_numpy()
        proms = []
        for z in runs:
            w = welch_peak(z["i"], z["t"], mem, T0_MS, t_ms)
            if w.get("welch") is None:
                continue
            ax.plot(w["freqs"][1:], w["welch"][1:], color="#2a78d6", lw=1, alpha=0.6)
            proms.append(w["prominence"] or 0.0)
        ax.axvspan(*BAND_HZ, color=GRID, alpha=0.5, lw=0)
        ax.set_yscale("log")
        ax.set_xlim(0, 60)
        pm = max(proms) if proms else 0.0
        out.append((leg, pm))
        ax.set_title(f"{leg.upper()}: proeminência máx. {pm:.1f} (limiar {PROMINENCE:g})", loc="left",
                     fontsize=9, color=INK)
    for ax in axs[-1]:
        ax.set_xlabel("frequência (Hz); faixa cinza = banda 3–20 Hz", fontsize=8, color=INK2)
    fig.suptitle(f"Espectro de Welch da taxa dos MNs, 5 sementes (métrica v2): {cond}", x=0.01,
                 ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(res / f"spectrum_v2_{cond}.png", dpi=130)
    plt.close(fig)
    return out
