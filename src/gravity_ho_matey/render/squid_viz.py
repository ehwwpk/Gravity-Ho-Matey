from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.health_bar_viz import draw_health_bar, hp_fraction
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon

# Mantle in squid-local space (+X = facing / prey direction).
_MANTLE_LOCAL: tuple[tuple[float, float], ...] = (
    (0.92, 0.0),
    (0.62, 0.58),
    (0.08, 0.78),
    (-0.42, 0.72),
    (-0.98, 0.38),
    (-1.05, 0.0),
    (-0.98, -0.38),
    (-0.42, -0.72),
    (0.08, -0.78),
    (0.62, -0.58),
)

_FIN_LOCAL: tuple[tuple[float, float], ...] = (
    (-0.55, 0.52),
    (-0.88, 0.68),
    (-0.72, 0.42),
    (-0.55, 0.52),
    (-0.55, -0.52),
    (-0.88, -0.68),
    (-0.72, -0.42),
    (-0.55, -0.52),
)


def _flat(points: list[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    for x, y in points:
        out.extend((x, y))
    return out


def _mantle_pulse(elapsed: float, *, engaging: bool) -> float:
    rate = 7.2 if engaging else 4.4
    return 1.0 + 0.055 * math.sin(elapsed * rate) + 0.028 * math.sin(elapsed * rate * 2.1)


def _mantle_screen_points(
    x: float,
    y: float,
    facing: float,
    radius: float,
    scale: float,
    *,
    pulse: float = 1.0,
) -> list[tuple[float, float]]:
    c = math.cos(facing)
    s = math.sin(facing)
    r = radius * scale * pulse
    return [(x + (lx * c - ly * s) * r, y + (lx * s + ly * c) * r) for lx, ly in _MANTLE_LOCAL]


def _fin_screen_points(
    x: float,
    y: float,
    facing: float,
    radius: float,
    scale: float,
    pulse: float,
    fin_index: int,
) -> list[tuple[float, float]]:
    c = math.cos(facing)
    s = math.sin(facing)
    r = radius * scale * pulse
    base = fin_index * 4
    return [
        (x + (lx * c - ly * s) * r, y + (lx * s + ly * c) * r)
        for lx, ly in _FIN_LOCAL[base : base + 4]
    ]


def _perp_offset(body: Vec2, tip: Vec2, amount: float) -> Vec2:
    delta = tip - body
    if delta.length_sq() < 1e-6:
        return Vec2(0.0, amount)
    return delta.rotated(math.pi / 2.0).normalized() * amount


def _tentacle_curve_points(
    body: tuple[float, float],
    tip: tuple[float, float],
    *,
    index: int,
    elapsed: float,
    engaging: bool,
) -> tuple[tuple[float, float], ...]:
    bx, by = body
    tx, ty = tip
    mx = bx + (tx - bx) * 0.48
    my = by + (ty - by) * 0.48
    wobble = math.sin(elapsed * (6.5 if engaging else 4.8) + index * 0.9) * (3.0 if engaging else 6.0)
    perp = _perp_offset(Vec2(bx, by), Vec2(tx, ty), wobble)
    mx += perp.x
    my += perp.y
    return (body, (mx, my), tip)


def draw_squid_coil_ring(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    coil_r: float,
    *,
    engaging: bool,
    elapsed: float,
    facing: float = 0.0,
    tentacle_count: int = 6,
    brood: bool = False,
) -> None:
    """Radial reach stubs at tentacle headings — no closed circle silhouette."""
    accent = palette.BROOD_MOON_VEIN if brood else (palette.SQUID_TOUCH_TIP if engaging else palette.SQUID_COIL_RING)
    shadow = lerp_hex(accent, "#180828", 0.55 if engaging else 0.72)
    pulse = 0.92 + 0.08 * math.sin(elapsed * 7.0)
    r_outer = coil_r * pulse
    r_inner = coil_r * (0.68 if engaging else 0.74)
    for i in range(tentacle_count):
        wobble_a = math.sin(elapsed * 5.5 + i * 1.1) * (0.12 if engaging else 0.06)
        angle = facing + math.tau * i / tentacle_count + wobble_a
        stretch = 1.0 + 0.06 * math.sin(elapsed * 6.0 + i * 0.85)
        ox = sx + math.cos(angle) * r_outer * stretch
        oy = sy + math.sin(angle) * r_outer * stretch * 0.86
        ix = sx + math.cos(angle) * r_inner * stretch
        iy = sy + math.sin(angle) * r_inner * stretch * 0.86
        canvas.create_line(ix, iy, ox, oy, fill=shadow, width=3 if engaging else 2, capstyle=tk.ROUND)
        canvas.create_line(ix, iy, ox, oy, fill=accent, width=2 if engaging else 1, capstyle=tk.ROUND)
        tip_r = 2.5 if engaging else 1.8
        canvas.create_oval(ox - tip_r, oy - tip_r, ox + tip_r, oy + tip_r, fill=accent, outline="")
    if engaging:
        tick_r = r_outer * 0.92
        for i in range(tentacle_count):
            a0 = facing + math.tau * i / tentacle_count
            a1 = facing + math.tau * ((i + 1) % tentacle_count) / tentacle_count
            mx = sx + math.cos((a0 + a1) * 0.5) * tick_r * 0.55
            my = sy + math.sin((a0 + a1) * 0.5) * tick_r * 0.48
            canvas.create_oval(mx - 1.5, my - 1.5, mx + 1.5, my + 1.5, fill=lerp_hex(accent, "#ffffff", 0.25), outline="")


def draw_boss_tentacle_crown(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    *,
    radius: float,
    scale: float,
    facing: float,
    prey_x: float,
    prey_y: float,
    engaging: bool,
    elapsed: float,
    tentacle_count: int = 10,
) -> None:
    """Brood-mother crown tentacles — arcs toward prey, not a hazard oval."""
    reach = radius * scale * (3.2 if engaging else 2.4)
    to_prey = math.atan2(prey_y - sy, prey_x - sx)
    body = (sx, sy)
    for i in range(tentacle_count):
        spread = facing + (i / max(1, tentacle_count - 1) - 0.5) * 1.4
        blend = 0.78 if engaging else 0.42
        angle = spread * (1.0 - blend) + to_prey * blend
        wobble = math.sin(elapsed * (5.0 if engaging else 3.2) + i * 0.75) * (8.0 if engaging else 5.0)
        perp = angle + math.pi / 2.0
        tip_x = sx + math.cos(angle) * reach + math.cos(perp) * wobble
        tip_y = sy + math.sin(angle) * reach * 0.82 + math.sin(perp) * wobble * 0.6
        mid_x = sx + math.cos(angle) * reach * 0.48 + math.cos(perp) * wobble * 0.35
        mid_y = sy + math.sin(angle) * reach * 0.42 + math.sin(perp) * wobble * 0.25
        curve = (body, (mid_x, mid_y), (tip_x, tip_y))
        _draw_tentacle_curved(
            canvas,
            curve,
            engaging=engaging,
            on_hull=False,
            index=i,
            elapsed=elapsed,
        )


def draw_squid_mantle(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    pos: Vec2,
    facing: float,
    radius: float,
    scale: float,
    rig: LightRig | None,
    material: MaterialTones | None,
    kind: str,
    elapsed: float,
    engaging: bool,
) -> None:
    _ = pos, kind
    pulse = _mantle_pulse(elapsed, engaging=engaging)
    if rig is not None and material is not None:
        screen = _mantle_screen_points(x, y, facing, radius, scale, pulse=pulse)
        if len(screen) >= 3:
            draw_illustrated_polygon(
                canvas,
                screen,
                rig=rig,
                material=material,
                seed=int(x) + int(y) * 3,
                radius_hint=radius * scale * pulse,
                outline_width=2,
                crater_count=0,
            )
        for fin_i in (0, 1):
            fin_screen = _fin_screen_points(x, y, facing, radius, scale, pulse, fin_i)
            if len(fin_screen) >= 3:
                canvas.create_polygon(
                    *_flat(fin_screen),
                    fill=lerp_hex(material.shadow, material.deep, 0.35),
                    outline=material.rim,
                    width=1,
                )
        c = math.cos(facing)
        s = math.sin(facing)
        r = radius * scale * pulse
        for side in (-1.0, 1.0):
            ex = x + (0.35 * c - side * 0.22 * s) * r
            ey = y + (0.35 * s + side * 0.22 * c) * r
            er = max(2.0, radius * scale * 0.11)
            canvas.create_oval(ex - er, ey - er, ex + er, ey + er, fill=material.deep, outline=material.rim, width=1)
            canvas.create_oval(
                ex - er * 0.45,
                ey - er * 0.45,
                ex + er * 0.45,
                ey + er * 0.45,
                fill=lerp_hex(material.highlight, "#ffffff", 0.35),
                outline="",
            )
        core_x = x + c * r * 0.12
        core_y = y + s * r * 0.12
        cr = r * 0.22
        canvas.create_oval(
            core_x - cr,
            core_y - cr * 0.85,
            core_x + cr,
            core_y + cr * 0.75,
            fill=lerp_hex(material.highlight, material.mid, 0.25),
            outline="",
        )
        glint = lerp_hex(material.highlight, "#ffffff", 0.3)
        canvas.create_oval(
            core_x - cr * 0.35,
            core_y - cr * 0.45,
            core_x + cr * 0.15,
            core_y - cr * 0.15,
            fill=glint,
            outline="",
        )
        return

    r = radius * scale * pulse
    body_fill = palette.SQUID_BODY
    rim = palette.SQUID_CORE
    core = palette.SQUID_CORE
    canvas.create_oval(x - r, y - r * 0.65, x + r, y + r * 0.55, fill=body_fill, outline=rim, width=2)
    canvas.create_oval(x - r * 0.35, y - r * 0.25, x + r * 0.38, y + r * 0.2, fill=core, outline="")


def _draw_tentacle_curved(
    canvas: tk.Canvas,
    points: tuple[tuple[float, float], ...],
    *,
    engaging: bool,
    on_hull: bool,
    index: int,
    elapsed: float,
) -> None:
    if len(points) < 3:
        return
    base = palette.SQUID_TOUCH_TIP if on_hull else palette.SQUID_TENTACLE
    shadow = lerp_hex(base, "#180828", 0.45)
    mid_color = lerp_hex(base, palette.SQUID_BODY, 0.25)
    pulse_w = 1.0 + 0.12 * math.sin(elapsed * 8.0 + index * 0.7) if on_hull else 1.0
    base_w = (5 if on_hull else 4 if engaging else 3) * pulse_w
    tip_w = max(1, base_w - 2)

    bx, by = points[0]
    mx, my = points[1]
    tx, ty = points[-1]
    canvas.create_line(bx, by, mx, my, tx, ty, fill=shadow, width=int(base_w + 2), smooth=True, capstyle=tk.ROUND)
    canvas.create_line(bx, by, mx, my, tx, ty, fill=mid_color, width=int(base_w), smooth=True, capstyle=tk.ROUND)
    canvas.create_line(bx, by, mx, my, tx, ty, fill=base, width=int(tip_w + 1), smooth=True, capstyle=tk.ROUND)

    for frac in (0.72, 0.88, 0.96):
        sx = bx + (tx - bx) * frac + (mx - bx) * (1.0 - frac) * 0.35
        sy = by + (ty - by) * frac + (my - by) * (1.0 - frac) * 0.35
        sr = max(1.2, (base_w - 1) * (1.0 - frac) * 0.9)
        fill = palette.SQUID_TOUCH_TIP if on_hull and frac > 0.85 else lerp_hex(base, "#ffffff", 0.15)
        canvas.create_oval(sx - sr, sy - sr, sx + sr, sy + sr, fill=fill, outline="")


def draw_squid_tentacles(
    canvas: tk.Canvas,
    body: tuple[float, float],
    tips: tuple[tuple[float, float], ...],
    *,
    coiled: bool,
    tentacle_color: str | None = None,
    touch_color: str | None = None,
    touch_tips: frozenset[int] | None = None,
) -> None:
    """Legacy API — simple 3-point curves."""
    _ = tentacle_color, touch_color
    for i, tip in enumerate(tips):
        on_hull = touch_tips is not None and i in touch_tips
        _draw_tentacle_curved(
            canvas,
            (body, (body[0] + (tip[0] - body[0]) * 0.48, body[1] + (tip[1] - body[1]) * 0.48), tip),
            engaging=coiled,
            on_hull=on_hull,
            index=i,
            elapsed=0.0,
        )


def draw_squid_tentacles_enhanced(
    canvas: tk.Canvas,
    squid: SquidEnemy,
    *,
    body: tuple[float, float],
    tips: list[tuple[float, float]],
    touch_tips: frozenset[int],
    engaging: bool,
    elapsed: float,
    mids: list[tuple[float, float]] | None = None,
) -> None:
    for i, tip in enumerate(tips):
        if mids is not None and i < len(mids):
            mx, my = mids[i]
            wobble = math.sin(elapsed * (6.5 if engaging else 4.8) + i * 0.9) * (2.0 if engaging else 4.0)
            perp = _perp_offset(Vec2(*body), Vec2(*tip), wobble)
            curve = (body, (mx + perp.x, my + perp.y), tip)
        else:
            curve = _tentacle_curve_points(
                body,
                tip,
                index=i,
                elapsed=elapsed,
                engaging=engaging,
            )
        _draw_tentacle_curved(
            canvas,
            curve,
            engaging=engaging,
            on_hull=i in touch_tips,
            index=i,
            elapsed=elapsed,
        )


def draw_squid_body(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    radius: float,
    scale: float = 1.0,
    rig: LightRig | None = None,
    material: MaterialTones | None = None,
    facing: float = 0.0,
    pos: Vec2 | None = None,
    elapsed: float = 0.0,
    engaging: bool = False,
) -> None:
    _ = pos
    draw_squid_mantle(
        canvas,
        x,
        y,
        pos=Vec2(x, y),
        facing=facing,
        radius=radius,
        scale=scale,
        rig=rig,
        material=material,
        kind="squid",
        elapsed=elapsed,
        engaging=engaging,
    )


def draw_squid_body_lit(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    radius: float,
    scale: float,
    rig: LightRig,
    kind: str = "squid",
    facing: float = 0.0,
    pos: Vec2 | None = None,
    elapsed: float = 0.0,
    engaging: bool = False,
) -> None:
    material = material_for(kind, theme=rig.theme, view=rig.view)
    draw_squid_body(
        canvas,
        x,
        y,
        radius=radius,
        scale=scale,
        rig=rig,
        material=material,
        facing=facing,
        pos=pos,
        elapsed=elapsed,
        engaging=engaging,
    )


def draw_squid_enemy_tactical(
    canvas: tk.Canvas,
    squid: SquidEnemy,
    *,
    camera,
    ship_pos: Vec2,
    ship_radius: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    p = camera.world_to_screen(squid.pos, ship_pos, 0.0)
    x, y = p.x, p.y + hud_top
    engaging = squid.clinging or squid.coils_ship(ship_pos, ship_radius)
    wobble = 0.5 + 0.5 * math.sin(elapsed * (7.0 if engaging else 4.0))
    coil_r = (squid.tentacle_span() + ship_radius + 8.0) * camera.tactical_scale * (1.0 + wobble * 0.04)
    brood = rig.theme == "brood_moon"
    alarm = getattr(squid, "detect_range", 640.0) >= 700.0

    r_px = squid.radius * camera.tactical_scale
    glow = palette.CHASE_FOG_BROOD[:2] if brood else palette.SQUID_WRAP_GLOW[:2]
    draw_ground_fog_glow(
        canvas,
        x,
        y + r_px * 0.15,
        (squid.tentacle_span() + squid.radius) * camera.tactical_scale * 0.55,
        glow,
        pulse=elapsed * (5.5 if engaging else 3.0),
    )
    draw_squid_coil_ring(
        canvas, x, y, coil_r,
        engaging=engaging, elapsed=elapsed,
        facing=squid.facing_angle,
        tentacle_count=len(squid.tentacle_tips()),
        brood=brood or alarm,
    )

    touch = ship_radius + 10.0
    touch_sq = touch * touch
    tips: list[tuple[float, float]] = []
    mids: list[tuple[float, float]] = []
    touch_indices: set[int] = set()
    for i, tip in enumerate(squid.tentacle_tips()):
        tp = camera.world_to_screen(tip, ship_pos, 0.0)
        tips.append((tp.x, tp.y + hud_top))
        if i < len(squid.tentacle_mid):
            mp = camera.world_to_screen(squid.tentacle_mid[i], ship_pos, 0.0)
            mids.append((mp.x, mp.y + hud_top))
        if (tip - ship_pos).length_sq() <= touch_sq:
            touch_indices.add(i)

    draw_squid_tentacles_enhanced(
        canvas,
        squid,
        body=(x, y),
        tips=tips,
        touch_tips=frozenset(touch_indices),
        engaging=engaging,
        elapsed=elapsed,
        mids=mids if mids else None,
    )
    draw_squid_body_lit(
        canvas,
        x,
        y,
        radius=squid.radius,
        scale=1.0,
        rig=rig,
        kind="squid",
        facing=squid.facing_angle,
        pos=squid.pos,
        elapsed=elapsed,
        engaging=engaging,
    )
    hp_frac = hp_fraction(squid)
    if hp_frac is not None:
        draw_health_bar(
            canvas,
            x,
            y - squid.radius - 10,
            squid.radius * 1.15,
            hp_frac,
            outline=palette.SQUID_CORE,
            fill="#ff4080",
            low_fill=palette.BOSS_SCRAPE_WARN,
        )


def draw_squid_enemy_chase(
    canvas: tk.Canvas,
    screen_pos: Vec2,
    squid: SquidEnemy,
    *,
    scale: float,
    ship_world: Vec2,
    ship_radius: float,
    tip_screen: tuple[tuple[float, float], ...] | None,
    rig: LightRig,
    elapsed: float,
) -> None:
    engaging = squid.clinging or squid.coils_ship(ship_world, ship_radius)
    r = min(squid.radius * scale, 34.0)
    reach = squid.tentacle_reach * scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * (8.0 if engaging else 4.0))
    brood = rig.theme == "brood_moon"

    if engaging:
        draw_ground_fog_glow(
            canvas,
            screen_pos.x,
            screen_pos.y + 4,
            (r + reach * 0.35) * (1.35 + pulse * 0.2),
            palette.CHASE_FOG_BROOD if brood else palette.SQUID_WRAP_GLOW,
            pulse=elapsed * 5.5,
        )
    else:
        draw_ground_fog_glow(
            canvas,
            screen_pos.x,
            screen_pos.y + 4,
            r * 1.35,
            (palette.CHASE_FOG_BROOD[:2] if brood else palette.SQUID_WRAP_GLOW[:2]),
            pulse=elapsed * 2.5,
        )

    coil_r = (r + reach * 0.85) * (1.0 + pulse * 0.06)
    draw_squid_coil_ring(
        canvas,
        screen_pos.x,
        screen_pos.y,
        coil_r,
        engaging=engaging,
        elapsed=elapsed,
        facing=squid.facing_angle,
        tentacle_count=len(squid.tentacle_tips()),
        brood=brood,
    )

    body = (screen_pos.x, screen_pos.y)
    touch = ship_radius + 10.0
    touch_sq = touch * touch
    tips: list[tuple[float, float]] = []
    mids: list[tuple[float, float]] = []
    touch_indices: set[int] = set()

    if tip_screen:
        for i, (tx, ty) in enumerate(tip_screen):
            tips.append((tx, ty))
            if i < len(squid.tentacle_mid):
                blend = 0.52
                mx = screen_pos.x + (tx - screen_pos.x) * blend
                my = screen_pos.y + (ty - screen_pos.y) * blend
                mids.append((mx, my))
            if i < len(squid.tentacle_tips()) and (squid.tentacle_tips()[i] - ship_world).length_sq() <= touch_sq:
                touch_indices.add(i)
    else:
        for i, tip in enumerate(squid.tentacle_tips()):
            spread = squid.facing_angle + math.tau * i / len(squid.tentacle_tips())
            reach_len = reach * (1.55 + pulse * 0.22 if engaging else 1.18)
            if engaging:
                to_ship = ship_world - screen_pos
                if to_ship.length_sq() > 1e-6:
                    coil_dir = to_ship.normalized()
                    blend = 0.72
                    dir_vec = (Vec2.from_angle(spread) * (1.0 - blend) + coil_dir * blend).normalized()
                    tip_pt = screen_pos + dir_vec * reach_len
                else:
                    tip_pt = screen_pos + Vec2.from_angle(spread) * reach_len
            else:
                sway = math.sin(elapsed * 6.0 + i * 0.9) * 5.0
                tip_pt = screen_pos + Vec2.from_angle(spread) * reach_len + Vec2(sway, sway * 0.35)
            tips.append((tip_pt.x, tip_pt.y))

    draw_squid_tentacles_enhanced(
        canvas,
        squid,
        body=body,
        tips=tips,
        touch_tips=frozenset(touch_indices),
        engaging=engaging,
        elapsed=elapsed,
        mids=mids if mids else None,
    )
    draw_squid_body_lit(
        canvas,
        screen_pos.x,
        screen_pos.y,
        radius=squid.radius,
        scale=scale,
        rig=rig,
        kind="squid",
        facing=squid.facing_angle,
        pos=squid.pos,
        elapsed=elapsed,
        engaging=engaging,
    )


def draw_squid_map_glyph(
    canvas: tk.Canvas,
    mx: float,
    my: float,
    *,
    radius: float,
    facing: float,
) -> None:
    c = math.cos(facing)
    s = math.sin(facing)
    mantle: list[tuple[float, float]] = []
    for lx, ly in _MANTLE_LOCAL:
        wx = lx * c - ly * s
        wy = lx * s + ly * c
        mantle.append((mx + wx * radius, my + wy * radius))
    if len(mantle) >= 3:
        canvas.create_polygon(
            *_flat(mantle),
            fill=palette.SQUID_BODY,
            outline=palette.SQUID_CORE,
            width=1,
        )
    for i in range(4):
        angle = facing + math.tau * i / 4
        tx = mx + math.cos(angle) * radius * 1.45
        ty = my + math.sin(angle) * radius * 1.45
        canvas.create_line(mx, my, tx, ty, fill=palette.SQUID_TENTACLE, width=1)


def project_tips_to_screen(
    tips: tuple[Vec2, ...],
    project,
) -> tuple[tuple[float, float], ...]:
    out: list[tuple[float, float]] = []
    for tip in tips:
        p = project(tip)
        if p is None:
            continue
        out.append(p)
    return tuple(out)
