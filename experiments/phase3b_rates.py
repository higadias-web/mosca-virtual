"""Fase 3b, Etapa B: sensibilidade à taxa dos ORNs (FASE3B_PLANO §N; pré-registrado antes de rodar).

Sem corpo, sem interface. FlyWire 783 (só cérebro), LIF do Shiu, 1 s, 10 sementes pareadas (1000–1009).
Taxas dos ORNs (Poisson, sem fundo):
  r20, r50, r100   20/50/100 Hz em todos os ORNs de DM1 e VA2 (sem fonte; varredura)
  vin5             taxa COM FONTE: vinagre de maçã a 5 %, fêmeas, aumento sobre a taxa pré-estímulo
                   (Faucher, Hilker & de Bruyne 2013, PLoS ONE 8:e56361, Fig. 2C, lido da figura):
                   ORN_DM1 (ab1A, Or42b) = 42 Hz; ORN_VA2 (ab1B, Or92a) = 22 Hz
Condições: real → controle, bilateral, só esquerda, só direita; 5 embaralhados → controle e bilateral.
Salva os spikes de TODOS os neurônios de cada execução (runs/phase3b/rates/*.npz) e, no fim, RATES_OK.
Análise separada (`analyze`), só com RATES_OK completo.
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
RUNS = ROOT / "runs/phase3b/rates"
OUT = ROOT / "results/phase3b"
SEEDS, T_MS = list(range(1000, 1010)), 1000
RATES = {"r20": {"ORN_DM1": 20.0, "ORN_VA2": 20.0}, "r50": {"ORN_DM1": 50.0, "ORN_VA2": 50.0},
         "r100": {"ORN_DM1": 100.0, "ORN_VA2": 100.0}, "vin5": {"ORN_DM1": 42.0, "ORN_VA2": 22.0}}
TYPES = ["DNp09", "MDN", "DNa01", "DNa02"]
SHUFFLES = [None, 0, 1, 2, 3, 4]
# critérios (§N)
A_ALPHA, A_MIN = 0.05 / 4, 1.0            # (a) DNp09 excitado: Bonferroni sobre 4 taxas; ≥ 1 Hz
B_ALPHA, B_MIN = 0.05 / 4, 2.0            # (b) viés E > D do DNa02 em cada taxa; ≥ 2 Hz
C_ALPHA, C_MIN = 0.05 / 16, 2.0           # (c) lado: 4 tipos × 4 taxas; ≥ 2 Hz
D_REF_FRAC, D_FACTOR = 435 / 138639, 10   # (d) regime: ≤ 10× a fração ativa do regime validado da Fase 1 (sem fonte)
_S = {}


def jobs_for(shuf):
    if shuf is None:
        return [(None, "none", "control", s) for s in SEEDS] + \
               [(None, r, c, s) for r in RATES for c in ("sim", "esq", "dir") for s in SEEDS]
    return [(shuf, "none", "control", s) for s in SEEDS] + [(shuf, r, "sim", s) for r in RATES for s in SEEDS]


def tag(shuf, rate, cond, seed):
    return f"{'real' if shuf is None else f'emb{shuf}'}_{rate}_{cond}_s{seed}"


def _init(shuf):
    from terrario.brain import connectomes
    from terrario.brain.shuffle import shuffled
    c = connectomes.load("783")
    _S["c"] = c if shuf is None else shuffled(c, shuf)
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    _S["orn"] = {(t, side): c.idx(a[(a.cell_type == t) & (a.side == side)].root_id)
                 for t in ("ORN_DM1", "ORN_VA2") for side in ("left", "right")}


def _job(job):
    from terrario.brain.lif import ShiuLIF
    shuf, rate, cond, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    if cond != "control":
        sides = {"sim": ("left", "right"), "esq": ("left",), "dir": ("right",)}[cond]
        for t, hz in RATES[rate].items():
            idx = np.concatenate([_S["orn"][(t, sd)] for sd in sides])
            m.set_poisson(idx, hz)  # set_poisson acumula alvos (terrario/brain/lif.py)
    i, t = m.run(int(T_MS / m.dt))
    np.savez_compressed(RUNS / f"{tag(shuf, rate, cond, seed)}.npz", i=i.astype(np.int32), t=t.astype(np.int32))
    return tag(shuf, rate, cond, seed)


def run():
    RUNS.mkdir(parents=True, exist_ok=True)
    total = 0
    for shuf in SHUFFLES:
        jobs = jobs_for(shuf)
        total += len(jobs)
        with ProcessPoolExecutor(10, initializer=_init, initargs=(shuf,)) as ex:
            for _ in ex.map(_job, jobs):
                pass
        print("conectoma", "real" if shuf is None else f"emb{shuf}", len(jobs), "execuções ok", flush=True)
    n = len(list(RUNS.glob("*.npz")))
    (RUNS / "RATES_OK").write_text(f"{n}/{total}\n" + ("COMPLETA\n" if n == total else "INCOMPLETA\n"))


def analyze():
    ok = RUNS / "RATES_OK"
    exp = sum(len(jobs_for(s)) for s in SHUFFLES)
    if not ok.exists() or ok.read_text().split()[0] != f"{exp}/{exp}":
        raise SystemExit("RATES_OK ausente ou incompleto: não analisar")
    from terrario.brain import connectomes
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    cells = {(t, sd): c.idx(a[(a.cell_type == t) & (a.side == sd)].root_id) for t in TYPES for sd in ("left", "right")}
    rows = []
    for shuf in SHUFFLES:
        for sh, rate, cond, seed in jobs_for(shuf):
            i = np.load(RUNS / f"{tag(sh, rate, cond, seed)}.npz")["i"]
            cnt = np.bincount(i, minlength=c.n)
            row = dict(conn="real" if sh is None else f"emb{sh}", rate=rate, cond=cond, seed=seed,
                       total_spikes=int(len(i)), frac_active=float((cnt > 0).mean()))
            for (t, sd), ix in cells.items():
                row[f"{t}_{sd}"] = float(cnt[ix].mean())
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rates_runs.csv", index=False)
    real = df[df.conn == "real"]
    ctl = real[real.cond == "control"].set_index("seed")

    def col(rate, cond, name):
        return real[(real.rate == rate) & (real.cond == cond)].set_index("seed")[name].reindex(SEEDS)

    def wil(x):
        x = np.asarray(x, float)
        return float(wilcoxon(x, zero_method="wilcox").pvalue) if np.any(x != 0) else 1.0

    res = dict(rates=RATES, criteria={}, per_rate={})
    a_hits, b_ok, c_hits = [], [], []
    for r in RATES:
        pr = {}
        d09 = (col(r, "sim", "DNp09_left") + col(r, "sim", "DNp09_right")) / 2 - \
              (ctl["DNp09_left"] + ctl["DNp09_right"]).reindex(SEEDS) / 2
        pr["a_DNp09_diff_median"], pr["a_p"] = float(d09.median()), wil(d09)
        pr["a_excited"] = bool(pr["a_p"] < A_ALPHA and pr["a_DNp09_diff_median"] >= A_MIN)
        a_hits.append(pr["a_excited"])
        bias = col(r, "sim", "DNa02_left") - col(r, "sim", "DNa02_right")
        pr["b_DNa02_LminusR_median"], pr["b_p"] = float(bias.median()), wil(bias)
        pr["b_DNa02_left_median"] = float(col(r, "sim", "DNa02_left").median())
        pr["b_DNa02_right_median"] = float(col(r, "sim", "DNa02_right").median())
        pr["b_bias_holds"] = bool(pr["b_p"] < B_ALPHA and pr["b_DNa02_LminusR_median"] >= B_MIN)
        b_ok.append(pr["b_bias_holds"])
        pr["c"] = {}
        for t in TYPES:
            lat = 0.5 * ((col(r, "esq", f"{t}_left") - col(r, "esq", f"{t}_right")) +
                         (col(r, "dir", f"{t}_right") - col(r, "dir", f"{t}_left")))
            p = wil(lat)
            hit = bool(p < C_ALPHA and abs(lat.median()) >= C_MIN)
            pr["c"][t] = dict(lat_median=float(lat.median()), p=p, carries_side=hit)
            c_hits.append(hit)
        for t in TYPES:
            pr[f"sim_{t}_L_R"] = (float(col(r, "sim", f"{t}_left").median()), float(col(r, "sim", f"{t}_right").median()))
        res["per_rate"][r] = pr
    act = df.groupby(["conn", "rate", "cond"])[["total_spikes", "frac_active"]].median().reset_index()
    res["activity"] = act.to_dict("records")
    lim = D_FACTOR * D_REF_FRAC
    real_sim = act[(act.conn == "real") & (act.cond == "sim")].set_index("rate").frac_active
    res["criteria"] = dict(
        a_DNp09_excited_any_rate=bool(any(a_hits)),
        b_DNa02_left_bias_all_rates=bool(all(b_ok)),
        c_some_DN_carries_side=bool(any(c_hits)),
        d_regime_limit_frac_active=lim,
        d_regime_in_range={r: bool(real_sim[r] <= lim) for r in RATES})
    json.dump(res, open(OUT / "rates.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res["criteria"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"run": run, "analyze": analyze}[sys.argv[1]]()
