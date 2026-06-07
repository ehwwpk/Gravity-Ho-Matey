import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.gameplay.friendly_fighter_config import (
    ALLY_ASTEROID_AVOID_RADIUS,
    ALLY_ENGAGE_RANGE,
    PATROL_ENGAGE_RANGE,
)
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.level_registry import build_level


def _ally_world(**kwargs) -> GameWorld:
    base = build_level("siege")
    return GameWorld(
        config=base.config,
        ship=kwargs.get("ship", Ship(pos=Vec2(base.ship.pos.x, base.ship.pos.y))),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(base.finish_gate.rect),
        enemies=kwargs.get("enemies", []),
        allies=kwargs.get("allies", []),
        mega_squid=None,
    )


class FriendlyFighterTests(unittest.TestCase):
    def test_siege_spawns_twelve_allies(self) -> None:
        world = build_level("siege")
        self.assertEqual(len(world.allies), 12)
        self.assertTrue(all(a.alive for a in world.allies))

    def test_rift_starts_without_field_allies(self) -> None:
        world = build_level("rift")
        self.assertEqual(len(world.allies), 0)

    def test_ally_fires_on_nearby_squid(self) -> None:
        squid = SquidEnemy(pos=Vec2(300.0, 300.0))
        ally = FriendlyFighter(wing_id=0, pos=Vec2(120.0, 300.0), fire_cooldown=0.0)
        world = _ally_world(enemies=[squid], allies=[ally])
        world.update(0.016, ControlIntent())
        ally_shots = [p for p in world.projectiles if p.from_ally]
        self.assertGreaterEqual(len(ally_shots), 1)

    def test_player_shots_do_not_hit_allies(self) -> None:
        ally = FriendlyFighter(wing_id=0, pos=Vec2(200.0, 200.0))
        world = _ally_world(allies=[ally])
        world.projectiles.append(
            Projectile(pos=Vec2(200.0, 200.0), vel=Vec2(), hostile=False, from_ally=False)
        )
        world._update_projectiles(0.016)
        self.assertTrue(ally.alive)
        self.assertEqual(ally.hits_remaining, 2)

    def test_ally_shots_damage_squids_without_loot(self) -> None:
        squid = SquidEnemy(pos=Vec2(200.0, 200.0))
        world = _ally_world(enemies=[squid])
        world.projectiles.append(
            Projectile(pos=Vec2(200.0, 200.0), vel=Vec2(), hostile=False, from_ally=True)
        )
        world._update_projectiles(0.016)
        self.assertEqual(squid.hits_remaining, 2)
        self.assertEqual(len(world.jewels), 0)

    def test_ally_follows_player_forward(self) -> None:
        ally = FriendlyFighter(wing_id=0, pos=Vec2(420.0, 1600.0))
        start = Vec2(ally.pos.x, ally.pos.y)
        world = _ally_world(allies=[ally])
        world.ship.pos = Vec2(1000.0, 1200.0)
        world.ship.vel = Vec2(220.0, 0.0)
        world.ship.angle = 0.0
        for _ in range(120):
            world.update(0.05, ControlIntent())
        self.assertGreater((ally.pos - start).length(), 40.0)

    def test_squid_ram_can_destroy_ally(self) -> None:
        squid = SquidEnemy(pos=Vec2(100.0, 100.0))
        ally = FriendlyFighter(wing_id=0, pos=Vec2(100.0, 100.0))
        world = _ally_world(enemies=[squid], allies=[ally])
        world._check_ally_hazards()
        self.assertFalse(ally.alive)
        self.assertFalse(squid.alive)

    def test_other_levels_have_no_allies(self) -> None:
        for level_id in ("cove", "solar", "drift"):
            world = build_level(level_id)
            self.assertEqual(len(world.allies), 0)

    def test_pick_threat_prioritizes_boss(self) -> None:
        ally = FriendlyFighter(wing_id=0, pos=Vec2(0.0, 0.0))
        squid = SquidEnemy(pos=Vec2(120.0, 0.0))
        boss = MegaSquidBoss(pos=Vec2(500.0, 0.0), anchor=Vec2(500.0, 0.0))
        threat = ally.pick_threat([squid], boss)
        self.assertIsNotNone(threat)
        assert threat is not None
        self.assertTrue(threat.is_boss)

    def test_pick_threat_prefers_squid_over_patrol(self) -> None:
        from gravity_ho_matey.gameplay.enemies import PatrolEnemy

        ally = FriendlyFighter(wing_id=0, pos=Vec2(0.0, 0.0))
        patrol = PatrolEnemy(waypoints=(Vec2(200.0, 0.0), Vec2(220.0, 0.0)))
        patrol.pos = Vec2(200.0, 0.0)
        squid = SquidEnemy(pos=Vec2(210.0, 0.0))
        threat = ally.pick_threat([patrol, squid], None)
        self.assertIsNotNone(threat)
        assert threat is not None
        self.assertAlmostEqual(threat.pos.x, 210.0)

    def test_pick_threat_engages_enemy_near_player(self) -> None:
        from gravity_ho_matey.gameplay.enemies import PatrolEnemy

        ally = FriendlyFighter(wing_id=0, pos=Vec2(0.0, 0.0))
        patrol = PatrolEnemy(waypoints=(Vec2(720.0, 0.0), Vec2(740.0, 0.0)))
        patrol.pos = Vec2(720.0, 0.0)
        threat = ally.pick_threat([patrol], None, player_pos=Vec2(660.0, 0.0))
        self.assertIsNotNone(threat)
        assert threat is not None
        self.assertAlmostEqual(threat.pos.x, 720.0)

    def test_default_engage_range_wider(self) -> None:
        ally = FriendlyFighter(wing_id=0, pos=Vec2(0.0, 0.0))
        self.assertEqual(ally.engage_range, ALLY_ENGAGE_RANGE)
        self.assertGreaterEqual(ALLY_ENGAGE_RANGE, 760.0)

    def test_ally_steers_away_from_approaching_asteroid(self) -> None:
        from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid

        ally = FriendlyFighter(wing_id=0, pos=Vec2(500.0, 500.0), angle=0.0)
        rock = make_asteroid(Vec2(640.0, 500.0), seed=3, size_class="rock")
        rock.vel = Vec2(-90.0, 0.0)
        start_gap = (rock.pos - ally.pos).length() - rock.approximate_radius() - ally.radius
        for _ in range(80):
            ally.integrate(
                0.05,
                player_pos=Vec2(380.0, 500.0),
                player_vel=Vec2(),
                player_angle=0.0,
                wells=[],
                gravity_scale=1.0,
                drag=0.98,
                well_maw_radius=10.0,
                threat=None,
                asteroids=[rock],
            )
            rock.pos = rock.pos + rock.vel * 0.05
        end_gap = (rock.pos - ally.pos).length() - rock.approximate_radius() - ally.radius
        self.assertGreater(end_gap, start_gap * 0.9)
        self.assertGreater(abs(ally.pos.y - 500.0), 12.0)
        self.assertLess((rock.pos - ally.pos).length(), ALLY_ASTEROID_AVOID_RADIUS + rock.approximate_radius() + 80.0)

    def test_patrol_default_engage_range_wider(self) -> None:
        from gravity_ho_matey.gameplay.enemies import PatrolEnemy

        enemy = PatrolEnemy(waypoints=(Vec2(0.0, 0.0), Vec2(10.0, 0.0)))
        self.assertEqual(enemy.engage_range, PATROL_ENGAGE_RANGE)
        self.assertGreaterEqual(PATROL_ENGAGE_RANGE, 560.0)

    def test_rift_render_with_stations(self) -> None:
        import tkinter as tk

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        try:
            scene = PlayScene("rift", CampaignState.new())
            canvas = tk.Canvas(root, width=960, height=640)
            renderer = TkRenderer(canvas)
            renderer.draw_world(
                scene.world,
                scene.campaign,
                scene.camera,
                scene.gravity_field,
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
