import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at


class GravityTests(unittest.TestCase):
    def test_well_pulls_toward_center(self):
        accel = gravity_acceleration_at(Vec2(50, 0), [GravityWell(Vec2(100, 0), strength=10000, radius=200)])
        self.assertGreater(accel.x, 0)
        self.assertAlmostEqual(accel.y, 0)

    def test_outside_radius_has_no_pull(self):
        accel = gravity_acceleration_at(Vec2(0, 0), [GravityWell(Vec2(1000, 0), strength=10000, radius=100)])
        self.assertEqual(accel, Vec2())

    def test_hazard_escape_pushes_away_from_black_hole(self):
        well = GravityWell(Vec2(100, 100), strength=52000, radius=150, kind="black_hole", maw_radius=22)
        escape = hazard_escape_acceleration_at(Vec2(100, 70), [well], gravity_scale=0.45)
        self.assertLess(escape.y, 0.0)

    def test_hazard_escape_pushes_away_from_planet(self):
        well = GravityWell(Vec2(200, 200), strength=24000, radius=90, kind="planet")
        escape = hazard_escape_acceleration_at(Vec2(230, 200), [well], gravity_scale=0.45)
        self.assertGreater(escape.x, 0.0)

    def test_hazard_escape_ignores_cove_wells(self):
        well = GravityWell(Vec2(100, 100), strength=40000, radius=180, kind="well")
        escape = hazard_escape_acceleration_at(Vec2(100, 70), [well], gravity_scale=0.5)
        self.assertEqual(escape, Vec2())


if __name__ == "__main__":
    unittest.main()
