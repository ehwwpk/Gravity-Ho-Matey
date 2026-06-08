from __future__ import annotations

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, Ship, SpaceJunk
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.space_junk_prefabs import reset_instance_counter, validate_space_junk_list
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_profiles import open_sector_config
from gravity_ho_matey.levels.space_junk_placements import junk_gate_pair, junk_wall_line, min_gate_gap_for_ship


def build_junk_sandbox_scrap() -> list[SpaceJunk]:
    """Dev-only corridor — not in LEVEL_ORDER."""
    gap = min_gate_gap_for_ship()
    left = junk_wall_line(Vec2(800.0, 400.0), Vec2(800.0, 2200.0), prefab="girder_a", angle=0.0)
    right = junk_wall_line(Vec2(1200.0, 400.0), Vec2(1200.0, 2200.0), prefab="girder_a", angle=0.0)
    gate = junk_gate_pair(center=Vec2(1000.0, 1200.0), width=gap + 48.0, prefab="truss_corner_a")
    mid_barrier = junk_wall_line(Vec2(950.0, 1600.0), Vec2(1050.0, 1600.0), prefab="boom_segment_a", angle=0.0)
    return left + right + gate + mid_barrier


def build_junk_sandbox_world() -> GameWorld:
    """Test/sandbox layout only — never wired into level_registry."""
    reset_instance_counter()
    config = open_sector_config(theme="drift", name="Junk Sandbox", arena_size=3200)
    junk = build_junk_sandbox_scrap()
    validate_space_junk_list(junk, max_count=config.max_space_junk)
    world = GameWorld(
        config=config,
        ship=Ship(pos=Vec2(1000.0, 520.0), angle=1.5708),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(980, 2280, 40, 40)),
        space_junk=junk,
        junk_spatial_static=True,
        enemies=[
            PatrolEnemy(
                waypoints=(Vec2(1000.0, 900.0), Vec2(1000.0, 1400.0)),
                pos=Vec2(1000.0, 900.0),
                vel=Vec2(0.0, 40.0),
            ),
            SquidEnemy(pos=Vec2(1020.0, 1100.0), vel=Vec2(-20.0, 30.0)),
        ],
    )
    world.junk_spatial.rebuild(world.space_junk)
    return world
