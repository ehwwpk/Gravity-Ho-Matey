from __future__ import annotations

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GravityWell, Ship
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.asteroid_placements import build_cove_asteroids, build_solar_asteroids
from gravity_ho_matey.levels.drift_belt_asteroids import build_drift_belt_asteroids
from gravity_ho_matey.levels.drift_belt_layout import build_drift_layout
from gravity_ho_matey.levels.drift_enemies import drift_squid_enemies
from gravity_ho_matey.gameplay.chart_bounds import COVE_CHART_MARGIN_FRAC, SOLAR_CHART_EXTRA_MARGIN_WU
from gravity_ho_matey.levels.level_profiles import (
    chart_sector_config,
    open_sector_config,
    protection_arena_config,
    skirmish_arena_config,
)
from gravity_ho_matey.levels.guard_asteroids import build_guard_asteroids
from gravity_ho_matey.levels.guard_layout import build_guard_layout
from gravity_ho_matey.levels.guard_stations import relay_friendly_stations
from gravity_ho_matey.gameplay.wave_director import WaveDirector
from gravity_ho_matey.levels.solar_patrols import solar_patrol_enemies
from gravity_ho_matey.levels.siege_asteroids import siege_spiral_asteroids
from gravity_ho_matey.levels.siege_enemies import siege_roster_patrols
from gravity_ho_matey.levels.siege_escorts import siege_friendly_fighters
from gravity_ho_matey.levels.siege_layout import ROSTER_KILL_QUOTA, build_siege_layout
from gravity_ho_matey.levels.siege_station import siege_hostile_station
from gravity_ho_matey.gameplay.tractor_beam import TractorBeamState
from gravity_ho_matey.gameplay.brood_moon_mission import BroodMoonState
from gravity_ho_matey.levels.brood_moon_layout import build_brood_moon_orbital_layout
from gravity_ho_matey.levels.brood_moon_asteroids import orbital_debris_asteroids
from gravity_ho_matey.levels.level_profiles import brood_moon_orbital_config
from gravity_ho_matey.settings import CANVAS_WIDTH, SOLAR_STRIP_HEIGHT


def _spawn_ship_copy(template: Ship) -> Ship:
    """Layout spawn templates must not alias live ship state (pos/vel mutate in play)."""
    return Ship(
        pos=Vec2(template.pos.x, template.pos.y),
        vel=Vec2(template.vel.x, template.vel.y),
        angle=template.angle,
    )


def build_cove_run_level() -> GameWorld:
    wells = [
        GravityWell(Vec2(240, 420), strength=34000, radius=210, label="Black Rum Eddy"),
        GravityWell(Vec2(470, 295), strength=42000, radius=235, label="Dead Star Reef"),
        GravityWell(Vec2(705, 120), strength=31000, radius=185, label="Kraken Moon"),
        GravityWell(Vec2(720, 430), strength=39000, radius=210, label="Maelstrom"),
    ]
    beacons = [
        Beacon(Vec2(95, 560)),
        Beacon(Vec2(335, 90)),
        Beacon(Vec2(600, 390)),
        Beacon(Vec2(870, 115)),
    ]
    config = chart_sector_config(
        theme="cove",
        name="Smuggler's Cove",
        chart_margin_frac=COVE_CHART_MARGIN_FRAC,
    )
    return GameWorld(
        config=config,
        ship=Ship(pos=Vec2(80, 70), angle=0.58),
        asteroids=build_cove_asteroids(config),
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(880, 550, 54, 54)),
    )


