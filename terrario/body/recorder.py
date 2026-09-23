"""Gravação dos sensores em Parquet (colunar), reduzida para `hz` (SPEC: 100–200 Hz no replay).

Protótipo do log da Fase 6: mesmas colunas que o log unificado terá para a mosca. Os metadados
(config da arena, semente, versões) vão no schema do Parquet.
"""

from __future__ import annotations

import json

import numpy as np

from terrario.body.sensors import SensorFrame

_ARRAYS = ["odor", "antenna_temp_c", "taste_surface", "taste_force", "contact_force",
           "joint_angles", "joint_velocities", "actuator_forces", "thorax_pos", "thorax_quat",
           "thorax_vel"]


class SensorRecorder:
    def __init__(self, hz: float = 200.0) -> None:
        self.period = 1.0 / hz
        self._next = 0.0
        self.rows: list[SensorFrame] = []

    def maybe_add(self, f: SensorFrame) -> None:
        if f.t + 1e-12 >= self._next:
            self.rows.append(f)
            self._next += self.period
            if self._next <= f.t:  # começou atrasado (ex.: depois do warmup): realinha
                self._next = f.t + self.period

    def arrays(self) -> dict[str, np.ndarray]:
        out = {"t": np.array([r.t for r in self.rows]), "light": np.array([r.light for r in self.rows])}
        for k in _ARRAYS:
            out[k] = np.stack([getattr(r, k) for r in self.rows])
        return out

    def to_parquet(self, path, meta: dict) -> int:
        import pyarrow as pa
        import pyarrow.parquet as pq

        a = self.arrays()
        cols = {}
        for k, v in a.items():
            if v.ndim == 1:
                cols[k] = pa.array(v)
            else:
                flat = v.reshape(len(v), -1)
                cols[k] = pa.FixedSizeListArray.from_arrays(
                    pa.array(flat.ravel().astype(np.float32 if v.dtype.kind == "f" else v.dtype)),
                    flat.shape[1])
        tbl = pa.table(cols).replace_schema_metadata({"terrario": json.dumps(meta)})
        pq.write_table(tbl, path, compression="zstd")
        return path.stat().st_size
