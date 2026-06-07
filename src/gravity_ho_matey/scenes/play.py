from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.progress import record_level_cleared
from gravity_ho_matey.gameplay.session import (
    LOOT_TOAST_SECONDS,
    capture_level_spawn,
    ensure_active_life_hull,
    recover_ship_in_place,
    respawn_ship_at_spawn,
    wire_world_for_campaign,
)
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_BOUNDS_TOAST_SECONDS,
    ChartBoundsToast,
    ship_in_chart,
)
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.levels.level_registry import build_level, next_level_id
from gravity_ho_matey.render.camera import CHASE_BEACON_CAPTURE_SLACK, CameraMode, ViewCamera
from gravity_ho_matey.scenes.base import Scene, SceneHost


class PlayScene(Scene):
    def __init__(self, level_id: str, campaign: CampaignState) -> None:
        self.level_id = level_id
        self.campaign = campaign
        ensure_active_life_hull(campaign)
        self.world = build_level(level_id)
        capture_level_spawn(self.world)
        self.camera = ViewCamera()
        self.gravity_field = GravityField.bake(
            self.world.wells,
            world_width=self.world.config.width,
            world_height=self.world.config.height,
            cols=32,
            rows=max(32, int(32 * self.world.config.height / max(1, self.world.config.width))),
            gravity_scale=self.world.config.gravity_scale,
        )
        self.hud_alert = ""
        self.hud_alert_ttl = 0.0
        self.bounds_toast_kind: ChartBoundsToast | None = None
        self.bounds_toast_ttl = 0.0
        self._ship_was_in_chart: bool | None = None
        self.loot_toast_kind: PowerUpKind | None = None
        self.loot_toast_is_new = False
        self.loot_toast_ttl = 0.0
        wire_world_for_campaign(self.world, campaign, on_powerup_collected_hud=self._on_powerup_collected_hud)
        self.world.refresh_threat_snapshots()
        self._sync_chart_bounds_state(suppress_toast=True)

    def _sync_chart_bounds_state(self, *, suppress_toast: bool) -> None:
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

    def _on_powerup_collected_hud(self, kind: PowerUpKind, is_new: bool) -> None:
        self.loot_toast_kind = kind
        self.loot_toast_is_new = is_new
        self.loot_toast_ttl = LOOT_TOAST_SECONDS

    def update(self, host: SceneHost, dt: float) -> None:
        from gravity_ho_matey.scenes.end import EndScene

        self.camera.tick(dt)
        self.camera.update_follow(self.world.ship.pos, self.world.config, dt)
        self.camera.update_chase_heading(self.world.ship.angle, dt)
        self.camera.update_chase_velocity(self.world.ship.vel, self.world.ship.angle, self.world.config, dt)

        if self.hud_alert_ttl > 0.0:
            self.hud_alert_ttl = max(0.0, self.hud_alert_ttl - dt)
        if self.bounds_toast_ttl > 0.0:
            self.bounds_toast_ttl = max(0.0, self.bounds_toast_ttl - dt)
            if self.bounds_toast_ttl <= 0.0:
                self.bounds_toast_kind = None
        if self.loot_toast_ttl > 0.0:
            self.loot_toast_ttl = max(0.0, self.loot_toast_ttl - dt)
            if self.loot_toast_ttl <= 0.0:
                self.loot_toast_kind = None

        capture_slack = CHASE_BEACON_CAPTURE_SLACK if self.camera.mode is CameraMode.CHASE else 0.0
        self.world.update(
            dt,
            host.input_state.to_control_intent(),
            beacon_capture_slack=capture_slack,
        )
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

            if damage.source in (DamageSource.CHART_RADIATION, DamageSource.SQUID_CLING):
                recover_ship_in_place(self.world)
                self._sync_chart_bounds_state(suppress_toast=True)
                if damage.source is DamageSource.CHART_RADIATION:
                    self.hud_alert = (
                        f"RADIATION BURN — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
                else:
                    self.hud_alert = (
                        f"SQUID CLING — {result.hull_chunks} CHUNK"
                        f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                    )
            else:
                respawn_ship_at_spawn(self.world)
                self._sync_chart_bounds_state(suppress_toast=True)
                self.hud_alert = (
                    f"HULL STRUCK — {result.hull_chunks} CHUNK"
                    f"{'S' if result.hull_chunks != 1 else ''} LEFT"
                )
            self.hud_alert_ttl = 0.55

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_world(
            self.world,
            self.campaign,
            self.camera,
            self.gravity_field,
            hud_alert=self.hud_alert if self.hud_alert_ttl > 0.0 else "",
            bounds_toast_kind=self.bounds_toast_kind,
            bounds_toast_ttl=self.bounds_toast_ttl,
            loot_toast_kind=self.loot_toast_kind,
            loot_toast_is_new=self.loot_toast_is_new,
            loot_toast_ttl=self.loot_toast_ttl,
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        key = keysym.lower()
        if key == "v":
            self.camera.cycle_mode()
        elif key == "r":
            host.set_scene(start_play(self.level_id, self.campaign))
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene

            host.set_scene(TitleScene())
