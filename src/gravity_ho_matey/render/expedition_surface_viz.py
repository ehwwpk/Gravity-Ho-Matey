from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.levels.comet_fuel_layout import LANDER_PAD
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import _lerp_color, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon


def _cell_seed(gx: int, gy: int) -> int:
    return (gx * 73856093) ^ (gy * 19349663) ^ 0xC0BEEF


def _visible_world_bounds(
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    *,
    margin: float = 120.0,
) -> tuple[float, float, float, float]:
    vw = float(camera.viewport_width)
    play_h = max(1.0, float(camera.viewport_height) - hud_top)
    scale = max(0.55, camera.tactical_scale)
    half_w = vw / scale / 2.0 + margin
    half_h = play_h / scale / 2.0 + margin
    return follow.x - half_w, follow.y - half_h, follow.x + half_w, follow.y + half_h


def _world_poly_to_screen(
    corners: tuple[tuple[float, float], ...],
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for wx, wy in corners:
        p = camera.world_to_screen(Vec2(wx, wy), follow, 0.0)
        out.append((p.x, p.y + hud_top))
    return out


def _world_cell_polygon(
    wx: float,
    wy: float,
    cell: float,
    seed: int,
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    overlap: float = 1.08,
) -> list[tuple[float, float]]:
    """Irregular regolith tile — slightly oversized so tiles overlap with no void."""
    bump = ((seed % 23) / 23.0 - 0.5) * cell * 0.12
    wobble = ((seed // 23) % 17) / 17.0 * cell * 0.07
    half = cell * 0.5 * overlap
    corners = (
        (wx - half + wobble, wy - half + bump),
        (wx + half * 0.94, wy - half * 0.86 - bump),
        (wx + half + wobble * 0.6, wy + half * 0.92),
        (wx - half * 0.96, wy + half + bump * 0.45),
    )
    return _world_poly_to_screen(corners, camera=camera, follow=follow, hud_top=hud_top)


def draw_comet_contact_ring(
    canvas: tk.Canvas,
    world_pos: Vec2,
    radius: float,
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    scale: float = 1.0,
) -> None:
    """Weight decal — elliptical contact patch under props and actors."""
    p = camera.world_to_screen(world_pos, follow, 0.0)
    sx, sy = p.x, p.y + hud_top
    r = radius * camera.tactical_scale * scale
    mat = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    dx = rig.key_dir.x * r * 0.22
    fill = lerp_hex(mat.deep, mat.shadow, 0.45)
    canvas.create_oval(
        sx - r * 1.25 + dx,
        sy + r * 0.05,
        sx + r * 1.25 + dx,
        sy + r * 0.38,
        fill=fill,
        outline=lerp_hex(mat.shadow, mat.mid, 0.35),
        width=1,
    )


def draw_expedition_tactical_backdrop(
    canvas: tk.Canvas,
    camera: ViewCamera,
    *,
    hud_top: float,
    follow: Vec2,
    rig: LightRig,
    elapsed: float,
    map_height: float = 1800.0,
    map_width: float = 2400.0,
    depot_center: Vec2 | None = None,
    depot_platform_radius: float = 340.0,
    lander_pad: Vec2 | None = None,
    lander_blast_radius: float = 200.0,
) -> None:
    """Comet foot crust — continuous regolith under the entire playfield, thin exosphere above."""
    vw = float(camera.viewport_width)
    vh = float(camera.viewport_height)
    play_h = max(1.0, vh - hud_top)
    xmin, ymin, xmax, ymax = _visible_world_bounds(camera, follow, hud_top)

    _draw_comet_exosphere(canvas, vw, hud_top, play_h, elapsed)
    _draw_solid_ground_slab(
        canvas,
        camera,
        follow,
        hud_top,
        xmin,
        ymin,
        xmax,
        ymax,
        rig=rig,
    )
    _draw_regolith_field(
        canvas,
        camera,
        follow,
        hud_top,
        xmin,
        ymin,
        xmax,
        ymax,
        rig=rig,
        map_width=map_width,
        map_height=map_height,
        depot_center=depot_center,
        depot_platform_radius=depot_platform_radius,
        lander_pad=lander_pad or LANDER_PAD,
        lander_blast_radius=lander_blast_radius,
    )
    _draw_lander_surface_zone(
        canvas,
        lander_pad or LANDER_PAD,
        lander_blast_radius,
        camera=camera,
        follow=follow,
        hud_top=hud_top,
        rig=rig,
        elapsed=elapsed,
    )
    if depot_center is not None:
        _draw_expedition_trail(
            canvas,
            lander_pad or LANDER_PAD,
            depot_center,
            camera=camera,
            follow=follow,
            hud_top=hud_top,
            rig=rig,
        )
        _draw_depot_surface_zone(
            canvas,
            depot_center,
            depot_platform_radius,
            camera=camera,
            follow=follow,
            hud_top=hud_top,
            rig=rig,
            elapsed=elapsed,
        )
    _draw_surface_haze_band(canvas, vw, hud_top, play_h, elapsed)


def _draw_comet_exosphere(
    canvas: tk.Canvas,
    vw: float,
    hud_top: float,
    play_h: float,
    elapsed: float,
) -> None:
    """Thin starfield + curved limb — you are on a small body, not open void."""
    canvas.create_rectangle(0, hud_top, vw, hud_top + play_h, fill=palette.COMET_SURFACE, outline="")
    sky_h = play_h * 0.22
    for band in range(5):
        t0 = band / 5.0
        y0 = hud_top + sky_h * t0
        y1 = hud_top + sky_h * (t0 + 1.0 / 5.0)
        fill = _lerp_color("#040810", _lerp_color(palette.COMET_BG, palette.COMET_SURFACE, 0.55), t0 * 0.85)
        canvas.create_rectangle(0, y0, vw, y1, fill=fill, outline="")
    horizon_y = hud_top + sky_h
    canvas.create_rectangle(0, horizon_y - 6, vw, horizon_y + 10, fill=_lerp_color(palette.COMET_SURFACE, palette.COMET_REGOLITH_MID, 0.35), outline="")
    limb_cy = horizon_y + play_h * 0.04
    canvas.create_arc(
        vw * 0.5 - vw * 1.35,
        limb_cy - vw * 0.55,
        vw * 0.5 + vw * 1.35,
        limb_cy + vw * 0.45,
        start=198,
        extent=144,
        style=tk.ARC,
        outline=lerp_hex(palette.COMET_VEIN, palette.COMET_SURFACE, 0.55),
        width=2,
    )
    canvas.create_arc(
        vw * 0.5 - vw * 1.28,
        limb_cy - vw * 0.48,
        vw * 0.5 + vw * 1.28,
        limb_cy + vw * 0.38,
        start=202,
        extent=136,
        style=tk.ARC,
        outline=lerp_hex(palette.COMET_REGOLITH_RIM, palette.COMET_SURFACE, 0.7),
        width=1,
    )
    for i in range(28):
        seed = i * 997 + 13
        sx = (seed * 173) % int(max(1.0, vw - 8)) + 4.0
        sy = hud_top + (seed * 89) % int(max(1.0, sky_h - 12)) + 4.0
        twinkle = 0.45 + 0.55 * math.sin(elapsed * 1.6 + i * 0.7)
        if twinkle < 0.55:
            continue
        r = 1.0 if i % 4 else 1.5
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=lerp_hex("#a8c8e8", "#ffffff", twinkle * 0.4), outline="")


def _draw_solid_ground_slab(
    canvas: tk.Canvas,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    *,
    rig: LightRig,
) -> None:
    """Continuous regolith fill — eliminates dark void between sparse tiles."""
    mat = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    base = _world_poly_to_screen(
        ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)),
        camera=camera,
        follow=follow,
        hud_top=hud_top,
    )
    flat = [c for pt in base for c in pt]
    canvas.create_polygon(*flat, fill=lerp_hex(mat.mid, mat.shadow, 0.28), outline="")
    canvas.create_polygon(*flat, fill="", outline=lerp_hex(mat.shadow, mat.deep, 0.4), width=0)


