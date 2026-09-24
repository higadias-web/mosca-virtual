"""Fase 3b, S1: lateralidade e especificidade (FASE3B_PLANO §H; critérios fixados antes de rodar).

Sem corpo. FlyWire 783 (só cérebro), LIF do Shiu. Odor = Poisson 100 Hz nos ORNs de DM1+VA2 (§F1).
Condições: controle (sem estímulo), sim (ORNs dos dois lados), esq (só ORNs com side == left), dir (só
right). Conectomas: real e 5 embaralhados com graus preservados (terrario/brain/shuffle.py, sementes 0–4).
10 sementes pareadas (1000–1009), 1 s. Taxa POR CÉLULA de DNp09 (E/D), MDN (2E/2D), DNa01 (E/D), DNa02 (E/D).

Critérios (§H):
  V1 especificidade da viabilidade: efeito_real = mediana(sementes) de [DNa01/02 sim − controle] no real;
     efeito_emb = mediana(5 embaralhamentos) da mediana(sementes) do mesmo; ESPECÍFICO se efeito_emb ≤ 0,5 × efeito_real.
  V2 carrega lado, por tipo T ∈ {DNa01, DNa02, DNp09, MDN}: Δ_T(semente) = ½[(r_E − r_D | esq) + (r_D − r_E | dir)]
     (ipsi − contra; MDN = média das 2 células do lado); Wilcoxon pareado bilateral contra 0, α = 0,05/4, e
     |mediana Δ| ≥ 2 Hz. Especificidade lateral: |Δ_emb| (mediana dos 5) ≤ 0,5 × |Δ_real|.
Uso: uv run python -m experiments.phase3b_laterality run   → grava runs/phase3b/laterality_runs.csv (+ LAT_OK)
     uv run python -m experiments.phase3b_laterality analyze → exige LAT_OK com 240 linhas
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from terrario import ROOT

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
ORN_TYPES = ["ORN_DM1", "ORN_VA2"]
TYPES = ["DNp09", "MDN", "DNa01", "DNa02"]
CONDS = ["control", "sim", "esq", "dir"]
SHUFFLES = [None, 0, 1, 2, 3, 4]
RATE_HZ, T_MS, SEEDS = 100.0, 1000, list(range(1000, 1010))
ALPHA, MIN_LAT_HZ = 0.05 / 4, 2.0
RUNS = ROOT / "runs/phase3b"
OUT = ROOT / "results/phase3b"
N_EXPECTED = len(SHUFFLES) * len(CONDS) * len(SEEDS)
_S = {}


def _ann():
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    return a


def _init(shuf):
    from terrario.brain import connectomes
    from terrario.brain.shuffle import shuffled
    c = connectomes.load("783")
    _S["c"] = c if shuf is None else shuffled(c, shuf)
    a = _ann()
    orn = a[a.cell_type.isin(ORN_TYPES)]
    _S["orn"] = {k: c.idx(orn[orn.side.isin(v)].root_id) for k, v in
                 {"sim": ["left", "right"], "esq": ["left"], "dir": ["right"]}.items()}
    dn = a[a.cell_type.isin(TYPES)].sort_values(["cell_type", "side", "root_id"])
    _S["cells"] = [(t, s, int(r), int(c.idx([r])[0])) for t, s, r in zip(dn.cell_type, dn.side, dn.root_id)]


def _job(job):
    from terrario.brain.lif import ShiuLIF
    shuf, cond, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    if cond != "control":
        m.set_poisson(_S["orn"][cond], RATE_HZ)
    i, _ = m.run(int(T_MS / m.dt))
    cnt = np.bincount(i, minlength=_S["c"].n)
    rows = []
    for t, s, r, k in _S["cells"]:
        rows.append(dict(shuffle=-1 if shuf is None else shuf, cond=cond, seed=seed, type=t, side=s,
                         root_id=r, rate=float(cnt[k] / (T_MS / 1000))))
    return rows


def run():
    RUNS.mkdir(parents=True, exist_ok=True)
    rows = []
    for shuf in SHUFFLES:  # um pool por conectoma (RAM: um conectoma por processo)
        if shuf is not None:  # gera/verifica o embaralhamento uma vez, fora do pool
            from terrario.brain import connectomes
            from terrario.brain.shuffle import shuffled
            shuffled(connectomes.load("783"), shuf)
        jobs = [(shuf, c, s) for c in CONDS for s in SEEDS]
        with ProcessPoolExecutor(10, initializer=_init, initargs=(shuf,)) as ex:
            for r in ex.map(_job, jobs):
                rows += r
        print("conectoma", "real" if shuf is None else f"emb{shuf}", "ok", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(RUNS / "laterality_runs.csv", index=False)
    n = df.groupby(["shuffle", "cond", "seed"]).ngroups
    (RUNS / "LAT_OK").write_text(f"{n}/{N_EXPECTED}\n" + ("COMPLETA\n" if n == N_EXPECTED else "INCOMPLETA\n"))


def _side_rate(d, t, side):
    x = d[(d.type == t) & (d.side == side)]
    return x.groupby("seed").rate.mean().reindex(SEEDS)


def analyze():
    ok = RUNS / "LAT_OK"
    if not ok.exists() or "COMPLETA" not in ok.read_text() or "INCOMPLETA" in ok.read_text():
        raise SystemExit("LAT_OK ausente ou incompleto: não analisar")
    df = pd.read_csv(RUNS / "laterality_runs.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(conds=CONDS, seeds=SEEDS, rate_hz=RATE_HZ, per_connectome={})
    for shuf, d in df.groupby("shuffle"):
        key = "real" if shuf == -1 else f"emb{shuf}"
        g = {}
        grp = d[d.type.isin(["DNa01", "DNa02"])].groupby(["cond", "seed"]).rate.mean().unstack(0)
        g["DNa0102_sim_minus_control_median"] = float((grp["sim"] - grp["control"]).median())
        for t in TYPES:
            lat = 0.5 * ((_side_rate(d[d.cond == "esq"], t, "left") - _side_rate(d[d.cond == "esq"], t, "right"))
                         + (_side_rate(d[d.cond == "dir"], t, "right") - _side_rate(d[d.cond == "dir"], t, "left")))
            nz = np.any(lat.to_numpy() != 0)
            p = float(wilcoxon(lat.to_numpy(), zero_method="wilcox").pvalue) if nz else 1.0
            g[t] = dict(lat_median=float(lat.median()), lat_min=float(lat.min()), lat_max=float(lat.max()), p=p,
                        carries_side=bool(p < ALPHA and abs(lat.median()) >= MIN_LAT_HZ),
                        **{f"{c}_{s}": float(_side_rate(d[d.cond == c], t, s).median())
                           for c in CONDS for s in ("left", "right")})
        res["per_connectome"][key] = g
    real = res["per_connectome"]["real"]
    embs = [v for k, v in res["per_connectome"].items() if k != "real"]
    e_real = real["DNa0102_sim_minus_control_median"]
    e_emb = float(np.median([v["DNa0102_sim_minus_control_median"] for v in embs]))
    res["V1"] = dict(effect_real=e_real, effect_shuffled_median=e_emb,
                     effect_shuffled_each=[v["DNa0102_sim_minus_control_median"] for v in embs],
                     specific=bool(e_emb <= 0.5 * e_real))
    res["V2"] = {}
    for t in TYPES:
        l_real = real[t]["lat_median"]
        l_emb = float(np.median([v[t]["lat_median"] for v in embs]))
        res["V2"][t] = dict(lat_real=l_real, p_real=real[t]["p"], carries_side=real[t]["carries_side"],
                            lat_shuffled_median=l_emb,
                            lateral_specific=(bool(abs(l_emb) <= 0.5 * abs(l_real)) if real[t]["carries_side"] else None))
    json.dump(res, open(OUT / "laterality.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"V1": res["V1"], "V2": res["V2"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"run": run, "analyze": analyze}[sys.argv[1]]()
