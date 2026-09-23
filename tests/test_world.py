"""Fase 2: arena do terrário, campos do ambiente e sensores da mosca."""

import numpy as np
import pytest

from terrario.world.terrarium import SURFACE_CODE, TerrariumWorld


@pytest.fixture(scope="module")
def world():
    return TerrariumWorld()


def test_floor_zones(world):
    cfg = world.cfg
    bc = cfg["zones"]["bacteria_colony"]["center"]
    assert world.floor_surface_at(-35.0, 25.0) == "soil"
    assert world.floor_surface_at(*bc) == "bacteria"
    assert world.floor_surface_at(35.0, 25.0) == "floor"


def test_ground_height(world):
    f = world.cfg["solids"]["fruit"]
    top = f["center"][2] + f["radii"][2]
    assert world.ground_height(f["center"][0], f["center"][1]) == pytest.approx(top)
    assert world.ground_height(-35.0, -25.0) == 0.0


def test_odor_steady_state_is_stationary(world):
    from terrario.world.fields import OdorField
    od = OdorField(world.cfg, world)
    c0 = od.c.copy()
    for _ in range(100):  # 1 s
        od.step()
    rel = np.abs(od.c - c0).max() / c0.max()
    assert rel < 1e-3, rel


def test_odor_gradients(world):
    from terrario.world.fields import OdorField
    od = OdorField(world.cfg, world)
    ch = od.channels
    y = world.cfg["solids"]["yeast"]["center"][:2]
    fr = world.cfg["solids"]["fruit"]["center"][:2]
    bac = world.cfg["zones"]["bacteria_colony"]["center"]
    far = [35.0, -25.0]
    c = od.sample(np.array([y, fr, bac, far]))
    assert c[0, ch.index("fermento")] > c[1, ch.index("fermento")] > c[3, ch.index("fermento")]
    assert c[1, ch.index("fruta")] > c[3, ch.index("fruta")]
    assert c[2, ch.index("bacterias")] > c[0, ch.index("bacterias")]


def _settle(scene, seconds=0.1):
    from flygym_demo.complex_terrain import (LocomotionAction, PreprogrammedSteps,
                                             apply_locomotion_action)
    sim, fly = scene.sim, scene.fly
    steps = PreprogrammedSteps()
    dof = fly.get_actuated_jointdofs_order("position")
    sim.reset()
    apply_locomotion_action(sim, fly.name, LocomotionAction(
        joint_angles=steps.default_pose_by_dof_order(dof), adhesion_onoff=np.ones(6, bool)))
    sim.warmup(seconds)
    scene.env.advance_to(sim.time)
    return scene.sensors.read()


@pytest.mark.parametrize("where,surface", [
    ("soil", "soil"), ("bacteria", "bacteria"), ("fruit", "fruit"), ("yeast", "yeast"),
    ("floor", "floor"),
])
def test_standing_fly_tastes_the_surface(world, where, surface):
    """Mosca parada em cada zona: os 6 tarsos tocam e reportam a superfície certa."""
    from terrario.body.fly import build_scene
    cfg = world.cfg
    xy = {"soil": (-30.0, -20.0), "bacteria": tuple(cfg["zones"]["bacteria_colony"]["center"]),
          "fruit": (3.0, 0.0), "yeast": tuple(cfg["solids"]["yeast"]["center"][:2]),
          "floor": (30.0, 20.0)}[where]
    sc = build_scene(xy, 0.0, colorize=False)
    f = _settle(sc)
    tarsi = f.taste_surface[:6]
    assert (tarsi == SURFACE_CODE[surface]).sum() >= 4, tarsi
    assert (f.taste_force[:6] > 0).sum() >= 4
    assert f.taste_surface[6] == 0            # labelo não toca o chão parado
    assert np.isfinite(f.odor).all() and f.odor.shape == (2, 3)
    assert abs(f.thorax_pos[2] - sc.world.ground_height(*xy)) < 2.0


def test_recorder_roundtrip(tmp_path, world):
    import pyarrow.parquet as pq

    from terrario.body.fly import build_scene
    from terrario.body.recorder import SensorRecorder
    sc = build_scene((-30.0, -20.0), 0.0, colorize=False)
    _settle(sc, 0.02)
    rec = SensorRecorder(hz=200)
    for _ in range(100):  # 10 ms
        sc.sim.step()
        rec.maybe_add(sc.sensors.read())
    size = rec.to_parquet(tmp_path / "s.parquet", {"test": 1})
    t = pq.read_table(tmp_path / "s.parquet")
    assert size > 0 and t.num_rows == 2
    assert b"terrario" in t.schema.metadata
