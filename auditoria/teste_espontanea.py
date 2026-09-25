"""Auditoria: sem odor, só atividade espontânea baixa em TODOS os ORNs. O modelo entra no estado alto?

Usa o motor do próprio projeto (ShiuLIF, FlyWire 783, parâmetros validados na Fase 1).
Taxas espontâneas são uma VARREDURA (0,5–5 Hz), não um valor com fonte.
Checagem de sanidade: vin5 (DM1 42 Hz, VA2 22 Hz), 1 semente, PN de DM1 deve ficar ~242–255 Hz.
"""
import sys
import json
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

ROOT = "/home/user/dados/terrario-virtual"
sys.path.insert(0, ROOT)
from terrario import ROOT as R  # noqa: E402

ANN = R / "third_party/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
_S = {}


def _init():
    from terrario.brain import connectomes
    c = connectomes.load("783")
    a = pd.read_csv(ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "cell_class", "side"])
    a["root_id"] = a.root_id.astype("int64")
    a = a[a.root_id.isin(c.flyids) if hasattr(c, "flyids") else a.root_id.map(lambda x: x in c.flyid2i)]
    ct = a.cell_type.fillna("")
    _S["c"] = c
    _S["orn_all"] = c.idx(a[ct.str.startswith("ORN_")].root_id)
    _S["orn"] = {t: c.idx(a[(ct == t) & a.side.isin(["left", "right"])].root_id) for t in ("ORN_DM1", "ORN_VA2")}
    _S["pn_dm1"] = c.idx(a[ct.str.startswith("DM1_")].root_id)
    _S["alpn"] = c.idx(a[a.cell_class.fillna("") == "ALPN"].root_id)
    _S["kc"] = c.idx(a[a.cell_class.fillna("") == "Kenyon_Cell"].root_id)


def _job(job):
    from terrario.brain.lif import ShiuLIF
    kind, rate, seed = job
    c = _S["c"]
    m = ShiuLIF(c, seed=seed)
    if kind == "espont":
        m.set_poisson(_S["orn_all"], rate)
    else:  # vin5
        m.set_poisson(_S["orn"]["ORN_DM1"], 42.0)
        m.set_poisson(_S["orn"]["ORN_VA2"], 22.0)
    i, t = m.run(int(1000 / m.dt))
    tm = t * m.dt if t.dtype.kind in "iu" else t
    late = tm >= 500
    n = c.n
    act_late = np.unique(i[late])
    cnt = np.bincount(i, minlength=n)
    orn_set = set(_S["orn_all"].tolist())
    nonorn_active = [x for x in np.unique(i) if x not in orn_set]
    return dict(kind=kind, rate=rate, seed=seed, spikes=int(len(i)),
                frac_active=len(np.unique(i)) / n, frac_active_late=len(act_late) / n,
                nonORN_active=len(nonorn_active),
                pn_dm1_hz=float(np.median(cnt[_S["pn_dm1"]])),
                alpn_mean_hz=float(cnt[_S["alpn"]].mean()),
                kc_frac=float((cnt[_S["kc"]] > 0).mean()), n_orn=len(_S["orn_all"]))


if __name__ == "__main__":
    jobs = [("vin5", 0, 1000)] + [("espont", r, s) for r in (0.5, 1.0, 2.0, 5.0) for s in (1000, 1001, 1002)]
    with ProcessPoolExecutor(4, initializer=_init) as ex:
        for res in ex.map(_job, jobs):
            print(json.dumps(res), flush=True)
