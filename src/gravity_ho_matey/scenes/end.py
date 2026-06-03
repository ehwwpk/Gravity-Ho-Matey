from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.scenes.base import Scene, SceneHost


@dataclass(slots=True)
class EndScene(Scene):
    won: bool
    elapsed: float
    reason: str = ""

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_end(self.won, self.elapsed, self.reason)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key == "return":
            from gravity_ho_matey.scenes.play import PlayScene
            host.set_scene(PlayScene())
        elif key == "escape":
            from gravity_ho_matey.scenes.title import TitleScene
            host.set_scene(TitleScene())
