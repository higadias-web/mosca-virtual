"""Aparato da Fase 3a: mosca presa sobre bola, movida por motoneurônios do cordão do BANC.

Tudo aqui é NON-CONNECTOME (aparato, biomecânica e transdução), listado em docs/NON_CONNECTOME.md.

Bola: parâmetros da `Ball` do FlyGym 1.x (third_party/flygym-gymnasium/flygym_gymnasium/arena/
tethered.py, NeuroMechFly v1): raio 5,3909 mm, massa 54,56 mg, atrito (1,3; 0,005; 0,0001),
junta esférica sem limites. O FlyGym 2.1 só tem `TetheredWorld` (tórax como corpo mocap), então a
bola é portada aqui para MjSpec. A altura da bola é ajustada para os tarsos tocarem nela na pose
neutra (como o posicionamento feito à mão no experimento).

Corpo: mesmo esqueleto e parâmetros passivos de `make_locomotion_fly` (flygym_demo), mas com
atuadores de TORQUE (motor) nos 42 graus de liberdade ativos das pernas, no lugar dos de posição.
Sem adesão tarsal (a bola é leve; o atrito das garras basta para girá-la).
"""

from __future__ import annotations

from dataclasses import dataclass

import mujoco as mj
import numpy as np

from flygym.anatomy import (ActuatedDOFPreset, AxisOrder, BodySegment, JointPreset,
                            PASSIVE_TARSAL_LINKS, Skeleton)
from flygym.compose import ActuatorType, KinematicPosePreset, NeuroMechFly
from flygym.compose.physics import ContactParams
from flygym.compose.world.base_world import BaseWorld, _GroundContactMixin
from flygym.utils.mjcf import GEOM_TYPES, JOINT_TYPES

from terrario.vnc.motor_map import LEGS

# FlyGym 1.x Ball (tethered.py): raio, posição relativa ao tórax, massa (g), atritos
BALL_RADIUS = 5.390852782067457
BALL_POS = (-0.09867235483, -0.05435809692, -5.20309506806)
BALL_MASS = 0.05456
BALL_FRICTION = (1.3, 0.005, 0.0001)
TORQUE_LIMIT = 65.0  # mesmo forcerange dos atuadores de posição de make_locomotion_fly

LEG_SEGS = [BodySegment(f"{leg}_{lk}") for leg in LEGS
            for lk in ("tibia", "tarsus1", "tarsus2", "tarsus3", "tarsus4", "tarsus5")]


def make_neuromuscular_fly(name: str = "fly") -> NeuroMechFly:
    """Como flygym_demo.complex_terrain.common.make_locomotion_fly, com atuadores de torque."""
    neutral = KinematicPosePreset.NEUTRAL.get_pose_by_axis_order(AxisOrder.YAW_PITCH_ROLL)
    sk = Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY)
    fly = NeuroMechFly(name=name)
    joints = fly.add_joints(sk, neutral_pose=neutral, stiffness=0.05, damping=0.06)
    for jd, j in joints.items():
        if jd.child.link in PASSIVE_TARSAL_LINKS:
            j.stiffness[0] = 7.5
            j.damping[0] = 1e-2
    dofs = sk.get_actuated_dofs_from_preset(ActuatedDOFPreset.LEGS_ACTIVE_ONLY)
    fly.add_actuators(dofs, ActuatorType.MOTOR, forcerange=(-TORQUE_LIMIT, TORQUE_LIMIT), gear=1.0)
    fly.colorize()
    return fly


