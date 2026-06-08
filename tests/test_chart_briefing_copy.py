import unittest

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER
from gravity_ho_matey.narrative.chart_briefing_copy import LEVEL_BRIEFING, LEVEL_INTEL


class ChartBriefingCopyTests(unittest.TestCase):
    def test_every_level_has_briefing_and_intel(self) -> None:
        for level_id in LEVEL_ORDER:
            self.assertIn(level_id, LEVEL_BRIEFING, msg=level_id)
            self.assertIn(level_id, LEVEL_INTEL, msg=level_id)
            self.assertGreaterEqual(len(LEVEL_BRIEFING[level_id]), 4)
            self.assertGreaterEqual(len(LEVEL_INTEL[level_id]), 2)

    def test_briefings_name_win_condition(self) -> None:
        joined = " ".join(v for _, v in LEVEL_BRIEFING["cove"])
        self.assertIn("three required", joined)
        joined = " ".join(v for _, v in LEVEL_BRIEFING["siege"])
        self.assertIn("12", joined)

    def test_rift_briefing_names_corsair_hold(self) -> None:
        joined = " ".join(v for _, v in LEVEL_BRIEFING["rift"]).lower()
        self.assertIn("corsair", joined)
        self.assertIn("clear all hostiles", joined)
        intel = " ".join(v for _, v in LEVEL_INTEL["rift"]).lower()
        self.assertIn("relay", intel)
        self.assertIn("extract", intel)


if __name__ == "__main__":
    unittest.main()
