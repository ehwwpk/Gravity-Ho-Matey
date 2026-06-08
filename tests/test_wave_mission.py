from __future__ import annotations

import unittest

from gravity_ho_matey.gameplay.wave_mission import (
    CLEAR_BREATHER,
    INBOUND_HINT_SECONDS,
    WAVE_NUDGE_SECONDS,
    WAVE_STACK_CAP,
    WaveMissionPresentation,
)
from gravity_ho_matey.levels.guard_layout import (
    NORTHERN_RIFT,
    STATION_RELAY,
    build_guard_layout,
)
from gravity_ho_matey.levels.guard_waves import (
    WAVE3_FIGHTER_COUNT,
    WAVE3_SQUID_COUNT,
    spawn_wave2_squids,
    spawn_wave3_assault,
)


class WaveMissionPresentationTests(unittest.TestCase):
    def test_wave_one_spawns_without_nudge(self) -> None:
        director = WaveMissionPresentation()
        director.tick(0.0, 0.0)
        wave = director.poll_spawn(0.0, hostiles_alive=0)
        self.assertEqual(wave, 1)
        self.assertEqual(director.nudge_wave, 0)
        self.assertAlmostEqual(director.nudge_ttl, 0.0)

    def test_inbound_hint_before_wave_two(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0, hostiles_alive=0)
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
        director.poll_spawn(0.0, hostiles_alive=0)
        wave = director.poll_spawn(20.0, hostiles_alive=0)
        self.assertEqual(wave, 2)
        self.assertEqual(director.nudge_wave, 2)
        self.assertAlmostEqual(director.nudge_ttl, WAVE_NUDGE_SECONDS)
        copy = director.nudge_copy()
        self.assertIsNotNone(copy)
        assert copy is not None
        self.assertEqual(copy.subtitle, "void squids")

    def test_wave_three_nudge_on_spawn(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0, hostiles_alive=0)
        director.poll_spawn(20.0, hostiles_alive=0)
        wave = director.poll_spawn(40.0, hostiles_alive=0)
        self.assertEqual(wave, 3)
        self.assertEqual(director.nudge_wave, 3)
        copy = director.nudge_copy()
        self.assertIsNotNone(copy)
        assert copy is not None
        self.assertEqual(copy.subtitle, "squids + corsairs")

    def test_clear_to_advance_after_breather(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0, hostiles_alive=0)
        self.assertIsNone(director.poll_spawn(2.0, hostiles_alive=0))
        wave = director.poll_spawn(3.0, hostiles_alive=0)
        self.assertEqual(wave, 2)

    def test_stack_cap_blocks_next_wave(self) -> None:
        director = WaveMissionPresentation()
        director.poll_spawn(0.0, hostiles_alive=0)
        self.assertIsNone(director.poll_spawn(25.0, hostiles_alive=WAVE_STACK_CAP))


class GuardIngressTests(unittest.TestCase):
    def test_wave_two_squids_spawn_with_ingress_velocity(self) -> None:
        layout = build_guard_layout()
        squids = spawn_wave2_squids(layout)
        self.assertEqual(len(squids), 7)
        for squid in squids:
            self.assertGreater(squid.vel.length(), 80.0)

    def test_wave_three_assault_from_north_arc(self) -> None:
        layout = build_guard_layout()
        enemies = spawn_wave3_assault(layout)
        self.assertEqual(len(enemies), WAVE3_SQUID_COUNT + WAVE3_FIGHTER_COUNT)
        for enemy in enemies:
            if enemy.kind.name == "SQUID":
                self.assertLess(enemy.pos.y, STATION_RELAY.y)
        fighters = [e for e in enemies if hasattr(e, "kind") and e.kind.name == "HOSTILE_FIGHTER"]
        self.assertEqual(len(fighters), WAVE3_FIGHTER_COUNT)
        for fighter in fighters:
            self.assertGreater(fighter.vel.length(), 60.0)

    def test_northern_rift_is_ingress_anchor(self) -> None:
        layout = build_guard_layout()
        self.assertEqual(layout.squid_ring_center, NORTHERN_RIFT)


if __name__ == "__main__":
    unittest.main()
