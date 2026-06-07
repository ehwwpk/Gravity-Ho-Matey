from __future__ import annotations

import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.space_station import SpaceStation, STATION_HITS_MAX
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.gameplay.tractor_beam import TractorBeamState, TractorPhase
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.level_registry import build_level, next_level_id
from gravity_ho_matey.levels.siege_layout import (
    ALLY_WING_COUNT,
    ARENA_HEIGHT,
    ARENA_WIDTH,
    ROSTER_ENEMY_COUNT,
    ROSTER_KILL_QUOTA,
)


class SiegeLevelBuildTests(unittest.TestCase):
    def test_siege_builder_counts(self) -> None:
        world = build_level("siege")
        self.assertEqual(world.config.width, ARENA_WIDTH)
        self.assertEqual(world.config.height, ARENA_HEIGHT)
        self.assertEqual(world.config.level_theme, "siege")
        self.assertTrue(world.config.exit_requires_roster_clear)
        self.assertEqual(world.config.roster_kill_quota, ROSTER_KILL_QUOTA)
        self.assertEqual(len(world.enemies), ROSTER_ENEMY_COUNT)
        self.assertEqual(len(world.allies), ALLY_WING_COUNT)
        self.assertIsNotNone(world.space_station)
        self.assertIsNotNone(world.tractor_beam)
        self.assertEqual(world.roster_enemies_total, ROSTER_KILL_QUOTA)
        self.assertEqual(world.roster_enemies_remaining, ROSTER_KILL_QUOTA)
        self.assertGreaterEqual(len(world.asteroids), 50)
        self.assertEqual(len(world.wells), 4)
        self.assertFalse(world.finish_unlocked)

    def test_all_roster_enemies_tagged(self) -> None:
        world = build_level("siege")
        ids = {e.skirmish_roster_id for e in world.enemies}
        self.assertEqual(ids, set(range(ROSTER_ENEMY_COUNT)))

    def test_campaign_order_includes_siege(self) -> None:
        self.assertEqual(next_level_id("rift"), "siege")
        self.assertIsNone(next_level_id("siege"))


class SiegeWinConditionTests(unittest.TestCase):
    def _siege_world(self) -> GameWorld:
        return build_level("siege")

    def test_gate_locked_until_twelve_kills(self) -> None:
        world = self._siege_world()
        for enemy in list(world.enemies):
            enemy.alive = False
            world._register_roster_kill(enemy)
            world._prune_dead_enemies()
            if world.roster_enemies_remaining == 1:
                self.assertFalse(world.finish_unlocked)
            if world.roster_enemies_remaining == 0:
                break
        self.assertTrue(world.finish_unlocked)

    def test_station_spawns_while_roster_full(self) -> None:
        world = self._siege_world()
        station = world.space_station
        assert station is not None
        spawned_count = 0
        for _ in range(400):
            station.integrate(0.05, world.wells, gravity_scale=1.0, drag=0.98)
            alive_station_spawns = sum(
                1
                for e in world.enemies
                if e.alive and getattr(e, "skirmish_roster_id", None) is None
            )
            spawned = station.tick_spawns(0.05, alive_station_spawns)
            if spawned is not None:
                world.enemies.append(spawned)
                spawned_count += 1
        self.assertGreaterEqual(spawned_count, 1)
        self.assertEqual(world.roster_enemies_remaining, ROSTER_KILL_QUOTA)

    def test_win_on_gate_intersect_when_roster_clear(self) -> None:
        world = self._siege_world()
        for enemy in world.enemies:
            enemy.alive = False
            world._register_roster_kill(enemy)
        world._prune_dead_enemies()
        gate = world.finish_gate.rect
        world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        world._check_finish()
        self.assertEqual(world.status, GameStatus.WON)


class SpaceStationCombatTests(unittest.TestCase):
    def test_station_takes_damage_and_drops_jewels(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=800, height=600, level_theme="siege"),
            ship=Ship(pos=Vec2(100, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(0, 0, 20, 20)),
        )
        station = SpaceStation(
            pos=Vec2(400, 300),
            anchor=Vec2(400, 300),
            faction=StationFaction.HOSTILE,
        )
        world.space_station = station
        for _ in range(STATION_HITS_MAX):
            bolt = Projectile(pos=Vec2(station.pos.x, station.pos.y), vel=Vec2(), ttl=1.0, hostile=False)
            world._projectile_hits_station(bolt)
        self.assertFalse(station.alive)
        self.assertTrue(world.station_cleared)
        self.assertGreater(len(world.jewels), 0)

    def test_tractor_cycle_does_not_crash(self) -> None:
        from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid

        world = build_level("siege")
        station = world.space_station
        tractor = world.tractor_beam
        assert station is not None and tractor is not None
        rock = make_asteroid(Vec2(station.pos.x - 220, station.pos.y), seed=1, size_class="rock")
        world.asteroids.append(rock)
        tractor.begin_acquire(rock, world.ship.pos)
        for _ in range(120):
            station.tick_tractor(0.05, tractor, world.asteroids, world.ship.pos, world.allies)
        self.assertIn(tractor.phase, (TractorPhase.COOLDOWN, TractorPhase.IDLE, TractorPhase.PULLING))

    def test_hostile_bolt_kills_ally(self) -> None:
        world = build_level("siege")
        ally = world.allies[0]
        bolt = Projectile(pos=Vec2(ally.pos.x, ally.pos.y), vel=Vec2(), ttl=1.0, hostile=True)
        world._projectile_hits_ally_hostile(bolt)
        self.assertFalse(ally.alive)


if __name__ == "__main__":
    unittest.main()
