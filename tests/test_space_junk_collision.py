import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.damage import DamageSource, damage_spec_for
from gravity_ho_matey.gameplay.entities import ContactPolicy, GameStatus, Ship
from gravity_ho_matey.gameplay.space_junk import apply_junk_separation, junk_hit_at, resolve_junk_bounce
from gravity_ho_matey.gameplay.space_junk_prefabs import instantiate_junk
from gravity_ho_matey.gameplay.space_junk_spatial import JunkSpatialGrid
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.gameplay.entities import FinishGate, WorldConfig


def _wall_at(x: float) -> list:
    return [instantiate_junk("girder_a", Vec2(x, 500.0), angle=0.0)]


class SpaceJunkCollisionTests(unittest.TestCase):
    def test_separation_pushes_circle_out(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(500.0, 500.0))
        spatial = JunkSpatialGrid()
        spatial.rebuild([junk])
        pos = Vec2(500.0, 500.0)
        vel = Vec2(0.0, -120.0)
        new_pos, new_vel = apply_junk_separation(pos, vel, 12.0, [junk], spatial)
        self.assertFalse(junk_hit_at([junk], spatial, new_pos, 12.0))

    def test_bounce_policy_no_damage(self) -> None:
        junk = instantiate_junk("docking_claw_a", Vec2(400.0, 400.0), contact_policy=ContactPolicy.BOUNCE)
        config = WorldConfig(width=800, height=800, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(400.0, 400.0), vel=Vec2(0.0, -80.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(700, 700, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
        )
        world.junk_spatial.rebuild(world.space_junk)
        world.update(1 / 60.0, ControlIntent())
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertIsNone(world.last_damage)

    def test_chip_registers_space_junk_damage(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(300.0, 300.0))
        config = WorldConfig(width=800, height=800, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(300.0, 300.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(700, 700, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
        )
        world.junk_spatial.rebuild(world.space_junk)
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertIsNotNone(world.last_damage)
        assert world.last_damage is not None
        self.assertIs(world.last_damage.source, DamageSource.SPACE_JUNK)

    def test_rubber_hull_bounce_consumes_charge(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(200.0, 200.0))
        charges = {"left": 1}

        def consume() -> bool:
            if charges["left"] <= 0:
                return False
            charges["left"] -= 1
            return True

        config = WorldConfig(width=800, height=800, open_bounds=True)
        ship = Ship(pos=Vec2(200.0, 200.0), vel=Vec2(0.0, -90.0))
        world = GameWorld(
            config=config,
            ship=ship,
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(700, 700, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
            consume_rubber_hull_bounce=consume,
        )
        world.junk_spatial.rebuild(world.space_junk)
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertEqual(charges["left"], 0)

    def test_damage_rules_chip(self) -> None:
        spec = damage_spec_for(DamageSource.SPACE_JUNK)
        self.assertEqual(spec.chunks, 1)


if __name__ == "__main__":
    unittest.main()
