"""PROXY de custo do cenário completo do perfil `padrao` (Fase 0).

Um processo só, relógio único:
  - física: FlyGym (NeuroMechFly + CPG de demonstração) + 2 cadeias-proxy de minhoca no
    MESMO MjModel (contatos cruzados possíveis), passo de 0,1 ms;
  - cérebro da mosca: motor numba-active (bench/lif_engines.py), conectoma v783
    completo, estímulo de GRNs de açúcar, sincronizado a cada 1 ms (10 passos);
  - 2 redes-proxy de minhoca (400 unidades densas cada), a cada 0,1 ms;
  - campo de odor 2D 256x256 (difusão explícita), atualizado a cada 10 ms.
Não há acoplamento sensório-motor real aqui: mede-se só o custo somado com a
contenção de cache/memória de rodar tudo junto.
"""

import argparse
import json
import resource
import sys
import time
from pathlib import Path

import mujoco as mj
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))

import bench_brain as bb  # noqa: E402
import bench_worm as bw  # noqa: E402
import lif_engines as le  # noqa: E402
from flygym import Simulation  # noqa: E402
from flygym.compose import FlatGroundWorld  # noqa: E402
from flygym.utils.math import Rotation3D  # noqa: E402
from flygym_demo.complex_terrain import (  # noqa: E402
    CPGController, LocomotionAction, PreprogrammedSteps, apply_locomotion_action,
    make_locomotion_fly, make_tripod_cpg_network,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-s", type=float, default=2.0)
    ap.add_argument("--no-brain", action="store_true")
    ap.add_argument("--jac", choices=["auto", "dense"], default="dense")
    args = ap.parse_args()

    fly = make_locomotion_fly(name="fly", add_adhesion=True)
    world = FlatGroundWorld()
    world.add_fly(fly, [0, 0, 0.5], Rotation3D("quat", [1, 0, 0, 0]))
    for w in range(2):
        bw.add_worm(world.mjcf_root, f"w{w}", [5.0, 1.0 + w, bw.RAD_MM + 1e-3])
    sim = Simulation(world)
    steps = PreprogrammedSteps()
    dof_order = fly.get_actuated_jointdofs_order("position")
    ctrl = CPGController(
        cpg_network=make_tripod_cpg_network(timestep=sim.timestep, intrinsic_amplitude=1.0,
                                            coupling_strength=10.0, convergence_coef=20.0,
                                            seed=0),
        preprogrammed_steps=steps, output_dof_order=dof_order)
    sim.reset()
    apply_locomotion_action(sim, fly.name, LocomotionAction(
        joint_angles=steps.default_pose_by_dof_order(dof_order),
        adhesion_onoff=np.ones(6, dtype=bool)))
    sim.warmup()
    m, d = sim.mj_model, sim.mj_data
    if args.jac == "dense":
        m.opt.jacobian = mj.mjtJacobian.mjJAC_DENSE
    worm_act = [np.array([mj.mj_name2id(m, mj.mjtObj.mjOBJ_ACTUATOR, f"w{w}_m{i}_{q}")
                          for i in range(1, bw.N_SEG) for q in range(4)]) for w in range(2)]

    brain = None
    if not args.no_brain:
        conn = le.load_connectome(str(bb.PATH_COMP), str(bb.PATH_CON))
        exc = [conn.flyid2i[x] for x in bb.SUGAR_630 if x in conn.flyid2i]
        brain = le.make_numba_active_engine(conn, exc)
        brain.run(10)

    rng = np.random.default_rng(0)
    N = 400
    W = [rng.normal(0, 1 / np.sqrt(N), (N, N)) for _ in range(2)]
    v = [np.zeros(N) for _ in range(2)]
    odor = np.zeros((256, 256))
    odor[128, 128] = 1.0
    nact = len(worm_act[0])
    seg_phase = np.repeat(np.arange(nact // 4), 4) * 0.4
    sign = np.tile([1, -1, 0, 0], nact // 4)

    n = int(args.sim_s / sim.timestep)
    tt = dict(physics=0.0, brain=0.0, worms=0.0, odor=0.0)
    t0 = time.perf_counter()
    for k in range(n):
        if brain is not None and k % 10 == 0:
            tb = time.perf_counter()
            brain.run(10)
            tt["brain"] += time.perf_counter() - tb
        tw = time.perf_counter()
        for w in range(2):
            v[w] += (-v[w] + W[w] @ np.tanh(v[w]) + 0.1) * (1e-4 / 0.01)
            u = np.clip(sign * np.sin(2 * np.pi * 0.5 * k * 1e-4 - seg_phase), 0, 1)
            d.ctrl[worm_act[w]] = u
        tt["worms"] += time.perf_counter() - tw
        if k % 100 == 0:
            to = time.perf_counter()
            lap = (np.roll(odor, 1, 0) + np.roll(odor, -1, 0) + np.roll(odor, 1, 1)
                   + np.roll(odor, -1, 1) - 4 * odor)
            odor += 0.2 * lap
            tt["odor"] += time.perf_counter() - to
        tp = time.perf_counter()
        apply_locomotion_action(sim, fly.name, ctrl.step())
        sim.step()
        tt["physics"] += time.perf_counter() - tp
    wall = time.perf_counter() - t0
    assert np.isfinite(d.qpos).all()
    print(json.dumps(dict(
        bench="full_proxy", brain=brain is not None, jac=args.jac, sim_s=args.sim_s,
        wall_per_sim_s=wall / args.sim_s,
        share={k: x / wall for k, x in tt.items()},
        nq=int(m.nq), nu=int(m.nu),
        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    )))


if __name__ == "__main__":
    main()
