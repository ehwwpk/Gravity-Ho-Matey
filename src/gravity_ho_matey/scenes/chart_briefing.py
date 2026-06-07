from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.scenes.base import Scene, SceneHost


def _kind_from_shop_hit(hit: str) -> PowerUpKind | None:
    if not hit.startswith("shop_"):
        return None
    suffix = hit.removeprefix("shop_").upper()
    try:
        return PowerUpKind[suffix]
    except KeyError:
        return None


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
        self._anim = 0.0

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
        )

    def on_pointer_motion(self, host: SceneHost, x: float, y: float) -> None:
        self.hover_id = host.renderer.chart_hit_test(x, y)

    def on_pointer(self, host: SceneHost, x: float, y: float, button: int) -> None:
        if button != 1:
            return
        hit = host.renderer.chart_hit_test(x, y)
        if hit == "shop_close":
            self.shop_open = False
            return
        if hit == "shop_open":
            self.shop_open = True
            return
        if self.shop_open:
            if hit and hit.startswith("shop_"):
                kind = _kind_from_shop_hit(hit)
                if kind is not None:
                    self.campaign.try_purchase(kind)
            return
        if hit == "launch":
            self._launch(host)
        elif hit == "back_title":
            self._back(host)

    def on_key_press(self, host: SceneHost, keysym: str) -> None:
        key = keysym.lower()
        if key == "return":
            if self.shop_open:
                self.shop_open = False
                return
            self._launch(host)
        elif key == "escape":
            if self.shop_open:
                self.shop_open = False
                return
            self._back(host)
        elif key == "b":
            self.shop_open = not self.shop_open

    def _launch(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        host.set_scene(start_play(self.upcoming_level_id, self.campaign))

    def _back(self, host: SceneHost) -> None:
        from gravity_ho_matey.scenes.title import TitleScene

        host.set_scene(TitleScene())
