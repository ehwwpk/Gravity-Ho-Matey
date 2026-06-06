from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.chart_bounds import ChartBoundsToast
from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.chart_map_overlay import ChartMapOverlay
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay
from gravity_ho_matey.render.title_overlay import TitlePage, TitleScreenOverlay
from gravity_ho_matey.render.view_renderers import PerspectiveViewRenderer, TacticalViewRenderer


class TkRenderer:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self._hud = SciFiHudOverlay()
        self._title = TitleScreenOverlay()
        self._chart = ChartMapOverlay()
        self._tactical = TacticalViewRenderer()
        self._perspective = PerspectiveViewRenderer()

    def clear(self) -> None:
        self.canvas.delete("all")

    def draw_title(self, *, page: TitlePage = TitlePage.WELCOME) -> None:
        self.clear()
        self._title.draw(
            self.canvas,
            page=page,
            solar_unlocked=is_level_selectable("solar"),
            draw_ship=lambda cx, cy: self._draw_demo_ship(Vec2(cx, cy), angle=0.12, scale=1.55),
        )

    def draw_world(
        self,
        world: GameWorld,
        campaign: CampaignState,
        camera: ViewCamera,
        gravity_field: GravityField,
        *,
        hud_alert: str = "",
        loot_toast_kind: PowerUpKind | None = None,
        loot_toast_is_new: bool = False,
        loot_toast_ttl: float = 0.0,
        bounds_toast_kind: ChartBoundsToast | None = None,
        bounds_toast_ttl: float = 0.0,
    ) -> None:
        self.clear()
        vw = camera.viewport_width
        vh = camera.viewport_height
        hud_top = SciFiHudOverlay.PANEL_H
        if hud_alert:
            hud_top += SciFiHudOverlay.ALERT_H
        if bounds_toast_kind is not None and bounds_toast_ttl > 0.0:
            hud_top += SciFiHudOverlay.CHART_BOUNDS_BANNER_H
        if loot_toast_kind is not None and loot_toast_ttl > 0.0:
            hud_top += SciFiHudOverlay.LOOT_BANNER_H

        if camera.mode is CameraMode.TACTICAL:
            self._tactical.draw(
                self.canvas,
                world,
                camera,
                gravity_field,
                hud_top=hud_top,
                powerup_stacks=campaign.powerup_stacks,
            )
        else:
            camera.set_play_layout(hud_top)
            self._perspective.draw(
                self.canvas,
                world,
                camera,
                gravity_field,
                hud_top=hud_top,
                powerup_stacks=campaign.powerup_stacks,
            )

        self._hud.draw_playfield_chrome(
            self.canvas,
            world,
            hud_top,
            camera_mode=camera.mode,
            camera_mode_flash=camera.mode_flash_ttl > 0.0,
            bounds_alert_flash=camera.bounds_alert_flash_ttl > 0.0,
        )
        self._hud.draw(
            self.canvas,
            world,
            campaign,
            hud_alert=hud_alert,
            bounds_toast_kind=bounds_toast_kind,
            bounds_toast_ttl=bounds_toast_ttl,
            loot_toast_kind=loot_toast_kind,
            loot_toast_is_new=loot_toast_is_new,
            loot_toast_ttl=loot_toast_ttl,
            camera_mode=camera.mode,
            camera_mode_flash=camera.mode_flash_ttl > 0.0,
        )
        if world.status is GameStatus.WON:
            self.canvas.create_text(
                vw // 2,
                vh // 2,
                text="YOU ESCAPED",
                fill=palette.GATE_OPEN,
                font=("Courier", 28, "bold"),
            )

    def draw_chart_briefing(
        self,
        world: GameWorld,
        field: GravityField,
        *,
        campaign: CampaignState,
        upcoming_level_id: str,
        cleared_level_id: str | None = None,
        elapsed: float = 0.0,
    ) -> None:
        self.clear()
        self._chart.draw(
            self.canvas,
            world,
            field,
            campaign=campaign,
            upcoming_level_id=upcoming_level_id,
            cleared_level_id=cleared_level_id,
            elapsed=elapsed,
        )

    def draw_end(
        self,
        won: bool,
        elapsed: float,
        reason: str,
        level_id: str,
        campaign: CampaignState,
        game_over: bool = False,
    ) -> None:
        from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER, next_level_id

        self.clear()
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.BACKGROUND, outline="")
        self._draw_starfield()
        if game_over:
            title = "Campaign over."
            subtitle = reason or "All three lives spent."
            prompt = "Enter: return to title     Esc: title"
        elif won:
            upcoming = next_level_id(level_id)
            if upcoming is not None:
                title = "Treasure route cleared!" if level_id == "cove" else "Star chart cleared!"
                subtitle = f"Finished in {elapsed:0.2f}s — next: {LEVEL_LABELS[upcoming]}"
                level_num = LEVEL_ORDER.index(upcoming) + 1
                prompt = f"Enter: open holo chart for level {level_num}     Esc: title"
            else:
                title = "Campaign complete!"
                subtitle = f"Singularity crossed in {elapsed:0.2f}s. Both charts cleared."
                prompt = "Enter: return to title     Esc: title"
        else:
            title = "Shipwrecked."
            subtitle = (
                f"{reason or 'The void claims another captain.'}   "
                f"Lives left: {campaign.lives}   Hull: {campaign.hull_chunks}/{CHUNKS_PER_LIFE}"
            )
            prompt = "Enter: try again     Esc: title"
        self.canvas.create_text(480, 220, text=title, fill=palette.TEXT, font=("Courier", 30, "bold"))
        self.canvas.create_text(480, 275, text=subtitle, fill=palette.MUTED_TEXT, font=("Courier", 16))
        self.canvas.create_text(480, 355, text=prompt, fill=palette.TEXT, font=("Courier", 15))
        if campaign.powerup_stacks:
            perks = "Carried loot: " + ", ".join(
                f"{POWERUP_LABELS[kind]}" + (f" ×{count}" if count > 1 else "")
                for kind, count in sorted(campaign.powerup_stacks.items(), key=lambda item: item[0].name)
                if count > 0
            )
            self.canvas.create_text(480, 410, text=perks, fill=palette.MUTED_TEXT, font=("Courier", 12))

    def _draw_starfield(self, dense: bool = False) -> None:
        count = 140 if dense else 80
        for i in range(count):
            x = (i * 83 + 17) % 960
            y = (i * 47 + 31) % 640
            size = 3 if dense and i % 5 == 0 else 2
            tone = "#3a5570" if dense and i % 7 == 0 else "#294764"
            self.canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")

    def _draw_demo_ship(self, pos: Vec2, angle: float, scale: float) -> None:
        from gravity_ho_matey.render.camera import CameraMode
        from gravity_ho_matey.render.lighting import LightRig
        from gravity_ho_matey.render.world_draw import draw_ship

        rig = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
        draw_ship(self.canvas, pos, angle, boost_energy=1.0, scale=scale, rig=rig)
