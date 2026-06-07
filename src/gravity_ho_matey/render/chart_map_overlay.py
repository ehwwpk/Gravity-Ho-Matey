from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, MAX_LIVES
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks, powerup_hud_tag
from gravity_ho_matey.gameplay.weapon_kinds import WEAPON_TRACK_SHORT
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.holo_shop_overlay import HoloShopOverlay
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.entity_viz import draw_gate_glyph
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button
from gravity_ho_matey.render.world_draw import gravity_field_color

# Layout aligned with SciFiHudOverlay command deck (960×640).
_HEADER_H = 54
_CLEARED_H = 34
_FOOTER_H = 82
_SHOP_CTA_H = 38
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

    def __init__(self) -> None:
        self.hits = MenuHitMap()
        self._shop = HoloShopOverlay()

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
        hover_id: str | None = None,
        shop_open: bool = False,
    ) -> None:
        self.hits.clear()
        vw = world.config.viewport_width
        vh = world.config.viewport_height
        solar = world.config.level_theme == "solar"
        drift = world.config.level_theme == "drift"
        rift = world.config.level_theme == "rift"
        siege = world.config.level_theme == "siege"
        accent = (
            palette.HUD_ACCENT_SOLAR
            if solar
            else palette.RIFT_HUD_ACCENT
            if rift
            else palette.SIEGE_HUD_ACCENT
            if siege
            else palette.HUD_ACCENT
        )
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG

        canvas.create_rectangle(
            0,
            0,
            vw,
            vh,
            fill=palette.SOLAR_BG if solar else palette.RIFT_BG if rift else palette.SIEGE_BG if siege else palette.BACKGROUND,
            outline="",
        )
        self._starfield(canvas, vw, vh, dense=solar or drift or rift or siege)
        self._draw_command_bar(canvas, world, campaign, cleared_level_id, accent, dim, frame, bg)
        self._draw_status_banner(canvas, vw, cleared_level_id, upcoming_level_id, elapsed, accent, dim)
        body_top = _HEADER_H + _CLEARED_H + 8
        footer_top = vh - _FOOTER_H - 8
        body_bottom = footer_top - _SHOP_CTA_H - 6
        body_h = body_bottom - body_top
        map_x = _MARGIN + _SIDE_W + _MAP_GAP
        map_w = vw - 2 * _MARGIN - 2 * _SIDE_W - 2 * _MAP_GAP
        self._draw_side_mission(
            canvas,
            _MARGIN,
            body_top,
            _SIDE_W,
            body_h,
            campaign,
            cleared_level_id,
            elapsed,
            upcoming_level_id,
            world,
            accent,
            dim,
            frame,
        )
        self._draw_holo_map(canvas, world, field, map_x, body_top, map_w, body_h, accent, dim, frame, elapsed)
        self._draw_side_intel(
            canvas,
            vw - _MARGIN - _SIDE_W,
            body_top,
            _SIDE_W,
            body_h,
            world,
            upcoming_level_id,
            accent,
            dim,
            frame,
        )
        self._draw_shop_cta(
            canvas,
            vw,
            footer_top - _SHOP_CTA_H - 4,
            _SHOP_CTA_H,
            campaign,
            accent,
            dim,
            frame,
            hover_id,
            elapsed,
        )
        self._draw_footer(canvas, vw, vh, footer_top, accent, dim, frame, bg, hover_id)
        if shop_open:
            self._shop.draw(
                canvas,
                vw=vw,
                vh=vh,
                campaign=campaign,
                hits=self.hits,
                hover_id=hover_id,
                elapsed=elapsed,
            )

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
        self._draw_hull_chunks(canvas, 170, 24, campaign.hull_chunks, campaign.max_hull_chunks_per_life, accent)

        hp.draw_panel(canvas, 336, 6, 128, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 344, 12, "NAV BEACONS", color=dim)
        total = len(world.beacons)
        if total == 0:
            beacon_text = "EXIT ONLY"
            beacon_color = palette.GATE_OPEN
        else:
            beacon_text = f"{total:02d} REQ"
            beacon_color = palette.BEACON
        canvas.create_text(344, 30, anchor="w", text=beacon_text, fill=beacon_color, font=self.FONT_DISPLAY)

        hp.draw_panel(canvas, 470, 6, 118, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 478, 12, "SECTOR", color=dim)
        draw_fitted_text(
            canvas,
            478,
            30,
            world.config.level_name.upper(),
            max_width=104,
            color=accent,
            font=("Courier New", 10, "bold"),
        )

        hp.draw_panel(canvas, 594, 6, 118, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 602, 12, "CHART MODE", color=dim)
        chart_mode = "HOLO PREVIEW" if cleared_level_id else "INITIAL BRIEF"
        draw_fitted_text(
            canvas,
            602,
            30,
            chart_mode,
            max_width=104,
            color=accent,
            font=("Courier New", 10, "bold"),
        )

        cargo_x = width - 156
        hp.draw_panel(canvas, cargo_x, 6, 148, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, cargo_x + 8, 12, "TREASURY", color=dim)
        canvas.create_text(
            cargo_x + 140,
            12,
            anchor="e",
            text=f"★ {campaign.jewels}",
            fill=palette.JEWEL_CORE,
            font=self.FONT,
        )
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
            short = upcoming.split(" — ", 1)[-1] if " — " in upcoming else upcoming
            headline = f"◈  CHART BRIEF — {short.upper()}  ◈"
            headline_color = accent
        else:
            label = LEVEL_LABELS.get(cleared_level_id, cleared_level_id.upper())
            short = label.split(" — ", 1)[-1] if " — " in label else label
            headline = f"◈  {short.upper()} CLEARED · {elapsed:05.1f}s  ◈"
            headline_color = palette.HUD_LOOT_NEW
        draw_fitted_text(
            canvas,
            width // 2,
            y + 11,
            headline,
            max_width=width - 40,
            color=headline_color,
            font=("Courier New", 11, "bold"),
            anchor="center",
        )
        canvas.create_text(
            width // 2,
            y + 26,
            text="Launch when ready · Esc returns to nav station",
            fill=dim,
            font=self.FONT_SMALL,
        )

    @staticmethod
    def _draw_kv_line(
        canvas: tk.Canvas,
        x: float,
        y: float,
        width: float,
        label: str,
        value: str,
        *,
        accent: str,
        dim: str,
        value_color: str | None = None,
        row_h: float = 30.0,
    ) -> float:
        """Label + clipped value row; returns next y."""
        inner = max(8.0, width - 20.0)
        hp.draw_panel_title(canvas, x + 10, y, label, color=dim)
        draw_fitted_text(
            canvas,
            x + 10,
            y + 12,
            value,
            max_width=inner,
            color=value_color or accent,
            font=ChartMapOverlay.FONT,
        )
        return y + row_h

    @staticmethod
    def _draw_body_lines(
        canvas: tk.Canvas,
        x: float,
        y: float,
        width: float,
        lines: tuple[str, ...],
        *,
        accent: str,
        line_h: float = 16.0,
    ) -> float:
        inner = max(8.0, width - 20.0)
        ry = y
        for line in lines:
            if not line:
                continue
            draw_fitted_text(
                canvas,
                x + 10,
                ry,
                line,
                max_width=inner,
                color=accent,
                font=ChartMapOverlay.FONT,
            )
            ry += line_h
        return ry

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
        upcoming_level_id: str,
        world: GameWorld,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        if cleared_level_id is None:
            hp.draw_panel_title(canvas, x + 10, y + 10, "BRIEFING", color=dim)
            if upcoming_level_id == "siege":
                rows = [
                    ("OBJECTIVE", "Eliminate 12 hostiles"),
                    ("", "Exit opens on roster clear"),
                    ("", "Station optional · blocks lane"),
                    ("ALLIES", "12 wing escorts"),
                    ("", "Push through spiral belt"),
                    ("HAZARDS", "Hostile station · tractor"),
                    ("", "Reinforcements ~17s"),
                    ("", "4 black hole pockets"),
                    ("STATUS", "Ready to launch"),
                ]
            elif upcoming_level_id == "rift":
                rows = [
                    ("OBJECTIVE", "Race boost braids north"),
                    ("", "Kill Brood-Mother"),
                    ("", "Portal opens on kill"),
                    ("ALLIES", "2 wing escorts"),
                    ("", "Cover fire · not ace pilots"),
                    ("HAZARDS", "Void pockets off-lane"),
                    ("", "Turbo pads · road squids"),
                    ("STATUS", "Ready to launch"),
                ]
            elif upcoming_level_id == "drift":
                rows = [
                    ("OBJECTIVE", "Reach north exit gate"),
                    ("", "No beacons — gate open"),
                    ("HAZARDS", "7 concentric belts"),
                    ("", "Titan black holes"),
                    ("", "Void squid wrap"),
                    ("STATUS", "Ready to launch"),
                ]
            elif upcoming_level_id == "solar":
                rows = [
                    ("OBJECTIVE", "Collect all beacons"),
                    ("", "Cross the singularity"),
                    ("HAZARDS", "Patrol skiffs · maw"),
                    ("", "Drifting asteroids"),
                    ("STATUS", "Ready to launch"),
                ]
            else:
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
                    ry += 13
                if value:
                    draw_fitted_text(
                        canvas,
                        x + 10,
                        ry,
                        value,
                        max_width=w - 20,
                        color=accent,
                        font=self.FONT,
                    )
                    ry += 18 if label else 15
            return

        hp.draw_panel_title(canvas, x + 10, y + 10, "MISSION LOG", color=dim)
        cleared = LEVEL_LABELS.get(cleared_level_id, cleared_level_id)
        short_cleared = cleared.split(" — ", 1)[-1] if " — " in cleared else cleared
        ry = y + 28
        ry = self._draw_kv_line(canvas, x, ry, w, "LAST SECTOR", short_cleared, accent=accent, dim=dim)
        ry = self._draw_kv_line(canvas, x, ry, w, "CLEAR TIME", f"{elapsed:05.1f}s", accent=accent, dim=dim)
        ry = self._draw_kv_line(canvas, x, ry, w, "LIVES", str(campaign.lives), accent=accent, dim=dim)
        ry = self._draw_kv_line(
            canvas,
            x,
            ry,
            w,
            "HULL",
            f"{campaign.hull_chunks}/{campaign.max_hull_chunks_per_life}",
            accent=accent,
            dim=dim,
        )
        ry = self._draw_kv_line(
            canvas,
            x,
            ry,
            w,
            "TREASURY",
            f"★ {campaign.jewels}",
            accent=accent,
            dim=dim,
            value_color=palette.JEWEL_CORE,
        )
        if campaign.rubber_hull_charges > 0:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "RUBBER HULL",
                f"{campaign.rubber_hull_charges} bounces left",
                accent=accent,
                dim=dim,
                value_color=palette.PICKUP_RUBBER,
            )
        if campaign.weapon_track is not None:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "WEAPON DOCTRINE",
                WEAPON_TRACK_SHORT[campaign.weapon_track],
                accent=accent,
                dim=dim,
                value_color=palette.WEAPON_LASER_MID,
            )
        if campaign.drone_wingman_pending:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "GUARDIAN DRONE",
                "Deploys next sector",
                accent=accent,
                dim=dim,
                value_color=palette.DRONE_CORE,
            )
        elif campaign.drone_wingman_hp > 0:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "GUARDIAN DRONE",
                f"{campaign.drone_wingman_hp}/{campaign.drone_hits_max} HP escort",
                accent=accent,
                dim=dim,
                value_color=palette.DRONE_CORE,
            )
        if campaign.powerup_stacks:
            hp.draw_panel_title(canvas, x + 10, ry + 2, "FITTINGS", color=dim)
            chip_y = ry + 16
            for kind in sorted(campaign.powerup_stacks.keys(), key=lambda k: k.name):
                count = campaign.powerup_stacks[kind]
                if count <= 0:
                    continue
                color = self._powerup_color(kind)
                tag = powerup_hud_tag(kind, count)
                chip_w = w - 20
                canvas.create_rectangle(x + 10, chip_y, x + 10 + chip_w, chip_y + 14, fill=color, outline=dim)
                draw_fitted_text(
                    canvas,
                    x + 14,
                    chip_y + 2,
                    tag,
                    max_width=chip_w - 8,
                    color=palette.HUD_BG,
                    font=self.FONT_SMALL,
                )
                chip_y += 16

    def _draw_shop_cta(
        self,
        canvas: tk.Canvas,
        vw: int,
        y: float,
        h: float,
        campaign: CampaignState,
        accent: str,
        dim: str,
        frame: str,
        hover_id: str | None,
        elapsed: float,
    ) -> None:
        x = _MARGIN
        w = vw - 2 * _MARGIN
        pulse = 0.72 + 0.28 * math.sin(elapsed * 3.2)
        border = palette.JEWEL_CORE if hover_id == "shop_open" else accent
        fill = "#122838" if hover_id == "shop_open" else "#0e2030"
        canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=border, width=2 if pulse > 0.88 else 1)
        canvas.create_line(x + 6, y + 2, x + 36, y + 2, fill=palette.JEWEL_CORE if pulse > 0.8 else accent)
        canvas.create_line(x + w - 36, y + h - 2, x + w - 6, y + h - 2, fill=palette.JEWEL_CORE if pulse > 0.8 else accent)
        self.hits.add("shop_open", x, y, w, h)
        label = f"◈  OPEN HOLO BAZAAR  ·  ★ {campaign.jewels} TREASURY  ·  CLICK TO TRADE FITTINGS  ◈"
        draw_fitted_text(
            canvas,
            x + w / 2,
            y + h / 2 - 1,
            label,
            max_width=w - 24,
            color=palette.JEWEL_CORE if hover_id == "shop_open" else accent,
            font=("Courier New", 11, "bold"),
            anchor="center",
        )
        canvas.create_text(
            x + w - 12,
            y + h / 2,
            anchor="e",
            text="▶",
            fill=border,
            font=hp.FONT_BODY_BOLD,
        )

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
        hostiles = sum(1 for e in world.enemies if e.alive)
        squids = sum(1 for e in world.enemies if e.alive and e.kind is EnemyKind.SQUID)
        roster = world.roster_enemies_total if world.config.exit_requires_roster_clear else 0
        hostile_label = "SQUIDS" if squids and squids == hostiles else "HOSTILES"
        intel_rows: list[tuple[str, str]] = [
            ("CHART ID", upcoming_level_id.upper()),
            ("THEME", cfg.level_theme.upper()),
            ("EXTENT", f"{cfg.width}×{cfg.height}"),
            ("BEACONS", str(len(world.beacons)) if world.beacons else "NONE"),
            ("WELLS", str(len(world.wells))),
            (hostile_label, str(hostiles) if hostiles else "—"),
        ]
        if roster:
            intel_rows.append(("ROSTER", f"{world.roster_enemies_remaining}/{roster}"))
        if world.allies:
            alive_wings = sum(1 for a in world.allies if a.alive)
            intel_rows.append(("ALLIES", f"{alive_wings}/{len(world.allies)}"))
        if world.space_station is not None and world.space_station.alive:
            intel_rows.append(("STATION", f"{world.space_station.hits_remaining} HP"))
        intel_rows.extend(
            [
                ("ASTEROIDS", str(len(world.asteroids))),
                ("BOUNDS", "OPEN" if cfg.open_bounds else "BOUNDED"),
            ]
        )
        ry = y + 28
        for label, value in intel_rows:
            ry = self._draw_kv_line(canvas, x, ry, w, label, value, accent=accent, dim=dim, row_h=28.0)
        hp.draw_panel_title(canvas, x + 10, ry + 4, "LEGEND", color=dim)
        legend_y = ry + 20
        legend_items = (
            ("◆", "Beacon", palette.BEACON),
            ("◎", "Well", palette.WELL),
            ("●", "Singularity", palette.BLACK_HOLE_RING),
            ("▣", "Gate", palette.GATE_LOCKED),
            ("▲", "Spawn", palette.SHIP),
            ("×", "Patrol", palette.ENEMY),
            ("◉", "Squid", palette.SQUID_CORE),
            ("⬡", "Asteroid", palette.ASTEROID_EDGE),
        )
        col_w = (w - 24) * 0.5
        for index, (glyph, text, color) in enumerate(legend_items):
            col = index % 2
            row = index // 2
            lx = x + 10 + col * col_w
            ly = legend_y + row * 15
            canvas.create_text(lx + 4, ly, anchor="w", text=glyph, fill=color, font=self.FONT)
            draw_fitted_text(
                canvas,
                lx + 20,
                ly,
                text,
                max_width=col_w - 24,
                color=dim,
                font=self.FONT_SMALL,
            )
        if strip:
            draw_fitted_text(
                canvas,
                x + 10,
                y + h - 18,
                "Vertical strip — spawn window on holo",
                max_width=w - 20,
                color=dim,
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
        elapsed: float,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill="#060810")
        draw_holo_corners(canvas, x, y, w, h, accent=accent, elapsed=elapsed)
        draw_fitted_text(
            canvas,
            x + 12,
            y + 10,
            world.config.level_name.upper(),
            max_width=w - 24,
            color=dim,
            font=hp.FONT_SMALL,
        )
        inner_x = x + 14
        inner_y = y + 28
        inner_w = w - 28
        inner_h = h - 42
        canvas.create_rectangle(inner_x, inner_y, inner_x + inner_w, inner_y + inner_h, fill="#040810", outline=frame)
        transform = self._map_transform(world, inner_x, inner_y, inner_w, inner_h)
        self._draw_map_field(canvas, field, transform)
        self._draw_map_entities(canvas, world, transform, dim, elapsed)
        if world.membrane_layout is not None:
            from gravity_ho_matey.render.membrane_viz import draw_membrane_holo_ribbons

            def to_screen(pos):
                sx = transform.origin_x + pos.x * transform.scale
                sy = transform.origin_y - pos.y * transform.scale
                return sx, sy

            draw_membrane_holo_ribbons(canvas, world.membrane_layout, to_screen=to_screen, accent=accent)
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

    def _draw_map_entities(self, canvas: tk.Canvas, world: GameWorld, t: _MapTransform, dim: str, elapsed: float) -> None:
        glyph_scale = max(0.35, min(0.85, t.scale * 1.1))

        from gravity_ho_matey.render.asteroid_viz import draw_map_asteroid_glyph
        from gravity_ho_matey.render.beacon_viz import beacon_seed_from_pos, draw_beacon_play
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
            mx, my = hit
            draw_beacon_play(
                canvas,
                mx,
                my,
                beacon,
                scale=glyph_scale,
                rig=map_rig,
                elapsed=elapsed,
                seed=beacon_seed_from_pos(beacon.pos),
                spark_orbits=False,
            )

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
            if enemy.kind is EnemyKind.SQUID:
                for i in range(4):
                    angle = enemy.facing_angle + (6.28318 * i / 4)
                    tx = mx + math.cos(angle) * r * 1.6
                    ty = my + math.sin(angle) * r * 1.6
                    canvas.create_line(mx, my, tx, ty, fill=palette.SQUID_TENTACLE, width=1)
                canvas.create_oval(mx - r, my - r, mx + r, my + r, fill=palette.SQUID_BODY, outline=palette.SQUID_CORE, width=1)
            else:
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

    def _draw_footer(
        self,
        canvas: tk.Canvas,
        vw: int,
        vh: int,
        y: float,
        accent: str,
        dim: str,
        frame: str,
        bg: str,
        hover_id: str | None,
    ) -> None:
        hp.draw_panel(canvas, _MARGIN, y, vw - 2 * _MARGIN, _FOOTER_H - 4, frame=frame, accent=accent, fill=bg)

        launch_x = vw // 2 - 170
        launch_w = 160.0
        back_x = vw // 2 + 10
        back_w = 160.0
        btn_y = y + 10
        btn_h = 32.0
        self.hits.add("launch", launch_x, btn_y, launch_w, btn_h)
        self.hits.add("back_title", back_x, btn_y, back_w, btn_h)
        draw_menu_button(
            canvas,
            launch_x,
            btn_y,
            launch_w,
            btn_h,
            "▶  LAUNCH COURSE",
            accent=accent,
            dim=dim,
            frame=frame,
            selected=True,
            hover=hover_id == "launch",
        )
        draw_menu_button(
            canvas,
            back_x,
            btn_y,
            back_w,
            btn_h,
            "←  NAV STATION",
            accent=accent,
            dim=dim,
            frame=frame,
            hover=hover_id == "back_title",
        )
        canvas.create_text(
            vw // 2,
            y + _FOOTER_H - 10,
            text="Enter launch · Esc nav station · Bazaar opens trade overlay",
            fill=dim,
            font=self.FONT_SMALL,
        )

    @staticmethod
    def _powerup_color(kind: PowerUpKind) -> str:
        return {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.BOOST_TAP: palette.PICKUP_BOOST,
            PowerUpKind.RUBBER_HULL: palette.PICKUP_RUBBER,
        }.get(kind, palette.HUD_LOOT_NEW)

    @staticmethod
    def _draw_lives(canvas: tk.Canvas, x: float, y: float, lives: int, accent: str) -> None:
        for i in range(MAX_LIVES):
            color = accent if i < lives else palette.HUD_LIFE_EMPTY
            cx = x + i * 22 + 8
            canvas.create_polygon(cx, y + 2, cx + 7, y + 14, cx - 7, y + 14, fill=color, outline=accent if i < lives else palette.HUD_LIFE_EMPTY)

    @staticmethod
    def _draw_hull_chunks(canvas: tk.Canvas, x: float, y: float, chunks: int, max_chunks: int, accent: str) -> None:
        for i in range(max_chunks):
            color = accent if i < chunks else palette.HUD_HULL_EMPTY
            sx = x + i * 28
            canvas.create_rectangle(sx, y, sx + 22, y + 12, fill=color, outline=accent if i < chunks else palette.HUD_HULL_EMPTY, width=1)

    @staticmethod
    def _draw_cargo(canvas: tk.Canvas, x: float, y: float, stacks: PowerUpStacks, accent: str, dim: str) -> None:
        if not stacks:
            canvas.create_text(x, y + 6, anchor="w", text="EMPTY", fill=dim, font=ChartMapOverlay.FONT)
            return
        chip_y = y + 2
        shown = 0
        for kind in sorted(stacks.keys(), key=lambda k: k.name):
            count = stacks[kind]
            if count <= 0:
                continue
            if shown >= 2:
                canvas.create_text(x, chip_y + 6, anchor="w", text=f"+{sum(stacks.values()) - shown} more", fill=dim, font=ChartMapOverlay.FONT_SMALL)
                return
            color = ChartMapOverlay._powerup_color(kind)
            tag = powerup_hud_tag(kind, count)
            chip_w = min(120, 148 - 16)
            canvas.create_rectangle(x, chip_y, x + chip_w, chip_y + 14, fill=color, outline=accent, width=1)
            draw_fitted_text(
                canvas,
                x + 4,
                chip_y + 2,
                tag,
                max_width=chip_w - 8,
                color=palette.HUD_BG,
                font=ChartMapOverlay.FONT_SMALL,
            )
            chip_y += 16
            shown += 1

    @staticmethod
    def _starfield(canvas: tk.Canvas, width: int, height: int, *, dense: bool) -> None:
        count = 120 if dense else 70
        for i in range(count):
            sx = (i * 83 + 17) % width
            sy = (i * 47 + 31) % height
            tone = palette.CHASE_STAR_FAR if dense and i % 5 == 0 else "#294764"
            canvas.create_rectangle(sx, sy, sx + 2, sy + 2, fill=tone, outline="")
