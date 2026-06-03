import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at


class GravityTests(unittest.TestCase):
    def test_well_pulls_toward_center(self):
        accel = gravity_acceleration_at(Vec2(50, 0), [GravityWell(Vec2(100, 0), strength=10000, radius=200)])
        self.assertGreater(accel.x, 0)
        self.assertAlmostEqual(accel.y, 0)

    def test_outside_radius_has_no_pull(self):
        accel = gravity_acceleration_at(Vec2(0, 0), [GravityWell(Vec2(1000, 0), strength=10000, radius=100)])
        self.assertEqual(accel, Vec2())


if __name__ == "__main__":
    unittest.main()
