import math
import tkinter as tk
import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship, WorldConfig
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_data import build_siege_line_level, build_solar_crossing_level
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.chase_helm import draw_xwing_cockpit_hud
from gravity_ho_matey.render.gravity_field_viz import (
    HEATMAP_NORM_FLOOR,
    heatmap_cell_visible,
    inside_black_hole_footprint,
)
from gravity_ho_matey.render.launch_countdown_overlay import accent_for_theme
from gravity_ho_matey.render.starfield_viz import draw_chase_parallax_stars, draw_layered_starfield, star_tones_for_theme
from gravity_ho_matey.render.view_renderers import PerspectiveViewRenderer, TacticalViewRenderer
from gravity_ho_matey.render.world_draw import draw_gravity_heatmap


def _tk_canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


def test_heatmap_norm_floor() -> None:
    assert heatmap_cell_visible(HEATMAP_NORM_FLOOR) is True
    assert heatmap_cell_visible(HEATMAP_NORM_FLOOR - 0.01) is False


def test_black_hole_footprint_suppresses_core() -> None:
    well = GravityWell(pos=Vec2(100.0, 100.0), strength=500.0, radius=40.0, kind="black_hole", label="")
    assert inside_black_hole_footprint((well,), 100.0, 100.0) is True
    assert inside_black_hole_footprint((well,), 200.0, 200.0) is False


def test_star_tones_per_theme() -> None:
    cove = star_tones_for_theme("cove")
    siege = star_tones_for_theme("siege")
    assert cove != siege
    assert star_tones_for_theme("unknown") == cove


def test_layered_starfield_draws_without_error() -> None:
    root, canvas = _tk_canvas()
    draw_layered_starfield(
        canvas,
        x=0.0,
        y=0.0,
        width=320.0,
        height=240.0,
        elapsed=1.5,
        theme="rift",
    )
    assert len(canvas.find_all()) > 0
    root.destroy()


def test_tactical_heatmap_suppresses_black_hole_core() -> None:
    root, canvas = _tk_canvas()
    bh = GravityWell(pos=Vec2(2400.0, 1600.0), strength=900.0, radius=80.0, kind="black_hole", label="")
    world = GameWorld(
        config=WorldConfig(width=4800, height=3200, viewport_width=960, viewport_height=640),
        ship=Ship(pos=Vec2(2400.0, 1600.0)),
        asteroids=[],
        wells=[bh],
        beacons=[],
        finish_gate=FinishGate(Rect(0, 0, 10, 10)),
    )
    field = GravityField.bake(
        world.wells,
        world_width=world.config.width,
        world_height=world.config.height,
        cols=32,
        rows=32,
        gravity_scale=world.config.gravity_scale,
    )
    hud_top = 54
    camera = ViewCamera(mode=CameraMode.TACTICAL)
    camera.set_play_layout(hud_top)
    camera.update_follow(world.ship.pos, world.config, 0.016)
    draw_gravity_heatmap(
        canvas,
        field,
        camera,
        y_offset=hud_top,
        alpha_step=2,
        ship_pos=world.ship.pos,
        world=world,
    )
    center_x = camera.viewport_width * 0.5
    center_y = hud_top + (camera.viewport_height - hud_top) * 0.5
    for item in canvas.find_all():
        if canvas.type(item) != "oval":
            continue
        x0, y0, x1, y1 = canvas.coords(item)
        cx = (x0 + x1) * 0.5
        cy = (y0 + y1) * 0.5
        assert math.hypot(cx - center_x, cy - center_y) > 28.0
    root.destroy()


def test_chase_parallax_stars_wrap_on_high_speed() -> None:
    root, canvas = _tk_canvas()
    world = build_solar_crossing_level()
    world.ship.vel = Vec2(420.0, 0.0)
    camera = ViewCamera(mode=CameraMode.CHASE, viewport_width=960, viewport_height=640)
    camera.set_play_layout(54.0)
    draw_chase_parallax_stars(
        canvas,
        camera=camera,
        world=world,
        horizon=camera.chase_horizon_y(),
    )
    for item in canvas.find_all():
        x0, _, x1, _ = canvas.coords(item)
        assert 0.0 <= x0 <= 960.0
        assert 0.0 <= x1 <= 960.0
    root.destroy()


def test_theme_accents_differ_for_siege_and_cove() -> None:
    assert accent_for_theme("siege") != accent_for_theme("cove")
    assert accent_for_theme("siege") == palette.SIEGE_HUD_ACCENT


def test_tactical_and_chase_renderers_draw_siege_without_error() -> None:
    root, canvas = _tk_canvas()
    world = build_siege_line_level()
    field = GravityField.bake(
        world.wells,
        world_width=world.config.width,
        world_height=world.config.height,
        cols=32,
        rows=32,
        gravity_scale=world.config.gravity_scale,
    )
    tactical = ViewCamera(mode=CameraMode.TACTICAL)
    tactical.set_play_layout(54)
    tactical.update_follow(world.ship.pos, world.config, 0.016)
    TacticalViewRenderer().draw(canvas, world, tactical, field, hud_top=54)
    assert len(canvas.find_all()) > 80

    canvas.delete("all")
    chase = ViewCamera(mode=CameraMode.CHASE)
    chase.set_play_layout(54)
    chase.update_follow(world.ship.pos, world.config, 0.016)
    PerspectiveViewRenderer().draw(canvas, world, chase, field, hud_top=54)
    assert len(canvas.find_all()) > 120
    root.destroy()


def test_helm_hud_uses_sector_accent() -> None:
    root, canvas = _tk_canvas()
    world = build_siege_line_level()
    field = GravityField.bake(
        world.wells,
        world_width=world.config.width,
        world_height=world.config.height,
        cols=24,
        rows=24,
        gravity_scale=world.config.gravity_scale,
    )
    camera = ViewCamera(mode=CameraMode.CHASE)
    camera.set_play_layout(54.0)
    anchor_x, anchor_y = camera.chase_anchor()
    draw_xwing_cockpit_hud(
        canvas,
        world,
        camera,
        field,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        ship_pos=world.ship.pos,
        ship_angle=world.ship.angle,
        hud_top=54.0,
    )
    accent = accent_for_theme("siege")
    line_items = [i for i in canvas.find_all() if canvas.type(i) == "line"]
    assert line_items
    colors = {canvas.itemcget(i, "fill") for i in line_items}
    assert accent in colors
    root.destroy()


