from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.jewel_config import (
    JEWEL_DRAG,
    JEWEL_RADIUS,
    MAGNET_RANGE,
    MAGNET_SPEED,
    SCATTER_OFFSET_MAX,
    SCATTER_SPEED_MAX,
    SCATTER_SPEED_MIN,
)
from gravity_ho_matey.gameplay.jewel_drops import rng_at


@dataclass(slots=True)
class JewelPickup:
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    radius: float = JEWEL_RADIUS


def spawn_scattered_jewels(pos: Vec2, count: int, rng: random.Random | None = None) -> list[JewelPickup]:
    if count <= 0:
        return []
    roll = rng or rng_at(pos)
    jewels: list[JewelPickup] = []
    for _ in range(count):
        angle = roll.uniform(0.0, math.tau)
        speed = roll.uniform(SCATTER_SPEED_MIN, SCATTER_SPEED_MAX)
        offset = Vec2.from_angle(angle) * roll.uniform(0.0, SCATTER_OFFSET_MAX)
        jewels.append(
            JewelPickup(
                pos=Vec2(pos.x + offset.x, pos.y + offset.y),
                vel=Vec2.from_angle(angle) * speed,
            )
        )
    return jewels


def tick_jewels(
    jewels: list[JewelPickup],
    ship_pos: Vec2,
    ship_radius: float,
    dt: float,
    *,
    allow_collect: bool = True,
    helper_pos: Vec2 | None = None,
    helper_radius: float = 0.0,
) -> tuple[list[JewelPickup], int]:
    remaining: list[JewelPickup] = []
    collected = 0
    drag = JEWEL_DRAG ** max(0.0, dt * 60.0)

    for jewel in jewels:
        collectors: list[tuple[Vec2, float]] = [(ship_pos, ship_radius)]
        if helper_pos is not None and helper_radius > 0.0:
            collectors.append((helper_pos, helper_radius))

        picked_up = False
        if allow_collect:
            for c_pos, c_radius in collectors:
                if (c_pos - jewel.pos).length() <= c_radius + jewel.radius:
                    collected += 1
                    picked_up = True
                    break
        if picked_up:
            continue

        magnet_pos: Vec2 | None = None
        magnet_dist = float("inf")
        for c_pos, c_radius in collectors:
            to_collector = c_pos - jewel.pos
            dist = to_collector.length()
            if dist <= MAGNET_RANGE and dist < magnet_dist:
                magnet_pos = c_pos
                magnet_dist = dist

        if magnet_pos is not None and magnet_dist > 1e-6:
            jewel.vel = (magnet_pos - jewel.pos).normalized() * MAGNET_SPEED
        else:
            jewel.vel = jewel.vel * drag

        jewel.pos = jewel.pos + jewel.vel * dt

        if allow_collect:
            for c_pos, c_radius in collectors:
                if (c_pos - jewel.pos).length() <= c_radius + jewel.radius:
                    collected += 1
                    picked_up = True
                    break
        if not picked_up:
            remaining.append(jewel)

    return remaining, collected
