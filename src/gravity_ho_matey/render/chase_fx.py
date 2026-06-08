from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CHASE_BOOST_KICK_Y, ViewCamera
from gravity_ho_matey.render.ship_viz import ENGINE_PORTS
from gravity_ho_matey.render.starfield_viz import draw_chase_parallax_stars

_SKY_THEMES: dict[str, tuple[str, str]] = {
    "cove": ("#040810", "#0a1830"),
    "drift": ("#030610", "#0c1a38"),
    "solar": ("#080408", "#281008"),
    "rift": ("#060410", "#140828"),
    "siege": ("#100608", "#281018"),
    "brood_moon": ("#120818", "#281830"),
}


def _engine_screen(
    anchor_x: float,
    anchor_y: float,
    display_angle: float,
    ship_scale: float,
    local: Vec2,
) -> tuple[float, float]:
    c = math.cos(display_angle)
    s = math.sin(display_angle)
    lx, ly = local.x, local.y
    return (
        anchor_x + (lx * c - ly * s) * ship_scale,
        anchor_y + (lx * s + ly * c) * ship_scale,
    )


def draw_chase_sky(canvas: tk.Canvas, camera: ViewCamera, world: GameWorld) -> None:
    """Gradient sky band + parallax starfield."""
    horizon = camera.chase_horizon_y()
    top = camera.play_hud_top
    width = camera.viewport_width
    theme = world.config.level_theme
    solar = theme == "solar"
    sky_top, sky_horizon = _SKY_THEMES.get(theme, _SKY_THEMES["cove"])
    steps = 8
    band = max(1.0, (horizon - top) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = top + band * i
        y1 = top + band * (i + 1)
        color = _lerp_color(sky_top, sky_horizon, t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")
    _draw_theme_nebula(canvas, camera, world, horizon, theme)
    if solar:
        _draw_solar_corona(canvas, camera, horizon)
    draw_chase_parallax_stars(canvas, camera=camera, world=world, horizon=horizon)


def _draw_theme_nebula(canvas: tk.Canvas, camera: ViewCamera, world: GameWorld, horizon: float, theme: str) -> None:
    width = camera.viewport_width
    top = camera.play_hud_top
    elapsed = world.elapsed
    blobs = {
        "cove": (("#0a2840", 0.22),),
        "drift": (("#180828", 0.18), ("#102038", 0.14)),
        "rift": (("#201040", 0.2),),
        "siege": (("#301008", 0.16),),
        "brood_moon": (("#281030", 0.18),),
    }.get(theme, ())
    for i, (color, frac) in enumerate(blobs):
        cx = width * (0.28 + 0.22 * i) + math.sin(elapsed * 0.15 + i) * 24.0
        cy = top + (horizon - top) * (0.35 + 0.12 * i)
        rx = width * frac * (0.9 + 0.08 * math.sin(elapsed * 0.4 + i))
        ry = (horizon - top) * frac * 0.55
        canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=color, outline="")


def _draw_solar_corona(canvas: tk.Canvas, camera: ViewCamera, horizon: float) -> None:
    width = camera.viewport_width
    top = camera.play_hud_top
    corona_y = top + (horizon - top) * 0.12
    canvas.create_rectangle(0, top, width, corona_y + 6, fill="#3a2010", outline="")
    canvas.create_line(0, corona_y, width, corona_y, fill="#806030", width=1)


def draw_siege_chase_floor_wash(canvas: tk.Canvas, camera: ViewCamera) -> None:
    """Ember haze on the chase floor for siege sectors."""
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 4
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color("#1a0c10", "#0a0608", t * 0.7)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")


def draw_rift_chase_floor_wash(canvas: tk.Canvas, camera: ViewCamera) -> None:
    """Soft horizon haze — keeps chase view readable in deep rift sectors."""
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 4
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color("#0a1420", "#060a10", t * 0.65)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")


def draw_brood_orbital_chase_floor_wash(canvas: tk.Canvas, camera: ViewCamera) -> None:
    """Mauve exosphere haze for brood moon orbital approach — not generic blue floor."""
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 5
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color("#140820", "#221028", t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")


def draw_chase_floor_gradient(canvas: tk.Canvas, camera: ViewCamera) -> None:
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 6
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color(palette.CHASE_FLOOR_TOP, palette.CHASE_FLOOR_BOTTOM, t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")


def draw_fog_glow(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    colors: tuple[str, ...],
    *,
    pulse: float = 0.0,
) -> None:
    """Layered concentric ovals simulating volumetric fog (Tk-safe, no alpha)."""
    breathe = 1.0 + math.sin(pulse) * 0.08
    for i, color in enumerate(colors):
        frac = (i + 1) / len(colors)
        r = radius * frac * breathe
        canvas.create_oval(cx - r, cy - r * 0.72, cx + r, cy + r * 0.72, fill=color, outline="")


def draw_ground_fog_glow(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    colors: tuple[str, ...],
    *,
    pulse: float = 0.0,
) -> None:
    """Floor-hugging well glow — squashed ellipses anchored on the grid plane."""
    breathe = 1.0 + math.sin(pulse) * 0.06
    base_y = cy + radius * 0.08
    for i, color in enumerate(colors):
        frac = (i + 1) / len(colors)
        r = radius * frac * breathe
        canvas.create_oval(cx - r, base_y - r * 0.28, cx + r, base_y + r * 0.1, fill=color, outline="")


def draw_speed_streaks(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    anchor_x: float,
    anchor_y: float,
    display_angle: float,
    ship_scale: float = 1.12,
) -> None:
    """Cruise-only motion streaks — aligned to chase ship rig, never world-velocity skew."""
    if world.ship.boost_flash > 0.0:
        return
    speed = world.ship.vel.length()
    if speed < 55.0:
        return
    forward = Vec2.from_angle(display_angle)
    right = forward.rotated(math.pi / 2.0)
    intensity = min(1.0, (speed - 55.0) / 180.0)
    count = min(14, int(4 + speed / 28.0))
    horizon = camera.chase_horizon_y()
    streak_len = min(72.0, 10.0 + speed * 0.12)
    color = palette.CHASE_SPEED_STREAK

    for i in range(count):
        t = (i + 1) / (count + 1)
        lateral = ((i * 41) % 19 - 9) * (1.1 - t * 0.35)
        back = 36.0 + t * (90.0 + intensity * 30.0)
        sx = anchor_x - forward.x * back + right.x * lateral
        sy = anchor_y - forward.y * back + right.y * lateral * 0.35
        if sy < horizon + 8:
            continue
        ex = sx - forward.x * streak_len * (0.45 + t * 0.55)
        ey = sy - forward.y * streak_len * (0.45 + t * 0.55)
        canvas.create_line(sx, sy, ex, ey, fill=color, width=1)


def _boost_tap_strength(flash: float, max_flash: float) -> float:
    """Early-boost window for shock/spark punch — eased ramp, not a hard snap."""
    window = max(0.05, max_flash * 0.34)
    elapsed = max(0.0, max_flash - flash)
    t = max(0.0, 1.0 - elapsed / window)
    return t * t * (3.0 - 2.0 * t)


def draw_chase_boost_jolt(
    canvas: tk.Canvas,
    *,
    anchor_x: float,
    anchor_y: float,
    display_angle: float,
    world: GameWorld,
    camera: ViewCamera,
    intensity: float,
    elapsed: float,
    ship_scale: float = 1.12,
) -> None:
    """Shift-boost punch — shock rings and sparks (screen-aligned).

    Line exhaust + engine blooms live on ``draw_fighter_ship(chase_boost=True)``.
    """
    flash = world.ship.boost_flash
    if flash <= 0.0:
        return
    max_flash = max(0.05, world.config.boost_flash_seconds)
    tap = _boost_tap_strength(flash, max_flash)
    kick = min(1.0, camera.boost_kick_y / max(1.0, CHASE_BOOST_KICK_Y))
    _ = elapsed

    forward = Vec2.from_angle(display_angle)
    aft_center_x = anchor_x - forward.x * 10.0 * ship_scale
    aft_center_y = anchor_y - forward.y * 10.0 * ship_scale
    sustain = min(1.0, flash / max_flash)

    # Sustained exhaust wisps — thin lines for the whole boost, not just tap.
    right = forward.rotated(math.pi / 2.0)
    wisp_count = int(4 + sustain * 6 + intensity * 2)
    for i in range(wisp_count):
        fan = (i / max(1, wisp_count - 1) - 0.5) * 0.85
        lateral = fan * (14.0 + sustain * 10.0) * ship_scale
        sx = aft_center_x + right.x * lateral
        sy = aft_center_y + right.y * lateral * 0.35
        wisp_len = (14.0 + sustain * 22.0 + tap * 8.0) * ship_scale
        color = palette.CHASE_BOOST_SPARK[1 + (i % 2)]
        canvas.create_line(
            sx,
            sy,
            sx - forward.x * wisp_len,
            sy - forward.y * wisp_len,
            fill=color,
            width=1,
        )

    if tap > 0.06:
        for ring, color in enumerate(palette.CHASE_BOOST_SHOCK):
            spread = (10.0 + tap * (20.0 + ring * 8.0) + kick * 10.0) * ship_scale
            canvas.create_oval(
                aft_center_x - spread,
                aft_center_y - spread * 0.62,
                aft_center_x + spread,
                aft_center_y + spread * 0.62,
                fill="",
                outline=color,
                width=2 - ring,
            )

    spark_count = int(4 + tap * 7 + intensity * 2)
    for i in range(spark_count):
        fan = (i / max(1, spark_count - 1) - 0.5) * 1.0
        spread_angle = display_angle + math.pi + fan
        dist = (8.0 + (i * 11) % 18 + tap * 12.0) * ship_scale
        sx = aft_center_x + math.cos(spread_angle) * dist * 0.35
        sy = aft_center_y + math.sin(spread_angle) * dist * 0.35
        spark_len = (6.0 + tap * 10.0 + kick * 5.0) * ship_scale
        ex = sx - forward.x * spark_len
        ey = sy - forward.y * spark_len
        color = palette.CHASE_BOOST_SPARK[i % len(palette.CHASE_BOOST_SPARK)]
        canvas.create_line(sx, sy, ex, ey, fill=color, width=1)


def draw_engine_bloom(
    canvas: tk.Canvas,
    anchor_x: float,
    anchor_y: float,
    *,
    display_angle: float,
    boost_energy: float,
    thrusting: bool,
    speed: float = 0.0,
    intensity: float = 0.0,
    ship_scale: float = 1.12,
) -> None:
    """Idle engine glow at cruise — boost uses draw_chase_boost_jolt instead."""
    if thrusting:
        return
    if speed < 48.0 and intensity < 0.08:
        return
    forward = Vec2.from_angle(display_angle)
    speed_scale = min(1.35, 1.0 + speed / 240.0)
    for eng in ENGINE_PORTS:
        ex, ey = _engine_screen(anchor_x, anchor_y, display_angle, ship_scale, eng)
        for i, frac in enumerate((0.55, 0.85, 1.0)):
            r = (5.0 + i * 3.5) * speed_scale * ship_scale
            color = palette.CHASE_ENGINE_CORE if i == 2 else palette.CHASE_ENGINE_GLOW
            canvas.create_oval(ex - r, ey - r * 0.5, ex + r, ey + r * 0.65, fill="", outline=color, width=1)
        if speed > 95.0 and boost_energy > 0.15:
            tail = 6.0 * speed_scale * ship_scale
            canvas.create_line(
                ex,
                ey,
                ex - forward.x * tail,
                ey - forward.y * tail,
                fill=palette.CHASE_ENGINE_GLOW,
                width=1,
            )


def draw_speed_vignette(
    canvas: tk.Canvas,
    camera: ViewCamera,
    speed: float,
    *,
    intensity: float | None = None,
) -> None:
    chase_intensity = intensity if intensity is not None else camera.chase_intensity()
    if speed < 85.0 and chase_intensity < 0.12:
        return
    speed_strength = min(1.0, (speed - 85.0) / 150.0)
    strength = max(speed_strength, chase_intensity * 0.85)
    if strength <= 0.05:
        return
    w = camera.viewport_width
    h = camera.viewport_height
    top = camera.play_hud_top
    inset = int(36 + strength * (54 + chase_intensity * 18))
    fill = palette.CHASE_VIGNETTE
    canvas.create_rectangle(0, top, inset, h, fill=fill, outline="")
    canvas.create_rectangle(w - inset, top, w, h, fill=fill, outline="")
    band = int(10 + strength * (20 + chase_intensity * 10))
    canvas.create_rectangle(0, top, w, top + band, fill=fill, outline="")
    canvas.create_rectangle(0, h - band, w, h, fill=fill, outline="")
    corner = int(20 + strength * (36 + chase_intensity * 16))
    for cx, cy in ((0, top), (w, top), (0, h), (w, h)):
        canvas.create_rectangle(cx - corner, cy - corner, cx + corner, cy + corner, fill=fill, outline="")


def draw_boost_pressure(
    canvas: tk.Canvas,
    camera: ViewCamera,
    *,
    thrusting: bool,
    intensity: float | None = None,
) -> None:
    """Edge pressure bands during boost — speed sensation without shifting the rig."""
    if not thrusting:
        return
    chase_intensity = intensity if intensity is not None else camera.chase_intensity()
    if chase_intensity < 0.2:
        return
    w = camera.viewport_width
    h = camera.viewport_height
    top = camera.play_hud_top
    band = int(5 + chase_intensity * 11)
    colors = ("#081018", "#060c14", "#040810")
    for i, color in enumerate(colors):
        inset = band * (i + 1)
        canvas.create_rectangle(0, top, inset, h, fill=color, outline="")
        canvas.create_rectangle(w - inset, top, w, h, fill=color, outline="")


def _lerp_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"
