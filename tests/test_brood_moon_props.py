from __future__ import annotations

import unittest

from gravity_ho_matey.levels.brood_moon_layout import SURFACE_BOSS_ANCHOR_FRAC, SURFACE_WRAP_WIDTH
from gravity_ho_matey.levels.brood_moon_props import BROOD_SURFACE_PROPS, zone_for_frac


class BroodMoonPropsTests(unittest.TestCase):
    def test_all_props_within_wrap_width(self) -> None:
        for prop in BROOD_SURFACE_PROPS:
            self.assertGreaterEqual(prop.pos.x, 0.0)
            self.assertLessEqual(prop.pos.x, float(SURFACE_WRAP_WIDTH))

    def test_boss_cathedral_zone_tracks_boss_anchor(self) -> None:
        self.assertEqual(zone_for_frac(SURFACE_BOSS_ANCHOR_FRAC), "boss_cathedral")


if __name__ == "__main__":
    unittest.main()
