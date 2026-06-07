from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, build_level


def test_all_registered_levels_build() -> None:
    from gravity_ho_matey.settings import SOLAR_STRIP_HEIGHT

    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        assert world.config.viewport_width == 960
        assert world.config.viewport_height == 640
        assert len(world.beacons) >= 3 or level_id == "drift"
        assert len(world.wells) >= 3 or level_id == "drift"
        if level_id == "cove":
            assert world.config.height == 640
        if level_id == "solar":
            assert world.config.height == SOLAR_STRIP_HEIGHT
        if level_id == "drift":
            assert world.config.width == 4800
            assert world.config.height == 4800


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
    assert len(void_ring) == 16
    drift_kinds = {a.drift_kind for a in intro}
    assert "ring" in drift_kinds


def test_solar_level_is_open_space_layout() -> None:
    world = build_level("solar")
    assert len(world.asteroids) >= 8
    assert world.config.open_bounds is True
    assert len(world.beacons) == 3
    drift_kinds = {a.drift_kind for a in world.asteroids}
    assert "ring" in drift_kinds
    assert "shower" in drift_kinds


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
    assert next_level_id("drift") is None


def test_solar_level_has_patrol_enemies() -> None:
    world = build_level("solar")
    assert len(world.enemies) >= 3
    assert any(enemy.alive for enemy in world.enemies)


def test_level_registry_matches_builders() -> None:
    from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, LEVEL_ORDER

    assert set(LEVEL_ORDER) == set(LEVEL_BUILDERS)
