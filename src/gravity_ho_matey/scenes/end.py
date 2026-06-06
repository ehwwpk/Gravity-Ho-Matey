from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.levels.level_registry import next_level_id
from gravity_ho_matey.scenes.base import Scene, SceneHost


@dataclass(slots=True)
class EndScene(Scene):
    won: bool
    elapsed: float
    campaign: CampaignState
    reason: str = ""
    level_id: str = "cove"
    game_over: bool = False

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_end(
            self.won,
            self.elapsed,
            self.reason,
            self.level_id,
            self.campaign,
            self.game_over,
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play
        from gravity_ho_matey.scenes.title import TitleScene

        key = keysym.lower()
        if key == "return":
            if self.game_over:
                host.set_scene(TitleScene())
                return
            if self.won:
                upcoming = next_level_id(self.level_id)
                if upcoming is not None:
                    host.set_scene(start_play(upcoming, self.campaign))
                else:
                    host.set_scene(TitleScene())
            else:
                host.set_scene(start_play(self.level_id, self.campaign))
        elif key == "escape":
            host.set_scene(TitleScene())
