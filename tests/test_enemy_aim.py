import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_aim import intercept_time, lead_aim_direction


class EnemyAimTests(unittest.TestCase):
    def test_intercept_stationary_target(self) -> None:
        rel = Vec2(300, 0)
        t = intercept_time(rel, Vec2(), 250.0)
        self.assertIsNotNone(t)
        assert t is not None
        self.assertAlmostEqual(t, 1.2, places=1)

    def test_lead_aim_tracks_crossing_target(self) -> None:
        shooter = Vec2(0, 0)
        target = Vec2(400, 0)
        target_vel = Vec2(0, 120)
        aim = lead_aim_direction(shooter, target, target_vel, 260.0)
        self.assertIsNotNone(aim)
        assert aim is not None
        self.assertGreater(aim.y, 0.15)

    def test_lead_aim_hits_linear_target_in_simulation(self) -> None:
        shooter = Vec2(0, 0)
        target = Vec2(500, 0)
        target_vel = Vec2(-80, 60)
        shot_speed = 255.0
        aim = lead_aim_direction(shooter, target, target_vel, shot_speed)
        self.assertIsNotNone(aim)
        assert aim is not None
        bullet_vel = aim * shot_speed
        bullet_pos = Vec2(shooter.x, shooter.y)
        ship_pos = Vec2(target.x, target.y)
        hit_dist = 999.0
        for _ in range(120):
            bullet_pos = bullet_pos + bullet_vel * 0.05
            ship_pos = ship_pos + target_vel * 0.05
            hit_dist = min(hit_dist, (ship_pos - bullet_pos).length())
        self.assertLess(hit_dist, 20.0)

    def test_intercept_returns_none_when_target_outruns_shot(self) -> None:
        rel = Vec2(100, 0)
        target_vel = Vec2(400, 0)
        t = intercept_time(rel, target_vel, 200.0)
        self.assertIsNone(t)


if __name__ == "__main__":
    unittest.main()
