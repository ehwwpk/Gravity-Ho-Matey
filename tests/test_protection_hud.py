from __future__ import annotations

import unittest

from gravity_ho_matey.gameplay.hud_objectives import objective_counters_for_world
from gravity_ho_matey.levels.level_registry import build_level


class ProtectionHudTests(unittest.TestCase):
    def test_rift_has_wave_and_hostile_counters(self) -> None:
        world = build_level("rift")
        counters = objective_counters_for_world(world)
        labels = [c.label for c in counters]
        self.assertIn("WAVES", labels)
        self.assertIn("HOSTILES", labels)

    def test_wave_counter_updates_after_spawn(self) -> None:
        from gravity_ho_matey.gameplay.world import ControlIntent

        world = build_level("rift")
        world.update(0.016, ControlIntent())
        counters = objective_counters_for_world(world)
        waves = next(c for c in counters if c.label == "WAVES")
        self.assertEqual(waves.total, 3)
        self.assertEqual(waves.remaining, 2)


if __name__ == "__main__":
    unittest.main()
