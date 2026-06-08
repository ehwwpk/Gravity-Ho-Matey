from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex

_CHEVRON_SEGMENTS = 9
_CHEVRON_GAP_DEG = 7.0


def _portal_pulse(elapsed: float, *, unlocked: bool) -> tuple[float, float, float]:
    """Return breathe (0..1), spin rate multiplier, shimmer (0..1)."""
    breathe = 0.5 + 0.5 * math.sin(elapsed * (4.2 if unlocked else 1.8))
    shimmer = 0.5 + 0.5 * math.sin(elapsed * 6.4 + 0.8)
    spin = 1.0 if unlocked else 0.12
    return breathe, spin, shimmer


def _portal_tones(*, unlocked: bool, solar: bool) -> dict[str, str]:
    if unlocked:
        if solar:
            return {
                "accent": palette.HUD_ACCENT_SOLAR,
                "rim": lerp_hex(palette.GATE_OPEN, palette.HUD_ACCENT_SOLAR, 0.45),
                "frame": palette.GATE_PORTAL_FRAME_HI,
                "frame_shadow": palette.GATE_PORTAL_FRAME,
                "core": "#100818",
                "tag": palette.HUD_ACCENT_SOLAR,
            }
        return {
            "accent": palette.GATE_OPEN,
            "rim": lerp_hex(palette.GATE_OPEN, palette.HUD_ACCENT, 0.35),
            "frame": palette.GATE_PORTAL_FRAME_HI,
            "frame_shadow": palette.GATE_PORTAL_FRAME,
            "core": "#020806",
            "tag": palette.GATE_OPEN,
        }
    return {
        "accent": palette.GATE_LOCKED,
        "rim": lerp_hex(palette.GATE_LOCKED, "#c85858", 0.35),
        "frame": palette.GATE_PORTAL_FRAME_LOCKED,
        "frame_shadow": "#281818",
        "core": "#060404",
        "tag": palette.GATE_LOCKED,
    }


def _fog_palette(*, unlocked: bool, solar: bool) -> tuple[str, ...]:
    if unlocked and solar:
        return palette.GATE_FOG_WORMHOLE
    if unlocked:
        return palette.GATE_FOG_OPEN
    return palette.GATE_FOG_LOCKED


def _horizon_layers(*, unlocked: bool, solar: bool, tones: dict[str, str]) -> tuple[str, ...]:
    if unlocked and solar:
        return ("#060410", "#180828", "#382868", "#6890d8", "#ffe8a0")
    if unlocked:
        return ("#020806", "#083820", "#148850", "#48d888", "#b8ffd0")
    return ("#060404", "#180808", "#301010", "#502020", "#804040")


def _draw_chevron_ring(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    *,
    rotation_deg: float,
    color: str,
    shadow: str,
    width: float,
    segments: int = _CHEVRON_SEGMENTS,
    gap_deg: float = _CHEVRON_GAP_DEG,
    squash: float = 0.9,
) -> None:
    span = (360.0 - segments * gap_deg) / segments
    ry = radius * squash
    for i in range(segments):
        start = rotation_deg + i * (span + gap_deg)
        canvas.create_arc(
            x - radius,
            y - ry,
            x + radius,
            y + ry,
            start=start,
            extent=span,
            style="arc",
            outline=shadow,
            width=max(1, int(width + 1.5)),
        )
        canvas.create_arc(
            x - radius,
            y - ry,
            x + radius,
            y + ry,
            start=start + 0.6,
            extent=span - 1.2,
            style="arc",
            outline=color,
            width=max(1, int(width)),
        )


def _draw_event_horizon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    inner_r: float,
    *,
    layers: tuple[str, ...],
    squash: float = 0.82,
    ripple: float = 0.0,
) -> None:
    for i, color in enumerate(layers):
        frac = (i + 1) / len(layers)
        wobble = 1.0 + ripple * math.sin(i * 1.7) * 0.06
        r = inner_r * frac * wobble
        ry = r * squash
        canvas.create_oval(x - r, y - ry, x + r, y + ry, fill=color, outline="")


