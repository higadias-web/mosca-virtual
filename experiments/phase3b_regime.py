"""Fase 3b, Etapa C: o regime de atividade alta (FASE3B_PLANO §P; pré-registrado antes de rodar).

Sem corpo, sem interface. FlyWire 783 (só cérebro), LIF do Shiu, 10 sementes pareadas (1000–1009).
Taxas dos ORNs (aumento sobre a espontânea; Faucher, Hilker & de Bruyne 2013, PLoS ONE 8:e56361, Fig. 2C,
leitura visual): vin0.1 → DM1 7 Hz, VA2 0 Hz (ponto único, sexo não distinguível); vin0.5 → DM1 16, VA2 11
(fêmeas); vin5 → DM1 42, VA2 22 (fêmeas).
Tipos de execução (odor sempre bilateral, ORNs de DM1+VA2):
  persist  vin5 em [0, 200) ms, desligado em [200, 1000) ms              real + 5 embaralhados
  dose     vin0.1 e vin0.5 contínuos por 1 s                              real + 5 embaralhados
           (vin5 contínuo e sem odor: reaproveitados da Etapa B, mesmo código e sementes)
  causal   vin5 contínuo com o AOTU019 esquerdo silenciado (saídas zeradas) real
Salva spikes de todos os neurônios em runs/phase3b/regime/ e REGIME_OK com a contagem. Análise separada.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from terrario import ROOT

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
RUNS = ROOT / "runs/phase3b/regime"
PREV = ROOT / "runs/phase3b/rates"
OUT = ROOT / "results/phase3b"
SEEDS, T_MS, ON_MS = list(range(1000, 1010)), 1000, 200
DOSES = {"vin0.1": {"ORN_DM1": 7.0, "ORN_VA2": 0.0}, "vin0.5": {"ORN_DM1": 16.0, "ORN_VA2": 11.0},
         "vin5": {"ORN_DM1": 42.0, "ORN_VA2": 22.0}}
SHUFFLES = [None, 0, 1, 2, 3, 4]
HIGH_FRAC = 0.0314          # "estado alto": fração ativa ≥ limite (d) da Etapa B (3,1 %; sem fonte)
P_RATIO = 0.10              # persistência: taxa em [400,1000) ≥ 10 % da taxa em [100,200)
C_MIN_HZ, C_ALPHA = 5.0, 0.05
_S = {}


def jobs_for(shuf):
    j = [(shuf, "persist", "vin5", s) for s in SEEDS] + [(shuf, "dose", d, s) for d in ("vin0.1", "vin0.5") for s in SEEDS]
    if shuf is None:
        j += [(None, "causal", "vin5", s) for s in SEEDS]
    return j


def tag(shuf, kind, dose, seed):
    return f"{'real' if shuf is None else f'emb{shuf}'}_{kind}_{dose}_s{seed}"


def _init(shuf):
    from terrario.brain import connectomes
    from terrario.brain.shuffle import shuffled
    c = connectomes.load("783")
    _S["c"] = c if shuf is None else shuffled(c, shuf)
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    _S["orn"] = {t: c.idx(a[(a.cell_type == t) & a.side.isin(["left", "right"])].root_id) for t in ("ORN_DM1", "ORN_VA2")}
    _S["aotu019_left"] = c.idx(a[(a.cell_type == "AOTU019") & (a.side == "left")].root_id)


def _job(job):
    from terrario.brain.lif import ShiuLIF
    shuf, kind, dose, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    if kind == "causal":
        m.silence(_S["aotu019_left"])
    for t in ("ORN_DM1", "ORN_VA2"):  # mesma ordem de chamadas de experiments/phase3b_rates.py
        m.set_poisson(_S["orn"][t], DOSES[dose][t])
    if kind == "persist":
        i1, t1 = m.run(int(ON_MS / m.dt))
        for t in ("ORN_DM1", "ORN_VA2"):
            m.set_poisson(_S["orn"][t], 0.0)
        i2, t2 = m.run(int((T_MS - ON_MS) / m.dt))
        i, t = np.concatenate([i1, i2]), np.concatenate([t1, t2])
    else:
        i, t = m.run(int(T_MS / m.dt))
    np.savez_compressed(RUNS / f"{tag(shuf, kind, dose, seed)}.npz", i=i.astype(np.int32), t=t.astype(np.int64))
    return tag(shuf, kind, dose, seed)


def run():
    RUNS.mkdir(parents=True, exist_ok=True)
    total = 0
    for shuf in SHUFFLES:
        jobs = jobs_for(shuf)
        total += len(jobs)
        t0 = time.time()
        with ProcessPoolExecutor(10, initializer=_init, initargs=(shuf,)) as ex:
            for _ in ex.map(_job, jobs):
                pass
        print(time.strftime("%H:%M:%S"), "conectoma", "real" if shuf is None else f"emb{shuf}",
              len(jobs), f"execuções em {time.time() - t0:.0f} s", flush=True)
    n = len(list(RUNS.glob("*.npz")))
    (RUNS / "REGIME_OK").write_text(f"{n}/{total}\n" + ("COMPLETA\n" if n == total else "INCOMPLETA\n"))


def analyze():
    exp = sum(len(jobs_for(s)) for s in SHUFFLES)
    ok = RUNS / "REGIME_OK"
    if not ok.exists() or ok.read_text().split()[0] != f"{exp}/{exp}":
        raise SystemExit("REGIME_OK ausente ou incompleto: não analisar")
    from terrario.brain import connectomes
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    dna02 = {sd: int(c.idx(a[(a.cell_type == "DNa02") & (a.side == sd)].root_id)[0]) for sd in ("left", "right")}
    dt = 0.1

    def load(path):
        z = np.load(path)
        return z["i"], z["t"] * dt  # ms

    res = dict(doses=DOSES, persist={}, dose={}, causal={})
    # persistência
    for shuf in SHUFFLES:
        key = "real" if shuf is None else f"emb{shuf}"
        ratios, last, late = [], [], []
        for s in SEEDS:
            i, t = load(RUNS / f"{tag(shuf, 'persist', 'vin5', s)}.npz")
            on = ((t >= 100) & (t < 200)).sum() / 100.0
            off = ((t >= 400) & (t < 1000)).sum() / 600.0
            ratios.append(off / on if on else np.nan)
            last.append(float(t.max()) if len(t) else 0.0)
            late.append(int(((t >= 900) & (t < 1000)).sum()))
        res["persist"][key] = dict(ratio_median=float(np.nanmedian(ratios)), ratios=ratios, last_spike_ms_median=float(np.median(last)),
                                   spikes_900_1000_median=float(np.median(late)), sustains=bool(np.nanmedian(ratios) >= P_RATIO))
    # dose
    for shuf in SHUFFLES:
        key = "real" if shuf is None else f"emb{shuf}"
        pre = "real" if shuf is None else f"emb{shuf}"
        d = {}
        for dose in ("vin0.1", "vin0.5", "vin5"):
            fr, tot = [], []
            for s in SEEDS:
                path = (PREV / f"{pre}_vin5_sim_s{s}.npz") if dose == "vin5" else (RUNS / f"{tag(shuf, 'dose', dose, s)}.npz")
                i, _ = load(path) if dose != "vin5" else (np.load(path)["i"], None)
                fr.append(float((np.bincount(i, minlength=c.n) > 0).mean()))
                tot.append(int(len(i)))
            d[dose] = dict(frac_active_median=float(np.median(fr)), total_spikes_median=float(np.median(tot)),
                           n_seeds_high=int(np.sum(np.array(fr) >= HIGH_FRAC)), frac_active=fr)
        res["dose"][key] = d
    rd = res["dose"]["real"]
    below = [k for k in ("vin0.1", "vin0.5") if rd[k]["n_seeds_high"] <= 2]
    res["dose_criteria"] = dict(
        threshold_exists=bool(len(below) > 0 and rd["vin5"]["n_seeds_high"] >= 8),
        doses_below_threshold=below,
        graded_below=(bool(rd["vin0.1"]["total_spikes_median"] < rd["vin0.5"]["total_spikes_median"])
                      if below == ["vin0.1", "vin0.5"] else None),
        mixed_doses=[k for k in DOSES if 3 <= rd[k]["n_seeds_high"] <= 7])
    # causal
    L, R, L0, R0 = [], [], [], []
    for s in SEEDS:
        ic = np.load(RUNS / f"{tag(None, 'causal', 'vin5', s)}.npz")["i"]
        i0 = np.load(PREV / f"real_vin5_sim_s{s}.npz")["i"]
        L.append(float((ic == dna02["left"]).sum())); R.append(float((ic == dna02["right"]).sum()))
        L0.append(float((i0 == dna02["left"]).sum())); R0.append(float((i0 == dna02["right"]).sum()))
    dR = np.array(R) - np.array(R0)
    p = float(wilcoxon(dR, zero_method="wilcox").pvalue) if np.any(dR != 0) else 1.0
    res["causal"] = dict(DNa02_left_intact=float(np.median(L0)), DNa02_left_silenced=float(np.median(L)),
                         DNa02_right_intact=float(np.median(R0)), DNa02_right_silenced=float(np.median(R)),
                         right_increase_median=float(np.median(dR)), p=p,
                         AOTU019L_contributes=bool(np.median(dR) >= C_MIN_HZ and p < C_ALPHA),
                         bias_removed=bool(np.median(R) >= 0.5 * np.median(L)))
    json.dump(res, open(OUT / "regime.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("persist", "dose_criteria", "causal")}, indent=1, ensure_ascii=False))
    print(json.dumps({k: {d: {kk: v[kk] for kk in ("frac_active_median", "total_spikes_median", "n_seeds_high")}
                          for d, v in dd.items()} for k, dd in res["dose"].items()}, indent=1))


if __name__ == "__main__":
    {"run": run, "analyze": analyze}[sys.argv[1]]()
