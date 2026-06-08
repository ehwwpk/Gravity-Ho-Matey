from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.hostile_fighter import HostileFighter


class HostileFighterTests(unittest.TestCase):
    def test_kind_is_hostile_fighter(self) -> None:
        fighter = HostileFighter(pos=Vec2(100.0, 200.0))
        self.assertEqual(fighter.kind, EnemyKind.HOSTILE_FIGHTER)

    def test_pick_pursue_target_prefers_nearest_threat(self) -> None:
        fighter = HostileFighter(pos=Vec2(0.0, 0.0), engage_range=600.0)
        station = Vec2(400.0, 0.0)
        player = Vec2(120.0, 0.0)
        picked = fighter.pick_pursue_target([(player, Vec2()), (station, Vec2())])
        self.assertIsNotNone(picked)
        assert picked is not None
        self.assertAlmostEqual((picked - player).length(), 0.0, delta=1.0)

    def test_integrate_moves_toward_pursue_target(self) -> None:
        fighter = HostileFighter(pos=Vec2(0.0, 0.0), vel=Vec2(), max_speed=125.0, thrust=280.0)
        target = Vec2(500.0, 0.0)
        for _ in range(30):
            fighter.integrate(
                0.05,
                [],
                gravity_scale=0.48,
                drag=0.98,
                well_maw_radius=10.0,
                homeward_target=None,
                homeward_thrust=0.0,
                pursue_target=target,
                pursue_thrust=260.0,
            )
        self.assertGreater(fighter.pos.x, 40.0)
        self.assertGreater(fighter.vel.length(), 20.0)

    def test_jewel_drop_tier_can_reach_ten(self) -> None:
        import random

        from gravity_ho_matey.gameplay.jewel_drops import jewel_count_for_enemy

        fighter = HostileFighter(pos=Vec2(900.0, 1200.0))
        counts = {jewel_count_for_enemy(fighter, random.Random(seed)) for seed in range(120)}
        self.assertIn(10, counts)

    def test_map_glyph_draws(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.enemy_viz import draw_hostile_fighter_map_glyph

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=40, height=40)
            draw_hostile_fighter_map_glyph(canvas, 20.0, 20.0, radius=8.0, facing=0.0)
            self.assertGreater(len(canvas.find_all()), 0)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
