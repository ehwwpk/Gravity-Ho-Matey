from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE, MAX_LIVES
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks, powerup_hud_tag
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.entity_viz import draw_beacon_glyph, draw_gate_glyph
from gravity_ho_matey.render.world_draw import gravity_field_color

# Layout aligned with SciFiHudOverlay command deck (960×640).
_HEADER_H = 54
_CLEARED_H = 34
_FOOTER_H = 48
_MARGIN = 12
_SIDE_W = 164
_MAP_GAP = 10


@dataclass(frozen=True, slots=True)
class _MapTransform:
    scale: float
    origin_x: float
    origin_y: float
    clip_x0: float
    clip_y0: float
    clip_x1: float
    clip_y1: float
    strip_window: bool
    world_y0: float = 0.0
    world_y1: float = 0.0


class ChartMapOverlay:
    """Diegetic holo-table between sectors — matches in-flight command HUD chrome."""

    FONT = ("Courier New", 10, "bold")
    FONT_SMALL = ("Courier New", 8)
    FONT_DISPLAY = ("Courier New", 14, "bold")

    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        field: GravityField,
        *,
        campaign: CampaignState,
        upcoming_level_id: str,
        cleared_level_id: str | None = None,
        elapsed: float = 0.0,
    ) -> None:
        vw = world.config.viewport_width
        vh = world.config.viewport_height
        solar = world.config.level_theme == "solar"
        accent = palette.HUD_ACCENT_SOLAR if solar else palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG

        canvas.create_rectangle(0, 0, vw, vh, fill=palette.SOLAR_BG if solar else palette.BACKGROUND, outline="")
        self._starfield(canvas, vw, vh, dense=solar)
        self._draw_command_bar(canvas, world, campaign, cleared_level_id, accent, dim, frame, bg)
        self._draw_status_banner(canvas, vw, cleared_level_id, upcoming_level_id, elapsed, accent, dim)
        body_top = _HEADER_H + _CLEARED_H + 8
        body_bottom = vh - _FOOTER_H - 8
        body_h = body_bottom - body_top
        map_x = _MARGIN + _SIDE_W + _MAP_GAP
        map_w = vw - 2 * _MARGIN - 2 * _SIDE_W - 2 * _MAP_GAP
        self._draw_side_mission(canvas, _MARGIN, body_top, _SIDE_W, body_h, campaign, cleared_level_id, elapsed, accent, dim, frame)
        self._draw_holo_map(canvas, world, field, map_x, body_top, map_w, body_h, accent, dim, frame)
        self._draw_side_intel(canvas, vw - _MARGIN - _SIDE_W, body_top, _SIDE_W, body_h, world, upcoming_level_id, accent, dim, frame)
        self._draw_footer(canvas, vw, vh, accent, dim, frame, bg)

    def _draw_command_bar(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        campaign: CampaignState,
        cleared_level_id: str | None,
        accent: str,
        dim: str,
        frame: str,
        bg: str,
    ) -> None:
        width = world.config.viewport_width
        canvas.create_rectangle(0, 0, width, _HEADER_H, fill=bg, outline="")
        canvas.create_line(0, _HEADER_H, width, _HEADER_H, fill=accent, width=1)
        hp.draw_scanlines(canvas, 0, 0, width, _HEADER_H)

        hp.draw_panel(canvas, 8, 6, 148, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 16, 12, "CAPTAIN", color=dim)
        self._draw_lives(canvas, 16, 24, campaign.lives, accent)

        hp.draw_panel(canvas, 162, 6, 168, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 170, 12, "HULL INTEGRITY", color=dim)
        self._draw_hull_chunks(canvas, 170, 24, campaign.hull_chunks, accent)

        hp.draw_panel(canvas, 336, 6, 128, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 344, 12, "NAV BEACONS", color=dim)
        total = len(world.beacons)
        canvas.create_text(344, 30, anchor="w", text=f"{total:02d} REQ", fill=palette.BEACON, font=self.FONT_DISPLAY)

        hp.draw_panel(canvas, 470, 6, 118, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 478, 12, "SECTOR", color=dim)
        canvas.create_text(
            478,
            30,
            anchor="w",
            text=world.config.level_name[:14].upper(),
            fill=accent,
            font=("Courier New", 11, "bold"),
        )

        hp.draw_panel(canvas, 594, 6, 118, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 602, 12, "CHART MODE", color=dim)
        chart_mode = "HOLO PREVIEW" if cleared_level_id else "INITIAL BRIEF"
        canvas.create_text(602, 30, anchor="w", text=chart_mode, fill=accent, font=("Courier New", 11, "bold"))

        cargo_x = width - 156
        hp.draw_panel(canvas, cargo_x, 6, 148, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, cargo_x + 8, 12, "CARGO MANIFEST", color=dim)
        self._draw_cargo(canvas, cargo_x + 8, 24, campaign.powerup_stacks, accent, dim)

    def _draw_status_banner(
        self,
        canvas: tk.Canvas,
        width: int,
        cleared_level_id: str | None,
        upcoming_level_id: str,
        elapsed: float,
        accent: str,
        dim: str,
    ) -> None:
        y = _HEADER_H
        canvas.create_rectangle(0, y, width, y + _CLEARED_H, fill=palette.HUD_LOOT_BG, outline="")
        canvas.create_line(0, y + _CLEARED_H, width, y + _CLEARED_H, fill=accent, width=1)
        if cleared_level_id is None:
            upcoming = LEVEL_LABELS.get(upcoming_level_id, upcoming_level_id.upper())
            headline = f"◈  HOLO CHART OPEN — {upcoming.upper()}  ◈"
            headline_color = accent
        else:
            label = LEVEL_LABELS.get(cleared_level_id, cleared_level_id.upper())
            headline = f"◈  {label.upper()} CLEARED — {elapsed:05.1f}s  ◈"
            headline_color = palette.HUD_LOOT_NEW
        canvas.create_text(
            width // 2,
            y + 11,
            text=headline,
            fill=headline_color,
            font=("Courier New", 11, "bold"),
        )
        canvas.create_text(
            width // 2,
            y + 26,
            text="Review sector chart · Enter to launch · Esc for title",
            fill=dim,
            font=self.FONT_SMALL,
        )

    def _draw_side_mission(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        campaign: CampaignState,
        cleared_level_id: str | None,
        elapsed: float,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        if cleared_level_id is None:
            hp.draw_panel_title(canvas, x + 10, y + 10, "BRIEFING", color=dim)
            rows = [
                ("OBJECTIVE", "Collect all beacons"),
                ("", "Unlock exit gate"),
                ("CONTROLS", "Arrows · thrust · fire"),
                ("HAZARDS", "Gravity wells"),
                ("", "Drifting asteroids"),
                ("STATUS", "Ready to launch"),
            ]
            ry = y + 28
            for label, value in rows:
                if label:
                    hp.draw_panel_title(canvas, x + 10, ry, label, color=dim)
                    ry += 12
                canvas.create_text(x + 10, ry, anchor="w", text=value, fill=accent, font=self.FONT)
                ry += 20 if label else 16
            return

        hp.draw_panel_title(canvas, x + 10, y + 10, "MISSION LOG", color=dim)
        cleared = LEVEL_LABELS.get(cleared_level_id, cleared_level_id)
        rows = [
            ("LAST SECTOR", cleared),
            ("CLEAR TIME", f"{elapsed:05.1f}s"),
            ("LIVES", str(campaign.lives)),
            ("HULL", f"{campaign.hull_chunks}/{CHUNKS_PER_LIFE}"),
        ]
        ry = y + 28
        for label, value in rows:
            hp.draw_panel_title(canvas, x + 10, ry, label, color=dim)
            canvas.create_text(x + 10, ry + 12, anchor="w", text=value, fill=accent, font=self.FONT)
            ry += 32
        if campaign.powerup_stacks:
            hp.draw_panel_title(canvas, x + 10, ry + 4, "FITTINGS", color=dim)
            chip_x = x + 10
            for kind in sorted(campaign.powerup_stacks.keys(), key=lambda k: k.name):
                count = campaign.powerup_stacks[kind]
                if count <= 0:
                    continue
                color = self._powerup_color(kind)
                tag = powerup_hud_tag(kind, count)
                chip_w = 42 + (10 if count > 1 else 0)
                canvas.create_rectangle(chip_x, ry + 18, chip_x + chip_w, ry + 28, fill=color, outline=dim)
                canvas.create_text(chip_x + 4, ry + 19, anchor="w", text=tag, fill=palette.HUD_BG, font=self.FONT_SMALL)
                chip_x += chip_w + 4

    def _draw_side_intel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        world: GameWorld,
        upcoming_level_id: str,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        cfg = world.config
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 10, y + 10, "SECTOR INTEL", color=dim)
        strip = cfg.height > cfg.viewport_height * 1.25
        enemies = sum(1 for e in world.enemies if e.alive)
        rows = [
            ("CHART ID", upcoming_level_id.upper()),
            ("THEME", cfg.level_theme.upper()),
            ("EXTENT", f"{cfg.width} × {cfg.height}"),
            ("BEACONS", str(len(world.beacons))),
            ("WELLS", str(len(world.wells))),
            ("PATROLS", str(enemies) if enemies else "—"),
            ("ASTEROIDS", str(len(world.asteroids))),
            ("BOUNDS", "OPEN" if cfg.open_bounds else "BOUNDED"),
        ]
        ry = y + 28
        for label, value in rows:
            hp.draw_panel_title(canvas, x + 10, ry, label, color=dim)
            canvas.create_text(x + 10, ry + 12, anchor="w", text=value, fill=accent, font=self.FONT)
            ry += 30
        hp.draw_panel_title(canvas, x + 10, ry + 6, "LEGEND", color=dim)
        legend_y = ry + 22
        for glyph, text, color in (
            ("◆", "Beacon", palette.BEACON),
            ("◎", "Gravity well", palette.WELL),
            ("●", "Singularity", palette.BLACK_HOLE_RING),
            ("▣", "Exit gate", palette.GATE_LOCKED),
            ("▲", "Spawn", palette.SHIP),
            ("×", "Patrol", palette.ENEMY),
            ("⬡", "Asteroid", palette.ASTEROID_EDGE),
        ):
            canvas.create_text(x + 14, legend_y, anchor="w", text=glyph, fill=color, font=self.FONT)
            canvas.create_text(x + 30, legend_y, anchor="w", text=text, fill=dim, font=self.FONT_SMALL)
            legend_y += 16
        if strip:
            canvas.create_text(
                x + 10,
                y + h - 22,
                anchor="w",
                text="Vertical strip — holo shows spawn window",
                fill=dim,
                font=self.FONT_SMALL,
            )

    def _draw_holo_map(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        field: GravityField,
        x: float,
        y: float,
        w: float,
        h: float,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill="#060810")
        hp.draw_panel_title(canvas, x + 12, y + 10, world.config.level_name.upper(), color=dim)
        inner_x = x + 14
        inner_y = y + 28
        inner_w = w - 28
        inner_h = h - 42
        canvas.create_rectangle(inner_x, inner_y, inner_x + inner_w, inner_y + inner_h, fill="#040810", outline=frame)
        transform = self._map_transform(world, inner_x, inner_y, inner_w, inner_h)
        self._draw_map_field(canvas, field, transform)
        self._draw_map_entities(canvas, world, transform, dim)
        if transform.strip_window:
            self._draw_strip_window_chrome(canvas, world, transform, accent, dim)
        hp.draw_scanlines(canvas, inner_x, inner_y, inner_w, inner_h)

    def _map_transform(
        self,
        world: GameWorld,
        inner_x: float,
        inner_y: float,
        inner_w: float,
        inner_h: float,
    ) -> _MapTransform:
        ww = float(world.config.width)
        wh = float(world.config.height)
        aspect = wh / max(1.0, ww)
        clip = (inner_x + 2, inner_y + 2, inner_x + inner_w - 2, inner_y + inner_h - 2)

        if aspect > 1.35:
            scale = inner_w / ww
            view_h = inner_h / scale
            center_y = world.ship.pos.y
            y0 = max(0.0, min(center_y - view_h * 0.42, wh - view_h))
            y1 = min(wh, y0 + view_h)
            return _MapTransform(
                scale=scale,
                origin_x=inner_x,
                origin_y=inner_y + inner_h,
                clip_x0=clip[0],
                clip_y0=clip[1],
                clip_x1=clip[2],
                clip_y1=clip[3],
                strip_window=True,
                world_y0=y0,
                world_y1=y1,
            )

        scale = min(inner_w / ww, inner_h / wh)
        map_w = ww * scale
        map_h = wh * scale
        ox = inner_x + (inner_w - map_w) * 0.5
        oy = inner_y + (inner_h - map_h) * 0.5
        return _MapTransform(
            scale=scale,
            origin_x=ox,
            origin_y=oy,
            clip_x0=clip[0],
            clip_y0=clip[1],
            clip_x1=clip[2],
            clip_y1=clip[3],
            strip_window=False,
        )

    def _world_to_map(self, p: Vec2, t: _MapTransform) -> tuple[float, float] | None:
        if t.strip_window:
            if p.y < t.world_y0 or p.y > t.world_y1:
                return None
            mx = t.origin_x + p.x * t.scale
            my = t.origin_y - (p.y - t.world_y0) * t.scale
        else:
            mx = t.origin_x + p.x * t.scale
            my = t.origin_y + p.y * t.scale
        if mx < t.clip_x0 or mx > t.clip_x1 or my < t.clip_y0 or my > t.clip_y1:
            return None
        return mx, my

    def _draw_map_field(self, canvas: tk.Canvas, field: GravityField, t: _MapTransform) -> None:
        step = 2 if field.rows > 32 else 1
        for row in range(0, field.rows, step):
            for col in range(0, field.cols, step):
                cell = field.cell_at(col, row)
                if cell.magnitude <= 1e-6:
                    continue
                wx = field.origin.x + col * field.cell_size + field.cell_size * 0.5
                wy = field.origin.y + row * field.cell_size + field.cell_size * 0.5
                hit = self._world_to_map(Vec2(wx, wy), t)
                if hit is None:
                    continue
                mx, my = hit
                size = field.cell_size * step * t.scale * 0.92
                norm = cell.magnitude / field.max_magnitude
                tone = gravity_field_color(norm)
                canvas.create_rectangle(mx, my, mx + size, my + size * 0.85, fill=tone, outline="")

    def _draw_map_entities(self, canvas: tk.Canvas, world: GameWorld, t: _MapTransform, dim: str) -> None:
        glyph_scale = max(0.35, min(0.85, t.scale * 1.1))

        from gravity_ho_matey.render.asteroid_viz import draw_map_asteroid_glyph
        from gravity_ho_matey.render.lighting import LightRig

        map_rig = LightRig.for_play(theme=world.config.level_theme, camera_mode=CameraMode.TACTICAL)

        for asteroid in world.asteroids:
            hit = self._world_to_map(asteroid.pos, t)
            if hit is None:
                continue
            draw_map_asteroid_glyph(
                canvas,
                Vec2(hit[0], hit[1]),
                asteroid,
                scale=max(0.22, min(0.55, glyph_scale * 0.55)),
                rig=map_rig,
            )

        for well in world.wells:
            hit = self._world_to_map(well.pos, t)
            if hit is None:
                continue
            mx, my = hit
            rr = max(5.0, well.radius * t.scale * 0.32)
            if well.kind == "black_hole":
                color = palette.BLACK_HOLE_RING
            elif well.kind == "planet":
                color = palette.PLANET_WELL
            else:
                color = palette.WELL
            canvas.create_oval(mx - rr, my - rr, mx + rr, my + rr, outline=color, width=2)
            if well.label and rr >= 6:
                canvas.create_text(mx, my - rr - 6, text=well.label, fill=dim if well.kind != "planet" else palette.PLANET_LABEL, font=self.FONT_SMALL)

        for beacon in world.beacons:
            hit = self._world_to_map(beacon.pos, t)
            if hit is None:
                continue
            draw_beacon_glyph(canvas, hit[0], hit[1], collected=False, scale=glyph_scale, show_ring=True)

        gate = world.finish_gate.rect
        gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        hit = self._world_to_map(gc, t)
        if hit is not None:
            solar = world.config.level_theme == "solar"
            draw_gate_glyph(
                canvas,
                hit[0],
                hit[1],
                size=max(gate.w, gate.h),
                unlocked=False,
                solar=solar,
                scale=glyph_scale,
            )

        for enemy in world.enemies:
            if not enemy.alive:
                continue
            hit = self._world_to_map(enemy.pos, t)
            if hit is None:
                continue
            mx, my = hit
            r = max(4.0, enemy.radius * t.scale * 0.35)
            canvas.create_oval(mx - r, my - r, mx + r, my + r, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=1)

        spawn = self._world_to_map(world.ship.pos, t)
        if spawn is not None:
            sx, sy = spawn
            canvas.create_polygon(
                sx,
                sy - 7,
                sx + 6,
                sy + 5,
                sx - 6,
                sy + 5,
                fill=palette.SHIP,
                outline="#fff0b5",
                width=2,
            )
            canvas.create_text(sx, sy + 14, text="SPAWN", fill=palette.SHIP, font=self.FONT_SMALL)

    def _draw_strip_window_chrome(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        t: _MapTransform,
        accent: str,
        dim: str,
    ) -> None:
        wh = float(world.config.height)
        if t.world_y0 > 4.0:
            canvas.create_text(
                t.clip_x0 + 8,
                t.clip_y0 + 10,
                anchor="w",
                text=f"↑ {int(t.world_y0)}u hidden",
                fill=dim,
                font=self.FONT_SMALL,
            )
        if t.world_y1 < wh - 4.0:
            canvas.create_text(
                t.clip_x0 + 8,
                t.clip_y1 - 10,
                anchor="w",
                text=f"↓ {int(wh - t.world_y1)}u below",
                fill=dim,
                font=self.FONT_SMALL,
            )
        canvas.create_text(
            t.clip_x1 - 8,
            t.clip_y0 + 10,
            anchor="e",
            text=f"WINDOW {int(t.world_y1 - t.world_y0)}u",
            fill=accent,
            font=self.FONT_SMALL,
        )

    def _draw_footer(self, canvas: tk.Canvas, vw: int, vh: int, accent: str, dim: str, frame: str, bg: str) -> None:
        y = vh - _FOOTER_H
        hp.draw_panel(canvas, _MARGIN, y, vw - 2 * _MARGIN, _FOOTER_H - 4, frame=frame, accent=accent, fill=bg)
        hp.draw_key_value_row(canvas, _MARGIN + 16, y + 14, "Enter", "Launch course", accent=accent, dim=dim, key_width=72.0)
        hp.draw_key_value_row(canvas, _MARGIN + 220, y + 14, "Esc", "Return to title", accent=accent, dim=dim, key_width=72.0)
        hp.draw_key_value_row(canvas, _MARGIN + 420, y + 14, "V", "Tactical / chase cam in flight", accent=accent, dim=dim, key_width=72.0)

    @staticmethod
    def _powerup_color(kind: PowerUpKind) -> str:
        return {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
        }.get(kind, palette.HUD_LOOT_NEW)

    @staticmethod
    def _draw_lives(canvas: tk.Canvas, x: float, y: float, lives: int, accent: str) -> None:
        for i in range(MAX_LIVES):
            color = accent if i < lives else palette.HUD_LIFE_EMPTY
            cx = x + i * 22 + 8
            canvas.create_polygon(cx, y + 2, cx + 7, y + 14, cx - 7, y + 14, fill=color, outline=accent if i < lives else palette.HUD_LIFE_EMPTY)

    @staticmethod
    def _draw_hull_chunks(canvas: tk.Canvas, x: float, y: float, chunks: int, accent: str) -> None:
        for i in range(CHUNKS_PER_LIFE):
            color = accent if i < chunks else palette.HUD_HULL_EMPTY
            sx = x + i * 28
            canvas.create_rectangle(sx, y, sx + 22, y + 12, fill=color, outline=accent if i < chunks else palette.HUD_HULL_EMPTY, width=1)

    @staticmethod
    def _draw_cargo(canvas: tk.Canvas, x: float, y: float, stacks: PowerUpStacks, accent: str, dim: str) -> None:
        if not stacks:
            canvas.create_text(x, y + 6, anchor="w", text="EMPTY", fill=dim, font=ChartMapOverlay.FONT)
            return
        chip_x = x
        for kind in sorted(stacks.keys(), key=lambda k: k.name):
            count = stacks[kind]
            if count <= 0:
                continue
            color = ChartMapOverlay._powerup_color(kind)
            tag = powerup_hud_tag(kind, count)
            chip_w = 64 + (12 if count > 1 else 0)
            canvas.create_rectangle(chip_x, y + 4, chip_x + chip_w, y + 16, fill=color, outline=accent, width=1)
            canvas.create_text(chip_x + 4, y + 6, anchor="w", text=tag, fill=palette.HUD_BG, font=ChartMapOverlay.FONT)
            chip_x += chip_w + 6

    @staticmethod
    def _starfield(canvas: tk.Canvas, width: int, height: int, *, dense: bool) -> None:
        count = 120 if dense else 70
        for i in range(count):
            sx = (i * 83 + 17) % width
            sy = (i * 47 + 31) % height
            tone = palette.CHASE_STAR_FAR if dense and i % 5 == 0 else "#294764"
            canvas.create_rectangle(sx, sy, sx + 2, sy + 2, fill=tone, outline="")
