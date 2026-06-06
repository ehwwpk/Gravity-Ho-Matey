import unittest

from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.lighting import (
    LightRig,
    lerp_hex,
    material_for,
    shade_band,
    tone_for_band,
)


class LightRigTests(unittest.TestCase):
    def test_key_direction_consistent_across_views(self) -> None:
        cove_t = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
        cove_c = LightRig.for_play(theme="cove", camera_mode=CameraMode.CHASE)
        self.assertAlmostEqual(cove_t.key_dir.x, cove_c.key_dir.x, places=4)
        self.assertAlmostEqual(cove_t.key_dir.y, cove_c.key_dir.y, places=4)

    def test_solar_and_cove_materials_differ(self) -> None:
        cove = material_for("asteroid", theme="cove")
        solar = material_for("asteroid", theme="solar")
        self.assertNotEqual(cove.mid, solar.mid)

    def test_chase_cove_asteroids_use_physical_rock_not_holo(self) -> None:
        tactical = material_for("asteroid", theme="cove", view="tactical")
        chase = material_for("asteroid", theme="cove", view="chase")
        self.assertEqual(tactical.rim, palette.HOLO_ASTEROID_EDGE)
        self.assertNotEqual(chase.rim, tactical.rim)


class ShadeBandTests(unittest.TestCase):
    def test_shade_band_monotone(self) -> None:
        self.assertEqual(shade_band(0.9), 0)
        self.assertEqual(shade_band(0.2), 1)
        self.assertEqual(shade_band(-0.1), 2)
        self.assertEqual(shade_band(-0.9), 3)

    def test_tone_for_band_maps_all(self) -> None:
        mat = material_for("asteroid", theme="cove")
        self.assertEqual(tone_for_band(mat, 0), mat.highlight)
        self.assertEqual(tone_for_band(mat, 3), mat.deep)


class ColorUtilTests(unittest.TestCase):
    def test_lerp_hex_endpoints(self) -> None:
        self.assertEqual(lerp_hex("#000000", "#ffffff", 0.0), "#000000")
        self.assertEqual(lerp_hex("#000000", "#ffffff", 1.0), "#ffffff")


class MaterialTests(unittest.TestCase):
    def test_well_material_kinds(self) -> None:
        from gravity_ho_matey.render.lighting import well_material_kind

        self.assertEqual(well_material_kind("black_hole"), "well_black_hole")
        self.assertEqual(well_material_kind("planet"), "well_planet")
        self.assertEqual(well_material_kind("well"), "well_cove")


if __name__ == "__main__":
    unittest.main()
