from __future__ import annotations

import traceback
import tkinter as tk

from gravity_ho_matey.narrative.startup_splash import has_startup_splash
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.tk_renderer import TkRenderer
from gravity_ho_matey.scenes.base import Scene
from gravity_ho_matey.scenes.startup_splash import StartupSplashScene
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
        self.scene: Scene = StartupSplashScene() if has_startup_splash() else TitleScene()
        self.scene.on_enter(self)
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<Button-1>", self._on_pointer)
        self.root.bind("<ButtonRelease-1>", self._on_pointer_release)
        self.root.bind("<B1-Motion>", self._on_pointer_drag)
        self.root.bind("<Motion>", self._on_pointer_motion)
        self.root.bind("<MouseWheel>", self._on_wheel)
        self.root.bind("<Button-4>", self._on_wheel)
        self.root.bind("<Button-5>", self._on_wheel)
        self._pointer_x = CANVAS_WIDTH * 0.5
        self._pointer_y = CANVAS_HEIGHT * 0.5

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
        try:
            self.scene.update(self, dt)
            self.scene.draw(self)
        except Exception:
            traceback.print_exc()
            self._show_tick_error()
        self.root.after(FRAME_MS, self._tick)

    def _show_tick_error(self) -> None:
        """Keep the loop alive after a draw/update crash — otherwise Tk looks frozen."""
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill="#180608", outline="")
        self.canvas.create_text(
            CANVAS_WIDTH // 2,
            CANVAS_HEIGHT // 2 - 24,
            text="FRAME ERROR",
            fill=palette.HUD_WARN,
            font=("Courier New", 18, "bold"),
        )
        self.canvas.create_text(
            CANVAS_WIDTH // 2,
            CANVAS_HEIGHT // 2 + 20,
            text="See terminal for traceback · Esc to title",
            fill=palette.MUTED_TEXT,
            font=("Courier New", 11),
        )

    def _on_key_press(self, event: tk.Event) -> None:
        self.input_state.set_key(str(event.keysym), True)
        self.scene.on_key_press(self, str(event.keysym))

    def _on_key_release(self, event: tk.Event) -> None:
        self.input_state.set_key(str(event.keysym), False)

    def _on_pointer(self, event: tk.Event) -> None:
        self._pointer_x = float(event.x)
        self._pointer_y = float(event.y)
        self.scene.on_pointer(self, self._pointer_x, self._pointer_y, int(getattr(event, "num", 1)))

    def _on_pointer_motion(self, event: tk.Event) -> None:
        self._pointer_x = float(event.x)
        self._pointer_y = float(event.y)
        self.scene.on_pointer_motion(self, self._pointer_x, self._pointer_y)

    def _on_pointer_drag(self, event: tk.Event) -> None:
        self._pointer_x = float(event.x)
        self._pointer_y = float(event.y)
        self.scene.on_pointer_motion(self, self._pointer_x, self._pointer_y)

    def _on_pointer_release(self, event: tk.Event) -> None:
        self._pointer_x = float(event.x)
        self._pointer_y = float(event.y)
        self.scene.on_pointer_release(self, self._pointer_x, self._pointer_y, int(getattr(event, "num", 1)))

    def _on_wheel(self, event: tk.Event) -> None:
        delta = int(getattr(event, "delta", 0))
        if delta == 0:
            delta = 120 if int(getattr(event, "num", 0)) == 4 else -120
        self._pointer_x = float(event.x)
        self._pointer_y = float(event.y)
        self.scene.on_wheel(self, self._pointer_x, self._pointer_y, delta)
