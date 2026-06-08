from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.narrative.launch_countdown import launch_countdown_for
from gravity_ho_matey.scenes.game_flow import start_launch_countdown, start_level_intro
from gravity_ho_matey.scenes.launch_countdown import LaunchCountdownScene
from gravity_ho_matey.scenes.play import PlayScene


class _FakeHost:
    def __init__(self) -> None:
        self.last_scene = None
        self.renderer = MagicMock()

    def set_scene(self, scene: object) -> None:
        self.last_scene = scene


class LaunchCountdownFlowTests(unittest.TestCase):
    def test_start_launch_countdown_returns_scene(self) -> None:
        scene = start_launch_countdown("cove", CampaignState.new())
        self.assertIsInstance(scene, LaunchCountdownScene)
        self.assertEqual(scene.level_id, "cove")
        self.assertAlmostEqual(launch_countdown_for("cove").total_seconds, 1.5)

    def test_default_step_timing(self) -> None:
        spec = launch_countdown_for("cove")
        self.assertAlmostEqual(spec.step_seconds, 0.5)
        self.assertAlmostEqual(spec.total_seconds, 1.5)

    def test_brood_moon_with_intro_returns_intro_scene(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro
        from gravity_ho_matey.scenes.level_intro import LevelIntroScene

        scene = start_level_intro("brood_moon", CampaignState.new())
        if has_level_intro("brood_moon"):
            self.assertIsInstance(scene, LevelIntroScene)
        else:
            self.assertIsInstance(scene, LaunchCountdownScene)

    def test_drift_with_intro_returns_intro_scene(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro
        from gravity_ho_matey.scenes.level_intro import LevelIntroScene

        scene = start_level_intro("drift", CampaignState.new())
        if has_level_intro("drift"):
            self.assertIsInstance(scene, LevelIntroScene)
        else:
            self.assertIsInstance(scene, LaunchCountdownScene)

    def test_countdown_steps_through_digits(self) -> None:
        scene = LaunchCountdownScene(level_id="cove", campaign=CampaignState.new())
        scene.session = MagicMock()
        host = _FakeHost()
        spec = launch_countdown_for("cove")
        for expected in spec.digits:
            self.assertEqual(scene._spec.digits[scene.step_index], expected)
            scene.update(host, spec.step_seconds)
        self.assertIsInstance(host.last_scene, PlayScene)

    def test_countdown_skip_on_enter(self) -> None:
        scene = LaunchCountdownScene(level_id="cove", campaign=CampaignState.new())
        scene.session = MagicMock()
        host = _FakeHost()
        scene.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, PlayScene)

    def test_reveal_ramps_over_full_sequence(self) -> None:
        scene = LaunchCountdownScene(level_id="cove", campaign=CampaignState.new())
        scene.session = MagicMock()
        host = _FakeHost()
        spec = launch_countdown_for("cove")
        scene.draw(host)
        first = host.renderer.draw_launch_countdown.call_args.kwargs["reveal"]
        scene.total_elapsed = spec.total_seconds * 0.5
        scene.step_index = 1
        scene.draw(host)
        mid = host.renderer.draw_launch_countdown.call_args.kwargs["reveal"]
        self.assertGreater(mid, first)


class LaunchCountdownRenderTests(unittest.TestCase):
    def test_countdown_strip_draws_without_error(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.launch_countdown_overlay import draw_launch_countdown_strip

        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            draw_launch_countdown_strip(
                canvas,
                vw=960,
                vh=640,
                level_id="cove",
                theme="cove",
                digits=(3, 2, 1),
                step_index=1,
                current_digit=2,
                step_elapsed=0.2,
                step_seconds=0.5,
                reveal=0.55,
                total_elapsed=0.7,
                total_seconds=1.5,
            )
            self.assertGreater(len(canvas.find_all()), 8)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
