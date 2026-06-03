from __future__ import annotations

from gravity_ho_matey.scenes.base import Scene, SceneHost


class TitleScene(Scene):
    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_title()

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        if keysym.lower() == "return":
            from gravity_ho_matey.scenes.play import PlayScene
            host.set_scene(PlayScene())
