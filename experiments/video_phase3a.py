"""Vídeo (WebM/VP9, 5 s) de uma execução do loop fechado da 3a: mosca na bola + MNs por perna.

A execução é refeita (determinística: mesmas sementes do LIF e da transdução; MuJoCo é
determinístico) e renderizada. A configuração é escolhida ANTES de ver resultados
(docs/FASE3_PLANO.md, pré-registro): nada de escolher pelo resultado.
Painel da direita: atividade dos MNs nos últimos 500 ms, uma faixa por perna e junta
(spikes por janela de 10 ms), com a cor da junta; linha de estado: DNs ligados/desligados.
Uso: MUJOCO_GL=egl uv run python -m experiments.video_phase3a --group G3_top20_drive --seed 7000
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from terrario import ROOT
from terrario.vnc.motor_map import JOINTS, LEGS

COL = {"ThC": (42, 120, 214), "CTr": (235, 104, 52), "TrF": (27, 175, 122), "FTi": (237, 161, 0),
       "TiTa": (232, 123, 164)}


def _font(sz=12):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
              "/usr/share/fonts/google-noto/NotoSans-Regular.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def mn_panel(hist, t_ms, t_on, t_off, size=(360, 360)):
    """hist: (n_faixas, n_bins) contagens; retorna imagem RGB."""
    h, w = size
    img = Image.new("RGB", (w, h), (252, 252, 251))
    d = ImageDraw.Draw(img)
    fn, fs = _font(12), _font(10)
    rows = [(leg, j) for leg in LEGS for j in JOINTS]
    top, left = 40, 70
    rh = (h - top - 10) / len(rows)
    bw = (w - left - 10) / hist.shape[1]
    mx = max(1.0, np.percentile(hist, 99))
    for r, (leg, j) in enumerate(rows):
        y0 = top + r * rh
        for b in range(hist.shape[1]):
            v = min(1.0, hist[r, b] / mx)
            if v > 0:
                c = tuple(int(252 - (252 - cc) * v) for cc in COL[j])
                d.rectangle([left + b * bw, y0, left + (b + 1) * bw, y0 + rh - 1], fill=c)
        if j == "ThC":
            d.text((8, y0), leg.upper(), fill=(11, 11, 11), font=fn)
            d.line([left, y0, w - 10, y0], fill=(82, 81, 78))
        d.text((36, y0 - 1), j, fill=(82, 81, 78), font=fs)
    on = t_on <= t_ms < t_off
    d.text((8, 4), f"MNs de perna, últimos 500 ms | t = {t_ms/1000:.2f} s", fill=(11, 11, 11), font=fn)
    d.text((8, 20), "DNs LIGADOS" if on else "DNs desligados", fill=(42, 120, 214) if on else (82, 81, 78),
           font=fn)
    return np.asarray(img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="G3_top20_drive")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--combo", default="00")
    ap.add_argument("--seed", type=int, default=7000)
    ap.add_argument("--video-s", type=float, default=5.0)
    args = ap.parse_args()
    import mujoco as mj
    from flygym.anatomy import BodySegment
    from flygym.compose import ActuatorType
    from terrario.brain import banc, hybrid
    from terrario.brain.lif import ShiuLIF
    from terrario.video import write_webm
    from terrario.vnc.apparatus import FLEX_SIGN, MotorDrive, build_ball_scene, dof_name
    from terrario.vnc.loop import KICK_LEGS
    from terrario.vnc.proprio import Proprioception

    S1 = ROOT / "runs/phase3a/s1"
    m = banc.load_meta()
    c = hybrid.load(args.scale, sign_mode="verified")
    mnt = pd.read_csv(S1 / "leg_mn_table.csv")
    dn = json.load(open(S1 / "dn_groups.json"))[args.group]
    combo = (int(args.combo[0]), int(args.combo[1]))
    # MESMA sequência de run_loop (terrario/vnc/loop.py), com renderização
    brain = ShiuLIF(c, seed=args.seed)
    sc = build_ball_scene(textured=True)
    sim, fly = sc.sim, sc.fly
    jd = [d.name for d in fly.get_jointdofs_order()]
    ad = [d.name for d in fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    pr = Proprioception(m, hybrid.banc_index(c, m), jd, seed=args.seed, combo=combo)
    md = MotorDrive(mnt, ad, FLEX_SIGN)
    dn_slots = brain.poisson_slots(dn)
    pr_slots = brain.poisson_slots(pr.h)
    tarsi = [BodySegment(f"{leg}_tarsus{k}") for leg in LEGS for k in range(1, 6)]
    kick = np.zeros(len(ad))
    for leg in KICK_LEGS:
        kick[ad.index(dof_name(leg, "ctr_pitch"))] = 10 * FLEX_SIGN["ctr_pitch"]
        kick[ad.index(dof_name(leg, "fti_pitch"))] = 10 * FLEX_SIGN["fti_pitch"]
    t_on, t_off, kick_ms = 200, 3450, 50.0
    sim.reset()
    sim.warmup(0.02)
    r = mj.Renderer(sim.mj_model, height=360, width=480)
    row_of = {h: LEGS.index(l) * len(JOINTS) + JOINTS.index(j)
              for h, l, j in zip(mnt.h, mnt.leg, mnt.joint)}
    hist = np.zeros((len(LEGS) * len(JOINTS), 50))
    frames = []
    fps = 30
    total = int(args.video_s * 1000)
    next_frame = 0.0
    for ms in range(total):
        brain.set_rates(dn_slots, 200.0 if t_on <= ms < t_off else 0.0)
        q, qd = sim.get_joint_angles(fly.name), sim.get_joint_velocities(fly.name)
        f = sim.get_bodysegment_contact_forces(fly.name, tarsi, ground_only=True)
        brain.set_rates(pr_slots, pr.rates(q, qd, np.linalg.norm(f, axis=1).reshape(6, 5).sum(1)))
        i, _ = brain.run(10, cap=1 << 22)
        mi = i[np.isin(i, mnt.h.to_numpy())]
        tq = md.step(mi, 1.0)
        if t_on <= ms < t_on + kick_ms:
            tq = tq + kick
        sim.set_actuator_inputs(fly.name, ActuatorType.MOTOR, tq)
        for _ in range(10):
            sim.step()
        if ms % 10 == 0:
            hist = np.roll(hist, -1, axis=1)
            hist[:, -1] = 0
        for h in mi:
            hist[row_of[int(h)], -1] += 1
        if ms >= next_frame:  # 1× tempo real: 5 s de vídeo = 5 s simulados
            next_frame += 1000 / fps
            r.update_scene(sim.mj_data, camera="lateral")
            cam = r.render().copy()
            frames.append(np.concatenate([cam, mn_panel(hist, ms, t_on, t_off)], axis=1))
    out = ROOT / "results/phase3a/s2" / f"video_closed_{args.group}_s{args.scale:g}_c{args.combo}_{args.seed}.webm"
    print(write_webm(out, frames, fps=fps), len(frames), "quadros")


if __name__ == "__main__":
    main()
