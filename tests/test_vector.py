import unittest

from gravity_ho_matey.core.vector import Vec2


class Vec2Tests(unittest.TestCase):
    def test_length_and_normalized(self):
        v = Vec2(3, 4)
        self.assertEqual(v.length(), 5)
        n = v.normalized()
        self.assertAlmostEqual(n.length(), 1.0)

    def test_clamped_length(self):
        v = Vec2(10, 0).clamped_length(3)
        self.assertAlmostEqual(v.length(), 3.0)


if __name__ == "__main__":
    unittest.main()
