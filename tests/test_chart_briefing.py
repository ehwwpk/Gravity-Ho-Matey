import unittest

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_data import build_cove_run_level, build_solar_crossing_level
from gravity_ho_matey.render.chart_map_overlay import ChartMapOverlay


def _canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class ChartBriefingLayoutTests(unittest.TestCase):
    def test_cove_briefing_draws_without_error(self) -> None:
        root, canvas = _canvas()
        world = build_cove_run_level()
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=24,
            rows=24,
            gravity_scale=world.config.gravity_scale,
        )
        ChartMapOverlay().draw(
            canvas,
            world,
            field,
            campaign=CampaignState.new(),
            upcoming_level_id="solar",
            cleared_level_id="cove",
            elapsed=42.5,
        )
        self.assertGreater(len(canvas.find_all()), 40)

    def test_solar_strip_uses_windowed_map(self) -> None:
        root, canvas = _canvas()
        world = build_solar_crossing_level()
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=24,
            rows=48,
            gravity_scale=world.config.gravity_scale,
        )
        overlay = ChartMapOverlay()
        overlay.draw(
            canvas,
            world,
            field,
            campaign=CampaignState.new(),
            upcoming_level_id="solar",
            cleared_level_id="cove",
            elapsed=90.0,
        )
        text_items = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        joined = " ".join(str(t) for t in text_items if t)
        self.assertIn("WINDOW", joined)
        self.assertIn("Singularity Crossing".upper(), joined)

    def test_map_transform_fits_compact_sector(self) -> None:
        world = build_cove_run_level()
        overlay = ChartMapOverlay()
        t = overlay._map_transform(world, 180.0, 100.0, 520.0, 400.0)
        self.assertFalse(t.strip_window)
        self.assertGreater(t.scale, 0.4)

    def test_map_transform_strip_is_width_fit(self) -> None:
        world = build_solar_crossing_level()
        overlay = ChartMapOverlay()
        t = overlay._map_transform(world, 180.0, 100.0, 520.0, 400.0)
        self.assertTrue(t.strip_window)
        self.assertAlmostEqual(t.scale, 520.0 / world.config.width, places=2)
        self.assertLess(t.world_y1 - t.world_y0, world.config.height)

    def test_inaugural_cove_briefing_draws_without_error(self) -> None:
        root, canvas = _canvas()
        world = build_cove_run_level()
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=24,
            rows=24,
            gravity_scale=world.config.gravity_scale,
        )
        ChartMapOverlay().draw(
            canvas,
            world,
            field,
            campaign=CampaignState.new(),
            upcoming_level_id="cove",
            cleared_level_id=None,
        )
        text_items = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        joined = " ".join(str(t) for t in text_items if t)
        self.assertIn("HOLO CHART OPEN", joined)
        self.assertIn("INITIAL BRIEF", joined)
        self.assertIn("BRIEFING", joined)
        self.assertGreater(len(canvas.find_all()), 40)
        root.destroy()

    def test_start_chart_briefing_factory_for_sector_one(self) -> None:
        from gravity_ho_matey.scenes.game_flow import start_chart_briefing

        scene = start_chart_briefing("cove")
        self.assertEqual(scene.upcoming_level_id, "cove")
        self.assertIsNone(scene.cleared_level_id)


if __name__ == "__main__":
    unittest.main()
