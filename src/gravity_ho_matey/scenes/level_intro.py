from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.narrative.level_intros import (
    LevelIntroSpec,
    intro_spec_for,
    resolve_intro_asset,
    resolve_playback_seconds,
)
from gravity_ho_matey.render.animated_image import AnimatedImageSequence
from gravity_ho_matey.scenes.base import Scene, SceneHost


@dataclass(slots=True)
class LevelIntroScene(Scene):
    """Post-holo narrative beat — plays sector intro GIF/PNG, then launches play."""

    level_id: str
    campaign: CampaignState
    elapsed: float = 0.0
    _frame_index: int = 0
    _frame_elapsed: float = 0.0
    _playback_seconds: float = 0.0
    _sequence: AnimatedImageSequence | None = field(default=None, repr=False)
    _spec: LevelIntroSpec | None = field(default=None, repr=False)
    hover_id: str | None = None

    def on_enter(self, host: SceneHost) -> None:
        self._spec = intro_spec_for(self.level_id)
        if self._spec is None:
            self._launch_play(host)
            return
        asset = resolve_intro_asset(self._spec)
        if asset is None:
            self._launch_play(host)
            return
        try:
            self._sequence = AnimatedImageSequence.load(
                asset,
                max_width=900,
                max_height=460,
                master=host.renderer.canvas,
            )
            self._playback_seconds = resolve_playback_seconds(self._spec, self._sequence)
        except (OSError, ValueError, RuntimeError):
            self._launch_play(host)

    def update(self, host: SceneHost, dt: float) -> None:
        if self._sequence is None or self._spec is None or self._playback_seconds <= 0.0:
            return
        self.elapsed += dt
        self._frame_elapsed += dt
        delay = self._sequence.delay_seconds(self._frame_index)
        last_frame = self._sequence.frame_count - 1
        if self._frame_index < last_frame and self._frame_elapsed >= delay:
            self._frame_elapsed = 0.0
            self._frame_index += 1

        if self.elapsed >= self._playback_seconds:
            self._launch_play(host)

    def draw(self, host: SceneHost) -> None:
        if self._sequence is None or self._spec is None or self._playback_seconds <= 0.0:
            return
        progress = min(1.0, self.elapsed / self._playback_seconds)
        host.renderer.draw_level_intro(
            level_id=self.level_id,
            spec=self._spec,
            frame_image=self._sequence.frame(self._frame_index),
            elapsed=self.elapsed,
            playback_seconds=self._playback_seconds,
            progress=progress,
            hover_id=self.hover_id,
        )

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        self.hover_id = host.renderer.level_intro_hit_test(x, y)

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        if button != 1:
            return
        if host.renderer.level_intro_hit_test(x, y) == "skip_intro":
            self._launch_play(host)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key in ("return", "space", "escape"):
            self._launch_play(host)

    def _launch_play(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.game_flow import start_launch_countdown

        host.set_scene(start_launch_countdown(self.level_id, self.campaign))
