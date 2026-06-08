from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.narrative.level_intros import (
    has_level_intro,
    intro_spec_for,
    resolve_intro_asset,
)
from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene
from gravity_ho_matey.scenes.game_flow import start_level_intro
from gravity_ho_matey.scenes.launch_countdown import LaunchCountdownScene
from gravity_ho_matey.scenes.level_intro import LevelIntroScene
from gravity_ho_matey.scenes.play import PlayScene


class _FakeHost:
    def __init__(self) -> None:
        self.last_scene = None
        self.renderer = MagicMock()
        self.renderer.level_intro_hit_test = MagicMock(return_value=None)

    def set_scene(self, scene: object) -> None:
        self.last_scene = scene


class LevelIntroRegistryTests(unittest.TestCase):
    def test_cove_has_intro_asset(self) -> None:
        spec = intro_spec_for("cove")
        self.assertIsNotNone(spec)
        assert spec is not None
        path = resolve_intro_asset(spec)
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.is_file())
        self.assertEqual(path.suffix.lower(), ".gif")

    def test_brood_moon_intro_registered(self) -> None:
        spec = intro_spec_for("brood_moon")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.asset_stem, "brood_moon")
        self.assertEqual(spec.header_tag, "BROOD MOON · CAPTAIN'S LOG")
        path = resolve_intro_asset(spec)
        if path is None:
            self.skipTest("brood_moon.gif not dropped yet")
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "brood_moon.gif")
        self.assertTrue(has_level_intro("brood_moon"))

    def test_rift_intro_registered(self) -> None:
        spec = intro_spec_for("rift")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.asset_stem, "rift")
        self.assertEqual(spec.header_tag, "RELAY HOLD · CAPTAIN'S LOG")
        path = resolve_intro_asset(spec)
        if path is None:
            self.skipTest("rift.gif not dropped yet")
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "rift.gif")
        self.assertTrue(has_level_intro("rift"))

    def test_siege_intro_registered(self) -> None:
        spec = intro_spec_for("siege")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.asset_stem, "siege")
        self.assertEqual(spec.header_tag, "SIEGE LINE · CAPTAIN'S LOG")
        path = resolve_intro_asset(spec)
        if path is None:
            self.skipTest("siege.gif not dropped yet")
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "siege.gif")
        self.assertTrue(has_level_intro("siege"))

    def test_drift_intro_registered(self) -> None:
        spec = intro_spec_for("drift")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.asset_stem, "drift")
        path = resolve_intro_asset(spec)
        if path is None:
            self.skipTest("drift.gif not dropped yet")
        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "drift.gif")
        self.assertTrue(has_level_intro("drift"))

    def test_solar_has_intro_asset(self) -> None:
        spec = intro_spec_for("solar")
        self.assertIsNotNone(spec)
        assert spec is not None
        path = resolve_intro_asset(spec)
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.name == "solar.gif")
        self.assertTrue(has_level_intro("solar"))

    def test_cove_asset_prefers_gif_when_present(self) -> None:
        spec = intro_spec_for("cove")
        assert spec is not None
        root = Path(__file__).resolve().parents[1] / "src" / "gravity_ho_matey" / "assets" / "narrative"
        gif_path = root / "cove.gif"
        if gif_path.is_file():
            self.assertEqual(resolve_intro_asset(spec), gif_path)

    def test_cove_gif_is_multi_frame(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence

        spec = intro_spec_for("cove")
        asset = resolve_intro_asset(spec) if spec else None
        if asset is None:
            self.skipTest("cove intro asset unavailable")
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        try:
            sequence = AnimatedImageSequence.load(
                asset,
                max_width=900,
                max_height=460,
                master=root,
            )
            self.assertGreater(sequence.frame_count, 1)
            self.assertGreaterEqual(sequence.duration_seconds(), 4.0)
            self.assertLessEqual(sequence.duration_seconds(), 12.0)
        finally:
            root.destroy()


class LevelIntroAnimationTests(unittest.TestCase):
    def test_resolve_playback_uses_gif_duration_by_default(self) -> None:
        from gravity_ho_matey.narrative.level_intros import resolve_playback_seconds

        spec = intro_spec_for("cove")
        assert spec is not None
        sequence = MagicMock()
        sequence.duration_seconds.return_value = 6.16
        self.assertAlmostEqual(resolve_playback_seconds(spec, sequence), 6.16)

    def test_resolve_playback_honors_per_level_override(self) -> None:
        from gravity_ho_matey.narrative.level_intros import LevelIntroSpec, resolve_playback_seconds

        spec = LevelIntroSpec(asset_stem="solar", playback_seconds=8.5)
        sequence = MagicMock()
        sequence.duration_seconds.return_value = 6.0
        self.assertAlmostEqual(resolve_playback_seconds(spec, sequence), 8.5)

    def test_intro_scene_advances_frames(self) -> None:
        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        scene._spec = intro_spec_for("cove")
        mock_seq = MagicMock()
        mock_seq.frame_count = 12
        mock_seq.delay_seconds.return_value = 0.07
        mock_seq.duration_seconds.return_value = 0.84
        scene._sequence = mock_seq
        scene._playback_seconds = 0.84
        host = _FakeHost()
        for _ in range(8):
            scene.update(host, 0.08)
        self.assertGreater(scene._frame_index, 0)

    def test_intro_holds_last_frame_after_one_playthrough(self) -> None:
        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        scene._spec = intro_spec_for("cove")
        mock_seq = MagicMock()
        mock_seq.frame_count = 4
        mock_seq.delay_seconds.return_value = 0.05
        scene._sequence = mock_seq
        scene._playback_seconds = 2.0
        host = _FakeHost()
        for _ in range(20):
            scene.update(host, 0.05)
        self.assertEqual(scene._frame_index, 3)

    def test_intro_auto_launches_when_playback_elapsed(self) -> None:
        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        scene._spec = intro_spec_for("cove")
        scene._sequence = MagicMock()
        scene._sequence.frame_count = 1
        scene._sequence.delay_seconds.return_value = 0.1
        scene._sequence.frame.return_value = MagicMock()
        scene._playback_seconds = 2.0
        host = _FakeHost()
        scene.update(host, 2.01)
        self.assertIsInstance(host.last_scene, LaunchCountdownScene)

    def test_intro_progress_tracks_playback_seconds(self) -> None:
        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        scene._spec = intro_spec_for("cove")
        scene._sequence = MagicMock()
        scene._sequence.frame.return_value = MagicMock()
        scene._playback_seconds = 10.0
        scene.elapsed = 5.0
        host = _FakeHost()
        scene.draw(host)
        host.renderer.draw_level_intro.assert_called_once()
        kwargs = host.renderer.draw_level_intro.call_args.kwargs
        self.assertAlmostEqual(kwargs["progress"], 0.5)
        self.assertAlmostEqual(kwargs["playback_seconds"], 10.0)

class LevelIntroFlowTests(unittest.TestCase):
    def test_start_level_intro_cove_returns_scene(self) -> None:
        scene = start_level_intro("cove", CampaignState.new())
        self.assertIsInstance(scene, LevelIntroScene)
        assert isinstance(scene, LevelIntroScene)
        self.assertEqual(scene.level_id, "cove")

    def test_start_level_intro_solar_returns_intro_scene(self) -> None:
        scene = start_level_intro("solar", CampaignState.new())
        self.assertIsInstance(scene, LevelIntroScene)
        self.assertEqual(scene.level_id, "solar")

    def test_chart_briefing_cove_launch_routes_to_intro(self) -> None:
        briefing = ChartBriefingScene(
            upcoming_level_id="cove",
            campaign=CampaignState.new(),
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, LevelIntroScene)

    def test_chart_briefing_solar_launch_routes_to_intro(self) -> None:
        briefing = ChartBriefingScene(
            upcoming_level_id="solar",
            campaign=CampaignState.new(),
            cleared_level_id="cove",
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, LevelIntroScene)
        assert isinstance(host.last_scene, LevelIntroScene)
        self.assertEqual(host.last_scene.level_id, "solar")

    def test_start_level_intro_drift_returns_intro_when_asset_present(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro

        scene = start_level_intro("drift", CampaignState.new())
        if has_level_intro("drift"):
            self.assertIsInstance(scene, LevelIntroScene)
            assert isinstance(scene, LevelIntroScene)
            self.assertEqual(scene.level_id, "drift")
        else:
            self.assertIsInstance(scene, LaunchCountdownScene)

    def test_start_level_intro_rift_returns_intro_when_asset_present(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro

        scene = start_level_intro("rift", CampaignState.new())
        if has_level_intro("rift"):
            self.assertIsInstance(scene, LevelIntroScene)
            assert isinstance(scene, LevelIntroScene)
            self.assertEqual(scene.level_id, "rift")
        else:
            self.assertIsInstance(scene, LaunchCountdownScene)

    def test_start_level_intro_siege_returns_intro_when_asset_present(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro

        scene = start_level_intro("siege", CampaignState.new())
        if has_level_intro("siege"):
            self.assertIsInstance(scene, LevelIntroScene)
            assert isinstance(scene, LevelIntroScene)
            self.assertEqual(scene.level_id, "siege")
        else:
            self.assertIsInstance(scene, LaunchCountdownScene)

    def test_chart_briefing_rift_launch_routes_to_intro_when_asset_present(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro

        briefing = ChartBriefingScene(
            upcoming_level_id="rift",
            campaign=CampaignState.new(),
            cleared_level_id="drift",
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        if has_level_intro("rift"):
            self.assertIsInstance(host.last_scene, LevelIntroScene)
            assert isinstance(host.last_scene, LevelIntroScene)
            self.assertEqual(host.last_scene.level_id, "rift")
        else:
            self.assertIsInstance(host.last_scene, LaunchCountdownScene)

    def test_chart_briefing_siege_launch_routes_to_intro_when_asset_present(self) -> None:
        from gravity_ho_matey.narrative.level_intros import has_level_intro

        briefing = ChartBriefingScene(
            upcoming_level_id="siege",
            campaign=CampaignState.new(),
            cleared_level_id="rift",
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        if has_level_intro("siege"):
            self.assertIsInstance(host.last_scene, LevelIntroScene)
            assert isinstance(host.last_scene, LevelIntroScene)
            self.assertEqual(host.last_scene.level_id, "siege")
        else:
            self.assertIsInstance(host.last_scene, LaunchCountdownScene)

    def test_intro_skip_launches_countdown(self) -> None:
        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        scene._spec = intro_spec_for("cove")
        scene._sequence = MagicMock()
        host = _FakeHost()
        scene.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, LaunchCountdownScene)

    def test_intro_missing_asset_falls_back_to_play(self) -> None:
        from unittest.mock import patch

        scene = LevelIntroScene(level_id="cove", campaign=CampaignState.new())
        host = _FakeHost()
        with patch("gravity_ho_matey.scenes.level_intro.resolve_intro_asset", return_value=None):
            scene.on_enter(host)
        self.assertIsInstance(host.last_scene, LaunchCountdownScene)


class LevelIntroRenderTests(unittest.TestCase):
    def test_overlay_draw_registers_skip_hit(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence
        from gravity_ho_matey.render.level_intro_overlay import LevelIntroOverlay

        spec = intro_spec_for("cove")
        asset = resolve_intro_asset(spec) if spec else None
        if spec is None or asset is None:
            self.skipTest("cove intro asset unavailable")
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            sequence = AnimatedImageSequence.load(
                asset,
                max_width=900,
                max_height=460,
                master=root,
            )
            overlay = LevelIntroOverlay()
            frame = sequence.frame(0)
            canvas._hold = frame  # prevent GC for test draw
            overlay.draw(
                canvas,
                level_id="cove",
                spec=spec,
                frame_image=frame,
                elapsed=3.08,
                playback_seconds=6.16,
                progress=0.5,
            )
            self.assertIsNotNone(overlay.hits.hit(900, 610))
        finally:
            root.destroy()

    def test_intro_status_line_is_rift_only(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.animated_image import AnimatedImageSequence
        from gravity_ho_matey.render.level_intro_overlay import LevelIntroOverlay

        def _header_text(level_id: str) -> str:
            spec = intro_spec_for(level_id)
            asset = resolve_intro_asset(spec) if spec else None
            if spec is None or asset is None:
                self.skipTest(f"{level_id} intro asset unavailable")
            root = tk.Tk()
            root.withdraw()
            try:
                canvas = tk.Canvas(root, width=960, height=640)
                sequence = AnimatedImageSequence.load(asset, max_width=900, max_height=460, master=root)
                frame = sequence.frame(0)
                canvas._hold = frame
                LevelIntroOverlay().draw(
                    canvas,
                    level_id=level_id,
                    spec=spec,
                    frame_image=frame,
                    elapsed=1.0,
                    playback_seconds=6.0,
                    progress=0.2,
                )
                parts = [
                    canvas.itemcget(item, "text")
                    for item in canvas.find_all()
                    if canvas.type(item) == "text"
                ]
                return " ".join(parts)
            finally:
                root.destroy()

        cove_txt = _header_text("cove")
        self.assertIn("LINK", cove_txt)
        self.assertNotIn("RELAY", cove_txt)
        rift_txt = _header_text("rift")
        self.assertIn("RELAY", rift_txt)


if __name__ == "__main__":
    unittest.main()
