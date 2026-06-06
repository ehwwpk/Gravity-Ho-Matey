from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE, MAX_LIVES
from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette


class SciFiHudOverlay:
    """Retro sci-fi command overlay — bracketed panels, segmented readouts, CRT accents."""

    PANEL_H = 54
    FONT = ("Courier New", 10, "bold")
    FONT_SMALL = ("Courier New", 8)
    FONT_TITLE = ("Courier New", 9, "bold")

    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        campaign: CampaignState,
        *,
        hud_alert: str = "",
    ) -> None:
        width = world.config.width
        solar = world.config.level_theme == "solar"
        accent = palette.HUD_ACCENT_SOLAR if solar else palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG

        canvas.create_rectangle(0, 0, width, self.PANEL_H, fill=bg, outline="")
        canvas.create_line(0, self.PANEL_H, width, self.PANEL_H, fill=accent, width=1)
        self._scanline(canvas, width)

        self._panel(canvas, 8, 6, 148, 42, frame, accent)
        self._label(canvas, 16, 12, "CAPTAIN", dim)
        self._draw_lives(canvas, 16, 24, campaign.lives, accent, palette.HUD_LIFE_EMPTY)

        self._panel(canvas, 162, 6, 148, 42, frame, accent)
        self._label(canvas, 170, 12, "HULL INTEGRITY", dim)
        self._draw_hull_chunks(canvas, 170, 24, campaign.hull_chunks, CHUNKS_PER_LIFE, accent, palette.HUD_HULL_EMPTY)

        self._panel(canvas, 316, 6, 128, 42, frame, accent)
        self._label(canvas, 324, 12, "NAV BEACONS", dim)
        remaining = world.beacons_remaining
        total = len(world.beacons)
        beacon_color = palette.BEACON if remaining else palette.BEACON_COLLECTED
        canvas.create_text(
            324,
            30,
            anchor="w",
            text=f"{remaining:02d} / {total:02d}",
            fill=beacon_color,
            font=("Courier New", 14, "bold"),
        )

        self._panel(canvas, 450, 6, 118, 42, frame, accent)
        self._label(canvas, 458, 12, "CHRONO", dim)
        canvas.create_text(
            458,
            30,
            anchor="w",
            text=f"{world.elapsed:05.1f}s",
            fill=accent,
            font=("Courier New", 14, "bold"),
        )

        self._panel(canvas, 574, 6, 118, 42, frame, accent)
        self._label(canvas, 582, 12, "REACTOR", dim)
        boost_pct = int(world.ship.boost_energy * 100)
        boost_color = palette.HUD_BOOST if boost_pct > 25 else palette.HUD_WARN
        canvas.create_text(582, 30, anchor="w", text=f"{boost_pct:3d}%", fill=boost_color, font=("Courier New", 14, "bold"))
        self._boost_bar(canvas, 582, 38, 100, 6, world.ship.boost_energy, accent, dim)

        cargo_x = width - 156
        self._panel(canvas, cargo_x, 6, 148, 42, frame, accent)
        self._label(canvas, cargo_x + 8, 12, "CARGO MANIFEST", dim)
        self._draw_cargo(canvas, cargo_x + 8, 24, campaign.powerups, accent, dim)

        level_tag = world.config.level_name.upper()
        canvas.create_text(width // 2, 10, text=level_tag, fill=dim, font=self.FONT_TITLE)

        if world.invuln_remaining > 0.0:
            shield_alpha = "#66e8ff" if int(world.elapsed * 12) % 2 == 0 else "#2a8aa8"
            canvas.create_text(
                width // 2,
                48,
                text=f"◈ SHIELDS {world.invuln_remaining:0.2f}s ◈",
                fill=shield_alpha,
                font=self.FONT_SMALL,
            )

        if hud_alert:
            canvas.create_rectangle(0, self.PANEL_H, width, self.PANEL_H + 22, fill=palette.HUD_ALERT_BG, outline="")
            canvas.create_line(0, self.PANEL_H + 22, width, self.PANEL_H + 22, fill=palette.HUD_WARN, width=1)
            canvas.create_text(
                width // 2,
                self.PANEL_H + 11,
                text=hud_alert,
                fill=palette.HUD_WARN,
                font=("Courier New", 10, "bold"),
            )

    def _scanline(self, canvas: tk.Canvas, width: int) -> None:
        for y in range(0, self.PANEL_H, 4):
            canvas.create_line(0, y, width, y, fill=palette.HUD_SCANLINE)

    def _panel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        frame: str,
        accent: str,
    ) -> None:
        canvas.create_rectangle(x, y, x + w, y + h, outline=frame, width=1, fill="")
        canvas.create_line(x + 4, y + 2, x + 18, y + 2, fill=accent)
        canvas.create_line(x + w - 18, y + h - 2, x + w - 4, y + h - 2, fill=accent)

    def _label(self, canvas: tk.Canvas, x: float, y: float, text: str, color: str) -> None:
        canvas.create_text(x, y, anchor="w", text=text, fill=color, font=self.FONT_SMALL)

    def _draw_lives(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        lives: int,
        full: str,
        empty: str,
    ) -> None:
        for i in range(MAX_LIVES):
            color = full if i < lives else empty
            cx = x + i * 22 + 8
            canvas.create_polygon(
                cx,
                y + 2,
                cx + 7,
                y + 14,
                cx - 7,
                y + 14,
                fill=color,
                outline=full if i < lives else empty,
            )

    def _draw_hull_chunks(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        chunks: int,
        max_chunks: int,
        full: str,
        empty: str,
    ) -> None:
        for i in range(max_chunks):
            color = full if i < chunks else empty
            sx = x + i * 28
            canvas.create_rectangle(sx, y, sx + 22, y + 12, fill=color, outline=full if i < chunks else empty, width=1)
            canvas.create_line(sx + 4, y + 3, sx + 18, y + 3, fill=palette.HUD_BG if i < chunks else empty)

    def _boost_bar(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        fraction: float,
        fill: str,
        bg: str,
    ) -> None:
        canvas.create_rectangle(x, y, x + w, y + h, outline=bg, fill=bg)
        canvas.create_rectangle(x, y, x + w * max(0.0, min(1.0, fraction)), y + h, outline="", fill=fill)

    def _draw_cargo(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        powerups: set[PowerUpKind],
        accent: str,
        dim: str,
    ) -> None:
        if not powerups:
            canvas.create_text(x, y + 6, anchor="w", text="EMPTY", fill=dim, font=self.FONT)
            return
        labels = [POWERUP_LABELS[kind][:3].upper() for kind in sorted(powerups, key=lambda k: k.name)]
        canvas.create_text(x, y + 6, anchor="w", text=" · ".join(labels), fill=accent, font=self.FONT)
