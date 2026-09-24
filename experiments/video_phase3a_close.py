"""Vídeo de fechamento da Fase 3a (WebM/VP9, ~18 s; roteiro fixado em docs/FASE3A_RELATORIO.md §6).

Corpo da última tentativa: passive="wang2025", limit="direct_dt".
  1. cartela; 2. teste (a): torques da marcha real (servo kp 150 → malha aberta, como em
  experiments/phase3a_s3_validate.py:test_a), 2 s a 0,25×; 3. cartela; 4. teste (c), pior caso pelo
  critério (1 kHz) na tentativa direct_dt: LF FTi extensor, ativação 1, 200 ms, bola afastada, a 0,025×.
Uso: MUJOCO_GL=egl uv run python -m experiments.video_phase3a_close
"""

from __future__ import annotations

import mujoco as mj
import numpy as np
from PIL import Image, ImageDraw

from flygym.compose import ActuatorType

from terrario import ROOT
from terrario.video import write_webm
from terrario.vnc.apparatus import FLEX_SIGN, TORQUE_LIMIT, MotorDrive, build_ball_scene
from experiments.video_phase3a import _font

FPS, H, W = 30, 360, 640
KP, SERVO_LIM = 150.0, 30.0
WORST = "lf_FTi_extensor"  # maior viol_act1 em results/phase3a/s3_validation_direct_dt/s3_validation_cd.csv


def _scene(offset=0.0):
    sc = build_ball_scene(ball_z_offset=offset, textured=True, passive="wang2025", limit="direct_dt")
    sc.sim.reset()
    sc.sim.warmup(0.02)
    return sc


def _caption(img, lines):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 18 * len(lines) + 8], fill=(252, 252, 251))
    for k, t in enumerate(lines):
        d.text((8, 4 + 18 * k), t, fill=(11, 11, 11), font=_font(13))
    return np.asarray(im)


def _card(lines, n):
    im = Image.new("RGB", (W, H), (252, 252, 251))
    d = ImageDraw.Draw(im)
    for k, t in enumerate(lines):
        d.text((30, 120 + 30 * k), t, fill=(11, 11, 11), font=_font(18 if k == 0 else 14))
    return [np.asarray(im)] * n


def part_a():
    from flygym_demo.spotlight_data import MotionSnippet
    sc = _scene()
    jd = [d.name for d in sc.fly.get_jointdofs_order()]
    ad = [d.name for d in sc.fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    aidx = np.array([jd.index(n) for n in ad])
    adofs = sc.fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)
    ref = MotionSnippet().get_joint_angles(output_timestep=1e-4, output_dof_order=adofs)
    tau = np.zeros((len(ref), len(ad)))
    for k in range(len(ref)):  # servo (sem render), idêntico ao teste (a)
        q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
        tau[k] = np.clip(KP * (ref[k] - q), -SERVO_LIM, SERVO_LIM)
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tau[k])
        sc.sim.step()
    sc2 = _scene()
    r = mj.Renderer(sc2.sim.mj_model, height=H, width=W)
    every = int(0.25 / FPS / 1e-4)  # 0,25× → passos de física por quadro
    frames = []
    for k in range(len(ref)):
        sc2.sim.set_actuator_inputs(sc2.fly.name, ActuatorType.MOTOR, np.clip(tau[k], -TORQUE_LIMIT, TORQUE_LIMIT))
        sc2.sim.step()
        if k % every == 0:
            r.update_scene(sc2.sim.mj_data, camera="lateral")
            frames.append(_caption(r.render().copy(), [
                "Teste (a): torques da marcha real em malha aberta (passou; razão de amplitude 0,95–1,00)",
                f"t = {k * 0.1:6.1f} ms   |   câmera lenta 0,25×"]))
    return frames


def part_c():
    import pandas as pd
    sc = _scene(-5.0)
    m = sc.sim.mj_model
    jd = [d.name for d in sc.fly.get_jointdofs_order()]
    ad = [d.name for d in sc.fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    md = MotorDrive(mnt, ad, FLEX_SIGN)
    names = [f"{l}_{j}_{r}" for (l, j, r), _ in mnt.groupby(["leg", "joint", "role"])]
    _, d, s = md.groups[names.index(WORST)]
    tq = np.zeros(len(ad))
    tq[d] = np.clip(s, -TORQUE_LIMIT, TORQUE_LIMIT)
    dof = ad[d]
    lo, hi = m.jnt_range[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"fly/{dof}")]
    r = mj.Renderer(m, height=H, width=W)
    every = max(1, int(0.025 / FPS / 1e-4))
    frames, vmax = [], 0.0
    for k in range(2000):
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tq)
        sc.sim.step()
        q = float(np.asarray(sc.sim.get_joint_angles(sc.fly.name))[jd.index(dof)])
        v = max(0.0, lo - q, q - hi)
        vmax = max(vmax, v)
        if k % every == 0:
            r.update_scene(sc.sim.mj_data, camera="lateral")
            frames.append(_caption(r.render().copy(), [
                f"Teste (c), PIOR CASO: LF FTi extensor, ativação 1 (torque {abs(s):.1f} µN·mm)",
                f"t = {k * 0.1:5.1f} ms  ângulo {q:+.3f} rad  limite [{lo:+.3f}, {hi:+.3f}]",
                f"violação agora {v:.3f} rad  |  máx. {vmax:.3f} rad  (Y = 0,05)  |  câmera lenta 0,025×"]))
    return frames


def main():
    frames = _card(["Fase 3a: fechamento", "Loop fechado não testável com este aparato no prazo",
                    "Corpo da última tentativa: rigidez de Wang et al. 2025, limites direct_dt"], FPS)
    frames += part_a()
    frames += _card(["Onde o aparato falha: teste (c)", "Pior caso (maior violação pelo critério de 1 kHz):",
                     "LF FTi extensor, 0,111 rad > Y = 0,05 rad"], FPS)
    frames += part_c()
    out = write_webm(ROOT / "results/phase3a/video_fechamento_3a.webm", frames, fps=FPS)
    print(out, len(frames), "quadros", f"{len(frames) / FPS:.1f} s")


if __name__ == "__main__":
    main()
