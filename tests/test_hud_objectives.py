from __future__ import annotations

import tkinter as tk
import unittest

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.hud_objectives import objective_counters_for_world
from gravity_ho_matey.gameplay.brood_moon_controller import apply_surface_layout
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay


class HudObjectiveCounterTests(unittest.TestCase):
    def test_cove_has_beacon_counter_only(self) -> None:
        world = build_level("cove")
        counters = objective_counters_for_world(world)
        self.assertEqual(len(counters), 1)
        self.assertEqual(counters[0].label, "NAV BEACONS")
        self.assertEqual(counters[0].remaining, len(world.beacons))

    def test_brood_surface_has_beacon_and_pod_counters(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        counters = objective_counters_for_world(world)
        self.assertEqual(len(counters), 2)
        self.assertEqual(counters[0].label, "NAV BEACONS")
        self.assertEqual(counters[1].label, "EGG PODS")
        self.assertEqual(counters[1].remaining, 8)
        self.assertEqual(counters[1].total, 8)
        self.assertFalse(counters[1].complete)

    def test_pod_counter_complete_at_six_ruptured(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        for i, pod in enumerate(world.egg_pods):
            pod.alive = i < 2
        counters = objective_counters_for_world(world)
        pod_counter = counters[1]
        self.assertEqual(pod_counter.remaining, 2)
        self.assertTrue(pod_counter.complete)

    def test_brood_surface_hud_uses_matching_objective_styles(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        world = build_level("brood_moon")
        apply_surface_layout(world)
        SciFiHudOverlay().draw(canvas, world, CampaignState.new())
        texts = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        fonts = {canvas.itemcget(i, "font") for i in canvas.find_all() if canvas.type(i) == "text"}
        self.assertIn("03 / 03", texts)
        self.assertIn("08 / 08", texts)
        self.assertIn("{Courier New} 14 bold", fonts)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
