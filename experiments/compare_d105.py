"""D-105: compara a Fig. 1D de cada conectoma candidato com a v783 (referência já validada).

Referência: runs/phase1/783/fig1d.parquet (Fase 1). Candidatos: runs/d105/fig1d_*.parquet.
Como os IDs diferem entre datasets, a comparação é por TIPO CELULAR do FlyWire:
  - IDs do FlyWire: cell_type de flywire_annotations/Supplemental_file1 (ou "<root_id>" sem tipo);
  - IDs do BANC: coluna fafb_cell_type dos metadados (tipo FAFB atribuído pelos autores do BANC).
Métricas: curva do MN9; nº de neurônios ativos a 200 Hz; top-200 a 200 Hz (tipos em comum);
correlação de Pearson das taxas médias por tipo (tipos ativos em pelo menos um dos dois).

Uso: uv run python -m experiments.compare_d105
"""

from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

from terrario import ROOT, THIRD_PARTY
from experiments.connectome_eval import MN9_BANC, MN9_FW


def type_maps():
    a = pd.read_csv(THIRD_PARTY / "flywire_annotations/supplemental_files/"
                    "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False,
                    usecols=["root_id", "cell_type"])
    fw = dict(zip(a.root_id, a.cell_type))
    from terrario.brain import banc
    m = banc.load_meta()
    bc = dict(zip(m.banc_888_id, m.fafb_cell_type.fillna(m.cell_type)))
    return fw, bc


def by_type(df, fw, bc):
    t = [fw.get(i) if i in fw else bc.get(i) for i in df.flyid]
    t = [x if isinstance(x, str) else f"id{i}" for x, i in zip(t, df.flyid)]
    return df.assign(ctype=t)


def main():
    fw, bc = type_maps()
    ref = pd.read_parquet(ROOT / "runs/phase1/783/fig1d.parquet")
    ref = ref.assign(exp_name=ref.exp_name.str.replace("sugarR_", "sugar_"))
    r200 = by_type(ref[ref.exp_name == "sugar_200Hz"], fw, bc)
    ref_top = r200.nlargest(200, "rate")
    ref_types = set(ref_top.ctype)
    ref_mean = r200.groupby("ctype").rate.mean()
    out = {"783 (referência)": dict(
        mn9={int(e.split("_")[1][:-2]): float(v) for e, v in
             ref[ref.flyid == MN9_FW].set_index("exp_name").rate.items()},
        n_active_200=int((r200.rate > 0).sum()), top200_types=len(ref_types))}
    for f in sorted(glob.glob(str(ROOT / "runs/d105/fig1d_*.parquet"))):
        tag = f.split("fig1d_")[1][:-8]
        df = pd.read_parquet(f)
        mn9 = MN9_BANC if tag.startswith("banc") else MN9_FW
        d200 = by_type(df[df.exp_name == "sugar_200Hz"], fw, bc)
        top = d200.nlargest(200, "rate")
        mean = d200.groupby("ctype").rate.mean()
        j = pd.concat([ref_mean.rename("ref"), mean.rename("cand")], axis=1).fillna(0)
        out[tag] = dict(
            mn9={int(e.split("_")[1][:-2]): float(v) for e, v in
                 df[df.flyid == mn9].set_index("exp_name").rate.items()},
            n_active_200=int((d200.rate > 0).sum()),
            top200_types=len(set(top.ctype)),
            top200_types_in_ref=len(set(top.ctype) & ref_types),
            ref_top200_types_recovered=round(len(set(top.ctype) & ref_types) / len(ref_types), 3),
            pearson_by_type=float(np.corrcoef(j.ref, j.cand)[0, 1]) if len(j) > 2 else None,
        )
    res = ROOT / "results" / "d105"
    res.mkdir(parents=True, exist_ok=True)
    with open(res / "fig1d_compare.json", "w") as fh:
        json.dump(out, fh, indent=1)
    for k, v in out.items():
        mn = v["mn9"]
        curve = " ".join(f"{mn.get(f, 0.0):.1f}" for f in (40, 60, 100, 150, 200))
        print(f"{k:32s} MN9@40/60/100/150/200 = {curve:28s} ativos={v['n_active_200']:4d} "
              f"top200∩ref={v.get('top200_types_in_ref', '-')}/{v['top200_types']} "
              f"r_tipo={v.get('pearson_by_type')}")


if __name__ == "__main__":
    main()
