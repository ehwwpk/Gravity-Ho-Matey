from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.narrative.startup_splash import (
    SKIP_DEBOUNCE_SECONDS,
    has_startup_splash,
    resolve_playback_seconds,
    startup_asset_path,
)
from gravity_ho_matey.render.animated_image import AnimatedImageSequence
from gravity_ho_matey.scenes.base import Scene, SceneHost


@dataclass(slots=True)
class StartupSplashScene(Scene):
    """Once-per-launch welcome GIF before the main title hub."""

    elapsed: float = 0.0
    _frame_index: int = 0
    _frame_elapsed: float = 0.0
    _playback_seconds: float = 0.0
    _sequence: AnimatedImageSequence | None = field(default=None, repr=False)
    _ready: bool = False

    def on_enter(self, host: SceneHost) -> None:
        if not has_startup_splash():
            self._go_title(host)
            return
        try:
            self._sequence = AnimatedImageSequence.load(
                startup_asset_path(),
                max_width=960,
                max_height=640,
                master=host.renderer.canvas,
            )
            self._playback_seconds = resolve_playback_seconds(self._sequence)
            self._ready = True
        except (OSError, ValueError, RuntimeError):
            self._go_title(host)

    def update(self, host: SceneHost, dt: float) -> None:
        if not self._ready or self._sequence is None or self._playback_seconds <= 0.0:
            return
        self.elapsed += dt
        self._frame_elapsed += dt
        delay = self._sequence.delay_seconds(self._frame_index)
        last_frame = self._sequence.frame_count - 1
        if self._frame_index < last_frame and self._frame_elapsed >= delay:
            self._frame_elapsed = 0.0
            self._frame_index += 1

        if self.elapsed >= self._playback_seconds:
            self._go_title(host)

    def draw(self, host: SceneHost) -> None:
        if not self._ready or self._sequence is None or self._playback_seconds <= 0.0:
            return
        progress = min(1.0, self.elapsed / self._playback_seconds)
        host.renderer.draw_startup_splash(
            frame_image=self._sequence.frame(self._frame_index),
            elapsed=self.elapsed,
            playback_seconds=self._playback_seconds,
            progress=progress,
            show_skip_hint=self.elapsed >= SKIP_DEBOUNCE_SECONDS,
        )

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        _ = x, y
        if button != 1:
            return
        if self.elapsed >= SKIP_DEBOUNCE_SECONDS:
            self._go_title(host)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        if self.elapsed < SKIP_DEBOUNCE_SECONDS:
            return
        if keysym.lower() in ("return", "space", "escape"):
            self._go_title(host)

    def _go_title(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.title import TitleScene

        host.set_scene(TitleScene())
