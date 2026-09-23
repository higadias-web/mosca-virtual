"""Benchmark do corpo da mosca (FlyGym 2.1.0 / NeuroMechFly v2), isolado.

Caminhada com o CPGController de demonstração do FlyGym, em FlatGroundWorld, com
passo de 0,1 ms. Segue tutorials/4a_cpg_controller.ipynb (FlyGym v2.1.0). O CPG serve
só para gerar carga de contato realista, não será o controlador do projeto.

Uso: MUJOCO_GL=egl uv run python bench/bench_flygym.py --vision-hz 0 --sim-s 2
  --vision-hz 0    sem visão
  --vision-hz N    lê os omatídeos (Simulation.get_ommatidia_readouts) N vezes por s simulado
"""

import argparse
import json
import resource
import time

import numpy as np

from flygym import Simulation
from flygym.compose import FlatGroundWorld
from flygym.utils.math import Rotation3D
from flygym_demo.complex_terrain import (
    CPGController,
    LocomotionAction,
    PreprogrammedSteps,
    apply_locomotion_action,
    make_locomotion_fly,
    make_tripod_cpg_network,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-s", type=float, default=2.0)
    ap.add_argument("--vision-hz", type=float, default=0.0)
    args = ap.parse_args()

    tb = time.perf_counter()
    fly = make_locomotion_fly(name="bench", add_adhesion=True)
    if args.vision_hz > 0:
        fly.add_vision()
    world = FlatGroundWorld()
    world.add_fly(fly, [0, 0, 0.5], Rotation3D("quat", [1, 0, 0, 0]))
    sim = Simulation(world)
    steps = PreprogrammedSteps()
    dof_order = fly.get_actuated_jointdofs_order("position")
    cpg = make_tripod_cpg_network(timestep=sim.timestep, intrinsic_amplitude=1.0,
                                  coupling_strength=10.0, convergence_coef=20.0, seed=0)
    ctrl = CPGController(cpg_network=cpg, preprogrammed_steps=steps, output_dof_order=dof_order)
    sim.reset()
    apply_locomotion_action(sim, fly.name, LocomotionAction(
        joint_angles=steps.default_pose_by_dof_order(dof_order),
        adhesion_onoff=np.ones(6, dtype=bool)))
    sim.warmup()
    tbuild = time.perf_counter() - tb

    n = int(args.sim_s / sim.timestep)
    every = int(round(1 / (args.vision_hz * sim.timestep))) if args.vision_hz > 0 else 0
    t_vis = 0.0
    x0 = sim.get_body_positions(fly.name)[0].copy()
    t0 = time.perf_counter()
    for k in range(n):
        apply_locomotion_action(sim, fly.name, ctrl.step())
        sim.step()
        if every and k % every == 0:
            tv = time.perf_counter()
            obs = sim.get_ommatidia_readouts(fly.name)
            t_vis += time.perf_counter() - tv
    wall = time.perf_counter() - t0
    x1 = sim.get_body_positions(fly.name)[0]
    print(json.dumps(dict(
        bench="flygym", vision_hz=args.vision_hz, sim_s=args.sim_s, timestep=sim.timestep,
        build_s=tbuild, wall_per_sim_s=wall / args.sim_s,
        vision_share=t_vis / wall if wall else 0.0,
        displacement_mm=float(np.linalg.norm(x1[:2] - x0[:2])),
        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        n_qpos=int(sim.mj_model.nq), n_geom=int(sim.mj_model.ngeom),
    )))


if __name__ == "__main__":
    main()
