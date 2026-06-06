import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def to_control_intent(self) -> ControlIntent:
        return ControlIntent()


class _FakeHost:
    input_state = _FakeInput()
    last_scene: object | None = None

    def set_scene(self, scene: object) -> None:
        self.last_scene = scene


class MultiPerspectiveFlowTests(unittest.TestCase):
    def test_play_scene_win_routes_to_chart_briefing_not_end(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        host = _FakeHost()
        for beacon in scene.world.beacons:
            beacon.collected = True
        scene.world.ship.pos = Vec2(scene.world.finish_gate.rect.x + 10, scene.world.finish_gate.rect.y + 10)
        scene.update(host, 0.016)
        self.assertEqual(scene.world.status, GameStatus.WON)
        self.assertIsInstance(host.last_scene, ChartBriefingScene)
        briefing = host.last_scene
        assert isinstance(briefing, ChartBriefingScene)
        self.assertEqual(briefing.upcoming_level_id, "solar")
        self.assertEqual(briefing.cleared_level_id, "cove")

    def test_camera_toggle_does_not_mutate_ship_physics_state(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.vel = Vec2(40, -20)
        before = (scene.world.ship.pos.x, scene.world.ship.pos.y, scene.world.ship.vel.x, scene.world.ship.angle)
        scene.camera.cycle_mode()
        scene.camera.cycle_mode()
        after = (scene.world.ship.pos.x, scene.world.ship.pos.y, scene.world.ship.vel.x, scene.world.ship.angle)
        self.assertEqual(before, after)

    def test_solar_strip_exceeds_viewport_height(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        self.assertGreater(scene.world.config.height, scene.world.config.viewport_height)
        self.assertGreaterEqual(scene.gravity_field.rows, 32)

    def test_tactical_follow_pans_when_ship_moves_down_strip(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene.world.ship.pos = Vec2(480, 1400)
        scene.camera.update_follow(scene.world.ship.pos, scene.world.config, 1.0)
        self.assertGreater(scene.camera.center.y, 600.0)

    def test_solar_campaign_complete_routes_to_end_scene(self) -> None:
        from gravity_ho_matey.scenes.end import EndScene

        scene = PlayScene("solar", CampaignState.new())
        host = _FakeHost()
        for beacon in scene.world.beacons:
            beacon.collected = True
        scene.world.ship.pos = Vec2(
            scene.world.finish_gate.rect.x + 10,
            scene.world.finish_gate.rect.y + 10,
        )
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, EndScene)
        end = host.last_scene
        assert isinstance(end, EndScene)
        self.assertTrue(end.won)

    def test_chart_briefing_launches_upcoming_level_on_enter(self) -> None:
        from gravity_ho_matey.scenes.game_flow import start_play

        briefing = ChartBriefingScene(
            upcoming_level_id="solar",
            campaign=CampaignState.new(),
            cleared_level_id="cove",
            elapsed=42.0,
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, PlayScene)
        play = host.last_scene
        assert isinstance(play, PlayScene)
        self.assertEqual(play.level_id, "solar")
        self.assertIsNot(host.last_scene, start_play("cove", CampaignState.new()))


if __name__ == "__main__":
    unittest.main()
