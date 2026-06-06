from __future__ import annotations

from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.game_flow import start_play


class TitleScene(Scene):
    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_title()

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key in ("return", "1"):
            host.set_scene(start_play("cove"))
        elif key == "2" and is_level_selectable("solar"):
            host.set_scene(start_play("solar"))
