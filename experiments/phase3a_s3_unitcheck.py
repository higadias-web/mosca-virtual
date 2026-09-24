"""Fase 3a, Sessão 3: checagem da leitura "mN·m/°" da Tabela 1 de Wang et al. 2025 (FASE3_PLANO §7.6).

Número do artigo a reproduzir (bioRxiv 10.1101/2025.04.29.651225 v2, PMC12324252): "a 40-fold increase
implemented uniformly across all leg joints was necessary to support the fly" (com a rigidez medida, a
mosca simulada cai). As leituras possíveis da unidade diferem por fatores de 10³ (mN·m, mN·mm, µN·m…),
então o multiplicador que sustenta a mosca NO NOSSO MODELO discrimina a leitura.

Protocolo (pré-registrado): NeuroMechFly com passive="wang2025" e rigidez × m (amortecimento pelo mesmo
critério, com o k escalado), livre sobre chão plano (flygym FlatGroundWorld, spawn a 0,5 mm como nos
exemplos do FlyGym), torque 0, sem adesão, 1 s. "Sustenta" = entre 0,5 e 1,0 s, a força de contato de
tórax, abdome e cabeça com o chão é zero em ≥ 95 % dos passos amostrados (a 1 kHz). m* = menor m da
grade que sustenta. Referência de sanidade: m = 1000 precisa sustentar (senão a checagem é inválida).
Critério: m* ∈ [10, 160] (fator 4 em torno de 40) → a leitura mN·m/° se mantém; fora → a leitura cai.
Descritivo (não é critério): com m = 1, tempo até o primeiro contato do corpo (o artigo: "fell within
20 milliseconds").
Saída: results/phase3a/s3_unitcheck.json
"""

from __future__ import annotations

import json

import numpy as np

from flygym import Simulation
from flygym.anatomy import BodySegment
from flygym.compose import ActuatorType
from flygym.compose.world import FlatGroundWorld
from flygym.utils.math import Rotation3D

from terrario import ROOT
from terrario.vnc.apparatus import make_neuromuscular_fly

GRID = [1, 2.5, 5, 10, 20, 40, 80, 160, 320, 640, 1000]
BODY = [BodySegment(s) for s in ("c_thorax", "c_head", "c_abdomen12", "c_abdomen3", "c_abdomen4",
                                 "c_abdomen5", "c_abdomen6")]


def run(m: float) -> dict:
    fly = make_neuromuscular_fly(passive="wang2025", k_scale=m)
    world = FlatGroundWorld()
    world.add_fly(fly, [0, 0, 0.5], Rotation3D("quat", [1, 0, 0, 0]))
    sim = Simulation(world)
    bodies = [b for b in BODY if b in fly.get_bodysegs_order()]
    na = len(fly.get_actuated_jointdofs_order(ActuatorType.MOTOR))
    sim.reset()
    dt = sim.mj_model.opt.timestep
    n = int(1.0 / dt)
    touch, first = [], None
    thor = fly.get_bodysegs_order().index(BodySegment("c_thorax"))
    z0 = float(sim.get_body_positions(fly.name)[thor, 2])
    for k in range(n):
        sim.set_actuator_inputs(fly.name, ActuatorType.MOTOR, np.zeros(na))
        sim.step()
        if k % 10 == 0:
            f = sim.get_bodysegment_contact_forces(fly.name, bodies, ground_only=True)
            t = bool(np.linalg.norm(f, axis=1).sum() > 0)
            if t and first is None:
                first = k * dt * 1000
            if k * dt >= 0.5:
                touch.append(t)
    z1 = float(sim.get_body_positions(fly.name)[thor, 2])
    frac = float(np.mean(touch))
    return dict(m=m, frac_body_contact=frac, supports=frac <= 0.05, first_contact_ms=first,
                thorax_z0=z0, thorax_z1=z1)


def main():
    rows = [run(m) for m in GRID]
    for r in rows:
        print(r)
    sup = [r["m"] for r in rows if r["supports"]]
    ref_ok = rows[-1]["supports"]
    m_star = min(sup) if sup else None
    # monotonicidade: todo m ≥ m* também sustenta
    mono = m_star is not None and all(r["supports"] for r in rows if r["m"] >= m_star)
    fly = make_neuromuscular_fly(passive="wang2025")
    world = FlatGroundWorld()
    world.add_fly(fly, [0, 0, 0.5], Rotation3D("quat", [1, 0, 0, 0]))
    mass = float(Simulation(world).mj_model.body_subtreemass[1])
    res = dict(grid=rows, m_star=m_star, monotonic=mono, reference_1000_supports=ref_ok,
               valid=bool(ref_ok), total_mass_model=mass,
               reading_holds=bool(ref_ok and m_star is not None and 10 <= m_star <= 160),
               paper_multiplier=40, first_contact_ms_at_m1=rows[0]["first_contact_ms"])
    json.dump(res, open(ROOT / "results/phase3a/s3_unitcheck.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k != "grid"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
