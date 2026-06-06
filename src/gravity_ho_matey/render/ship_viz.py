from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon

# Top-down fighter hull in ship-local space (+X = nose / thrust forward).
_FIGHTER_HULL_LOCAL: tuple[tuple[float, float], ...] = (
    (21.0, 0.0),
    (14.0, 4.0),
    (6.0, 9.5),
    (-5.0, 10.5),
    (-12.0, 5.5),
    (-14.0, 2.0),
    (-10.5, 0.0),
    (-14.0, -2.0),
    (-12.0, -5.5),
    (-5.0, -10.5),
    (6.0, -9.5),
    (14.0, -4.0),
)

_ENGINE_LOCAL = (Vec2(-12.5, 3.6), Vec2(-12.5, -3.6))
_PANEL_LINES_LOCAL = (
    ((8.0, 0.0), (0.0, 6.5)),
    ((8.0, 0.0), (0.0, -6.5)),
    ((-2.0, 7.5), (-9.0, 4.0)),
    ((-2.0, -7.5), (-9.0, -4.0)),
)


def fighter_hull_screen_points(pos: Vec2, angle: float, scale: float) -> list[tuple[float, float]]:
    c = math.cos(angle)
    s = math.sin(angle)
    out: list[tuple[float, float]] = []
    for lx, ly in _FIGHTER_HULL_LOCAL:
        wx = pos.x + (lx * c - ly * s) * scale
        wy = pos.y + (lx * s + ly * c) * scale
        out.append((wx, wy))
    return out


def _local_to_screen(pos: Vec2, angle: float, scale: float, local: Vec2) -> tuple[float, float]:
    c = math.cos(angle)
    s = math.sin(angle)
    lx, ly = local.x, local.y
    return (
        pos.x + (lx * c - ly * s) * scale,
        pos.y + (lx * s + ly * c) * scale,
    )


def _material_with_fittings(base: MaterialTones, stacks: PowerUpStacks) -> MaterialTones:
    if not stacks:
        return base
    rim = base.rim
    if stacks.get(PowerUpKind.THRUST_BOOST, 0):
        rim = lerp_hex(rim, palette.PICKUP_THRUST, 0.35)
    if stacks.get(PowerUpKind.RAPID_FIRE, 0):
        rim = lerp_hex(rim, palette.PICKUP_RAPID, 0.28)
    if stacks.get(PowerUpKind.STABILIZER, 0):
        rim = lerp_hex(rim, palette.PICKUP_STABILIZER, 0.25)
    return MaterialTones(
        highlight=base.highlight,
        mid=base.mid,
        shadow=base.shadow,
        deep=base.deep,
        rim=rim,
        crater_pit=base.crater_pit,
        crater_rim_hi=base.crater_rim_hi,
    )


def _draw_upgrade_fittings(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    scale: float,
    stacks: PowerUpStacks,
    *,
    material: MaterialTones,
    forward: Vec2,
    right: Vec2,
) -> None:
    thrust = stacks.get(PowerUpKind.THRUST_BOOST, 0)
    rapid = stacks.get(PowerUpKind.RAPID_FIRE, 0)
    stabilizer = stacks.get(PowerUpKind.STABILIZER, 0)

    for eng in _ENGINE_LOCAL:
        ex, ey = _local_to_screen(pos, angle, scale, eng)
        er = (2.6 + 0.75 * thrust) * scale
        canvas.create_oval(ex - er, ey - er * 0.85, ex + er, ey + er * 0.85, fill=material.deep, outline=material.shadow, width=1)
        if thrust:
            ring = er + (1.2 + 0.5 * min(thrust, 3)) * scale
            canvas.create_oval(
                ex - ring,
                ey - ring * 0.85,
                ex + ring,
                ey + ring * 0.85,
                outline=palette.PICKUP_THRUST,
                width=max(1, int(thrust)),
            )

    for side in (-1.0, 1.0):
        wing = side * 10.5
        if stabilizer:
            tip = _local_to_screen(pos, angle, scale, Vec2(-5.0, wing))
            root = _local_to_screen(pos, angle, scale, Vec2(-11.0, wing * 0.72))
            canvas.create_line(root[0], root[1], tip[0], tip[1], fill=palette.PICKUP_STABILIZER, width=max(1, int(1 + stabilizer * 0.5)))
            canvas.create_line(
                root[0],
                root[1],
                _local_to_screen(pos, angle, scale, Vec2(-8.0, wing * 1.08))[0],
                _local_to_screen(pos, angle, scale, Vec2(-8.0, wing * 1.08))[1],
                fill=material.crater_rim_hi,
                width=1,
            )

        for n in range(min(rapid, 3)):
            gx = 5.0 - n * 2.8
            gy = wing * (0.72 + n * 0.08)
            muzzle = _local_to_screen(pos, angle, scale, Vec2(gx, gy))
            base = _local_to_screen(pos, angle, scale, Vec2(gx - 3.2, gy))
            canvas.create_line(base[0], base[1], muzzle[0], muzzle[1], fill=palette.PICKUP_RAPID, width=max(1, int(1 + n * 0.5)))
            canvas.create_oval(
                muzzle[0] - 1.4 * scale,
                muzzle[1] - 1.4 * scale,
                muzzle[0] + 1.4 * scale,
                muzzle[1] + 1.4 * scale,
                fill=palette.PICKUP_RAPID,
                outline="",
            )

    if rapid:
        nose = pos + forward * (19.0 * scale)
        canvas.create_oval(
            nose.x - 2.2 * scale,
            nose.y - 2.2 * scale,
            nose.x + 2.2 * scale,
            nose.y + 2.2 * scale,
            outline=palette.PICKUP_RAPID,
            width=1,
        )


