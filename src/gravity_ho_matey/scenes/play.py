from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.progress import record_level_cleared
from gravity_ho_matey.gameplay.session import (
    capture_level_spawn,
    ensure_active_life_hull,
    respawn_ship_at_spawn,
    wire_world_for_campaign,
)
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.scenes.base import Scene, SceneHost


class PlayScene(Scene):
    def __init__(self, level_id: str, campaign: CampaignState) -> None:
        self.level_id = level_id
        self.campaign = campaign
        ensure_active_life_hull(campaign)
        self.world = build_level(level_id)
        capture_level_spawn(self.world)
        wire_world_for_campaign(self.world, campaign)
        self.hud_alert = ""
        self.hud_alert_ttl = 0.0

    def update(self, host: SceneHost, dt: float) -> None:
        from gravity_ho_matey.scenes.end import EndScene

        if self.hud_alert_ttl > 0.0:
            self.hud_alert_ttl = max(0.0, self.hud_alert_ttl - dt)

        self.world.update(dt, host.input_state.to_control_intent())

        if self.world.status is GameStatus.WON:
            record_level_cleared(self.level_id)
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
            result = self.campaign.apply_damage(
                self.world.last_damage,
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

            respawn_ship_at_spawn(self.world)
            self.hud_alert = f"HULL STRUCK — {result.hull_chunks} CHUNK{'S' if result.hull_chunks != 1 else ''} LEFT"
            self.hud_alert_ttl = 0.55

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_world(
            self.world,
            self.campaign,
            hud_alert=self.hud_alert if self.hud_alert_ttl > 0.0 else "",
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        key = keysym.lower()
        if key == "r":
            host.set_scene(start_play(self.level_id, self.campaign))
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene

            host.set_scene(TitleScene())
