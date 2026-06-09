from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import EvaAvatar, GravityWell, Ship
from gravity_ho_matey.gameplay.expedition_foot import tick_expedition_foot
from gravity_ho_matey.gameplay.expedition_mission import (
    ExpeditionInteractNode,
    ExpeditionPhase,
    InteractKind,
    delivery_node,
    expedition_foot_objectives_met,
    in_docking_band,
)
from gravity_ho_matey.levels.comet_fuel_asteroids import escape_patrol_squids, orbital_debris_asteroids
from gravity_ho_matey.levels.comet_fuel_expedition import (
    expedition_dimensions,
    expedition_squids,
    fuel_feed_lines,
    fuel_interact_nodes,
    squid_feed_points,
)
from gravity_ho_matey.gameplay.expedition_foot_config import FOOT_HUD_DEFAULT
from gravity_ho_matey.levels.comet_fuel_layout import (
    DELIVERY_CHARGE_SECONDS,
    LANDING_CHARGE_SECONDS,
    LANDER_PAD,
    CometFuelOrbitalLayout,
)
from gravity_ho_matey.levels.level_profiles import comet_fuel_expedition_config, comet_fuel_orbital_config


def _spawn_ship_copy(template: Ship) -> Ship:
    return Ship(
        pos=Vec2(template.pos.x, template.pos.y),
        vel=Vec2(template.vel.x, template.vel.y),
        angle=template.angle,
    )


def _update_comet_well(world, comet) -> None:
    pos = comet.position()
    if not world.wells:
        return
    world.wells[0] = GravityWell(
        pos,
        strength=28000.0,
        radius=comet.surface_radius * 2.2,
        label="Volatile Comet",
        kind="planet",
    )


def apply_orbital_layout(world, layout: CometFuelOrbitalLayout, *, escape: bool) -> None:
    config = comet_fuel_orbital_config(width=layout.width, height=layout.height)
    world.config = config
    exp = world.expedition
    comet = layout.comet
    if exp is not None and exp.comet is not None:
        comet = exp.comet.with_frozen_phase(False) if escape else exp.comet
        exp.comet = comet
    world.wells = list(layout.wells)
    _update_comet_well(world, comet)
    world.asteroids = orbital_debris_asteroids(layout, config, comet)
    world.beacons = []
    world.enemies = escape_patrol_squids(layout) if escape else []
    world.allies = []
    world.mega_squid = None
    world.squid_pods = []
    world.projectiles.clear()
    world.explosions.active.clear()
    world.avatar = None
    world.finish_gate = layout.finish_gate
    if exp is None:
        return
    if escape:
        world.ship.pos = Vec2(exp.parked_ship_pos.x, exp.parked_ship_pos.y)
        world.ship.vel = Vec2(0.0, -80.0)
        world.ship.angle = exp.parked_ship_angle
        exp.phase = ExpeditionPhase.ESCAPE_FLIGHT
        exp.hud_prompt = "CHARTER DEPOT — HOLD E TO DELIVER FUEL"
        exp.interact_nodes = [
            ExpeditionInteractNode(
                id="delivery_beacon",
                pos=layout.delivery_point,
                kind=InteractKind.DELIVERY_BEACON,
                charge_seconds=DELIVERY_CHARGE_SECONDS,
                radius=72.0,
            )
        ]
    else:
        world.ship = _spawn_ship_copy(layout.spawn_ship)
        exp.phase = ExpeditionPhase.ORBITAL
        exp.hud_prompt = "COMET APPROACH — HOLD E TO DOCK"
    world.asteroid_spatial.rebuild(world.asteroids)
    world.refresh_threat_snapshots()


def apply_expedition_foot_layout(world) -> None:
    width, height = expedition_dimensions()
    config = comet_fuel_expedition_config(width=width, height=height)
    world.config = config
    world.wells = []
    world.asteroids = []
    world.beacons = []
    exp = world.expedition
    if exp is None:
        return
    lines = fuel_feed_lines()
    feed_points = squid_feed_points(lines)
    squids, entries = expedition_squids(feed_points)
    exp.feed_lines = lines
    exp.feed_points = feed_points
    exp.interact_nodes = fuel_interact_nodes()
    exp.squid_entries = entries
    exp.hostiles_remaining = len(squids)
    world.enemies = squids
    world.mega_squid = None
    world.squid_pods = []
    world.projectiles.clear()
    world.explosions.active.clear()
    world.avatar = EvaAvatar(pos=Vec2(LANDER_PAD.x, LANDER_PAD.y + 28.0))
    world.ship.pos = Vec2(LANDER_PAD.x, LANDER_PAD.y - 18.0)
    world.ship.vel = Vec2()
    world.ship.angle = exp.parked_ship_angle if exp.parked_ship_angle else -math.pi / 2
    exp.phase = ExpeditionPhase.ON_FOOT
    exp.hud_prompt = FOOT_HUD_DEFAULT
    if exp.comet is not None:
        exp.comet = exp.comet.with_frozen_phase(True)
    world.asteroid_spatial.rebuild(world.asteroids)
    world.refresh_threat_snapshots()


