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
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button, draw_wrapped_text
from gravity_ho_matey.render.shop_tree_view import ShopTreeView
from gravity_ho_matey.render.gravity_field_viz import heatmap_cell_visible, inside_black_hole_footprint
from gravity_ho_matey.render.world_draw import gravity_field_color
from gravity_ho_matey.narrative.chart_briefing_copy import (
    BRIEFING_LOW_PRIORITY,
    BRIEFING_SECTION_ORDER,
    LEVEL_BRIEFING,
    LEVEL_INTEL,
)

# Layout aligned with SciFiHudOverlay command deck (960×640).
_HEADER_H = 54
_CLEARED_H = 34
_FOOTER_H = 82
_SHOP_CTA_H = 38
_MARGIN = 12
_BRIEFING_W = 252
_INTEL_W = 142
_MAP_GAP = 8
_BRIEF_LINE_H = 12.0
_INTEL_LINE_H = 12.0


@dataclass(frozen=True, slots=True)
class _ChartBodyLayout:
    body_top: float
    body_h: float
    briefing_x: float
    briefing_w: float
    map_x: float
    map_w: float
    intel_x: float
    intel_w: float


def _chart_body_layout(vw: float, body_top: float, body_h: float) -> _ChartBodyLayout:
    briefing_x = float(_MARGIN)
    briefing_w = float(_BRIEFING_W)
    intel_w = float(_INTEL_W)
    intel_x = float(vw) - _MARGIN - intel_w
    map_x = briefing_x + briefing_w + _MAP_GAP
    map_w = max(320.0, intel_x - _MAP_GAP - map_x)
    return _ChartBodyLayout(
        body_top=body_top,
        body_h=body_h,
        briefing_x=briefing_x,
        briefing_w=briefing_w,
        map_x=map_x,
        map_w=map_w,
        intel_x=intel_x,
        intel_w=intel_w,
    )


