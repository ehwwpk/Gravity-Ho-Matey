import unittest

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.session import LOOT_TOAST_SECONDS
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def to_control_intent(self) -> ControlIntent:
        return ControlIntent()


class _FakeHost:
    input_state = _FakeInput()

    def set_scene(self, _scene: object) -> None:
        pass


class LootHudTests(unittest.TestCase):
    def test_play_scene_sets_loot_toast_on_pickup(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene._on_powerup_collected_hud(PowerUpKind.THRUST_BOOST, True)
        self.assertEqual(scene.loot_toast_kind, PowerUpKind.THRUST_BOOST)
        self.assertTrue(scene.loot_toast_is_new)
        self.assertAlmostEqual(scene.loot_toast_ttl, LOOT_TOAST_SECONDS)

    def test_loot_toast_expires_after_duration(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene._on_powerup_collected_hud(PowerUpKind.STABILIZER, True)
        scene.update(_FakeHost(), LOOT_TOAST_SECONDS + 0.1)
        self.assertIsNone(scene.loot_toast_kind)
        self.assertEqual(scene.loot_toast_ttl, 0.0)


if __name__ == "__main__":
    unittest.main()
