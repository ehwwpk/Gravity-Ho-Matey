from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_behavior import SquidBehaviorMode, SquidFeedPoint
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.expedition_mission import ExpeditionSquidEntry

ALERT_DURATION = 0.6
PROXIMITY_ALERT_SECONDS = 0.35
CHAIN_ALERT_RADIUS = 480.0
MAX_CHAIN_ALERT = 3


def _feed_point_by_id(feed_points: list[SquidFeedPoint], feed_id: str | None) -> SquidFeedPoint | None:
    if feed_id is None:
        return None
    for fp in feed_points:
        if fp.id == feed_id:
            return fp
    return None


def tick_expedition_squid(
    squid: SquidEnemy,
    entry: ExpeditionSquidEntry,
    *,
    feed_points: list[SquidFeedPoint],
    avatar_pos: Vec2,
    avatar_radius: float,
    dt: float,
) -> None:
    if not squid.alive:
        return
    mode = SquidBehaviorMode[entry.mode]
    feed = _feed_point_by_id(feed_points, entry.feed_point_id)
    dist_avatar = (avatar_pos - squid.pos).length()
    detect = squid.detect_range * (0.5 if mode is SquidBehaviorMode.FEEDING else 1.0)

    if mode is SquidBehaviorMode.FEEDING:
        if feed is not None:
            wobble = Vec2.from_angle(squid.facing_angle + 0.4) * 8.0
            target = feed.pos + wobble
            squid.pos = squid.pos + (target - squid.pos) * min(1.0, dt * 4.0)
            squid.vel = Vec2()
            squid.facing_angle = math.atan2(
                feed.feed_target.y - squid.pos.y,
                feed.feed_target.x - squid.pos.x,
            )
            squid.update_tentacles(dt, feed.feed_target, 8.0)
        if dist_avatar <= detect:
            entry.alert_timer += dt
            if entry.alert_timer >= PROXIMITY_ALERT_SECONDS:
                entry.mode = SquidBehaviorMode.ALERT.name
                entry.alert_timer = ALERT_DURATION
        else:
            entry.alert_timer = max(0.0, entry.alert_timer - dt * 0.5)
        return

    if mode is SquidBehaviorMode.ALERT:
        entry.alert_timer -= dt
        if feed is not None:
            squid.facing_angle = math.atan2(
                avatar_pos.y - squid.pos.y,
                avatar_pos.x - squid.pos.x,
            )
            squid.update_tentacles(dt, avatar_pos, avatar_radius)
        if entry.alert_timer <= 0.0:
            entry.mode = SquidBehaviorMode.ENGAGE.name
        return

    squid.integrate(
        dt,
        avatar_pos,
        Vec2(),
        [],
        gravity_scale=0.0,
        drag=0.92,
        prey_radius=avatar_radius,
    )


def alert_squid_on_damage(entry: ExpeditionSquidEntry) -> None:
    if entry.mode == SquidBehaviorMode.FEEDING.name:
        entry.mode = SquidBehaviorMode.ALERT.name
        entry.alert_timer = ALERT_DURATION


def chain_alert_nearby(
    entries: list[ExpeditionSquidEntry],
    squids: list[SquidEnemy],
    origin: Vec2,
) -> None:
    count = 0
    for entry, squid in zip(entries, squids, strict=False):
        if not squid.alive or entry.mode != SquidBehaviorMode.FEEDING.name:
            continue
        if (squid.pos - origin).length() <= CHAIN_ALERT_RADIUS:
            entry.mode = SquidBehaviorMode.ALERT.name
            entry.alert_timer = ALERT_DURATION
            count += 1
            if count >= MAX_CHAIN_ALERT:
                break
