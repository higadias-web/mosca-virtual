"""Arena do terrário no FlyGym 2.1 (MjSpec), em escala real (mm).

Tudo aqui é ambiente (NON-CONNECTOME). A disposição vem de configs/arena.yaml.

Integração com o FlyGym (third_party/flygym, v2.1.0):
  - BaseWorld (flygym/compose/world/base_world.py) + _GroundContactMixin: a mosca ganha uma
    free joint e pares de contato (<pair>) entre cada geom dos segmentos escolhidos e cada geom
    de `ground_geoms`. Mesmo padrão de flygym/compose/world/complex_terrain.py.
  - Com mais de um geom de chão, o FlyGym não cria sensores de contato por perna
    (_add_ground_contact_sensors). A leitura por superfície é nossa: terrario/body/sensors.py
    percorre mj_data.contact e usa `surface_of_geom` abaixo.

Superfícies: cada sólido tem um rótulo (fruit, yeast, water, stone, moss, floor). O piso plano
e os montes marcados "floor" recebem o rótulo pela posição: solo úmido (x < soil_x_max),
colônia de bactérias (disco no solo) ou piso da paisagem.
"""

from __future__ import annotations

from pathlib import Path
from typing import override

import mujoco as mj
import numpy as np
import yaml

from flygym.anatomy import BodySegment, ContactBodiesPreset
from flygym.compose.physics import ContactParams
from flygym.compose.world.base_world import BaseWorld, _GroundContactMixin
from flygym.utils.mjcf import GEOM_TYPES, add_material, add_texture

from terrario import ROOT

DEFAULT_CONFIG = ROOT / "configs" / "arena.yaml"

# Códigos inteiros das superfícies (log e sensores). 0 = sem contato.
SURFACES = ["none", "soil", "bacteria", "floor", "fruit", "yeast", "water", "stone", "moss",
            "wall"]
SURFACE_CODE = {s: i for i, s in enumerate(SURFACES)}

# Segmentos com contato: o preset padrão do FlyGym (pernas, tórax, abdome, cabeça) + a probóscide
# (c_rostrum, c_haustellum), que o preset não inclui e que carrega o labelo (gustação).
CONTACT_SEGMENTS = [*ContactBodiesPreset.LEGS_THORAX_ABDOMEN_HEAD.to_body_segments_list(),
                    BodySegment("c_rostrum"), BodySegment("c_haustellum")]


