"""PROXY de custo de 1 C. elegans (Fase 0). NÃO é o modelo do projeto.

Mede só custo computacional, sem nenhuma pretensão biológica:
  - corpo: cadeia de N_SEG cápsulas em escala real (~1 mm × 0,06 mm), 2 dobradiças por
    junta, uma junta livre na cabeça, 4 atuadores ("quadrantes") por segmento, contato
    com o chão (fricção isotrópica), passo de 0,1 ms;
  - rede: 400 unidades graduadas densas (302 neurônios + 95 músculos, arredondado),
    dv/dt = (-v + W tanh(v) + I)/tau, com W aleatório. É só carga de CPU.
  - acionamento: onda senoidal (NON-CONNECTOME, só para gerar contatos).

Uso: uv run python bench/bench_worm.py --sim-s 2 --n-worms 1
"""

import argparse
import json
import resource
import time

import mujoco as mj
import numpy as np

N_SEG = 24
LEN_MM = 1.0
RAD_MM = 0.03


def add_worm(spec: mj.MjSpec, name: str, pos, n_seg=N_SEG):
    """Adiciona a cadeia proxy a um MjSpec (também usado pelo cenário completo)."""
    seg = LEN_MM / n_seg
    parent = spec.worldbody.add_body(name=f"{name}_s0", pos=list(pos))
    parent.add_freejoint(name=f"{name}_root")
    bodies = [parent]
    for i in range(n_seg):
        b = bodies[-1] if i == 0 else bodies[-1].add_body(name=f"{name}_s{i}", pos=[seg, 0, 0])
        if i > 0:
            for ax, tag in (([0, 0, 1], "yaw"), ([0, 1, 0], "pitch")):
                b.add_joint(name=f"{name}_j{i}_{tag}", type=mj.mjtJoint.mjJNT_HINGE, axis=ax,
                            range=[-0.6, 0.6], limited=1, stiffness=[1e-4, 0, 0],
                            damping=[2e-5, 0, 0])
        b.add_geom(type=mj.mjtGeom.mjGEOM_CAPSULE, fromto=[0, 0, 0, seg, 0, 0],
                   size=[RAD_MM, 0, 0], density=1.07e-3, friction=[1.0, 0.005, 0.0001])
        if i > 0:
            bodies.append(b)
    acts = []
    for i in range(1, n_seg):
        for q, (tag, sign) in enumerate((("yaw", 1), ("yaw", -1), ("pitch", 1), ("pitch", -1))):
            a = spec.add_actuator(name=f"{name}_m{i}_{q}", target=f"{name}_j{i}_{tag}",
                                  trntype=mj.mjtTrn.mjTRN_JOINT)
            a.set_to_motor()
            a.gear[0] = sign * 1e-4
            a.ctrllimited = 1
            a.ctrlrange = [0, 1]
            acts.append(a)
    # sem autocolisão (cápsulas vizinhas se sobrepõem: segmento 42 µm < 2 × raio)
    for i in range(n_seg):
        for j in range(i + 1, n_seg):
            spec.add_exclude(bodyname1=f"{name}_s{i}", bodyname2=f"{name}_s{j}")
    return acts


def build(n_worms):
    spec = mj.MjSpec()
    spec.option.timestep = 1e-4
    spec.option.gravity = [0, 0, -9810]
    spec.worldbody.add_geom(type=mj.mjtGeom.mjGEOM_PLANE, size=[10, 10, 0.1])
    for w in range(n_worms):
        add_worm(spec, f"w{w}", [0, 0.3 * w, RAD_MM + 1e-3])
    m = spec.compile()
    # o modo automático escolhe Jacobiano esparso para nv >= 60, 2x mais lento aqui
    m.opt.jacobian = mj.mjtJacobian.mjJAC_DENSE
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-s", type=float, default=2.0)
    ap.add_argument("--n-worms", type=int, default=1)
    args = ap.parse_args()
    m = build(args.n_worms)
    d = mj.MjData(m)
    rng = np.random.default_rng(0)
    N = 400
    W = [rng.normal(0, 1 / np.sqrt(N), (N, N)) for _ in range(args.n_worms)]
    v = [np.zeros(N) for _ in range(args.n_worms)]
    n = int(args.sim_s / m.opt.timestep)
    nact = m.nu // args.n_worms
    seg_phase = np.repeat(np.arange(nact // 4), 4) * 0.4
    sign = np.tile([1, -1, 0, 0], nact // 4)
    t_net = 0.0
    t0 = time.perf_counter()
    for k in range(n):
        t = k * m.opt.timestep
        tn = time.perf_counter()
        for w in range(args.n_worms):
            v[w] += (-v[w] + W[w] @ np.tanh(v[w]) + 0.1) * (1e-4 / 0.01)
        t_net += time.perf_counter() - tn
        # NON-CONNECTOME (apenas proxy): onda viajante
        u = np.clip(sign * np.sin(2 * np.pi * 0.5 * t - seg_phase), 0, 1)
        d.ctrl[:] = np.tile(u, args.n_worms)
        mj.mj_step(m, d)
    wall = time.perf_counter() - t0
    assert np.isfinite(d.qpos).all(), "instável"
    print(json.dumps(dict(
        bench="worm_proxy", n_worms=args.n_worms, sim_s=args.sim_s,
        wall_per_sim_s=wall / args.sim_s, net_share=t_net / wall,
        nq=int(m.nq), nu=int(m.nu), ncon_final=int(d.ncon),
        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    )))


if __name__ == "__main__":
    main()