def build_solar_crossing_level() -> GameWorld:
    """Level 2 — vertical star strip; free forward/back flight with central singularity."""
    cx = CANVAS_WIDTH / 2
    strip_h = SOLAR_STRIP_HEIGHT
    wells = [
        GravityWell(
            Vec2(cx, strip_h * 0.5),
            strength=52000,
            radius=155,
            label="Singularity",
            kind="black_hole",
            maw_radius=22,
        ),
        GravityWell(Vec2(cx, 180), strength=19000, radius=78, label="Scorched Prince", kind="planet"),
        GravityWell(Vec2(755, strip_h * 0.38), strength=24000, radius=92, label="Verdant Shell", kind="planet"),
        GravityWell(Vec2(205, strip_h * 0.62), strength=21000, radius=82, label="Rust Belt", kind="planet"),
        GravityWell(Vec2(795, strip_h * 0.72), strength=27000, radius=118, label="Jolly Giant", kind="planet"),
        GravityWell(Vec2(175, strip_h * 0.28), strength=20000, radius=76, label="Ice Halo", kind="planet"),
    ]
    beacons = [
        Beacon(Vec2(915, strip_h * 0.22)),
        # Mid-strip nav point — offset from singularity core (was on the inner rim at x=cx).
        Beacon(Vec2(530, strip_h * 0.575)),
        Beacon(Vec2(165, strip_h * 0.78)),
    ]
    config = chart_sector_config(
        theme="solar",
        name="Singularity Crossing",
        width=CANVAS_WIDTH,
        height=int(strip_h),
        gravity_scale=0.45,
        turn_rate=5.2,
        thrust=255.0,
        chart_extra_margin_wu=SOLAR_CHART_EXTRA_MARGIN_WU,
    )
    return GameWorld(
        config=config,
        ship=Ship(pos=Vec2(52, 120), angle=1.52),
        asteroids=build_solar_asteroids(),
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(895, strip_h - 90, 50, 50)),
        enemies=solar_patrol_enemies(strip_h),
    )


def build_drift_belt_level() -> GameWorld:
    """Level 3 — concentric belts, titan wells, void squids, north exit."""
    layout = build_drift_layout()
    config = open_sector_config(theme="drift", name="The Drift", arena_size=4800)
    return GameWorld(
        config=config,
        ship=_spawn_ship_copy(layout.spawn_ship),
        asteroids=build_drift_belt_asteroids(config),
        wells=list(layout.wells),
        beacons=[],
        finish_gate=layout.finish_gate,
        enemies=drift_squid_enemies(layout),
    )


def build_relay_hold_level() -> GameWorld:
    """Level 4 — defend the relay station through three timed assault waves."""
    layout = build_guard_layout()
    config = protection_arena_config(theme="rift", name="Relay Hold", width=layout.width, height=layout.height)
    return GameWorld(
        config=config,
        ship=_spawn_ship_copy(layout.spawn_ship),
        asteroids=build_guard_asteroids(layout, config),
        wells=list(layout.wells),
        beacons=[],
        finish_gate=layout.finish_gate,
        friendly_stations=relay_friendly_stations(layout),
        guard_layout=layout,
        wave_director=WaveDirector(),
    )


def build_siege_line_level() -> GameWorld:
    """Level 5 — two-force skirmish across a spiral belt; hostile station guards exit."""
    layout = build_siege_layout()
    config = skirmish_arena_config(
        theme="siege",
        name="The Siege Line",
        width=layout.width,
        height=layout.height,
        roster_kill_quota=ROSTER_KILL_QUOTA,
    )
    roster = siege_roster_patrols(layout)
    return GameWorld(
        config=config,
        ship=_spawn_ship_copy(layout.spawn_ship),
        asteroids=siege_spiral_asteroids(layout, config),
        wells=list(layout.wells),
        beacons=[],
        finish_gate=layout.finish_gate,
        enemies=roster,
        allies=siege_friendly_fighters(layout),
        space_station=siege_hostile_station(layout),
        tractor_beam=TractorBeamState(),
        roster_enemies_total=config.roster_kill_quota,
        roster_enemies_remaining=config.roster_kill_quota,
    )


def build_brood_moon_level() -> GameWorld:
    """Level 6 — land on the Brood Moon, tag beacons, rupture egg pods, RTB dock."""
    layout = build_brood_moon_orbital_layout()
    config = brood_moon_orbital_config(width=layout.width, height=layout.height)
    world = GameWorld(
        config=config,
        ship=_spawn_ship_copy(layout.spawn_ship),
        asteroids=orbital_debris_asteroids(layout, config),
        wells=list(layout.wells),
        beacons=[],
        finish_gate=layout.finish_gate,
        brood_moon=BroodMoonState(layout=layout),
    )
    return world
