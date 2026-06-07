from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.egg_pod_objective import EggPodObjective
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.brood_viz_helpers import (
    draw_brood_membrane_ring,
    draw_brood_rim_bloom,
)
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, chase_depth_fade, depth_faded_material, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon


def _pod_material(*, alarm: bool, view: str, rig: LightRig) -> MaterialTones:
    base = material_for("brood_membrane", theme=rig.theme, view=view)
    if alarm:
        return MaterialTones(
            highlight=lerp_hex(base.highlight, palette.SQUID_CORE, 0.55),
            mid=lerp_hex(base.mid, palette.SQUID_BODY, 0.45),
            shadow=lerp_hex(base.shadow, "#4a2068", 0.35),
            deep=lerp_hex(base.deep, "#2a1040", 0.4),
            rim=lerp_hex(base.rim, palette.SQUID_TENTACLE, 0.5),
            crater_pit=base.crater_pit,
            crater_rim_hi=lerp_hex(base.crater_rim_hi, "#9858c8", 0.45),
        )
    if view == "chase":
        return MaterialTones(
            highlight=lerp_hex(base.highlight, "#9858c8", 0.25),
            mid=base.mid,
            shadow=base.shadow,
            deep=base.deep,
            rim=base.rim,
            crater_pit=base.crater_pit,
            crater_rim_hi=base.crater_rim_hi,
        )
    return base


def _pod_verts(r: float, pulse: float) -> list[tuple[float, float]]:
    wobble = 1.0 + pulse * 0.08
    rr = r * wobble
    local = [
        (-0.88, -0.32),
        (-0.58, -0.85),
        (0.12, -0.98),
        (0.82, -0.64),
        (0.96, 0.10),
        (0.52, 0.76),
        (-0.18, 0.92),
        (-0.85, 0.45),
    ]
    return [(lx * rr, ly * rr) for lx, ly in local]


def _draw_pod_tethers(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    r: float,
    material: MaterialTones,
    *,
    pulse: float,
) -> None:
    sway = math.sin(pulse * 1.8) * 4.0
    for i, ox in enumerate((-0.35, 0.0, 0.35)):
        x0 = sx + ox * r
        y0 = sy + r * 0.55
        x1 = sx + ox * r * 0.6 + sway * (i - 1)
        y1 = sy + r * 1.35 + math.sin(pulse + i) * 6.0
        canvas.create_line(x0, y0, x1, y1, fill=material.rim, width=2, smooth=True)
        canvas.create_line(x0, y0, x1, y1, fill=material.shadow, width=1, smooth=True)


def _draw_pod_core(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    r: float,
    material: MaterialTones,
    *,
    pulse: float,
) -> None:
    core_r = r * (0.28 + 0.04 * math.sin(pulse * 2.2))
    canvas.create_oval(
        sx - core_r,
        sy - core_r * 0.85,
        sx + core_r,
        sy + core_r * 0.85,
        fill=material.crater_rim_hi,
        outline=material.highlight,
        width=1,
    )
    draw_fog_glow(canvas, sx, sy, core_r * 2.2, palette.CHASE_FOG_BROOD, pulse=pulse)


