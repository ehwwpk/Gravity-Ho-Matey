from __future__ import annotations

import math
from dataclasses import dataclass

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y, SURFACE_WRAP_WIDTH
from gravity_ho_matey.render.brood_surface_mesh import mesh_for
from gravity_ho_matey.render.brood_viz_helpers import draw_brood_ground_shadow, draw_brood_rim_bloom
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, chase_depth_fade, depth_faded_material, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon
from gravity_ho_matey.render import palette

FAUNA_DRAW_MAX = 28
_FAUNA_VIEW_MARGIN = 1600.0


@dataclass(frozen=True, slots=True)
class _FaunaSpec:
    frac_x: float
    height_above_floor: float
    kind: str
    seed: int
    scale: float


# Neutral mid-air nursery life — deterministic wrap-fraction anchors.
_FAUNA_SPECS: tuple[_FaunaSpec, ...] = (
    _FaunaSpec(0.055, 220.0, "spore_jelly", 3, 1.15),
    _FaunaSpec(0.102, 340.0, "veil_wisp", 7, 1.25),
    _FaunaSpec(0.148, 180.0, "drift_pod", 11, 0.95),
    _FaunaSpec(0.198, 280.0, "spore_jelly", 17, 1.05),
    _FaunaSpec(0.252, 420.0, "drift_ribbon", 23, 1.1),
    _FaunaSpec(0.305, 160.0, "chitin_puff", 29, 0.88),
    _FaunaSpec(0.358, 300.0, "veil_wisp", 31, 1.0),
    _FaunaSpec(0.412, 240.0, "spore_jelly", 37, 1.2),
    _FaunaSpec(0.468, 380.0, "drift_pod", 41, 1.05),
    _FaunaSpec(0.518, 200.0, "drift_ribbon", 43, 0.92),
    _FaunaSpec(0.572, 360.0, "chitin_puff", 47, 1.12),
    _FaunaSpec(0.628, 260.0, "veil_wisp", 53, 1.18),
    _FaunaSpec(0.682, 190.0, "spore_jelly", 59, 0.98),
    _FaunaSpec(0.738, 320.0, "drift_ribbon", 61, 1.08),
    _FaunaSpec(0.792, 210.0, "drift_pod", 67, 1.0),
    _FaunaSpec(0.848, 350.0, "chitin_puff", 71, 1.05),
    _FaunaSpec(0.902, 270.0, "veil_wisp", 73, 1.22),
    _FaunaSpec(0.958, 400.0, "spore_jelly", 79, 1.1),
)


def _material_for_fauna(kind: str, rig: LightRig):
    if kind in ("spore_jelly", "veil_wisp"):
        return material_for("brood_flora", theme=rig.theme, view=rig.view)
    if kind == "chitin_puff":
        return material_for("brood_chitin", theme=rig.theme, view=rig.view)
    if kind == "drift_pod":
        return material_for("brood_membrane", theme=rig.theme, view=rig.view)
    return material_for("brood_crystal", theme=rig.theme, view=rig.view)


def _wrap_near(ship_x: float, target_x: float) -> float:
    return min(
        abs(target_x - ship_x),
        abs(target_x - ship_x - SURFACE_WRAP_WIDTH),
        abs(target_x - ship_x + SURFACE_WRAP_WIDTH),
    )


def _fauna_world_pos(spec: _FaunaSpec, elapsed: float) -> Vec2:
    x = SURFACE_WRAP_WIDTH * spec.frac_x
    bob = math.sin(elapsed * 0.55 + spec.seed) * 22.0
    sway = math.sin(elapsed * 0.38 + spec.seed * 1.7) * 36.0
    y = SURFACE_FLOOR_Y - spec.height_above_floor + bob
    return Vec2(x + sway, y)


def _draw_drift_ribbon(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    rig: LightRig,
    material,
    seed: int,
    scale: float,
    elapsed: float,
    to_screen,
) -> None:
    pts: list[tuple[float, float]] = []
    segments = 5
    for i in range(segments + 1):
        t = i / segments
        wx = pos.x + (t - 0.5) * 90.0 * scale
        wy = pos.y + math.sin(elapsed * 1.6 + t * 4.2) * 28.0 * scale - t * 18.0 * scale
        sx, sy = to_screen(Vec2(wx, wy))
        pts.append((sx, sy))
    for i in range(len(pts) - 1):
        canvas.create_line(
            pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
            fill=material.rim, width=2, smooth=True,
        )
    draw_fog_glow(canvas, pts[0][0], pts[0][1], 10.0 * scale, palette.CHASE_FOG_BROOD, pulse=elapsed + seed)
    draw_fog_glow(canvas, pts[-1][0], pts[-1][1], 12.0 * scale, palette.CHASE_FOG_BROOD, pulse=elapsed + seed + 2.0)


