"""Vídeo da Fase 2 (~12 s): travessia solo → fruta → paisagem, câmera que segue a mosca + visão geral.

A marcha é o CPG de demonstração do FlyGym (arnês de teste, NON-CONNECTOME), como em
experiments/phase2_demo.py. Legenda: tempo, superfície sob cada perna e odor de fermento.
Uso: MUJOCO_GL=egl uv run python -m experiments.video_phase2
"""

import numpy as np

from terrario import ROOT
from terrario.body.fly import build_scene, heading_to
from terrario.body.sensors import TASTE_ORGANS
from terrario.video import Recorder
from terrario.world.terrarium import SURFACES


def main(sim_s: float = 3.0):
    from flygym_demo.complex_terrain import (CPGController, LocomotionAction, PreprogrammedSteps,
                                             apply_locomotion_action, make_tripod_cpg_network)
    start, target = (-14.0, 5.0), (9.0, 6.0)
    sc = build_scene(start, heading_to(start, target), tracking_camera=True)
    sim, fly = sc.sim, sc.fly
    steps = PreprogrammedSteps()
    dof = fly.get_actuated_jointdofs_order("position")
    ctrl = CPGController(cpg_network=make_tripod_cpg_network(
        timestep=sim.timestep, intrinsic_amplitude=1.0, coupling_strength=10.0,
        convergence_coef=20.0, seed=0), preprogrammed_steps=steps, output_dof_order=dof)
    sim.reset()
    apply_locomotion_action(sim, fly.name, LocomotionAction(
        joint_angles=steps.default_pose_by_dof_order(dof), adhesion_onoff=np.ones(6, bool)))
    sim.warmup()
    rec = Recorder(sim, [f"{fly.name}/trackcam", "overview"], playback=0.25)
    fer = sc.env.odor.channels.index("fermento")
    for k in range(int(sim_s / sim.timestep)):
        apply_locomotion_action(sim, fly.name, ctrl.step())
        sim.step()
        if k % 10 == 9:
            sc.env.advance_to(sim.time)
            f = sc.sensors.read()
            surf = " ".join(f"{o}:{SURFACES[s]}" for o, s in zip(TASTE_ORGANS[:6], f.taste_surface[:6]))
            rec.maybe_capture(f"Fase 2 | t = {f.t:5.2f} s (0,25x) | {surf} | "
                              f"fermento {f.odor[:, fer].mean():.3f} | pernas: CPG de teste do FlyGym")
    out = rec.save(ROOT / "results" / "phase2" / "fase2_travessia.webm")
    print(out, len(rec.frames), "quadros")


if __name__ == "__main__":
    main()
