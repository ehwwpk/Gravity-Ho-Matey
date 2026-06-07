from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.render.shop_skill_tree_layout import SkillTreeViewport

ZOOM_DEFAULT = 1.48
ZOOM_MIN = 0.62
ZOOM_MAX = 3.35
WHEEL_ZOOM_FACTOR = 1.14
KEY_ZOOM_FACTOR = 1.18


@dataclass(slots=True)
class ShopTreeView:
    """Pan/zoom on top of the auto-fit skill tree viewport."""

    zoom: float = ZOOM_DEFAULT
    pan_x: float = 0.0
    pan_y: float = 0.0

    def reset(self) -> None:
        self.zoom = ZOOM_DEFAULT
        self.pan_x = 0.0
        self.pan_y = 0.0

    def fit_all(self) -> None:
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def _clamp_zoom(self) -> None:
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom))

    def pan_by(self, dx: float, dy: float) -> None:
        self.pan_x += dx
        self.pan_y += dy

    def zoom_by(self, factor: float, *, mx: float, my: float, fit: SkillTreeViewport) -> None:
        """Zoom toward a screen point — keeps the tree coordinate under the cursor stable."""
        old_scale = fit.scale * self.zoom
        if old_scale <= 1e-6:
            self.zoom *= factor
            self._clamp_zoom()
            return
        tx = (mx - fit.screen_cx - self.pan_x) / old_scale
        ty = (my - fit.screen_cy - self.pan_y) / old_scale
        self.zoom *= factor
        self._clamp_zoom()
        new_scale = fit.scale * self.zoom
        self.pan_x = mx - fit.screen_cx - tx * new_scale
        self.pan_y = my - fit.screen_cy - ty * new_scale


def apply_shop_tree_view(fit: SkillTreeViewport, view: ShopTreeView) -> SkillTreeViewport:
    return SkillTreeViewport(
        fit.screen_cx + view.pan_x,
        fit.screen_cy + view.pan_y,
        fit.scale * view.zoom,
    )
