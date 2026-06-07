from __future__ import annotations

import unittest

from gravity_ho_matey.render.brood_fauna_viz import FAUNA_DRAW_MAX, _FAUNA_SPECS
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.brood_viz_helpers import (
    draw_brood_membrane_ring,
    draw_brood_rim_bloom,
    draw_brood_vein_glow_line,
)
from gravity_ho_matey.render.lighting import LightRig, material_for


class BroodSurfacePolishTests(unittest.TestCase):
    def test_fauna_catalog_populated(self) -> None:
        self.assertGreaterEqual(len(_FAUNA_SPECS), 16)
        kinds = {spec.kind for spec in _FAUNA_SPECS}
        self.assertIn("spore_jelly", kinds)
        self.assertIn("veil_wisp", kinds)
        self.assertIn("drift_ribbon", kinds)

    def test_fauna_draw_cap(self) -> None:
        self.assertGreaterEqual(FAUNA_DRAW_MAX, 24)

    def test_brood_membrane_material(self) -> None:
        rig = LightRig.for_play(theme="brood_moon", camera_mode=CameraMode.TACTICAL)
        mat = material_for("brood_membrane", theme=rig.theme, view=rig.view)
        self.assertTrue(mat.highlight)
        self.assertTrue(mat.rim)

    def test_polish_helpers_callable(self) -> None:
        self.assertTrue(callable(draw_brood_rim_bloom))
        self.assertTrue(callable(draw_brood_vein_glow_line))
        self.assertTrue(callable(draw_brood_membrane_ring))

    def test_surface_props_include_flora_kinds(self) -> None:
        from gravity_ho_matey.levels.brood_moon_props import BROOD_SURFACE_PROPS

        kinds = {p.kind for p in BROOD_SURFACE_PROPS}
        self.assertIn("chitin_bloom", kinds)
        self.assertIn("float_bulb", kinds)
        self.assertGreaterEqual(len(BROOD_SURFACE_PROPS), 20)


if __name__ == "__main__":
    unittest.main()
