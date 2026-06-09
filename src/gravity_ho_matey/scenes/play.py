from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.gameplay.progress import record_level_cleared
from gravity_ho_matey.gameplay.session import (
    chip_damage_recovers_in_place,
    recover_eva_in_place,
    recover_ship_in_place,
    wire_world_for_campaign,
)
from gravity_ho_matey.gameplay.jewel_config import TREASURY_FLASH_SECONDS
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_BOUNDS_TOAST_SECONDS,
    ChartBoundsToast,
    ship_in_chart,
)
from gravity_ho_matey.levels.level_registry import next_level_id
from gravity_ho_matey.render.camera import CHASE_BEACON_CAPTURE_SLACK, CameraMode, ViewCamera
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.play_session import PlaySession, build_play_session


class PlayScene(Scene):
    def __init__(self, level_id: str, campaign: CampaignState) -> None:
        self._init_from_session(build_play_session(level_id, campaign))

    @classmethod
    def from_session(cls, session: PlaySession) -> PlayScene:
        scene = cls.__new__(cls)
        scene._init_from_session(session)
        return scene

    def _init_from_session(self, session: PlaySession) -> None:
        self.level_id = session.level_id
        self.campaign = session.campaign
        self.world = session.world
        self.camera = session.camera
        self.gravity_field = session.gravity_field
        self.hud_alert = session.hud_alert
        self.hud_alert_ttl = session.hud_alert_ttl
        self.bounds_toast_kind = session.bounds_toast_kind
        self.bounds_toast_ttl = session.bounds_toast_ttl
        self._ship_was_in_chart = session.ship_was_in_chart
        self.treasury_flash_ttl = session.treasury_flash_ttl
        self._transition_sequence = None
        self._transition_frame_index = 0
        self._transition_frame_elapsed = 0.0
        self._transition_frame_hold: object | None = None
        self._transition_loaded_stem: str = ""
        self._prev_boost_flash: float = 0.0
        wire_world_for_campaign(
            self.world,
            self.campaign,
            on_jewels_collected_hud=self._on_jewels_collected_hud,
        )
        self._prev_boost_flash = self.world.ship.boost_flash

    def _sync_chart_bounds_state(self, *, suppress_toast: bool) -> None:
        from gravity_ho_matey.gameplay.expedition_mission import is_expedition_foot

        if is_expedition_foot(self.world.config):
            self._ship_was_in_chart = True
            return
        if self.world.expedition is not None and self.world.expedition.in_cinematic:
            self._ship_was_in_chart = True
            return
        if not self.world.config.open_bounds:
            self._ship_was_in_chart = True
            return
        in_chart = ship_in_chart(self.world.ship.pos, self.world.config)
        if suppress_toast or self._ship_was_in_chart is None:
            self._ship_was_in_chart = in_chart
            return
        if in_chart == self._ship_was_in_chart:
            return
        self._ship_was_in_chart = in_chart
        self.bounds_toast_kind = (
            ChartBoundsToast.ENTERED_CHART if in_chart else ChartBoundsToast.LEFT_CHART
        )
        self.bounds_toast_ttl = CHART_BOUNDS_TOAST_SECONDS
        self.camera.flash_bounds_alert()

    def _on_jewels_collected_hud(self, amount: int) -> None:
        _ = amount
        self.treasury_flash_ttl = TREASURY_FLASH_SECONDS

    def _playfield_hud_top(self) -> float:
        return SciFiHudOverlay.playfield_top(
            hud_alert=self.hud_alert if self.hud_alert_ttl > 0.0 else "",
            bounds_toast_kind=self.bounds_toast_kind,
            bounds_toast_ttl=self.bounds_toast_ttl,
        )

    def _update_camera(self, dt: float) -> None:
        if self._expedition_on_foot() and self.world.avatar is not None:
            self.camera.set_play_layout(self._playfield_hud_top())
            self.camera.update_follow(self.world.avatar.pos, self.world.config, dt)
            return
        self.camera.set_play_layout(self._playfield_hud_top())
        self.camera.update_follow(self.world.ship.pos, self.world.config, dt)
        self.camera.update_chase_heading(self.world.ship.angle, dt)
        boost_tapped = (
            self.world.ship.boost_flash > 0.0 and self._prev_boost_flash <= 0.0
        )
        self.camera.update_chase_dynamics(
            self.world.ship.vel,
            self.world.ship.angle,
            self.world.config,
            dt,
            boost_flash=self.world.ship.boost_flash,
            boost_energy=self.world.ship.boost_energy,
            boost_tapped=boost_tapped,
        )
        self._prev_boost_flash = self.world.ship.boost_flash

    def update(self, host: SceneHost, dt: float) -> None:
        from gravity_ho_matey.scenes.end import EndScene

        self.camera.tick(dt)

        if self.hud_alert_ttl > 0.0:
            self.hud_alert_ttl = max(0.0, self.hud_alert_ttl - dt)
        if self.bounds_toast_ttl > 0.0:
            self.bounds_toast_ttl = max(0.0, self.bounds_toast_ttl - dt)
            if self.bounds_toast_ttl <= 0.0:
                self.bounds_toast_kind = None
        if self.treasury_flash_ttl > 0.0:
            self.treasury_flash_ttl = max(0.0, self.treasury_flash_ttl - dt)

        capture_slack = CHASE_BEACON_CAPTURE_SLACK if self.camera.mode is CameraMode.CHASE else 0.0
        interaction_hold = (
            host.input_state.down("e") if hasattr(host.input_state, "down") else False
        )
        rebake = self.world.update(
            dt,
            host.input_state.to_control_intent(),
            beacon_capture_slack=capture_slack,
            interaction_hold=interaction_hold,
            aim_world=self._expedition_aim_world(host),
        )
        if rebake:
            self._rebuild_gravity_field()
            if self._expedition_on_foot():
                self._snap_expedition_camera()
            else:
                self.camera.snap_tactical_to_ship(self.world.ship.pos, self.world.config)
        self._tick_brood_transition(dt)
        self._tick_expedition_transition(dt)
        from gravity_ho_matey.gameplay.drone_session import sync_drone_wingman_to_campaign
        from gravity_ho_matey.gameplay.nifflerp_session import sync_nifflerp_to_campaign

        sync_drone_wingman_to_campaign(self.world, self.campaign)
        sync_nifflerp_to_campaign(self.world, self.campaign)
        self._sync_chart_bounds_state(suppress_toast=False)

        if self.world.status is GameStatus.WON:
            record_level_cleared(self.level_id)
            upcoming = next_level_id(self.level_id)
            if upcoming is not None:
                from gravity_ho_matey.scenes.game_flow import start_chart_briefing

                host.set_scene(
                    start_chart_briefing(
                        upcoming,
                        campaign=self.campaign,
                        cleared_level_id=self.level_id,
                        elapsed=self.world.elapsed,
                    )
                )
            else:
                host.set_scene(
                    EndScene(
                        won=True,
                        elapsed=self.world.elapsed,
                        level_id=self.level_id,
                        campaign=self.campaign,
                    )
                )
            return

        if self.world.status is GameStatus.SHIP_HIT and self.world.last_damage is not None:
            damage = self.world.last_damage
            result = self.campaign.apply_damage(
                damage,
                level_theme=self.world.config.level_theme,
            )
            if result.life_lost:
                host.set_scene(
                    EndScene(
                        won=False,
                        elapsed=self.world.elapsed,
                        reason=result.reason,
                        level_id=self.level_id,
                        campaign=self.campaign,
                        game_over=result.campaign_over,
                    )
                )
                return

            if chip_damage_recovers_in_place(life_lost=result.life_lost):
                if self._expedition_on_foot():
                    recover_eva_in_place(self.world)
                else:
                    recover_ship_in_place(self.world)
                self.camera.reset_chase_presentation()
                self._prev_boost_flash = self.world.ship.boost_flash
                self._sync_chart_bounds_state(suppress_toast=True)
                if self._expedition_on_foot() and damage.source is DamageSource.SQUID_CLING:
                    self.hud_alert = (
                        f"SUIT BREACH — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT · RTB TO LANDER"
                    )
                elif damage.source is DamageSource.CHART_RADIATION:
                    self.hud_alert = (
                        f"RADIATION BURN — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
                elif damage.source is DamageSource.SQUID_CLING:
                    self.hud_alert = (
                        f"SQUID CLING — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
                elif damage.source is DamageSource.SPACE_JUNK:
                    self.hud_alert = (
                        f"SALVAGE STRIKE — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
                else:
                    self.hud_alert = (
                        f"HULL STRUCK — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
                self.hud_alert_ttl = 0.55

        self._update_camera(dt)
        self._enforce_brood_surface_camera()
        self._enforce_expedition_camera()

    def _expedition_on_foot(self) -> bool:
        from gravity_ho_matey.gameplay.expedition_mission import is_expedition_foot

        return is_expedition_foot(self.world.config)

    def _expedition_in_cinematic(self) -> bool:
        exp = self.world.expedition
        return exp is not None and exp.in_cinematic

    def _expedition_aim_world(self, host: SceneHost):
        from gravity_ho_matey.core.vector import Vec2

        if not self._expedition_on_foot() or self.world.avatar is None:
            return None
        if not hasattr(host, "pointer") and not hasattr(host.input_state, "pointer"):
            return None
        ptr = getattr(host, "pointer", None) or getattr(host.input_state, "pointer", None)
        if ptr is None:
            return None
        follow = self.world.avatar.pos
        hud_top = self._playfield_hud_top()
        self.camera.set_play_layout(hud_top)
        wx = ptr[0] / max(1e-6, self.camera.tactical_scale) + follow.x - self.camera.viewport_width * 0.5 / max(1e-6, self.camera.tactical_scale)
        wy = (ptr[1] - hud_top) / max(1e-6, self.camera.tactical_scale) + follow.y - (self.camera.viewport_height - hud_top) * 0.5 / max(1e-6, self.camera.tactical_scale)
        return Vec2(wx, wy)

    def _snap_expedition_camera(self) -> None:
        if self.world.avatar is None:
            return
        self.camera.mode = CameraMode.TACTICAL
        self.camera.set_play_layout(self._playfield_hud_top())
        self.camera.snap_tactical_to_ship(self.world.avatar.pos, self.world.config)

    def _enforce_expedition_camera(self) -> None:
        if not self._expedition_on_foot():
            return
        if self.camera.mode is CameraMode.TACTICAL and self.world.avatar is not None:
            self.camera.set_play_layout(self._playfield_hud_top())
            self.camera.update_follow(self.world.avatar.pos, self.world.config, 0.016)
            return
        self.camera.mode = CameraMode.TACTICAL
        self._snap_expedition_camera()

    def _ensure_expedition_transition_sequence(self, canvas) -> None:
        exp = self.world.expedition
        if exp is None or not exp.in_cinematic:
            return
        if self._transition_loaded_stem != exp.transition_asset_stem:
            self._transition_sequence = None
            self._transition_frame_index = 0
            self._transition_frame_elapsed = 0.0
            self._transition_frame_hold = None
            self._transition_loaded_stem = exp.transition_asset_stem
        if self._transition_sequence is not None:
            return
        from gravity_ho_matey.gameplay.expedition_mission import resolve_transition_asset
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence

        asset = resolve_transition_asset(exp.transition_asset_stem)
        if asset is None:
            return
        try:
            self._transition_sequence = AnimatedImageSequence.load(
                asset, max_width=900, max_height=460, master=canvas
            )
            from gravity_ho_matey.levels.comet_fuel_layout import CINEMATIC_DEFAULT_SECONDS

            exp.cinematic_seconds = CINEMATIC_DEFAULT_SECONDS
            self._transition_frame_hold = self._transition_sequence.frame(0)
        except (OSError, ValueError, RuntimeError, tk.TclError):
            self._transition_sequence = None
            self._transition_frame_hold = None

    def _tick_expedition_transition(self, dt: float) -> None:
        exp = self.world.expedition
        if exp is None or not exp.in_cinematic:
            return
        if self._transition_sequence is None:
            return
        self._transition_frame_elapsed += dt
        delay = self._transition_sequence.delay_seconds(self._transition_frame_index)
        last_frame = self._transition_sequence.frame_count - 1
        if self._transition_frame_index < last_frame and self._transition_frame_elapsed >= delay:
            self._transition_frame_elapsed = 0.0
            self._transition_frame_index += 1
            self._transition_frame_hold = self._transition_sequence.frame(self._transition_frame_index)

    def _skip_expedition_cinematic(self) -> None:
        exp = self.world.expedition
        if exp is None or not exp.in_cinematic:
            return
        exp.cinematic_elapsed = exp.cinematic_seconds
        rebake = self.world.update(0.0, ControlIntent(), interaction_hold=False)
        if rebake:
            self._rebuild_gravity_field()
            if self._expedition_on_foot():
                self._snap_expedition_camera()
            else:
                self.camera.snap_tactical_to_ship(self.world.ship.pos, self.world.config)

    def _brood_on_surface(self) -> bool:
        bm = self.world.brood_moon
        return bm is not None and bm.on_surface

    def _enforce_brood_surface_camera(self) -> None:
        """Surface is a side-scroll chart — chase cam is open-space projection and breaks reads."""
        if not self._brood_on_surface():
            return
        if self.camera.mode is CameraMode.TACTICAL:
            return
        self.camera.mode = CameraMode.TACTICAL
        self.camera.reset_chase_presentation()
        self.camera.set_play_layout(self._playfield_hud_top())
        self.camera.snap_tactical_to_ship(self.world.ship.pos, self.world.config)

    def _rebuild_gravity_field(self) -> None:
        from gravity_ho_matey.gameplay.gravity_field import GravityField

        self.gravity_field = GravityField.bake(
            self.world.wells,
            world_width=self.world.config.width,
            world_height=self.world.config.height,
            cols=32,
            rows=max(32, int(32 * self.world.config.height / max(1, self.world.config.width))),
            gravity_scale=self.world.config.gravity_scale,
        )

    def _ensure_transition_sequence(self, canvas) -> None:
        bm = self.world.brood_moon
        if bm is None or not bm.in_cinematic:
            return
        if self._transition_loaded_stem != bm.transition_asset_stem:
            self._transition_sequence = None
            self._transition_frame_index = 0
            self._transition_frame_elapsed = 0.0
            self._transition_frame_hold = None
            self._transition_loaded_stem = bm.transition_asset_stem
        if self._transition_sequence is not None:
            return
        from gravity_ho_matey.gameplay.brood_moon_mission import resolve_transition_asset
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence

        asset = resolve_transition_asset(bm.transition_asset_stem)
        if asset is None:
            return
        try:
            self._transition_sequence = AnimatedImageSequence.load(
                asset,
                max_width=900,
                max_height=460,
                master=canvas,
            )
            bm.cinematic_seconds = max(
                bm.cinematic_seconds,
                self._transition_sequence.duration_seconds(),
            )
            self._transition_frame_hold = self._transition_sequence.frame(0)
        except (OSError, ValueError, RuntimeError, tk.TclError):
            self._transition_sequence = None
            self._transition_frame_hold = None

    def _tick_brood_transition(self, dt: float) -> None:
        bm = self.world.brood_moon
        if bm is None or not bm.in_cinematic:
            self._transition_sequence = None
            self._transition_frame_hold = None
            return
        if self._transition_sequence is None:
            return
        self._transition_frame_elapsed += dt
        delay = self._transition_sequence.delay_seconds(self._transition_frame_index)
        last_frame = self._transition_sequence.frame_count - 1
        if self._transition_frame_index < last_frame and self._transition_frame_elapsed >= delay:
            self._transition_frame_elapsed = 0.0
            self._transition_frame_index += 1
            self._transition_frame_hold = self._transition_sequence.frame(self._transition_frame_index)

    def _skip_brood_cinematic(self) -> None:
        bm = self.world.brood_moon
        if bm is None or not bm.in_cinematic:
            return
        bm.cinematic_elapsed = bm.cinematic_seconds
        rebake = self.world.update(0.0, ControlIntent(), interaction_hold=False)
        if rebake:
            self._rebuild_gravity_field()
            self.camera.snap_tactical_to_ship(self.world.ship.pos, self.world.config)

    def draw(self, host: SceneHost) -> None:
        exp = self.world.expedition
        if exp is not None and exp.in_cinematic:
            self._ensure_expedition_transition_sequence(host.renderer.canvas)
            frame = self._transition_frame_hold
            if self._transition_sequence is not None:
                frame = self._transition_sequence.frame(self._transition_frame_index)
                self._transition_frame_hold = frame
            host.renderer.draw_expedition_transition(self.world, frame_image=frame)
            return
        bm = self.world.brood_moon
        if bm is not None and bm.in_cinematic:
            self._ensure_transition_sequence(host.renderer.canvas)
            frame = self._transition_frame_hold
            if self._transition_sequence is not None:
                frame = self._transition_sequence.frame(self._transition_frame_index)
                self._transition_frame_hold = frame
            host.renderer.draw_brood_transition(self.world, frame_image=frame)
            return
        host.renderer.draw_world(
            self.world,
            self.campaign,
            self.camera,
            self.gravity_field,
            hud_alert=self.hud_alert if self.hud_alert_ttl > 0.0 else "",
            bounds_toast_kind=self.bounds_toast_kind,
            bounds_toast_ttl=self.bounds_toast_ttl,
            treasury_flash_ttl=self.treasury_flash_ttl,
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        key = keysym.lower()
        if key == "space" and self.world.brood_moon is not None and self.world.brood_moon.in_cinematic:
            self._skip_brood_cinematic()
            return
        if key == "space" and self.world.expedition is not None and self.world.expedition.in_cinematic:
            self._skip_expedition_cinematic()
            return
        if key == "v":
            if self._expedition_on_foot():
                self.hud_alert = "EVA · A/D TURN · W/S FWD·BACK · SHIFT RUN · SPACE FIRE · E WORK"
                self.hud_alert_ttl = 2.2
                self._enforce_expedition_camera()
                return
            if self._brood_on_surface():
                self.hud_alert = "SURFACE OPS — TACTICAL CHART VIEW ONLY"
                self.hud_alert_ttl = 1.4
                self._enforce_brood_surface_camera()
                return
            self.camera.cycle_mode()
            self._prev_boost_flash = self.world.ship.boost_flash
            if self.camera.mode is CameraMode.TACTICAL:
                self.camera.set_play_layout(self._playfield_hud_top())
                self.camera.snap_tactical_to_ship(self.world.ship.pos, self.world.config)
        elif key == "r":
            host.set_scene(start_play(self.level_id, self.campaign))
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene

            host.set_scene(TitleScene())
