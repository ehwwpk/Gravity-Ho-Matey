from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from gravity_ho_matey.narrative.startup_splash import (
    MAX_PLAYBACK_SECONDS,
    MIN_PLAYBACK_SECONDS,
    has_startup_splash,
    resolve_playback_seconds,
    startup_asset_path,
)
from gravity_ho_matey.scenes.startup_splash import StartupSplashScene
from gravity_ho_matey.scenes.title import TitleScene


class _FakeHost:
    def __init__(self) -> None:
        self.last_scene = None
        self.renderer = MagicMock()

    def set_scene(self, scene: object) -> None:
        self.last_scene = scene


class StartupSplashRegistryTests(unittest.TestCase):
    def test_startup_asset_present(self) -> None:
        if not startup_asset_path().is_file():
            self.skipTest("startup.gif not in assets/narrative")
        self.assertTrue(has_startup_splash())
        self.assertEqual(startup_asset_path().name, "startup.gif")

    def test_playback_clamped(self) -> None:
        sequence = MagicMock()
        sequence.duration_seconds.return_value = 12.0
        self.assertAlmostEqual(resolve_playback_seconds(sequence), MAX_PLAYBACK_SECONDS)
        sequence.duration_seconds.return_value = 1.0
        self.assertAlmostEqual(resolve_playback_seconds(sequence), MIN_PLAYBACK_SECONDS)


class StartupSplashSceneTests(unittest.TestCase):
    def test_auto_advances_to_title(self) -> None:
        scene = StartupSplashScene()
        scene._ready = True
        scene._sequence = MagicMock()
        scene._sequence.frame_count = 3
        scene._sequence.delay_seconds.return_value = 0.05
        scene._sequence.frame.return_value = MagicMock()
        scene._playback_seconds = 2.5
        host = _FakeHost()
        scene.update(host, 2.6)
        self.assertIsInstance(host.last_scene, TitleScene)

    def test_skip_after_debounce(self) -> None:
        scene = StartupSplashScene()
        scene._ready = True
        scene._sequence = MagicMock()
        scene._playback_seconds = 4.0
        scene.elapsed = 0.5
        host = _FakeHost()
        scene.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, TitleScene)

    def test_skip_blocked_before_debounce(self) -> None:
        scene = StartupSplashScene()
        scene._ready = True
        scene._sequence = MagicMock()
        scene._playback_seconds = 4.0
        scene.elapsed = 0.1
        host = _FakeHost()
        scene.on_key_press(host, "Return")
        self.assertIsNone(host.last_scene)

    def test_holds_last_frame(self) -> None:
        scene = StartupSplashScene()
        scene._ready = True
        scene._sequence = MagicMock()
        scene._sequence.frame_count = 4
        scene._sequence.delay_seconds.return_value = 0.05
        scene._playback_seconds = 3.0
        host = _FakeHost()
        for _ in range(70):
            scene.update(host, 0.05)
        self.assertEqual(scene._frame_index, 3)
        scene.update(host, 1.6)
        self.assertIsInstance(host.last_scene, TitleScene)


class StartupSplashRenderTests(unittest.TestCase):
    def test_overlay_draws_with_asset(self) -> None:
        if not has_startup_splash():
            self.skipTest("startup.gif not in assets/narrative")
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence
        from gravity_ho_matey.render.startup_splash_overlay import StartupSplashOverlay

        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            sequence = AnimatedImageSequence.load(
                startup_asset_path(),
                max_width=960,
                max_height=640,
                master=root,
            )
            frame = sequence.frame(0)
            canvas._hold = frame
            StartupSplashOverlay().draw(
                canvas,
                frame_image=frame,
                elapsed=1.0,
                playback_seconds=3.0,
                progress=0.33,
                show_skip_hint=True,
            )
            self.assertGreater(len(canvas.find_all()), 2)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
