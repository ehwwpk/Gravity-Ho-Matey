"""Standard wave-ingress markers for protection / timed-wave missions."""

from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2


@dataclass(frozen=True, slots=True)
class WaveIngressMarker:
    """One threat lane — rim chevron + tactical map glyph."""

    pos: Vec2
    tag: str
    toward: Vec2 | None = None


def _centroid(points: tuple[Vec2, ...]) -> Vec2:
    if not points:
        return Vec2()
    sx = sum(p.x for p in points)
    sy = sum(p.y for p in points)
    n = float(len(points))
    return Vec2(sx / n, sy / n)


def relay_wave_ingress_markers(wave: int, *, station: Vec2) -> tuple[WaveIngressMarker, ...]:
    """Relay Hold (L4) — per-wave ingress lanes authored in guard_layout."""
    from gravity_ho_matey.levels.guard_layout import (
        NORTHERN_RIFT,
        WAVE1_NE_SPAWNS,
        WAVE1_NW_SPAWNS,
        WAVE3_FIGHTER_SPAWNS,
    )

    if wave == 1:
        return (
            WaveIngressMarker(_centroid(WAVE1_NW_SPAWNS), "NW", toward=station),
            WaveIngressMarker(_centroid(WAVE1_NE_SPAWNS), "NE", toward=station),
        )
    if wave == 2:
        return (WaveIngressMarker(NORTHERN_RIFT, "N", toward=station),)
    if wave == 3:
        west_fighters = WAVE3_FIGHTER_SPAWNS[:2]
        east_fighters = WAVE3_FIGHTER_SPAWNS[2:4]
        return (
            WaveIngressMarker(_centroid(west_fighters), "NW", toward=station),
            WaveIngressMarker(NORTHERN_RIFT, "N", toward=station),
            WaveIngressMarker(_centroid(east_fighters), "NE", toward=station),
        )
    return ()


def ingress_wave_index(world) -> int | None:
    """Which wave's ingress lanes should be shown — inbound, active combat, or fresh spawn."""
    if not world.config.protection_mission or world.wave_director is None:
        return None
    if world.finish_unlocked or world.protection_combat_cleared:
        return None
    director = world.wave_director
    if director.inbound_wave > 0:
        return director.inbound_wave
    if director.nudge_ttl > 0.0 and director.nudge_wave > 0:
        return director.nudge_wave
    if director.waves_spawned > 0 and world.protection_hostiles_alive() > 0:
        return director.waves_spawned
    if (
        director.waves_spawned > 0
        and director.waves_spawned < director.total_waves
        and world.protection_hostiles_alive() == 0
    ):
        return director.waves_spawned + 1
    return None


def wave_ingress_markers_for_world(world) -> tuple[WaveIngressMarker, ...]:
    wave = ingress_wave_index(world)
    if wave is None:
        return ()
    if world.guard_layout is not None:
        return relay_wave_ingress_markers(wave, station=world.guard_layout.station_anchor)
    return ()
