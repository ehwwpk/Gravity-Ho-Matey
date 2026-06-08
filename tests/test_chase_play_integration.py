import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def __init__(self) -> None:
        self._shift_down = False

    def to_control_intent(self) -> ControlIntent:
        intent = ControlIntent(boost_tap=self._shift_down and not getattr(self, "_shift_was_down", False))
        self._shift_was_down = self._shift_down
        return intent

    def down(self, key: str) -> bool:
        return key == "e" and False

    def tap_shift(self) -> None:
        self._shift_down = True

    def release_shift(self) -> None:
        self._shift_down = False
        self._shift_was_down = False


class _FakeHost:
    def __init__(self) -> None:
        self.input_state = _FakeInput()


class ChasePlayIntegrationTests(unittest.TestCase):
    def test_boost_tap_edge_detected_once_per_burst(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        host = _FakeHost()
        scene.camera.mode = CameraMode.CHASE
        scene.world.ship.boost_energy = 1.0
        host.input_state.tap_shift()
        scene.update(host, 0.016)
        self.assertGreater(scene.world.ship.boost_flash, 0.0)
        self.assertAlmostEqual(scene.camera.boost_kick_y, 7.0, places=1)
        kick_after_first = scene.camera.boost_kick_y
        host.input_state.release_shift()
        scene.update(host, 0.016)
        self.assertLess(scene.camera.boost_kick_y, kick_after_first)

    def test_hull_chip_resets_chase_presentation(self) -> None:
        from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSource
        from gravity_ho_matey.gameplay.entities import GameStatus

        scene = PlayScene("cove", CampaignState.new())
        host = _FakeHost()
        scene.camera.mode = CameraMode.CHASE
        scene.camera.velocity_lag_y = 15.0
        scene.camera.fov_boost = 0.04
        scene.world.ship.boost_flash = 0.2
        scene.world.status = GameStatus.SHIP_HIT
        scene.world.last_damage = DamageEvent(DamageSource.ASTEROID)
        scene.campaign.hull_chunks = 3
        scene.update(host, 0.016)
        self.assertEqual(scene.world.ship.boost_flash, 0.0)
        self.assertEqual(scene.camera.velocity_lag_y, 0.0)
        self.assertEqual(scene.camera.fov_boost, 0.0)

    def test_cycle_mode_clears_dynamics_without_physics_change(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.camera.mode = CameraMode.CHASE
        scene.camera.velocity_lag_y = 10.0
        vel_before = Vec2(scene.world.ship.vel.x, scene.world.ship.vel.y)
        scene.camera.cycle_mode()
        scene.camera.cycle_mode()
        self.assertEqual(scene.camera.velocity_lag_y, 0.0)
        self.assertEqual(
            (scene.world.ship.vel.x, scene.world.ship.vel.y),
            (vel_before.x, vel_before.y),
        )


if __name__ == "__main__":
    unittest.main()
