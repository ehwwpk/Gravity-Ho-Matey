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
    EXPLOSIVE_BLAST_RADIUS,
    EXPLOSIVE_COOLDOWN_MULT,
    LASER_PIERCE_COUNT,
    SHOTGUN_PELLET_COUNT,
    WEAPON_DOCTRINE_PRICE,
)
from gravity_ho_matey.gameplay.weapon_fire import player_fire_cooldown, spawn_player_shots
from gravity_ho_matey.gameplay.weapon_combat import resolve_projectile_after_hit
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
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

    def test_resolve_pierce_vs_consume(self) -> None:
        laser = Projectile(pos=Vec2(), vel=Vec2(), pierce_remaining=2)
        self.assertEqual(resolve_projectile_after_hit(laser, hit=True), "pierce")
        self.assertEqual(laser.pierce_remaining, 1)
        explosive = Projectile(pos=Vec2(), vel=Vec2(), explosive_radius=40.0)
        self.assertEqual(resolve_projectile_after_hit(explosive, hit=True), "consume")


if __name__ == "__main__":
    unittest.main()
