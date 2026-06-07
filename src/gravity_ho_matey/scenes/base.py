from __future__ import annotations

from typing import Protocol

from gravity_ho_matey.render.tk_renderer import TkRenderer
from gravity_ho_matey.util.input import InputState


class SceneHost(Protocol):
    input_state: InputState
    renderer: TkRenderer

    def set_scene(self, scene: "Scene") -> None: ...


class Scene:
    def on_enter(self, host: SceneHost) -> None:
        pass

    def update(self, host: SceneHost, dt: float) -> None:
        pass

    def draw(self, host: SceneHost) -> None:
        pass

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        pass

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        pass

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        pass
