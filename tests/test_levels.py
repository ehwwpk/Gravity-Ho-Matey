from gravity_ho_matey.gameplay.chart_bounds import CHART_SECTOR_MARGIN_FRAC, COVE_CHART_MARGIN_FRAC
from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, build_level


def test_all_registered_levels_build() -> None:
    from gravity_ho_matey.settings import SOLAR_STRIP_HEIGHT

    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        assert world.config.viewport_width == 960
        assert world.config.viewport_height == 640
        assert len(world.beacons) >= 3 or level_id in ("drift", "rift", "siege")
        assert len(world.wells) >= 3 or level_id in ("drift", "rift", "siege")
        if level_id == "cove":
            assert world.config.height == 640
        if level_id == "solar":
            assert world.config.height == SOLAR_STRIP_HEIGHT
        if level_id == "drift":
            assert world.config.width == 4800
            assert world.config.height == 4800
        if level_id == "rift":
            assert world.config.width == 2000
            assert world.config.height == 5000
            assert world.config.exit_requires_boss is True
        if level_id == "siege":
            assert world.config.width == 5200
            assert world.config.height == 3200
            assert world.config.exit_requires_roster_clear is True
            assert len(world.enemies) == 12
            assert len(world.allies) == 12
            assert world.space_station is not None


def test_all_registered_levels_have_asteroids() -> None:
    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        min_rocks = 3 if level_id == "cove" else (100 if level_id == "drift" else 8)
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
    from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
    from gravity_ho_matey.gameplay.chart_bounds import chart_limits, chart_oob_distance, ship_in_chart

    world = build_level("cove")
    rim = [
        a
        for a in world.asteroids
        if a.free_bounds and a.tier is AsteroidTier.MEDIUM and a.size_class == "rock"
    ]
    assert len(rim) == 4
    for asteroid in rim:
        assert not ship_in_chart(asteroid.pos, world.config)
        dist = chart_oob_distance(asteroid.pos, world.config)
        assert 8.0 <= dist <= 40.0


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
    assert next_level_id("siege") is None


def test_solar_level_has_patrol_enemies() -> None:
    world = build_level("solar")
    assert len(world.enemies) == 2
    assert any(enemy.alive for enemy in world.enemies)


def test_chart_sectors_use_expanded_margin_on_levels_one_and_two() -> None:
    cove = build_level("cove")
    solar = build_level("solar")
    drift = build_level("drift")
    assert cove.config.chart_margin_frac == COVE_CHART_MARGIN_FRAC
    assert solar.config.chart_margin_frac == CHART_SECTOR_MARGIN_FRAC
    assert drift.config.chart_margin_frac != CHART_SECTOR_MARGIN_FRAC


def test_level_registry_matches_builders() -> None:
    from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, LEVEL_ORDER

    assert set(LEVEL_ORDER) == set(LEVEL_BUILDERS)
