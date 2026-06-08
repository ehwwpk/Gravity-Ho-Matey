"""Player weapon heat — escalating buildup, steep slowdown, accelerated cool-down."""

from __future__ import annotations

from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.weapon_config import (
    PLAYER_WEAPON_HEAT_DECAY_BASE,
    PLAYER_WEAPON_HEAT_DECAY_HEAT_POWER,
    PLAYER_WEAPON_HEAT_DECAY_HEAT_SCALE,
    PLAYER_WEAPON_HEAT_ESCALATION_POWER,
    PLAYER_WEAPON_HEAT_ESCALATION_SCALE,
    PLAYER_WEAPON_HEAT_ESCALATION_START,
    PLAYER_WEAPON_HEAT_GAIN_MULT,
    PLAYER_WEAPON_HEAT_PER_SHOT_DEFAULT,
    PLAYER_WEAPON_HEAT_PER_SHOT_EXPLOSIVE,
    PLAYER_WEAPON_HEAT_PER_SHOT_LASER,
    PLAYER_WEAPON_HEAT_PER_SHOT_SHOTGUN,
    PLAYER_WEAPON_HEAT_PER_SHOT_SHOTGUN_ADV,
    PLAYER_WEAPON_HEAT_SIMMER_BASE,
    PLAYER_WEAPON_HEAT_SIMMER_HEAT_SCALE,
    PLAYER_WEAPON_HEAT_SOFT_MAX_MULT,
    PLAYER_WEAPON_HEAT_SOFT_START,
    PLAYER_WEAPON_HEAT_SOFT_TIER_1,
    PLAYER_WEAPON_HEAT_SOFT_TIER_2,
    PLAYER_WEAPON_HEAT_SOFT_TIER_3,
    PLAYER_WEAPON_OVERHEAT_COOLDOWN,
    PLAYER_WEAPON_RAPID_FIRE_HEAT_MULT,
)
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack


def player_weapon_overheated(ship: Ship) -> bool:
    return ship.weapon_overheat_timer > 0.0


def ship_weapon_heat_visible(ship: Ship) -> bool:
    return ship.weapon_heat > 0.08 or ship.weapon_overheat_timer > 0.0


def heat_per_shot(
    track: WeaponTrack | None,
    *,
    advanced: bool = False,
    rapid_fire: bool = False,
) -> float:
    if track is WeaponTrack.LASER:
        amount = PLAYER_WEAPON_HEAT_PER_SHOT_LASER
    elif track is WeaponTrack.SHOTGUN:
        amount = PLAYER_WEAPON_HEAT_PER_SHOT_SHOTGUN_ADV if advanced else PLAYER_WEAPON_HEAT_PER_SHOT_SHOTGUN
    elif track is WeaponTrack.EXPLOSIVE:
        amount = PLAYER_WEAPON_HEAT_PER_SHOT_EXPLOSIVE
    else:
        amount = PLAYER_WEAPON_HEAT_PER_SHOT_DEFAULT
    if rapid_fire:
        amount *= PLAYER_WEAPON_RAPID_FIRE_HEAT_MULT
    return amount


def heat_escalation_multiplier(current_heat: float) -> float:
    """Hot barrels absorb more heat per trigger pull — sustained fire keeps climbing."""
    hot = max(0.0, current_heat - PLAYER_WEAPON_HEAT_ESCALATION_START)
    if hot <= 0.0:
        return 1.0
    return 1.0 + (hot ** PLAYER_WEAPON_HEAT_ESCALATION_POWER) * PLAYER_WEAPON_HEAT_ESCALATION_SCALE


def apply_heat_on_fire(
    ship: Ship,
    track: WeaponTrack | None,
    *,
    advanced: bool = False,
    rapid_fire: bool = False,
) -> None:
    gain = heat_per_shot(track, advanced=advanced, rapid_fire=rapid_fire)
    gain *= heat_escalation_multiplier(ship.weapon_heat)
    _add_weapon_heat(ship, gain)


def player_heat_decay_rate(heat: float) -> float:
    """Higher heat sheds faster once you stop firing — 90% cools quicker than 70%."""
    h = max(0.0, min(1.0, heat))
    return PLAYER_WEAPON_HEAT_DECAY_BASE * (0.35 + (h ** PLAYER_WEAPON_HEAT_DECAY_HEAT_POWER) * PLAYER_WEAPON_HEAT_DECAY_HEAT_SCALE)


def player_heat_simmer_rate(heat: float) -> float:
    """Passive barrel heat while the trigger is held — climbs even between slow shots."""
    h = max(0.0, min(1.0, heat))
    return PLAYER_WEAPON_HEAT_SIMMER_BASE + h * PLAYER_WEAPON_HEAT_SIMMER_HEAT_SCALE


def _add_weapon_heat(ship: Ship, amount: float) -> None:
    if amount <= 0.0:
        return
    amount *= PLAYER_WEAPON_HEAT_GAIN_MULT
    ship.weapon_heat = min(1.0, ship.weapon_heat + amount)
    if ship.weapon_heat >= 1.0:
        ship.weapon_overheat_timer = PLAYER_WEAPON_OVERHEAT_COOLDOWN


def tick_player_weapon_heat(ship: Ship, dt: float, *, trigger_held: bool = False) -> None:
    if ship.weapon_overheat_timer > 0.0:
        ship.weapon_overheat_timer = max(0.0, ship.weapon_overheat_timer - dt)
        if ship.weapon_overheat_timer <= 0.0:
            ship.weapon_heat = 0.0
        return
    if trigger_held:
        _add_weapon_heat(ship, player_heat_simmer_rate(ship.weapon_heat) * dt)
        return
    if ship.weapon_heat > 0.0:
        ship.weapon_heat = max(0.0, ship.weapon_heat - player_heat_decay_rate(ship.weapon_heat) * dt)


def _lerp_mult(low: float, high: float, heat: float, start: float, end: float) -> float:
    if heat <= start:
        return low
    if heat >= end:
        return high
    t = (heat - start) / max(1e-6, end - start)
    return low + t * (high - low)


def player_heat_fire_cooldown_multiplier(heat: float) -> float:
    """Soft throttle — gentle early, brutal past ~70%, ~90% slower by 85%+."""
    h = max(0.0, min(1.0, heat))
    if h <= PLAYER_WEAPON_HEAT_SOFT_START:
        return 1.0
    if h <= PLAYER_WEAPON_HEAT_SOFT_TIER_1:
        return _lerp_mult(1.0, 1.85, h, PLAYER_WEAPON_HEAT_SOFT_START, PLAYER_WEAPON_HEAT_SOFT_TIER_1)
    if h <= PLAYER_WEAPON_HEAT_SOFT_TIER_2:
        return _lerp_mult(1.85, 3.35, h, PLAYER_WEAPON_HEAT_SOFT_TIER_1, PLAYER_WEAPON_HEAT_SOFT_TIER_2)
    if h <= PLAYER_WEAPON_HEAT_SOFT_TIER_3:
        return _lerp_mult(3.35, 8.25, h, PLAYER_WEAPON_HEAT_SOFT_TIER_2, PLAYER_WEAPON_HEAT_SOFT_TIER_3)
    return _lerp_mult(8.25, PLAYER_WEAPON_HEAT_SOFT_MAX_MULT, h, PLAYER_WEAPON_HEAT_SOFT_TIER_3, 0.93)


def reset_player_weapon_heat(ship: Ship) -> None:
    ship.weapon_heat = 0.0
    ship.weapon_overheat_timer = 0.0
