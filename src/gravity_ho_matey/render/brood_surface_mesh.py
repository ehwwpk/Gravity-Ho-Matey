from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2

MAX_PROP_VERTS = 12


def mesh_for(kind: str, seed: int, scale: float) -> tuple[Vec2, ...]:
    """Procedural local mesh for brood surface props — max 12 verts."""
    rng = random.Random(seed)
    if kind == "spire":
        h = 48.0 * scale
        w = 14.0 * scale
        return (
            Vec2(-w, 0.0),
            Vec2(w, 0.0),
            Vec2(w * 0.6, -h * 0.45),
            Vec2(0.0, -h),
            Vec2(-w * 0.6, -h * 0.45),
        )
    if kind == "stalk":
        h = 32.0 * scale
        w = 8.0 * scale
        return (
            Vec2(-w, 0.0),
            Vec2(w, 0.0),
            Vec2(w * 0.4, -h * 0.55),
            Vec2(0.0, -h),
            Vec2(-w * 0.4, -h * 0.55),
        )
    if kind == "spore_jelly":
        r = 16.0 * scale
        count = 8
        verts: list[Vec2] = []
        for idx in range(count):
            angle = (idx / count) * math.tau
            verts.append(
                Vec2(
                    math.cos(angle) * r * rng.uniform(0.88, 1.08),
                    math.sin(angle) * r * rng.uniform(0.82, 1.05),
                )
            )
        return tuple(verts)
    if kind == "drift_pod":
        w = 14.0 * scale
        h = 20.0 * scale
        return (
            Vec2(-w * 0.9, h * 0.2),
            Vec2(w * 0.85, h * 0.15),
            Vec2(w, -h * 0.35),
            Vec2(0.0, -h),
            Vec2(-w, -h * 0.3),
        )
    if kind == "veil_wisp":
        w = 38.0 * scale
        h = 10.0 * scale
        return (
            Vec2(-w, h * 0.3),
            Vec2(-w * 0.4, -h),
            Vec2(w * 0.35, -h * 0.85),
            Vec2(w, h * 0.2),
            Vec2(w * 0.2, h),
            Vec2(-w * 0.6, h * 0.85),
        )
    if kind == "chitin_bloom":
        r = 20.0 * scale
        return (
            Vec2(-r * 0.8, r * 0.15),
            Vec2(-r * 0.2, -r * 0.55),
            Vec2(r * 0.35, -r * 0.65),
            Vec2(r * 0.85, -r * 0.1),
            Vec2(r * 0.45, r * 0.45),
            Vec2(-r * 0.55, r * 0.5),
        )
    if kind == "float_bulb":
        r = 12.0 * scale
        stem = 26.0 * scale
        return (
            Vec2(-r * 0.35, 0.0),
            Vec2(r * 0.35, 0.0),
            Vec2(r * 0.25, -stem * 0.55),
            Vec2(0.0, -stem),
            Vec2(-r * 0.25, -stem * 0.55),
        )
    if kind == "crystal":
        h = 28.0 * scale
        return (
            Vec2(0.0, -h),
            Vec2(h * 0.35, -h * 0.2),
            Vec2(h * 0.2, h * 0.15),
            Vec2(-h * 0.2, h * 0.15),
            Vec2(-h * 0.35, -h * 0.2),
        )
    if kind == "sinkhole_rim":
        r = 22.0 * scale
        count = 8
        verts: list[Vec2] = []
        for idx in range(count):
            angle = (idx / count) * math.tau + rng.uniform(-0.1, 0.1)
            verts.append(
                Vec2(
                    math.cos(angle) * r * rng.uniform(0.85, 1.05),
                    math.sin(angle) * r * 0.35 * rng.uniform(0.9, 1.1),
                )
            )
        return tuple(verts)
    if kind == "vein_node":
        r = 18.0 * scale
        return (
            Vec2(-r, 0.0),
            Vec2(r, 0.0),
            Vec2(r * 0.5, -r * 0.6),
            Vec2(-r * 0.5, -r * 0.6),
        )
    # scarp, mound default rock chunk
    count = 7
    verts: list[Vec2] = []
    base = 24.0 * scale
    for i in range(count):
        angle = (i / count) * math.tau + rng.uniform(-0.12, 0.12)
        radius = base * rng.uniform(0.75, 1.05)
        verts.append(Vec2(math.cos(angle) * radius, math.sin(angle) * radius * 0.55))
    return tuple(verts[:MAX_PROP_VERTS])
