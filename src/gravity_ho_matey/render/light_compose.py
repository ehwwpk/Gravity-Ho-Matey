from __future__ import annotations

import math
from dataclasses import dataclass, field

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, material_for, well_material_kind


@dataclass(slots=True)
class LightLayerBuilder:
    """B-lite: stacked fog ovals on canvas. B-full multiply reserved for optional Pillow later."""

    rig: LightRig
    elapsed: float = 0.0
    _sources: list[tuple[str, float, float, float, tuple[str, ...], float]] = field(default_factory=list)

    def add_well(
        self,
        well: GravityWell,
        screen_pos: Vec2,
        *,
        scale: float,
        depth: float,
    ) -> None:
        kind = well_material_kind(well.kind)
        mat = material_for(kind, theme=self.rig.theme)
        radius = max(24.0, well.radius * scale * 0.42)
        if well.kind == "black_hole":
            self._sources.append(("sink", screen_pos.x, screen_pos.y, radius * 0.55, (mat.deep,), 1.0))
            colors = palette.CHASE_FOG_BLACK_HOLE
        elif well.kind == "planet":
            colors = palette.CHASE_FOG_PLANET
        else:
            colors = palette.CHASE_FOG_WELL
        pulse = self.elapsed * (2.2 if well.kind == "black_hole" else 1.6)
        strength = max(0.35, min(1.0, 220.0 / max(depth, 40.0)))
        self._sources.append(("glow", screen_pos.x, screen_pos.y, radius, colors, strength * (0.85 + 0.15 * math.sin(pulse))))

    def add_engine(self, anchor_x: float, anchor_y: float, *, thrusting: bool, boost: float) -> None:
        if not thrusting and boost < 0.15:
            return
        r = 28.0 if thrusting else 16.0
        colors = (palette.CHASE_ENGINE_CORE, palette.CHASE_ENGINE_GLOW, "#ff6020")
        self._sources.append(("engine", anchor_x, anchor_y + 8, r, colors, 0.7 if thrusting else 0.35))

    def draw_onto_canvas(self, canvas: tk.Canvas, *, horizon_y: float) -> None:
        """Draw light sinks first, then additive glows (Tk-safe approximation of multiply stack)."""
        for kind, x, y, radius, colors, strength in self._sources:
            if kind == "sink":
                draw_ground_fog_glow(canvas, x, y + 4, radius * strength, colors, pulse=0.0)
                continue
            if y < horizon_y - 8:
                continue
            scaled = tuple(colors) if isinstance(colors, tuple) else (str(colors),)
            if kind == "engine":
                draw_fog_glow(canvas, x, y, radius * strength, scaled, pulse=self.elapsed * 8.0)
            else:
                draw_ground_fog_glow(canvas, x, y + radius * 0.06, radius * strength, scaled, pulse=self.elapsed * 2.0)

    @staticmethod
    def compose_multiply_unavailable() -> None:
        """B-full: requires Pillow + offscreen buffer. Stdlib-first project uses B-lite only."""
        raise NotImplementedError(
            "Multiply lightmap compositing requires Pillow; use LightLayerBuilder.draw_onto_canvas (B-lite)."
        )
