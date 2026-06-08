from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase, in_landing_zone
from gravity_ho_matey.gameplay.brood_moon_controller import apply_surface_layout, tick_brood_moon
from gravity_ho_matey.gameplay.entities import Beacon, GameStatus
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.brood_moon_layout import (
    LANDING_CHARGE_SECONDS,
    SEAL_TRAVEL_DISTANCE,
    build_brood_moon_orbital_layout,
)
from gravity_ho_matey.levels.level_registry import build_level, next_level_id


class BroodMoonLevelTests(unittest.TestCase):
    def test_registry_chain_includes_brood_moon(self) -> None:
        self.assertEqual(next_level_id("siege"), "brood_moon")
        self.assertIsNone(next_level_id("brood_moon"))

    def test_world_content(self) -> None:
        world = build_level("brood_moon")
        self.assertEqual(world.config.level_theme, "brood_moon")
        self.assertTrue(world.config.brood_moon_mission)
        self.assertIsNotNone(world.brood_moon)
        assert world.brood_moon is not None
        self.assertEqual(world.brood_moon.phase, BroodPhase.ORBITAL)
        self.assertGreaterEqual(len(world.wells), 1)
        self.assertGreaterEqual(len(world.asteroids), 8)

    def test_landing_window_and_surface_swap(self) -> None:
        world = build_level("brood_moon")
        layout = build_brood_moon_orbital_layout()
        toward_moon = layout.planet.center - world.ship.pos
        approach = layout.planet.center + toward_moon.normalized() * (layout.planet.surface_radius + 120.0)
        world.ship.pos = approach
        self.assertTrue(in_landing_zone(world.ship.pos, layout))

        bm = world.brood_moon
        assert bm is not None
        bm.landing_charge = LANDING_CHARGE_SECONDS
        rebake = tick_brood_moon(world, 0.016, interaction_hold=True)
        self.assertFalse(rebake)
        self.assertEqual(bm.phase, BroodPhase.LANDING_CINEMATIC)

        bm.cinematic_elapsed = bm.cinematic_seconds
        rebake = tick_brood_moon(world, 0.016, interaction_hold=False)
        self.assertTrue(rebake)
        self.assertEqual(bm.phase, BroodPhase.SURFACE)
        self.assertEqual(len(world.beacons), 3)
        self.assertEqual(len(world.egg_pods), 8)
        self.assertTrue(world.config.surface_wrap)

    def test_objectives_greenlight_at_six_pods_not_all_eight(self) -> None:
        from gravity_ho_matey.gameplay.brood_moon_mission import surface_objectives_met

        world = build_level("brood_moon")
        apply_surface_layout(world)
        for beacon in world.beacons:
            beacon.collected = True
        for i, pod in enumerate(world.egg_pods):
            pod.alive = i < 2  # six ruptured, two intact
        self.assertTrue(surface_objectives_met(world))

        for pod in world.egg_pods[:3]:
            pod.alive = True
        self.assertFalse(surface_objectives_met(world))

    def test_objectives_seal_and_dock_win(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        bm = world.brood_moon
        assert bm is not None

        for beacon in world.beacons:
            beacon.collected = True
        for pod in world.egg_pods:
            pod.alive = False

        tick_brood_moon(world, 0.05, interaction_hold=False)
        self.assertTrue(bm.objectives_complete)
        self.assertTrue(bm.boss_spawned)
        self.assertIsNotNone(world.mega_squid)

        bm.seal_travel = SEAL_TRAVEL_DISTANCE
        bm.seal_complete = True
        bm.ascent_ready = True
        from gravity_ho_matey.gameplay.brood_moon_mission import LIFTOFF_CHARGE_SECONDS

        bm.liftoff_charge = LIFTOFF_CHARGE_SECONDS
        tick_brood_moon(world, 0.05, interaction_hold=True)
        self.assertEqual(bm.phase, BroodPhase.ASCENT_CINEMATIC)

        bm.cinematic_elapsed = bm.cinematic_seconds
        tick_brood_moon(world, 0.05, interaction_hold=False)
        self.assertEqual(bm.phase, BroodPhase.ORBITAL_RETURN)
        self.assertTrue(world.finish_unlocked)

        gate = world.finish_gate.rect
        world.ship.pos = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        world.update(0.016, ControlIntent())
        self.assertEqual(world.status, GameStatus.WON)

    def test_liftoff_blocked_near_boss(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        bm = world.brood_moon
        assert bm is not None
        bm.objectives_complete = True
        bm.seal_complete = True
        bm.ascent_ready = True
        from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
        from gravity_ho_matey.levels.brood_moon_surface import boss_anchor

        anchor = boss_anchor()
        world.mega_squid = MegaSquidBoss(pos=anchor, anchor=anchor)
        world.ship.pos = anchor
        tick_brood_moon(world, 0.05, interaction_hold=True)
        self.assertEqual(bm.phase, BroodPhase.SURFACE)
        self.assertEqual(bm.liftoff_charge, 0.0)

    def test_egg_pod_jewel_drop_chance(self) -> None:
        from gravity_ho_matey.gameplay.jewel_drops import jewel_count_for_egg_pod, rng_at

        pos = Vec2(1200.0, 800.0)
        rng = rng_at(pos)
        drops = [jewel_count_for_egg_pod(pos, rng=rng) for _ in range(200)]
        self.assertTrue(any(d == 1 for d in drops))
        self.assertTrue(any(d == 0 for d in drops))
        self.assertTrue(all(d in (0, 1) for d in drops))

    def test_boss_anchor_sits_left_of_final_beacon(self) -> None:
        from gravity_ho_matey.levels.brood_moon_layout import (
            BOSS_ANCHOR,
            SURFACE_BOSS_LEFT_OF_FINAL_FRAC,
            SURFACE_FINAL_BEACON_FRAC,
            SURFACE_WRAP_WIDTH,
        )
        from gravity_ho_matey.levels.brood_moon_surface import surface_beacons

        final_x = SURFACE_WRAP_WIDTH * SURFACE_FINAL_BEACON_FRAC
        self.assertLess(BOSS_ANCHOR.x, final_x)
        self.assertAlmostEqual(
            final_x - BOSS_ANCHOR.x,
            SURFACE_WRAP_WIDTH * SURFACE_BOSS_LEFT_OF_FINAL_FRAC,
            delta=1.0,
        )
        beacons = surface_beacons()
        self.assertAlmostEqual(beacons[-1].pos.x, final_x, delta=1.0)

    def test_surface_wrap_width_shrunk(self) -> None:
        from gravity_ho_matey.levels.brood_moon_layout import SEAL_TRAVEL_DISTANCE, SURFACE_WRAP_WIDTH

        self.assertEqual(SURFACE_WRAP_WIDTH, 9240)
        self.assertEqual(SEAL_TRAVEL_DISTANCE, SURFACE_WRAP_WIDTH)

    def test_transition_assets_resolve_brood_gifs(self) -> None:
        from gravity_ho_matey.gameplay.brood_moon_mission import resolve_transition_asset

        landing = resolve_transition_asset("brood_moon_landing")
        ascent = resolve_transition_asset("brood_moon_ascent")
        self.assertIsNotNone(landing)
        self.assertIsNotNone(ascent)
        assert landing is not None and ascent is not None
        self.assertEqual(landing.name, "brood_moon_landing.gif")
        self.assertEqual(ascent.name, "brood_moon_ascent.gif")

    def test_layout_swap_clears_projectiles(self) -> None:
        from gravity_ho_matey.gameplay.entities import Projectile
        from gravity_ho_matey.gameplay.brood_moon_controller import apply_orbital_layout
        from gravity_ho_matey.levels.brood_moon_layout import build_brood_moon_orbital_layout

        world = build_level("brood_moon")
        apply_surface_layout(world)
        world.projectiles.append(
            Projectile(pos=Vec2(100.0, 100.0), vel=Vec2(10.0, 0.0), hostile=True),
        )
        layout = build_brood_moon_orbital_layout()
        apply_orbital_layout(world, layout, return_phase=True)
        self.assertEqual(len(world.projectiles), 0)


if __name__ == "__main__":
    unittest.main()
