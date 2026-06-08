from __future__ import annotations

import unittest

from gravity_ho_matey.gameplay.wave_ingress import (
    ingress_wave_index,
    relay_wave_ingress_markers,
    wave_ingress_markers_for_world,
)
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.guard_layout import STATION_RELAY
from gravity_ho_matey.levels.level_registry import build_level


class WaveIngressTests(unittest.TestCase):
    def test_relay_wave_one_has_nw_and_ne_lanes(self) -> None:
        markers = relay_wave_ingress_markers(1, station=STATION_RELAY)
        tags = {m.tag for m in markers}
        self.assertEqual(tags, {"NW", "NE"})
        for marker in markers:
            self.assertIsNotNone(marker.toward)

    def test_relay_wave_three_has_three_lanes(self) -> None:
        markers = relay_wave_ingress_markers(3, station=STATION_RELAY)
        self.assertEqual({m.tag for m in markers}, {"NW", "N", "NE"})

    def test_active_wave_one_shows_ingress_on_rift(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        self.assertEqual(world.wave_director.waves_spawned, 1)
        self.assertEqual(ingress_wave_index(world), 1)
        tags = {m.tag for m in wave_ingress_markers_for_world(world)}
        self.assertEqual(tags, {"NW", "NE"})

    def test_cleared_wave_shows_next_ingress_during_breather(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        self.assertEqual(ingress_wave_index(world), 2)
        tags = {m.tag for m in wave_ingress_markers_for_world(world)}
        self.assertEqual(tags, {"N"})

    def test_no_ingress_after_all_waves_cleared(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        world.wave_director.waves_spawned = 3
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        self.assertTrue(world.protection_combat_cleared)
        self.assertIsNone(ingress_wave_index(world))


if __name__ == "__main__":
    unittest.main()
