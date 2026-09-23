"""Transdução proprioceptiva da Fase 3a: estado das pernas → taxas de Poisson nos sensores do BANC.

Neurônios (BANC v888, `cell_sub_class`, lado por `side`):
  claw  <perna>_claw_chordotonal_organ_neuron  → POSIÇÃO do fêmur–tíbia (FTi)
  hook  <perna>_hook_chordotonal_organ_neuron  → DIREÇÃO do movimento do FTi
  club  <perna>_club_chordotonal_organ_neuron  → movimento/vibração do FTi (bidirecional)
  hair plates <perna>_hair_plate_neuron        → ângulo de juntas proximais (ThC pitch, CTr pitch)
  campaniformes <perna>_campaniform_…          → carga (força de contato da perna na bola)
Funções dos três subtipos do órgão cordotonal femoral: Mamiya, Gurung & Tuthill 2018, Neuron,
"Neural coding of leg proprioception in Drosophila" (claw: posição, com subgrupos de flexão e de
extensão e limiares em faixas; hook: direção; club: movimento/vibração).

NON-CONNECTOME (tudo): as curvas de ajuste, as taxas máximas e, principalmente, QUAL neurônio é de
flexão ou de extensão e qual é o seu limiar. O BANC não anota isso por neurônio; a atribuição é
pseudoaleatória e reprodutível (semente fixa, metade de cada sentido, limiares espalhados na faixa
da junta). A Sessão 2 testa a sensibilidade a essa atribuição (outras sementes).
Na mosca real a fração de cada subgrupo não é necessariamente 1/2.
"""

from __future__ import annotations

import numpy as np

from terrario.vnc.apparatus import dof_name

R_MAX = 100.0          # Hz
W_RAD = 0.15           # largura da sigmoide de posição (rad)
V_SAT = 10.0           # rad/s: velocidade que satura hook/club
F_SAT = 20.0           # força de contato que satura os campaniformes (unidade do MuJoCo)
# Faixa (percentis 5–95) de cada ângulo durante a marcha do CPG do FlyGym na Fase 2
# (runs/phase2/walk_soil_fruit_landscape.parquet); os limiares dos sensores de posição ficam nela.
_R = {"thc_pitch": {"f": (0.17, 0.67), "m": (-0.21, 0.35), "h": (0.36, 0.83)},
      "ctr_pitch": {"f": (-2.70, -1.81), "m": (-1.73, -1.16), "h": (-2.18, -1.38)},
      "fti_pitch": {"f": (1.28, 2.18), "m": (1.86, 2.23), "h": (1.15, 2.22)}}
LEGPOS = {"front": "f", "middle": "m", "hind": "h"}


def _leg(sub: str, side: str) -> str | None:
    for k, v in LEGPOS.items():
        if sub.startswith(f"{k}_leg"):
            return ("l" if side == "left" else "r") + v
    return None


class Proprioception:
    def __init__(self, meta, hidx, jdof_order: list[str], seed: int = 0):
        """meta: banc.load_meta(); hidx(banc_ids) → índices no conectoma; jdof_order: nomes dos
        DOFs na ordem de Simulation.get_joint_angles."""
        rng = np.random.default_rng(seed)
        sub = meta["cell_sub_class"].astype(str)
        rows = []
        for kind, pat in [("claw", "_claw_chordotonal_organ_neuron"),
                          ("hook", "_hook_chordotonal_organ_neuron"),
                          ("club", "_club_chordotonal_organ_neuron"),
                          ("hair", "_hair_plate_neuron"),
                          ("cs", "campaniform_sensillum_neuron")]:
            x = meta[sub.str.endswith(pat) & sub.str.contains("_leg_")]
            for bid, s, side in zip(x["banc_888_id"], sub[x.index], x["side"]):
                leg = _leg(s, side)
                if leg:
                    rows.append((int(bid), kind, leg))
        ids = [r[0] for r in rows]
        h = hidx(ids)
        keep = [k for k, v in enumerate(h) if v >= 0]
        self.h = np.array([h[k] for k in keep], dtype=np.int64)
        self.kind = np.array([rows[k][1] for k in keep])
        self.leg = np.array([rows[k][2] for k in keep])
        n = len(self.h)
        self.direction = rng.choice([-1.0, 1.0], n)       # flexão (−) ou extensão (+) do ângulo
        self.dof = np.empty(n, dtype=object)
        for k in range(n):
            if self.kind[k] in ("claw", "hook", "club"):
                self.dof[k] = "fti_pitch"
            elif self.kind[k] == "hair":
                self.dof[k] = "thc_pitch" if rng.random() < 0.5 else "ctr_pitch"
            else:
                self.dof[k] = None
        self.theta = np.array([rng.uniform(*_R[d][lg[1]]) if d else 0.0
                               for d, lg in zip(self.dof, self.leg)])
        self.jidx = np.array([jdof_order.index(dof_name(lg, d)) if d else -1
                              for lg, d in zip(self.leg, self.dof)])
        self.legi = np.array(["lf lm lh rf rm rh".split().index(lg) for lg in self.leg])

    def counts(self) -> dict:
        return {k: int((self.kind == k).sum()) for k in np.unique(self.kind)}

    def rates(self, q: np.ndarray, qd: np.ndarray, leg_force: np.ndarray) -> np.ndarray:
        """q, qd: ângulos e velocidades (ordem jdof_order); leg_force: (6,) força de contato."""
        r = np.zeros(len(self.h))
        j = self.jidx
        ang = np.where(j >= 0, q[np.maximum(j, 0)], 0.0)
        vel = np.where(j >= 0, qd[np.maximum(j, 0)], 0.0)
        pos = (self.kind == "claw") | (self.kind == "hair")
        r[pos] = R_MAX / (1 + np.exp(-self.direction[pos] * (ang[pos] - self.theta[pos]) / W_RAD))
        hk = self.kind == "hook"
        r[hk] = R_MAX * np.clip(self.direction[hk] * vel[hk] / V_SAT, 0, 1)
        cl = self.kind == "club"
        r[cl] = R_MAX * np.clip(np.abs(vel[cl]) / V_SAT, 0, 1)
        cs = self.kind == "cs"
        r[cs] = R_MAX * np.clip(leg_force[self.legi[cs]] / F_SAT, 0, 1)
        return r
