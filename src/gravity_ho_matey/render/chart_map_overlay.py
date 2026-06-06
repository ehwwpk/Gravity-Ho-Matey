from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


class ChartMapOverlay:
    """Diegetic holo-table preview between levels."""

    TABLE_X = 180
    TABLE_Y = 150
    TABLE_W = 600
    TABLE_H = 360

    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        field: GravityField,
        *,
        campaign: CampaignState,
        cleared_level_id: str,
        elapsed: float,
    ) -> None:
        width = world.config.viewport_width
        canvas.create_rectangle(0, 0, width, world.config.viewport_height, fill=palette.BACKGROUND, outline="")
        self._starfield(canvas, width)
        canvas.create_text(
            width // 2,
            48,
            text="◈ NAV HOLO — SET COURSE ◈",
            fill=palette.HUD_ACCENT,
            font=("Courier New", 18, "bold"),
        )
        canvas.create_text(
            width // 2,
            78,
            text=f"Sector cleared in {elapsed:0.2f}s — review the upcoming chart before launch.",
            fill=palette.MUTED_TEXT,
            font=("Courier New", 11),
        )
        hp.draw_panel(canvas, self.TABLE_X, self.TABLE_Y, self.TABLE_W, self.TABLE_H, frame=palette.HUD_FRAME, accent=palette.HUD_ACCENT)
        canvas.create_text(
            self.TABLE_X + 12,
            self.TABLE_Y + 10,
            anchor="w",
            text=world.config.level_name.upper(),
            fill=palette.HUD_DIM,
            font=("Courier New", 10, "bold"),
        )
        self._draw_map(canvas, world, field)
        self._draw_legend(canvas, world)
        self._draw_campaign_strip(canvas, campaign, cleared_level_id)
        canvas.create_text(
            width // 2,
            580,
            text="Enter: launch course     Esc: title     V in-flight: toggle tactical / chase cam",
            fill=palette.TEXT,
            font=("Courier New", 12),
        )

    def _draw_map(self, canvas: tk.Canvas, world: GameWorld, field: GravityField) -> None:
        inner_x = self.TABLE_X + 20
        inner_y = self.TABLE_Y + 36
        inner_w = self.TABLE_W - 40
        inner_h = self.TABLE_H - 52
        scale_x = inner_w / world.config.width
        scale_y = inner_h / world.config.height
        scale = min(scale_x, scale_y)

        def to_map(p: Vec2) -> tuple[float, float]:
            mx = inner_x + p.x * scale
            my = inner_y + p.y * scale
            return mx, my

        for row in range(field.rows):
            for col in range(field.cols):
                cell = field.cell_at(col, row)
                if cell.magnitude <= 1e-6:
                    continue
                wx = field.origin.x + col * field.cell_size
                wy = field.origin.y + row * field.cell_size
                mx, my = to_map(Vec2(wx, wy))
                size = field.cell_size * scale
                norm = cell.magnitude / field.max_magnitude
                tone = "#2a3558" if norm < 0.45 else "#5a1840"
                canvas.create_rectangle(mx, my, mx + size, my + size, fill=tone, outline="")

        for wall in world.walls:
            r = wall.rect
            x1, y1 = to_map(Vec2(r.x, r.y))
            x2, y2 = to_map(Vec2(r.x + r.w, r.y + r.h))
            canvas.create_rectangle(x1, y1, x2, y2, fill=palette.WALL, outline=palette.WALL_EDGE)

        for well in world.wells:
            mx, my = to_map(well.pos)
            rr = max(4.0, well.radius * scale * 0.35)
            color = palette.BLACK_HOLE if well.kind == "black_hole" else palette.PLANET_WELL
            canvas.create_oval(mx - rr, my - rr, mx + rr, my + rr, outline=color, width=2)

        for beacon in world.beacons:
            mx, my = to_map(beacon.pos)
            canvas.create_rectangle(mx - 4, my - 4, mx + 4, my + 4, fill=palette.BEACON, outline="")

        gx, gy = to_map(Vec2(world.finish_gate.rect.x, world.finish_gate.rect.y))
        gw = world.finish_gate.rect.w * scale
        gh = world.finish_gate.rect.h * scale
        canvas.create_rectangle(gx, gy, gx + gw, gy + gh, outline=palette.GATE_LOCKED, width=2)

        sx, sy = to_map(world.ship.pos)
        canvas.create_polygon(
            sx,
            sy - 6,
            sx + 5,
            sy + 4,
            sx - 5,
            sy + 4,
            fill=palette.SHIP,
            outline="#fff0b5",
        )

    def _draw_legend(self, canvas: tk.Canvas, world: GameWorld) -> None:
        lx = self.TABLE_X + self.TABLE_W + 24
        ly = self.TABLE_Y + 40
        canvas.create_text(lx, ly, anchor="w", text="CHART NOTES", fill=palette.HUD_DIM, font=("Courier New", 9, "bold"))
        strip = "Long strip — free forward/back" if world.config.height > world.config.viewport_height else "Compact tactical arena"
        lines = [
            strip,
            f"World: {world.config.width}×{world.config.height}",
            f"Beacons: {len(world.beacons)}",
            f"Wells: {len(world.wells)}",
            "Cameras: TACTICAL / CHASE (V to toggle)",
        ]
        for i, line in enumerate(lines):
            canvas.create_text(lx, ly + 22 + i * 18, anchor="w", text=line, fill=palette.MUTED_TEXT, font=("Courier New", 9))

    def _draw_campaign_strip(self, canvas: tk.Canvas, campaign: CampaignState, cleared_level_id: str) -> None:
        y = 528
        canvas.create_text(48, y, anchor="w", text=f"LIVES {campaign.lives}", fill=palette.HUD_ACCENT, font=("Courier New", 10, "bold"))
        canvas.create_text(
            48,
            y + 20,
            anchor="w",
            text=f"HULL {campaign.hull_chunks}/{CHUNKS_PER_LIFE}",
            fill=palette.HUD_ACCENT,
            font=("Courier New", 10, "bold"),
        )
        canvas.create_text(48, y + 40, anchor="w", text=f"Last sector: {cleared_level_id}", fill=palette.MUTED_TEXT, font=("Courier New", 9))

    def _starfield(self, canvas: tk.Canvas, width: int) -> None:
        for i in range(70):
            x = (i * 83 + 17) % width
            y = (i * 47 + 31) % 640
            canvas.create_rectangle(x, y, x + 2, y + 2, fill="#294764", outline="")
