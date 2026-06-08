"""Tactical-map ingress glyphs — visible in OG view when threats spawn off-screen or at distance."""

from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.wave_ingress import WaveIngressMarker, wave_ingress_markers_for_world
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera


def draw_wave_ingress_tactical(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    hud_top: float,
    elapsed: float,
) -> None:
    """Lane chevrons on the chart — primary cue in tactical (OG) mode."""
    markers = wave_ingress_markers_for_world(world)
    if not markers:
        return
    ship_pos = world.ship.pos
    ship_angle = world.ship.angle
    pulse = 0.55 + 0.45 * math.sin(elapsed * 4.2)
    accent = palette.RIFT_HUD_ACCENT
    warn = palette.HUD_WARN if pulse > 0.75 else palette.ENEMY_EDGE

    for marker in markers:
        p = camera.world_to_screen(marker.pos, ship_pos, ship_angle)
        sx, sy = p.x, p.y + hud_top
        toward = marker.toward or ship_pos
        tp = camera.world_to_screen(toward, ship_pos, ship_angle)
        angle = math.atan2(tp.y - p.y, tp.x - p.x)
        _draw_lane_glyph(canvas, sx, sy, angle, marker.tag, accent, warn, pulse=pulse)


def draw_wave_ingress_edge_hints(
    hints: list[tuple[float, str, str]],
    camera: ViewCamera,
    world: GameWorld,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    vw: float,
    vh: float,
    play_top: float,
) -> None:
    """Append rim chevrons for off-screen ingress lanes (chase + tactical)."""
    from gravity_ho_matey.render.edge_hints import _maybe_hint

    accent = palette.RIFT_HUD_ACCENT
    for marker in wave_ingress_markers_for_world(world):
        _maybe_hint(
            hints,
            camera,
            marker.pos,
            ship_pos,
            ship_angle,
            marker.tag,
            accent,
            vw,
            vh,
            play_top,
        )


def _draw_lane_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    angle: float,
    tag: str,
    accent: str,
    warn: str,
    *,
    pulse: float,
) -> None:
    ring = 14.0 + 3.0 * pulse
    canvas.create_oval(x - ring, y - ring, x + ring, y + ring, outline=accent, width=1, dash=(4, 3))
    tip_len = 11.0 + 2.0 * pulse
    wing = 7.0
    tip = Vec2(x, y) + Vec2.from_angle(angle) * tip_len
    left = Vec2(x, y) + Vec2.from_angle(angle + 2.55) * wing
    right = Vec2(x, y) + Vec2.from_angle(angle - 2.55) * wing
    canvas.create_polygon(tip.x, tip.y, left.x, left.y, right.x, right.y, fill=warn, outline="")
    canvas.create_text(x, y - 16.0, text=tag, fill=accent, font=("Courier New", 9, "bold"))
