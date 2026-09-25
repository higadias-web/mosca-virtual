"""Conectoma FlyWire no formato do modelo de Shiu et al. 2024.

Fonte: third_party/Drosophila_brain_model (commit 91bdd1e), arquivos
  v630: 2023_03_23_completeness_630_final.csv + 2023_03_23_connectivity_630_final.parquet
  v783: Completeness_783.csv + Connectivity_783.parquet
Mesma construção de model.py:create_model: índice do neurônio = ordem das linhas do
arquivo de completude; peso = 'Excitatory x Connectivity' (sinal x número de sinapses).

O CSR é salvo em cache (data/cache/flywire_<versão>.npz) para evitar a leitura do Parquet
via pandas, que custa ~3 GB de RAM de pico.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np

from terrario import DATA, THIRD_PARTY

SHIU_DIR = THIRD_PARTY / "Drosophila_brain_model"
FILES = {
    "630": ("2023_03_23_completeness_630_final.csv", "2023_03_23_connectivity_630_final.parquet"),
    "783": ("Completeness_783.csv", "Connectivity_783.parquet"),
}


@dataclass
class FlyWireConnectome:
    version: str
    flyids: np.ndarray    # int64, flyid do neurônio i
    indptr: np.ndarray    # CSR por neurônio PRÉ-sináptico
    indices: np.ndarray   # int32, pós-sináptico
    syn_count: np.ndarray  # float64, 'Excitatory x Connectivity' (com sinal)

    @property
    def n(self) -> int:
        return len(self.flyids)

    @cached_property
    def flyid2i(self) -> dict[int, int]:
        return {int(f): i for i, f in enumerate(self.flyids)}

    def idx(self, flyids) -> np.ndarray:
        """Índices dos flyids (KeyError se algum não existir nesta versão)."""
        m = self.flyid2i
        return np.array([m[int(f)] for f in flyids], dtype=np.int64)


def load(version: str = "783", cache: bool = True) -> FlyWireConnectome:
    if version not in FILES:
        raise ValueError(f"versão desconhecida: {version}")
    path_cache = DATA / "cache" / f"flywire_{version}.npz"
    if cache and path_cache.exists():
        z = np.load(path_cache)
        return FlyWireConnectome(version, z["flyids"], z["indptr"], z["indices"], z["syn_count"])

    import pandas as pd
    import scipy.sparse as sp

    comp, con = FILES[version]
    df_comp = pd.read_csv(SHIU_DIR / comp, index_col=0)
    df_con = pd.read_parquet(SHIU_DIR / con, columns=[
        "Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"])
    n = len(df_comp)
    W = sp.csr_matrix(
        (df_con["Excitatory x Connectivity"].to_numpy(np.float64),
         (df_con["Presynaptic_Index"].to_numpy(), df_con["Postsynaptic_Index"].to_numpy())),
        shape=(n, n))
    W.sum_duplicates()  # Brian2 soma sinapses duplicadas; nos arquivos não há duplicatas
    c = FlyWireConnectome(version, df_comp.index.to_numpy(np.int64), W.indptr.astype(np.int64),
                          W.indices.astype(np.int32), W.data.astype(np.float64))
    if cache:
        path_cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path_cache, flyids=c.flyids, indptr=c.indptr, indices=c.indices,
                 syn_count=c.syn_count)
    return c
