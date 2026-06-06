import math
import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, Ship, WorldConfig
from gravity_ho_matey.gameplay.session import capture_level_spawn
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.util.input import InputState


def tiny_world(*, angle: float = -math.pi / 2) -> GameWorld:
    world = GameWorld(
        config=WorldConfig(width=200, height=200),
        ship=Ship(pos=Vec2(100, 100), angle=angle),
        walls=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(150, 150, 25, 25)),
    )
    capture_level_spawn(world)
    return world


class BoostBurstTests(unittest.TestCase):
    def test_tap_adds_nose_velocity_without_thrust(self) -> None:
        world = tiny_world()
        before = world.ship.vel.length()
        world.update(0.016, ControlIntent(boost_tap=True))
        after = world.ship.vel.length()
        self.assertGreater(after, before + 80.0)
        self.assertLess(world.ship.vel.y, -80.0)
        self.assertLess(abs(world.ship.vel.x), 5.0)

    def test_hold_shift_does_not_repeat_burst(self) -> None:
        world = tiny_world()
        world.update(0.016, ControlIntent(boost_tap=True))
        speed_after_tap = world.ship.vel.length()
        world.update(0.016, ControlIntent(boost_tap=False))
        self.assertLess(world.ship.vel.length(), speed_after_tap + 40.0)

    def test_burst_costs_reactor_and_sets_flash(self) -> None:
        world = tiny_world()
        world.update(0.016, ControlIntent(boost_tap=True))
        self.assertLess(world.ship.boost_energy, 1.0)
        self.assertGreater(world.ship.boost_flash, 0.0)

    def test_empty_reactor_blocks_burst(self) -> None:
        world = tiny_world()
        world.ship.boost_energy = 0.05
        world.update(0.016, ControlIntent(boost_tap=True))
        self.assertEqual(world.ship.vel.length(), 0.0)
        self.assertEqual(world.ship.boost_flash, 0.0)

    def test_slip_burst_redirects_momentum_toward_nose(self) -> None:
        world = tiny_world(angle=0.0)
        world.ship.vel = Vec2(0.0, 180.0)
        world.update(0.016, ControlIntent(boost_tap=True))
        self.assertGreater(world.ship.vel.x, 40.0)

    def test_input_shift_edge_is_single_tap(self) -> None:
        state = InputState()
        state.set_key("Shift_L", True)
        self.assertTrue(state.to_control_intent().boost_tap)
        self.assertFalse(state.to_control_intent().boost_tap)
        state.set_key("Shift_L", False)
        state.set_key("Shift_L", True)
        self.assertTrue(state.to_control_intent().boost_tap)


if __name__ == "__main__":
    unittest.main()
