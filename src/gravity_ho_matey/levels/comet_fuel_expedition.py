from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_behavior import FuelFeedLine, SquidFeedPoint
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.expedition_mission import ExpeditionInteractNode, ExpeditionSquidEntry, InteractKind
from gravity_ho_matey.levels.comet_fuel_layout import (
    EXPEDITION_FEEDING_SQUID_COUNT,
    EXPEDITION_HEIGHT,
    EXPEDITION_SQUID_COUNT,
    EXPEDITION_WIDTH,
    EXTRACT_CHARGE_SECONDS,
    FUEL_FEED_LINE_COUNT,
    FUEL_LOAD_CHARGE_SECONDS,
    FUEL_NODES_REQUIRED,
    LANDER_PAD,
)
from gravity_ho_matey.gameplay.squid_behavior import SquidBehaviorMode


def expedition_dimensions() -> tuple[int, int]:
    return EXPEDITION_WIDTH, EXPEDITION_HEIGHT


def charter_depot_center() -> Vec2:
    return Vec2(1200.0, 680.0)


DEPOT_PLATFORM_RADIUS = 340.0
LANDER_BLAST_RADIUS = 200.0


def foot_regolith_anchors() -> tuple[tuple[int, float, float, float], ...]:
    """(seed, cx, cy, radius) — comet regolith boulders on the foot map."""
    return (
        (11, 600.0, 900.0, 120.0),
        (12, 1700.0, 700.0, 140.0),
        (13, 900.0, 1300.0, 100.0),
        (14, 1500.0, 1200.0, 110.0),
        (15, 420.0, 620.0, 88.0),
        (16, 1980.0, 980.0, 95.0),
        (17, 680.0, 1520.0, 72.0),
        (18, 1720.0, 1480.0, 78.0),
    )


def fuel_feed_lines() -> list[FuelFeedLine]:
    depot = charter_depot_center()
    return [
        FuelFeedLine("line_a", depot, Vec2(980.0, 1180.0)),
        FuelFeedLine("line_b", depot, Vec2(1420.0, 1160.0)),
        FuelFeedLine("line_c", Vec2(1200.0, 820.0), Vec2(860.0, 980.0)),
        FuelFeedLine("line_d", Vec2(1200.0, 820.0), Vec2(1540.0, 960.0)),
        FuelFeedLine("line_e", Vec2(1080.0, 720.0), Vec2(720.0, 1320.0)),
        FuelFeedLine("line_f", Vec2(1320.0, 720.0), Vec2(1680.0, 1280.0)),
    ][:FUEL_FEED_LINE_COUNT]


def squid_feed_points(lines: list[FuelFeedLine]) -> list[SquidFeedPoint]:
    points: list[SquidFeedPoint] = []
    for i, line in enumerate(lines):
        anchor = line.start + (line.end - line.start) * 0.72
        facing = math.atan2(line.end.y - line.start.y, line.end.x - line.start.x)
        points.append(
            SquidFeedPoint(
                id=f"feed_{i}",
                pos=anchor,
                line_id=line.id,
                feed_target=line.end,
                facing_angle=facing,
            )
        )
    return points


def _foot_squid(pos: Vec2, *, feeding: bool) -> SquidEnemy:
    return SquidEnemy(
        pos=pos,
        radius=14.0,
        tentacle_reach=72.0,
        max_speed=185.0 if not feeding else 42.0,
        detect_range=520.0 if not feeding else 260.0,
        engage_range=440.0 if not feeding else 220.0,
        approach_thrust=380.0 if not feeding else 0.0,
    )


def expedition_squids(feed_points: list[SquidFeedPoint]) -> tuple[list[SquidEnemy], list[ExpeditionSquidEntry]]:
    squids: list[SquidEnemy] = []
    entries: list[ExpeditionSquidEntry] = []
    feeding_target = EXPEDITION_FEEDING_SQUID_COUNT
    for i, fp in enumerate(feed_points):
        per_line = 2 if i < 5 else 1
        for j in range(per_line):
            if len(squids) >= feeding_target:
                break
            offset = Vec2.from_angle(fp.facing_angle + math.pi + j * 0.4) * (18.0 + j * 8.0)
            squids.append(_foot_squid(fp.pos + offset, feeding=True))
            entries.append(
                ExpeditionSquidEntry(
                    squid_index=len(squids) - 1,
                    mode=SquidBehaviorMode.FEEDING.name,
                    feed_point_id=fp.id,
                )
            )
    patrol_spots = (
        Vec2(1200.0, 580.0),
        Vec2(900.0, 760.0),
        Vec2(1500.0, 760.0),
        Vec2(1050.0, 1050.0),
        Vec2(1350.0, 1040.0),
        Vec2(760.0, 1380.0),
    )
    for spot in patrol_spots:
        if len(squids) >= EXPEDITION_SQUID_COUNT:
            break
        squids.append(_foot_squid(spot, feeding=False))
        entries.append(
            ExpeditionSquidEntry(
                squid_index=len(squids) - 1,
                mode=SquidBehaviorMode.ENGAGE.name,
            )
        )
    return squids, entries


def fuel_interact_nodes() -> list[ExpeditionInteractNode]:
    valves = (
        Vec2(1080.0, 640.0),
        Vec2(1200.0, 600.0),
        Vec2(1320.0, 640.0),
    )
    nodes: list[ExpeditionInteractNode] = []
    for i, pos in enumerate(valves[:FUEL_NODES_REQUIRED]):
        nodes.append(
            ExpeditionInteractNode(
                id=f"valve_{i}",
                pos=pos,
                kind=InteractKind.FUEL_VALVE,
                charge_seconds=FUEL_LOAD_CHARGE_SECONDS,
            )
        )
    nodes.append(
        ExpeditionInteractNode(
            id="extract_pad",
            pos=Vec2(LANDER_PAD.x, LANDER_PAD.y + 8.0),
            kind=InteractKind.EXTRACT_PAD,
            charge_seconds=EXTRACT_CHARGE_SECONDS,
            radius=108.0,
            one_shot=False,
        )
    )
    return nodes