def draw_egg_pods_tactical(
    canvas: tk.Canvas,
    pods: list[EggPodObjective],
    *,
    to_screen,
    rig: LightRig | None = None,
    elapsed: float = 0.0,
) -> None:
    rig = rig or LightRig.for_play(theme="brood_moon", view="tactical")
    chitin = material_for("brood_chitin", theme=rig.theme, view=rig.view)
    for pod in pods:
        if not pod.alive:
            continue
        sx, sy = to_screen(pod.pos)
        pulse = pod.pulse
        breathe = 0.5 + 0.5 * math.sin(pulse)
        r = pod.radius * (0.92 + breathe * 0.10)
        material = _pod_material(alarm=pod.alarm, view="tactical", rig=rig)

        draw_brood_rim_bloom(canvas, sx, sy + r * 0.15, r * 1.1, material, flatten=0.45)
        _draw_pod_tethers(canvas, sx, sy, r, chitin, pulse=pulse)
        draw_brood_membrane_ring(canvas, sx, sy, r * 1.08, material, pulse=pulse, rig=rig)

        verts = [(sx + lx, sy + ly) for lx, ly in _pod_verts(r, breathe)]
        draw_illustrated_polygon(
            canvas,
            verts,
            rig=rig,
            material=material,
            seed=pod.pod_id + 40,
            radius_hint=r,
            crater_count=2 if pod.hits_remaining < pod.hits_max else 3,
            outline_width=2,
        )
        _draw_pod_core(canvas, sx, sy - r * 0.08, r, material, pulse=pulse)

        if pod.alarm:
            draw_ground_fog_glow(canvas, sx, sy + r * 0.35, r * 2.8, palette.CHASE_FOG_BROOD, pulse=pulse)
            canvas.create_oval(
                sx - r * 1.25, sy - r * 1.15, sx + r * 1.25, sy + r * 1.15,
                outline=lerp_hex(palette.SQUID_CORE, palette.HUD_WARN, 0.35 + 0.25 * breathe),
                width=2,
            )
        if pod.hits_remaining < pod.hits_max:
            canvas.create_text(
                sx,
                sy - r - 12,
                text=f"{pod.hits_remaining}",
                fill=palette.HUD_WARN,
                font=("Courier New", 9, "bold"),
            )


def draw_egg_pod_chase(
    canvas: tk.Canvas,
    pod: EggPodObjective,
    *,
    pos: Vec2,
    scale: float,
    depth: float,
    rig: LightRig,
) -> None:
    pulse = pod.pulse
    breathe = 0.5 + 0.5 * math.sin(pulse)
    r = pod.radius * scale * (0.92 + breathe * 0.10)
    fade = chase_depth_fade(depth)
    material = depth_faded_material(_pod_material(alarm=pod.alarm, view="chase", rig=rig), fade)
    chitin = depth_faded_material(material_for("brood_chitin", theme=rig.theme, view=rig.view), fade)

    draw_brood_rim_bloom(canvas, pos.x, pos.y + r * 0.15, r * 1.1, material, flatten=0.45)
    _draw_pod_tethers(canvas, pos.x, pos.y, r, chitin, pulse=pulse)
    draw_brood_membrane_ring(canvas, pos.x, pos.y, r * 1.08, material, pulse=pulse, rig=rig)

    verts = [(pos.x + lx, pos.y + ly) for lx, ly in _pod_verts(r, breathe)]
    draw_illustrated_polygon(
        canvas,
        verts,
        rig=rig,
        material=material,
        seed=pod.pod_id + 40,
        radius_hint=r,
        crater_count=2,
        outline_width=2,
    )
    _draw_pod_core(canvas, pos.x, pos.y - r * 0.08, r, material, pulse=pulse)

    if pod.alarm:
        draw_ground_fog_glow(
            canvas,
            pos.x,
            pos.y + r * 0.35,
            r * 2.6,
            palette.CHASE_FOG_BROOD,
            pulse=pulse,
        )


def draw_egg_pod_map_glyph(
    canvas: tk.Canvas,
    mx: float,
    my: float,
    *,
    radius: float,
    alarm: bool,
    elapsed: float,
) -> None:
    pulse = 0.5 + 0.5 * math.sin(elapsed * 3.0 + mx * 0.01)
    r = radius * (0.90 + pulse * 0.10)
    rim = palette.SQUID_TENTACLE if alarm else palette.BROOD_CHITIN_RIM
    fill = lerp_hex(palette.SQUID_BODY if alarm else "#5a2868", palette.BROOD_REGOLITH_MID, 0.25)
    canvas.create_oval(mx - r * 1.05, my - r * 0.95, mx + r * 1.05, my + r * 0.95, fill=fill, outline=rim, width=2)
    canvas.create_oval(mx - r * 0.42, my - r * 0.48, mx + r * 0.42, my + r * 0.02, fill=palette.SQUID_CORE if alarm else palette.BROOD_FLORA_HIGHLIGHT, outline="")
    canvas.create_oval(mx - r * 1.2, my - r * 0.5, mx + r * 1.2, my + r * 0.55, outline=lerp_hex(rim, palette.BROOD_MOON_VEIN, 0.35), width=1)
