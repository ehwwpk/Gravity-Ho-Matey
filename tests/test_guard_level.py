import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GameStatus, Projectile
from gravity_ho_matey.gameplay.space_station import STATION_HITS_MAX
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.guard_layout import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    BOSS_SPAWN,
    BOSS_SPAWN_RELAY_OFFSET,
    EXTRACT_PAD_CENTER,
    PLAYER_SPAWN,
    STATION_RELAY,
)
from gravity_ho_matey.levels.level_registry import build_level, next_level_id


class GuardLevelTests(unittest.TestCase):
    def test_registry_chain_includes_rift(self) -> None:
        self.assertEqual(next_level_id("drift"), "rift")
        self.assertEqual(next_level_id("rift"), "siege")

    def test_rift_world_content(self) -> None:
        world = build_level("rift")
        self.assertEqual(world.config.level_theme, "rift")
        self.assertEqual(world.config.level_name, "Relay Hold")
        self.assertTrue(world.config.protection_mission)
        self.assertEqual(world.config.width, ARENA_WIDTH)
        self.assertEqual(world.config.height, ARENA_HEIGHT)
        self.assertEqual(len(world.friendly_stations), 1)
        self.assertEqual(world.friendly_stations[0].station_label, "RELAY")
        dist = (world.ship.pos - STATION_RELAY).length()
        self.assertLess(dist, 200.0)
        self.assertEqual(len(world.enemies), 0)
        self.assertIsNone(world.mega_squid)
        self.assertIsNotNone(world.wave_director)
        self.assertIsNotNone(world.guard_layout)
        self.assertGreaterEqual(len(world.asteroids), 12)
        self.assertEqual(len(world.wells), 3)

    def test_wave_one_spawns_at_start(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        self.assertEqual(world.wave_director.waves_spawned, 1)
        self.assertEqual(len(world.enemies), 4)

    def test_wave_three_spawns_boss(self) -> None:
        world = build_level("rift")
        world.elapsed = 40.0
        world._tick_wave_director(0.016)
        self.assertEqual(world.wave_director.waves_spawned, 3)
        self.assertIsNotNone(world.mega_squid)
        assert world.mega_squid is not None
        self.assertGreater(world.mega_squid.vel.length(), 0.0)
        self.assertEqual(world.wave_director.nudge_wave, 3)
        self.assertGreater(len(world.enemies), 4)

    def test_wave_one_does_not_nudge(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        self.assertEqual(world.wave_director.waves_spawned, 1)
        self.assertEqual(world.wave_director.nudge_wave, 0)

    def test_station_loss_fails_mission(self) -> None:
        world = build_level("rift")
        station = world.friendly_stations[0]
        station.hits_remaining = 1
        world.projectiles.append(
            Projectile(
                pos=Vec2(station.pos.x, station.pos.y),
                vel=Vec2(),
                hostile=True,
                radius=8.0,
            )
        )
        world._update_projectiles(0.016)
        self.assertFalse(station.alive)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertIn("Relay", world.last_damage.reason if world.last_damage else "")

    def test_boss_spawn_tight_on_relay(self) -> None:
        self.assertAlmostEqual(BOSS_SPAWN.x, STATION_RELAY.x)
        self.assertLess(BOSS_SPAWN_RELAY_OFFSET, 180.0)
        self.assertGreater(BOSS_SPAWN.y, STATION_RELAY.y)
        self.assertLess(BOSS_SPAWN.y, PLAYER_SPAWN.y + 24.0)

    def test_extract_gate_at_south_pad(self) -> None:
        world = build_level("rift")
        gate = world.finish_gate.rect
        self.assertAlmostEqual(gate.x + gate.w * 0.5, EXTRACT_PAD_CENTER.x, delta=2.0)
        self.assertAlmostEqual(gate.y + gate.h * 0.5, EXTRACT_PAD_CENTER.y, delta=2.0)
        self.assertGreater(EXTRACT_PAD_CENTER.y, PLAYER_SPAWN.y)

    def test_protection_combat_clear_unlocks_extract_not_win(self) -> None:
        world = build_level("rift")
        world.wave_director.waves_spawned = 3
        world.boss_cleared = True
        if world.mega_squid is not None:
            world.mega_squid.alive = False
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        self.assertTrue(world.protection_combat_cleared)
        self.assertTrue(world.finish_unlocked)
        self.assertEqual(world.status, GameStatus.RUNNING)

    def test_protection_win_requires_extract_pad(self) -> None:
        world = build_level("rift")
        world.wave_director.waves_spawned = 3
        world.boss_cleared = True
        if world.mega_squid is not None:
            world.mega_squid.alive = False
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        gate = world.finish_gate.rect
        world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        world._check_finish()
        self.assertEqual(world.status, GameStatus.WON)

    def test_protection_requires_boss_cleared(self) -> None:
        world = build_level("rift")
        world.wave_director.waves_spawned = 3
        world.boss_cleared = False
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        self.assertFalse(world.protection_combat_cleared)

    def test_relay_does_not_shoot_boss(self) -> None:
        from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
        from gravity_ho_matey.levels.guard_layout import build_guard_layout

        layout = build_guard_layout()
        station = build_level("rift").friendly_stations[0]
        boss = MegaSquidBoss(pos=BOSS_SPAWN, anchor=layout.station_anchor)
        picked = station._pick_friendly_gun_target([], boss, prioritize_boss=False)
        self.assertIsNone(picked)

    def test_protection_win_requires_all_waves_cleared(self) -> None:
        world = build_level("rift")
        world.wave_director.waves_spawned = 3
        world.boss_cleared = True
        for enemy in world.enemies:
            enemy.alive = False
        world._prune_dead_enemies()
        self.assertTrue(world.protection_combat_cleared)

    def test_friendly_station_spawns_fighter(self) -> None:
        world = build_level("rift")
        station = world.friendly_stations[0]
        station.spawn_timer = station.spawn_interval
        spawned = station.tick_friendly_spawns(0.05, 0)
        self.assertIsNotNone(spawned)
        assert spawned is not None
        self.assertGreaterEqual(spawned.wing_id, 100)


class RiftPlayLoopTests(unittest.TestCase):
    def test_rift_update_fire_and_chase_draw_survives(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.camera import CameraMode
        from gravity_ho_matey.scenes.launch_countdown import LaunchCountdownScene
        from gravity_ho_matey.util.input import InputState

        class Host:
            input_state = InputState()

            def __init__(self) -> None:
                self.root = tk.Tk()
                self.root.withdraw()
                from gravity_ho_matey.render.tk_renderer import TkRenderer

                self.renderer = TkRenderer(tk.Canvas(self.root, width=960, height=640))

            def set_scene(self, scene) -> None:
                self.scene = scene
                scene.on_enter(self)

        host = Host()
        try:
            countdown = LaunchCountdownScene("rift", CampaignState.new())
            countdown.on_enter(host)
            countdown.on_key_press(host, "space")
            play = host.scene
            for frame in range(120):
                host.input_state.pressed.clear()
                if frame >= 2:
                    host.input_state.pressed.add("space")
                play.update(host, 1 / 60.0)
                if frame == 8:
                    play.camera.cycle_mode()
                    self.assertIs(play.camera.mode, CameraMode.CHASE)
                play.draw(host)
            self.assertEqual(play.world.wave_director.waves_spawned, 1)
            self.assertGreaterEqual(len(play.world.enemies), 4)
        finally:
            host.root.destroy()


class GuardStationCombatTests(unittest.TestCase):
    def test_hostile_shot_damages_friendly_station(self) -> None:
        world = build_level("rift")
        station = world.friendly_stations[0]
        before = station.hits_remaining
        world.projectiles.append(
            Projectile(
                pos=Vec2(station.pos.x, station.pos.y),
                vel=Vec2(),
                hostile=True,
                radius=6.0,
            )
        )
        world._update_projectiles(0.016)
        self.assertEqual(station.hits_remaining, before - 1)

    def test_stations_start_at_full_hp(self) -> None:
        world = build_level("rift")
        for station in world.friendly_stations:
            self.assertEqual(station.hits_remaining, STATION_HITS_MAX)
            self.assertTrue(station.alive)
