"""Fase 3b, S1: teste de viabilidade sem corpo (FASE3B_PLANO §F1; critério fixado antes de rodar).

Pergunta: estimular só os neurônios olfativos de fruta fermentada muda a taxa dos DNs de marcha no LIF do
Shiu (FlyWire 783, só cérebro)?
  odor     Poisson a 100 Hz nos ORNs de DM1 e VA2, os dois lados (Semmelhack & Wang 2009; 100 Hz sem fonte)
  controle sem estímulo, mesma semente (pareado)
10 sementes (1000–1009), 1 s. Grupos: DNp09 (2), MDN (4), DNa01/02 (4); IDs pela anotação do FlyWire
(third_party/flywire_annotations/.../Supplemental_file1_neuron_annotations.tsv, coluna cell_type).
Critério: um grupo muda se Wilcoxon pareado bilateral p < 0,05/3 E diferença mediana ≥ 1 Hz.
Viável (segue para a interface) se ≥ 1 grupo mudar. Descritivo: diferença mediana ≥ 10 Hz (|δ| ≈ 0,1).
Saída: results/phase3b/viability.json e viability_runs.csv
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from terrario import ROOT

ANN = ROOT / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
ORN_TYPES = ["ORN_DM1", "ORN_VA2"]
GROUPS = {"DNp09": ["DNp09"], "MDN": ["MDN"], "DNa01/02": ["DNa01", "DNa02"]}
RATE_HZ, T_MS, SEEDS = 100.0, 1000, list(range(1000, 1010))
ALPHA, MIN_DIFF_HZ, RELEVANT_HZ = 0.05 / 3, 1.0, 10.0
OUT = ROOT / "results/phase3b"
_S = {}


def _ids():
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type"])
    orn = a[a.cell_type.isin(ORN_TYPES)].root_id.astype("int64").tolist()
    grp = {g: a[a.cell_type.isin(t)].root_id.astype("int64").tolist() for g, t in GROUPS.items()}
    return orn, grp


def _init():
    from terrario.brain import connectomes
    _S["c"] = connectomes.load("783")
    orn, grp = _ids()
    _S["orn"] = _S["c"].idx(orn)
    _S["grp"] = {g: _S["c"].idx(v) for g, v in grp.items()}


def _job(job):
    from terrario.brain.lif import ShiuLIF
    cond, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    if cond == "odor":
        m.set_poisson(_S["orn"], RATE_HZ)
    i, _ = m.run(int(T_MS / m.dt))
    row = dict(cond=cond, seed=seed, n_spikes_total=int(len(i)))
    for g, idx in _S["grp"].items():
        row[g] = float(np.isin(i, idx).sum() / len(idx) / (T_MS / 1000))
    row["orn_rate"] = float(np.isin(i, _S["orn"]).sum() / len(_S["orn"]) / (T_MS / 1000))
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    orn, grp = _ids()
    jobs = [(c, s) for s in SEEDS for c in ("odor", "control")]
    with ProcessPoolExecutor(10, initializer=_init) as ex:
        rows = list(ex.map(_job, jobs))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "viability_runs.csv", index=False)
    od = df[df.cond == "odor"].set_index("seed").sort_index()
    ct = df[df.cond == "control"].set_index("seed").sort_index()
    res = dict(n_orn=len(orn), n_cells={g: len(v) for g, v in grp.items()}, rate_hz=RATE_HZ, seeds=SEEDS,
               orn_rate_odor_median=float(od.orn_rate.median()), groups={})
    for g in GROUPS:
        d = (od[g] - ct[g]).to_numpy()
        p = float(wilcoxon(od[g], ct[g], zero_method="wilcox").pvalue) if np.any(d != 0) else 1.0
        med = float(np.median(d))
        res["groups"][g] = dict(odor_median=float(od[g].median()), control_median=float(ct[g].median()),
                                diff_median=med, diff_min=float(d.min()), diff_max=float(d.max()),
                                p_wilcoxon=p, changes=bool(p < ALPHA and abs(med) >= MIN_DIFF_HZ),
                                relevant_ge_10Hz=bool(abs(med) >= RELEVANT_HZ))
    res["viable"] = any(v["changes"] for v in res["groups"].values())
    res["decision"] = ("segue para a interface (S1)" if res["viable"]
                       else "nenhum grupo mudou: 3b vai direto para o relatório")
    json.dump(res, open(OUT / "viability.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
