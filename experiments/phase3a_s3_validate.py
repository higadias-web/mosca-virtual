"""Fase 3a, Sessão 3: validação do aparato com o A2' (FASE3_PLANO §7.4.3). NÃO RODAR antes da aprovação
das tolerâncias. Se qualquer teste falhar, nenhuma fila roda (e o critério não é ajustado).

Corpo: build_ball_scene(passive="wang2025") (rigidez de Wang et al. 2025, amortecimento pelo critério,
limites da marcha real ± 30 %). Tolerâncias (propostas; valores em TOL):
  (a) réplica com torques: servo kp = 150 µN·mm/rad, limitado a ±30 (atuador de posição do tutorial 2
      do FlyGym 2.1, third_party/flygym/tutorials/2_replaying_experimental_recordings.ipynb; o |τ| máximo
      da calibração do A4 foi 30) seguindo a marcha real (flygym_demo MotionSnippet, 2 s) NA BOLA; os
      torques são gravados e tocados em malha aberta como MOTOR no mesmo aparato, com a mesma condição
      inicial. Cada uma das 18 amplitudes p5–p95 (perna × ThC pitch, CTr, FTi) fica a ±X da marcha real.
  (b) repouso: 5,7 s sem torque; depois de 0,5 s, cada DOF ativo a < Y rad do seu ângulo em 0,5 s, e a
      superfície da bola percorre < 0,2 mm.
  (c) limites: ativação 1 (torque = ganho do A4) num grupo muscular por vez, 200 ms, bola afastada
      (−5 mm, como tests/test_apparatus.py): nenhum DOF passa do range em mais de Y.
  (d) faixa dinâmica: ativação 0,2…1,0 em 5 degraus por grupo (bola afastada): o ângulo final do DOF do
      grupo (média dos últimos 50 ms) anda no sentido do torque e de forma monotônica (tolerância de
      Y/5 para ruído); e respeita (c).
Saída: results/phase3a/s3_validation.json (+ .csv por teste)
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from flygym.compose import ActuatorType

from terrario import ROOT
from terrario.vnc.apparatus import (FLEX_SIGN, TORQUE_LIMIT, BALL_RADIUS, MotorDrive, build_ball_scene,
                                    dof_name)
from terrario.vnc.motor_map import LEGS

TOL = dict(X=0.35, Y=0.05, Z_s=5.7, settle_s=0.5, ball_mm=0.2, limit_ms=200, mono=0.05 / 5)
KP, SERVO_LIM = 150.0, 30.0
KEYS = {"ThC": "thc_pitch", "CTr": "ctr_pitch", "FTi": "fti_pitch"}
OUT = ROOT / "results/phase3a"


def _scene(offset=0.0):
    sc = build_ball_scene(ball_z_offset=offset, passive="wang2025")
    fly = sc.fly
    jd = [d.name for d in fly.get_jointdofs_order()]
    ad = [d.name for d in fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    sc.sim.reset()
    sc.sim.warmup(0.02)
    return sc, jd, ad


def _ranges(sc, names):
    import mujoco as mj
    m = sc.sim.mj_model
    out = {}
    for n in names:
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"fly/{n}")
        out[n] = tuple(m.jnt_range[j])
    return out


def _amp(x):
    return float(np.ptp(np.percentile(x, [5, 95])))


def test_a():
    from flygym_demo.spotlight_data import MotionSnippet
    sc, jd, ad = _scene()
    sn = MotionSnippet()
    adofs = sc.fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)
    ref = sn.get_joint_angles(output_timestep=1e-4, output_dof_order=adofs)  # (n, 42)
    real = sn.get_joint_angles(output_timestep=1e-3, output_dof_order=adofs)
    aidx = np.array([jd.index(n) for n in ad])
    n = len(ref)
    tau = np.zeros((n, len(ad)))
    q_servo = []
    for k in range(n):
        q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
        tau[k] = np.clip(KP * (ref[k] - q), -SERVO_LIM, SERVO_LIM)
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tau[k])
        sc.sim.step()
        if k % 10 == 0:
            q_servo.append(q)
    sc2, _, _ = _scene()
    q_open = []
    for k in range(n):
        sc2.sim.set_actuator_inputs(sc2.fly.name, ActuatorType.MOTOR, np.clip(tau[k], -TORQUE_LIMIT, TORQUE_LIMIT))
        sc2.sim.step()
        if k % 10 == 0:
            q_open.append(np.asarray(sc2.sim.get_joint_angles(sc2.fly.name))[aidx])
    q_servo, q_open = np.array(q_servo), np.array(q_open)
    gain = {k: MotorDrive.GAIN[j] for j, k in [("ThC", "thc_pitch"), ("CTr", "ctr_pitch"), ("FTi", "fti_pitch")]}
    rows = []
    for leg in LEGS:
        for j, key in KEYS.items():
            c = ad.index(dof_name(leg, key))
            r = _amp(real[:, c])
            rows.append(dict(leg=leg, joint=j, real=r, servo=_amp(q_servo[:, c]), open=_amp(q_open[:, c]),
                             ratio_open=_amp(q_open[:, c]) / r, ratio_servo=_amp(q_servo[:, c]) / r,
                             frac_tau_over_gain=float((np.abs(tau[:, c]) > gain[key]).mean())))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "s3_validation_a.csv", index=False)
    ok = bool(((df.ratio_open - 1).abs() <= TOL["X"]).all())
    return dict(passed=ok, ratio_open_min=float(df.ratio_open.min()), ratio_open_max=float(df.ratio_open.max()),
                ratio_open_median=float(df.ratio_open.median()), n_outside=int(((df.ratio_open - 1).abs() > TOL["X"]).sum()))


def test_b():
    sc, jd, ad = _scene()
    aidx = np.array([jd.index(n) for n in ad])
    dt = sc.sim.mj_model.opt.timestep
    n, n0 = int(TOL["Z_s"] / dt), int(TOL["settle_s"] / dt)
    zero = np.zeros(len(ad))
    q0, dmax, ball = None, np.zeros(len(ad)), 0.0
    for k in range(n):
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, zero)
        sc.sim.step()
        if k == n0:
            q0 = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx].copy()
        if k > n0:
            if k % 10 == 0:
                q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
                dmax = np.maximum(dmax, np.abs(q - q0))
            w = sc.sim.mj_data.qvel[sc.ball_vadr:sc.ball_vadr + 3]
            ball += float(np.linalg.norm(w)) * BALL_RADIUS * dt
    pd.DataFrame(dict(dof=ad, drift_max=dmax)).to_csv(OUT / "s3_validation_b.csv", index=False)
    ok = bool(dmax.max() < TOL["Y"] and ball < TOL["ball_mm"])
    return dict(passed=ok, drift_max=float(dmax.max()), drift_worst_dof=ad[int(dmax.argmax())], ball_mm=ball)


def _groups(ad):
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    md = MotorDrive(mnt, ad, FLEX_SIGN)
    names = [f"{l}_{j}_{r}" for (l, j, r), _ in mnt.groupby(["leg", "joint", "role"])]
    return [(nm, d, s) for nm, (_, d, s) in zip(names, md.groups)]


def _hold(tq_vec, ms, jd, ad, offset=-5.0):
    sc, _, _ = _scene(offset)
    aidx = np.array([jd.index(n) for n in ad])
    rng = _ranges(sc, ad)
    lo = np.array([rng[n][0] for n in ad])
    hi = np.array([rng[n][1] for n in ad])
    viol, tail = 0.0, []
    steps = int(ms * 10)
    for k in range(steps):
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tq_vec)
        sc.sim.step()
        if k % 10 == 0:
            q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
            viol = max(viol, float(np.max(np.maximum(lo - q, q - hi))))
            if k >= steps - 500:
                tail.append(q)
    return viol, np.mean(tail, 0)


def test_c_d():
    sc, jd, ad = _scene(-5.0)
    aidx = np.array([jd.index(n) for n in ad])
    q_rest = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
    rows = []
    for name, d, s in _groups(ad):
        finals, viols = [], []
        for a in (0.2, 0.4, 0.6, 0.8, 1.0):
            tq = np.zeros(len(ad))
            tq[d] = np.clip(s * a, -TORQUE_LIMIT, TORQUE_LIMIT)
            v, qf = _hold(tq, TOL["limit_ms"], jd, ad)
            viols.append(v)
            finals.append(np.sign(s) * (qf[d] - q_rest[d]))
        f = np.array(finals)
        mono = bool(np.all(np.diff(f) >= -TOL["mono"]) and f[-1] > 0)
        rows.append(dict(group=name, dof=ad[d], viol_act1=viols[-1], viol_max=max(viols), monotonic=mono,
                         **{f"dq_{a}": x for a, x in zip((0.2, 0.4, 0.6, 0.8, 1.0), f)}))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "s3_validation_cd.csv", index=False)
    c_ok = bool((df.viol_act1 <= TOL["Y"]).all())
    d_ok = bool(df.monotonic.all() and (df.viol_max <= TOL["Y"]).all())
    return (dict(passed=c_ok, viol_max=float(df.viol_act1.max()), n_fail=int((df.viol_act1 > TOL["Y"]).sum())),
            dict(passed=d_ok, n_nonmonotonic=int((~df.monotonic).sum()), n_groups=len(df)))


def main():
    res = dict(tol=TOL, a=test_a(), b=test_b())
    res["c"], res["d"] = test_c_d()
    res["all_passed"] = all(res[k]["passed"] for k in "abcd")
    json.dump(res, open(OUT / "s3_validation.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
