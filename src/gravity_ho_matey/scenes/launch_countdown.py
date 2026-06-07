from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.narrative.launch_countdown import launch_countdown_for
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.play_session import PlaySession, build_play_session


@dataclass(slots=True)
class LaunchCountdownScene(Scene):
    """3-2-1 beat after intro GIF — sector + HUD fade in, then live play."""

    level_id: str
    campaign: CampaignState
    session: PlaySession | None = None
    step_index: int = 0
    step_elapsed: float = 0.0
    total_elapsed: float = 0.0

    def __post_init__(self) -> None:
        self._spec = launch_countdown_for(self.level_id)

    def on_enter(self, host: SceneHost) -> None:
        if self.session is None:
            self.session = build_play_session(self.level_id, self.campaign)

    def update(self, host: SceneHost, dt: float) -> None:
        if self.session is None:
            return
        self.step_elapsed += dt
        self.total_elapsed += dt
        if self.step_elapsed >= self._spec.step_seconds:
            self.step_index += 1
            self.step_elapsed = 0.0
            if self.step_index >= len(self._spec.digits):
                self._enter_play(host)

    def draw(self, host: SceneHost) -> None:
        if self.session is None or self.step_index >= len(self._spec.digits):
            return
        reveal = min(1.0, self.total_elapsed / max(0.01, self._spec.total_seconds))
        host.renderer.draw_launch_countdown(
            self.session,
            reveal=reveal,
            digit=self._spec.digits[self.step_index],
            step_index=self.step_index,
            digits=self._spec.digits,
            step_elapsed=self.step_elapsed,
            step_seconds=self._spec.step_seconds,
            total_elapsed=self.total_elapsed,
            total_seconds=self._spec.total_seconds,
        )

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key in ("return", "space"):
            self._enter_play(host)

    def _enter_play(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.play import PlayScene

        assert self.session is not None
        host.set_scene(PlayScene.from_session(self.session))
