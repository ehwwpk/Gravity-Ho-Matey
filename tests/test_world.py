import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GameStatus, Ship, WorldConfig
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


def tiny_world() -> GameWorld:
    return GameWorld(
        config=WorldConfig(width=200, height=200),
        ship=Ship(pos=Vec2(20, 20)),
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

    def test_finish_wins_after_beacons_collected(self):
        world = tiny_world()
        world.update(0.016, ControlIntent())
        world.ship.pos = Vec2(160, 160)
        world.update(0.016, ControlIntent())
        self.assertEqual(world.status, GameStatus.WON)

    def test_fire_projectile_adds_projectile(self):
        world = tiny_world()
        world.fire_projectile()
        self.assertEqual(len(world.projectiles), 1)


if __name__ == "__main__":
    unittest.main()
