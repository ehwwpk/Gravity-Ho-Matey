import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.levels.level_data import build_cove_run_level
from gravity_ho_matey.render.chase_helm import bank_angle_for_chase, predict_ship_path, slip_angle_rad
from gravity_ho_matey.render.chase_threat import ThreatLevel, nearest_asteroid_threat, predict_path_with_threats, threat_at_point


class ChaseHelmTests(unittest.TestCase):
    def test_slip_zero_when_velocity_matches_heading(self) -> None:
        angle = -math.pi / 2
        vel = Vec2.from_angle(angle) * 120
        self.assertAlmostEqual(slip_angle_rad(vel, angle), 0.0, places=4)

    def test_slip_positive_when_drifting_right(self) -> None:
        angle = -math.pi / 2
        vel = Vec2(80, -40)
        self.assertGreater(slip_angle_rad(vel, angle), 0.0)

    def test_bank_tilts_with_slip(self) -> None:
        angle = -math.pi / 2
        straight = bank_angle_for_chase(Vec2.from_angle(angle) * 100, angle)
        drift = bank_angle_for_chase(Vec2(120, -20), angle)
        self.assertNotAlmostEqual(straight, drift, places=3)

    def test_bank_tilts_with_turn_rate(self) -> None:
        angle = -math.pi / 2
        idle = bank_angle_for_chase(Vec2.from_angle(angle) * 100, angle, turn_rate=0.0)
        turning = bank_angle_for_chase(Vec2.from_angle(angle) * 100, angle, turn_rate=120.0)
        self.assertNotAlmostEqual(idle, turning, places=3)

    def test_g_frame_splits_forward_and_lateral(self) -> None:
        from gravity_ho_matey.render.chase_helm import _ship_frame_accel

        world = build_cove_run_level()
        world.ship.pos = Vec2(480, 320)
        g_fwd, g_lat, total = _ship_frame_accel(world, -math.pi / 2)
        self.assertGreater(total, 0.0)
        self.assertNotAlmostEqual(g_fwd, g_lat, places=0)

    def test_predict_path_curves_under_gravity(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(40, -80)
        path = predict_ship_path(world, steps=10)
        self.assertEqual(len(path), 11)
        moved = sum((path[i] - path[i - 1]).length_sq() for i in range(1, len(path)))
        self.assertGreater(moved, 1.0)

    def test_path_threat_tags_lethal_near_singularity(self) -> None:
        world = build_cove_run_level()
        reef = next(w for w in world.wells if w.label == "Dead Star Reef")
        world.ship.pos = Vec2(reef.pos.x, reef.pos.y + reef.radius * 0.2)
        world.ship.vel = Vec2(0, -60)
        samples = predict_path_with_threats(world, steps=8, step_dt=0.05)
        self.assertTrue(any(level is ThreatLevel.LETHAL for _, level in samples))

    def test_asteroid_threat_detects_near_rock(self) -> None:
        from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid

        world = build_cove_run_level()
        world.asteroids = [make_asteroid(Vec2(480, 30), seed=12, drift_kind="fast", velocity=Vec2(0, 80))]
        world.ship.pos = Vec2(480, 18)
        world.ship.vel = Vec2(0, 120)
        dist, closing = nearest_asteroid_threat(world)
        self.assertLess(dist, 40.0)
        self.assertGreater(closing, 0.0)

    def test_maw_point_is_lethal(self) -> None:
        world = build_cove_run_level()
        reef = next(w for w in world.wells if w.label == "Dead Star Reef")
        self.assertEqual(threat_at_point(world, reef.pos), ThreatLevel.LETHAL)


if __name__ == "__main__":
    unittest.main()
