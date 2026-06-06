import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.chart_bounds import CHART_RADIATION_EXPOSURE_LIMIT
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def to_control_intent(self) -> ControlIntent:
        return ControlIntent()


class _FakeHost:
    input_state = _FakeInput()

    def set_scene(self, _scene: object) -> None:
        pass


class RadiationPlaySceneTests(unittest.TestCase):
    def test_radiation_chip_applies_one_chunk_without_spawn_teleport(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(-30, 400)
        start = Vec2(scene.world.spawn_pos.x, scene.world.spawn_pos.y)
        self.assertEqual(scene.campaign.hull_chunks, 3)

        remaining = CHART_RADIATION_EXPOSURE_LIMIT + 0.2
        while remaining > 0 and scene.world.status is GameStatus.RUNNING:
            step = min(remaining, 0.05)
            scene.update(_FakeHost(), step)
            remaining -= step

        self.assertEqual(scene.campaign.hull_chunks, 2)
        self.assertEqual(scene.world.status, GameStatus.RUNNING)
        self.assertNotAlmostEqual(scene.world.ship.pos.x, start.x)
        self.assertNotAlmostEqual(scene.world.ship.pos.y, start.y)
        self.assertGreater(scene.world.invuln_remaining, 0.0)


if __name__ == "__main__":
    unittest.main()
