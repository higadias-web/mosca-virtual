"""Compara a reprodução (runs/phase1/<versão>/*.parquet) com os resultados publicados do
Shiu et al. 2024 (results.zip do Edmond, doi:10.17617/3.CZODIW, em data/shiu_published).

Critério estatístico: para cada (condição, neurônio), z = (r_nosso - r_pub) / EP, com
EP = sqrt((sd_pub² + sd_nosso²) / 30). Se as duas simulações amostram o mesmo modelo,
|z| > 3 deve ocorrer em ~0,3 % dos casos (um pouco mais com contagens baixas, não gaussianas).

Uso: uv run python -m experiments.compare_shiu fig1d [--version 630]
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from terrario import ROOT
from experiments.shiu_repro import MN9_L, N_RUN, PUB, _top200


def _pub_long(rate_csv, std_csv):
    r = pd.read_csv(rate_csv, index_col=0)
    s = pd.read_csv(std_csv, index_col=0)
    r = r.drop(columns=[c for c in ("name",) if c in r.columns])
    s = s.drop(columns=[c for c in ("name",) if c in s.columns])
    lr = r.stack().rename("rate_pub")
    ls = s.stack().rename("std_pub")
    df = pd.concat([lr, ls], axis=1).reset_index()
    df.columns = ["flyid", "exp_name", "rate_pub", "std_pub"]
    df["flyid"] = df["flyid"].astype(np.int64)
    return df


def _pub_mn9(files):
    """CSVs com uma coluna por neurônio (MN9), linhas = exp_name."""
    out = []
    for rf, sf in files:
        r = pd.read_csv(rf, index_col=0)
        s = pd.read_csv(sf, index_col=0)
        col = r.columns[0]
        out.append(pd.DataFrame({"exp_name": r.index, "flyid": MN9_L,
                                 "rate_pub": r[col].to_numpy(), "std_pub": s[col].to_numpy()}))
    return pd.concat(out, ignore_index=True)


def stats(m: pd.DataFrame) -> dict:
    se = np.sqrt((m.std_pub**2 + m["std"] ** 2) / N_RUN)
    diff = m.rate - m.rate_pub
    z = np.where(se > 0, diff / se.where(se > 0, 1), np.where(diff == 0, 0.0, np.inf))
    sig = (m.rate_pub + m.rate) >= 1.0  # ignora taxas ínfimas (contagens quase nulas)
    out = m.assign(z=z)[sig & (np.abs(z) > 3)]
    outliers = out.sort_values("z", key=np.abs, ascending=False)[
        ["exp_name", "flyid", "rate_pub", "rate", "z"]].round(3).values.tolist()
    return dict(
        outliers_abs_z_gt3=outliers,
        n_pairs=int(len(m)), n_pairs_ge_0p5Hz=int(sig.sum()),
        pearson_r=float(np.corrcoef(m.rate, m.rate_pub)[0, 1]),
        frac_abs_z_gt3=float((np.abs(z[sig]) > 3).mean()) if sig.any() else 0.0,
        n_abs_z_gt3=int((np.abs(z[sig]) > 3).sum()),
        n_abs_z_gt4=int((np.abs(z[sig]) > 4).sum()),
        total_rate_rel_diff=float(m.rate.sum() / m.rate_pub.sum() - 1),
        median_abs_rel_diff_top=float(np.median(
            np.abs(diff[m.rate_pub > 20] / m.rate_pub[m.rate_pub > 20]))) if (m.rate_pub > 20).any() else None,
    )


def compare(exp: str, version: str) -> dict:
    d = ROOT / "runs" / "phase1" / version
    parts = [d / f"{exp}.parquet"] if (d / f"{exp}.parquet").exists() else sorted(d.glob(f"{exp}_*.parquet"))
    ours = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    if exp == "fig1d":
        pub = _pub_long(PUB / "figure_1" / "fig_1d_rate.csv", PUB / "figure_1" / "fig_1d_rate_std.csv")
    elif exp == "fig3a":
        pub = _pub_mn9([(PUB / "figure_3" / "fig_3a_rate.csv", PUB / "figure_3" / "fig_3a_rate_std.csv")])
    elif exp in ("fig1e", "fig1f"):
        tag = exp[-2:]
        import glob
        rfs = sorted(glob.glob(str(PUB / "figure_1" / f"fig_{tag}_*_hz_rate.csv")))
        pub = _pub_mn9([(f, f.replace("_rate.csv", "_rate_std.csv")) for f in rfs])
    else:
        raise ValueError(exp)
    # condições = todas as simuladas (antes de filtrar o MN9: MN9 = 0 Hz também conta)
    conds = set(ours.exp_name)
    if exp != "fig1d":
        ours = ours[ours.flyid == MN9_L]
    pub = pub[pub.exp_name.isin(conds)]
    m = pub.merge(ours, on=["exp_name", "flyid"], how="outer").fillna(
        {"rate": 0.0, "std": 0.0, "rate_pub": 0.0, "std_pub": 0.0})
    res = {"exp": exp, "version": version, "conditions": len(conds), **stats(m)}
    if exp == "fig1d":
        res["active_neurons_200Hz"] = {
            "pub": int((m[m.exp_name == "sugarR_200Hz"].rate_pub > 0).sum()),
            "ours": int((m[m.exp_name == "sugarR_200Hz"].rate > 0).sum())}
        top_pub = _top200()
        o200 = m[m.exp_name == "sugarR_200Hz"].sort_values("rate", ascending=False).flyid[:200]
        res["top200_overlap"] = len(set(top_pub) & set(o200.astype(int)))
        mn = m[m.flyid == MN9_L].copy()
        mn["f"] = mn.exp_name.str.extract(r"(\d+)Hz").astype(int)
        res["mn9_curve"] = mn.sort_values("f")[["f", "rate_pub", "rate"]].round(2).values.tolist()
    if exp == "fig3a":
        g = m.copy()
        g[["s", "b"]] = g.exp_name.str.extract(r"Sugar_Bitter_(\d+)_Hz_(\d+)_Hz").astype(int)
        res["grid_pub"] = g.pivot(index="s", columns="b", values="rate_pub").round(1).values.tolist()
        res["grid_ours"] = g.pivot(index="s", columns="b", values="rate").round(1).values.tolist()
    out = ROOT / "runs" / "phase1" / version / f"{exp}_compare.json"
    out.write_text(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("--version", default="630")
    a = ap.parse_args()
    r = compare(a.exp, a.version)
    for k, v in r.items():
        if k not in ("grid_pub", "grid_ours"):
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
