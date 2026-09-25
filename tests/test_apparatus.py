"""Fase 3a: aparato (bola, sinal de flexão, MN → torque)."""

import numpy as np
import pytest

from terrario import DATA

pytestmark = pytest.mark.skipif(not (DATA / "banc" / "banc_888_meta.feather").exists(),
                                reason="dados do BANC ausentes")


def _angle(sim, fly, a, b, c):
    names = [s.name for s in fly.get_bodysegs_order()]
    p = sim.get_body_positions(fly.name)
    u, v = p[names.index(a)] - p[names.index(b)], p[names.index(c)] - p[names.index(b)]
    return np.degrees(np.arccos(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v)))


@pytest.mark.parametrize("leg", ["lf", "rh"])
def test_flexion_signs(leg):
    from flygym.compose import ActuatorType
    from terrario.vnc.apparatus import FLEX_SIGN, build_ball_scene, dof_name
    sc = build_ball_scene(ball_z_offset=-5.0)
    sim, fly = sc.sim, sc.fly
    order = [d.name for d in fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    tri = {"ctr_pitch": (f"{leg}_coxa", f"{leg}_trochanterfemur", f"{leg}_tibia"),
           "fti_pitch": (f"{leg}_trochanterfemur", f"{leg}_tibia", f"{leg}_tarsus1")}
    for key, t in tri.items():
        sim.reset()
        sim.warmup(0.01)
        a0 = _angle(sim, fly, *t)
        u = np.zeros(len(order))
        u[order.index(dof_name(leg, key))] = 15 * FLEX_SIGN[key]
        for _ in range(300):
            sim.set_actuator_inputs(fly.name, ActuatorType.MOTOR, u)
            sim.step()
        assert _angle(sim, fly, *t) < a0 - 10, key  # flexão fecha a junta


def test_ball_spins_when_legs_push():
    from flygym.compose import ActuatorType
    from terrario.vnc.apparatus import build_ball_scene
    sc = build_ball_scene()
    sim, fly = sc.sim, sc.fly
    sim.reset()
    sim.warmup(0.02)
    n = len(fly.get_actuated_jointdofs_order(ActuatorType.MOTOR))
    rng = np.random.default_rng(0)
    for _ in range(2000):
        sim.set_actuator_inputs(fly.name, ActuatorType.MOTOR, rng.normal(0, 20, n))
        sim.step()
    assert np.abs(sim.mj_data.qvel[sc.ball_vadr:sc.ball_vadr + 3]).max() > 0.05


def test_motor_drive_flexor_spikes_give_flexion_torque():
    import pandas as pd
    from flygym.compose import ActuatorType
    from terrario.brain import banc, hybrid
    from terrario.vnc.apparatus import FLEX_SIGN, MotorDrive, dof_name, make_neuromuscular_fly
    from terrario.vnc.motor_map import leg_mn_table
    c = hybrid.load(1.0)
    mnt = leg_mn_table(banc.load_meta())
    mnt["h"] = c.idx(mnt.banc_888_id)
    order = [d.name for d in make_neuromuscular_fly().get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    md = MotorDrive(mnt, order, FLEX_SIGN)
    flex = mnt[(mnt.leg == "lf") & (mnt.joint == "FTi") & (mnt.role == "flexor")].h.to_numpy()
    for _ in range(100):  # 100 ms com todos os flexores da tíbia a 1 spike/ms
        tq = md.step(flex, 1.0)
    k = order.index(dof_name("lf", "fti_pitch"))
    assert np.sign(tq[k]) == FLEX_SIGN["fti_pitch"] and abs(tq[k]) > 1
    assert np.count_nonzero(tq) == 1
