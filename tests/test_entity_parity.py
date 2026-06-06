import unittest

from gravity_ho_matey.render import palette
from gravity_ho_matey.render.entity_viz import gate_label


class EntityParityTests(unittest.TestCase):
    def test_gate_labels_match_tactical_conventions(self) -> None:
        self.assertEqual(gate_label(unlocked=True, solar=False), "OPEN")
        self.assertEqual(gate_label(unlocked=False, solar=False), "LOCK")
        self.assertEqual(gate_label(unlocked=True, solar=True), "WORMHOLE")
        self.assertEqual(gate_label(unlocked=False, solar=True), "SEALED")

    def test_beacon_palette_uses_shared_colors(self) -> None:
        self.assertNotEqual(palette.BEACON, palette.BEACON_COLLECTED)
        self.assertEqual(palette.BEACON, "#53ffd0")


if __name__ == "__main__":
    unittest.main()
