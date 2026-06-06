from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.scenes.base import Scene, SceneHost


@dataclass(slots=True)
class ChartBriefingScene(Scene):
    """Diegetic holo-map between cleared sectors and the next launch."""

    upcoming_level_id: str
    campaign: CampaignState
    cleared_level_id: str
    elapsed: float

    def __post_init__(self) -> None:
        self._preview = build_level(self.upcoming_level_id)
        self._field = GravityField.bake(
            self._preview.wells,
            world_width=self._preview.config.width,
            world_height=self._preview.config.height,
            cols=24,
            rows=max(24, int(24 * self._preview.config.height / max(1, self._preview.config.width))),
            gravity_scale=self._preview.config.gravity_scale,
        )

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_chart_briefing(
            self._preview,
            self._field,
            campaign=self.campaign,
            upcoming_level_id=self.upcoming_level_id,
            cleared_level_id=self.cleared_level_id,
            elapsed=self.elapsed,
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play
        from gravity_ho_matey.scenes.title import TitleScene

        key = keysym.lower()
        if key == "return":
            host.set_scene(start_play(self.upcoming_level_id, self.campaign))
        elif key == "escape":
            host.set_scene(TitleScene())
