from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.shop_skill_tree_layout import shop_open_anim_at
from gravity_ho_matey.scenes.base import Scene, SceneHost
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


@dataclass(slots=True)
class ChartBriefingScene(Scene):
    """Diegetic holo-map before launch — inaugural chart or post-clear transition."""

    upcoming_level_id: str
    campaign: CampaignState
    cleared_level_id: str | None = None
    elapsed: float = 0.0

    def __post_init__(self) -> None:
        self._preview = build_level(self.upcoming_level_id)
        self._field = GravityField.bake(
            self._preview.wells,
            world_width=self._preview.config.width,
            world_height=self._preview.config.height,
            cols=24,
            rows=max(24, int(24 * self._preview.config.height / max(1, self._preview.config.width))),
            gravity_scale=self._preview.config.gravity_scale,
        )
        self.hover_id: str | None = None
        self.shop_open: bool = False
        self._shop_opened_at: float | None = None
        self._anim = 0.0
        self._shop_ui = ShopUiState()
        self._pointer = (480.0, 320.0)

    def update(self, host: SceneHost, dt: float) -> None:
        _ = host
        self._anim += dt

    def draw(self, host: SceneHost) -> None:
        host.renderer.draw_chart_briefing(
            self._preview,
            self._field,
            campaign=self.campaign,
            upcoming_level_id=self.upcoming_level_id,
            cleared_level_id=self.cleared_level_id,
            elapsed=self.elapsed,
            hover_id=self.hover_id,
            anim=self._anim,
            shop_open=self.shop_open,
            shop_open_anim=shop_open_anim_at(self._shop_opened_at, self._anim),
            shop_view=self._shop_ui.view,
        )

    def _set_shop_open(self, open_: bool) -> None:
        opening = open_ and not self.shop_open
        if open_ and not self.shop_open:
            self._shop_opened_at = self._anim
        if not open_:
            self._shop_opened_at = None
        shop_on_open(self._shop_ui, opening=opening)
        self.shop_open = open_

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        self._pointer = (x, y)
        self.hover_id = host.renderer.chart_hit_test(x, y)
        shop_on_pointer_motion(self._shop_ui, x, y, shop_open=self.shop_open)

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        if button != 1:
            return
        self._pointer = (x, y)
        hit = host.renderer.chart_hit_test(x, y)
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
        if hit == "launch":
            self._launch(host)
        elif hit == "back_title":
            self._back(host)

    def on_pointer_release(self, host: SceneHost, x: float, y: float, button: int) -> None:
        _ = host, x, y, button
        shop_on_pointer_up(self._shop_ui)

    def on_wheel(self, host: SceneHost, x: float, y: float, delta: int) -> None:
        _ = host
        self._pointer = (x, y)
        fit = shop_fit_viewport_for(self._shop_ui, self.campaign)
        shop_on_wheel(self._shop_ui, x, y, delta, shop_open=self.shop_open, fit_viewport=fit)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if self.shop_open:
            fit = shop_fit_viewport_for(self._shop_ui, self.campaign)
            if shop_on_key(self._shop_ui, key, shop_open=True, fit_viewport=fit, pointer=self._pointer):
                return
        if key == "return":
            if self.shop_open:
                self._set_shop_open(False)
                return
            self._launch(host)
        elif key == "escape":
            if self.shop_open:
                self._set_shop_open(False)
                return
            self._back(host)
        elif key == "b":
            self._set_shop_open(not self.shop_open)

    def _launch(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.game_flow import start_level_intro

        host.set_scene(start_level_intro(self.upcoming_level_id, self.campaign))

    def _back(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.title import TitleScene

        host.set_scene(TitleScene(campaign=self.campaign))
