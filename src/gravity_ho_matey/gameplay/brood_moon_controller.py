from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.brood_moon_mission import (
    BroodMoonState,
    BroodPhase,
    LANDING_CHARGE_SECONDS,
    LIFTOFF_CHARGE_SECONDS,
    in_landing_zone,
    liftoff_blocked,
    resolve_transition_asset,
    surface_objectives_met,
    tick_seal_progress,
    transition_playback_seconds,
    wrap_surface_x,
)
from gravity_ho_matey.gameplay.egg_pod_objective import EggPodObjective
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.brood_moon_layout import (
    SURFACE_CEILING_Y,
    SURFACE_EXOSPHERE_Y,
    SURFACE_GRAVITY_ACCEL,
    SURFACE_SCRAPE_Y,
)
from gravity_ho_matey.levels.brood_moon_surface import (
    boss_anchor,
    surface_beacons,
    surface_dimensions,
    surface_egg_pods,
    surface_patrols,
    surface_spawn_ship,
    surface_squid_drifters,
)
from gravity_ho_matey.levels.brood_moon_asteroids import orbital_debris_asteroids, surface_scree_asteroids
from gravity_ho_matey.levels.brood_moon_layout import BroodMoonOrbitalLayout
from gravity_ho_matey.levels.level_profiles import brood_moon_orbital_config, brood_moon_surface_config


def _spawn_ship_copy(template: Ship) -> Ship:
    return Ship(
        pos=Vec2(template.pos.x, template.pos.y),
        vel=Vec2(template.vel.x, template.vel.y),
        angle=template.angle,
    )


def apply_orbital_layout(world, layout: BroodMoonOrbitalLayout, *, return_phase: bool) -> None:
    config = brood_moon_orbital_config(width=layout.width, height=layout.height)
    world.config = config
    world.wells = list(layout.wells)
    world.asteroids = orbital_debris_asteroids(layout, config)
    world.beacons = []
    world.egg_pods = []
    world.enemies = []
    world.allies = []
    world.mega_squid = None
    world.squid_pods = []
    world.projectiles.clear()
    world.explosions.active.clear()
    world.finish_gate = layout.finish_gate
    bm = world.brood_moon
    if bm is None:
        return
    if return_phase:
        world.ship.pos = Vec2(bm.orbital_ship_pos.x, bm.orbital_ship_pos.y)
        world.ship.vel = Vec2(bm.orbital_ship_vel.x, bm.orbital_ship_vel.y)
        world.ship.angle = bm.orbital_ship_angle
        bm.phase = BroodPhase.ORBITAL_RETURN
        bm.dock_unlocked = True
        bm.hud_prompt = "RTB — QUARANTINE DOCK"
    else:
        world.ship = _spawn_ship_copy(layout.spawn_ship)
        bm.phase = BroodPhase.ORBITAL
        bm.dock_unlocked = False
    world.asteroid_spatial.rebuild(world.asteroids)
    world.refresh_threat_snapshots()


def apply_surface_layout(world) -> None:
    width, height = surface_dimensions()
    config = brood_moon_surface_config(width=width, height=height)
    world.config = config
    world.wells = []
    world.asteroids = surface_scree_asteroids(config)
    world.beacons = surface_beacons()
    world.egg_pods = surface_egg_pods()
    world.enemies = surface_patrols() + surface_squid_drifters()
    world.mega_squid = None
    world.squid_pods = []
    world.projectiles.clear()
    world.explosions.active.clear()
    world.ship = _spawn_ship_copy(surface_spawn_ship())
    bm = world.brood_moon
    if bm is not None:
        bm.phase = BroodPhase.SURFACE
        bm.last_ship_x = world.ship.pos.x
        bm.seal_travel = 0.0
        bm.seal_complete = False
        bm.objectives_complete = False
        bm.boss_spawned = False
        bm.ascent_ready = False
        bm.hud_prompt = "SURFACE — TAG BEACONS · RUPTURE PODS"
    world.asteroid_spatial.rebuild(world.asteroids)
    world.refresh_threat_snapshots()


def _begin_cinematic(bm: BroodMoonState, kind: str) -> None:
    bm.cinematic_kind = kind
    bm.cinematic_elapsed = 0.0
    bm.transition_asset_stem = f"brood_moon_{kind}"
    asset = resolve_transition_asset(bm.transition_asset_stem)
    bm.cinematic_seconds = transition_playback_seconds(bm.transition_asset_stem, None)
    if asset is not None:
        bm.cinematic_seconds = transition_playback_seconds(bm.transition_asset_stem, 4.0)
    if kind == "landing":
        bm.phase = BroodPhase.LANDING_CINEMATIC
    else:
        bm.phase = BroodPhase.ASCENT_CINEMATIC


def _spawn_surface_boss(world) -> None:
    anchor = boss_anchor()
    world.mega_squid = MegaSquidBoss(
        pos=Vec2(anchor.x, anchor.y - 120.0),
        anchor=anchor,
        max_cruise=58.0,
    )
    bm = world.brood_moon
    if bm is not None:
        bm.boss_spawned = True
        bm.boss_intro_flash = 3.5
        bm.hud_prompt = "BROOD MOTHER AWAKE — OPTIONAL HUNT"


