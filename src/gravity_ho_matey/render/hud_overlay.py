from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE, MAX_LIVES
from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_HUD_TAGS, POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.session import LOOT_PULSE_SECONDS, LOOT_TOAST_SECONDS
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


class SciFiHudOverlay:
    """Retro sci-fi command overlay — bracketed panels, segmented readouts, CRT accents."""

    PANEL_H = 54
    ALERT_H = 22
    LOOT_BANNER_H = 40
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
        loot_toast_kind: PowerUpKind | None = None,
        loot_toast_is_new: bool = False,
        loot_toast_ttl: float = 0.0,
        camera_mode: CameraMode | None = None,
        camera_mode_flash: bool = False,
    ) -> None:
        width = world.config.viewport_width
        solar = world.config.level_theme == "solar"
        accent = palette.HUD_ACCENT_SOLAR if solar else palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG
        cargo_highlight = loot_toast_kind if loot_toast_ttl > 0.0 else None

        canvas.create_rectangle(0, 0, width, self.PANEL_H, fill=bg, outline="")
        canvas.create_line(0, self.PANEL_H, width, self.PANEL_H, fill=accent, width=1)
        self._scanline(canvas, width)

        self._panel(canvas, 8, 6, 148, 42, frame, accent)
        self._label(canvas, 16, 12, "CAPTAIN", dim)
        self._draw_lives(canvas, 16, 24, campaign.lives, accent, palette.HUD_LIFE_EMPTY)

        self._panel(canvas, 162, 6, 168, 42, frame, accent)
        self._label(canvas, 170, 12, "HULL INTEGRITY", dim)
        self._draw_hull_chunks(canvas, 170, 24, campaign.hull_chunks, CHUNKS_PER_LIFE, accent, palette.HUD_HULL_EMPTY)
        if campaign.powerups:
            self._draw_hull_fittings(canvas, 170, 38, campaign.powerups, dim, cargo_highlight)

        self._panel(canvas, 336, 6, 128, 42, frame, accent)
        self._label(canvas, 344, 12, "NAV BEACONS", dim)
        remaining = world.beacons_remaining
        total = len(world.beacons)
        beacon_color = palette.BEACON if remaining else palette.BEACON_COLLECTED
        canvas.create_text(
            344,
            30,
            anchor="w",
            text=f"{remaining:02d} / {total:02d}",
            fill=beacon_color,
            font=("Courier New", 14, "bold"),
        )

        self._panel(canvas, 470, 6, 118, 42, frame, accent)
        self._label(canvas, 478, 12, "CHRONO", dim)
        canvas.create_text(
            478,
            30,
            anchor="w",
            text=f"{world.elapsed:05.1f}s",
            fill=accent,
            font=("Courier New", 14, "bold"),
        )

        self._panel(canvas, 594, 6, 118, 42, frame, accent)
        self._label(canvas, 602, 12, "REACTOR", dim)
        boost_pct = int(world.ship.boost_energy * 100)
        boost_color = palette.HUD_BOOST if boost_pct > 25 else palette.HUD_WARN
        canvas.create_text(602, 30, anchor="w", text=f"{boost_pct:3d}%", fill=boost_color, font=("Courier New", 14, "bold"))
        self._boost_bar(canvas, 602, 38, 100, 6, world.ship.boost_energy, accent, dim)

        cargo_x = width - 156
        cargo_frame = self._powerup_color(cargo_highlight) if cargo_highlight else accent
        if cargo_highlight:
            canvas.create_rectangle(cargo_x - 2, 4, cargo_x + 150, 50, outline=cargo_frame, width=2)
        self._panel(canvas, cargo_x, 6, 148, 42, frame, cargo_frame if cargo_highlight else accent)
        self._label(canvas, cargo_x + 8, 12, "CARGO MANIFEST", dim)
        self._draw_cargo(
            canvas,
            cargo_x + 8,
            24,
            campaign.powerups,
            cargo_frame if cargo_highlight else accent,
            dim,
            highlight_kind=cargo_highlight,
        )

        if world.invuln_remaining > 0.0:
            shield_alpha = "#66e8ff" if int(world.elapsed * 12) % 2 == 0 else "#2a8aa8"
            canvas.create_text(
                width // 2,
                48,
                text=f"◈ SHIELDS {world.invuln_remaining:0.2f}s ◈",
                fill=shield_alpha,
                font=self.FONT_SMALL,
            )

        banner_y = self.PANEL_H
        if hud_alert:
            canvas.create_rectangle(0, banner_y, width, banner_y + self.ALERT_H, fill=palette.HUD_ALERT_BG, outline="")
            canvas.create_line(0, banner_y + self.ALERT_H, width, banner_y + self.ALERT_H, fill=palette.HUD_WARN, width=1)
            canvas.create_text(
                width // 2,
                banner_y + self.ALERT_H // 2,
                text=hud_alert,
                fill=palette.HUD_WARN,
                font=("Courier New", 10, "bold"),
            )
            banner_y += self.ALERT_H

        if loot_toast_kind is not None and loot_toast_ttl > 0.0:
            self._draw_loot_acquired_banner(
                canvas,
                width,
                banner_y,
                loot_toast_kind,
                loot_toast_is_new,
                loot_toast_ttl,
            )

    def draw_playfield_chrome(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        hud_top: float,
        *,
        camera_mode: CameraMode | None = None,
        camera_mode_flash: bool = False,
    ) -> None:
        """Sector + camera badges on the playfield — never stacked on command panels."""
        width = world.config.viewport_width
        solar = world.config.level_theme == "solar"
        accent = palette.HUD_ACCENT_SOLAR if solar else palette.HUD_ACCENT
        dim = palette.HUD_DIM
        y = hud_top + 8
        level_tag = world.config.level_name.upper()
        self._badge(
            canvas,
            10,
            y,
            anchor="nw",
            text=f"◈ {level_tag}",
            fill=accent,
            font=self.FONT_TITLE,
        )
        if camera_mode is not None:
            mode_color = accent if camera_mode_flash else dim
            self._badge(
                canvas,
                width - 10,
                y,
                anchor="ne",
                text=f"◈ {camera_mode.hud_label} ◈",
                fill=mode_color,
                font=self.FONT_SMALL,
            )

    @staticmethod
    def _badge(
        canvas: tk.Canvas,
        x: float,
        y: float,
        *,
        anchor: str,
        text: str,
        fill: str,
        font: tuple[str, int, str],
    ) -> None:
        pad_x, pad_y = 6, 3
        tid = canvas.create_text(x, y, anchor=anchor, text=text, fill=fill, font=font)
        bx0, by0, bx1, by1 = canvas.bbox(tid)
        if bx0 is None:
            return
        canvas.create_rectangle(
            bx0 - pad_x,
            by0 - pad_y,
            bx1 + pad_x,
            by1 + pad_y,
            fill=palette.HUD_BG,
            outline=fill,
            width=1,
        )
        canvas.tag_raise(tid)

    @staticmethod
    def _powerup_color(kind: PowerUpKind) -> str:
        return {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
        }.get(kind, palette.HUD_LOOT_NEW)

    def _draw_loot_acquired_banner(
        self,
        canvas: tk.Canvas,
        width: int,
        y: float,
        kind: PowerUpKind,
        is_new: bool,
        ttl: float,
    ) -> None:
        color = self._powerup_color(kind)
        elapsed = LOOT_TOAST_SECONDS - ttl
        pulse = is_new and elapsed < LOOT_PULSE_SECONDS and int(elapsed * 2.5) % 2 == 0
        border = palette.HUD_LOOT_NEW if pulse else color
        label = POWERUP_LABELS[kind].upper()
        tag = POWERUP_HUD_TAGS[kind]
        headline = "◈ LOOT ACQUIRED ◈" if is_new else "◈ SUPPLY SECURED ◈"
        subline = f"{tag} — {label}" if is_new else f"{label} — ALREADY FITTED"

        canvas.create_rectangle(0, y, width, y + self.LOOT_BANNER_H, fill=palette.HUD_LOOT_BG, outline="")
        canvas.create_rectangle(2, y + 2, width - 2, y + self.LOOT_BANNER_H - 2, outline=border, width=2)
        canvas.create_line(12, y + 6, 48, y + 6, fill=color)
        canvas.create_line(width - 48, y + self.LOOT_BANNER_H - 6, width - 12, y + self.LOOT_BANNER_H - 6, fill=color)
        canvas.create_text(
            width // 2,
            y + 13,
            text=headline,
            fill=palette.HUD_LOOT_NEW if is_new else color,
            font=("Courier New", 11, "bold"),
        )
        canvas.create_text(
            width // 2,
            y + 29,
            text=subline,
            fill=color,
            font=("Courier New", 13, "bold"),
        )

    def _scanline(self, canvas: tk.Canvas, width: int) -> None:
        hp.draw_scanlines(canvas, 0, 0, width, self.PANEL_H)

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
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent)

    def _label(self, canvas: tk.Canvas, x: float, y: float, text: str, color: str) -> None:
        hp.draw_panel_title(canvas, x, y, text, color=color)

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

    def _draw_hull_fittings(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        powerups: set[PowerUpKind],
        dim: str,
        highlight_kind: PowerUpKind | None,
    ) -> None:
        if not powerups:
            canvas.create_text(x, y, anchor="w", text="FITTINGS: —", fill=dim, font=self.FONT_SMALL)
            return
        canvas.create_text(x, y, anchor="w", text="FITTINGS:", fill=dim, font=self.FONT_SMALL)
        chip_x = x + 58
        for kind in sorted(powerups, key=lambda k: k.name):
            color = self._powerup_color(kind)
            tag = POWERUP_HUD_TAGS[kind]
            if highlight_kind is kind:
                canvas.create_rectangle(chip_x - 2, y - 2, chip_x + 44, y + 10, outline=color, width=1)
            canvas.create_rectangle(chip_x, y, chip_x + 40, y + 8, fill=color, outline=dim, width=1)
            canvas.create_text(chip_x + 4, y + 1, anchor="w", text=tag, fill=palette.HUD_BG, font=self.FONT_SMALL)
            chip_x += 46

    def _draw_cargo(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        powerups: set[PowerUpKind],
        accent: str,
        dim: str,
        *,
        highlight_kind: PowerUpKind | None = None,
    ) -> None:
        if not powerups:
            canvas.create_text(x, y + 6, anchor="w", text="EMPTY", fill=dim, font=self.FONT)
            return
        chip_x = x
        for kind in sorted(powerups, key=lambda k: k.name):
            color = self._powerup_color(kind)
            label = POWERUP_HUD_TAGS[kind]
            active = highlight_kind is kind
            if active:
                canvas.create_rectangle(chip_x - 2, y + 2, chip_x + 68, y + 18, outline=color, width=2)
            canvas.create_rectangle(chip_x, y + 4, chip_x + 64, y + 16, fill=color, outline=accent if active else dim, width=1)
            canvas.create_text(
                chip_x + 4,
                y + 6,
                anchor="w",
                text=label,
                fill=palette.HUD_BG,
                font=self.FONT,
            )
            chip_x += 70