def _begin_cinematic(exp, kind: str) -> None:
    from gravity_ho_matey.levels.comet_fuel_layout import CINEMATIC_DEFAULT_SECONDS

    exp.cinematic_kind = kind
    exp.cinematic_elapsed = 0.0
    exp.transition_asset_stem = f"comet_fuel_{kind}"
    exp.cinematic_seconds = CINEMATIC_DEFAULT_SECONDS
    exp.phase = (
        ExpeditionPhase.DOCK_CINEMATIC if kind == "dock" else ExpeditionPhase.UNDOCK_CINEMATIC
    )


def tick_expedition(world, dt: float, intent, *, interaction_hold: bool, aim_world: Vec2 | None = None) -> bool:
    """Returns True when gravity field should be rebaked."""
    exp = world.expedition
    if exp is None or exp.layout is None:
        return False

    if exp.in_cinematic:
        exp.cinematic_elapsed += dt
        if exp.cinematic_elapsed >= exp.cinematic_seconds:
            if exp.phase is ExpeditionPhase.DOCK_CINEMATIC:
                apply_expedition_foot_layout(world)
            elif exp.phase is ExpeditionPhase.UNDOCK_CINEMATIC:
                apply_orbital_layout(world, exp.layout, escape=True)
            return True
        return False

    if exp.phase is ExpeditionPhase.ORBITAL:
        if exp.comet is not None and not exp.comet.phase_frozen:
            exp.comet = exp.comet.advance(dt)
            _update_comet_well(world, exp.comet)
        comet = exp.comet
        if comet is not None and in_docking_band(world.ship.pos, comet):
            if interaction_hold:
                exp.landing_charge = min(LANDING_CHARGE_SECONDS, exp.landing_charge + dt)
                if exp.landing_charge >= LANDING_CHARGE_SECONDS:
                    exp.parked_ship_pos = Vec2(world.ship.pos.x, world.ship.pos.y)
                    exp.parked_ship_vel = Vec2(world.ship.vel.x, world.ship.vel.y)
                    exp.parked_ship_angle = world.ship.angle
                    if exp.comet is not None:
                        exp.comet = exp.comet.with_frozen_phase(True)
                    _begin_cinematic(exp, "dock")
            else:
                exp.landing_charge = max(0.0, exp.landing_charge - dt * 2.0)
        else:
            exp.landing_charge = max(0.0, exp.landing_charge - dt * 2.0)
        return False

    if exp.phase is ExpeditionPhase.ON_FOOT:
        tick_expedition_foot(world, exp, dt, intent, interaction_hold=interaction_hold, aim_world=aim_world)
        if exp.extract_pending and expedition_foot_objectives_met(exp):
            exp.extract_pending = False
            exp.fuel_aboard = True
            _begin_cinematic(exp, "undock")
        return False

    if exp.phase is ExpeditionPhase.ESCAPE_FLIGHT:
        if exp.comet is not None:
            exp.comet = exp.comet.advance(dt)
            _update_comet_well(world, exp.comet)
        if not exp.fuel_delivered:
            node = delivery_node(exp)
            if node is not None and (world.ship.pos - node.pos).length() <= node.radius:
                if interaction_hold:
                    exp.delivery_charge = min(DELIVERY_CHARGE_SECONDS, exp.delivery_charge + dt)
                    if exp.delivery_charge >= DELIVERY_CHARGE_SECONDS:
                        exp.fuel_delivered = True
                        exp.gate_unlocked = True
                        exp.hud_prompt = "FUEL SECURED — ENTER GATE"
                else:
                    exp.delivery_charge = max(0.0, exp.delivery_charge - dt * 2.0)
            else:
                exp.delivery_charge = max(0.0, exp.delivery_charge - dt * 2.0)
        else:
            exp.hud_prompt = "GATE OPEN — ENTER CHARTER LANE"
        return False

    return False
