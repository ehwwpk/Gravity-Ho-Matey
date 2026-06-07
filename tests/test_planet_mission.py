from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.planet_mission import PlanetBody, in_planet_landing_band, limb_point_toward
from gravity_ho_matey.levels.brood_moon_layout import MOON_CENTER, MOON_RADIUS, build_brood_moon_orbital_layout


class PlanetMissionTests(unittest.TestCase):
    def test_landing_band_accepts_full_limb_ring(self) -> None:
        layout = build_brood_moon_orbital_layout()
        body = layout.planet
        for angle in (0.0, 1.2, 2.5, 4.0, 5.5):
            pos = body.center + Vec2.from_angle(angle) * (body.surface_radius + 90.0)
            self.assertTrue(in_planet_landing_band(pos, body), msg=f"angle {angle}")

    def test_landing_band_rejects_deep_space_and_surface_core(self) -> None:
        layout = build_brood_moon_orbital_layout()
        body = layout.planet
        self.assertFalse(in_planet_landing_band(body.center, body))
        far = body.center + Vec2(1.0, 0.0) * (body.landing_band_outer + 80.0)
        self.assertFalse(in_planet_landing_band(far, body))

    def test_limb_hint_faces_ship(self) -> None:
        body = PlanetBody.from_surface_radius(MOON_CENTER, MOON_RADIUS)
        ship = Vec2(620.0, 1580.0)
        limb = limb_point_toward(ship, body)
        self.assertAlmostEqual((limb - body.center).length(), body.surface_radius, places=3)


if __name__ == "__main__":
    unittest.main()