def _spawn_alarm_squids(world, pod: EggPodObjective) -> None:
    for i in range(3):
        offset = Vec2.from_angle(0.9 + i * 1.4) * 80.0
        world.enemies.append(
            SquidEnemy(
                pos=pod.pos + offset,
                tentacle_reach=60.0,
                max_speed=178.0,
                detect_range=720.0,
                engage_range=580.0,
            )
        )


def on_egg_pod_destroyed(world, pod: EggPodObjective) -> None:
    from gravity_ho_matey.gameplay.jewel_drops import jewel_count_for_egg_pod

    drop_count = jewel_count_for_egg_pod(pod.pos)
    if drop_count > 0:
        world._spawn_jewels_at(pod.pos, drop_count)
    if pod.alarm:
        _spawn_alarm_squids(world, pod)


def tick_brood_moon(world, dt: float, *, interaction_hold: bool) -> bool:
    """Returns True when gravity field should be rebaked."""
    bm = world.brood_moon
    if bm is None or bm.layout is None:
        return False

    if bm.in_cinematic:
        bm.cinematic_elapsed += dt
        if bm.cinematic_elapsed >= bm.cinematic_seconds:
            if bm.phase is BroodPhase.LANDING_CINEMATIC:
                apply_surface_layout(world)
            elif bm.phase is BroodPhase.ASCENT_CINEMATIC:
                apply_orbital_layout(world, bm.layout, return_phase=True)
            return True
        return False

    if bm.phase is BroodPhase.ORBITAL:
        bm.hud_prompt = "APPROACH MOON LIMB · HOLD E"
        if in_landing_zone(world.ship.pos, bm.layout):
            if interaction_hold:
                bm.landing_charge = min(LANDING_CHARGE_SECONDS, bm.landing_charge + dt)
                if bm.landing_charge >= LANDING_CHARGE_SECONDS:
                    bm.orbital_ship_pos = Vec2(world.ship.pos.x, world.ship.pos.y)
                    bm.orbital_ship_vel = Vec2(world.ship.vel.x, world.ship.vel.y)
                    bm.orbital_ship_angle = world.ship.angle
                    _begin_cinematic(bm, "landing")
            else:
                bm.landing_charge = max(0.0, bm.landing_charge - dt * 2.0)
        else:
            bm.landing_charge = max(0.0, bm.landing_charge - dt * 2.0)
        return False

    if bm.phase is BroodPhase.SURFACE:
        tick_seal_progress(world, dt)
        if bm.boss_intro_flash > 0.0:
            bm.boss_intro_flash = max(0.0, bm.boss_intro_flash - dt)

        if not bm.objectives_complete and surface_objectives_met(world):
            bm.objectives_complete = True
            bm.hud_prompt = "NURSERY TAGGED — CIRCUMNAV TO SEAL"
            if not bm.boss_spawned:
                _spawn_surface_boss(world)

        wrap_w = float(world.config.width)
        world.ship.pos = Vec2(wrap_surface_x(world.ship.pos.x, wrap_w), world.ship.pos.y)

        if world.ship.pos.y > SURFACE_SCRAPE_Y:
            world.boss_scrape_flash = 0.35
            bm.terrain_scrape_cd = max(0.0, bm.terrain_scrape_cd - dt)
            if bm.terrain_scrape_cd <= 0.0 and world.invuln_remaining <= 0.0:
                bm.terrain_scrape_cd = 0.55
                world._register_ship_hit(DamageSource.ASTEROID, reason="Terrain scrape — hull chunk lost.")
        elif world.ship.pos.y < SURFACE_EXOSPHERE_Y:
            pull = (SURFACE_CEILING_Y - world.ship.pos.y) * 0.015
            world.ship.vel = Vec2(world.ship.vel.x * 0.992, world.ship.vel.y + pull)

        if bm.ascent_ready and not liftoff_blocked(world):
            bm.hud_prompt = "HOLD E TO ASCEND"
            if interaction_hold:
                bm.liftoff_charge = min(LIFTOFF_CHARGE_SECONDS, bm.liftoff_charge + dt)
                if bm.liftoff_charge >= LIFTOFF_CHARGE_SECONDS:
                    _begin_cinematic(bm, "ascent")
            else:
                bm.liftoff_charge = max(0.0, bm.liftoff_charge - dt * 2.0)
        elif liftoff_blocked(world):
            bm.hud_prompt = "BROOD COMBAT — ESCAPE LOCKED"
            bm.liftoff_charge = 0.0
        else:
            bm.liftoff_charge = max(0.0, bm.liftoff_charge - dt * 2.0)
        return False

    if bm.phase is BroodPhase.ORBITAL_RETURN:
        bm.hud_prompt = "QUARANTINE DOCK — ENTER GATE"
        return False

    return False


def surface_gravity_accel(world) -> Vec2 | None:
    bm = world.brood_moon
    if bm is None or not bm.on_surface:
        return None
    return Vec2(0.0, SURFACE_GRAVITY_ACCEL)
