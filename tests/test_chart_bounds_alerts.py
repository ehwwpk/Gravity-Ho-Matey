import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_BOUNDS_TOAST_SECONDS,
    ChartBoundsToast,
    chart_bounds_toast_copy,
)
from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def to_control_intent(self) -> ControlIntent:
        return ControlIntent()


class _FakeHost:
    input_state = _FakeInput()

    def set_scene(self, _scene: object) -> None:
        pass


class ChartBoundsAlertTests(unittest.TestCase):
    def test_toast_copy_for_leave_and_return(self) -> None:
        leave_headline, _ = chart_bounds_toast_copy(
            ChartBoundsToast.LEFT_CHART,
            level_theme="cove",
            exposure=0.0,
        )
        enter_headline, enter_sub = chart_bounds_toast_copy(
            ChartBoundsToast.ENTERED_CHART,
            level_theme="cove",
            exposure=2.0,
        )
        self.assertIn("Off chart", leave_headline)
        self.assertIn("Back on chart", enter_headline)
        self.assertIn("2.0s", enter_sub)

    def test_play_scene_fires_leave_toast_when_crossing_out(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(-60, 100)
        scene.update(_FakeHost(), 0.05)
        self.assertEqual(scene.bounds_toast_kind, ChartBoundsToast.LEFT_CHART)
        self.assertAlmostEqual(scene.bounds_toast_ttl, CHART_BOUNDS_TOAST_SECONDS, places=2)
        self.assertGreater(scene.camera.bounds_alert_flash_ttl, 0.0)

    def test_play_scene_fires_enter_toast_when_returning(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(-60, 100)
        scene.update(_FakeHost(), 0.05)
        scene.bounds_toast_ttl = 0.0
        scene.bounds_toast_kind = None
        scene.world.ship.pos = Vec2(100, 100)
        scene.update(_FakeHost(), 0.05)
        self.assertEqual(scene.bounds_toast_kind, ChartBoundsToast.ENTERED_CHART)

    def test_toast_expires(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(-60, 100)
        scene.update(_FakeHost(), 0.05)
        scene.update(_FakeHost(), CHART_BOUNDS_TOAST_SECONDS + 0.1)
        self.assertIsNone(scene.bounds_toast_kind)
        self.assertEqual(scene.bounds_toast_ttl, 0.0)

    def test_respawn_does_not_fire_enter_toast(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(-60, 100)
        scene.update(_FakeHost(), 0.05)
        scene.bounds_toast_ttl = 0.0
        scene.bounds_toast_kind = None
        scene.world.ship.pos = scene.world.spawn_pos
        scene._sync_chart_bounds_state(suppress_toast=True)
        self.assertIsNone(scene.bounds_toast_kind)
        self.assertTrue(scene._ship_was_in_chart)

    def test_closed_bounds_never_toasts(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        cfg = scene.world.config
        scene.world.config = WorldConfig(
            width=cfg.width,
            height=cfg.height,
            viewport_width=cfg.viewport_width,
            viewport_height=cfg.viewport_height,
            open_bounds=False,
            level_name=cfg.level_name,
            level_theme=cfg.level_theme,
        )
        scene._ship_was_in_chart = None
        scene.world.ship.pos = Vec2(-60, 100)
        scene._sync_chart_bounds_state(suppress_toast=False)
        self.assertIsNone(scene.bounds_toast_kind)


if __name__ == "__main__":
    unittest.main()
