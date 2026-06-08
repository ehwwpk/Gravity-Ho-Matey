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

    def test_camera_toggle_preserves_weapon_heat(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.weapon_heat = 0.55
        scene.world.ship.weapon_overheat_timer = 0.4
        scene.camera.cycle_mode()
        self.assertAlmostEqual(scene.world.ship.weapon_heat, 0.55)
        self.assertAlmostEqual(scene.world.ship.weapon_overheat_timer, 0.4)

    def test_cove_play_scene_snaps_tactical_camera_on_start(self) -> None:
        scene = PlayScene("cove", CampaignState.new())
        scene.world.ship.pos = Vec2(880, 550)
        scene.camera.snap_tactical_to_ship(scene.world.ship.pos, scene.world.config)
        p = scene.camera.world_to_screen(scene.world.ship.pos, scene.world.ship.pos, 0.0)
        hud = 54
        self.assertGreater(p.x, 16.0)
        self.assertLess(p.x, scene.world.config.viewport_width - 16.0)
        self.assertGreater(p.y + hud, hud + 16.0)
        self.assertLess(p.y + hud, scene.world.config.viewport_height - 16.0)

    def test_solar_strip_exceeds_viewport_height(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        self.assertGreater(scene.world.config.height, scene.world.config.viewport_height)
        self.assertGreaterEqual(scene.gravity_field.rows, 32)

    def test_tactical_follow_pans_when_ship_moves_down_strip(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene.world.ship.pos = Vec2(480, 1400)
        scene.camera.update_follow(scene.world.ship.pos, scene.world.config, 1.0)
        self.assertGreater(scene.camera.center.y, 600.0)

    def test_solar_win_routes_to_drift_briefing(self) -> None:
        from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

        scene = PlayScene("solar", CampaignState.new())
        host = _FakeHost()
        for beacon in scene.world.beacons:
            beacon.collected = True
        scene.world.ship.pos = Vec2(
            scene.world.finish_gate.rect.x + 10,
            scene.world.finish_gate.rect.y + 10,
        )
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, ChartBriefingScene)
        briefing = host.last_scene
        assert isinstance(briefing, ChartBriefingScene)
        self.assertEqual(briefing.upcoming_level_id, "drift")

    def test_drift_campaign_complete_routes_to_rift_briefing(self) -> None:
        from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

        scene = PlayScene("drift", CampaignState.new())
        host = _FakeHost()
        scene.world.ship.pos = Vec2(
            scene.world.finish_gate.rect.x + 10,
            scene.world.finish_gate.rect.y + 10,
        )
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, ChartBriefingScene)
        briefing = host.last_scene
        assert isinstance(briefing, ChartBriefingScene)
        self.assertEqual(briefing.upcoming_level_id, "rift")

    def test_rift_win_routes_to_siege_briefing(self) -> None:
        from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

        scene = PlayScene("rift", CampaignState.new())
        host = _FakeHost()
        scene.world.wave_director.waves_spawned = 3  # type: ignore[union-attr]
        for enemy in scene.world.enemies:
            enemy.alive = False
        scene.world._prune_dead_enemies()
        gate = scene.world.finish_gate.rect
        scene.world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, ChartBriefingScene)
        briefing = host.last_scene
        assert isinstance(briefing, ChartBriefingScene)
        self.assertEqual(briefing.upcoming_level_id, "siege")

    def test_siege_campaign_complete_routes_to_brood_moon_briefing(self) -> None:
        from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

        scene = PlayScene("siege", CampaignState.new())
        host = _FakeHost()
        for enemy in scene.world.enemies:
            enemy.alive = False
            scene.world._register_roster_kill(enemy)
        scene.world._prune_dead_enemies()
        gate = scene.world.finish_gate.rect
        scene.world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, ChartBriefingScene)
        briefing = host.last_scene
        assert isinstance(briefing, ChartBriefingScene)
        self.assertEqual(briefing.upcoming_level_id, "brood_moon")

    def test_brood_moon_campaign_complete_routes_to_end_scene(self) -> None:
        from gravity_ho_matey.gameplay.brood_moon_controller import apply_surface_layout
        from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase
        from gravity_ho_matey.levels.brood_moon_layout import SEAL_TRAVEL_DISTANCE
        from gravity_ho_matey.scenes.end import EndScene

        scene = PlayScene("brood_moon", CampaignState.new())
        apply_surface_layout(scene.world)
        bm = scene.world.brood_moon
        assert bm is not None
        for beacon in scene.world.beacons:
            beacon.collected = True
        for pod in scene.world.egg_pods:
            pod.alive = False
        bm.objectives_complete = True
        bm.seal_travel = SEAL_TRAVEL_DISTANCE
        bm.seal_complete = True
        bm.phase = BroodPhase.ORBITAL_RETURN
        bm.dock_unlocked = True
        gate = scene.world.finish_gate.rect
        scene.world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        host = _FakeHost()
        scene.update(host, 0.016)
        self.assertIsInstance(host.last_scene, EndScene)
        end = host.last_scene
        assert isinstance(end, EndScene)
        self.assertTrue(end.won)

    def test_chart_briefing_launches_upcoming_level_on_enter(self) -> None:
        from gravity_ho_matey.scenes.game_flow import start_chart_briefing, start_play
        from gravity_ho_matey.scenes.level_intro import LevelIntroScene

        briefing = start_chart_briefing(
            "solar",
            cleared_level_id="cove",
            elapsed=42.0,
        )
        host = _FakeHost()
        briefing.on_key_press(host, "Return")
        self.assertIsInstance(host.last_scene, LevelIntroScene)
        intro = host.last_scene
        assert isinstance(intro, LevelIntroScene)
        self.assertEqual(intro.level_id, "solar")
        self.assertIsNot(host.last_scene, start_play("cove", CampaignState.new()))


if __name__ == "__main__":
    unittest.main()
