from __future__ import annotations

import math
import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import FinishGate, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.upgrade_config import RAPID_FIRE_COOLDOWN_MULT
from gravity_ho_matey.gameplay.weapon_config import (
    EXPLOSIVE_ADV_BLAST_RADIUS,
    EXPLOSIVE_ADV_COOLDOWN_MULT,
    EXPLOSIVE_ADV_SPEED_MULT,
    EXPLOSIVE_BLAST_RADIUS,
    EXPLOSIVE_COOLDOWN_MULT,
    EXPLOSIVE_SPEED_MULT,
    LASER_ADV_PIERCE_COUNT,
    LASER_PIERCE_COUNT,
    PLAYER_WEAPON_HEAT_GAIN_MULT,
    SHOTGUN_ADV_PELLET_COUNT,
    SHOTGUN_ADV_SIDE_SPREAD_RAD,
    SHOTGUN_PELLET_COUNT,
    WEAPON_ADVANCED_PRICE,
    WEAPON_DOCTRINE_PRICE,
)
from gravity_ho_matey.gameplay.weapon_fire import player_fire_cooldown, spawn_player_shots
from gravity_ho_matey.gameplay.weapon_heat import (
    apply_heat_on_fire,
    heat_escalation_multiplier,
    heat_per_shot,
    player_heat_decay_rate,
    player_heat_fire_cooldown_multiplier,
    player_weapon_overheated,
    reset_player_weapon_heat,
    tick_player_weapon_heat,
)
from gravity_ho_matey.gameplay.weapon_combat import resolve_projectile_after_hit
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
from gravity_ho_matey.gameplay.explosions import ExplosionKind
from gravity_ho_matey.gameplay.world import GameWorld


class WeaponTrackShopTests(unittest.TestCase):
    def test_weapon_doctrine_mutually_exclusive(self) -> None:
        campaign = CampaignState()
        campaign.jewels = 999
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_LASER))
        self.assertEqual(campaign.weapon_track, WeaponTrack.LASER)
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_SHOTGUN))
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_EXPLOSIVE))
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_LASER))

    def test_weapon_advanced_requires_doctrine(self) -> None:
        campaign = CampaignState()
        campaign.jewels = 999
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_ADV_SHOTGUN))
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_SHOTGUN))
        self.assertTrue(campaign.can_purchase(PowerUpKind.WEAPON_ADV_SHOTGUN))
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_ADV_LASER))
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_ADV_SHOTGUN))
        self.assertTrue(campaign.weapon_advanced)
        self.assertFalse(campaign.can_purchase(PowerUpKind.WEAPON_ADV_SHOTGUN))

    def test_weapon_advanced_price(self) -> None:
        campaign = CampaignState()
        campaign.jewels = WEAPON_DOCTRINE_PRICE + WEAPON_ADVANCED_PRICE
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_EXPLOSIVE))
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_ADV_EXPLOSIVE))
        self.assertEqual(campaign.jewels, 0)

    def test_weapon_doctrine_price(self) -> None:
        campaign = CampaignState()
        campaign.jewels = WEAPON_DOCTRINE_PRICE
        self.assertTrue(campaign.try_purchase(PowerUpKind.WEAPON_SHOTGUN))
        self.assertEqual(campaign.jewels, 0)


class RapidFireOneTimeTests(unittest.TestCase):
    def test_rapid_fire_one_purchase_only(self) -> None:
        campaign = CampaignState()
        campaign.jewels = 999
        ship = Ship(pos=Vec2(0, 0))
        self.assertTrue(campaign.try_purchase(PowerUpKind.RAPID_FIRE, ship))
        self.assertFalse(campaign.can_purchase(PowerUpKind.RAPID_FIRE))
        self.assertAlmostEqual(ship.fire_cooldown_multiplier, RAPID_FIRE_COOLDOWN_MULT)