def _draw_portal_ripples(
    canvas: tk.Canvas,
    x: float,
    y: float,
    base_r: float,
    *,
    color: str,
    elapsed: float,
    squash: float = 0.86,
) -> None:
    for i in range(3):
        phase = (elapsed * 1.6 + i * 0.55) % 1.0
        r = base_r * (0.55 + phase * 0.55)
        alpha_t = 1.0 - phase
        ring_color = lerp_hex(color, "#ffffff", alpha_t * 0.35)
        ry = r * squash
        canvas.create_oval(
            x - r,
            y - ry,
            x + r,
            y + ry,
            outline=ring_color,
            width=max(1, int(2 * alpha_t)),
        )


def _draw_rim_sparks(
    canvas: tk.Canvas,
    x: float,
    y: float,
    orbit_r: float,
    *,
    color: str,
    elapsed: float,
    scale: float,
    count: int = 6,
) -> None:
    spin = elapsed * 2.8
    for i in range(count):
        angle = spin + math.tau * i / count
        sx = x + math.cos(angle) * orbit_r
        sy = y + math.sin(angle) * orbit_r * 0.84
        pr = 2.2 * scale
        canvas.create_oval(sx - pr, sy - pr, sx + pr, sy + pr, fill=color, outline="")


def _draw_sealed_cross(
    canvas: tk.Canvas,
    x: float,
    y: float,
    inner_r: float,
    *,
    color: str,
    shimmer: float,
) -> None:
    arm = inner_r * 0.42
    cross = lerp_hex(color, "#ffffff", shimmer * 0.25)
    canvas.create_line(x - arm, y, x + arm, y, fill=cross, width=2)
    canvas.create_line(x, y - arm * 0.72, x, y + arm * 0.72, fill=cross, width=2)
    canvas.create_oval(
        x - inner_r * 0.18,
        y - inner_r * 0.18,
        x + inner_r * 0.18,
        y + inner_r * 0.18,
        outline=cross,
        width=1,
    )


def _draw_status_tag(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    label: str,
    color: str,
    scale: float,
) -> None:
    tag_y = y + 2.0 * scale
    pad_x = 5.0 * scale
    pad_y = 2.0 * scale
    font_size = max(6, min(9, int(7 * scale)))
    canvas.create_rectangle(
        x - pad_x * (len(label) * 0.42 + 1.2),
        tag_y - pad_y,
        x + pad_x * (len(label) * 0.42 + 1.2),
        tag_y + pad_y + font_size,
        fill="#040810",
        outline=color,
        width=1,
    )
    canvas.create_text(
        x,
        tag_y + font_size * 0.45,
        text=label,
        fill=color,
        font=("Courier New", font_size, "bold"),
    )


def _draw_portal_volumetric_glow(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    scale: float,
    elapsed: float,
    rig: LightRig,
    fog: tuple[str, ...],
    unlocked: bool,
) -> None:
    breathe, _, shimmer = _portal_pulse(elapsed, unlocked=unlocked)
    base_r = 34.0 * scale * (1.0 + breathe * (0.18 if unlocked else 0.08))
    pulse_t = elapsed * (3.6 if unlocked else 1.4)

    if rig.view == "chase":
        draw_ground_fog_glow(canvas, x, y + 5 * scale, base_r, fog, pulse=pulse_t)
        if unlocked:
            pillar_y = y - base_r * (0.28 + shimmer * 0.16)
            pillar_fog = palette.GATE_FOG_OPEN_PILLAR if not fog[0].startswith("#18") else fog[:4]
            draw_fog_glow(canvas, x, pillar_y, base_r * 0.78, pillar_fog, pulse=pulse_t * 0.9)
    else:
        draw_fog_glow(canvas, x, y, base_r * 1.05, fog[:4], pulse=pulse_t)


