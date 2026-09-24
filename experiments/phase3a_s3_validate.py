"""Fase 3a, Sessão 3: validação do aparato com o A2' (FASE3_PLANO §7.4.3 e §7.6). Tolerâncias (a)–(d)
aprovadas em 2026-09-23; (e) pedido na mesma aprovação. Se qualquer teste falhar, nenhuma fila roda (e o
critério não é ajustado).

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
  (e) controle negativo mecânico (§7.6): sem conectoma. Cada MN de perna dispara Poisson tônico na sua
      taxa média da Sessão 2 (runs/phase3a/s2/diag_rates_closed.npy, janela A, média das 120 execuções
      do loop fechado), com o mesmo protocolo do loop (MotorDrive, pulso A7 em 200–250 ms, 5,7 s),
      5 sementes (7000–7004). A métrica congelada (v2), na janela A (450–3450 ms), é aplicada:
        - aos proprioceptores: trens de Poisson gerados pela transdução (terrario/vnc/proprio.py) a
          partir da cinemática, população de cada perna, 4 combinações de direção → rhythm_v2 completo;
        - aos ângulos: cada DOF ativo (7 por perna), média em janelas de 5 ms → só a parte espectral da
          v2 (Welch, proeminência ≥ 5) + reprodutibilidade (≥ 3/5 sementes a ±1 Hz). O teste de
          surrogados (deslocamento circular por neurônio) não se define para um sinal único; sem ele o
          critério fica MAIS sensível, o que é o lado conservador num controle negativo.
      Passa se não houver NENHUM positivo. Se houver, o aparato gera ritmo sozinho e nenhuma fila roda.
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
from terrario.vnc import rhythm

TOL = dict(X=0.35, Y=0.05, Z_s=5.7, settle_s=0.5, ball_mm=0.2, limit_ms=200, mono=0.05 / 5)
KP, SERVO_LIM = 150.0, 30.0
KEYS = {"ThC": "thc_pitch", "CTr": "ctr_pitch", "FTi": "fti_pitch"}
OUT = ROOT / "results/phase3a"


LIMIT = "std2dt"  # §7.8; trocado por --limit direct_dt só na alternativa única


# Instabilidade = falha (§7.10, condição do usuário): NaN/Inf no estado, qualquer aviso do MuJoCo de
# aceleração/velocidade/posição inválida ou "huge" (mjWARN_BADQACC, BADQVEL, BADQPOS; o MuJoCo reinicia o
# estado sozinho nesses casos, então só o contador de avisos mostra) em QUALQUER teste, ou energia
# crescendo sem entrada no teste (b), reprova a tentativa, mesmo que (c) passe.
SCENES: list = []
INSTAB: dict = {}


def _audit(test: str):
    import mujoco as mj
    for sc in SCENES:
        d = sc.sim.mj_data
        w = {n: int(d.warning[getattr(mj.mjtWarning, n)].number)
             for n in ("mjWARN_BADQACC", "mjWARN_BADQVEL", "mjWARN_BADQPOS")}
        finite = bool(np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all() and np.isfinite(d.qacc).all())
        rec = INSTAB.setdefault(test, dict(n_scenes=0, warnings={k: 0 for k in w}, nonfinite=0))
        rec["n_scenes"] += 1
        for k, v in w.items():
            rec["warnings"][k] += v
        rec["nonfinite"] += int(not finite)
    SCENES.clear()


def _scene(offset=0.0):
    sc = build_ball_scene(ball_z_offset=offset, passive="wang2025", limit=LIMIT)
    SCENES.append(sc)
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
    _audit("a")
    ok = bool(((df.ratio_open - 1).abs() <= TOL["X"]).all())
    return dict(passed=ok, ratio_open_min=float(df.ratio_open.min()), ratio_open_max=float(df.ratio_open.max()),
                ratio_open_median=float(df.ratio_open.median()), n_outside=int(((df.ratio_open - 1).abs() > TOL["X"]).sum()))


def test_b():
    import mujoco as mj
    sc, jd, ad = _scene()
    sc.sim.mj_model.opt.enableflags |= mj.mjtEnableBit.mjENBL_ENERGY  # d.energy = (potencial, cinética)
    aidx = np.array([jd.index(n) for n in ad])
    E0, Emax_rise = None, 0.0
    dt = sc.sim.mj_model.opt.timestep
    n, n0 = int(TOL["Z_s"] / dt), int(TOL["settle_s"] / dt)
    zero = np.zeros(len(ad))
    q0, dmax, ball = None, np.zeros(len(ad)), 0.0
    for k in range(n):
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, zero)
        sc.sim.step()
        if k == n0:
            q0 = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx].copy()
            E0 = float(sc.sim.mj_data.energy.sum())
        if k > n0 and k % 100 == 0:  # energia total a cada 10 ms, sem entrada
            Emax_rise = max(Emax_rise, float(sc.sim.mj_data.energy.sum()) - E0)
        if k > n0:
            if k % 10 == 0:
                q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
                dmax = np.maximum(dmax, np.abs(q - q0))
            w = sc.sim.mj_data.qvel[sc.ball_vadr:sc.ball_vadr + 3]
            ball += float(np.linalg.norm(w)) * BALL_RADIUS * dt
    pd.DataFrame(dict(dof=ad, drift_max=dmax)).to_csv(OUT / "s3_validation_b.csv", index=False)
    ok = bool(dmax.max() < TOL["Y"] and ball < TOL["ball_mm"])
    # energia crescendo sem entrada: E(t) − E(0,5 s) > 1e-3 g·mm²/s² (= nJ) em algum ponto de 0,5 a 5,7 s.
    # Tolerância absoluta (ESCOLHA, fixada antes de rodar): |E| é dominada pela gravidade (~2,8e3 nJ), então
    # uma tolerância relativa seria frouxa; 1e-3 nJ ≈ energia cinética de ~1e-5 g (massa de uma perna) a
    # ~14 mm/s, ~40× a cinética da cena parada (2,5e-5 nJ).
    energy_rise = bool(Emax_rise > 1e-3)
    INSTAB["b_energy"] = dict(E_0p5s=E0, max_rise=Emax_rise, rising=energy_rise)
    _audit("b")
    return dict(passed=ok, drift_max=float(dmax.max()), drift_worst_dof=ad[int(dmax.argmax())], ball_mm=ball,
                energy_E0=E0, energy_max_rise=Emax_rise)


def _groups(ad):
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    md = MotorDrive(mnt, ad, FLEX_SIGN)
    names = [f"{l}_{j}_{r}" for (l, j, r), _ in mnt.groupby(["leg", "joint", "role"])]
    return [(nm, d, s) for nm, (_, d, s) in zip(names, md.groups)]


def _hold(tq_vec, ms, jd, ad, offset=-5.0, d_target=None):
    sc, _, _ = _scene(offset)
    aidx = np.array([jd.index(n) for n in ad])
    rng = _ranges(sc, ad)
    lo = np.array([rng[n][0] for n in ad])
    hi = np.array([rng[n][1] for n in ad])
    viol, tail = 0.0, []
    steps = int(ms * 10)
    viol_step = 0.0  # descritivo: pico a cada passo de 0,1 ms (o critério usa 1 kHz, como sensores e rede)
    vt = np.zeros(steps)  # violação do DOF do grupo a cada passo (0 se dentro da faixa)
    for k in range(steps):
        sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tq_vec)
        sc.sim.step()
        qs = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
        viol_step = max(viol_step, float(np.max(np.maximum(lo - qs, qs - hi))))
        if d_target is not None:
            vt[k] = max(0.0, lo[d_target] - qs[d_target], qs[d_target] - hi[d_target])
        if k % 10 == 0:
            q = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
            viol = max(viol, float(np.max(np.maximum(lo - q, q - hi))))
            if k >= steps - 500:
                tail.append(q)
    _hold.last_step_viol = viol_step
    # §7.10: impacto = pico por passo nos primeiros 50 ms; sustentação = média por passo em 100–200 ms
    _hold.impact_peak = float(vt[:500].max())
    _hold.impact_t_ms = float(vt[:500].argmax() / 10)
    _hold.sustain_mean = float(vt[1000:2000].mean())
    _audit("cd")
    return viol, np.mean(tail, 0)


def test_c_d():
    sc, jd, ad = _scene(-5.0)
    aidx = np.array([jd.index(n) for n in ad])
    q_rest = np.asarray(sc.sim.get_joint_angles(sc.fly.name))[aidx]
    rows = []
    for name, d, s in _groups(ad):
        finals, viols, vsteps = [], [], []
        for a in (0.2, 0.4, 0.6, 0.8, 1.0):
            tq = np.zeros(len(ad))
            tq[d] = np.clip(s * a, -TORQUE_LIMIT, TORQUE_LIMIT)
            v, qf = _hold(tq, TOL["limit_ms"], jd, ad, d_target=d)
            viols.append(v)
            vsteps.append(_hold.last_step_viol)
            if a == 1.0:
                imp, imp_t, sus = _hold.impact_peak, _hold.impact_t_ms, _hold.sustain_mean
            finals.append(np.sign(s) * (qf[d] - q_rest[d]))
        f = np.array(finals)
        mono = bool(np.all(np.diff(f) >= -TOL["mono"]) and f[-1] > 0)
        rows.append(dict(group=name, dof=ad[d], viol_act1=viols[-1], viol_max=max(viols), monotonic=mono,
                         viol_step_act1=vsteps[-1], viol_step_max=max(vsteps),
                         impact_peak_act1=imp, impact_t_ms_act1=imp_t, sustain_mean_act1=sus,
                         **{f"dq_{a}": x for a, x in zip((0.2, 0.4, 0.6, 0.8, 1.0), f)}))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "s3_validation_cd.csv", index=False)
    c_ok = bool((df.viol_act1 <= TOL["Y"]).all())
    d_ok = bool(df.monotonic.all() and (df.viol_max <= TOL["Y"]).all())
    return (dict(passed=c_ok, viol_max=float(df.viol_act1.max()), n_fail=int((df.viol_act1 > TOL["Y"]).sum()),
                 viol_step_max_descritivo=float(df.viol_step_max.max())),
            dict(passed=d_ok, n_nonmonotonic=int((~df.monotonic).sum()), n_groups=len(df)))


def _welch_prom_signal(x, bin_ms=5.0, seg_ms=1000.0, band=rhythm.BAND_HZ, fmax=60.0):
    """Cópia fiel da parte espectral de rhythm.welch_peak (congelada), para um sinal contínuo já em
    janelas de bin_ms, no lugar das contagens de spikes. Conferida contra welch_peak em _check_copy()."""
    L = int(seg_ms / bin_ms)
    step = L // 2
    win = np.hanning(L)
    P = []
    for s0 in range(0, len(x) - L + 1, step):
        y = x[s0:s0 + L] - x[s0:s0 + L].mean()
        P.append(np.abs(np.fft.rfft(y * win)) ** 2)
    P = np.mean(P, axis=0)
    f = np.fft.rfftfreq(L, d=bin_ms / 1000)
    best_k, prom = None, 0.0
    for k in range(3, len(f) - 3):
        if not (band[0] <= f[k] <= band[1]) or f[k] > fmax:
            continue
        if P[k] <= P[k - 1] or P[k] <= P[k + 1]:
            continue
        flank = np.r_[P[k - 3:k - 1], P[k + 2:k + 4]]
        pr = float(P[k] / flank.mean()) if flank.mean() > 0 else 0.0
        if pr > prom:
            best_k, prom = k, pr
    if best_k is None:
        return False, None, 0.0
    return bool(prom >= rhythm.PROMINENCE), float(f[best_k]), prom


def _check_copy():
    rng = np.random.default_rng(1)
    t = np.sort(rng.uniform(0, 3000, 3000))
    t = np.r_[t, np.arange(0, 3000, 125.0)]  # componente a 8 Hz
    i = np.zeros(len(t), dtype=np.int64)
    ref = rhythm.welch_peak(i, t, np.array([0]), 0, 3000)
    counts, _ = np.histogram(t, bins=600, range=(0, 3000))
    mine = _welch_prom_signal(counts.astype(float))
    assert ref["peak_hz"] == mine[1] and abs(ref["prominence"] - mine[2]) < 1e-9, (ref, mine)


def _reproducible(peaks):
    ok = [p for p in peaks if p[0] and p[1] is not None]
    if not ok:
        return False, None
    f0 = float(np.median([p[1] for p in ok]))
    return sum(abs(p[1] - f0) <= 1.0 for p in ok) >= 3, f0


def test_e():
    from terrario.brain import banc, hybrid
    from terrario.vnc.proprio import Proprioception
    from flygym.anatomy import BodySegment
    _check_copy()
    mnt = pd.read_csv(ROOT / "runs/phase3a/s1/leg_mn_table.csv")
    rates = np.load(ROOT / "runs/phase3a/s2/diag_rates_closed.npy").mean(0)  # (391,), ordem de mnt.h
    mn_h = mnt.h.to_numpy()
    meta = banc.load_meta()
    hidx = hybrid.banc_index(hybrid.load(1.0, sign_mode="verified"), meta)
    seeds = [7000 + k for k in range(5)]
    A0, A1, T = 450, 3450, 5700
    kin = []
    for seed in seeds:
        sc, jd, ad = _scene()
        md = MotorDrive(mnt, ad, FLEX_SIGN)
        kick = np.zeros(len(ad))
        for leg in ("lf", "rm", "lh"):  # mesmo pulso de terrario/vnc/loop.py (A7)
            kick[ad.index(dof_name(leg, "ctr_pitch"))] = 10 * FLEX_SIGN["ctr_pitch"]
            kick[ad.index(dof_name(leg, "fti_pitch"))] = 10 * FLEX_SIGN["fti_pitch"]
        tarsi = [BodySegment(f"{leg}_tarsus{k}") for leg in ["lf", "lm", "lh", "rf", "rm", "rh"] for k in range(1, 6)]
        rng = np.random.default_rng(seed)
        Q, QD, LF = [], [], []
        for ms in range(T):
            q = np.asarray(sc.sim.get_joint_angles(sc.fly.name)).copy()
            qd = np.asarray(sc.sim.get_joint_velocities(sc.fly.name)).copy()
            f = sc.sim.get_bodysegment_contact_forces(sc.fly.name, tarsi, ground_only=True)
            Q.append(q); QD.append(qd); LF.append(np.linalg.norm(f, axis=1).reshape(6, 5).sum(1))
            spk = mn_h[rng.random(len(mn_h)) < rates * 1e-3]
            tq = md.step(spk, 1.0)
            if 200 <= ms < 250:
                tq = tq + kick
            sc.sim.set_actuator_inputs(sc.fly.name, ActuatorType.MOTOR, tq)
            for _ in range(10):
                sc.sim.step()
        kin.append((np.array(Q), np.array(QD), np.array(LF), jd, ad))
    rows = []
    # ângulos: 7 DOFs ativos por perna
    for leg in LEGS:
        for key in ("thc_yaw", "thc_pitch", "thc_roll", "ctr_pitch", "trf_roll", "fti_pitch", "tita_pitch"):
            peaks = []
            for Q, _, _, jd, _ in kin:
                x = Q[A0:A1, jd.index(dof_name(leg, key))].reshape(-1, 5).mean(1)
                peaks.append(_welch_prom_signal(x))
            pos, f0 = _reproducible(peaks)
            rows.append(dict(signal="angle", leg=leg, what=key, combo="-", positive=pos, peak_hz=f0,
                             max_prominence=max(p[2] for p in peaks)))
    # proprioceptores: população por perna, 4 combinações, rhythm_v2 completo
    for combo in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        runs, prs = [], []
        for seed, (Q, QD, LF, jd, _) in zip(seeds, kin):
            pr = Proprioception(meta, hidx, jd, seed=seed, combo=combo)
            rng = np.random.default_rng(seed + 17)
            ii, tt = [], []
            for ms in range(T):
                r = pr.rates(Q[ms], QD[ms], LF[ms])
                fire = rng.random(len(r)) < r * 1e-3
                ii.append(pr.h[fire]); tt.append(np.full(fire.sum(), float(ms)))
            runs.append((np.concatenate(ii), np.concatenate(tt)))
            prs.append(pr)
        for leg in LEGS:
            members = prs[0].h[prs[0].leg == leg]
            r2 = rhythm.rhythm_v2(runs, members, A0, A1)
            rows.append(dict(signal="proprio", leg=leg, what="all", combo=f"{combo[0]}{combo[1]}",
                             positive=r2["rhythmic"], peak_hz=r2["peak_hz"],
                             max_prominence=max((p["prominence"] or 0) for p in r2["per_seed"])))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "s3_validation_e.csv", index=False)
    _audit("e")
    return dict(passed=bool(not df.positive.any()), n_positive=int(df.positive.sum()), n_tests=len(df),
                max_prominence_angle=float(df[df.signal == "angle"].max_prominence.max()),
                max_prominence_proprio=float(df[df.signal == "proprio"].max_prominence.max()),
                mn_rate_mean=float(rates.mean()))


def main():
    global OUT, LIMIT
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", default="std2dt", choices=["std2dt", "direct_dt"])
    LIMIT = ap.parse_args().limit
    OUT = ROOT / "results/phase3a" / f"s3_validation_{LIMIT}"  # a 1ª validação (limite padrão) fica em s3_validation*.csv
    OUT.mkdir(exist_ok=True)
    res = dict(tol=TOL, limit=LIMIT, a=test_a(), b=test_b())
    res["c"], res["d"] = test_c_d()
    res["e"] = test_e()
    _audit("cd")
    unstable = bool(any(sum(r["warnings"].values()) or r["nonfinite"] for k, r in INSTAB.items() if k != "b_energy")
                    or INSTAB.get("b_energy", {}).get("rising", False))
    res["instability"] = dict(INSTAB, unstable=unstable)
    res["all_passed"] = all(res[k]["passed"] for k in "abcde") and not unstable
    json.dump(res, open(OUT / f"s3_validation_{LIMIT}.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