class WeaponFireTests(unittest.TestCase):
    def test_shotgun_spawns_two_projectiles(self) -> None:
        shots = spawn_player_shots(
            ship_pos=Vec2(100, 100),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.SHOTGUN,
        )
        self.assertEqual(len(shots), SHOTGUN_PELLET_COUNT)
        angles = sorted(math.atan2(s.vel.y, s.vel.x) for s in shots)
        self.assertGreater(angles[1] - angles[0], 0.01)

    def test_shotgun_advanced_spawns_three_with_center_shot(self) -> None:
        shots = spawn_player_shots(
            ship_pos=Vec2(100, 100),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.SHOTGUN,
            advanced=True,
        )
        self.assertEqual(len(shots), SHOTGUN_ADV_PELLET_COUNT)
        angles = sorted(math.atan2(s.vel.y, s.vel.x) for s in shots)
        self.assertAlmostEqual(angles[1], 0.0, places=4)
        self.assertAlmostEqual(angles[0], -SHOTGUN_ADV_SIDE_SPREAD_RAD, places=4)
        self.assertAlmostEqual(angles[2], SHOTGUN_ADV_SIDE_SPREAD_RAD, places=4)

    def test_laser_advanced_more_pierce(self) -> None:
        base = spawn_player_shots(
            ship_pos=Vec2(0, 0),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.LASER,
            advanced=False,
        )
        adv = spawn_player_shots(
            ship_pos=Vec2(0, 0),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.LASER,
            advanced=True,
        )
        self.assertEqual(base[0].pierce_remaining, LASER_PIERCE_COUNT)
        self.assertEqual(adv[0].pierce_remaining, LASER_ADV_PIERCE_COUNT)
        self.assertGreater(adv[0].vel.length(), base[0].vel.length())

    def test_explosive_advanced_faster_and_larger_blast(self) -> None:
        base = spawn_player_shots(
            ship_pos=Vec2(0, 0),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.EXPLOSIVE,
            advanced=False,
        )
        adv = spawn_player_shots(
            ship_pos=Vec2(0, 0),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.EXPLOSIVE,
            advanced=True,
        )
        self.assertEqual(base[0].explosive_radius, EXPLOSIVE_BLAST_RADIUS)
        self.assertEqual(adv[0].explosive_radius, EXPLOSIVE_ADV_BLAST_RADIUS)
        self.assertGreater(adv[0].vel.length(), base[0].vel.length())
        base_cd = player_fire_cooldown(0.18, 1.0, WeaponTrack.EXPLOSIVE, advanced=False)
        adv_cd = player_fire_cooldown(0.18, 1.0, WeaponTrack.EXPLOSIVE, advanced=True)
        self.assertLess(adv_cd, base_cd)
        self.assertAlmostEqual(adv_cd / base_cd, EXPLOSIVE_ADV_COOLDOWN_MULT / EXPLOSIVE_COOLDOWN_MULT, places=4)

    def test_laser_has_pierce(self) -> None:
        shots = spawn_player_shots(
            ship_pos=Vec2(0, 0),
            ship_vel=Vec2(),
            ship_angle=0.0,
            ship_radius=12.0,
            projectile_speed=300.0,
            track=WeaponTrack.LASER,
        )
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0].pierce_remaining, LASER_PIERCE_COUNT)

    def test_explosive_slower_cooldown(self) -> None:
        base = 0.18
        std = player_fire_cooldown(base, 1.0, None)
        slow = player_fire_cooldown(base, 1.0, WeaponTrack.EXPLOSIVE)
        self.assertGreater(slow, std)
        self.assertAlmostEqual(slow, base * EXPLOSIVE_COOLDOWN_MULT)


class WeaponCombatTests(unittest.TestCase):
    def test_laser_pierces_second_enemy(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=800, height=600),
            ship=Ship(pos=Vec2(100, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(0, 0, 10, 10)),
            enemies=[
                PatrolEnemy(waypoints=(Vec2(200, 100),), pos=Vec2(200, 100)),
                PatrolEnemy(waypoints=(Vec2(240, 100),), pos=Vec2(240, 100)),
            ],
        )
        projectile = Projectile(
            pos=Vec2(195, 100),
            vel=Vec2(200, 0),
            pierce_remaining=1,
            weapon_track=WeaponTrack.LASER,
        )
        disposition = world._projectile_hits_enemy(projectile)
        self.assertEqual(disposition, "pierce")
        self.assertEqual(projectile.pierce_remaining, 0)
        self.assertEqual(len(world.enemies), 1)

        projectile.pos = Vec2(235, 100)
        disposition = world._projectile_hits_enemy(projectile)
        self.assertEqual(disposition, "consume")
        self.assertEqual(len(world.enemies), 0)

    def test_explosive_hits_multiple_enemies(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=800, height=600),
            ship=Ship(pos=Vec2(100, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(0, 0, 10, 10)),
            enemies=[
                PatrolEnemy(waypoints=(Vec2(200, 100),), pos=Vec2(200, 100)),
                PatrolEnemy(waypoints=(Vec2(220, 130),), pos=Vec2(220, 130)),
            ],
        )
        projectile = Projectile(
            pos=Vec2(200, 110),
            vel=Vec2(50, 0),
            explosive_radius=EXPLOSIVE_BLAST_RADIUS,
            weapon_track=WeaponTrack.EXPLOSIVE,
        )
        disposition = world._projectile_hits_enemy(projectile)
        self.assertEqual(disposition, "consume")
        self.assertEqual(len(world.enemies), 0)
        kinds = {fx.kind for fx in world.explosions.active}
        self.assertIn(ExplosionKind.NOVA_BLAST, kinds)

    def test_resolve_pierce_vs_consume(self) -> None:
        laser = Projectile(pos=Vec2(), vel=Vec2(), pierce_remaining=2)
        self.assertEqual(resolve_projectile_after_hit(laser, hit=True), "pierce")
        self.assertEqual(laser.pierce_remaining, 1)
        explosive = Projectile(pos=Vec2(), vel=Vec2(), explosive_radius=40.0)
        self.assertEqual(resolve_projectile_after_hit(explosive, hit=True), "consume")


