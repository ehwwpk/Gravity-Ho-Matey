from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for


def beacon_pulse(elapsed: float, *, seed: float = 0.0) -> tuple[float, float]:
    """Breathe + shimmer in 0..1 for layered beacon animation."""
    t = elapsed + seed
    breathe = 0.5 + 0.5 * math.sin(t * 3.6)
    shimmer = 0.5 + 0.5 * math.sin(t * 6.2 + 1.4)
    return breathe, shimmer


def draw_beacon_volumetric_glow(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    scale: float,
    elapsed: float,
    rig: LightRig,
    seed: float = 0.0,
) -> None:
    """Fog-stack halo — chase uses floor pool + sky pillar; tactical uses radial bloom."""
    breathe, shimmer = beacon_pulse(elapsed, seed=seed)
    base_r = 22.0 * scale * (1.0 + breathe * 0.16)
    pulse_t = elapsed * 3.4 + seed

    if rig.view == "chase":
        draw_ground_fog_glow(
            canvas,
            x,
            y + 4,
            base_r,
            palette.CHASE_FOG_BEACON,
            pulse=pulse_t,
        )
        pillar_y = y - base_r * (0.35 + shimmer * 0.22)
        draw_fog_glow(
            canvas,
            x,
            pillar_y,
            base_r * (0.72 + shimmer * 0.18),
            palette.CHASE_FOG_BEACON_PILLAR,
            pulse=pulse_t * 0.85,
        )
    else:
        draw_fog_glow(
            canvas,
            x,
            y,
            base_r * 1.05,
            palette.CHASE_FOG_BEACON[:4],
            pulse=pulse_t,
        )


def draw_beacon_pulse_rings(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    scale: float,
    elapsed: float,
    material_mid: str,
    material_hi: str,
    seed: float = 0.0,
) -> None:
    breathe, shimmer = beacon_pulse(elapsed, seed=seed)
    outer = 12.0 * scale * (1.0 + breathe * 0.28)
    inner = 8.5 * scale * (1.0 + shimmer * 0.14)
    canvas.create_oval(
        x - outer,
        y - outer,
        x + outer,
        y + outer,
        outline=lerp_hex(material_mid, material_hi, shimmer),
        width=2,
    )
    canvas.create_oval(
        x - inner,
        y - inner,
        x + inner,
        y + inner,
        outline=lerp_hex(material_hi, "#ffffff", breathe * 0.35),
        width=1,
    )


def draw_beacon_spark_orbits(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    scale: float,
    elapsed: float,
    color: str,
    seed: float = 0.0,
) -> None:
    orbit_r = 14.0 * scale
    spin = elapsed * 2.4 + seed
    for i in range(4):
        angle = spin + math.tau * i / 4.0
        sx = x + math.cos(angle) * orbit_r
        sy = y + math.sin(angle) * orbit_r * 0.82
        pr = 2.0 * scale
        canvas.create_oval(sx - pr, sy - pr, sx + pr, sy + pr, fill=color, outline="")


def draw_beacon_lit_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    collected: bool,
    scale: float,
    rig: LightRig,
    elapsed: float = 0.0,
    show_ring: bool = True,
    seed: float = 0.0,
) -> None:
    material = material_for("beacon", theme=rig.theme, view=rig.view)
    if collected:
        color = palette.BEACON_COLLECTED
        body = 6.0 * scale
        canvas.create_rectangle(x - body, y - body, x + body, y + body, fill=color, outline=material.shadow, width=1)
        return

    breathe, shimmer = beacon_pulse(elapsed, seed=seed)
    if show_ring:
        draw_beacon_pulse_rings(
            canvas,
            x,
            y,
            scale=scale,
            elapsed=elapsed,
            material_mid=material.mid,
            material_hi=material.highlight,
            seed=seed,
        )

    body = 6.0 * scale
    lit_x = x + rig.key_dir.x * body * 0.35
    lit_y = y + rig.key_dir.y * body * 0.35
    canvas.create_rectangle(
        x - body,
        y - body,
        x + body,
        y + body,
        fill=material.shadow,
        outline=material.rim,
        width=1,
    )
    canvas.create_polygon(
        x,
        y - 10 * scale,
        x + 5 * scale,
        y - 4 * scale,
        x,
        y + 2 * scale,
        x - 5 * scale,
        y - 4 * scale,
        fill=lerp_hex(material.mid, material.highlight, 0.35 + shimmer * 0.45),
        outline="",
    )
    spark = 3.0 * scale * (0.85 + breathe * 0.25)
    canvas.create_oval(
        lit_x - spark,
        lit_y - spark,
        lit_x + spark,
        lit_y + spark,
        fill=lerp_hex(material.highlight, "#ffffff", shimmer * 0.4),
        outline="",
    )


def draw_beacon_play(
    canvas: tk.Canvas,
    x: float,
    y: float,
    beacon: Beacon,
    *,
    scale: float,
    rig: LightRig,
    elapsed: float,
    seed: float = 0.0,
    spark_orbits: bool = False,
) -> None:
    if not beacon.collected:
        if rig.view != "chase":
            draw_beacon_volumetric_glow(canvas, x, y, scale=scale, elapsed=elapsed, rig=rig, seed=seed)
        if spark_orbits:
            material = material_for("beacon", theme=rig.theme, view=rig.view)
            draw_beacon_spark_orbits(
                canvas,
                x,
                y,
                scale=scale,
                elapsed=elapsed,
                color=material.highlight,
                seed=seed,
            )
    draw_beacon_lit_glyph(
        canvas,
        x,
        y,
        collected=beacon.collected,
        scale=scale,
        rig=rig,
        elapsed=elapsed,
        show_ring=True,
        seed=seed,
    )


def beacon_seed_from_pos(pos: Vec2) -> float:
    return (pos.x * 0.017 + pos.y * 0.013) % math.tau