class TerrariumWorld(_GroundContactMixin, BaseWorld):
    """Terrário: piso com zonas, fruta, fermento, gotícula, pedrinhas, musgo, relevo, paredes."""

    @override
    def __init__(self, name: str = "terrario", config: Path | dict = DEFAULT_CONFIG,
                 dense_jacobian: bool = True) -> None:
        super().__init__(name=name)
        cfg = config if isinstance(config, dict) else yaml.safe_load(Path(config).read_text())
        self.cfg = cfg
        self.dense_jacobian = dense_jacobian
        hx, hy = cfg["arena"]["half_size"]
        self.half_size = (hx, hy)
        self.ground_geoms = []
        self._geom_surface: dict[str, str] = {}
        root = self.mjcf_root

        # ---- piso (plano) e marcações visuais das zonas (sem colisão)
        add_texture(root, name="terra_floor", type="2d", builtin="flat", width=64, height=64,
                    rgb1=(0.80, 0.74, 0.62), rgb2=(0.80, 0.74, 0.62))
        add_material(root, name="terra_floor", texture="terra_floor", reflectance=0.05)
        floor = root.worldbody.add_geom(type=GEOM_TYPES["plane"], name="floor",
                                        material="terra_floor", size=(hx, hy, 1),
                                        contype=0, conaffinity=0)
        self._add_ground(floor, "floor")
        xs = cfg["zones"]["soil_x_max"]
        self._visual_box("zone_soil", ((xs - (-hx)) / 2, hy, 0.002), ((xs + -hx) / 2, 0, 0.0),
                         (0.36, 0.26, 0.18, 1))
        bc = cfg["zones"]["bacteria_colony"]
        root.worldbody.add_geom(type=GEOM_TYPES["cylinder"], name="zone_bacteria",
                                size=(bc["radius"], 0.003, 0), pos=(*bc["center"], 0.0),
                                rgba=(0.85, 0.80, 0.55, 1), contype=0, conaffinity=0, group=1)

        # ---- sólidos
        for key, s in cfg["solids"].items():
            if s["shape"] == "ellipsoid":
                g = root.worldbody.add_geom(type=GEOM_TYPES["ellipsoid"], name=key,
                                            size=tuple(s["radii"]), pos=tuple(s["center"]),
                                            rgba=tuple(s["rgba"]), contype=0, conaffinity=0)
            elif s["shape"] == "sphere":
                g = root.worldbody.add_geom(type=GEOM_TYPES["sphere"], name=key,
                                            size=(s["radius"], 0, 0), pos=tuple(s["center"]),
                                            rgba=tuple(s["rgba"]), contype=0, conaffinity=0)
            else:
                raise ValueError(f"forma desconhecida: {s['shape']}")
            self._add_ground(g, s["surface"])

        # ---- paredes de vidro
        h = cfg["arena"]["wall_height"]
        t = 0.5
        for nm, size, pos in [
            ("wall_xn", (t, hy + t, h / 2), (-hx - t, 0, h / 2)),
            ("wall_xp", (t, hy + t, h / 2), (hx + t, 0, h / 2)),
            ("wall_yn", (hx, t, h / 2), (0, -hy - t, h / 2)),
            ("wall_yp", (hx, t, h / 2), (0, hy + t, h / 2)),
        ]:
            g = root.worldbody.add_geom(type=GEOM_TYPES["box"], name=nm, size=size, pos=pos,
                                        rgba=(0.8, 0.9, 1.0, 0.12), contype=0, conaffinity=0)
            self._add_ground(g, "wall")

        # luz de cima (o headlight do NeuroMechFly continua)
        root.worldbody.add_light(name="sun", pos=(0, 0, 120), dir=(0, 0, -1),
                                 diffuse=(0.5, 0.5, 0.5), castshadow=False)
        # câmera de visão geral (fixa)
        root.worldbody.add_camera(name="overview", pos=(0, -75, 70), xyaxes=(1, 0, 0, 0, 0.68, 0.73))

    # ------------------------------------------------------------------ montagem
    def _add_ground(self, geom, surface: str) -> None:
        self.ground_geoms.append(geom)
        self._geom_surface[geom.name] = surface

    def _visual_box(self, name, size, pos, rgba) -> None:
        self.mjcf_root.worldbody.add_geom(type=GEOM_TYPES["box"], name=name, size=size, pos=pos,
                                          rgba=rgba, contype=0, conaffinity=0, group=1)

    @override
    def _attach_fly_mjcf(self, fly, spawn_position, spawn_rotation, *,
                         bodysegs_with_ground_contact=None,
                         ground_contact_params: ContactParams = ContactParams(),
                         add_ground_contact_sensors: bool = False) -> set[str]:
        segs = bodysegs_with_ground_contact or CONTACT_SEGMENTS
        return super()._attach_fly_mjcf(
            fly, spawn_position, spawn_rotation, bodysegs_with_ground_contact=segs,
            ground_contact_params=ground_contact_params,
            add_ground_contact_sensors=add_ground_contact_sensors)

    @override
    def compile(self):
        if self.dense_jacobian:
            # CLAUDE.md, riscos: com vários corpos no mesmo MjModel o Jacobiano esparso automático
            # custa caro; o denso foi medido mais rápido (BENCHMARK §3–4). Revalidado na Fase 2.
            self.mjcf_root.option.jacobian = mj.mjtJacobian.mjJAC_DENSE
        return super().compile()

    # ------------------------------------------------------------------ consultas
    def surface_of_geom(self, geom_name: str, pos_xy) -> str:
        """Rótulo da superfície tocada num geom do chão, na posição (x, y) do contato."""
        s = self._geom_surface[geom_name]
        if s != "floor":
            return s
        return self.floor_surface_at(*pos_xy[:2])

    def floor_surface_at(self, x: float, y: float) -> str:
        z = self.cfg["zones"]
        if x < z["soil_x_max"]:
            bc = z["bacteria_colony"]
            if (x - bc["center"][0]) ** 2 + (y - bc["center"][1]) ** 2 <= bc["radius"] ** 2:
                return "bacteria"
            return "soil"
        return "floor"

    def solid_surface_z(self, key: str, x: float, y: float) -> float:
        """Altura do topo de um sólido em (x, y), ou -inf fora dele (para posicionar a mosca)."""
        s = self.cfg["solids"][key]
        c = np.array(s["center"], dtype=float)
        r = np.array(s["radii"] if s["shape"] == "ellipsoid" else [s["radius"]] * 3, dtype=float)
        q = ((x - c[0]) / r[0]) ** 2 + ((y - c[1]) / r[1]) ** 2
        return float(c[2] + r[2] * np.sqrt(1 - q)) if q < 1 else -np.inf

    def ground_height(self, x: float, y: float) -> float:
        return max([0.0] + [self.solid_surface_z(k, x, y) for k in self.cfg["solids"]])
