from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.boost_lane import LaneState
from gravity_ho_matey.gameplay.boost_pad import BoostPad
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_pod import PodPhase, SquidPod
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.membrane_layout import MembraneLayout
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.health_bar_viz import draw_health_bar
from gravity_ho_matey.render.lighting import (
    LightRig,
    chase_depth_fade,
    depth_faded_material,
    lerp_hex,
    material_for,
)
from gravity_ho_matey.render.squid_viz import draw_squid_body

_CHASE_GLOW_CAP = 280.0
_CHASE_RIBBON_DECIMATE = 10
_CHASE_MAX_HALF_PX = 78.0
_CHASE_MAX_AHEAD = 820.0
_TACTICAL_RIBBON_DECIMATE = 4


def _chase_ahead(camera: ViewCamera, depth: float) -> float:
    return max(depth, camera.min_depth)


def _chase_project_scale(camera: ViewCamera, depth: float) -> float:
    """World units → screen pixels (matches chase camera lateral projection)."""
    return camera.perspective_scale(_chase_ahead(camera, depth)) * camera.chase_thrust_boost


def _chase_entity_scale(camera: ViewCamera, depth: float) -> float:
    """Normalized entity scale — same formula as view_renderers chase sprites."""
    return max(0.35, camera.perspective_scale(_chase_ahead(camera, depth)) / camera.focal_length)


def _chase_world_px(camera: ViewCamera, world_units: float, depth: float) -> float:
    return world_units * _chase_project_scale(camera, depth)


def _clamp_glow(radius: float, *, cap: float = _CHASE_GLOW_CAP) -> float:
    return min(max(0.0, radius), cap)


def boss_scrape_radius(boss: MegaSquidBoss, ship_radius: float) -> float:
    return boss.radius + ship_radius


def _perp(tangent: Vec2) -> Vec2:
    t = tangent.normalized()
    return t.rotated(math.pi / 2.0)


def _flatten_poly(left: list[float], right: list[float]) -> list[float]:
    poly: list[float] = list(left)
    for i in range(len(right) - 2, -1, -2):
        poly.extend((right[i], right[i + 1]))
    return poly


def _ribbon_y_scale(*, tactical: bool) -> float:
    return 0.34 if tactical else 0.3


def _ribbon_seed(ribbon_id: str) -> int:
    return sum(ord(c) * (i + 3) for i, c in enumerate(ribbon_id)) & 0xFFFF


def _ribbon_edges(
    center_pts: list[tuple[float, float]],
    normals: list[tuple[float, float]],
    half_widths: list[float],
    *,
    y_scale: float,
) -> tuple[list[float], list[float]]:
    left_edge: list[float] = []
    right_edge: list[float] = []
    for (x, y), (nx, ny), hw in zip(center_pts, normals, half_widths, strict=True):
        left_edge.extend((x + nx * hw, y + ny * hw * y_scale))
        right_edge.extend((x - nx * hw, y - ny * hw * y_scale))
    return left_edge, right_edge


def _draw_ribbon_shadow_segments(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    half_widths: list[float],
    *,
    material,
    y_scale: float,
    tactical: bool,
    step: int = 8,
) -> None:
    tone = material.deep if tactical else palette.CHASE_ASTEROID_SHADOW
    for i, ((x, y), hw) in enumerate(zip(center_pts, half_widths, strict=True)):
        if i % step != 0 and i != len(center_pts) - 1:
            continue
        rx = max(6.0, hw * 0.72)
        ry = max(2.0, hw * y_scale * 0.32)
        canvas.create_oval(x - rx, y + ry * 0.35, x + rx, y + ry * 1.35, fill=tone, outline="")


def _draw_road_regolith(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    normals: list[tuple[float, float]],
    half_widths: list[float],
    *,
    rig: LightRig,
    material,
    seed_base: int,
    y_scale: float,
    step: int = 5,
) -> None:
    for i, ((x, y), (nx, ny), hw) in enumerate(zip(center_pts, normals, half_widths, strict=True)):
        if i % step != 0:
            continue
        pit_seed = seed_base + i * 17
        jitter_x = ((pit_seed % 7) - 3) * hw * 0.045
        jitter_y = ((pit_seed % 5) - 2) * hw * 0.04
        px = x + nx * jitter_x
        py = y + ny * jitter_y * y_scale
        pr = max(1.2, hw * 0.032 + (pit_seed % 4))
        canvas.create_oval(px - pr, py - pr * 0.82, px + pr, py + pr * 0.82, fill=material.crater_pit, outline="")
        hx = px + rig.key_dir.x * pr * 0.38
        hy = py + rig.key_dir.y * pr * 0.32
        canvas.create_oval(
            hx - pr * 0.32,
            hy - pr * 0.26,
            hx + pr * 0.32,
            hy + pr * 0.26,
            fill=material.crater_rim_hi,
            outline="",
        )


