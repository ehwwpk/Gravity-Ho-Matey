from __future__ import annotations

from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.render.title_overlay import TITLE_PAGE_ORDER, TitlePage
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.game_flow import start_chart_briefing


class TitleScene(Scene):
    def __init__(self) -> None:
        self.page = TitlePage.WELCOME

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_title(page=self.page)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key in ("right", "bracketright"):
            self._step_page(1)
        elif key in ("left", "bracketleft"):
            self._step_page(-1)
        elif key in ("return", "1"):
            host.set_scene(start_chart_briefing("cove"))
        elif key == "2" and is_level_selectable("solar"):
            host.set_scene(start_chart_briefing("solar"))

    def _step_page(self, delta: int) -> None:
        idx = TITLE_PAGE_ORDER.index(self.page)
        idx = (idx + delta) % len(TITLE_PAGE_ORDER)
        self.page = TITLE_PAGE_ORDER[idx]
