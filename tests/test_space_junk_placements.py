import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_junk_prefabs import instantiate_junk, validate_space_junk_list
from gravity_ho_matey.levels.space_junk_placements import junk_wall_line, min_gate_gap_for_ship


class SpaceJunkPlacementTests(unittest.TestCase):
    def test_wall_line_overlap_between_segments(self) -> None:
        wall = junk_wall_line(Vec2(0, 0), Vec2(0, 400), prefab="girder_a", overlap=8.0)
        self.assertGreaterEqual(len(wall), 2)
        for i in range(len(wall) - 1):
            gap = (wall[i + 1].pos - wall[i].pos).length()
            piece_r = wall[i].approximate_radius()
            overlap = piece_r * 2.0 - gap
            self.assertGreaterEqual(overlap, 4.0, msg=f"segment {i} gap leak")

    def test_min_gate_gap_matches_ship_radius(self) -> None:
        self.assertGreaterEqual(min_gate_gap_for_ship(), 32.0)

    def test_validate_rejects_over_max(self) -> None:
        junk = [instantiate_junk("girder_a", Vec2(i * 10, 0)) for i in range(5)]
        with self.assertRaises(ValueError):
            validate_space_junk_list(junk, max_count=4)


if __name__ == "__main__":
    unittest.main()