def _draw_lane_dashes(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    normals: list[tuple[float, float]],
    half_widths: list[float],
    *,
    lane_blend: float,
    material,
    y_scale: float,
    step: int = 2,
) -> None:
    if lane_blend < 0.06:
        return
    dash_tone = lerp_hex(material.highlight, "#ffffff", 0.32 * lane_blend)
    width = max(1, int(2 + lane_blend))
    for i, ((x, y), (nx, ny), hw) in enumerate(zip(center_pts, normals, half_widths, strict=True)):
        if i % step != 0:
            continue
        tx, ty = -ny, nx
        half = max(2.5, hw * 0.11)
        canvas.create_line(
            x - tx * half,
            y - ty * half * y_scale,
            x + tx * half,
            y + ty * half * y_scale,
            fill=dash_tone,
            width=width,
        )


def _draw_chevron_kerbs(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    normals: list[tuple[float, float]],
    half_widths: list[float],
    *,
    kerb_a: str,
    kerb_b: str,
    y_scale: float,
    step: int = 3,
) -> None:
    tick = max(5.0, sum(half_widths) / max(1, len(half_widths)) * 0.18)
    for i, ((x, y), (nx, ny), hw) in enumerate(zip(center_pts, normals, half_widths, strict=True)):
        if i % step != 0:
            continue
        if i < len(center_pts) - 1:
            tx = center_pts[i + 1][0] - x
            ty = center_pts[i + 1][1] - y
        else:
            tx = x - center_pts[i - 1][0]
            ty = y - center_pts[i - 1][1]
        t_len = math.hypot(tx, ty)
        if t_len < 1e-6:
            tx, ty = -ny, nx
            t_len = 1.0
        tx, ty = tx / t_len, ty / t_len
        color = kerb_a if (i // step) % 2 == 0 else kerb_b
        for side in (1.0, -1.0):
            ox = x + nx * hw * side * 1.04
            oy = y + ny * hw * side * y_scale * 1.04
            tip_x = ox + tx * tick * 0.55
            tip_y = oy + ty * tick * 0.55
            back_x = ox - tx * tick * 0.35
            back_y = oy - ty * tick * 0.35
            left_x = back_x + nx * side * tick * 0.42
            left_y = back_y + ny * side * tick * 0.42 * y_scale
            right_x = back_x - nx * side * tick * 0.42
            right_y = back_y - ny * side * tick * 0.42 * y_scale
            canvas.create_polygon(
                tip_x,
                tip_y,
                left_x,
                left_y,
                right_x,
                right_y,
                fill=color,
                outline=lerp_hex(color, "#000000", 0.25),
                width=1,
            )


def _draw_road_surface(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    half_widths: list[float],
    *,
    rig: LightRig,
    material,
    elapsed: float,
    lane_blend: float,
    y_scale: float,
    ribbon_seed: int,
    tactical: bool,
    depths: list[float] | None = None,
) -> None:
    if len(center_pts) < 2:
        return
    if depths and not tactical:
        avg_depth = sum(depths) / len(depths)
        material = depth_faded_material(material, chase_depth_fade(avg_depth))
    pulse = 0.96 + 0.04 * math.sin(elapsed * 0.9)
    normals = _ribbon_normals(center_pts)
    left_edge, right_edge = _ribbon_edges(center_pts, normals, half_widths, y_scale=y_scale)
    _draw_ribbon_shadow_segments(
        canvas,
        center_pts,
        half_widths,
        material=material,
        y_scale=y_scale,
        tactical=tactical,
    )
    bed_shadow = lerp_hex(material.deep, material.shadow, 0.38)
    bed_mid = lerp_hex(material.shadow, material.mid, 0.5 * pulse)
    bed_hi = lerp_hex(material.mid, material.highlight, 0.24 + lane_blend * 0.28)
    edge_tone = lerp_hex(material.rim, material.highlight, 0.3 * lane_blend)
    canvas.create_polygon(*_flatten_poly(left_edge, right_edge), fill=bed_shadow, outline=edge_tone, width=1)
    kx, ky = rig.key_dir.x, rig.key_dir.y
    lit_left: list[float] = []
    lit_right: list[float] = []
    for (x, y), (nx, ny), hw in zip(center_pts, normals, half_widths, strict=True):
        lit_shift = (nx * kx + ny * ky) * hw * 0.16
        lit_left.extend(
            (
                x + nx * hw * 0.58 + lit_shift,
                y + (ny * hw * 0.58 + lit_shift) * y_scale,
            )
        )
        lit_right.extend((x - nx * hw * 0.1, y - ny * hw * 0.1 * y_scale))
    if len(lit_left) >= 4:
        canvas.create_polygon(*_flatten_poly(lit_left, lit_right), fill=bed_mid, outline="")
    canvas.create_line(*left_edge, fill=bed_hi, width=2, smooth=True)
    canvas.create_line(*right_edge, fill=lerp_hex(bed_hi, edge_tone, 0.42), width=1, smooth=True)
    _draw_road_regolith(
        canvas,
        center_pts,
        normals,
        half_widths,
        rig=rig,
        material=material,
        seed_base=ribbon_seed,
        y_scale=y_scale,
    )
    _draw_lane_dashes(
        canvas,
        center_pts,
        normals,
        half_widths,
        lane_blend=lane_blend,
        material=material,
        y_scale=y_scale,
    )
    _draw_chevron_kerbs(
        canvas,
        center_pts,
        normals,
        half_widths,
        kerb_a=palette.RIFT_KERB_A,
        kerb_b=palette.RIFT_KERB_B,
        y_scale=y_scale,
    )
    if not tactical and lane_blend > 0.3:
        cx = sum(p[0] for p in center_pts) / len(center_pts)
        cy = sum(p[1] for p in center_pts) / len(center_pts)
        avg_hw = sum(half_widths) / len(half_widths)
        draw_ground_fog_glow(
            canvas,
            cx,
            cy + 4,
            min(avg_hw * 1.15, 118.0),
            palette.CHASE_FOG_RIBBON,
            pulse=elapsed * 1.6,
        )


def _project_ribbon_points(
    chain: tuple,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_y: float = 0.0,
    horizon: float | None = None,
    max_ahead: float | None = None,
    half_width_fn,
) -> tuple[list[tuple[float, float]], list[float], list[float]]:
    center_pts: list[tuple[float, float]] = []
    half_widths: list[float] = []
    depths: list[float] = []
    for sample in chain:
        sp = camera.world_to_screen(sample.pos, ship_pos, ship_angle)
        if horizon is not None and sp.y < horizon - 20:
            continue
        ahead = _chase_ahead(camera, sp.depth)
        if max_ahead is not None and ahead > max_ahead:
            continue
        center_pts.append((sp.x, sp.y + hud_y))
        half_widths.append(half_width_fn(sample, ahead))
        depths.append(ahead)
    return center_pts, half_widths, depths


def _draw_lit_ribbon_tactical(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    half_widths: list[float],
    *,
    rig: LightRig,
    material,
    elapsed: float,
    ribbon_seed: int,
) -> None:
    _draw_road_surface(
        canvas,
        center_pts,
        half_widths,
        rig=rig,
        material=material,
        elapsed=elapsed,
        lane_blend=1.0,
        y_scale=_ribbon_y_scale(tactical=True),
        ribbon_seed=ribbon_seed,
        tactical=True,
    )


def _draw_lit_ribbon_chase(
    canvas: tk.Canvas,
    center_pts: list[tuple[float, float]],
    half_widths: list[float],
    *,
    lane_blend: float,
    rig: LightRig,
    material,
    elapsed: float,
    ribbon_seed: int,
    depths: list[float] | None = None,
) -> None:
    _draw_road_surface(
        canvas,
        center_pts,
        half_widths,
        rig=rig,
        material=material,
        elapsed=elapsed,
        lane_blend=lane_blend,
        y_scale=_ribbon_y_scale(tactical=False),
        ribbon_seed=ribbon_seed,
        tactical=False,
        depths=depths,
    )


def draw_boss_stable_zone_tactical(
    canvas: tk.Canvas,
    layout: MembraneLayout,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    elapsed: float,
) -> None:
    p = camera.world_to_screen(layout.boss_anchor, ship_pos, ship_angle)
    sx, sy = p.x, p.y + hud_top
    r = layout.boss_stable_radius * camera.tactical_scale * 0.38
    pulse = 0.94 + 0.06 * math.sin(elapsed * 2.6)
    draw_ground_fog_glow(
        canvas,
        sx,
        sy,
        r * 1.05,
        palette.CHASE_FOG_STABLE,
        pulse=elapsed * 1.8,
    )
    canvas.create_oval(
        sx - r * pulse,
        sy - r * pulse * 0.82,
        sx + r * pulse,
        sy + r * pulse * 0.82,
        fill="",
        outline=palette.RIFT_STABLE_RING,
        width=2,
        dash=(10, 14),
    )
    draw_fog_glow(
        canvas,
        sx,
        sy,
        r * 0.68,
        (palette.RIFT_STABLE_FILL, palette.RIFT_STABLE_FILL, palette.RIFT_STABLE_RING),
        pulse=elapsed * 1.4,
    )


def draw_boss_stable_zone_chase(
    canvas: tk.Canvas,
    layout: MembraneLayout,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
) -> None:
    sp = camera.world_to_screen(layout.boss_anchor, ship_pos, ship_angle)
    ahead = _chase_ahead(camera, sp.depth)
    r = _clamp_glow(_chase_world_px(camera, layout.boss_stable_radius * 0.42, ahead))
    pulse = 0.92 + 0.08 * math.sin(elapsed * 3.0)
    draw_ground_fog_glow(
        canvas,
        sp.x,
        sp.y + 8,
        _clamp_glow(r * 0.95, cap=240.0),
        palette.CHASE_FOG_STABLE,
        pulse=elapsed * 2.2,
    )
    canvas.create_oval(
        sp.x - r * pulse,
        sp.y - r * pulse * 0.75,
        sp.x + r * pulse,
        sp.y + r * pulse * 0.75,
        outline=palette.RIFT_STABLE_RING,
        width=2,
        dash=(8, 12),
    )


def _decimate_chain(chain: list, *, step: int) -> list:
    if len(chain) <= 2:
        return chain
    out = [chain[0]]
    for i in range(step, len(chain) - 1, step):
        out.append(chain[i])
    if out[-1] is not chain[-1]:
        out.append(chain[-1])
    return out


def _chase_half_width_px(camera: ViewCamera, world_half: float, ahead: float) -> float:
    return min(_CHASE_MAX_HALF_PX, world_half * _chase_project_scale(camera, ahead))


def _pad_mk_tint(elapsed: float, *, ready: bool, flashing: bool) -> tuple[str, str, str]:
    if flashing:
        return palette.RIFT_PAD_FLASH, palette.RIFT_PAD_ZIGZAG, palette.RIFT_PAD_FLASH
    if not ready:
        return palette.RIFT_PAD_COOLDOWN, palette.RIFT_PAD_COOLDOWN, "#4a5868"
    cycle = int(elapsed * 1.8) % 4
    fills = (
        palette.RIFT_PAD_MK_RED,
        palette.RIFT_PAD_MK_PINK,
        palette.RIFT_PAD_MK_YELLOW,
        palette.RIFT_PAD_MK_ORANGE,
    )
    fill = fills[cycle]
    return fill, lerp_hex(fill, "#ffffff", 0.22), lerp_hex(fill, "#3a4858", 0.42)


def _draw_pad_zigzag(
    canvas: tk.Canvas,
    corners: tuple[Vec2, Vec2, Vec2, Vec2],
    tangent: Vec2,
    *,
    color: str,
    rows: int = 4,
) -> None:
    t = tangent.normalized()
    n = _perp(t)
    back = (corners[0] + corners[1]) * 0.5
    front = (corners[2] + corners[3]) * 0.5
    for row in range(rows):
        frac = (row + 0.5) / rows
        center = back + (front - back) * frac
        span = (corners[0] - corners[1]).length() * 0.42 * (1.0 - frac * 0.12)
        zig = span * 0.55
        a = center + n * span
        b = center - n * span
        c = center + n * span * 0.35 + t * zig
        d = center - n * span * 0.35 + t * zig
        canvas.create_line(a.x, a.y, c.x, c.y, fill=color, width=2)
        canvas.create_line(c.x, c.y, b.x, b.y, fill=color, width=2)
        canvas.create_line(b.x, b.y, d.x, d.y, fill=color, width=2)


def _draw_pad_gate_posts(
    canvas: tk.Canvas,
    corners: tuple[Vec2, Vec2, Vec2, Vec2],
    *,
    fill: str,
    rim: str,
    ready: bool,
) -> None:
    if not ready:
        return
    for idx in (0, 1):
        base = corners[idx]
        post_h = (corners[2] - base).length() * 0.08
        top = base + Vec2(0.0, -post_h)
        w = 3.0
        canvas.create_rectangle(base.x - w, top.y, base.x + w, base.y + 2, fill=fill, outline=rim, width=1)


def _ribbon_normals(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    normals: list[tuple[float, float]] = []
    for i in range(len(points)):
        if i < len(points) - 1:
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
        else:
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length < 1e-6:
            normals.append((0.0, 1.0))
        else:
            normals.append((-dy / length, dx / length))
    return normals


def _draw_pad_chevron(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    tangent: Vec2,
    size: float,
    *,
    fill: str,
    outline: str,
) -> None:
    t = tangent.normalized()
    n = t.rotated(math.pi / 2.0)
    tip = Vec2(sx, sy) + t * size
    left = Vec2(sx, sy) - t * size * 0.35 + n * size * 0.55
    right = Vec2(sx, sy) - t * size * 0.35 - n * size * 0.55
    canvas.create_polygon(tip.x, tip.y, left.x, left.y, right.x, right.y, fill=fill, outline=outline, width=1)


def _draw_mk_boost_strip(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    tangent: Vec2,
    span: float,
    *,
    ready: bool,
    flashing: bool,
    elapsed: float,
    tactical: bool,
    rig: LightRig,
) -> None:
    """Mario Kart-style boost gate — lit bed, zig-zag stripes, cycling warm tints."""
    _ = rig
    t = tangent.normalized()
    n = _perp(t)
    length = span * (1.12 if ready else 0.9)
    half_w = span * 0.44
    back = Vec2(sx, sy) - t * length * 0.44
    front = Vec2(sx, sy) + t * length * 0.56
    pulse = 0.92 + 0.08 * math.sin(elapsed * 3.2)
    corners = (
        back + n * half_w,
        back - n * half_w,
        front - n * half_w * 0.86,
        front + n * half_w * 0.86,
    )
    if ready or flashing:
        glow_r = half_w * (1.18 if flashing else 0.98) * pulse
        draw_ground_fog_glow(
            canvas,
            sx,
            sy + 2,
            min(glow_r, 58.0 if tactical else 48.0),
            palette.RIFT_PAD_GLOW if ready else palette.CHASE_FOG_PAD,
            pulse=elapsed * 2.8,
        )
        canvas.create_oval(
            sx - half_w * 0.35,
            sy + half_w * 0.12,
            sx + half_w * 0.35,
            sy + half_w * 0.42,
            fill=palette.CHASE_ASTEROID_SHADOW if not tactical else material_for("boost_pad", theme=rig.theme).deep,
            outline="",
        )
    fill, stripe, rim = _pad_mk_tint(elapsed, ready=ready, flashing=flashing)
    shadow_fill = lerp_hex(fill, "#101820", 0.55 if ready else 0.35)
    canvas.create_polygon(
        *(coord for pt in corners for coord in (pt.x, pt.y)),
        fill=shadow_fill,
        outline="",
    )
    inset = 0.88 if ready else 0.94
    inset_corners = tuple(
        Vec2(sx, sy) + (pt - Vec2(sx, sy)) * inset for pt in corners
    )
    canvas.create_polygon(
        *(coord for pt in inset_corners for coord in (pt.x, pt.y)),
        fill=fill,
        outline=rim,
        width=2 if ready or flashing else 1,
    )
    if ready or flashing:
        _draw_pad_zigzag(canvas, corners, tangent, color=stripe, rows=5 if tactical else 4)
        _draw_pad_gate_posts(canvas, corners, fill=rim, rim=stripe, ready=ready)
        chev_span = half_w * 0.18
        for frac in (-0.22, 0.08, 0.34):
            cx = sx + t.x * length * frac
            cy = sy + t.y * length * frac
            _draw_pad_chevron(
                canvas,
                cx,
                cy,
                tangent,
                chev_span,
                fill=lerp_hex(stripe, "#ffffff", 0.35),
                outline="",
            )


def draw_membrane_ribbons_tactical(
    canvas: tk.Canvas,
    layout: MembraneLayout,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    material = material_for("rift_ribbon", theme=rig.theme, view=rig.view)
    for ribbon_id, chain in layout.ribbon_chains:
        decimated = _decimate_chain(list(chain), step=_TACTICAL_RIBBON_DECIMATE)
        if len(decimated) < 2:
            continue
        center_pts: list[tuple[float, float]] = []
        half_widths: list[float] = []
        hw_world = decimated[0].half_width * camera.tactical_scale * 0.4
        for sample in decimated:
            p = camera.world_to_screen(sample.pos, ship_pos, ship_angle)
            center_pts.append((p.x, p.y + hud_top))
            half_widths.append(hw_world)
        _draw_lit_ribbon_tactical(
            canvas,
            center_pts,
            half_widths,
            rig=rig,
            material=material,
            elapsed=elapsed,
            ribbon_seed=_ribbon_seed(ribbon_id),
        )


def draw_boost_pads_tactical(
    canvas: tk.Canvas,
    pads: list[BoostPad],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    for pad in pads:
        p = camera.world_to_screen(pad.pos, ship_pos, ship_angle)
        sx, sy = p.x, p.y + hud_top
        span = max(14.0, pad.radius * camera.tactical_scale * 0.58)
        _draw_mk_boost_strip(
            canvas,
            sx,
            sy,
            pad.tangent,
            span,
            ready=pad.cooldown <= 0.0,
            flashing=pad.pad_flash > 0.0,
            elapsed=elapsed,
            tactical=True,
            rig=rig,
        )


def draw_boost_pads_chase(
    canvas: tk.Canvas,
    pads: list[BoostPad],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
    rig: LightRig,
) -> None:
    horizon = camera.chase_horizon_y()
    for pad in pads:
        sp = camera.world_to_screen(pad.pos, ship_pos, ship_angle)
        if sp.y < horizon:
            continue
        ahead = _chase_ahead(camera, sp.depth)
        span = min(64.0, max(8.0, _chase_world_px(camera, pad.radius, ahead) * 0.85))
        _draw_mk_boost_strip(
            canvas,
            sp.x,
            sp.y,
            pad.tangent,
            span,
            ready=pad.cooldown <= 0.0,
            flashing=pad.pad_flash > 0.0,
            elapsed=elapsed,
            tactical=False,
            rig=rig,
        )


def _lane_blend(world: GameWorld) -> float:
    if world.lane_probe is None:
        return 0.0
    if world.lane_probe.state is LaneState.ON_RIBBON:
        return 1.0
    if world.lane_probe.state is LaneState.RUNOFF:
        return 0.45
    return 0.0


def draw_membrane_ribbons_chase(
    canvas: tk.Canvas,
    layout: MembraneLayout,
    camera: ViewCamera,
    world: GameWorld,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
    rig: LightRig,
) -> None:
    _ = elapsed
    lane_blend = _lane_blend(world)
    material = material_for("rift_ribbon", theme=rig.theme, view="chase")
    horizon = camera.chase_horizon_y()

    def half_w(sample, ahead: float) -> float:
        return _chase_half_width_px(camera, sample.half_width, ahead)

    for ribbon_id, chain in layout.ribbon_chains:
        decimated = _decimate_chain(list(chain), step=_CHASE_RIBBON_DECIMATE)
        center_pts, half_widths, depths = _project_ribbon_points(
            tuple(decimated),
            camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            horizon=horizon,
            max_ahead=_CHASE_MAX_AHEAD,
            half_width_fn=half_w,
        )
        _draw_lit_ribbon_chase(
            canvas,
            center_pts,
            half_widths,
            lane_blend=lane_blend,
            rig=rig,
            material=material,
            elapsed=world.elapsed,
            ribbon_seed=_ribbon_seed(ribbon_id),
            depths=depths,
        )


def draw_boss_scrape_zone(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    scrape_r: float,
    *,
    ship_inside: bool,
    flash: float,
    elapsed: float,
    scale: float = 1.0,
) -> None:
    r = scrape_r * scale
    pulse = 0.88 + 0.12 * math.sin(elapsed * 6.0)
    if ship_inside or flash > 0.0:
        warn = palette.BOSS_SCRAPE_WARN if flash > 0.0 else palette.BOSS_SCRAPE_RING
        draw_fog_glow(
            canvas,
            sx,
            sy,
            _clamp_glow(r * (1.05 + flash * 0.35), cap=200.0),
            palette.CHASE_FOG_BOSS,
            pulse=elapsed * 8.0,
        )
        canvas.create_oval(
            sx - r * pulse,
            sy - r * pulse * 0.85,
            sx + r * pulse,
            sy + r * pulse * 0.85,
            outline=warn,
            width=3 if flash > 0.0 else 2,
        )
    else:
        canvas.create_oval(
            sx - r,
            sy - r * 0.85,
            sx + r,
            sy + r * 0.85,
            outline=palette.BOSS_SCRAPE_RING,
            width=1,
            dash=(6, 8),
        )
    canvas.create_text(
        sx,
        sy - r - 8,
        text="HULL SCRAPE",
        fill=palette.BOSS_SCRAPE_RING if not ship_inside else palette.BOSS_SCRAPE_WARN,
        font=("Courier New", 7, "bold"),
    )


def draw_mega_squid_tactical(
    canvas: tk.Canvas,
    boss: MegaSquidBoss,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    ship_radius: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
    scrape_flash: float = 0.0,
) -> None:
    if not boss.alive:
        return
    p = camera.world_to_screen(boss.pos, ship_pos, ship_angle)
    sx, sy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    r = boss.radius * scale
    scrape_r = boss_scrape_radius(boss, ship_radius) * scale
    ship_inside = (boss.pos - ship_pos).length() <= boss.radius + ship_radius
    draw_ground_fog_glow(canvas, sx, sy + r * 0.2, r * 2.2, palette.CHASE_FOG_BOSS, pulse=elapsed * 4.0)
    draw_boss_scrape_zone(
        canvas,
        sx,
        sy,
        scrape_r,
        ship_inside=ship_inside,
        flash=scrape_flash,
        elapsed=elapsed,
        scale=1.0,
    )
    material = material_for("mega_squid", theme=rig.theme, view=rig.view)
    body_fill = lerp_hex(material.shadow, material.mid, 0.55 + math.sin(elapsed * 3.0) * 0.08)
    canvas.create_oval(
        sx - r,
        sy - r * 0.72,
        sx + r,
        sy + r * 0.62,
        fill=body_fill,
        outline=material.rim,
        width=3,
    )
    canvas.create_oval(
        sx - r * 0.38,
        sy - r * 0.28,
        sx + r * 0.38,
        sy + r * 0.22,
        fill=material.highlight,
        outline="",
    )
    hp_frac = boss.hits_remaining / max(1, boss.hits_max)
    draw_health_bar(
        canvas,
        sx,
        sy - r - 14,
        r,
        hp_frac,
        outline=material.rim,
        fill=material.rim,
        low_fill=palette.BOSS_SCRAPE_WARN,
    )


def draw_mega_squid_chase(
    canvas: tk.Canvas,
    boss: MegaSquidBoss,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    ship_radius: float,
    elapsed: float,
    scrape_flash: float = 0.0,
    rig: LightRig | None = None,
) -> None:
    if not boss.alive:
        return
    sp = camera.world_to_screen(boss.pos, ship_pos, ship_angle)
    ahead = _chase_ahead(camera, sp.depth)
    entity_scale = _chase_entity_scale(camera, ahead)
    r = min(boss.radius * entity_scale, 36.0)
    scrape_r = min(_chase_world_px(camera, boss_scrape_radius(boss, ship_radius), ahead), 140.0)
    ship_inside = (boss.pos - ship_pos).length() <= boss.radius + ship_radius
    draw_ground_fog_glow(
        canvas,
        sp.x,
        sp.y + 6,
        _clamp_glow(r * 2.0, cap=200.0),
        palette.CHASE_FOG_BOSS,
        pulse=elapsed * 5.0,
    )
    draw_boss_scrape_zone(
        canvas,
        sp.x,
        sp.y,
        scrape_r,
        ship_inside=ship_inside,
        flash=scrape_flash,
        elapsed=elapsed,
        scale=1.0,
    )
    from gravity_ho_matey.render.squid_viz import draw_squid_body, draw_squid_body_lit

    if rig is not None:
        draw_squid_body_lit(
            canvas,
            sp.x,
            sp.y,
            radius=boss.radius,
            scale=entity_scale,
            rig=rig,
            kind="mega_squid",
        )
    else:
        draw_squid_body(canvas, sp.x, sp.y, radius=boss.radius, scale=entity_scale)
    hp_frac = boss.hits_remaining / max(1, boss.hits_max)
    bar_w = r * 1.6
    draw_health_bar(
        canvas,
        sp.x,
        sp.y - r - 12,
        bar_w,
        hp_frac,
        outline="#c058ff",
        fill="#ff4080",
        low_fill=palette.BOSS_SCRAPE_WARN,
    )


def draw_squid_coil_ring_tactical(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    coil_r: float,
    *,
    engaging: bool,
    elapsed: float,
) -> None:
    pulse = 0.92 + 0.08 * math.sin(elapsed * 7.0)
    color = palette.SQUID_TOUCH_TIP if engaging else palette.SQUID_COIL_RING
    canvas.create_oval(
        sx - coil_r * pulse,
        sy - coil_r * pulse * 0.85,
        sx + coil_r * pulse,
        sy + coil_r * pulse * 0.85,
        outline=color,
        width=2 if engaging else 1,
        dash=() if engaging else (5, 7),
    )


def draw_squid_pods_tactical(
    canvas: tk.Canvas,
    pods: list[SquidPod],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    elapsed: float,
) -> None:
    for pod in pods:
        if not pod.alive:
            continue
        p = camera.world_to_screen(pod.pos, ship_pos, ship_angle)
        sx, sy = p.x, p.y + hud_top
        if pod.phase is PodPhase.HATCHING:
            shrink = max(0.2, 1.0 - pod.hatch_timer / pod.hatch_duration)
            r = 16.0 * shrink
            draw_fog_glow(canvas, sx, sy, r * 1.8, palette.CHASE_FOG_BOSS[:3], pulse=elapsed * 10.0)
            canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill="#401858", outline="#ff80c0", width=2)
        else:
            draw_ground_fog_glow(canvas, sx, sy + 3, 14.0, palette.CHASE_FOG_BOSS[:2], pulse=elapsed * 8.0)
            canvas.create_oval(sx - 9, sy - 9, sx + 9, sy + 9, fill="#602878", outline="#ffa0d0", width=2)


def draw_squid_pods_chase(
    canvas: tk.Canvas,
    pods: list[SquidPod],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
) -> None:
    horizon = camera.chase_horizon_y()
    for pod in pods:
        if not pod.alive:
            continue
        sp = camera.world_to_screen(pod.pos, ship_pos, ship_angle)
        if sp.y < horizon:
            continue
        ahead = _chase_ahead(camera, sp.depth)
        entity_scale = _chase_entity_scale(camera, ahead)
        r = min(10.0 * entity_scale, 22.0)
        if pod.phase is PodPhase.HATCHING:
            shrink = max(0.2, 1.0 - pod.hatch_timer / pod.hatch_duration)
            r *= shrink
            draw_fog_glow(
                canvas,
                sp.x,
                sp.y,
                _clamp_glow(r * 2.2, cap=120.0),
                palette.CHASE_FOG_BOSS[:3],
                pulse=elapsed * 12.0,
            )
        canvas.create_oval(sp.x - r, sp.y - r, sp.x + r, sp.y + r, fill="#502070", outline="#ffa0d0", width=2)


def draw_membrane_holo_ribbons(
    canvas: tk.Canvas,
    layout: MembraneLayout,
    *,
    to_screen,
    accent: str,
) -> None:
    for ribbon_id, chain in layout.ribbon_chains:
        if not chain:
            continue
        hw_px = max(5, int(chain[0].half_width * 0.055))
        pts: list[float] = []
        for sample in chain[::4]:
            sx, sy = to_screen(sample.pos)
            pts.extend((sx, sy))
        if len(pts) >= 4:
            canvas.create_line(*pts, fill=palette.RIFT_ROAD_BED, width=hw_px + 5, smooth=True)
            canvas.create_line(*pts, fill=palette.RIFT_RIBBON_SHADOW, width=hw_px + 3, smooth=True)
            canvas.create_line(*pts, fill=accent, width=hw_px + 1, smooth=True)
            canvas.create_line(*pts, fill=palette.RIFT_RIBBON_STRIPE, width=max(1, hw_px // 3), smooth=True)
            seed = _ribbon_seed(ribbon_id)
            for i in range(0, len(pts) // 2, 8):
                x, y = pts[i * 2], pts[i * 2 + 1]
                pr = 2 + (seed + i) % 3
                canvas.create_oval(x - pr, y - pr, x + pr, y + pr, fill=palette.ASTEROID_CRATER, outline="")