def _near_point(pos: Vec2, center: Vec2 | None, radius: float) -> bool:
    if center is None:
        return False
    return (pos - center).length_sq() <= radius * radius


def _draw_regolith_field(
    canvas: tk.Canvas,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    *,
    rig: LightRig,
    map_width: float,
    map_height: float,
    depot_center: Vec2 | None,
    depot_platform_radius: float,
    lander_pad: Vec2,
    lander_blast_radius: float,
) -> None:
    scale = max(0.55, camera.tactical_scale)
    cell = 92.0
    regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    ice = material_for("comet_ice", theme=rig.theme, view=rig.view)
    x0 = int(xmin / cell) - 1
    x1 = int(xmax / cell) + 2
    y0 = int(ymin / cell) - 1
    y1 = int(ymax / cell) + 2

    for gy in range(y0, y1):
        for gx in range(x0, x1):
            seed = _cell_seed(gx, gy)
            wx = gx * cell + cell * 0.5 + ((seed % 11) - 5) * 2.0
            wy = gy * cell + cell * 0.5 + ((seed // 11) % 11 - 5) * 2.0
            if wx < -20.0 or wy < -20.0 or wx > map_width + 20.0 or wy > map_height + 20.0:
                continue
            world_pos = Vec2(wx, wy)
            poly = _world_cell_polygon(wx, wy, cell, seed, camera=camera, follow=follow, hud_top=hud_top)
            priority = (
                _near_point(world_pos, depot_center, depot_platform_radius + 80.0)
                or _near_point(world_pos, lander_pad, lander_blast_radius + 60.0)
                or abs(wx - 1200.0) < 95.0
            )
            if priority or (gx + gy) % 2 == 0:
                draw_illustrated_polygon(
                    canvas,
                    poly,
                    rig=rig,
                    material=regolith,
                    seed=seed,
                    radius_hint=cell * scale * 0.42,
                    crater_count=2 if priority else 1,
                    outline_width=1,
                )
            else:
                draw_simplified_polygon(canvas, poly, rig=rig, material=regolith)
            if seed % 11 == 0:
                cx = sum(pt[0] for pt in poly) / len(poly)
                cy = sum(pt[1] for pt in poly) / len(poly)
                pr = 4.0 + (seed % 5)
                canvas.create_oval(cx - pr, cy - pr, cx + pr, cy + pr, fill=regolith.crater_pit, outline=regolith.shadow)
            if seed % 17 == 2:
                inner_cx = sum(pt[0] for pt in poly) / len(poly)
                inner_cy = sum(pt[1] for pt in poly) / len(poly)
                inner = [
                    (inner_cx + math.cos(i * 1.05) * 10.0, inner_cy + math.sin(i * 1.05) * 7.0)
                    for i in range(6)
                ]
                draw_illustrated_polygon(
                    canvas,
                    inner,
                    rig=rig,
                    material=ice,
                    seed=seed + 3,
                    radius_hint=12.0,
                    crater_count=0,
                )


def _draw_expedition_trail(
    canvas: tk.Canvas,
    lander: Vec2,
    depot: Vec2,
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
) -> None:
    """Worn boot path from lander pad upslope to the charter depot."""
    mat = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    direction = depot - lander
    length = direction.length()
    if length < 1.0:
        return
    norm = direction / length
    perp = Vec2(-norm.y, norm.x)
    steps = max(8, int(length / 85.0))
    for i in range(steps):
        t = (i + 0.5) / steps
        center = lander + direction * t
        width = 58.0 - abs(t - 0.5) * 18.0
        wobble = math.sin(i * 0.9) * 14.0
        c = center + perp * wobble
        half_l = 42.0
        corners = (
            (c.x - norm.x * half_l - perp.x * width, c.y - norm.y * half_l - perp.y * width),
            (c.x + norm.x * half_l - perp.x * width * 0.85, c.y + norm.y * half_l - perp.y * width * 0.85),
            (c.x + norm.x * half_l + perp.x * width * 0.85, c.y + norm.y * half_l + perp.y * width * 0.85),
            (c.x - norm.x * half_l + perp.x * width, c.y - norm.y * half_l + perp.y * width),
        )
        pts = _world_poly_to_screen(corners, camera=camera, follow=follow, hud_top=hud_top)
        draw_simplified_polygon(canvas, pts, rig=rig, material=mat)
        if i % 2 == 0:
            draw_illustrated_polygon(
                canvas,
                pts,
                rig=rig,
                material=mat,
                seed=500 + i,
                radius_hint=38.0 * camera.tactical_scale,
                crater_count=0,
                outline_width=0,
            )


def _draw_lander_surface_zone(
    canvas: tk.Canvas,
    center: Vec2,
    blast_radius: float,
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    """Landing blast disc — flattened regolith where the charter vessel touched down."""
    scale = camera.tactical_scale
    regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    slab = material_for("station_neutral", theme=rig.theme, view=rig.view)
    pulse = 0.5 + 0.5 * math.sin(elapsed * 1.9)

    ring_pts: list[tuple[float, float]] = []
    flat_pts: list[tuple[float, float]] = []
    for i in range(16):
        a = i / 16.0 * math.tau
        wobble = math.sin(a * 4.0 + elapsed * 0.25) * 10.0
        outer_wp = center + Vec2.from_angle(a) * (blast_radius + 36.0 + wobble)
        inner_wp = center + Vec2.from_angle(a) * (blast_radius * 0.78 + wobble * 0.4)
        outer_sp = camera.world_to_screen(outer_wp, follow, 0.0)
        inner_sp = camera.world_to_screen(inner_wp, follow, 0.0)
        ring_pts.append((outer_sp.x, outer_sp.y + hud_top))
        flat_pts.append((inner_sp.x, inner_sp.y + hud_top))
    draw_illustrated_polygon(
        canvas,
        ring_pts,
        rig=rig,
        material=regolith,
        seed=770,
        radius_hint=blast_radius * scale * 0.5,
        crater_count=2,
    )
    draw_simplified_polygon(canvas, flat_pts, rig=rig, material=slab)
    cp = camera.world_to_screen(center, follow, 0.0)
    cx, cy = cp.x, cp.y + hud_top
    pad_r = blast_radius * scale * 0.62
    canvas.create_oval(
        cx - pad_r * 1.1,
        cy - pad_r * 0.95,
        cx + pad_r * 1.1,
        cy + pad_r * 0.95,
        fill=lerp_hex(slab.mid, palette.COMET_SURFACE, 0.4),
        outline=palette.COMET_DEPOT_RIM,
        width=2,
    )
    canvas.create_oval(
        cx - pad_r * 0.72,
        cy - pad_r * 0.62,
        cx + pad_r * 0.72,
        cy + pad_r * 0.62,
        outline=palette.COMET_HUD_ACCENT if pulse > 0.5 else palette.COMET_VEIN,
        width=2,
        dash=(7, 5),
    )


def _draw_depot_surface_zone(
    canvas: tk.Canvas,
    center: Vec2,
    platform_radius: float,
    *,
    camera: ViewCamera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    """Blasted regolith apron and berm ring where the charter depot sits in the crust."""
    scale = camera.tactical_scale
    regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    slab = material_for("station_neutral", theme=rig.theme, view=rig.view)
    pulse = 0.5 + 0.5 * math.sin(elapsed * 1.6)

    berm_pts: list[tuple[float, float]] = []
    apron_pts: list[tuple[float, float]] = []
    trench_pts: list[tuple[float, float]] = []
    for i in range(16):
        a = i / 16.0 * math.tau
        wobble = math.sin(a * 5.0 + elapsed * 0.4) * 12.0
        radii = (
            platform_radius + 52.0 + wobble,
            platform_radius * 0.92 + wobble * 0.35,
            platform_radius * 0.55 + wobble * 0.2,
        )
        targets = (berm_pts, apron_pts, trench_pts)
        for radius, target in zip(radii, targets, strict=True):
            wp = center + Vec2.from_angle(a) * radius
            sp = camera.world_to_screen(wp, follow, 0.0)
            target.append((sp.x, sp.y + hud_top))
    draw_illustrated_polygon(
        canvas,
        berm_pts,
        rig=rig,
        material=regolith,
        seed=880,
        radius_hint=platform_radius * scale * 0.55,
        crater_count=3,
    )
    draw_simplified_polygon(canvas, apron_pts, rig=rig, material=slab)
    canvas.create_polygon(
        *[c for pt in trench_pts for c in pt],
        fill=lerp_hex(regolith.deep, palette.COMET_BG, 0.35),
        outline=lerp_hex(regolith.shadow, palette.COMET_VEIN, 0.4),
        width=1,
    )
    cp = camera.world_to_screen(center, follow, 0.0)
    cx, cy = cp.x, cp.y + hud_top
    pad_r = platform_radius * scale * 0.72
    canvas.create_oval(
        cx - pad_r,
        cy - pad_r * 0.82,
        cx + pad_r,
        cy + pad_r * 0.82,
        fill=lerp_hex(slab.deep, palette.COMET_BG, 0.5),
        outline=palette.COMET_DEPOT_RIM,
        width=2,
    )
    canvas.create_oval(
        cx - pad_r * 0.88,
        cy - pad_r * 0.72,
        cx + pad_r * 0.88,
        cy + pad_r * 0.72,
        outline=palette.COMET_HUD_ACCENT,
        width=1,
        dash=(8, 6),
    )
    for i in range(8):
        ang = i / 8.0 * math.tau + elapsed * 0.15
        lx = cx + math.cos(ang) * pad_r * 0.78
        ly = cy + math.sin(ang) * pad_r * 0.62
        canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=palette.COMET_VEIN if pulse > 0.45 else palette.COMET_HUD_ACCENT, outline="")


def _draw_surface_haze_band(
    canvas: tk.Canvas,
    vw: float,
    hud_top: float,
    play_h: float,
    elapsed: float,
) -> None:
    """Thin volatile skim at the surface limb — subtle, not a bottom letterbox."""
    band_top = hud_top + play_h * 0.9
    band_h = play_h * 0.1
    for i in range(3):
        t = i / 3.0
        y0 = band_top + band_h * t
        y1 = band_top + band_h * (t + 0.34)
        alpha = 0.04 + t * 0.06
        fill = _lerp_color(palette.COMET_SURFACE, palette.COMET_VEIN, alpha)
        canvas.create_rectangle(0, y0, vw, y1, fill=fill, outline="")
    pulse = 0.5 + 0.5 * math.sin(elapsed * 1.4)
    for i, frac in enumerate((0.2, 0.5, 0.8)):
        fx = vw * frac
        fy = hud_top + play_h * (0.93 + 0.02 * math.sin(elapsed * 0.8 + i))
        draw_ground_fog_glow(
            canvas,
            fx,
            fy,
            14.0 + pulse * 5.0,
            palette.CHASE_FOG_COMET,
            pulse=elapsed * 1.1 + i,
        )
