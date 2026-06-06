from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.progress import record_level_cleared
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.scenes.base import Scene, SceneHost


class PlayScene(Scene):
    def __init__(self, level_id: str, campaign: CampaignState) -> None:
        self.level_id = level_id
        self.campaign = campaign
        self.world = build_level(level_id)
        wire_world_for_campaign(self.world, campaign)

    def update(self, host: SceneHost, dt: float) -> None:
        from gravity_ho_matey.scenes.end import EndScene

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
        elif self.world.status is GameStatus.LOST:
            still_alive = self.campaign.lose_life()
            host.set_scene(
                EndScene(
                    won=False,
                    elapsed=self.world.elapsed,
                    reason=self.world.loss_reason,
                    level_id=self.level_id,
                    campaign=self.campaign,
                    game_over=not still_alive,
                )
            )

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_world(self.world, self.campaign)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        key = keysym.lower()
        if key == "r":
            host.set_scene(start_play(self.level_id, self.campaign))
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene

            host.set_scene(TitleScene())