def draw_fighter_ship(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    rig: LightRig,
    boost_burst: float = 0.0,
    powerup_stacks: PowerUpStacks | None = None,
) -> None:
    stacks = powerup_stacks or PowerUpStacks()
    base_material = material_for("ship", theme=rig.theme, view=rig.view)
    material = _material_with_fittings(base_material, stacks)
    hull = fighter_hull_screen_points(pos, angle, scale)
    draw_illustrated_polygon(
        canvas,
        hull,
        rig=rig,
        material=material,
        seed=7,
        radius_hint=20.0 * scale,
        outline_width=max(1, int(1 + scale)),
        crater_count=0,
    )

    forward = Vec2.from_angle(angle)
    right = forward.rotated(math.pi / 2.0)

    cp = pos + forward * (9.0 * scale)
    crx = 4.2 * scale
    cry = 2.8 * scale
    canvas.create_oval(
        cp.x - crx,
        cp.y - cry,
        cp.x + crx,
        cp.y + cry,
        fill=material.crater_rim_hi,
        outline=material.crater_pit,
        width=1,
    )
    glint = cp + forward * (1.6 * scale) + right * (-0.8 * scale)
    canvas.create_oval(
        glint.x - 1.2 * scale,
        glint.y - 0.8 * scale,
        glint.x + 0.4 * scale,
        glint.y + 0.5 * scale,
        fill="#e8fcff",
        outline="",
    )

    for a, b in _PANEL_LINES_LOCAL:
        ax, ay = _local_to_screen(pos, angle, scale, Vec2(a[0], a[1]))
        bx, by = _local_to_screen(pos, angle, scale, Vec2(b[0], b[1]))
        canvas.create_line(ax, ay, bx, by, fill=material.shadow, width=1)

    nose = pos + forward * (21.0 * scale)
    canvas.create_line(nose.x, nose.y, cp.x, cp.y, fill=material.highlight, width=1)

    _draw_upgrade_fittings(
        canvas,
        pos,
        angle,
        scale,
        stacks,
        material=material,
        forward=forward,
        right=right,
    )

    if boost_burst > 0.0:
        flame_len = (16.0 + 3.0 * stacks.get(PowerUpKind.THRUST_BOOST, 0)) * scale * (
            0.85 + 0.35 * min(1.0, boost_burst / 0.35)
        )
        width = max(2, int(2 + 2 * min(1.0, boost_burst / 0.35) + stacks.get(PowerUpKind.THRUST_BOOST, 0)))
        core = "#ffb060" if boost_burst > 0.12 else "#ff9048"
        if stacks.get(PowerUpKind.THRUST_BOOST, 0):
            core = lerp_hex(core, palette.PICKUP_THRUST, 0.45)
        for eng in _ENGINE_LOCAL:
            ex, ey = _local_to_screen(pos, angle, scale, eng)
            tail = (ex - forward.x * flame_len, ey - forward.y * flame_len)
            canvas.create_line(ex, ey, tail[0], tail[1], fill=core, width=width)
            canvas.create_line(ex, ey, tail[0], tail[1], fill="#fff0c0", width=max(1, width - 1))


def draw_fighter_ship_fallback(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
) -> None:
    hull = fighter_hull_screen_points(pos, angle, scale)
    flat: list[float] = []
    for x, y in hull:
        flat.extend((x, y))
    canvas.create_polygon(*flat, fill=palette.SHIP, outline="#fff0b5", width=2)
