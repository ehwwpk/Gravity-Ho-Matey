from __future__ import annotations

import unittest
import tkinter as tk

from gravity_ho_matey.render.title_codex import CODEX_ENTRIES, TitleCodexState
from gravity_ho_matey.render.title_codex_viz import draw_codex_preview, turntable_scale_x
from gravity_ho_matey.render.title_home_layout import (
    codex_viewport_contains,
    compute_codex_layout,
    compute_welcome_home_layout,
)
from gravity_ho_matey.render.title_overlay import TitlePage, TitleScreenOverlay
from gravity_ho_matey.scenes.title import TitleScene


def _canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class TitleCodexStateTests(unittest.TestCase):
    def test_step_wraps_index(self) -> None:
        state = TitleCodexState(index=len(CODEX_ENTRIES) - 1)
        state.step(1, elapsed=1.0)
        self.assertEqual(state.index, 0)

    def test_manual_step_pauses_auto_advance(self) -> None:
        state = TitleCodexState()
        state.step(1, elapsed=2.0, manual=True)
        state.tick(0.5, elapsed=2.5)
        self.assertEqual(state.index, 1)

    def test_auto_advance_after_interval(self) -> None:
        state = TitleCodexState()
        state.tick(0.0, elapsed=7.1)
        self.assertEqual(state.index, 1)


class TitleCodexLayoutTests(unittest.TestCase):
    def _layout(self):
        chrome = TitleScreenOverlay.chrome_layout()
        welcome = compute_welcome_home_layout(chrome, screen_w=960.0)
        return compute_codex_layout(welcome)

    def test_codex_viewport_contains_center(self) -> None:
        layout = self._layout()
        cx = layout.viewport_x + layout.viewport_w * 0.5
        cy = layout.viewport_y + layout.viewport_h * 0.5
        self.assertTrue(codex_viewport_contains(layout, cx, cy))

    def test_nav_buttons_inside_viewport(self) -> None:
        layout = self._layout()
        self.assertGreaterEqual(layout.prev_x, layout.viewport_x)
        self.assertLessEqual(layout.next_x + layout.next_w, layout.viewport_x + layout.viewport_w)


class TitleCodexDrawTests(unittest.TestCase):
    def test_all_entries_draw_without_error(self) -> None:
        root, canvas = _canvas()
        try:
            for entry in CODEX_ENTRIES:
                draw_codex_preview(canvas, entry, 480.0, 280.0, elapsed=1.2, yaw=0.6)
        finally:
            root.destroy()

    def test_welcome_registers_codex_hits(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        try:
            overlay.draw(
                canvas,
                page=TitlePage.WELCOME,
                campaign=__import__(
                    "gravity_ho_matey.gameplay.campaign", fromlist=["CampaignState"]
                ).CampaignState.new(),
                solar_unlocked=False,
                codex=TitleCodexState(),
            )
            ids = {r.id for r in overlay.hits.regions}
            self.assertIn("codex_prev", ids)
            self.assertIn("codex_next", ids)
            self.assertIn("codex_body", ids)
        finally:
            root.destroy()


class TitleCodexSceneTests(unittest.TestCase):
    def test_wheel_over_hangar_steps_codex(self) -> None:
        from gravity_ho_matey.render.title_home_layout import compute_codex_layout, compute_welcome_home_layout
        from gravity_ho_matey.render.title_overlay import TitleScreenOverlay

        class _Host:
            renderer = type("_R", (), {"title_hit_test": lambda _s, _x, _y: None})()

        scene = TitleScene()
        chrome = TitleScreenOverlay.chrome_layout()
        layout = compute_codex_layout(
            compute_welcome_home_layout(chrome, screen_w=960.0),
            scene.codex.entry(),
        )
        cx = layout.viewport_x + layout.viewport_w * 0.5
        cy = layout.viewport_y + layout.viewport_h * 0.5
        scene.on_wheel(_Host(), cx, cy, 1)
        self.assertEqual(scene.codex.index, 1)

    def test_up_down_keys_step_codex_on_welcome(self) -> None:
        from gravity_ho_matey.scenes.base import SceneHost

        class _Host:
            renderer = type("_R", (), {"title_hit_test": lambda _s, _x, _y: None})()

        scene = TitleScene()
        scene.on_key_press(_Host(), "down")
        self.assertEqual(scene.codex.index, 1)
        scene.on_key_press(_Host(), "up")
        self.assertEqual(scene.codex.index, 0)


class TitleCodexContentTests(unittest.TestCase):
    def test_entry_count_is_ten(self) -> None:
        ids = {e.entry_id for e in CODEX_ENTRIES}
        self.assertIn("drone", ids)
        self.assertIn("hostile_stn", ids)
        self.assertIn("relay", ids)
        self.assertIn("corsair", ids)
        self.assertNotIn("brood", ids)
        self.assertNotIn("moon_matriarch", ids)
        self.assertEqual(len(CODEX_ENTRIES), 10)

    def test_all_preview_kinds_are_supported(self) -> None:
        from gravity_ho_matey.render.title_codex_tactical import draw_codex_tactical_preview
        from gravity_ho_matey.render.lighting import LightRig
        from gravity_ho_matey.render.camera import CameraMode

        root, canvas = _canvas()
        try:
            rig = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
            for entry in CODEX_ENTRIES:
                canvas.delete("all")
                draw_codex_tactical_preview(
                    canvas, entry, 120.0, 120.0, rig=rig, elapsed=1.0, yaw=0.3,
                )
                self.assertGreater(len(canvas.find_all()), 0, msg=entry.entry_id)
        finally:
            root.destroy()

    def test_blurb_is_single_string(self) -> None:
        for entry in CODEX_ENTRIES:
            self.assertGreater(len(entry.blurb), 12)
            self.assertNotIn("\n", entry.blurb)


class TitleCodexVizTests(unittest.TestCase):
    def test_turntable_scale_oscillates(self) -> None:
        narrow = turntable_scale_x(1.5708)
        wide = turntable_scale_x(0.0)
        self.assertLess(narrow, wide)


if __name__ == "__main__":
    unittest.main()
