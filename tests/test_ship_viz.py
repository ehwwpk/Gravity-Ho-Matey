import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render.ship_viz import fighter_hull_screen_points


class FighterHullTests(unittest.TestCase):
    def test_hull_has_faceted_silhouette(self) -> None:
        pts = fighter_hull_screen_points(Vec2(100, 100), 0.0, 1.0)
        self.assertEqual(len(pts), 12)

    def test_hull_rotates_with_heading(self) -> None:
        base = fighter_hull_screen_points(Vec2(0, 0), 0.0, 1.0)
        turned = fighter_hull_screen_points(Vec2(0, 0), math.pi / 2, 1.0)
        self.assertNotAlmostEqual(base[0][0], turned[0][0], places=3)
        self.assertNotAlmostEqual(base[0][1], turned[0][1], places=3)

    def test_nose_leads_hull_along_heading(self) -> None:
        pos = Vec2(50, 50)
        angle = -0.4
        pts = fighter_hull_screen_points(pos, angle, 1.0)
        forward = Vec2.from_angle(angle)
        nose = Vec2(pts[0][0], pts[0][1])
        rel = nose - pos
        self.assertGreater(rel.dot(forward), 18.0)


if __name__ == "__main__":
    unittest.main()
