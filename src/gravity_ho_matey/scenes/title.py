from __future__ import annotations

from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.levels.level_registry import LEVEL_ORDER
from gravity_ho_matey.render.title_overlay import TITLE_PAGE_ORDER, TitlePage
from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.game_flow import start_chart_briefing


class TitleScene(Scene):
    def __init__(self) -> None:
        self.page = TitlePage.WELCOME
        self.deploy_focus = 0
        self.hover_id: str | None = None
        self.elapsed = 0.0

    def update(self, host: SceneHost, dt: float) -> None:
        _ = host
        self.elapsed += dt

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_title(
            page=self.page,
            deploy_focus=self.deploy_focus,
            hover_id=self.hover_id,
            elapsed=self.elapsed,
        )

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        self.hover_id = host.renderer.title_hit_test(x, y)

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        if button != 1:
            return
        hit = host.renderer.title_hit_test(x, y)
        if hit == "goto_deploy":
            self.page = TitlePage.DEPLOY
            return
        if hit == "page_prev":
            self._step_page(-1)
            return
        if hit == "page_next":
            self._step_page(1)
            return
        if hit and hit.startswith("tab:"):
            tab_name = hit.split(":", 1)[1]
            for page in TITLE_PAGE_ORDER:
                if page.name.lower() == tab_name:
                    self.page = page
                    return
        if hit and hit.startswith("level:"):
            level_id = hit.split(":", 1)[1]
            if is_level_selectable(level_id):
                host.set_scene(start_chart_briefing(level_id))

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key in ("right", "bracketright", "tab"):
            self._step_page(1)
        elif key in ("left", "bracketleft"):
            self._step_page(-1)
        elif key in ("up", "w") and self.page is TitlePage.DEPLOY:
            self.deploy_focus = (self.deploy_focus - 1) % len(LEVEL_ORDER)
        elif key in ("down", "s") and self.page is TitlePage.DEPLOY:
            self.deploy_focus = (self.deploy_focus + 1) % len(LEVEL_ORDER)
        elif key == "return":
            if self.page is TitlePage.DEPLOY:
                self._launch_focused(host)
            elif self.page is TitlePage.WELCOME:
                self.page = TitlePage.DEPLOY
            else:
                self.page = TitlePage.DEPLOY
        elif key == "1":
            self._launch_level(host, "cove")
        elif key == "2":
            self._launch_level(host, "solar")
        elif key == "3":
            self._launch_level(host, "drift")

    def _launch_focused(self, host: SceneHost) -> None:
        level_id = LEVEL_ORDER[self.deploy_focus]
        self._launch_level(host, level_id)

    @staticmethod
    def _launch_level(host: SceneHost, level_id: str) -> None:
        if is_level_selectable(level_id):
            host.set_scene(start_chart_briefing(level_id))

    def _step_page(self, delta: int) -> None:
        idx = TITLE_PAGE_ORDER.index(self.page)
        idx = (idx + delta) % len(TITLE_PAGE_ORDER)
        self.page = TITLE_PAGE_ORDER[idx]
