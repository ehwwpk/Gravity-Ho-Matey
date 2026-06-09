from __future__ import annotations



from gravity_ho_matey.gameplay.campaign import CampaignState

from gravity_ho_matey.gameplay.progress import is_level_selectable

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER

from gravity_ho_matey.render.shop_skill_tree_layout import shop_open_anim_at

from gravity_ho_matey.render.title_overlay import TITLE_PAGE_ORDER, TitlePage
from gravity_ho_matey.render.title_codex import TitleCodexState

from gravity_ho_matey.scenes.base import Scene, SceneHost
from gravity_ho_matey.scenes.game_flow import start_chart_briefing
from gravity_ho_matey.scenes.title_deploy_ui import (
    DeployListUiState,
    deploy_list_pointer_down,
    deploy_list_pointer_motion,
    deploy_list_pointer_up,
    deploy_list_reset,
    deploy_list_track_click,
    deploy_list_wheel,
)
from gravity_ho_matey.scenes.shop_ui import (
    ShopUiState,
    shop_fit_viewport_for,
    shop_handle_pointer_click,
    shop_on_key,
    shop_on_open,
    shop_on_pointer_down,
    shop_on_pointer_motion,
    shop_on_pointer_up,
    shop_on_wheel,
)





class TitleScene(Scene):

    def __init__(self, campaign: CampaignState | None = None) -> None:

        self.campaign = campaign or CampaignState.new()

        self.page = TitlePage.WELCOME

        self.deploy_focus = 0

        self.deploy_scroll = 0.0

        self.hover_id: str | None = None

        self.elapsed = 0.0

        self.shop_open = False

        self._shop_opened_at: float | None = None

        self._shop_ui = ShopUiState()

        self._deploy_ui = DeployListUiState()

        self.codex = TitleCodexState()

        self._pointer = (480.0, 320.0)



    def update(self, host: SceneHost, dt: float) -> None:

        _ = host

        self.elapsed += dt

        if self.page is TitlePage.WELCOME and not self.shop_open:
            self.codex.tick(dt, self.elapsed)



    def draw(self, host: SceneHost) -> None:

        host.renderer.draw_title(

            page=self.page,

            campaign=self.campaign,

            deploy_focus=self.deploy_focus,

            deploy_scroll=self.deploy_scroll,

            hover_id=self.hover_id,

            elapsed=self.elapsed,

            shop_open=self.shop_open,

            shop_open_anim=shop_open_anim_at(self._shop_opened_at, self.elapsed),

            shop_ui=self._shop_ui,

            codex=self.codex,

        )



    def _set_shop_open(self, open_: bool) -> None:

        opening = open_ and not self.shop_open

        if open_ and not self.shop_open:

            self._shop_opened_at = self.elapsed

        if not open_:

            self._shop_opened_at = None

        shop_on_open(self._shop_ui, opening=opening)

        self.shop_open = open_



    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:

        self._pointer = (x, y)

        if self.page is TitlePage.DEPLOY and not self.shop_open:
            layout = self._deploy_layout()
            updated = deploy_list_pointer_motion(
                self._deploy_ui,
                x,
                y,
                layout=layout,
                scroll=self.deploy_scroll,
            )
            if updated is not None:
                self.deploy_scroll = updated

        self.hover_id = host.renderer.title_hit_test(x, y)

        shop_on_pointer_motion(self._shop_ui, x, y, shop_open=self.shop_open)



    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:

        if button != 1:

            return

        self._pointer = (x, y)

        hit = host.renderer.title_hit_test(x, y)

        if hit == "shop_close":

            self._set_shop_open(False)

            return

        if hit == "shop_open":

            self._set_shop_open(True)

            return

        if self.shop_open:

            fit = shop_fit_viewport_for(self._shop_ui, self.campaign)

            if shop_handle_pointer_click(
                hit,
                self._shop_ui,
                shop_open=True,
                fit_viewport=fit,
                pointer=self._pointer,
                on_purchase=self.campaign.try_purchase,
            ):
                return

            shop_on_pointer_down(self._shop_ui, x, y, hit, shop_open=True)

            return

        if hit == "goto_deploy":

            self.page = TitlePage.DEPLOY

            deploy_list_reset(self._deploy_ui)
            self._sync_deploy_scroll()

            return

        if self.page is TitlePage.WELCOME:
            if hit == "codex_prev":
                self.codex.step(-1, self.elapsed)
                return
            if hit == "codex_next":
                self.codex.step(1, self.elapsed)
                return
            if hit == "codex_body":
                self.codex.step(1, self.elapsed)
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

                    if page is TitlePage.DEPLOY:
                        deploy_list_reset(self._deploy_ui)
                        self._sync_deploy_scroll()

                    return

        if self.page is TitlePage.DEPLOY and not self.shop_open:
            from gravity_ho_matey.render.title_deploy_list import panel_list_contains

            layout = self._deploy_layout()
            if (
                (hit and hit.startswith("level:"))
                or hit in ("deploy_scroll_track", "deploy_scroll_thumb")
                or panel_list_contains(layout, x, y)
            ):
                if hit == "deploy_scroll_track":
                    jumped = deploy_list_track_click(layout, x, y, self.deploy_scroll)
                    if jumped is not None:
                        self.deploy_scroll = jumped
                deploy_list_pointer_down(
                    self._deploy_ui,
                    x,
                    y,
                    hit,
                    layout=layout,
                    scroll=self.deploy_scroll,
                )
                return

        if hit and hit.startswith("level:"):

            level_id = hit.split(":", 1)[1]

            if is_level_selectable(level_id):

                host.set_scene(start_chart_briefing(level_id, campaign=self.campaign))



    def on_pointer_release(self, host: SceneHost, x: float, y: float, button: int) -> None:

        if button != 1:
            shop_on_pointer_up(self._shop_ui)
            return

        if self.page is TitlePage.DEPLOY and not self.shop_open:
            pending, dragged = deploy_list_pointer_up(self._deploy_ui)
            if not dragged and pending and pending.startswith("level:"):
                level_id = pending.split(":", 1)[1]
                if level_id in LEVEL_ORDER:
                    self.deploy_focus = LEVEL_ORDER.index(level_id)
                    self._sync_deploy_scroll()
                if is_level_selectable(level_id):
                    host.set_scene(start_chart_briefing(level_id, campaign=self.campaign))
                    return

        shop_on_pointer_up(self._shop_ui)



    def on_wheel(self, host: SceneHost, x: float, y: float, delta: int) -> None:

        from gravity_ho_matey.render.title_overlay import TitleScreenOverlay

        self._pointer = (x, y)

        if self.page is TitlePage.WELCOME and not self.shop_open and delta != 0:
            from gravity_ho_matey.render.title_home_layout import (
                codex_viewport_contains,
                compute_codex_layout,
                compute_welcome_home_layout,
            )

            chrome = TitleScreenOverlay.chrome_layout()
            welcome = compute_welcome_home_layout(chrome, screen_w=float(TitleScreenOverlay.WIDTH))
            codex_layout = compute_codex_layout(welcome, self.codex.entry())
            if codex_viewport_contains(codex_layout, x, y):
                self.codex.step(1 if delta > 0 else -1, self.elapsed)
                return

        if self.page is TitlePage.DEPLOY and not self.shop_open and delta != 0:
            split = self._deploy_split()
            updated = deploy_list_wheel(self.deploy_scroll, split.list, x, y, delta, split=split)
            if updated is not None:
                self.deploy_scroll = updated
                return

        fit = shop_fit_viewport_for(self._shop_ui, self.campaign)

        shop_on_wheel(self._shop_ui, x, y, delta, shop_open=self.shop_open, fit_viewport=fit)



    def on_key_press(self, host: SceneHost, keysym: str) -> None:

        key = keysym.lower()

        if key == "b":

            self._set_shop_open(not self.shop_open)

            return

        if self.shop_open:

            fit = shop_fit_viewport_for(self._shop_ui, self.campaign)

            if shop_on_key(self._shop_ui, key, shop_open=True, fit_viewport=fit, pointer=self._pointer):

                return

            if key in ("return", "escape"):

                self._set_shop_open(False)

            return

        if key in ("right", "bracketright", "tab"):

            self._step_page(1)

        elif key in ("left", "bracketleft"):

            self._step_page(-1)

        elif key in ("up", "w") and self.page is TitlePage.WELCOME:

            self.codex.step(-1, self.elapsed)

        elif key in ("down", "s") and self.page is TitlePage.WELCOME:

            self.codex.step(1, self.elapsed)

        elif key in ("up", "w") and self.page is TitlePage.DEPLOY:

            self.deploy_focus = (self.deploy_focus - 1) % len(LEVEL_ORDER)

            self._sync_deploy_scroll()

        elif key in ("down", "s") and self.page is TitlePage.DEPLOY:

            self.deploy_focus = (self.deploy_focus + 1) % len(LEVEL_ORDER)

            self._sync_deploy_scroll()

        elif key in ("prior", "page_up") and self.page is TitlePage.DEPLOY:

            self._scroll_deploy_page(-1)

        elif key in ("next", "page_down") and self.page is TitlePage.DEPLOY:

            self._scroll_deploy_page(1)

        elif key == "return":

            if self.page is TitlePage.DEPLOY:

                self._launch_focused(host)

            elif self.page is TitlePage.WELCOME:

                self.page = TitlePage.DEPLOY

                self._sync_deploy_scroll()

            else:

                self.page = TitlePage.DEPLOY

                self._sync_deploy_scroll()

        elif key == "1":

            self._launch_level(host, "cove")

        elif key == "2":

            self._launch_level(host, "solar")

        elif key == "3":

            self._launch_level(host, "drift")

        elif key == "4":

            self._launch_level(host, "rift")

        elif key == "5":

            self._launch_level(host, "siege")

        elif key == "6":

            self._launch_level(host, "brood_moon")



    def _deploy_split(self):
        from gravity_ho_matey.render.title_deploy_list import compute_deploy_split_layout
        from gravity_ho_matey.render.title_overlay import TitleScreenOverlay

        chrome = TitleScreenOverlay.chrome_layout()
        return compute_deploy_split_layout(chrome, screen_w=float(TitleScreenOverlay.WIDTH))

    def _deploy_layout(self):
        return self._deploy_split().list

    def _sync_deploy_scroll(self) -> None:
        from gravity_ho_matey.render.title_deploy_list import scroll_to_show_index

        layout = self._deploy_layout()
        self.deploy_scroll = scroll_to_show_index(self.deploy_scroll, layout, self.deploy_focus)

    def _scroll_deploy_page(self, direction: int) -> None:
        from gravity_ho_matey.render.title_deploy_list import clamp_scroll

        layout = self._deploy_layout()
        step = max(48.0, layout.viewport_h * 0.85)
        self.deploy_scroll = clamp_scroll(self.deploy_scroll + direction * step, layout)



    def _launch_focused(self, host: SceneHost) -> None:

        level_id = LEVEL_ORDER[self.deploy_focus]

        self._launch_level(host, level_id)



    def _launch_level(self, host: SceneHost, level_id: str) -> None:

        if is_level_selectable(level_id):

            host.set_scene(start_chart_briefing(level_id, campaign=self.campaign))



    def _step_page(self, delta: int) -> None:

        idx = TITLE_PAGE_ORDER.index(self.page)

        idx = (idx + delta) % len(TITLE_PAGE_ORDER)

        self.page = TITLE_PAGE_ORDER[idx]

        if self.page is TitlePage.DEPLOY:
            self._sync_deploy_scroll()


