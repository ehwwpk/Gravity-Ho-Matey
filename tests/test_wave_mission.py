from __future__ import annotations

import unittest

from gravity_ho_matey.gameplay.wave_mission import (
    INBOUND_HINT_SECONDS,
    WAVE_NUDGE_SECONDS,
    WaveMissionPresentation,
)
from gravity_ho_matey.levels.guard_layout import (
    BOSS_SPAWN,
    BOSS_SPAWN_RELAY_OFFSET,
    PLAYER_SPAWN,
    STATION_RELAY,
    build_guard_layout,
)
from gravity_ho_matey.levels.guard_waves import spawn_wave2_squids, spawn_wave3_squids_and_boss


class WaveMissionPresentationTests(unittest.TestCase):
    def test_wave_one_spawns_without_nudge(self) -> None:
        director = WaveMissionPresentation()
        director.tick(0.0, 0.0)
        wave = director.poll_spawn(0.0)
        self.assertEqual(wave, 1)
        self.assertEqual(director.nudge_wave, 0)
        self.assertAlmostEqual(director.nudge_ttl, 0.0)

    def test_inbound_hint_before_wave_two(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0)
        director.tick(15.0, 0.016)
        self.assertEqual(director.inbound_wave, 2)
        self.assertGreater(director.inbound_seconds, 0.0)
        self.assertLessEqual(director.inbound_seconds, INBOUND_HINT_SECONDS)

    def test_no_inbound_for_immediate_wave_one(self) -> None:
        director = WaveMissionPresentation()
        director.tick(0.0, 0.016)
        self.assertEqual(director.inbound_wave, 0)

    def test_wave_two_nudge_on_spawn(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0)
        wave = director.poll_spawn(20.0)
        self.assertEqual(wave, 2)
        self.assertEqual(director.nudge_wave, 2)
        self.assertAlmostEqual(director.nudge_ttl, WAVE_NUDGE_SECONDS)
        copy = director.nudge_copy()
        self.assertIsNotNone(copy)
        assert copy is not None
        self.assertEqual(copy.subtitle, "void squids")

    def test_wave_three_nudge_on_spawn(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0)
        director.poll_spawn(20.0)
        wave = director.poll_spawn(40.0)
        self.assertEqual(wave, 3)
        self.assertEqual(director.nudge_wave, 3)
        copy = director.nudge_copy()
        self.assertIsNotNone(copy)
        assert copy is not None
        self.assertEqual(copy.subtitle, "brood mother")


class GuardIngressTests(unittest.TestCase):
    def test_wave_two_squids_spawn_with_ingress_velocity(self) -> None:
        layout = build_guard_layout()
        squids = spawn_wave2_squids(layout)
        self.assertEqual(len(squids), 7)
        for squid in squids:
            self.assertGreater(squid.vel.length(), 80.0)

    def test_wave_three_boss_spawns_tight_on_relay_south(self) -> None:
        layout = build_guard_layout()
        _, boss = spawn_wave3_squids_and_boss(layout)
        self.assertGreater(BOSS_SPAWN.y, STATION_RELAY.y)
        self.assertLess(BOSS_SPAWN.y, PLAYER_SPAWN.y + 24.0)
        self.assertLess(BOSS_SPAWN_RELAY_OFFSET, 180.0)
        self.assertGreater(BOSS_SPAWN_RELAY_OFFSET, 120.0)
        self.assertEqual(boss.anchor, STATION_RELAY)
        self.assertGreater(boss.vel.length(), 80.0)
        self.assertLess(boss.vel.y, 0.0)


if __name__ == "__main__":
    unittest.main()
