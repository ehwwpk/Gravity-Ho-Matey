from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.chart_bounds import ChartBoundsToast
from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_LABELS
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.chart_map_overlay import ChartMapOverlay
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay
from gravity_ho_matey.render.launch_countdown_overlay import draw_launch_countdown_strip, draw_playfield_reveal
from gravity_ho_matey.render.level_intro_overlay import LevelIntroOverlay
from gravity_ho_matey.render.brood_moon_transition_overlay import BroodMoonTransitionOverlay
from gravity_ho_matey.render.startup_splash_overlay import StartupSplashOverlay
from gravity_ho_matey.render.title_overlay import TitlePage, TitleScreenOverlay
from gravity_ho_matey.render.shop_tree_view import ShopTreeView
from gravity_ho_matey.render.view_renderers import PerspectiveViewRenderer, TacticalViewRenderer


class TkRenderer:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self._hud = SciFiHudOverlay()
        self._title = TitleScreenOverlay()
        self._chart = ChartMapOverlay()
        self._level_intro = LevelIntroOverlay()
        self._startup_splash = StartupSplashOverlay()
        self._brood_transition = BroodMoonTransitionOverlay()
        self._tactical = TacticalViewRenderer()
        self._perspective = PerspectiveViewRenderer()

    def clear(self) -> None:
        self.canvas.delete("all")

    def draw_title(
        self,
        *,
        page: TitlePage = TitlePage.WELCOME,
        campaign: CampaignState | None = None,
        deploy_focus: int = 0,
        deploy_scroll: float = 0.0,
        hover_id: str | None = None,
        elapsed: float = 0.0,
        shop_open: bool = False,
        shop_open_anim: float = 1.0,
        shop_ui: object | None = None,
        codex: TitleCodexState | None = None,
    ) -> None:
        from gravity_ho_matey.gameplay.campaign import CampaignState as _CampaignState
        from gravity_ho_matey.render.title_codex import TitleCodexState as _TitleCodexState

        self.clear()
        self._title.draw(
            self.canvas,
            page=page,
            campaign=campaign or _CampaignState.new(),
            solar_unlocked=is_level_selectable("solar"),
            drift_unlocked=is_level_selectable("drift"),
            rift_unlocked=is_level_selectable("rift"),
            siege_unlocked=is_level_selectable("siege"),
            brood_unlocked=is_level_selectable("brood_moon"),
            deploy_focus=deploy_focus,
            deploy_scroll=deploy_scroll,
            hover_id=hover_id,
            elapsed=elapsed,
            shop_open=shop_open,
            shop_open_anim=shop_open_anim,
            shop_view=shop_ui.view if shop_ui is not None else None,
            shop_ui=shop_ui,
            codex=codex or _TitleCodexState(),
        )

    def title_hit_test(self, x: float, y: float) -> str | None:
        return self._title.hits.hit(x, y)

    def draw_world(
        self,
        world: GameWorld,
        campaign: CampaignState,
        camera: ViewCamera,
        gravity_field: GravityField,
        *,
        hud_alert: str = "",
        bounds_toast_kind: ChartBoundsToast | None = None,
        bounds_toast_ttl: float = 0.0,
        treasury_flash_ttl: float = 0.0,
    ) -> None:
        self.clear()
        vw = camera.viewport_width
        vh = camera.viewport_height
        hud_top = SciFiHudOverlay.playfield_top(
            hud_alert=hud_alert,
            bounds_toast_kind=bounds_toast_kind,
            bounds_toast_ttl=bounds_toast_ttl,
        )

        if camera.mode is CameraMode.TACTICAL:
            camera.set_play_layout(hud_top)
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
            bounds_alert_flash=camera.bounds_alert_flash_ttl > 0.0,
        )
        self._hud.draw(
            self.canvas,
            world,
            campaign,
            hud_alert=hud_alert,
            bounds_toast_kind=bounds_toast_kind,
            bounds_toast_ttl=bounds_toast_ttl,
            treasury_flash_ttl=treasury_flash_ttl,
            camera_mode=camera.mode,
        )
        if world.status is GameStatus.WON:
            self.canvas.create_text(
                vw // 2,
                vh // 2,
                text="YOU ESCAPED",
                fill=palette.GATE_OPEN,
                font=("Courier", 28, "bold"),
            )

    def draw_brood_transition(
        self,
        world: GameWorld,
        *,
        frame_image: tk.PhotoImage | None = None,
    ) -> None:
        self.clear()
        bm = world.brood_moon
        if bm is None:
            return
        self._brood_transition.draw(
            self.canvas,
            bm=bm,
            frame_image=frame_image,
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
        hover_id: str | None = None,
        anim: float = 0.0,
        shop_open: bool = False,
        shop_open_anim: float = 1.0,
        shop_ui: object | None = None,
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
            hover_id=hover_id,
            shop_open=shop_open,
            shop_open_anim=shop_open_anim,
            shop_view=shop_ui.view if shop_ui is not None else None,
            shop_ui=shop_ui,
        )

    def chart_hit_test(self, x: float, y: float) -> str | None:
        return self._chart.hits.hit(x, y)

    def draw_level_intro(
        self,
        *,
        level_id: str,
        spec: object,
        frame_image: object,
        elapsed: float = 0.0,
        playback_seconds: float = 1.0,
        progress: float = 0.0,
        hover_id: str | None = None,
    ) -> None:
        from gravity_ho_matey.narrative.level_intros import LevelIntroSpec

        assert isinstance(spec, LevelIntroSpec)
        self.clear()
        self._level_intro.draw(
            self.canvas,
            level_id=level_id,
            spec=spec,
            frame_image=frame_image,  # type: ignore[arg-type]
            elapsed=elapsed,
            playback_seconds=playback_seconds,
            progress=progress,
            hover_id=hover_id,
        )

    def level_intro_hit_test(self, x: float, y: float) -> str | None:
        return self._level_intro.hits.hit(x, y)

    def draw_startup_splash(
        self,
        *,
        frame_image: object,
        elapsed: float,
        playback_seconds: float,
        progress: float,
        show_skip_hint: bool,
    ) -> None:
        self.clear()
        self._startup_splash.draw(
            self.canvas,
            frame_image=frame_image,  # type: ignore[arg-type]
            elapsed=elapsed,
            playback_seconds=playback_seconds,
            progress=progress,
            show_skip_hint=show_skip_hint,
        )

    def draw_launch_countdown(
        self,
        session: object,
        *,
        reveal: float,
        digit: int,
        step_index: int,
        digits: tuple[int, ...],
        step_elapsed: float,
        step_seconds: float,
        total_elapsed: float,
        total_seconds: float,
    ) -> None:
        from gravity_ho_matey.scenes.play_session import PlaySession

        assert isinstance(session, PlaySession)
        self.draw_world(
            session.world,
            session.campaign,
            session.camera,
            session.gravity_field,
        )
        vw = session.camera.viewport_width
        vh = session.camera.viewport_height
        hud_top = SciFiHudOverlay.playfield_top()
        draw_playfield_reveal(
            self.canvas,
            hud_top=hud_top,
            vw=vw,
            vh=vh,
            reveal=reveal,
            theme=session.world.config.level_theme,
        )
        draw_launch_countdown_strip(
            self.canvas,
            vw=vw,
            vh=vh,
            level_id=session.level_id,
            theme=session.world.config.level_theme,
            digits=digits,
            step_index=step_index,
            current_digit=digit,
            step_elapsed=step_elapsed,
            step_seconds=step_seconds,
            reveal=reveal,
            total_elapsed=total_elapsed,
            total_seconds=total_seconds,
        )

    def draw_end(
        self,
        won: bool,
        elapsed: float,
        reason: str,
        level_id: str,
        campaign: CampaignState,
        game_over: bool = False,
        *,
        hover_id: str | None = None,
    ) -> None:
        from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, next_level_id
        from gravity_ho_matey.render import hud_primitives as hp
        from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button

        self.clear()
        self._end_hits = MenuHitMap()
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.SOLAR_BG, outline="")
        self._draw_starfield(dense=True)

        px, py, pw, ph = 130.0, 120.0, 700.0, 360.0
        hp.draw_panel(self.canvas, px, py, pw, ph, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(self.canvas, px, py, pw, ph, accent=accent)

        if game_over:
            title = "Campaign Over"
            subtitle = reason or "All three lives spent."
            primary_id = "action_title"
            primary_label = "RETURN TO NAV STATION"
            show_secondary = False
        elif won:
            upcoming = next_level_id(level_id)
            if upcoming is not None:
                title = "Sector Cleared"
                subtitle = f"Cleared in {elapsed:0.1f}s · Next: {LEVEL_LABELS[upcoming]}"
                primary_id = "action_next"
                primary_label = "OPEN NEXT CHART"
                show_secondary = True
            else:
                title = "Campaign Complete"
                cleared = LEVEL_LABELS.get(level_id, level_id).split(" — ", 1)[-1]
                subtitle = f"{cleared} cleared in {elapsed:0.1f}s."
                primary_id = "action_title"
                primary_label = "RETURN TO NAV STATION"
                show_secondary = False
        else:
            title = "Shipwrecked"
            subtitle = (
                f"{reason or 'The void claims another captain.'}  "
                f"Lives {campaign.lives} · Hull {campaign.hull_chunks}/{campaign.max_hull_chunks_per_life}"
            )
            primary_id = "action_retry"
            primary_label = "TRY AGAIN"
            show_secondary = True

        self.canvas.create_text(480, py + 48, text=title, fill=palette.TEXT, font=("Courier New", 28, "bold"))
        draw_fitted_text(
            self.canvas,
            480,
            py + 92,
            subtitle,
            max_width=pw - 48,
            color=palette.MUTED_TEXT,
            font=("Courier New", 13),
            anchor="center",
        )

        carry_y = py + 124
        if campaign.jewels > 0:
            draw_fitted_text(
                self.canvas,
                480,
                carry_y,
                f"Treasury: ★ {campaign.jewels}",
                max_width=pw - 48,
                color=palette.JEWEL_CORE,
                font=("Courier New", 11),
                anchor="center",
            )
            carry_y += 18
        if campaign.powerup_stacks:
            perks = "Carried: " + ", ".join(
                f"{POWERUP_LABELS[kind]}" + (f" ×{count}" if count > 1 else "")
                for kind, count in sorted(campaign.powerup_stacks.items(), key=lambda item: item[0].name)
                if count > 0
            )
            draw_fitted_text(
                self.canvas,
                480,
                carry_y,
                perks,
                max_width=pw - 48,
                color=dim,
                font=("Courier New", 11),
                anchor="center",
            )

        btn_w = 220.0
        btn_h = 40.0
        btn_y = py + ph - 88
        if show_secondary:
            primary_x = 480 - btn_w - 12
            secondary_x = 480 + 12
        else:
            primary_x = 480 - btn_w / 2
            secondary_x = 0.0
        self._end_hits.add(primary_id, primary_x, btn_y, btn_w, btn_h)
        draw_menu_button(
            self.canvas,
            primary_x,
            btn_y,
            btn_w,
            btn_h,
            primary_label,
            accent=accent,
            dim=dim,
            frame=frame,
            selected=True,
            hover=hover_id == primary_id,
        )
        if show_secondary:
            self._end_hits.add("action_title", secondary_x, btn_y, btn_w, btn_h)
            draw_menu_button(
                self.canvas,
                secondary_x,
                btn_y,
                btn_w,
                btn_h,
                "← NAV STATION",
                accent=accent,
                dim=dim,
                frame=frame,
                hover=hover_id == "action_title",
            )
        self.canvas.create_text(
            480,
            py + ph - 28,
            text="Click buttons · Enter confirms · Esc to nav station",
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def end_hit_test(self, x: float, y: float) -> str | None:
        hits = getattr(self, "_end_hits", None)
        if hits is None:
            return None
        return hits.hit(x, y)

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
