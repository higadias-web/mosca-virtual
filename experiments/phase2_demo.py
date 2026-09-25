"""Fase 2: mosca no terrário com os sensores gerando dados.

A mosca anda em linha reta do solo úmido, sobe na fruta (passando pela borda do fermento) e desce
na paisagem. QUEM MOVE AS PERNAS AQUI
É O CPG DE DEMONSTRAÇÃO DO FLYGYM (flygym_demo.complex_terrain.CPGController), como no benchmark
da Fase 0: é só um arnês de teste para passar pelas superfícies e validar os sensores.
# NON-CONNECTOME: arnês de teste; não é o controle do animal (que vem na Fase 3, D-105).

Saídas:
  runs/phase2/<nome>.parquet         sensores a 200 Hz (fora do git)
  results/phase2/<nome>.json         resumo (sequência de superfícies, odor, custo, tamanho)
  results/phase2/arena.png           vista geral (câmera 'overview'), se --render

Uso: MUJOCO_GL=egl uv run python -m experiments.phase2_demo --sim-s 2.5 --render
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np

from terrario import ROOT
from terrario.body.fly import build_scene, heading_to
from terrario.body.recorder import SensorRecorder
from terrario.body.sensors import TASTE_ORGANS
from terrario.world.terrarium import SURFACES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-s", type=float, default=2.5)
    ap.add_argument("--start", type=float, nargs=2, default=[-14.0, 5.0])
    ap.add_argument("--target", type=float, nargs=2, default=[9.0, 6.0])  # centro do fermento
    ap.add_argument("--vision-hz", type=float, default=0.0)
    ap.add_argument("--sparse-jacobian", action="store_true")
    ap.add_argument("--no-sensors", action="store_true", help="só física (para o benchmark)")
    ap.add_argument("--name", default="walk_soil_fruit_landscape")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    from flygym_demo.complex_terrain import (CPGController, LocomotionAction, PreprogrammedSteps,
                                             apply_locomotion_action, make_tripod_cpg_network)

    tb = time.perf_counter()
    sc = build_scene(tuple(args.start), heading_to(args.start, args.target),
                     vision_hz=args.vision_hz, dense_jacobian=not args.sparse_jacobian)
    sim, fly = sc.sim, sc.fly
    steps = PreprogrammedSteps()
    dof = fly.get_actuated_jointdofs_order("position")
    cpg = make_tripod_cpg_network(timestep=sim.timestep, intrinsic_amplitude=1.0,
                                  coupling_strength=10.0, convergence_coef=20.0, seed=0)
    ctrl = CPGController(cpg_network=cpg, preprogrammed_steps=steps, output_dof_order=dof)
    sim.reset()
    apply_locomotion_action(sim, fly.name, LocomotionAction(
        joint_angles=steps.default_pose_by_dof_order(dof), adhesion_onoff=np.ones(6, bool)))
    sim.warmup()
    sc.env.advance_to(sim.time)
    t_build = time.perf_counter() - tb

    rec = SensorRecorder(hz=200)
    n = int(args.sim_s / sim.timestep)
    sync = int(round(1e-3 / sim.timestep))  # 1 ms (D-006)
    tp = ts = 0.0
    t0 = time.perf_counter()
    for k in range(n):
        a = time.perf_counter()
        apply_locomotion_action(sim, fly.name, ctrl.step())
        sim.step()
        tp += time.perf_counter() - a
        if not args.no_sensors and (k + 1) % sync == 0:
            a = time.perf_counter()
            sc.env.advance_to(sim.time)
            rec.maybe_add(sc.sensors.read())
            ts += time.perf_counter() - a
    wall = time.perf_counter() - t0

    out = dict(name=args.name, sim_s=args.sim_s, build_s=t_build, wall_per_sim_s=wall / args.sim_s,
               physics_per_sim_s=tp / args.sim_s, sensors_env_per_sim_s=ts / args.sim_s,
               vision_hz=args.vision_hz, jacobian="sparse" if args.sparse_jacobian else "dense",
               nv=int(sim.mj_model.nv), npair=int(sim.mj_model.npair))
    if not args.no_sensors:
        a = rec.arrays()
        # sequência de superfícies por órgão (mudanças), e odor ao longo do caminho
        seq = {}
        for j, organ in enumerate(TASTE_ORGANS):
            s = a["taste_surface"][:, j]
            touched = [SURFACES[v] for v in s if v]
            seq[organ] = [x for i, x in enumerate(touched) if i == 0 or x != touched[i - 1]]
        stance = (a["taste_surface"][:, :6] > 0).mean(0)
        rp = ROOT / "runs" / "phase2"
        rp.mkdir(parents=True, exist_ok=True)
        size = rec.to_parquet(rp / f"{args.name}.parquet",
                              dict(config=sc.world.cfg, args=vars(args), odor_channels=sc.env.odor.channels))
        out.update(
            start_xy=a["thorax_pos"][0, :2].round(2).tolist(),
            end_xy=a["thorax_pos"][-1, :2].round(2).tolist(),
            path_mm=float(np.linalg.norm(np.diff(a["thorax_pos"][:, :2], axis=0), axis=1).sum()),
            max_height_mm=float(a["thorax_pos"][:, 2].max()),
            surfaces_by_organ=seq,
            stance_fraction_by_leg=dict(zip(TASTE_ORGANS[:6], stance.round(2).tolist())),
            odor_channels=sc.env.odor.channels,
            odor_start=a["odor"][0].mean(0).round(5).tolist(),
            odor_end=a["odor"][-1].mean(0).round(5).tolist(),
            antenna_temp_start_end=[float(a["antenna_temp_c"][0].mean()),
                                    float(a["antenna_temp_c"][-1].mean())],
            log_bytes_per_sim_s=size / args.sim_s,
            n_rows=len(a["t"]),
        )
    if args.render:
        import mujoco as mj
        r = mj.Renderer(sim.mj_model, height=540, width=960)
        r.update_scene(sim.mj_data, camera="overview")
        from PIL import Image
        res = ROOT / "results" / "phase2"
        res.mkdir(parents=True, exist_ok=True)
        Image.fromarray(r.render()).save(res / "arena.png")
    res = ROOT / "results" / "phase2"
    res.mkdir(parents=True, exist_ok=True)
    with open(res / f"{args.name}.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
