from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.mega_squid_boss import (
    ENERGY_ORB_COOLDOWN,
    ENERGY_ORB_RANGE,
    MEGA_SQUID_HITS,
    PHASE_2_HP_THRESHOLD,
    PHASE_3_HP_THRESHOLD,
    PHASE_INVULN_SECONDS,
    POD_SPAWN_INTERVALS,
    SQUID_SPAWN_INTERVALS,
    MegaSquidBoss,
    combat_phase_for_hp,
)


class MegaSquidBossTests(unittest.TestCase):
    def _boss(self, *, hp: int = MEGA_SQUID_HITS) -> MegaSquidBoss:
        anchor = Vec2(0.0, 0.0)
        return MegaSquidBoss(pos=anchor, anchor=anchor, hits_remaining=hp, hits_max=MEGA_SQUID_HITS)

    def test_default_hp_is_32(self) -> None:
        boss = self._boss()
        self.assertEqual(MEGA_SQUID_HITS, 32)
        self.assertEqual(boss.hits_max, 32)
        self.assertEqual(boss.hits_remaining, 32)

    def test_phase_thresholds(self) -> None:
        self.assertEqual(combat_phase_for_hp(32), 1)
        self.assertEqual(combat_phase_for_hp(PHASE_2_HP_THRESHOLD + 1), 1)
        self.assertEqual(combat_phase_for_hp(PHASE_2_HP_THRESHOLD), 2)
        self.assertEqual(combat_phase_for_hp(PHASE_3_HP_THRESHOLD + 1), 2)
        self.assertEqual(combat_phase_for_hp(PHASE_3_HP_THRESHOLD), 3)
        self.assertEqual(combat_phase_for_hp(1), 3)

    def test_squid_spawn_intervals_by_phase(self) -> None:
        for phase, expected in enumerate(SQUID_SPAWN_INTERVALS, start=1):
            hp = {1: 32, 2: PHASE_2_HP_THRESHOLD, 3: PHASE_3_HP_THRESHOLD}[phase]
            boss = self._boss(hp=hp)
            boss.spawn_timer = expected - 0.5
            squid, _ = boss.tick_spawns(0.01, Vec2(400.0, 0.0), alive_squids=0)
            self.assertIsNone(squid, f"phase {phase} should not spawn before interval")
            boss.spawn_timer = expected - 0.01
            squid, _ = boss.tick_spawns(0.02, Vec2(400.0, 0.0), alive_squids=0)
            self.assertIsNotNone(squid, f"phase {phase} should spawn at interval {expected}s")

    def test_pods_only_phase_two_and_three(self) -> None:
        boss = self._boss(hp=32)
        boss.pod_timer = 999.0
        _, pod = boss.tick_spawns(0.0, Vec2(500.0, 0.0), alive_squids=0)
        self.assertIsNone(pod)

        boss = self._boss(hp=PHASE_2_HP_THRESHOLD)
        boss.pod_timer = POD_SPAWN_INTERVALS[1]
        _, pod = boss.tick_spawns(0.0, Vec2(500.0, 0.0), alive_squids=0)
        self.assertIsNotNone(pod)

    def test_phase_transition_grants_invuln(self) -> None:
        boss = self._boss(hp=PHASE_2_HP_THRESHOLD + 1)
        self.assertEqual(boss.combat_phase, 1)
        killed = boss.apply_shot()
        self.assertFalse(killed)
        self.assertEqual(boss.combat_phase, 2)
        self.assertGreater(boss.phase_invuln_remaining, 0.0)
        self.assertTrue(boss.phase_shift_pending)
        self.assertAlmostEqual(boss.phase_invuln_remaining, PHASE_INVULN_SECONDS)

    def test_invuln_blocks_damage(self) -> None:
        boss = self._boss(hp=20)
        boss.phase_invuln_remaining = 0.2
        hp_before = boss.hits_remaining
        self.assertFalse(boss.apply_shot())
        self.assertEqual(boss.hits_remaining, hp_before)

    def test_invuln_decays(self) -> None:
        boss = self._boss()
        boss.phase_invuln_remaining = 0.2
        boss.tick_combat(0.25)
        self.assertEqual(boss.phase_invuln_remaining, 0.0)

    def test_energy_orb_waits_for_cooldown_from_spawn(self) -> None:
        boss = self._boss()
        ship = Vec2(400.0, 0.0)
        self.assertIsNone(boss.try_fire(ship, Vec2()))
        boss.energy_cooldown = ENERGY_ORB_COOLDOWN
        self.assertIsNotNone(boss.try_fire(ship, Vec2()))

    def test_energy_orb_respects_cooldown(self) -> None:
        boss = self._boss()
        ship = Vec2(400.0, 0.0)
        boss.energy_cooldown = ENERGY_ORB_COOLDOWN - 0.1
        self.assertIsNone(boss.try_fire(ship, Vec2()))
        boss.energy_cooldown = ENERGY_ORB_COOLDOWN
        orb = boss.try_fire(ship, Vec2())
        self.assertIsNotNone(orb)
        self.assertTrue(orb.boss_energy_orb)
        self.assertTrue(orb.hostile)
        self.assertEqual(boss.energy_cooldown, 0.0)
        self.assertIsNone(boss.try_fire(ship, Vec2()))

    def test_energy_orb_out_of_range(self) -> None:
        boss = self._boss()
        boss.energy_cooldown = ENERGY_ORB_COOLDOWN
        far = Vec2(ENERGY_ORB_RANGE + 50.0, 0.0)
        self.assertIsNone(boss.try_fire(far, Vec2()))

    def test_energy_orb_blocked_during_invuln(self) -> None:
        boss = self._boss()
        boss.phase_invuln_remaining = 0.1
        boss.energy_cooldown = ENERGY_ORB_COOLDOWN
        self.assertIsNone(boss.try_fire(Vec2(400.0, 0.0), Vec2()))

    def test_apply_shot_kills_at_zero(self) -> None:
        boss = self._boss(hp=1)
        self.assertTrue(boss.apply_shot())
        self.assertFalse(boss.alive)

    def test_phase_transition_resets_spawn_timers(self) -> None:
        boss = self._boss(hp=PHASE_2_HP_THRESHOLD + 1)
        boss.spawn_timer = 4.0
        boss.pod_timer = 3.0
        boss.apply_shot()
        self.assertEqual(boss.spawn_timer, 0.0)
        self.assertEqual(boss.pod_timer, 0.0)


class SquidPodCombatTests(unittest.TestCase):
    def test_squid_pod_hit_radius(self) -> None:
        from gravity_ho_matey.gameplay.squid_pod import PodPhase, SquidPod

        flying = SquidPod(pos=Vec2(), vel=Vec2(), target=Vec2(100.0, 0.0))
        self.assertEqual(flying.hit_radius(), 10.0)
        hatching = SquidPod(
            pos=Vec2(),
            vel=Vec2(),
            target=Vec2(),
            phase=PodPhase.HATCHING,
        )
        self.assertEqual(hatching.hit_radius(), 16.0)


if __name__ == "__main__":
    unittest.main()
