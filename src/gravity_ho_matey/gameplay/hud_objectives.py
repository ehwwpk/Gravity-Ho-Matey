from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.world import GameWorld


@dataclass(frozen=True, slots=True)
class HudObjectiveCounter:
    """Play-HUD objective readout — same semantics as NAV BEACONS (remaining / total)."""

    label: str
    remaining: int
    total: int
    complete: bool


def egg_pods_required_count(world: GameWorld) -> int:
    """Ruptures needed to satisfy the pod objective — defaults to all pods on field."""
    if world.config.brood_moon_mission:
        from gravity_ho_matey.levels.brood_moon_layout import EGG_PODS_REQUIRED

        return EGG_PODS_REQUIRED
    return len(world.egg_pods)


def egg_pods_objective_complete(world: GameWorld) -> bool:
    from gravity_ho_matey.gameplay.brood_moon_mission import egg_pods_ruptured

    if not world.egg_pods:
        return True
    return egg_pods_ruptured(world) >= egg_pods_required_count(world)


def _protection_hostile_total(world: GameWorld) -> int:
    director = world.wave_director
    if director is None:
        return 0
    from gravity_ho_matey.levels.guard_waves import (
        WAVE1_PATROL_COUNT,
        WAVE2_SQUID_COUNT,
        WAVE3_FIGHTER_COUNT,
        WAVE3_SQUID_COUNT,
    )

    total = 0
    if director.waves_spawned >= 1:
        total += WAVE1_PATROL_COUNT
    if director.waves_spawned >= 2:
        total += WAVE2_SQUID_COUNT
    if director.waves_spawned >= 3:
        total += WAVE3_SQUID_COUNT + WAVE3_FIGHTER_COUNT
    return total


def objective_counters_for_world(world: GameWorld) -> tuple[HudObjectiveCounter, ...]:
    """Ordered HUD counters for the nav-objectives panel (beacons, pods, future types)."""
    counters: list[HudObjectiveCounter] = []

    if world.beacons:
        remaining = world.beacons_remaining
        total = len(world.beacons)
        counters.append(
            HudObjectiveCounter(
                label="NAV BEACONS",
                remaining=remaining,
                total=total,
                complete=remaining == 0,
            )
        )

    if world.egg_pods:
        remaining = world.egg_pods_remaining
        total = len(world.egg_pods)
        counters.append(
            HudObjectiveCounter(
                label="EGG PODS",
                remaining=remaining,
                total=total,
                complete=egg_pods_objective_complete(world),
            )
        )

    if world.config.protection_mission and world.wave_director is not None:
        director = world.wave_director
        wave_total = director.total_waves
        wave_current = director.waves_spawned
        counters.append(
            HudObjectiveCounter(
                label="WAVES",
                remaining=max(0, wave_total - wave_current),
                total=wave_total,
                complete=director.all_waves_fired,
            )
        )
        hostiles_alive = world.protection_hostiles_alive()
        hostile_total = _protection_hostile_total(world)
        counters.append(
            HudObjectiveCounter(
                label="HOSTILES",
                remaining=hostiles_alive,
                total=max(hostile_total, hostiles_alive, 1),
                complete=hostiles_alive == 0 and director.all_waves_fired,
            )
        )

    return tuple(counters)