class TetheredBallWorld(_GroundContactMixin, BaseWorld):
    """Tórax fixo (mocap, como flygym.compose.world.TetheredWorld) sobre uma bola livre."""

    def __init__(self, name: str = "bola", ball_z_offset: float = 0.0) -> None:
        super().__init__(name=name)
        pos = (BALL_POS[0], BALL_POS[1], BALL_POS[2] + ball_z_offset)
        body = self.mjcf_root.worldbody.add_body(name="ball", pos=pos)
        body.add_joint(name="ball_joint", type=JOINT_TYPES["ball"])
        self.ball_geom = body.add_geom(name="ball", type=GEOM_TYPES["sphere"],
                                       size=(BALL_RADIUS, 0, 0), mass=BALL_MASS,
                                       rgba=(0.55, 0.55, 0.52, 1), contype=0, conaffinity=0)
        self.ground_geoms = [self.ball_geom]
        self.mjcf_root.worldbody.add_light(name="luz", pos=(0, 0, 40), dir=(0, 0, -1),
                                           diffuse=(0.6, 0.6, 0.6), castshadow=False)
        self.mjcf_root.worldbody.add_camera(name="lateral", pos=(0, -9, 1.0),
                                            xyaxes=(1, 0, 0, 0, 0.1, 1))

    def _attach_fly_mjcf(self, fly, spawn_position, spawn_rotation, *args, **kwargs):
        site = self.mjcf_root.worldbody.add_site(name=fly.name, pos=spawn_position,
                                                 **spawn_rotation.as_kwargs())
        self.mjcf_root.attach(fly.mjcf_root, prefix=f"{fly.name}/", site=site)
        fly.bodyseg_to_mjcfbody[fly.root_segment].mocap = True  # como TetheredWorld
        self._set_ground_contact(fly, LEG_SEGS, ContactParams(sliding_friction=BALL_FRICTION[0],
                                                              torsional_friction=BALL_FRICTION[1],
                                                              rolling_friction=BALL_FRICTION[2]))
        return set()


@dataclass
class BallScene:
    sim: object
    fly: NeuroMechFly
    world: TetheredBallWorld
    ball_qadr: int
    ball_vadr: int


def build_ball_scene(ball_z_offset: float = 0.0) -> BallScene:
    from flygym import Simulation
    from flygym.utils.math import Rotation3D
    fly = make_neuromuscular_fly()
    world = TetheredBallWorld(ball_z_offset=ball_z_offset)
    world.add_fly(fly, [0, 0, 0], Rotation3D("quat", [1, 0, 0, 0]))
    sim = Simulation(world)
    jid = mj.mj_name2id(sim.mj_model, mj.mjtObj.mjOBJ_JOINT, "ball_joint")
    return BallScene(sim, fly, world, int(sim.mj_model.jnt_qposadr[jid]), int(sim.mj_model.jnt_dofadr[jid]))


# ------------------------------------------------------------------------------ MN → torque
# (junta, papel) → (sufixo do DOF, sinal). O sinal de FLEXÃO de cada DOF foi medido com torque
# imposto (tests/test_apparatus.py::test_flexion_signs) e está em FLEX_SIGN.
ROLE_DOF = {
    ("ThC", "promotor"): ("thc_pitch", +1), ("ThC", "remotor"): ("thc_pitch", -1),
    ("ThC", "rotator_ant"): ("thc_roll", +1), ("ThC", "rotator_post"): ("thc_roll", -1),
    ("ThC", "adductor"): ("thc_yaw", +1),
    ("CTr", "flexor"): ("ctr_pitch", +1), ("CTr", "extensor"): ("ctr_pitch", -1),
    ("TrF", "reductor"): ("trf_roll", +1),
    ("FTi", "flexor"): ("fti_pitch", +1), ("FTi", "extensor"): ("fti_pitch", -1),
    ("TiTa", "depressor"): ("tita_pitch", +1), ("TiTa", "levator"): ("tita_pitch", -1),
}


def dof_name(leg: str, key: str) -> str:
    return {"thc_yaw": f"c_thorax-{leg}_coxa-yaw", "thc_pitch": f"c_thorax-{leg}_coxa-pitch",
            "thc_roll": f"c_thorax-{leg}_coxa-roll",
            "ctr_pitch": f"{leg}_coxa-{leg}_trochanterfemur-pitch",
            "trf_roll": f"{leg}_coxa-{leg}_trochanterfemur-roll",
            "fti_pitch": f"{leg}_trochanterfemur-{leg}_tibia-pitch",
            "tita_pitch": f"{leg}_tibia-{leg}_tarsus1-pitch"}[key]


