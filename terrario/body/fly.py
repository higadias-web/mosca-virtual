"""Monta a cena da Fase 2: mosca NeuroMechFly (FlyGym 2.1) no terrário, com ambiente e sensores.

Corpo: `flygym_demo.complex_terrain.make_locomotion_fly` (third_party/flygym/src/flygym_demo/
complex_terrain/common.py): pernas com atuadores de posição e adesão tarsal, parâmetros do
FlyGym. A probóscide não tem juntas neste corpo; a extensão da probóscide (MN9 → corpo) entra na
Fase 3, junto com a ⚠️ D-105.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from flygym import Simulation
from flygym.utils.math import Rotation3D
from flygym_demo.complex_terrain import make_locomotion_fly

from terrario.body.sensors import FlySensors
from terrario.world.fields import Environment
from terrario.world.terrarium import DEFAULT_CONFIG, TerrariumWorld


@dataclass
class FlyScene:
    sim: Simulation
    fly: object
    world: TerrariumWorld
    env: Environment
    sensors: FlySensors


def build_scene(spawn_xy=(-15.0, 4.0), heading_rad: float = 0.0, *, vision_hz: float = 0.0,
                config=DEFAULT_CONFIG, dense_jacobian: bool = True, name: str = "fly",
                colorize: bool = True, tracking_camera: bool = False) -> FlyScene:
    fly = make_locomotion_fly(name=name, add_adhesion=True, colorize=colorize)
    if tracking_camera:
        fly.add_tracking_camera()  # flygym BaseFly.add_tracking_camera ("<nome>/trackcam")
    if vision_hz > 0:
        fly.add_vision()
    world = TerrariumWorld(config=config, dense_jacobian=dense_jacobian)
    x, y = spawn_xy
    z = world.ground_height(x, y) + 0.5  # como o [0, 0, 0.5] dos exemplos do FlyGym
    q = Rotation3D("quat", [math.cos(heading_rad / 2), 0, 0, math.sin(heading_rad / 2)])
    world.add_fly(fly, [x, y, z], q)
    sim = Simulation(world)
    env = Environment(world.cfg, world)
    sensors = FlySensors(sim, fly, world, env, vision_hz=vision_hz)
    return FlyScene(sim, fly, world, env, sensors)


def heading_to(src_xy, dst_xy) -> float:
    return float(np.arctan2(dst_xy[1] - src_xy[1], dst_xy[0] - src_xy[0]))
