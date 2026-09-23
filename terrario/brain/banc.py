"""Conectoma BANC v888 (cérebro + cordão nervoso ventral da mesma mosca) no formato do Shiu.

Fonte: Harvard Dataverse doi:10.7910/DVN/7WTH1N, versão 3 (2026-07-01), baixado em data/banc/:
  banc_888_meta.feather               metadados por neurônio (81 colunas)
  banc_888_edgelist_simple_v2.feather arestas neurônio→neurônio (pre, post, count, ...)
A escolha da edgelist v2 (sinapses v2 com tamanho >= 5) segue o padrão do próprio projeto:
third_party/BANC-project/R/startup/banc-edgelist.R ("2026-04-21: flipped consumer-side default
from v3 to v2"). Os mesmos filtros daquele arquivo são aplicados aqui:
  - só neurônios `proofread` ou `roughly_proofread` (nas duas pontas da aresta);
  - sem autoconexões (pre == post); sem limiar global de contagem.
Excluímos também o que não é neurônio (super_class glia, not_a_neuron, trachea).

Sinal (NON-CONNECTOME, mesma regra do Shiu na v783, conferida em Connectivity_783.parquet contra
top_nt das anotações: GABA/glutamato → −1, demais → +1). Diferença necessária: o BANC prevê
histamina, que o FlyWire não previa. Histamina entra como inibitória (receptores ort/HisCl1 são
canais de cloreto). Afeta quase só a óptica (fotorreceptores; ver docs/DECISIONS.md D-105).
Neurônios sem previsão de transmissor ficam +1, como o "demais" do Shiu.
"""

from __future__ import annotations

import numpy as np

from terrario import DATA
from terrario.brain.flywire import FlyWireConnectome

BANC_DIR = DATA / "banc"
META = BANC_DIR / "banc_888_meta.feather"
EDGES = {"v2": BANC_DIR / "banc_888_edgelist_simple_v2.feather",
         "v3": BANC_DIR / "banc_888_edgelist_simple_v3.feather"}
NOT_NEURON = {"glia", "not_a_neuron", "trachea"}
INHIBITORY = {"gaba", "glutamate", "histamine"}


def load_meta():
    """Metadados dos neurônios incluídos no modelo, na ordem dos índices do modelo."""
    import pandas as pd

    m = pd.read_feather(META)
    pr = (m["proofread"].astype(str).str.upper() == "TRUE") | \
         (m["roughly_proofread"].astype(str).str.upper() == "TRUE")
    m = m[pr & ~m["super_class"].isin(NOT_NEURON)]
    m = m.drop_duplicates("banc_888_id").copy()
    m["banc_888_id"] = m["banc_888_id"].astype(np.int64)
    m = m.sort_values("banc_888_id").reset_index(drop=True)
    m["sign"] = np.where(m["neurotransmitter_predicted"].isin(INHIBITORY), -1, 1)
    return m


SIGN_MODES = ("predicted", "verified", "verified_gluexc")


def neuron_signs(m, mode: str = "predicted") -> np.ndarray:
    """Sinal (+1/−1) de cada neurônio de `load_meta()` para a H6 da Fase 3a.

    predicted        transmissor previsto pelo BANC (`neurotransmitter_predicted`), regra do Shiu
                     com histamina inibitória. É o padrão de `load()`.
    verified         `neurotransmitter_verified` (1º transmissor da lista) quando existe; senão, o
                     verificado mais comum da mesma hemilinhagem (no VNC o transmissor rápido é
                     fixo por hemilinhagem: Lacin et al. 2019, eLife); senão, o previsto. Todos os
                     motoneurônios (super_class motor) = glutamato: os MNs de Drosophila são
                     glutamatérgicos; a previsão do BANC para eles tem score mediano 0,47 (H6).
    verified_gluexc  como `verified`, mas glutamato EXCITATÓRIO nos neurônios do VNC (teste de
                     sensibilidade de classe inteira; sem base documentada para o VNC todo).
    NON-CONNECTOME: regra de sinal e as substituições acima.
    """
    if mode not in SIGN_MODES:
        raise ValueError(mode)
    nt = m["neurotransmitter_predicted"].astype(object).copy()
    if mode != "predicted":
        ver = m["neurotransmitter_verified"].astype(str).str.split(",").str[0]
        ver = ver.where(m["neurotransmitter_verified"].notna())
        hl = m["hemilineage"]
        cons = ver.groupby(hl).agg(lambda x: x.value_counts().index[0] if x.notna().any() else None)
        by_hl = hl.map(cons)
        nt = ver.fillna(by_hl.where(m["region"] == "ventral_nerve_cord")).fillna(nt)
        nt[m["super_class"] == "motor"] = "glutamate"
    sign = np.where(nt.isin(INHIBITORY), -1, 1)
    if mode == "verified_gluexc":
        sign[((nt == "glutamate") & (m["region"] == "ventral_nerve_cord")).to_numpy()] = 1
    return sign


def load(edges: str = "v2", cache: bool = True) -> FlyWireConnectome:
    """Conectoma BANC no mesmo contêiner CSR do FlyWire (flyids = banc_888_id)."""
    path_cache = DATA / "cache" / f"banc_888_{edges}.npz"
    version = f"banc888{'' if edges == 'v2' else edges}"
    if cache and path_cache.exists():
        z = np.load(path_cache)
        return FlyWireConnectome(version, z["flyids"], z["indptr"], z["indices"], z["syn_count"])

    import pandas as pd
    import scipy.sparse as sp

    m = load_meta()
    ids = m["banc_888_id"].to_numpy()
    e = pd.read_feather(EDGES[edges], columns=["pre", "post", "count"])
    pre = e["pre"].astype(np.int64).to_numpy()
    post = e["post"].astype(np.int64).to_numpy()
    ip, iq = np.searchsorted(ids, pre), np.searchsorted(ids, post)
    ip[ip == len(ids)] = 0
    iq[iq == len(ids)] = 0
    ok = (ids[ip] == pre) & (ids[iq] == post) & (pre != post)
    w = e["count"].to_numpy(np.float64)[ok] * m["sign"].to_numpy()[ip[ok]]
    W = sp.csr_matrix((w, (ip[ok], iq[ok])), shape=(len(ids), len(ids)))
    W.sum_duplicates()
    c = FlyWireConnectome(version, ids, W.indptr.astype(np.int64), W.indices.astype(np.int32),
                          W.data.astype(np.float64))
    if cache:
        path_cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path_cache, flyids=c.flyids, indptr=c.indptr, indices=c.indices,
                 syn_count=c.syn_count)
    return c