# sinal do torque que FLEXIONA cada DOF de pitch (medido; ver teste). Para ThC/TrF roll/yaw o
# "+1" do papel é só uma convenção de antagonismo (sem sentido anatômico validado ainda).
# Medido na Sessão 1 (bola afastada, 15 unidades de torque por 30 ms, ângulo interno da junta),
# igual nas 6 pernas e nos dois lados: CTr flexiona com −τ, FTi com +τ, TiTa com −τ.
FLEX_SIGN = {"ctr_pitch": -1, "fti_pitch": +1, "tita_pitch": -1}


class MotorDrive:
    """Spikes de MNs → ativação de cada grupo muscular (1ª ordem) → torque nas juntas.

    ativação: da/dt = (u − a)/τ, u = (spikes do grupo no passo)/(n_MN · dt · F_SAT), a ∈ [0, 1].
    torque(DOF) = GAIN[junta] · Σ_grupos sinal · a, limitado a ±TORQUE_LIMIT.
    τ = 20 ms e F_SAT = 200 Hz: NON-CONNECTOME (ordem de grandeza da contração de músculos de
    perna de Drosophila, Azevedo et al. 2020, eLife, "A size principle for recruitment of Drosophila leg motor
    neurons").

    GAIN (A4), fixado na Sessão 2 ANTES de analisar o loop fechado, por critério independente do
    ritmo: torque que o próprio NeuroMechFly precisa para reproduzir a marcha REAL gravada
    (flygym_demo MotionSnippet, 330 fps), no procedimento do tutorial 2 do FlyGym 2.1
    (tutorials/2_replaying_experimental_recordings.ipynb: atuadores de posição kp = 150 µN·mm/rad,
    chão plano, adesão). Ganho de cada junta = percentil 95 de |τ| em todas as pernas
    (results/phase3a/gain_calibration_replay.json). Ativação máxima de um grupo muscular = torque
    que cobre 95 % do que a marcha real exige. A fila anterior usou 30 em todas as juntas, sem
    fonte, e foi descartada.
    """

    TAU_MS, F_SAT = 20.0, 200.0
    GAIN = {"ThC": 10.0, "CTr": 19.45, "TrF": 15.89, "FTi": 22.39, "TiTa": 12.22}
    _KEY2JOINT = {"thc_pitch": "ThC", "thc_roll": "ThC", "thc_yaw": "ThC", "ctr_pitch": "CTr",
                  "trf_roll": "TrF", "fti_pitch": "FTi", "tita_pitch": "TiTa"}

    def __init__(self, mnt, dof_order: list[str], flex_sign: dict[str, int]):
        self.dof_index = {d: k for k, d in enumerate(dof_order)}
        groups = mnt.groupby(["leg", "joint", "role"])
        self.groups = []
        for (leg, joint, role), g in groups:
            key, s = ROLE_DOF[(joint, role)]
            s = s * flex_sign.get(key, 1) * self.GAIN[self._KEY2JOINT[key]]
            self.groups.append((np.array(g.h, dtype=np.int64), self.dof_index[dof_name(leg, key)], s))
        self.a = np.zeros(len(self.groups))
        self.lut = {}
        for k, (hh, _, _) in enumerate(self.groups):
            for h in hh:
                self.lut[int(h)] = k
        self.n_dof = len(dof_order)

    def step(self, spike_idx: np.ndarray, dt_ms: float) -> np.ndarray:
        cnt = np.zeros(len(self.groups))
        for h in spike_idx:
            k = self.lut.get(int(h))
            if k is not None:
                cnt[k] += 1
        u = cnt / (np.array([len(g[0]) for g in self.groups]) * dt_ms * 1e-3 * self.F_SAT)
        self.a += (np.clip(u, 0, 1) - self.a) * (dt_ms / self.TAU_MS)
        tq = np.zeros(self.n_dof)
        for k, (_, d, s) in enumerate(self.groups):
            tq[d] += s * self.a[k]
        return np.clip(tq, -TORQUE_LIMIT, TORQUE_LIMIT)
