from __future__ import annotations

import unittest

from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.offscreen_hostile_hints import append_offscreen_hostile_hints


class OffscreenHostileHintTests(unittest.TestCase):
    def test_rift_wave_one_hostiles_north_get_rim_bearings(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        self.assertGreater(world.protection_hostiles_alive(), 0)

        ship = world.ship.pos
        cam = ViewCamera(mode=CameraMode.TACTICAL, viewport_width=960, viewport_height=720)
        cam.snap_tactical_to_ship(ship, world.config)
        hud_top = 80.0

        hints: list[tuple[float, str, str]] = []
        append_offscreen_hostile_hints(
            hints,
            cam,
            world,
            ship,
            world.ship.angle,
            vw=960.0,
            vh=720.0,
            play_top=hud_top,
        )
        self.assertGreater(len(hints), 0)
        # Wave 1 patrols approach from the north — bearings should aim upward on screen.
        for angle, tag, _color in hints:
            self.assertIn(tag, {"EN", "SQ", "CR"})
            self.assertLess(angle, -0.2)

    def test_on_screen_hostiles_do_not_add_rim_hints(self) -> None:
        world = build_level("rift")
        world.update(0.016, ControlIntent())
        for enemy in world.enemies:
            enemy.pos = world.ship.pos

        ship = world.ship.pos
        cam = ViewCamera(mode=CameraMode.TACTICAL, viewport_width=960, viewport_height=720)
        cam.snap_tactical_to_ship(ship, world.config)

        hints: list[tuple[float, str, str]] = []
        append_offscreen_hostile_hints(
            hints,
            cam,
            world,
            ship,
            world.ship.angle,
            vw=960.0,
            vh=720.0,
            play_top=80.0,
        )
        self.assertEqual(hints, [])


if __name__ == "__main__":
    unittest.main()
