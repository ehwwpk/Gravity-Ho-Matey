import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GameStatus, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.jewel_drops import jewel_count_for_beacon
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


def tiny_world(*, ship_pos: Vec2 | None = None) -> GameWorld:
    return GameWorld(
        config=WorldConfig(width=200, height=200),
        ship=Ship(pos=ship_pos or Vec2(20, 20)),
        asteroids=[],
        wells=[],
        beacons=[Beacon(Vec2(20, 20))],
        finish_gate=FinishGate(Rect(150, 150, 25, 25)),
    )


class WorldTests(unittest.TestCase):
    def test_beacon_collection_unlocks_finish(self):
        world = tiny_world()
        self.assertFalse(world.finish_unlocked)
        world.update(0.016, ControlIntent())
        self.assertTrue(world.finish_unlocked)

    def test_beacon_collection_spawns_jewels(self) -> None:
        beacon_pos = Vec2(20, 20)
        world = tiny_world()
        expected = jewel_count_for_beacon(beacon_pos)
        world.update(0.016, ControlIntent())
        self.assertTrue(world.beacons[0].collected)
        self.assertEqual(len(world.jewels), expected)
        self.assertGreaterEqual(expected, 2)
        self.assertLessEqual(expected, 5)

    def test_chase_capture_slack_collects_from_farther_away(self):
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(0, 0)),
            asteroids=[],
            wells=[],
            beacons=[Beacon(Vec2(24, 0))],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world.update(0.016, ControlIntent(), beacon_capture_slack=0.0)
        self.assertFalse(world.beacons[0].collected)
        world.update(0.016, ControlIntent(), beacon_capture_slack=5.0)
        self.assertTrue(world.beacons[0].collected)

    def test_finish_wins_after_beacons_collected(self):
        world = tiny_world()
        world.update(0.016, ControlIntent())
        world.ship.pos = Vec2(160, 160)
        world.update(0.016, ControlIntent())
        self.assertEqual(world.status, GameStatus.WON)

    def test_chart_sectors_unlock_with_one_beacon_skipped(self) -> None:
        from gravity_ho_matey.levels.level_registry import build_level

        for level_id, required in (("cove", 3), ("solar", 2)):
            world = build_level(level_id)
            self.assertEqual(world.beacons_required_for_exit, required)
            for beacon in world.beacons[: required - 1]:
                beacon.collected = True
            self.assertFalse(world.finish_unlocked)
            world.beacons[required - 1].collected = True
            self.assertTrue(world.finish_unlocked)

    def test_fire_projectile_adds_projectile(self):
        world = tiny_world()
        world.fire_projectile()
        self.assertEqual(len(world.projectiles), 1)

    def test_open_bounds_projectile_survives_off_map(self) -> None:
        world = tiny_world(ship_pos=Vec2(-60, 100))
        world.fire_projectile()
        world._update_projectiles(0.016)
        self.assertEqual(len(world.projectiles), 1)

    def test_closed_bounds_culls_off_map_projectile(self) -> None:
        world = tiny_world()
        world.config = WorldConfig(width=200, height=200, open_bounds=False)
        world.projectiles.append(Projectile(pos=Vec2(-50, 100), vel=Vec2(100, 0)))
        world._update_projectiles(0.016)
        self.assertEqual(len(world.projectiles), 0)


if __name__ == "__main__":
    unittest.main()
