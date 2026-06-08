from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_RIM_EXPAND_L12,
    CHART_SECTOR_MARGIN_FRAC,
    COVE_CHART_MARGIN_FRAC,
    COVE_OOB_PLACEMENT_MARGIN_FRAC,
)
from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, build_level


def test_all_registered_levels_build() -> None:
    from gravity_ho_matey.settings import SOLAR_STRIP_HEIGHT

    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        assert world.config.viewport_width == 960
        assert world.config.viewport_height == 640
        assert len(world.beacons) >= 3 or level_id in ("drift", "rift", "siege", "brood_moon")
        assert len(world.wells) >= 3 or level_id in ("drift", "rift", "siege", "brood_moon")
        if level_id == "cove":
            assert world.config.height == 640
        if level_id == "solar":
            assert world.config.height == SOLAR_STRIP_HEIGHT
        if level_id == "drift":
            assert world.config.width == 4800
            assert world.config.height == 4800
        if level_id == "rift":
            assert world.config.width == 4000
            assert world.config.height == 3200
            assert world.config.protection_mission is True
            assert len(world.friendly_stations) == 1
        if level_id == "siege":
            assert world.config.width == 5200
            assert world.config.height == 3200
            assert world.config.exit_requires_roster_clear is True
            assert len(world.enemies) == 12
            assert len(world.allies) == 12
            assert world.space_station is not None
        if level_id == "brood_moon":
            assert world.config.width == 4800
            assert world.config.brood_moon_mission is True
            assert world.brood_moon is not None


def test_all_registered_levels_have_asteroids() -> None:
    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        min_rocks = 3 if level_id == "cove" else (100 if level_id == "drift" else (12 if level_id == "rift" else 8))
        assert len(world.asteroids) >= min_rocks
        assert world.config.open_bounds is True


def test_cove_is_light_intro_asteroid_field() -> None:
    world = build_level("cove")
    intro = [a for a in world.asteroids if not a.free_bounds]
    void_ring = [a for a in world.asteroids if a.free_bounds]
    assert len(intro) <= 5
    assert len(void_ring) == 20
    drift_kinds = {a.drift_kind for a in intro}
    assert "ring" in drift_kinds


def test_cove_chart_rim_mediums_sit_just_outside_chart() -> None:
    from dataclasses import replace

    from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
    from gravity_ho_matey.gameplay.chart_bounds import (
        COVE_OOB_PLACEMENT_MARGIN_FRAC,
        chart_oob_distance,
        ship_in_chart,
    )

    world = build_level("cove")
    placement_cfg = replace(world.config, chart_margin_frac=COVE_OOB_PLACEMENT_MARGIN_FRAC)
    rim = [
        a
        for a in world.asteroids
        if a.free_bounds and a.tier is AsteroidTier.MEDIUM and a.size_class == "rock"
    ]
    assert len(rim) == 4
    for asteroid in rim:
        assert not ship_in_chart(asteroid.pos, placement_cfg)
        dist = chart_oob_distance(asteroid.pos, world.config)
        # Hazard rim frozen; expanded play chart may overlap slightly.
        assert -2.0 <= dist <= 18.0


def test_solar_level_is_open_space_layout() -> None:
    world = build_level("solar")
    assert len(world.asteroids) == 14
    assert world.config.open_bounds is True
    assert len(world.beacons) == 3
    drift_kinds = {a.drift_kind for a in world.asteroids}
    assert "ring" in drift_kinds
    assert "shower" in drift_kinds


def test_solar_mid_beacon_clear_of_singularity_core() -> None:
    from gravity_ho_matey.core.vector import Vec2

    world = build_level("solar")
    singularity = next(w for w in world.wells if w.kind == "black_hole")
    mid_beacon = world.beacons[1]
    inset = (mid_beacon.pos - singularity.pos).length()
    assert inset >= 120.0
    assert abs(mid_beacon.pos.x - singularity.pos.x) > 40.0


def test_solar_level_has_black_hole_and_planets() -> None:
    world = build_level("solar")
    assert world.config.level_theme == "solar"
    kinds = {well.kind for well in world.wells}
    assert "black_hole" in kinds
    assert "planet" in kinds


def test_campaign_level_order() -> None:
    from gravity_ho_matey.levels.level_registry import next_level_id

    assert next_level_id("cove") == "solar"
    assert next_level_id("solar") == "drift"
    assert next_level_id("drift") == "rift"
    assert next_level_id("rift") == "siege"
    assert next_level_id("siege") == "brood_moon"
    assert next_level_id("brood_moon") is None


def test_solar_level_has_patrol_enemies() -> None:
    world = build_level("solar")
    assert len(world.enemies) == 2
    assert any(enemy.alive for enemy in world.enemies)


def test_cove_play_chart_wider_than_hazard_placement_rim() -> None:
    from dataclasses import replace

    from gravity_ho_matey.core.vector import Vec2
    from gravity_ho_matey.gameplay.chart_bounds import (
        COVE_OOB_PLACEMENT_MARGIN_FRAC,
        chart_limits,
        chart_limits_for_margin_frac,
        ship_in_chart,
    )

    world = build_level("cove")
    x0, _, x1, _ = chart_limits(world.config)
    px0, _, px1, _ = chart_limits_for_margin_frac(world.config, COVE_OOB_PLACEMENT_MARGIN_FRAC)
    assert x0 < px0
    assert x1 > px1
    probe = Vec2(px0 - 4.0, world.config.height * 0.5)
    old_cfg = replace(world.config, chart_margin_frac=COVE_OOB_PLACEMENT_MARGIN_FRAC)
    assert not ship_in_chart(probe, old_cfg)
    assert ship_in_chart(probe, world.config)


def test_chart_sectors_use_expanded_margin_on_levels_one_and_two() -> None:
    cove = build_level("cove")
    solar = build_level("solar")
    drift = build_level("drift")
    assert cove.config.chart_margin_frac == COVE_CHART_MARGIN_FRAC
    assert solar.config.chart_margin_frac == CHART_SECTOR_MARGIN_FRAC
    assert drift.config.chart_margin_frac != CHART_SECTOR_MARGIN_FRAC
    assert abs(COVE_CHART_MARGIN_FRAC / COVE_OOB_PLACEMENT_MARGIN_FRAC - CHART_RIM_EXPAND_L12) < 1e-6
    assert abs(CHART_SECTOR_MARGIN_FRAC / (COVE_OOB_PLACEMENT_MARGIN_FRAC - 0.05) - CHART_RIM_EXPAND_L12) < 1e-6


def test_l12_play_chart_gives_more_room_than_pre_expand_rim() -> None:
    """Play chart must extend well past the frozen hazard-placement rim on both L1/L2."""
    from gravity_ho_matey.gameplay.chart_bounds import chart_limits, chart_limits_for_margin_frac

    for level_id in ("cove", "solar"):
        world = build_level(level_id)
        x0, y0, x1, y1 = chart_limits(world.config)
        px0, py0, px1, py1 = chart_limits_for_margin_frac(
            world.config, COVE_OOB_PLACEMENT_MARGIN_FRAC if level_id == "cove" else (COVE_OOB_PLACEMENT_MARGIN_FRAC - 0.05)
        )
        assert x0 < px0
        assert y0 < py0
        assert x1 > px1
        assert y1 > py1
        # At least ~10 world units of grace beyond the old rim on every axis (Cove L1).
        assert px0 - x0 >= 10.0
        assert x1 - px1 >= 10.0


def test_level_registry_matches_builders() -> None:
    from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, LEVEL_ORDER

    assert set(LEVEL_ORDER) == set(LEVEL_BUILDERS)
