"""Loop fechado da Fase 3a: cérebro FlyWire + cordão BANC (LIF) ↔ corpo na bola (MuJoCo).

A cada 1 ms (D-006):
  1. DNs do grupo recebem Poisson (ligado em [t_on, t_off));
  2. proprioceptores do BANC recebem Poisson com a taxa da transdução (terrario/vnc/proprio.py),
     calculada do estado das juntas e da força de contato de cada perna na bola;
  3. o LIF avança 10 passos de 0,1 ms;
  4. os spikes dos MNs de perna viram ativação muscular → torque (terrario/vnc/apparatus.py);
  5. a física avança 10 passos de 0,1 ms.
Opções:
  kick_ms: pulso inicial de flexão (CTr/FTi) só no trípode L1-R2-L3, para quebrar a simetria
           (NON-CONNECTOME, protocolo); o ritmo é avaliado depois dele.
  imposed: ângulos gravados (flygym_demo MotionSnippet, 330 fps, marcha real) no lugar do corpo:
           só a transdução lê esses ângulos; os MNs não movem nada (teste H1-i, aferência imposta).
"""

from __future__ import annotations

import time

import numpy as np

from flygym.anatomy import BodySegment
from flygym.compose import ActuatorType

from terrario.brain.lif import ShiuLIF
from terrario.vnc.apparatus import FLEX_SIGN, MotorDrive, build_ball_scene, dof_name
from terrario.vnc.proprio import Proprioception

KICK_LEGS = ("lf", "rm", "lh")


def run_loop(conn, meta, mnt, hidx, *, dn_idx, dn_rate, t_on_ms, t_off_ms, total_ms,
             seed=0, proprio_seed=0, combo=(0, 0), kick_ms=50.0, imposed=None, record_hz=200,
             bg_idx=None, bg_rate=0.0, sensory=True, f_sat=None):
    """bg_idx/bg_rate: fundo de Poisson tônico (H5), com refratário normal nesses neurônios.
    sensory=False: proprioceptores em 0 Hz (controle sem aferência)."""
    t_wall = time.perf_counter()
    brain = ShiuLIF(conn, seed=seed)
    sc = build_ball_scene()
    sim, fly = sc.sim, sc.fly
    jdofs = [d.name for d in fly.get_jointdofs_order()]
    adofs = [d.name for d in fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
    pr = Proprioception(meta, hidx, jdofs, seed=proprio_seed, combo=combo)
    md = MotorDrive(mnt, adofs, FLEX_SIGN, f_sat=f_sat)
    dn_slots = brain.poisson_slots(dn_idx)
    pr_slots = brain.poisson_slots(pr.h)
    if bg_idx is not None and len(bg_idx):
        bg = np.setdiff1d(np.asarray(bg_idx, dtype=np.int64), np.concatenate([dn_idx, pr.h]))
        brain.set_rates(brain.poisson_slots(bg), bg_rate)
        brain.rfc_steps[bg] = brain.R  # mantém o refratário (poisson_slots o zera, como no Shiu)
    tarsi = [[BodySegment(f"{leg}_tarsus{k}") for k in range(1, 6)] for leg in
             ["lf", "lm", "lh", "rf", "rm", "rh"]]
    flat_tarsi = [s for leg in tarsi for s in leg]
    kick = np.zeros(len(adofs))
    for leg in KICK_LEGS:
        kick[adofs.index(dof_name(leg, "ctr_pitch"))] = 10 * FLEX_SIGN["ctr_pitch"]
        kick[adofs.index(dof_name(leg, "fti_pitch"))] = 10 * FLEX_SIGN["fti_pitch"]
    mn_set = np.array(mnt.h)
    if imposed is not None:  # (n_ms, n_jdofs) ângulos já na ordem jdofs, a 1 kHz
        imp_q = imposed
        imp_qd = np.gradient(imposed, 1e-3, axis=0)
    sim.reset()
    sim.warmup(0.02)
    out_i, out_t, ball, qrec = [], [], [], []
    rec_every = int(1000 / record_hz)
    for ms in range(int(total_ms)):
        on = t_on_ms <= ms < t_off_ms
        brain.set_rates(dn_slots, dn_rate if on else 0.0)
        if imposed is not None:
            k = min(ms, len(imp_q) - 1)
            q, qd = imp_q[k], imp_qd[k]
            lf = np.zeros(6)
        else:
            q = sim.get_joint_angles(fly.name)
            qd = sim.get_joint_velocities(fly.name)
            f = sim.get_bodysegment_contact_forces(fly.name, flat_tarsi, ground_only=True)
            lf = np.linalg.norm(f, axis=1).reshape(6, 5).sum(1)
        brain.set_rates(pr_slots, pr.rates(q, qd, lf) if sensory else 0.0)
        i, t = brain.run(10, cap=1 << 22)
        mi = np.isin(i, mn_set)
        out_i.append(i[mi])
        out_t.append(t[mi] * brain.dt)
        if imposed is None:
            tq = md.step(i[mi], 1.0)
            if t_on_ms <= ms < t_on_ms + kick_ms:
                tq = tq + kick
            sim.set_actuator_inputs(fly.name, ActuatorType.MOTOR, tq)
            for _ in range(10):
                sim.step()
        if ms % rec_every == 0:
            ball.append(sim.mj_data.qvel[sc.ball_vadr:sc.ball_vadr + 3].copy())
            qrec.append(np.asarray(q).copy())
    return dict(i=np.concatenate(out_i), t=np.concatenate(out_t), ball=np.array(ball),
                q=np.array(qrec), jdofs=jdofs, wall_s=time.perf_counter() - t_wall,
                prop_counts=pr.counts())
