from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, build_level


def test_all_registered_levels_build() -> None:
    from gravity_ho_matey.levels.level_data import SOLAR_STRIP_HEIGHT

    for level_id in LEVEL_BUILDERS:
        world = build_level(level_id)
        assert world.config.viewport_width == 960
        assert world.config.viewport_height == 640
        assert len(world.beacons) >= 3
        assert len(world.wells) >= 3
        if level_id == "cove":
            assert world.config.height == 640
        if level_id == "solar":
            assert world.config.height == SOLAR_STRIP_HEIGHT


def test_solar_level_is_open_space_layout() -> None:
    world = build_level("solar")
    assert len(world.walls) == 4
    assert len(world.beacons) == 3


def test_solar_level_has_black_hole_and_planets() -> None:
    world = build_level("solar")
    assert world.config.level_theme == "solar"
    kinds = {well.kind for well in world.wells}
    assert "black_hole" in kinds
    assert "planet" in kinds


def test_campaign_level_order() -> None:
    from gravity_ho_matey.levels.level_registry import next_level_id

    assert next_level_id("cove") == "solar"
    assert next_level_id("solar") is None


def test_solar_level_has_patrol_enemies() -> None:
    world = build_level("solar")
    assert len(world.enemies) >= 3
    assert any(enemy.alive for enemy in world.enemies)


def test_level_registry_matches_builders() -> None:
    from gravity_ho_matey.levels.level_registry import LEVEL_BUILDERS, LEVEL_ORDER

    assert set(LEVEL_ORDER) == set(LEVEL_BUILDERS)