def _draw_fauna_entity(
    canvas: tk.Canvas,
    spec: _FaunaSpec,
    pos: Vec2,
    *,
    rig: LightRig,
    material,
    elapsed: float,
    to_screen,
    illustrated: bool = True,
) -> None:
    if spec.kind == "drift_ribbon":
        _draw_drift_ribbon(
            canvas, pos, rig=rig, material=material, seed=spec.seed,
            scale=spec.scale, elapsed=elapsed, to_screen=to_screen,
        )
        return

    mesh_kind = spec.kind if spec.kind != "chitin_puff" else "spore_jelly"
    local = mesh_for(mesh_kind, spec.seed, spec.scale)
    wobble = math.sin(elapsed * 1.4 + spec.seed) * 5.0
    screen_pts: list[tuple[float, float]] = []
    for v in local:
        sx, sy = to_screen(pos + Vec2(v.x + wobble * 0.15, v.y))
        screen_pts.append((sx, sy))
    if len(screen_pts) < 3:
        return

    sp, sy = to_screen(pos)
    draw_brood_ground_shadow(canvas, sp, sy + 40.0 * spec.scale, 16.0 * spec.scale, rig=rig)

    radius = 22.0 * spec.scale
    if illustrated and spec.kind in ("spore_jelly", "drift_pod", "veil_wisp", "chitin_puff"):
        draw_illustrated_polygon(
            canvas,
            screen_pts,
            rig=rig,
            material=material,
            seed=spec.seed,
            radius_hint=radius,
            crater_count=1 if spec.kind == "drift_pod" else 0,
            outline_width=2 if spec.kind == "veil_wisp" else 1,
        )
    else:
        draw_simplified_polygon(canvas, screen_pts, rig=rig, material=material, outline_width=1)

    if spec.kind in ("spore_jelly", "veil_wisp", "drift_pod"):
        draw_brood_rim_bloom(canvas, sp, sy, radius, material, flatten=0.32 if spec.kind == "veil_wisp" else 0.42)
        draw_ground_fog_glow(
            canvas, sp, sy, radius * 1.4, palette.CHASE_FOG_BROOD,
            pulse=elapsed * 2.1 + spec.seed,
        )


def draw_brood_fauna_tactical(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    hud_top: float,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
) -> None:
    drawn = 0
    elapsed = world.elapsed

    def to_screen(world_pos: Vec2) -> tuple[float, float]:
        p = camera.world_to_screen(world_pos, ship_pos, ship_angle)
        return p.x, p.y + hud_top

    for spec in _FAUNA_SPECS:
        if drawn >= FAUNA_DRAW_MAX:
            break
        if _wrap_near(ship_pos.x, SURFACE_WRAP_WIDTH * spec.frac_x) > _FAUNA_VIEW_MARGIN:
            continue
        pos = _fauna_world_pos(spec, elapsed)
        material = _material_for_fauna(spec.kind, rig)
        _draw_fauna_entity(
            canvas, spec, pos, rig=rig, material=material,
            elapsed=elapsed, to_screen=to_screen, illustrated=True,
        )
        drawn += 1


def draw_brood_fauna_chase(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
) -> None:
    drawn = 0
    elapsed = world.elapsed

    for spec in _FAUNA_SPECS:
        if drawn >= FAUNA_DRAW_MAX:
            break
        if _wrap_near(ship_pos.x, SURFACE_WRAP_WIDTH * spec.frac_x) > _FAUNA_VIEW_MARGIN:
            continue
        pos = _fauna_world_pos(spec, elapsed)
        base_mat = _material_for_fauna(spec.kind, rig)
        p = camera.world_to_chase_screen(pos, ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0)
        if p.depth < 6.0:
            continue
        fade = chase_depth_fade(p.depth)
        material = depth_faded_material(base_mat, fade)

        def to_screen(world_pos: Vec2) -> tuple[float, float]:
            pp = camera.world_to_chase_screen(
                world_pos, ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0,
            )
            return pp.x, pp.y

        _draw_fauna_entity(
            canvas, spec, pos, rig=rig, material=material,
            elapsed=elapsed, to_screen=to_screen,
            illustrated=fade < 0.55,
        )
        drawn += 1