def _group_briefing_sections(rows: tuple[tuple[str, str], ...]) -> dict[str, str]:
    """Merge continuation lines into one wrapped body per section label."""
    sections: dict[str, list[str]] = {}
    current = ""
    for label, value in rows:
        if label:
            current = label
            if value:
                sections.setdefault(current, []).append(value)
        elif value and current:
            sections.setdefault(current, []).append(value)
    return {key: " · ".join(parts) for key, parts in sections.items()}


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
        shop_open_anim: float = 1.0,
        shop_view: ShopTreeView | None = None,
        shop_ui: object | None = None,
    ) -> None:
        self.hits.clear()
        vw = world.config.viewport_width
        vh = world.config.viewport_height
        solar = world.config.level_theme == "solar"
        drift = world.config.level_theme == "drift"
        rift = world.config.level_theme == "rift"
        siege = world.config.level_theme == "siege"
        brood = world.config.level_theme == "brood_moon"
        accent = (
            palette.HUD_ACCENT_SOLAR
            if solar
            else palette.RIFT_HUD_ACCENT
            if rift
            else palette.SIEGE_HUD_ACCENT
            if siege
            else palette.BROOD_MOON_HUD_ACCENT
            if brood
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
            fill=palette.SOLAR_BG if solar else palette.RIFT_BG if rift else palette.SIEGE_BG if siege else palette.BROOD_MOON_BG if brood else palette.BACKGROUND,
            outline="",
        )
        self._starfield(canvas, vw, vh, theme=world.config.level_theme, elapsed=elapsed, dense=solar or drift or rift or siege or brood)
        self._draw_command_bar(canvas, world, campaign, cleared_level_id, accent, dim, frame, bg)
        self._draw_status_banner(canvas, vw, cleared_level_id, upcoming_level_id, elapsed, accent, dim)
        body_top = _HEADER_H + _CLEARED_H + 8
        footer_top = vh - _FOOTER_H - 8
        body_bottom = footer_top - _SHOP_CTA_H - 6
        body_h = body_bottom - body_top
        layout = _chart_body_layout(vw, body_top, body_h)
        self._draw_side_mission(
            canvas,
            layout.briefing_x,
            layout.body_top,
            layout.briefing_w,
            layout.body_h,
            campaign,
            cleared_level_id,
            elapsed,
            upcoming_level_id,
            world,
            accent,
            dim,
            frame,
        )
        self._draw_holo_map(canvas, world, field, layout.map_x, layout.body_top, layout.map_w, layout.body_h, accent, dim, frame, elapsed)
        self._draw_side_intel(
            canvas,
            layout.intel_x,
            layout.body_top,
            layout.intel_w,
            layout.body_h,
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
                shop_open_anim=shop_open_anim,
                shop_view=shop_view,
                shop_ui=shop_ui,
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

        hp.draw_panel(canvas, 462, 6, 132, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 470, 12, "SECTOR", color=dim)
        draw_fitted_text(
            canvas,
            470,
            30,
            world.config.level_name.upper(),
            max_width=118,
            color=accent,
            font=("Courier New", 9, "bold"),
        )

        hp.draw_panel(canvas, 600, 6, 112, 42, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, 608, 12, "CHART MODE", color=dim)
        chart_mode = "PREVIEW" if cleared_level_id else "PRE-BRIEF"
        draw_fitted_text(
            canvas,
            608,
            30,
            chart_mode,
            max_width=98,
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

    @staticmethod
    def _draw_wrapped_kv(
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
        max_lines: int = 3,
        line_h: float = _INTEL_LINE_H,
        bottom_y: float | None = None,
    ) -> float:
        if bottom_y is not None and y >= bottom_y:
            return y
        inner = max(8.0, width - 20.0)
        hp.draw_panel_title(canvas, x + 10, y, label, color=dim)
        text_y = y + 11
        if bottom_y is not None and text_y >= bottom_y:
            return y
        used = draw_wrapped_text(
            canvas,
            x + 10,
            text_y,
            value,
            max_width=inner,
            line_height=line_h,
            color=value_color or accent,
            font=ChartMapOverlay.FONT_SMALL,
            max_lines=max_lines,
        )
        return text_y + used + 6.0

    @staticmethod
    def _draw_briefing_sections(
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        sections: dict[str, str],
        accent: str,
        dim: str,
    ) -> None:
        bottom = y + h - 8.0
        ry = y + 28.0
        inner = max(8.0, w - 20.0)
        ordered = [key for key in BRIEFING_SECTION_ORDER if key in sections]
        for key in sections:
            if key not in ordered:
                ordered.append(key)

        def _section_height(body: str, max_lines: int) -> float:
            from gravity_ho_matey.render.menu_ui import wrap_text_lines

            lines = wrap_text_lines(body, inner, ChartMapOverlay.FONT_SMALL, max_lines=max_lines)
            return 11.0 + len(lines) * _BRIEF_LINE_H + 8.0

        # First pass: draw high-priority sections; skip low-priority if they would clip.
        for label in ordered:
            body = sections[label]
            max_lines = 4 if label in ("OBJECTIVE", "ORBITAL", "SURFACE", "WIN") else 2
            need = _section_height(body, max_lines)
            if label in BRIEFING_LOW_PRIORITY and ry + need > bottom:
                continue
            if ry + 11.0 > bottom:
                break
            hp.draw_panel_title(canvas, x + 10, ry, label, color=dim)
            ry += 11.0
            used = draw_wrapped_text(
                canvas,
                x + 10,
                ry,
                body,
                max_width=inner,
                line_height=_BRIEF_LINE_H,
                color=accent,
                font=ChartMapOverlay.FONT_SMALL,
                max_lines=max_lines,
            )
            ry += used + 8.0

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
            rows = LEVEL_BRIEFING.get(upcoming_level_id, LEVEL_BRIEFING["cove"])
            sections = _group_briefing_sections(rows)
            self._draw_briefing_sections(
                canvas, x, y, w, h, sections=sections, accent=accent, dim=dim,
            )
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
        if campaign.nifflerp_pending:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "NIFFLERP",
                "Deploys next sector",
                accent=accent,
                dim=dim,
                value_color=palette.NIFFLERP_CORE,
            )
        elif campaign.nifflerp_hp > 0:
            ry = self._draw_kv_line(
                canvas,
                x,
                ry,
                w,
                "NIFFLERP",
                f"{campaign.nifflerp_hp}/3 HP jewel retriever",
                accent=accent,
                dim=dim,
                value_color=palette.NIFFLERP_CORE,
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
        hover_id: str | None,
        elapsed: float,
    ) -> None:
        self._shop.draw_bazaar_cta(
            canvas,
            x=_MARGIN,
            y=y,
            w=vw - 2 * _MARGIN,
            h=h,
            campaign=campaign,
            hits=self.hits,
            accent=accent,
            hover_id=hover_id,
            elapsed=elapsed,
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
        bottom = y + h - (18.0 if strip else 8.0)
        ry = y + 28.0

        refresher = LEVEL_INTEL.get(upcoming_level_id, LEVEL_INTEL["cove"])
        for label, value in refresher:
            ry = self._draw_wrapped_kv(
                canvas, x, ry, w, label, value,
                accent=accent, dim=dim, max_lines=3, bottom_y=bottom,
            )

        status_parts: list[str] = []
        if world.beacons:
            required = world.beacons_required_for_exit
            status_parts.append(f"{required} of {len(world.beacons)} beacons")
        elif world.config.brood_moon_mission:
            status_parts.append("surface beacons after land")
        else:
            status_parts.append("exit open — no beacons")
        if roster:
            status_parts.append(f"roster {world.roster_enemies_remaining}/{roster}")
        elif hostiles:
            label = "squids" if squids and squids == hostiles else "hostiles"
            status_parts.append(f"{hostiles} {label}")
        if world.allies:
            alive_wings = sum(1 for a in world.allies if a.alive)
            status_parts.append(f"{alive_wings}/{len(world.allies)} escorts")
        if status_parts and ry < bottom:
            ry = self._draw_wrapped_kv(
                canvas, x, ry, w, "FIELD", " · ".join(status_parts),
                accent=accent, dim=dim, max_lines=2, bottom_y=bottom,
            )

        if strip and ry < bottom:
            draw_wrapped_text(
                canvas,
                x + 10,
                y + h - 22,
                "Tall sector — map pans with your position.",
                max_width=w - 20,
                line_height=11.0,
                color=dim,
                font=self.FONT_SMALL,
                max_lines=2,
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
        inner_h = h - 56
        canvas.create_rectangle(inner_x, inner_y, inner_x + inner_w, inner_y + inner_h, fill="#040810", outline=frame)
        transform = self._map_transform(world, inner_x, inner_y, inner_w, inner_h)
        self._draw_map_field(canvas, field, transform, world.wells)
        sweep_y = inner_y + (elapsed * 0.32 % 1.0) * inner_h
        canvas.create_line(inner_x, sweep_y, inner_x + inner_w, sweep_y, fill=accent, width=1)
        canvas.create_line(inner_x, sweep_y + 1, inner_x + inner_w, sweep_y + 1, fill=frame, width=1)
        self._draw_map_entities(canvas, world, transform, dim, elapsed)
        if transform.strip_window:
            self._draw_strip_window_chrome(canvas, world, transform, accent, dim)
        self._draw_map_legend(canvas, inner_x, inner_y + inner_h + 4, inner_w, dim)
        hp.draw_scanlines(canvas, inner_x, inner_y, inner_w, inner_h)

    @staticmethod
    def _draw_map_legend(canvas: tk.Canvas, x: float, y: float, w: float, dim: str) -> None:
        """Compact glyph strip under the map — same on every level."""
        items = (
            ("◆", palette.BEACON),
            ("◎", palette.WELL),
            ("●", palette.BLACK_HOLE_RING),
            ("▣", palette.GATE_LOCKED),
            ("▲", palette.SHIP),
            ("×", palette.ENEMY),
            ("◉", palette.SQUID_CORE),
            ("⬡", palette.ASTEROID_EDGE),
        )
        step = w / len(items)
        for index, (glyph, color) in enumerate(items):
            cx = x + step * (index + 0.5)
            canvas.create_text(cx, y + 6, text=glyph, fill=color, font=ChartMapOverlay.FONT_SMALL, anchor="center")
        canvas.create_line(x, y, x + w, y, fill=dim, width=1)

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

    def _draw_map_field(
        self,
        canvas: tk.Canvas,
        field: GravityField,
        t: _MapTransform,
        wells: tuple,
    ) -> None:
        step = 2 if field.rows > 32 else 1
        for row in range(0, field.rows, step):
            for col in range(0, field.cols, step):
                cell = field.cell_at(col, row)
                if cell.magnitude <= 1e-6:
                    continue
                wx = field.origin.x + col * field.cell_size + field.cell_size * 0.5
                wy = field.origin.y + row * field.cell_size + field.cell_size * 0.5
                if wells and inside_black_hole_footprint(wells, wx, wy):
                    continue
                hit = self._world_to_map(Vec2(wx, wy), t)
                if hit is None:
                    continue
                mx, my = hit
                norm = cell.magnitude / field.max_magnitude
                if not heatmap_cell_visible(norm):
                    continue
                size = field.cell_size * step * t.scale * 0.92
                tone = gravity_field_color(norm)
                canvas.create_rectangle(mx, my, mx + size, my + size * 0.85, fill=tone, outline="")

    def _draw_map_entities(self, canvas: tk.Canvas, world: GameWorld, t: _MapTransform, dim: str, elapsed: float) -> None:
        glyph_scale = max(0.35, min(0.85, t.scale * 1.1))

        from gravity_ho_matey.render.asteroid_viz import draw_map_asteroid_glyph
        from gravity_ho_matey.render.beacon_viz import beacon_seed_from_pos, draw_beacon_play
        from gravity_ho_matey.render.lighting import LightRig
        from gravity_ho_matey.render.station_viz import draw_map_station_glyph

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

        if world.space_junk:
            from gravity_ho_matey.render.space_junk_viz import draw_holo_junk_glyph

            for junk in world.space_junk:
                hit = self._world_to_map(junk.pos, t)
                if hit is None:
                    continue
                draw_holo_junk_glyph(
                    canvas,
                    junk,
                    map_x=hit[0],
                    map_y=hit[1],
                    map_scale=glyph_scale,
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
            if (
                world.config.level_theme == "brood_moon"
                and well.kind == "planet"
                and world.brood_moon is not None
                and world.brood_moon.layout is not None
            ):
                planet = world.brood_moon.layout.planet
                inner_rr = max(3.0, planet.landing_band_inner * t.scale * 0.32)
                outer_rr = max(4.0, planet.landing_band_outer * t.scale * 0.32)
                canvas.create_oval(
                    mx - inner_rr, my - inner_rr, mx + inner_rr, my + inner_rr,
                    outline=palette.BROOD_MOON_HUD_ACCENT, width=1, dash=(3, 4),
                )
                canvas.create_oval(
                    mx - outer_rr, my - outer_rr, mx + outer_rr, my + outer_rr,
                    outline=palette.BROOD_MOON_VEIN, width=1, dash=(4, 3),
                )
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

        for station in world.friendly_stations:
            if not station.alive:
                continue
            hit = self._world_to_map(station.pos, t)
            if hit is None:
                continue
            draw_map_station_glyph(
                canvas,
                Vec2(hit[0], hit[1]),
                station,
                scale=max(0.22, min(0.55, glyph_scale * 0.55)),
                rig=map_rig,
            )
        if world.space_station is not None and world.space_station.alive:
            hit = self._world_to_map(world.space_station.pos, t)
            if hit is not None:
                draw_map_station_glyph(
                    canvas,
                    Vec2(hit[0], hit[1]),
                    world.space_station,
                    scale=max(0.22, min(0.55, glyph_scale * 0.55)),
                    rig=map_rig,
                )
        if world.mega_squid is not None and world.mega_squid.alive:
            hit = self._world_to_map(world.mega_squid.pos, t)
            if hit is not None:
                mx, my = hit
                rr = max(7.0, world.mega_squid.radius * t.scale * 0.42)
                canvas.create_oval(
                    mx - rr,
                    my - rr,
                    mx + rr,
                    my + rr,
                    outline=palette.SQUID_CORE,
                    width=2,
                )
                canvas.create_text(mx, my - rr - 6, text="BOSS", fill=palette.SQUID_CORE, font=self.FONT_SMALL)

        for enemy in world.enemies:
            if not enemy.alive:
                continue
            hit = self._world_to_map(enemy.pos, t)
            if hit is None:
                continue
            mx, my = hit
            r = max(4.0, enemy.radius * t.scale * 0.35)
            if enemy.kind is EnemyKind.SQUID:
                from gravity_ho_matey.render.squid_viz import draw_squid_map_glyph

                draw_squid_map_glyph(canvas, mx, my, radius=r, facing=enemy.facing_angle)
            elif enemy.kind is EnemyKind.HOSTILE_FIGHTER:
                from gravity_ho_matey.render.enemy_viz import draw_hostile_fighter_map_glyph

                draw_hostile_fighter_map_glyph(canvas, mx, my, radius=r, facing=enemy.facing_angle)
            else:
                from gravity_ho_matey.render.enemy_viz import draw_patrol_enemy_map_glyph

                draw_patrol_enemy_map_glyph(canvas, mx, my, radius=r, facing=enemy.facing_angle)

        if world.egg_pods:
            from gravity_ho_matey.render.egg_pod_viz import draw_egg_pod_map_glyph

            for pod in world.egg_pods:
                if not pod.alive:
                    continue
                hit = self._world_to_map(pod.pos, t)
                if hit is None:
                    continue
                mx, my = hit
                draw_egg_pod_map_glyph(
                    canvas,
                    mx,
                    my,
                    radius=max(5.0, pod.radius * t.scale * 0.38),
                    alarm=pod.alarm,
                    elapsed=elapsed,
                )

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
                text="↑ more chart",
                fill=dim,
                font=self.FONT_SMALL,
            )
        if t.world_y1 < wh - 4.0:
            canvas.create_text(
                t.clip_x0 + 8,
                t.clip_y1 - 10,
                anchor="w",
                text="↓ more chart",
                fill=dim,
                font=self.FONT_SMALL,
            )
        canvas.create_text(
            t.clip_x1 - 8,
            t.clip_y0 + 10,
            anchor="e",
            text="◈ PAN VIEW ◈",
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
            "▶  START LEVEL",
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
    def _starfield(
        canvas: tk.Canvas,
        width: int,
        height: int,
        *,
        theme: str = "cove",
        elapsed: float = 0.0,
        dense: bool,
    ) -> None:
        from gravity_ho_matey.render.starfield_viz import draw_layered_starfield

        if not dense:
            return
        draw_layered_starfield(
            canvas,
            x=0.0,
            y=0.0,
            width=float(width),
            height=float(height),
            elapsed=elapsed,
            theme=theme,
        )
