import unittest
from collections import Counter

from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import powerup_hud_tag
from gravity_ho_matey.render.lighting import material_for
from gravity_ho_matey.render.ship_viz import _material_with_fittings


class PowerUpStackTests(unittest.TestCase):
    def test_hud_tag_shows_stack_count(self) -> None:
        self.assertEqual(powerup_hud_tag(PowerUpKind.THRUST_BOOST, 1), "THRUST")
        self.assertEqual(powerup_hud_tag(PowerUpKind.THRUST_BOOST, 2), "THRUST×2")

    def test_fittings_tint_rim_with_upgrades(self) -> None:
        base = material_for("ship", theme="cove")
        tinted = _material_with_fittings(base, Counter({PowerUpKind.RAPID_FIRE: 1}))
        self.assertNotEqual(base.rim, tinted.rim)


if __name__ == "__main__":
    unittest.main()
