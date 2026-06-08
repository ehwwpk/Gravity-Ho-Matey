"""Hostile audit — asteroid breakup spawn, velocity, and integration invariants."""

from __future__ import annotations

import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_combat import apply_projectile_hit
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.entities import FinishGate, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.level_registry import build_level


def _break(parent, *, vel: Vec2 = Vec2(), free_bounds: bool = False):
    parent.vel = vel
    parent.free_bounds = free_bounds
    parent_pos = Vec2(parent.pos.x, parent.pos.y)
    while parent.hits_remaining > 1:
        apply_projectile_hit(parent, parent_pos, Vec2(400, 0), world_asteroid_count=1)
    result = apply_projectile_hit(parent, parent_pos, Vec2(400, 0), world_asteroid_count=1)
    return parent_pos, result


class AsteroidBreakupAuditTests(unittest.TestCase):
    def test_stagnant_medium_spawn_tight_and_fast_burst(self) -> None:
        parent = make_asteroid(Vec2(500, 500), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        parent_pos, result = _break(parent)
        radius = 51.5  # known for this seed
        self.assertGreaterEqual(len(result.asteroids_added), 2)
        for child in result.asteroids_added:
            self.assertFalse(child.free_bounds)
            self.assertIsNone(child.ring_anchor)
            spawn_dist = (child.pos - parent_pos).length()
            self.assertLessEqual(spawn_dist, radius * 0.08 + 0.01)
            burst = (child.vel - parent.vel).length()
            self.assertGreaterEqual(burst, 50.0)
            self.assertLessEqual(burst, 110.0)

    def test_free_bounds_parent_children_move_via_full_update(self) -> None:
        parent = make_asteroid(Vec2(500, 500), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        parent.free_bounds = True
        world = GameWorld(
            config=WorldConfig(width=2000, height=2000, open_bounds=True),
            ship=Ship(pos=Vec2(400, 500)),
            asteroids=[parent],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1900, 1900, 40, 40)),
        )
        parent_pos = Vec2(parent.pos.x, parent.pos.y)
        for _ in range(parent.hits_max):
            world.projectiles = [Projectile(pos=Vec2(450, 500), vel=Vec2(500, 0))]
            world.update(1 / 60, ControlIntent())
        self.assertGreater(len(world.asteroids), 1)
        for child in world.asteroids:
            self.assertFalse(child.free_bounds)
            self.assertGreater((child.pos - parent_pos).length(), 1.0)

    def test_fragments_keep_separating_over_30_frames(self) -> None:
        parent = make_asteroid(Vec2(800, 800), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        world = GameWorld(
            config=WorldConfig(width=2000, height=2000),
            ship=Ship(pos=Vec2(700, 800)),
            asteroids=[parent],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1900, 1900, 40, 40)),
        )
        parent_pos = Vec2(parent.pos.x, parent.pos.y)
        for _ in range(parent.hits_max):
            world.projectiles = [Projectile(pos=Vec2(750, 800), vel=Vec2(500, 0))]
            world.update(1 / 60, ControlIntent())
        dists_after_break = [(c.pos - parent_pos).length() for c in world.asteroids]
        for _ in range(30):
            world.update(1 / 60, ControlIntent())
        dists_after_30 = [(c.pos - parent_pos).length() for c in world.asteroids]
        self.assertGreater(max(dists_after_30), max(dists_after_break) + 15.0)

    def test_nova_explosive_breakup_moves_fragments(self) -> None:
        parent = make_asteroid(Vec2(500, 500), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        world = GameWorld(
            config=WorldConfig(width=2000, height=2000),
            ship=Ship(pos=Vec2(400, 500)),
            asteroids=[parent],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1900, 1900, 40, 40)),
        )
        parent_pos = Vec2(parent.pos.x, parent.pos.y)
        while parent.hits_remaining > 1:
            world.projectiles = [
                Projectile(
                    pos=Vec2(500, 500),
                    vel=Vec2(200, 0),
                    weapon_track=WeaponTrack.LASER,
                )
            ]
            world.update(1 / 60, ControlIntent())
        world.projectiles = [
            Projectile(
                pos=Vec2(500, 500),
                vel=Vec2(200, 0),
                weapon_track=WeaponTrack.EXPLOSIVE,
                explosive_radius=80.0,
            )
        ]
        world.update(1 / 60, ControlIntent())
        self.assertGreater(len(world.asteroids), 1)
        for child in world.asteroids:
            self.assertGreater((child.pos - parent_pos).length(), 0.5)
            self.assertGreater(child.vel.length(), 10.0)

    def test_ring_parent_breakup_clears_orbit(self) -> None:
        parent = make_asteroid(Vec2(1000, 1000), seed=401001, size_class="rock", drift_kind="ring", velocity=Vec2(40, 0))
        parent.ring_anchor = Vec2(1000, 1000)
        parent.ring_radius = 300.0
        parent.ring_orbit_radius = 300.0
        parent_pos, result = _break(parent)
        self.assertGreater(len(result.asteroids_added), 0)
        for child in result.asteroids_added:
            self.assertIsNone(child.ring_anchor)
            self.assertEqual(child.drift_kind, "medium")
            self.assertGreater((child.vel - parent.vel).length(), 50.0)
            self.assertLessEqual((child.pos - parent_pos).length(), parent.approximate_radius() * 0.08 + 0.01)

    def test_rim_rock_fragments_stay_near_parent_on_break(self) -> None:
        parent = make_asteroid(Vec2(-140, 400), seed=921, size_class="rock", drift_kind="slow", velocity=Vec2())
        parent.free_bounds = True
        world = GameWorld(
            config=WorldConfig(width=2000, height=2000, open_bounds=True),
            ship=Ship(pos=Vec2(400, 500)),
            asteroids=[parent],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1900, 1900, 40, 40)),
        )
        parent_pos = Vec2(parent.pos.x, parent.pos.y)
        radius = parent.approximate_radius()
        for _ in range(parent.hits_max + 2):
            world.projectiles = [Projectile(pos=parent_pos + Vec2(-40, 0), vel=Vec2(600, 0))]
            world.update(1 / 60, ControlIntent())
            if not any(a.generation == 0 and a.seed == parent.seed for a in world.asteroids):
                break
        for child in world.asteroids:
            dist = (child.pos - parent_pos).length()
            self.assertLessEqual(dist, radius * 0.08 + 6.0, f"rim shard teleported {dist:.0f}u from parent")

    def test_cove_authored_medium_breaks_in_play(self) -> None:
        world = build_level("cove")
        medium = next(a for a in world.asteroids if a.seed == 102)
        self.assertEqual(medium.tier, AsteroidTier.MEDIUM)
        parent_pos = Vec2(medium.pos.x, medium.pos.y)
        world.ship.pos = medium.pos + Vec2(-80, 0)
        for _ in range(medium.hits_max + 2):
            if not any(a.seed == 102 for a in world.asteroids):
                break
            world.projectiles = [Projectile(pos=medium.pos + Vec2(-40, 0), vel=Vec2(600, 0))]
            world.update(1 / 60, ControlIntent())
        children = [a for a in world.asteroids if a.generation == 1]
        self.assertGreaterEqual(len(children), 2)
        for child in children:
            self.assertFalse(child.free_bounds)
            self.assertGreater((child.pos - parent_pos).length(), 0.5)


if __name__ == "__main__":
    unittest.main()
