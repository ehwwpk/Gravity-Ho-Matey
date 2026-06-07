import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.boost_pad import BoostPad, try_trigger_pad
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.levels.membrane_escorts import membrane_friendly_fighters
from gravity_ho_matey.levels.membrane_layout import build_membrane_layout


def _rift_world(**kwargs) -> GameWorld:
    base = build_level("rift")
    return GameWorld(
        config=base.config,
        ship=kwargs.get("ship", Ship(pos=Vec2(base.ship.pos.x, base.ship.pos.y))),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=base.finish_gate,
        enemies=kwargs.get("enemies", []),
        allies=kwargs.get("allies", []),
        membrane_layout=base.membrane_layout,
        boost_pads=[],
        mega_squid=None,
    )


class FriendlyFighterTests(unittest.TestCase):
    def test_rift_spawns_two_allies(self) -> None:
        world = build_level("rift")
        self.assertEqual(len(world.allies), 2)
        self.assertTrue(all(a.alive for a in world.allies))

    def test_membrane_escorts_flank_spawn(self) -> None:
        layout = build_membrane_layout()
        allies = membrane_friendly_fighters(layout)
        self.assertEqual({a.wing_id for a in allies}, {0, 1})
        spawn = layout.spawn_ship.pos
        for ally in allies:
            self.assertLess((ally.pos - spawn).length(), 180.0)

    def test_ally_fires_on_nearby_squid(self) -> None:
        squid = SquidEnemy(pos=Vec2(300.0, 300.0))
        ally = FriendlyFighter(wing_id=0, pos=Vec2(120.0, 300.0), fire_cooldown=0.0)
        world = _rift_world(enemies=[squid], allies=[ally])
        world.update(0.016, ControlIntent())
        ally_shots = [p for p in world.projectiles if p.from_ally]
        self.assertGreaterEqual(len(ally_shots), 1)

    def test_player_shots_do_not_hit_allies(self) -> None:
        ally = FriendlyFighter(wing_id=0, pos=Vec2(200.0, 200.0))
        world = _rift_world(allies=[ally])
        world.projectiles.append(
            Projectile(pos=Vec2(200.0, 200.0), vel=Vec2(), hostile=False, from_ally=False)
        )
        world._update_projectiles(0.016)
        self.assertTrue(ally.alive)
        self.assertEqual(ally.hits_remaining, 2)

    def test_ally_shots_damage_squids_without_loot(self) -> None:
        squid = SquidEnemy(pos=Vec2(200.0, 200.0))
        world = _rift_world(enemies=[squid])
        world.projectiles.append(
            Projectile(pos=Vec2(200.0, 200.0), vel=Vec2(), hostile=False, from_ally=True)
        )
        world._update_projectiles(0.016)
        self.assertEqual(squid.hits_remaining, 2)
        self.assertEqual(len(world.jewels), 0)

    def test_ally_follows_player_forward(self) -> None:
        layout = build_membrane_layout()
        ally = membrane_friendly_fighters(layout)[0]
        start = Vec2(ally.pos.x, ally.pos.y)
        world = _rift_world(allies=[ally])
        world.ship.pos = Vec2(1000.0, 3000.0)
        world.ship.vel = Vec2(0.0, -220.0)
        world.ship.angle = -1.5707963267948966
        for _ in range(120):
            world.update(0.05, ControlIntent())
        self.assertGreater((ally.pos - start).length(), 40.0)

    def test_squid_ram_can_destroy_ally(self) -> None:
        squid = SquidEnemy(pos=Vec2(100.0, 100.0))
        ally = FriendlyFighter(wing_id=0, pos=Vec2(100.0, 100.0))
        world = _rift_world(enemies=[squid], allies=[ally])
        world._check_ally_hazards()
        self.assertFalse(ally.alive)
        self.assertFalse(squid.alive)

    def test_other_levels_have_no_allies(self) -> None:
        for level_id in ("cove", "solar", "drift"):
            world = build_level(level_id)
            self.assertEqual(len(world.allies), 0)

    def test_ally_triggers_boost_pad_on_ribbon(self) -> None:
        layout = build_membrane_layout()
        pad_spec = layout.boost_pads[0]
        ally = FriendlyFighter(wing_id=0, pos=Vec2(pad_spec.pos.x, pad_spec.pos.y))
        pads = [
            BoostPad(
                pos=Vec2(pad_spec.pos.x, pad_spec.pos.y),
                tangent=Vec2(pad_spec.tangent.x, pad_spec.tangent.y),
                radius=pad_spec.radius,
                kick_speed=pad_spec.kick_speed,
            )
        ]
        before = ally.vel.length()
        triggered = try_trigger_pad(pads, ally, layout, pad_flash_seconds=0.4)
        self.assertTrue(triggered)
        self.assertGreater(ally.vel.length(), before)
        self.assertGreater(ally.boost_flash, 0.0)

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

    def test_rift_render_with_allies(self) -> None:
        import tkinter as tk

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        root = tk.Tk()
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
