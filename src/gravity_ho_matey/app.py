from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.render.tk_renderer import TkRenderer
from gravity_ho_matey.scenes.base import Scene
from gravity_ho_matey.scenes.title import TitleScene
from gravity_ho_matey.settings import APP_TITLE, BACKGROUND, CANVAS_HEIGHT, CANVAS_WIDTH, FRAME_MS
from gravity_ho_matey.util.input import InputState
from gravity_ho_matey.util.timekeeper import TimeKeeper


class GravityHoMateyApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack()
        self.input_state = InputState()
        self.renderer = TkRenderer(self.canvas)
        self.timekeeper = TimeKeeper()
        self.scene: Scene = TitleScene()
        self.scene.on_enter(self)
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)

    def run(self) -> None:
        self.timekeeper.reset()
        self._tick()
        self.root.mainloop()

    def set_scene(self, scene: Scene) -> None:
        self.scene = scene
        self.scene.on_enter(self)
        self.scene.draw(self)

    def _tick(self) -> None:
        dt = self.timekeeper.tick()
        self.scene.update(self, dt)
        self.scene.draw(self)
        self.root.after(FRAME_MS, self._tick)

    def _on_key_press(self, event: tk.Event) -> None:
        self.input_state.set_key(str(event.keysym), True)
        self.scene.on_key_press(self, str(event.keysym))

    def _on_key_release(self, event: tk.Event) -> None:
        self.input_state.set_key(str(event.keysym), False)
