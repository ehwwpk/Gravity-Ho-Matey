from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import SpaceJunk
from gravity_ho_matey.gameplay.space_junk_prefabs import PREFAB_REGISTRY
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.lighting import LightRig, chase_depth_fade, depth_faded_material, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon

JUNK_VIEW_MARGIN = 96.0
CHASE_JUNK_FORWARD_REACH = 2600.0
CHASE_JUNK_LATERAL_REACH = 1200.0
CHASE_JUNK_BEHIND_REACH = 380.0


def junk_in_play_view(
    junk: SpaceJunk,
    ship_pos: Vec2,
    *,
    viewport_width: float,
    viewport_height: float,
    margin: float = JUNK_VIEW_MARGIN,
) -> bool:
    half_w = viewport_width * 0.58 + margin + junk.approximate_radius()
    half_h = viewport_height * 0.58 + margin + junk.approximate_radius()
    return abs(junk.pos.x - ship_pos.x) <= half_w and abs(junk.pos.y - ship_pos.y) <= half_h


def junk_in_chase_view(
    junk: SpaceJunk,
    ship_pos: Vec2,
    ship_angle: float,
) -> bool:
    rel = junk.pos - ship_pos
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    ahead = rel.dot(forward)
    lateral = abs(rel.dot(right))
    pad = junk.approximate_radius() + 28.0
    if ahead < -CHASE_JUNK_BEHIND_REACH - pad:
        return False
    if ahead > CHASE_JUNK_FORWARD_REACH + pad:
        return False
    return lateral <= CHASE_JUNK_LATERAL_REACH + pad


def _world_ring(junk: SpaceJunk, camera: ViewCamera, ship_pos: Vec2, ship_angle: float, hud_top: float) -> list[tuple[float, float]]:
    ring: list[tuple[float, float]] = []
    for v in junk.world_vertices():
        p = camera.world_to_screen(v, ship_pos, ship_angle)
        ring.append((p.x, p.y + hud_top))
    return ring


def _local_detail_lines(junk: SpaceJunk) -> tuple[tuple[Vec2, Vec2], ...]:
    prefab = PREFAB_REGISTRY.get(junk.prefab_id)
    if prefab is None:
        return ()
    return prefab.tactical_detail.rib_lines


def _local_rivets(junk: SpaceJunk) -> tuple[Vec2, ...]:
    prefab = PREFAB_REGISTRY.get(junk.prefab_id)
    if prefab is None:
        return ()
    return prefab.tactical_detail.rivet_points


def draw_tactical_junk(
    canvas: tk.Canvas,
    junk: SpaceJunk,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    hud_top: float,
    rig: LightRig,
    ship_angle: float,
    theme: str,
) -> None:
    ring = _world_ring(junk, camera, ship_pos, ship_angle, hud_top)
    if len(ring) < 3:
        return
    material = material_for("space_junk", theme=theme, view="tactical")
    draw_simplified_polygon(
        canvas,
        ring,
        rig=rig,
        material=material,
        outline_width=1,
    )
    c = math.cos(junk.angle)
    s = math.sin(junk.angle)
    for a, b in _local_detail_lines(junk):
        wa = Vec2(junk.pos.x + a.x * c - a.y * s, junk.pos.y + a.x * s + a.y * c)
        wb = Vec2(junk.pos.x + b.x * c - b.y * s, junk.pos.y + b.x * s + b.y * c)
        pa = camera.world_to_screen(wa, ship_pos, ship_angle)
        pb = camera.world_to_screen(wb, ship_pos, ship_angle)
        canvas.create_line(pa.x, pa.y + hud_top, pb.x, pb.y + hud_top, fill=palette.JUNK_RUST, width=1)
    for rv in _local_rivets(junk):
        w = Vec2(junk.pos.x + rv.x * c - rv.y * s, junk.pos.y + rv.x * s + rv.y * c)
        p = camera.world_to_screen(w, ship_pos, ship_angle)
        canvas.create_oval(p.x - 2, p.y + hud_top - 2, p.x + 2, p.y + hud_top + 2, fill=palette.JUNK_RIVET, outline="")


def draw_chase_junk(
    canvas: tk.Canvas,
    junk: SpaceJunk,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
    theme: str,
    elapsed: float,
) -> None:
    ring = _world_ring(junk, camera, ship_pos, ship_angle, 0.0)
    if len(ring) < 3:
        return
    prefab = PREFAB_REGISTRY.get(junk.prefab_id)
    depth_bias = prefab.chase_depth_bias if prefab is not None else -4.0
    rel = junk.pos - ship_pos
    forward = Vec2.from_angle(ship_angle)
    depth = rel.dot(forward) + depth_bias
    base = material_for("space_junk", theme=theme, view="chase")
    material = depth_faded_material(base, chase_depth_fade(depth))
    draw_illustrated_polygon(
        canvas,
        ring,
        rig=rig,
        material=material,
        seed=junk.instance_id,
        radius_hint=junk.approximate_radius(),
        crater_count=0,
    )
    c = math.cos(junk.angle)
    s = math.sin(junk.angle)
    for a, b in _local_detail_lines(junk):
        wa = Vec2(junk.pos.x + a.x * c - a.y * s, junk.pos.y + a.x * s + a.y * c)
        wb = Vec2(junk.pos.x + b.x * c - b.y * s, junk.pos.y + b.x * s + b.y * c)
        pa = camera.world_to_screen(wa, ship_pos, ship_angle)
        pb = camera.world_to_screen(wb, ship_pos, ship_angle)
        canvas.create_line(pa.x, pa.y, pb.x, pb.y, fill=palette.JUNK_RUST, width=1)


def draw_holo_junk_glyph(
    canvas: tk.Canvas,
    junk: SpaceJunk,
    *,
    map_x: float,
    map_y: float,
    map_scale: float,
) -> None:
    r = max(4.0, junk.approximate_radius() * map_scale * 0.22)
    canvas.create_rectangle(
        map_x - r,
        map_y - r * 0.72,
        map_x + r,
        map_y + r * 0.72,
        fill=palette.HOLO_JUNK_FILL,
        outline=palette.HOLO_JUNK_HATCH,
        width=1,
    )
    step = max(2.0, r * 0.35)
    y = map_y - r * 0.5
    while y <= map_y + r * 0.5:
        canvas.create_line(map_x - r * 0.8, y, map_x + r * 0.8, y, fill=palette.HOLO_JUNK_HATCH, width=1)
        y += step
