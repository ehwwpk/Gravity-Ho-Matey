from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy


def enemy_visual_seed(enemy: PatrolEnemy) -> int:
    rid = enemy.skirmish_roster_id
    if rid is not None:
        return (rid * 7919 + 17) & 0x7FFFFFFF
    return (int(enemy.pos.x) * 5 + int(enemy.pos.y) * 11 + 9031) & 0x7FFFFFFF


@dataclass(frozen=True, slots=True)
class EnemyGreebleLamp:
    x: float
    y: float
    radius: float


@dataclass(slots=True)
class EnemySkiffMesh:
    """Hostile patrol skiff — local space, +X = facing, unit radius = enemy.radius."""

    hull: list[tuple[float, float]]
    left_wing: list[tuple[float, float]]
    right_wing: list[tuple[float, float]]
    engine_block: list[tuple[float, float]]
    weapon_pod: list[tuple[float, float]]
    spine_lines: list[tuple[float, float, float, float]] = field(default_factory=list)
    panel_lines: list[tuple[float, float, float, float]] = field(default_factory=list)
    lamps: list[EnemyGreebleLamp] = field(default_factory=list)
    antenna: tuple[float, float, float, float] | None = None



def _wing_quad(rng: random.Random, *, side: float, reach: float, chord: float) -> list[tuple[float, float]]:
    """Side = +1 starboard, -1 port."""
    root_x = 0.08 + rng.random() * 0.06
    tip_x = root_x - reach * (0.55 + rng.random() * 0.2)
    spread = chord * (0.88 + rng.random() * 0.18)
    return [
        (root_x, side * spread * 0.35),
        (root_x - 0.12, side * spread * 0.95),
        (tip_x, side * spread * 0.72),
        (tip_x + 0.08, side * spread * 0.28),
    ]


def build_enemy_skiff_mesh(*, seed: int) -> EnemySkiffMesh:
    rng = random.Random(seed)
    wobble = 0.06 + rng.random() * 0.05
    nose = 1.02 + rng.random() * 0.08
    beam = 0.48 + rng.random() * wobble

    hull = [
        (nose, 0.0),
        (0.42, beam),
        (-0.05, beam + 0.06),
        (-0.72, beam * 0.88),
        (-0.98, 0.28),
        (-1.02, 0.0),
        (-0.98, -0.28),
        (-0.72, -beam * 0.88),
        (-0.05, -(beam + 0.06)),
        (0.42, -beam),
    ]

    left_wing = _wing_quad(rng, side=-1.0, reach=0.38 + rng.random() * 0.08, chord=0.42)
    right_wing = _wing_quad(rng, side=1.0, reach=0.38 + rng.random() * 0.08, chord=0.42)

    engine_block = [
        (-0.88, -0.18),
        (-1.05, -0.12),
        (-1.08, 0.0),
        (-1.05, 0.12),
        (-0.88, 0.18),
        (-0.72, 0.14),
        (-0.72, -0.14),
    ]

    pod_w = 0.14 + rng.random() * 0.04
    weapon_pod = [
        (0.72, -pod_w),
        (0.98, -pod_w * 0.55),
        (0.98, pod_w * 0.55),
        (0.72, pod_w),
        (0.58, pod_w * 0.75),
        (0.58, -pod_w * 0.75),
    ]

    spine: list[tuple[float, float, float, float]] = [
        (0.55, 0.0, -0.55, 0.0),
        (0.2, 0.0, -0.85, 0.0),
    ]
    panels: list[tuple[float, float, float, float]] = []
    for i in range(2 + rng.randint(0, 2)):
        px = 0.15 + i * 0.22
        py = beam * 0.55 * (1.0 if i % 2 == 0 else -1.0)
        panels.append((px, py, px - 0.18, py * 0.35))

    lamps: list[EnemyGreebleLamp] = []
    for _ in range(2 + rng.randint(0, 2)):
        angle = rng.random() * math.tau
        lamps.append(
            EnemyGreebleLamp(
                x=math.cos(angle) * (0.55 + rng.random() * 0.25),
                y=math.sin(angle) * (0.28 + rng.random() * 0.18),
                radius=0.035 + rng.random() * 0.02,
            )
        )

    ant_angle = rng.random() * 0.5 - 0.25
    _ = ant_angle
    antenna = (
        -0.55,
        0.32 + rng.random() * 0.08,
        -0.55 - 0.22,
        0.32 + 0.18 + rng.random() * 0.1,
    )

    return EnemySkiffMesh(
        hull=hull,
        left_wing=left_wing,
        right_wing=right_wing,
        engine_block=engine_block,
        weapon_pod=weapon_pod,
        spine_lines=spine,
        panel_lines=panels,
        lamps=lamps,
        antenna=antenna,
    )


def mesh_for_enemy(enemy: PatrolEnemy) -> EnemySkiffMesh:
    return build_enemy_skiff_mesh(seed=enemy_visual_seed(enemy))


def local_to_world_rotated(
    point: tuple[float, float],
    pos: Vec2,
    radius: float,
    facing: float,
) -> Vec2:
    lx, ly = point
    c = math.cos(facing)
    s = math.sin(facing)
    return Vec2(pos.x + (lx * c - ly * s) * radius, pos.y + (lx * s + ly * c) * radius)
