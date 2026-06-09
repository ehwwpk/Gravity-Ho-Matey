from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.expedition_foot_config import (
    INTERACT_PROMPT_FADE_RANGE,
    INTERACT_PROMPT_FULL_RANGE,
    INTERACT_PROMPT_SHOW_RANGE,
)
from gravity_ho_matey.gameplay.expedition_mission import (
    ExpeditionState,
    InteractKind,
    expedition_foot_objectives_met,
    expedition_fuel_loaded,
)
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.lighting import lerp_hex


def _proximity_strength(dist: float) -> float:
    if dist > INTERACT_PROMPT_SHOW_RANGE:
        return 0.0
    if dist <= INTERACT_PROMPT_FULL_RANGE:
        return 1.0
    span = max(1.0, INTERACT_PROMPT_SHOW_RANGE - INTERACT_PROMPT_FULL_RANGE)
    return 1.0 - (dist - INTERACT_PROMPT_FULL_RANGE) / span


def _holo(fill: str, *, strength: float, bg: str = palette.COMET_BG) -> str:
    """Blend accent toward background for a translucent holo read."""
    blend = 0.82 - strength * 0.38
    return lerp_hex(fill, bg, max(0.0, min(1.0, blend)))


def draw_expedition_interact_prompts(
    canvas: tk.Canvas,
    exp: ExpeditionState,
    avatar_pos: Vec2,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    elapsed: float,
) -> None:
    """Proximity holo HOLD E badges — faint until you walk up."""
    scale = camera.tactical_scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * 3.8)

    candidates: list[tuple[float, object, str, str | None, str, bool, float]] = []
    for node in exp.interact_nodes:
        if node.one_shot and node.id in exp.completed_interact_ids:
            continue
        if node.kind is InteractKind.FUEL_VALVE and expedition_fuel_loaded(exp):
            continue
        dist = (node.pos - avatar_pos).length()
        strength = _proximity_strength(dist)
        if strength < 0.08:
            continue
        label, sublabel, accent, blocked = _prompt_copy(exp, node)
        if label is None:
            continue
        candidates.append((dist, node, label, sublabel, accent, blocked, strength))

    candidates.sort(key=lambda item: item[0])
    for dist, node, label, sublabel, accent, blocked, strength in candidates[:3]:
        p = camera.world_to_screen(node.pos, follow, 0.0)
        cx, cy = p.x, p.y + hud_top - 24.0 * scale
        bob = math.sin(elapsed * 2.8 + hash(node.id) % 5) * 2.0 * scale * strength
        cy -= bob
        ring_r = (14.0 + pulse * 3.0 * strength) * scale
        ring_color = _holo(palette.BOSS_SCRAPE_WARN if blocked else accent, strength=strength)
        fill = _holo(accent if not blocked else palette.COMET_VEIN, strength=strength * 0.85)
        holo_stipple = "gray50" if strength > 0.55 else "gray25"
        text_color = lerp_hex(palette.COMET_ICE_HIGHLIGHT, accent, 0.35 + strength * 0.45)

        canvas.create_oval(
            cx - ring_r - 3,
            cy - ring_r - 3,
            cx + ring_r + 3,
            cy + ring_r + 3,
            outline=ring_color,
            width=1,
            dash=(6, 5),
        )
        canvas.create_oval(
            cx - ring_r,
            cy - ring_r,
            cx + ring_r,
            cy + ring_r,
            fill=fill,
            outline=ring_color,
            width=1,
            stipple=holo_stipple,
        )
        canvas.create_text(
            cx,
            cy - 1,
            text="E",
            fill=text_color,
            font=("Courier New", max(9, int(10 * scale)), "bold"),
        )
        if strength >= 0.45:
            canvas.create_text(
                cx,
                cy + ring_r + 8 * scale,
                text=label,
                fill=lerp_hex(accent, palette.COMET_VEIN, 1.0 - strength * 0.6),
                font=("Consolas", max(7, int(8 * scale))),
            )
        if sublabel and strength >= 0.65:
            canvas.create_text(
                cx,
                cy + ring_r + 18 * scale,
                text=sublabel,
                fill=lerp_hex(
                    palette.BOSS_SCRAPE_WARN if blocked else palette.COMET_VEIN,
                    palette.COMET_BG,
                    0.45 - strength * 0.2,
                ),
                font=("Consolas", max(6, int(7 * scale))),
            )


def _prompt_copy(
    exp: ExpeditionState,
    node,
) -> tuple[str | None, str | None, str, bool]:
    if node.kind is InteractKind.FUEL_VALVE:
        if node.id in exp.completed_interact_ids:
            return None, None, palette.GATE_OPEN, False
        return "LOAD", "HOLD E", palette.COMET_HUD_ACCENT, False
    if node.kind is InteractKind.EXTRACT_PAD:
        if not expedition_fuel_loaded(exp):
            return "LANDER", "DEPOT FUEL FIRST", palette.COMET_VEIN, True
        if expedition_foot_objectives_met(exp):
            return "RTB", "HOLD E", palette.GATE_OPEN, False
        return "RTB", "HOLD E", palette.GATE_OPEN, False
    return None, None, palette.HUD_DIM, False
