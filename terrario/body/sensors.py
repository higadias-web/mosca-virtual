"""Sensores da mosca no terrário (Fase 2): o que o corpo e o ambiente oferecem aos neurônios.

Aqui só se MEDE o estímulo físico em cada órgão sensorial. Converter em taxa de disparo de
neurônios anotados (ORNs, GRNs, mecanossensores) é a codificação sensorial da Fase 3, depois da
⚠️ D-105 (o conectoma define quais neurônios existem para receber cada sinal).

Canais (um `SensorFrame` por chamada de `read()`, a cada 1 ms de simulação, D-006):
  olfato        concentração de cada canal de odor em cada antena (funículo E/D), e temperatura
                nas antenas (termossensores antenais). FlyGym 2.x não tem olfato (D-002): a
                amostragem é nossa, na posição de `l_funiculus`/`r_funiculus`
                (Simulation.get_body_positions).
  gustação      por órgão gustativo (6 tarsos + labelo): superfície tocada (código de
                terrario.world.terrarium.SURFACES) e força normal. Tarso = segmentos tarsus1..5
                de cada perna; labelo = c_haustellum.
  mecanossensação  força de contato (norma, mN·mm/s² do MuJoCo) em cada segmento com contato.
  propriocepção ângulos e velocidades das juntas (Simulation.get_joint_angles/velocities) e
                forças dos atuadores de posição.
  corpo         posição e orientação do tórax, velocidade linear (para log e replay).
  luz           nível de luz ambiente (ciclo dia/noite).
  visão         opcional (perfil `completo`): Simulation.get_ommatidia_readouts, à taxa
                `vision_hz` (desligada por padrão; SPEC, consequência 4).

Leitura dos contatos: como em Simulation.get_bodysegment_contact_forces (flygym/simulation.py),
mas guardando QUAL geom do chão foi tocado, para saber a superfície.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import mujoco as mj
import numpy as np

from flygym.anatomy import LEGS, BodySegment
from flygym.compose import ActuatorType

from terrario.world.terrarium import CONTACT_SEGMENTS, SURFACE_CODE

TASTE_ORGANS = [*LEGS, "labellum"]  # lf lm lh rf rm rh labellum
ANTENNAE = ["l_funiculus", "r_funiculus"]


@dataclass
class SensorFrame:
    t: float
    odor: np.ndarray            # (2 antenas, canais)
    antenna_temp_c: np.ndarray  # (2,)
    light: float
    taste_surface: np.ndarray   # (7,) int8, código da superfície (0 = sem contato)
    taste_force: np.ndarray     # (7,) força normal somada, na unidade do MuJoCo
    contact_force: np.ndarray   # (n_segmentos de contato,) norma da força
    joint_angles: np.ndarray
    joint_velocities: np.ndarray
    actuator_forces: np.ndarray
    thorax_pos: np.ndarray      # (3,)
    thorax_quat: np.ndarray     # (4,)
    thorax_vel: np.ndarray      # (3,)
    ommatidia: np.ndarray | None = field(default=None)


class FlySensors:
    def __init__(self, sim, fly, world, env, vision_hz: float = 0.0) -> None:
        self.sim, self.fly, self.world, self.env = sim, fly, world, env
        self.vision_hz = vision_hz
        self._next_vision_t = 0.0
        m = sim.mj_model
        order = fly.get_bodysegs_order()
        names = [s.name for s in order]
        self._ant_idx = [names.index(a) for a in ANTENNAE]
        self._thorax_idx = names.index("c_thorax")
        self._thorax_bodyid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{fly.name}/c_thorax")

        # geom -> (índice do segmento de contato, órgão gustativo ou -1)
        self.contact_segments = [s.name for s in CONTACT_SEGMENTS]
        self._geom_seg = {}
        for k, seg in enumerate(CONTACT_SEGMENTS):
            for g in fly.bodyseg_to_mjcfgeom[seg]:
                gid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, g.name)  # já tem o prefixo da mosca
                organ = -1
                if seg.name == "c_haustellum":
                    organ = TASTE_ORGANS.index("labellum")
                elif seg.is_leg() and seg.link.startswith("tarsus"):
                    organ = TASTE_ORGANS.index(seg.pos)
                self._geom_seg[gid] = (k, organ)
        # geom do chão -> nome
        self._ground = {mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, g.name): g.name
                        for g in world.ground_geoms}
        self._wrench = np.zeros(6)

    def _contacts(self):
        d = self.sim.mj_data
        nseg = len(self.contact_segments)
        cforce = np.zeros(nseg)
        tsurf = np.zeros(len(TASTE_ORGANS), dtype=np.int8)
        tforce = np.zeros(len(TASTE_ORGANS))
        n = d.ncon
        if n == 0:
            return cforce, tsurf, tforce
        con = d.contact
        g1, g2 = con.geom1[:n], con.geom2[:n]
        for c in range(n):
            a, b = int(g1[c]), int(g2[c])
            if a in self._geom_seg and b in self._ground:
                fg, gg = a, b
            elif b in self._geom_seg and a in self._ground:
                fg, gg = b, a
            else:
                continue
            mj.mj_contactForce(self.sim.mj_model, d, c, self._wrench)
            fn = abs(self._wrench[0])                   # componente normal (frame do contato)
            k, organ = self._geom_seg[fg]
            cforce[k] += float(np.linalg.norm(self._wrench[:3]))
            if organ >= 0:
                surf = self.world.surface_of_geom(self._ground[gg], con.pos[c])
                # se o órgão toca duas superfícies, fica a de maior força
                if fn > tforce[organ]:
                    tsurf[organ] = SURFACE_CODE[surf]
                tforce[organ] += fn
        return cforce, tsurf, tforce

    def read(self) -> SensorFrame:
        sim, fly = self.sim, self.fly
        t = sim.time
        pos = sim.get_body_positions(fly.name)
        ant = pos[self._ant_idx]
        cforce, tsurf, tforce = self._contacts()
        om = None
        if self.vision_hz > 0 and t + 1e-12 >= self._next_vision_t:
            om = sim.get_ommatidia_readouts(fly.name)
            self._next_vision_t += 1.0 / self.vision_hz
        vel = np.zeros(6)
        mj.mj_objectVelocity(sim.mj_model, sim.mj_data, mj.mjtObj.mjOBJ_BODY,
                             self._thorax_bodyid, vel, 0)
        return SensorFrame(
            t=t,
            odor=self.env.odor.sample(ant[:, :2]),
            antenna_temp_c=self.env.temperature.sample(ant[:, :2]),
            light=self.env.light.level(t),
            taste_surface=tsurf, taste_force=tforce, contact_force=cforce,
            joint_angles=sim.get_joint_angles(fly.name).copy(),
            joint_velocities=sim.get_joint_velocities(fly.name).copy(),
            actuator_forces=sim.get_actuator_forces(fly.name, ActuatorType.POSITION).copy(),
            thorax_pos=pos[self._thorax_idx].copy(),
            thorax_quat=sim.get_body_rotations(fly.name)[self._thorax_idx].copy(),
            thorax_vel=vel[3:].copy(),
            ommatidia=om,
        )
