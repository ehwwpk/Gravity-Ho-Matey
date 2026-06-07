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

    def __post_init__(self) -> None:
        self.hover_id: str | None = None

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_end(
            self.won,
            self.elapsed,
            self.reason,
            self.level_id,
            self.campaign,
            self.game_over,
            hover_id=self.hover_id,
        )

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        self.hover_id = host.renderer.end_hit_test(x, y)

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        if button != 1:
            return
        hit = host.renderer.end_hit_test(x, y)
        if hit == "action_retry":
            self._retry(host)
        elif hit == "action_next":
            self._next_chart(host)
        elif hit == "action_title":
            self._title(host)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key == "return":
            if self.game_over:
                self._title(host)
            elif self.won:
                upcoming = next_level_id(self.level_id)
                if upcoming is not None:
                    self._next_chart(host)
                else:
                    self._title(host)
            else:
                self._retry(host)
        elif key == "escape":
            self._title(host)

    def _title(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.title import TitleScene

        host.set_scene(TitleScene())

    def _retry(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        host.set_scene(start_play(self.level_id, self.campaign))

    def _next_chart(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.game_flow import start_chart_briefing

        upcoming = next_level_id(self.level_id)
        if upcoming is None:
            self._title(host)
            return
        host.set_scene(
            start_chart_briefing(
                upcoming,
                campaign=self.campaign,
                cleared_level_id=self.level_id,
                elapsed=self.elapsed,
            )
        )
