from __future__ import annotations

from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.levels.level_data import build_cove_run_level
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.end import EndScene


class PlayScene(Scene):
    def __init__(self) -> None:
        self.world = build_cove_run_level()

    def update(self, host: SceneHost, dt: float) -> None:
        self.world.update(dt, host.input_state.to_control_intent())
        if self.world.status is GameStatus.WON:
            host.set_scene(EndScene(won=True, elapsed=self.world.elapsed))
        elif self.world.status is GameStatus.LOST:
            host.set_scene(EndScene(won=False, elapsed=self.world.elapsed, reason=self.world.loss_reason))

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_world(self.world)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key == "r":
            host.set_scene(PlayScene())
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene
            host.set_scene(TitleScene())
