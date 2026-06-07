from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState, MAX_LIVES
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_RADIATION_EXPOSURE_LIMIT,
    ChartBoundsToast,
    chart_bounds_edge_badge,
    chart_bounds_toast_copy,
    ship_in_chart,
)
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks, powerup_hud_tag
from gravity_ho_matey.gameplay.jewel_config import TREASURY_FLASH_SECONDS
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


class SciFiHudOverlay:
    """Retro sci-fi command overlay — bracketed panels, segmented readouts, CRT accents."""

    PANEL_H = 54
    ALERT_H = 22
    CHART_BOUNDS_BANNER_H = 26
    FONT = ("Courier New", 10, "bold")
    FONT_SMALL = ("Courier New", 8)
    FONT_TITLE = ("Courier New", 9, "bold")
    FONT_WAVE = ("Courier New", 12, "bold")
    FONT_WAVE_ALERT = ("Courier New", 13, "bold")
    FONT_WAVE_HINT = ("Courier New", 10, "bold")

    @staticmethod
    def playfield_top(
        *,
        hud_alert: str = "",
        bounds_toast_kind: ChartBoundsToast | None = None,
        bounds_toast_ttl: float = 0.0,
    ) -> float:
        """Top inset for the playfield — must match camera layout and tactical draw offset."""
        top = float(SciFiHudOverlay.PANEL_H)
        if hud_alert:
            top += SciFiHudOverlay.ALERT_H
        if bounds_toast_kind is not None and bounds_toast_ttl > 0.0:
            top += SciFiHudOverlay.CHART_BOUNDS_BANNER_H
        return top

    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        campaign: CampaignState,
        *,
        hud_alert: str = "",
        bounds_toast_kind: ChartBoundsToast | None = None,
        bounds_toast_ttl: float = 0.0,
        treasury_flash_ttl: float = 0.0,
        camera_mode: CameraMode | None = None,
        camera_mode_flash: bool = False,
    ) -> None:
        width = world.config.viewport_width
        solar = world.config.level_theme == "solar"
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
        cargo_highlight: PowerUpKind | None = None

        canvas.create_rectangle(0, 0, width, self.PANEL_H, fill=bg, outline="")
        canvas.create_line(0, self.PANEL_H, width, self.PANEL_H, fill=accent, width=1)
        self._scanline(canvas, width)

        self._panel(canvas, 8, 6, 148, 42, frame, accent)
        self._label(canvas, 16, 12, "CAPTAIN", dim)
        self._draw_lives(canvas, 16, 24, campaign.lives, accent, palette.HUD_LIFE_EMPTY)

        self._panel(canvas, 162, 6, 168, 42, frame, accent)
        self._label(canvas, 170, 12, "HULL INTEGRITY", dim)
        self._draw_hull_chunks(
            canvas,
            170,
            24,
            campaign.hull_chunks,
            campaign.max_hull_chunks_per_life,
            accent,
            palette.HUD_HULL_EMPTY,
        )
        if campaign.powerup_stacks:
            self._draw_hull_fittings(canvas, 170, 38, campaign.powerup_stacks, dim, cargo_highlight)

        self._panel(canvas, 336, 6, 128, 42, frame, accent)
        if world.beacons:
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
            if world.egg_pods:
                pods_left = world.egg_pods_remaining
                pod_total = len(world.egg_pods)
                canvas.create_text(
                    344,
                    44,
                    anchor="w",
                    text=f"PODS {pods_left:02d} / {pod_total:02d}",
                    fill=palette.HUD_WARN if pods_left else palette.GATE_OPEN,
                    font=self.FONT_SMALL,
                )
        else:
            if brood and world.brood_moon is not None:
                from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase

                bm = world.brood_moon
                self._label(canvas, 344, 12, "BROOD MOON", dim)
                if bm.phase is BroodPhase.ORBITAL_RETURN and world.finish_unlocked:
                    status_txt, status_color = "DOCK OPEN", palette.GATE_OPEN
                elif bm.seal_complete:
                    status_txt, status_color = "RTB", palette.GATE_OPEN
                elif bm.on_surface and bm.objectives_complete:
                    from gravity_ho_matey.levels.brood_moon_layout import SEAL_TRAVEL_DISTANCE

                    pct = min(100, int(100 * bm.seal_travel / SEAL_TRAVEL_DISTANCE))
                    status_txt = f"SEAL {pct:3d}%"
                    status_color = palette.BROOD_MOON_HUD_ACCENT
                elif bm.on_surface:
                    status_txt = "NURSERY"
                    status_color = palette.HUD_WARN
                else:
                    status_txt = "ORBIT"
                    status_color = palette.BROOD_MOON_HUD_ACCENT
                canvas.create_text(
                    344,
                    30,
                    anchor="w",
                    text=status_txt,
                    fill=status_color,
                    font=("Courier New", 11, "bold"),
                )
                if bm.hud_prompt:
                    canvas.create_text(
                        344,
                        44,
                        anchor="w",
                        text=bm.hud_prompt[:22],
                        fill=dim,
                        font=self.FONT_SMALL,
                    )
            elif siege and world.config.exit_requires_roster_clear:
                self._label(canvas, 344, 12, "HOSTILE ROSTER", dim)
                defeated = world.roster_enemies_defeated
                total = world.roster_enemies_total
                if world.finish_unlocked:
                    roster_txt, roster_color = "LANE OPEN", palette.GATE_OPEN
                else:
                    roster_txt = f"{defeated:02d} / {total:02d}"
                    roster_color = palette.HUD_WARN
                canvas.create_text(
                    344,
                    30,
                    anchor="w",
                    text=roster_txt,
                    fill=roster_color,
                    font=("Courier New", 11, "bold"),
                )
                if world.space_station is not None and world.space_station.alive:
                    canvas.create_text(
                        344,
                        44,
                        anchor="w",
                        text=f"STN {world.space_station.hits_remaining:02d} HP",
                        fill=palette.HUD_DIM,
                        font=self.FONT_SMALL,
                    )
            elif rift and world.config.protection_mission:
                self._label(canvas, 344, 12, "RELAY HOLD", dim)
                wave_font = self.FONT_WAVE
                wave_y = 30
                sub_font = self.FONT_SMALL
                if world.finish_unlocked:
                    wave_txt, wave_color = "EXTRACT OPEN", palette.GATE_OPEN
                    relay_sub = "RTB · south pad"
                    sub_color = palette.RIFT_HUD_ACCENT
                elif world.protection_boss_intro_flash > 0.0:
                    wave_txt, wave_color = "WAVE 3 / 3", palette.HUD_WARN
                    wave_font = self.FONT_WAVE_ALERT
                    relay_sub = "brood mother contact"
                    sub_color = palette.RIFT_HUD_ACCENT
                    sub_font = self.FONT_WAVE_HINT
                elif world.wave_director is not None:
                    director = world.wave_director
                    inbound = director.inbound_copy()
                    nudge = director.nudge_copy()
                    wave = director.current_wave
                    if nudge is not None:
                        wave_txt = f"WAVE {director.nudge_wave} / 3"
                        wave_color = palette.HUD_ACCENT if director.nudge_ttl > 0.35 else palette.HUD_WARN
                        wave_font = self.FONT_WAVE_ALERT
                        relay_sub = nudge.subtitle
                        sub_font = self.FONT_WAVE_HINT
                        sub_color = palette.HUD_ACCENT
                    elif inbound is not None:
                        wave_txt = f"WAVE {wave} / 3"
                        wave_color = palette.HUD_WARN
                        relay_sub = f"next · {inbound.subtitle}"
                        sub_font = self.FONT_WAVE_HINT
                        sub_color = palette.RIFT_HUD_ACCENT
                    else:
                        wave_txt = f"WAVE {wave} / 3"
                        wave_color = palette.HUD_WARN
                        relay_sub = None
                        sub_color = palette.HUD_DIM
                else:
                    wave_txt, wave_color = "STANDBY", palette.HUD_DIM
                    relay_sub = None
                    sub_color = palette.HUD_DIM
                canvas.create_text(
                    344,
                    wave_y,
                    anchor="w",
                    text=wave_txt,
                    fill=wave_color,
                    font=wave_font,
                )
                if world.friendly_stations:
                    relay = world.friendly_stations[0]
                    relay_hp = relay.hits_remaining if relay.alive else 0
                    if relay_sub:
                        sub_txt = relay_sub
                    elif (
                        world.mega_squid is not None
                        and world.mega_squid.alive
                        and world.wave_director is not None
                        and world.wave_director.current_wave >= 3
                    ):
                        sub_txt = "kill brood-mother"
                        sub_color = palette.RIFT_HUD_ACCENT
                        sub_font = self.FONT_WAVE_HINT
                    else:
                        sub_txt = f"RELAY {relay_hp:02d} HP"
                        sub_color = palette.HUD_DIM
                    canvas.create_text(
                        344,
                        44,
                        anchor="w",
                        text=sub_txt,
                        fill=sub_color,
                        font=sub_font,
                    )
            else:
                self._label(canvas, 344, 12, "EXIT VECTOR", dim)
                canvas.create_text(
                    344,
                    30,
                    anchor="w",
                    text="NORTH GATE",
                    fill=palette.GATE_OPEN if world.finish_unlocked else palette.GATE_LOCKED,
                    font=("Courier New", 11, "bold"),
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

        if world.squid_cling_timer > 0.0:
            from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL

            frac = min(1.0, world.squid_cling_timer / SQUID_CLING_DAMAGE_INTERVAL)
            self._badge(
                canvas,
                720,
                54 if rift else 34,
                anchor="nw",
                text=f"CLING {int(frac * 100):3d}%",
                fill=palette.SQUID_TOUCH_TIP,
                font=self.FONT_SMALL,
            )

        if (rift or siege) and world.allies:
            alive_wings = sum(1 for ally in world.allies if ally.alive)
            wing_y = 54
            if world.squid_cling_timer > 0.0:
                wing_y = 74
            self._badge(
                canvas,
                720,
                wing_y,
                anchor="nw",
                text=f"WING {alive_wings}/{len(world.allies)}",
                fill=palette.FRIENDLY_SHIP if alive_wings else palette.HUD_DIM,
                font=self.FONT_SMALL,
            )

        if campaign.rubber_hull_charges > 0:
            rubber_y = 34
            if world.squid_cling_timer > 0.0:
                rubber_y = 54
            elif (rift or siege) and world.allies:
                rubber_y = 74
            self._badge(
                canvas,
                720,
                rubber_y,
                anchor="nw",
                text=f"RUBBER {campaign.rubber_hull_charges:02d}",
                fill=palette.PICKUP_RUBBER,
                font=self.FONT_SMALL,
            )

        if world.drone_wingman is not None and world.drone_wingman.alive:
            drone = world.drone_wingman
            drone_y = 34
            if world.squid_cling_timer > 0.0:
                drone_y = 54
            elif (rift or siege) and world.allies:
                drone_y = 74
            if campaign.rubber_hull_charges > 0:
                drone_y += 20
            drone_txt = f"DRONE {drone.hits_remaining:02d}/{drone.hits_max}"
            drone_color = palette.DRONE_CORE
            if drone.is_overheated:
                drone_txt = "DRONE COOLING"
                drone_color = palette.HUD_WARN
            elif drone.heat > 0.55:
                drone_txt = f"DRONE {drone.hits_remaining:02d}/{drone.hits_max} · HOT"
                drone_color = palette.DRONE_HEAT
            self._badge(
                canvas,
                720,
                drone_y,
                anchor="nw",
                text=drone_txt,
                fill=drone_color,
                font=self.FONT_SMALL,
            )

        cargo_x = width - 156
        cargo_frame = self._powerup_color(cargo_highlight) if cargo_highlight else accent
        treasury_pulse = treasury_flash_ttl > 0.0
        if cargo_highlight or treasury_pulse:
            pulse_frame = palette.JEWEL_EDGE if treasury_pulse else cargo_frame
            canvas.create_rectangle(cargo_x - 2, 4, cargo_x + 150, 50, outline=pulse_frame, width=2)
        self._panel(canvas, cargo_x, 6, 148, 42, frame, cargo_frame if cargo_highlight else accent)
        self._label(canvas, cargo_x + 8, 12, "TREASURY", dim)
        jewel_color = palette.JEWEL_CORE
        if treasury_pulse:
            pulse_t = treasury_flash_ttl / TREASURY_FLASH_SECONDS
            jewel_color = palette.JEWEL_HIGHLIGHT if pulse_t > 0.45 else palette.JEWEL_EDGE
        canvas.create_text(
            cargo_x + 140,
            12,
            anchor="e",
            text=f"★ {campaign.jewels}",
            fill=jewel_color,
            font=("Courier New", 10, "bold"),
        )
        self._draw_cargo(
            canvas,
            cargo_x + 8,
            24,
            campaign.powerup_stacks,
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

        if bounds_toast_kind is not None and bounds_toast_ttl > 0.0:
            self._draw_chart_bounds_toast(
                canvas,
                width,
                banner_y,
                bounds_toast_kind,
                world,
                bounds_toast_ttl,
            )
            banner_y += self.CHART_BOUNDS_BANNER_H

        if brood and world.brood_moon is not None and world.brood_moon.boss_intro_flash > 0.0:
            flash_y = banner_y if banner_y > self.PANEL_H else self.PANEL_H
            canvas.create_rectangle(0, flash_y, width, flash_y + self.ALERT_H, fill="#301040", outline="")
            canvas.create_line(0, flash_y + self.ALERT_H, width, flash_y + self.ALERT_H, fill=palette.SQUID_CORE, width=1)
            canvas.create_text(
                width // 2,
                flash_y + self.ALERT_H // 2,
                text="◈ BROOD MOTHER INBOUND ◈",
                fill=palette.SQUID_CORE,
                font=("Courier New", 10, "bold"),
            )

    def draw_playfield_chrome(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        hud_top: float,
        *,
        camera_mode: CameraMode | None = None,
        camera_mode_flash: bool = False,
        bounds_alert_flash: bool = False,
    ) -> None:
        """Sector + camera badges on the playfield — never stacked on command panels."""
        width = world.config.viewport_width
        height = world.config.viewport_height
        solar = world.config.level_theme == "solar"
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
        if world.config.open_bounds and not ship_in_chart(world.ship.pos, world.config):
            self._draw_chart_bounds_playfield_overlay(
                canvas,
                world,
                hud_top,
                height,
                camera_mode=camera_mode,
                bounds_alert_flash=bounds_alert_flash,
            )
        elif (
            world.config.open_bounds
            and world.chart_radiation_exposure > 0.0
            and ship_in_chart(world.ship.pos, world.config)
        ):
            self._badge(
                canvas,
                width // 2,
                y,
                anchor="n",
                text=(
                    f"BANKED {world.chart_radiation_exposure:0.1f}"
                    f" / {CHART_RADIATION_EXPOSURE_LIMIT:0.0f}s"
                ),
                fill=dim,
                font=self.FONT_SMALL,
            )
        if brood and world.brood_moon is not None:
            self._draw_brood_interaction_charge(
                canvas,
                world,
                width,
                height,
                hud_top,
                accent=accent,
                dim=dim,
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

    def _draw_brood_interaction_charge(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        width: float,
        height: float,
        hud_top: float,
        *,
        accent: str,
        dim: str,
    ) -> None:
        from gravity_ho_matey.gameplay.brood_moon_mission import (
            BroodPhase,
            in_landing_zone,
            liftoff_blocked,
        )
        from gravity_ho_matey.levels.brood_moon_layout import LANDING_CHARGE_SECONDS, LIFTOFF_CHARGE_SECONDS

        bm = world.brood_moon
        if bm is None or bm.in_cinematic or bm.layout is None:
            return

        charge = 0.0
        label = ""
        active = False
        if bm.phase is BroodPhase.ORBITAL and in_landing_zone(world.ship.pos, bm.layout):
            charge = bm.landing_charge / max(1e-6, LANDING_CHARGE_SECONDS)
            label = "LAND"
            active = True
        elif bm.phase is BroodPhase.SURFACE and bm.ascent_ready and not liftoff_blocked(world):
            charge = bm.liftoff_charge / max(1e-6, LIFTOFF_CHARGE_SECONDS)
            label = "ASCEND"
            active = True
        if not active:
            return

        cx = width * 0.5
        cy = height - 72.0
        outer_r = 34.0
        inner_r = 26.0
        canvas.create_oval(
            cx - outer_r,
            cy - outer_r,
            cx + outer_r,
            cy + outer_r,
            outline=dim,
            width=2,
        )
        start = 90.0
        extent = -360.0 * max(0.0, min(1.0, charge))
        if abs(extent) > 0.5:
            canvas.create_arc(
                cx - inner_r,
                cy - inner_r,
                cx + inner_r,
                cy + inner_r,
                start=start,
                extent=extent,
                style=tk.PIESLICE,
                outline="",
                fill=accent,
            )
        canvas.create_oval(
            cx - inner_r,
            cy - inner_r,
            cx + inner_r,
            cy + inner_r,
            outline=accent,
            width=2,
        )
        canvas.create_text(cx, cy - 4, text="E", fill=accent, font=("Courier New", 14, "bold"))
        canvas.create_text(cx, cy + 12, text=label, fill=dim, font=self.FONT_SMALL)

    def _draw_chart_bounds_playfield_overlay(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        hud_top: float,
        viewport_height: float,
        *,
        camera_mode: CameraMode | None,
        bounds_alert_flash: bool,
    ) -> None:
        vw = world.config.viewport_width
        warn = palette.HUD_WARN if bounds_alert_flash else "#a84840"
        border_w = 2
        canvas.create_rectangle(4, hud_top + 4, vw - 4, viewport_height - 4, outline=warn, width=border_w)
        badge = chart_bounds_edge_badge(
            level_theme=world.config.level_theme,
            exposure=world.chart_radiation_exposure,
        )
        badge_y = hud_top + 34 if camera_mode is CameraMode.CHASE else hud_top + 30
        warn_fill = palette.HUD_WARN if world.chart_radiation_exposure >= CHART_RADIATION_EXPOSURE_LIMIT * 0.65 else warn
        self._badge(
            canvas,
            vw // 2,
            badge_y,
            anchor="n",
            text=f"◈ {badge} ◈",
            fill=warn_fill,
            font=self.FONT_SMALL,
        )

    def _draw_chart_bounds_toast(
        self,
        canvas: tk.Canvas,
        width: int,
        y: float,
        kind: ChartBoundsToast,
        world: GameWorld,
        ttl: float,
    ) -> None:
        headline, subline = chart_bounds_toast_copy(
            kind,
            level_theme=world.config.level_theme,
            exposure=world.chart_radiation_exposure,
        )
        leaving = kind is ChartBoundsToast.LEFT_CHART
        bg = palette.HUD_ALERT_BG if leaving else "#081810"
        border = palette.HUD_WARN if leaving else palette.HUD_DIM
        headline_color = palette.HUD_WARN if leaving else palette.GATE_OPEN

        canvas.create_rectangle(0, y, width, y + self.CHART_BOUNDS_BANNER_H, fill=bg, outline="")
        canvas.create_line(0, y + self.CHART_BOUNDS_BANNER_H - 1, width, y + self.CHART_BOUNDS_BANNER_H - 1, fill=border, width=1)
        canvas.create_text(
            width // 2,
            y + 10,
            text=headline.upper(),
            fill=headline_color,
            font=("Courier New", 10, "bold"),
        )
        canvas.create_text(
            width // 2,
            y + 21,
            text=subline,
            fill=border if leaving else palette.HUD_DIM,
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
        stacks: PowerUpStacks,
        dim: str,
        highlight_kind: PowerUpKind | None,
    ) -> None:
        if not stacks:
            canvas.create_text(x, y, anchor="w", text="FITTINGS: —", fill=dim, font=self.FONT_SMALL)
            return
        canvas.create_text(x, y, anchor="w", text="FITTINGS:", fill=dim, font=self.FONT_SMALL)
        chip_x = x + 58
        for kind in sorted(stacks.keys(), key=lambda k: k.name):
            count = stacks[kind]
            if count <= 0:
                continue
            color = self._powerup_color(kind)
            tag = powerup_hud_tag(kind, count)
            chip_w = 40 + (10 if count > 1 else 0)
            if highlight_kind is kind:
                canvas.create_rectangle(chip_x - 2, y - 2, chip_x + chip_w + 2, y + 10, outline=color, width=1)
            canvas.create_rectangle(chip_x, y, chip_x + chip_w, y + 8, fill=color, outline=dim, width=1)
            canvas.create_text(chip_x + 4, y + 1, anchor="w", text=tag, fill=palette.HUD_BG, font=self.FONT_SMALL)
            chip_x += chip_w + 6

    def _draw_cargo(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        stacks: PowerUpStacks,
        accent: str,
        dim: str,
        *,
        highlight_kind: PowerUpKind | None = None,
    ) -> None:
        if not stacks:
            canvas.create_text(x, y + 6, anchor="w", text="EMPTY", fill=dim, font=self.FONT)
            return
        chip_x = x
        for kind in sorted(stacks.keys(), key=lambda k: k.name):
            count = stacks[kind]
            if count <= 0:
                continue
            color = self._powerup_color(kind)
            label = powerup_hud_tag(kind, count)
            active = highlight_kind is kind
            chip_w = 64 + (12 if count > 1 else 0)
            if active:
                canvas.create_rectangle(chip_x - 2, y + 2, chip_x + chip_w + 2, y + 18, outline=color, width=2)
            canvas.create_rectangle(chip_x, y + 4, chip_x + chip_w, y + 16, fill=color, outline=accent if active else dim, width=1)
            canvas.create_text(
                chip_x + 4,
                y + 6,
                anchor="w",
                text=label,
                fill=palette.HUD_BG,
                font=self.FONT,
            )
            chip_x += chip_w + 6
