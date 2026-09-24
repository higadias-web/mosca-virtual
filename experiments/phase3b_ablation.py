"""Fase 3b, Etapa D: ablações DIAGNÓSTICAS (FASE3B_PLANO §R; pré-registrado). O modelo oficial NÃO muda:
as sinapses são zeradas numa cópia do conectoma, só dentro deste experimento.

  A  sem as sinapses químicas eLN → PN. eLN = LN do lobo antenal (cell_class ALLN) com saída excitatória no
     modelo (sinal do arquivo do Shiu) e known_nt que não seja GABA, glutamato ou octopamina (Yaksi & Wilson
     2010: a excitação eLN → PN é elétrica na mosca; os eLNs são colinérgicos, Shang et al. 2007)
  B  sem as entradas excitatórias nos ORNs (toda sinapse de peso > 0 que chega a um ORN_*)
  C  A + B
Odor: vinagre (Faucher et al. 2013, Fig. 2C) a 0,1 % (DM1 7 Hz, VA2 0), 0,5 % (16/11) e 5 % (42/22), bilateral,
ligado em [0, 200) ms e desligado até 1000 ms; e sem odor. 10 sementes pareadas (1000–1009).
Referência intacta: persistência a 0,1 % e 0,5 % (novas) e a 5 % (Etapa C, runs/phase3b/regime/).
Salva spikes de todos os neurônios em runs/phase3b/ablation/ e ABL_OK. Análise separada.
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
RUNS = ROOT / "runs/phase3b/ablation"
PREV = ROOT / "runs/phase3b/regime"
OUT = ROOT / "results/phase3b"
SEEDS, T_MS, ON_MS = list(range(1000, 1010)), 1000, 200
DOSES = {"vin0.1": {"ORN_DM1": 7.0, "ORN_VA2": 0.0}, "vin0.5": {"ORN_DM1": 16.0, "ORN_VA2": 11.0},
         "vin5": {"ORN_DM1": 42.0, "ORN_VA2": 22.0}}
ABL = ["A", "B", "C"]
BASAL_RATIO, PERSIST_RATIO, HIGH_FRAC = 0.01, 0.10, 0.0314
_S = {}


def _ann(c):
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_class", "cell_type", "known_nt"])
    a["root_id"] = a.root_id.astype("int64")
    return a.set_index("root_id").reindex(c.flyids)


def edge_masks(c):
    """Máscaras (sobre as arestas CSR) das sinapses removidas em A e B, e os conjuntos usados."""
    a = _ann(c)
    pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
    post = c.indices.astype(np.int64)
    out_pos = np.zeros(c.n, bool)
    out_pos[pre[c.syn_count > 0]] = True
    ln = (a.cell_class == "ALLN").to_numpy()
    kn = a.known_nt.astype(str).str.lower()
    bad = kn.str.contains("gaba") | kn.str.contains("glutamate") | kn.str.contains("octopamine")
    eln = ln & out_pos & ~bad.to_numpy()
    pn = (a.cell_class == "ALPN").to_numpy()
    orn = a.cell_type.astype(str).str.startswith("ORN_").to_numpy()
    mA = eln[pre] & pn[post]
    mB = orn[post] & (c.syn_count > 0)
    info = dict(n_eLN=int(eln.sum()), n_PN=int(pn.sum()), n_ORN=int(orn.sum()),
                A_edges=int(mA.sum()), A_synapses=float(c.syn_count[mA].sum()),
                B_edges=int(mB.sum()), B_synapses=float(c.syn_count[mB].sum()),
                model_excitatory_LN_with_known_inhibitory=int((ln & out_pos & bad.to_numpy()).sum()))
    return mA, mB, info


def ablated(c, which):
    from terrario.brain.flywire import FlyWireConnectome
    mA, mB, _ = edge_masks(c)
    m = {"A": mA, "B": mB, "C": mA | mB}[which]
    w = c.syn_count.copy()
    w[m] = 0.0
    return FlyWireConnectome(version=f"{c.version}-abl{which}", flyids=c.flyids, indptr=c.indptr, indices=c.indices, syn_count=w)


def jobs_for(which):
    if which == "intact":
        return [("intact", d, s) for d in ("vin0.1", "vin0.5") for s in SEEDS]
    return [(which, d, s) for d in ("none", "vin0.1", "vin0.5", "vin5") for s in SEEDS]


def tag(which, dose, seed):
    return f"{which}_{dose}_s{seed}"


def _init(which):
    from terrario.brain import connectomes
    c = connectomes.load("783")
    _S["c"] = c if which == "intact" else ablated(c, which)
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    _S["orn"] = {t: c.idx(a[(a.cell_type == t) & a.side.isin(["left", "right"])].root_id) for t in ("ORN_DM1", "ORN_VA2")}


def _job(job):
    from terrario.brain.lif import ShiuLIF
    which, dose, seed = job
    m = ShiuLIF(_S["c"], seed=seed)
    if dose != "none":
        for t in ("ORN_DM1", "ORN_VA2"):  # mesma ordem de experiments/phase3b_regime.py
            m.set_poisson(_S["orn"][t], DOSES[dose][t])
    i1, t1 = m.run(int(ON_MS / m.dt))
    if dose != "none":
        for t in ("ORN_DM1", "ORN_VA2"):
            m.set_poisson(_S["orn"][t], 0.0)
    i2, t2 = m.run(int((T_MS - ON_MS) / m.dt))
    np.savez_compressed(RUNS / f"{tag(which, dose, seed)}.npz", i=np.concatenate([i1, i2]).astype(np.int32),
                        t=np.concatenate([t1, t2]).astype(np.int64))
    return tag(which, dose, seed)


def run():
    RUNS.mkdir(parents=True, exist_ok=True)
    total = 0
    for which in ["intact"] + ABL:
        jobs = jobs_for(which)
        total += len(jobs)
        t0 = time.time()
        with ProcessPoolExecutor(10, initializer=_init, initargs=(which,)) as ex:
            for _ in ex.map(_job, jobs):
                pass
        print(time.strftime("%H:%M:%S"), which, len(jobs), f"execuções em {time.time() - t0:.0f} s", flush=True)
    n = len(list(RUNS.glob("*.npz")))
    (RUNS / "ABL_OK").write_text(f"{n}/{total}\n" + ("COMPLETA\n" if n == total else "INCOMPLETA\n"))


def analyze():
    exp = sum(len(jobs_for(w)) for w in ["intact"] + ABL)
    ok = RUNS / "ABL_OK"
    if not ok.exists() or ok.read_text().split()[0] != f"{exp}/{exp}":
        raise SystemExit("ABL_OK ausente ou incompleto: não analisar")
    from terrario.brain import connectomes
    from experiments.phase3b_breakdown import group, ANN as ANN2
    c = connectomes.load("783")
    _, _, info = edge_masks(c)
    a = pd.read_csv(ANN2, sep="\t", low_memory=False, usecols=["root_id", "super_class", "cell_class", "cell_type", "side"])
    a["root_id"] = a.root_id.astype("int64")
    a = a.set_index("root_id").reindex(c.flyids)
    g = np.array([group(r) for r in a.itertuples()])
    classes = {"KC": g == "células de Kenyon", "PN": g == "PNs do lobo antenal", "LN": g == "LNs do lobo antenal"}

    def path(which, dose, s):
        if which == "intact" and dose == "vin5":
            return PREV / f"real_persist_vin5_s{s}.npz"
        return RUNS / f"{tag(which, dose, s)}.npz"

    res = dict(sets=info, conditions={})
    for which in ["intact"] + ABL:
        cond = {}
        for dose in (["none"] if which != "intact" else []) + list(DOSES):
            on_sp, ratios, fr_on, cls = [], [], [], {k: [] for k in classes}
            for s in SEEDS:
                z = np.load(path(which, dose, s))
                t = z["t"] * 0.1
                i = z["i"]
                on = ((t >= 100) & (t < 200)).sum() / 100.0
                off = ((t >= 400) & (t < 1000)).sum() / 600.0
                ratios.append(off / on if on else (0.0 if off == 0 else np.inf))
                ion = i[t < 200]
                on_sp.append(int(len(ion)))
                act = np.bincount(ion, minlength=c.n) > 0
                fr_on.append(float(act.mean()))
                for k, m in classes.items():
                    cls[k].append(float(act[m].mean()))
            r = float(np.median(ratios))
            cond[dose] = dict(ratio_off_on_median=r, spikes_0_200_median=float(np.median(on_sp)),
                              frac_active_0_200_median=float(np.median(fr_on)),
                              frac_active_by_class_0_200={k: float(np.median(v)) for k, v in cls.items()},
                              returns_to_basal=bool(r <= BASAL_RATIO), persistent=bool(r >= PERSIST_RATIO),
                              spikes_0_200=on_sp)
        d = [cond[k]["spikes_0_200"] for k in DOSES]
        p1 = float(wilcoxon(np.array(d[1]) - np.array(d[0])).pvalue) if np.any(np.array(d[1]) != np.array(d[0])) else 1.0
        p2 = float(wilcoxon(np.array(d[2]) - np.array(d[1])).pvalue) if np.any(np.array(d[2]) != np.array(d[1])) else 1.0
        med = [float(np.median(x)) for x in d]
        cond["dose_grows"] = bool(med[0] < med[1] < med[2] and p1 < 0.025 and p2 < 0.025)
        cond["dose_p"] = [p1, p2]
        res["conditions"][which] = cond
    json.dump(res, open(OUT / "ablation.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(info, indent=1))
    for w, cd in res["conditions"].items():
        print(f"== {w}: dose cresce = {cd['dose_grows']} (p {cd['dose_p'][0]:.3f}, {cd['dose_p'][1]:.3f})")
        for dose in [k for k in cd if k in DOSES or k == "none"]:
            v = cd[dose]
            print(f"   {dose:6s} razão off/on {v['ratio_off_on_median']:.3f} basal={v['returns_to_basal']} persist={v['persistent']} | "
                  f"spikes 0–200 {v['spikes_0_200_median']:.0f} | ativos {100 * v['frac_active_0_200_median']:.2f} % | "
                  f"KC {100 * v['frac_active_by_class_0_200']['KC']:.1f} % PN {100 * v['frac_active_by_class_0_200']['PN']:.1f} % LN {100 * v['frac_active_by_class_0_200']['LN']:.1f} %")


if __name__ == "__main__":
    {"run": run, "analyze": analyze, "sets": lambda: print(edge_masks(__import__('terrario.brain.connectomes', fromlist=['load']).load('783'))[2])}[sys.argv[1]]()