def draw_gate_portal_play(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    scale: float,
    rig: LightRig,
    elapsed: float = 0.0,
    show_tag: bool = True,
    label: str = "",
) -> None:
    """Stargate-style exit portal — lit frame, event horizon, volumetric glow."""
    tones = _portal_tones(unlocked=unlocked, solar=solar)
    breathe, spin_mul, shimmer = _portal_pulse(elapsed, unlocked=unlocked)
    outer_r = max(18.0, size * 0.48) * scale
    inner_r = outer_r * 0.58
    spin = elapsed * (42.0 if unlocked else 4.0) * spin_mul

    _draw_portal_volumetric_glow(
        canvas,
        x,
        y,
        scale=scale,
        elapsed=elapsed,
        rig=rig,
        fog=_fog_palette(unlocked=unlocked, solar=solar),
        unlocked=unlocked,
    )

    if unlocked:
        _draw_portal_ripples(
            canvas,
            x,
            y,
            outer_r * 1.05,
            color=tones["rim"],
            elapsed=elapsed,
        )

    _draw_event_horizon(
        canvas,
        x,
        y,
        inner_r,
        layers=_horizon_layers(unlocked=unlocked, solar=solar, tones=tones),
        ripple=breathe if unlocked else shimmer * 0.35,
    )

    if not unlocked:
        _draw_sealed_cross(canvas, x, y, inner_r * 0.72, color=tones["accent"], shimmer=shimmer)

    _draw_chevron_ring(
        canvas,
        x,
        y,
        outer_r * 1.02,
        rotation_deg=200.0 + spin * 0.35,
        color=lerp_hex(tones["frame"], tones["rim"], shimmer * (0.55 if unlocked else 0.25)),
        shadow=tones["frame_shadow"],
        width=3.5 * scale,
    )
    _draw_chevron_ring(
        canvas,
        x,
        y,
        outer_r * 0.88,
        rotation_deg=188.0 - spin,
        color=lerp_hex(tones["frame"], tones["accent"], 0.35 + breathe * 0.25),
        shadow=tones["frame_shadow"],
        width=2.5 * scale,
        gap_deg=8.0,
    )

    canvas.create_oval(
        x - inner_r * 1.02,
        y - inner_r * 0.84,
        x + inner_r * 1.02,
        y + inner_r * 0.84,
        outline=lerp_hex(tones["rim"], "#ffffff", shimmer * 0.3 if unlocked else 0.12),
        width=max(1, int(2 * scale)),
    )

    if unlocked:
        _draw_rim_sparks(
            canvas,
            x,
            y,
            outer_r * 0.94,
            color=lerp_hex(tones["accent"], "#ffffff", 0.45),
            elapsed=elapsed,
            scale=scale,
        )
        if solar:
            _draw_chevron_ring(
                canvas,
                x,
                y,
                outer_r * 1.14,
                rotation_deg=160.0 + spin * 0.55,
                color=lerp_hex(palette.HUD_ACCENT_SOLAR, palette.GATE_OPEN, breathe * 0.4),
                shadow="#181028",
                width=1.5 * scale,
                gap_deg=10.0,
            )

    if show_tag and label:
        _draw_status_tag(canvas, x, y + outer_r * 0.55, label=label, color=tones["tag"], scale=scale)


def draw_gate_portal_map(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    scale: float,
    label: str = "",
) -> None:
    """Compact holo-map portal glyph — readable at small scale."""
    tones = _portal_tones(unlocked=unlocked, solar=solar)
    outer_r = max(10.0, size * 0.45) * scale
    inner_r = outer_r * 0.55
    draw_fog_glow(canvas, x, y, outer_r * 1.1, _fog_palette(unlocked=unlocked, solar=solar)[:3], pulse=0.0)
    _draw_event_horizon(
        canvas,
        x,
        y,
        inner_r,
        layers=_horizon_layers(unlocked=unlocked, solar=solar, tones=tones)[:3],
    )
    if not unlocked:
        _draw_sealed_cross(canvas, x, y, inner_r * 0.65, color=tones["accent"], shimmer=0.0)
    _draw_chevron_ring(
        canvas,
        x,
        y,
        outer_r,
        rotation_deg=200.0,
        color=tones["frame"],
        shadow=tones["frame_shadow"],
        width=max(1, 2.0 * scale),
    )
    canvas.create_oval(
        x - inner_r,
        y - inner_r * 0.82,
        x + inner_r,
        y + inner_r * 0.82,
        outline=tones["rim"],
        width=1,
    )
    if label:
        font_size = max(5, min(7, int(6 * scale)))
        canvas.create_text(
            x,
            y + outer_r * 0.35,
            text=label,
            fill=tones["tag"],
            font=("Courier New", font_size, "bold"),
        )