class PlayerWeaponHeatTests(unittest.TestCase):
    def test_heat_builds_and_soft_throttles_cooldown(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        apply_heat_on_fire(ship, None)
        self.assertGreater(ship.weapon_heat, 0.0)
        self.assertLess(player_heat_fire_cooldown_multiplier(0.0), player_heat_fire_cooldown_multiplier(0.75))
        self.assertGreaterEqual(player_heat_fire_cooldown_multiplier(0.82), 6.5)
        self.assertGreaterEqual(player_heat_fire_cooldown_multiplier(0.88), 8.8)

    def test_escalation_climbs_while_already_hot(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        ship.weapon_heat = 0.72
        before = ship.weapon_heat
        apply_heat_on_fire(ship, None)
        low_gain = ship.weapon_heat - before
        ship.weapon_heat = 0.72
        escalation = heat_escalation_multiplier(0.72)
        self.assertGreater(escalation, 1.15)
        self.assertAlmostEqual(
            low_gain,
            heat_per_shot(None) * escalation * PLAYER_WEAPON_HEAT_GAIN_MULT,
            places=5,
        )

    def test_high_heat_cools_faster_than_moderate_heat(self) -> None:
        hot = Ship(pos=Vec2(0, 0))
        warm = Ship(pos=Vec2(0, 0))
        hot.weapon_heat = 0.90
        warm.weapon_heat = 0.70
        self.assertGreater(player_heat_decay_rate(0.90), player_heat_decay_rate(0.70))
        tick_player_weapon_heat(hot, 0.25, trigger_held=False)
        tick_player_weapon_heat(warm, 0.25, trigger_held=False)
        self.assertGreater(0.90 - hot.weapon_heat, 0.70 - warm.weapon_heat)

    def test_overheat_lockout_and_recovery(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        ship.weapon_heat = 1.0
        apply_heat_on_fire(ship, None)
        self.assertTrue(player_weapon_overheated(ship))
        tick_player_weapon_heat(ship, 10.0, trigger_held=False)
        self.assertFalse(player_weapon_overheated(ship))
        self.assertAlmostEqual(ship.weapon_heat, 0.0)

    def test_heat_decays_when_idle(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        ship.weapon_heat = 0.6
        tick_player_weapon_heat(ship, 0.5, trigger_held=False)
        self.assertLess(ship.weapon_heat, 0.6)

    def test_sustained_hold_reaches_high_heat_over_seconds(self) -> None:
        from gravity_ho_matey.core.vector import Vec2
        from gravity_ho_matey.gameplay.weapon_heat import player_heat_fire_cooldown_multiplier

        ship = Ship(pos=Vec2(0, 0))
        t = 0.0
        cooldown = 0.0
        dt = 0.016
        marks: dict[float, float] = {}
        while t < 4.0 and ship.weapon_overheat_timer <= 0.0:
            tick_player_weapon_heat(ship, dt, trigger_held=True)
            cooldown = max(0.0, cooldown - dt)
            if cooldown <= 0.0 and ship.weapon_overheat_timer <= 0.0:
                apply_heat_on_fire(ship, None)
                cooldown = 0.18 * player_heat_fire_cooldown_multiplier(ship.weapon_heat)
            for mark in (1.0, 1.5, 3.0):
                if abs(t - mark) < dt:
                    marks[mark] = ship.weapon_heat
            t += dt
        self.assertGreater(marks.get(1.0, 0.0), 0.14)
        self.assertLess(marks.get(1.0, 1.0), 0.24)
        self.assertGreaterEqual(marks.get(1.5, 0.0), 0.20)
        self.assertLessEqual(marks.get(1.5, 0.0), 0.35)
        self.assertGreater(marks.get(3.0, 0.0), 0.42)
        self.assertLess(marks.get(3.0, 1.0), 0.62)

    def test_trigger_held_prevents_decay_between_slow_shots(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        ship.weapon_heat = 0.55
        tick_player_weapon_heat(ship, 0.35, trigger_held=True)
        self.assertGreater(ship.weapon_heat, 0.55)

    def test_shotgun_builds_more_heat_than_laser(self) -> None:
        laser = heat_per_shot(WeaponTrack.LASER)
        shotgun = heat_per_shot(WeaponTrack.SHOTGUN)
        self.assertGreater(shotgun, laser)

    def test_world_blocks_fire_while_overheated(self) -> None:
        from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld

        world = GameWorld(
            config=WorldConfig(width=800, height=600),
            ship=Ship(pos=Vec2(100, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(0, 0, 10, 10)),
        )
        world.ship.weapon_overheat_timer = 1.0
        world.ship.cooldown = 0.0
        before = len(world.projectiles)
        world._update_ship(0.016, ControlIntent(fire=True))
        self.assertEqual(len(world.projectiles), before)

    def test_reset_clears_weapon_heat(self) -> None:
        ship = Ship(pos=Vec2(0, 0))
        ship.weapon_heat = 0.8
        ship.weapon_overheat_timer = 1.2
        reset_player_weapon_heat(ship)
        self.assertAlmostEqual(ship.weapon_heat, 0.0)
        self.assertAlmostEqual(ship.weapon_overheat_timer, 0.0)


if __name__ == "__main__":
    unittest.main()
