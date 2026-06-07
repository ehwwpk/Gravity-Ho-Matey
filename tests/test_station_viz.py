from __future__ import annotations

import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.lighting import LightRig, station_material_for
from gravity_ho_matey.render.station_mesh import mesh_for_station, station_visual_seed


class StationMeshTests(unittest.TestCase):
    def _station(self, *, faction: StationFaction, label: str = "RELAY") -> SpaceStation:
        return SpaceStation(
            pos=Vec2(2000.0, 1600.0),
            anchor=Vec2(2000.0, 1600.0),
            faction=faction,
            station_label=label,
        )

    def test_mesh_seed_stable(self) -> None:
        station = self._station(faction=StationFaction.FRIENDLY)
        seed_a = station_visual_seed(station)
        seed_b = station_visual_seed(station)
        self.assertEqual(seed_a, seed_b)

    def test_friendly_and_hostile_share_topology(self) -> None:
        pos = Vec2(2000.0, 1600.0)
        friendly = SpaceStation(pos=pos, anchor=pos, faction=StationFaction.FRIENDLY, station_label="RELAY")
        hostile = SpaceStation(pos=pos, anchor=pos, faction=StationFaction.HOSTILE, station_label="RELAY")
        f_mesh = mesh_for_station(friendly)
        h_mesh = mesh_for_station(hostile)
        self.assertEqual(len(f_mesh.back_ring), len(h_mesh.back_ring))
        self.assertEqual(len(f_mesh.mid_arms), len(h_mesh.mid_arms))
        self.assertEqual(len(f_mesh.panel_recesses), len(h_mesh.panel_recesses))
        self.assertEqual(len(f_mesh.lamps), len(h_mesh.lamps))
        self.assertEqual(len(f_mesh.pods), len(h_mesh.pods))
        self.assertEqual(len(f_mesh.antennas), len(h_mesh.antennas))

    def test_faction_materials_differ(self) -> None:
        rig = LightRig.for_play(theme="rift", camera_mode=CameraMode.TACTICAL)
        friendly = station_material_for(StationFaction.FRIENDLY, theme=rig.theme, view=rig.view)
        hostile = station_material_for(StationFaction.HOSTILE, theme=rig.theme, view=rig.view)
        self.assertNotEqual(friendly.mid, hostile.mid)
        self.assertNotEqual(friendly.rim, hostile.rim)


class StationDrawTests(unittest.TestCase):
    def test_tactical_and_map_draw_without_error(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.gameplay.entities import WorldConfig
        from gravity_ho_matey.render.station_viz import draw_map_station_glyph, draw_space_station_tactical

        station = SpaceStation(
            pos=Vec2(2000.0, 1600.0),
            anchor=Vec2(2000.0, 1600.0),
            faction=StationFaction.FRIENDLY,
            station_label="RELAY",
        )
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        config = WorldConfig(width=4000, height=3200, viewport_width=960, viewport_height=586)
        camera.snap_tactical_to_ship(Vec2(2000.0, 1800.0), config)
        rig = LightRig.for_play(theme="rift", camera_mode=CameraMode.TACTICAL)
        draw_space_station_tactical(
            canvas,
            station,
            camera,
            ship_pos=Vec2(2000.0, 1800.0),
            ship_angle=0.0,
            hud_top=54.0,
            rig=rig,
            elapsed=1.0,
        )
        self.assertGreater(len(canvas.find_all()), 20)
        draw_map_station_glyph(canvas, Vec2(120.0, 80.0), station, scale=0.5, rig=rig)
        self.assertGreater(len(canvas.find_all()), 22)
        root.destroy()

    def test_chase_projection_capped_when_close(self) -> None:
        from gravity_ho_matey.render.station_viz import CHASE_STATION_MAX_R_PX, chase_station_screen_points

        station = SpaceStation(
            pos=Vec2(2000.0, 1600.0),
            anchor=Vec2(2000.0, 1600.0),
            faction=StationFaction.FRIENDLY,
            station_label="RELAY",
        )
        mesh = mesh_for_station(station)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = Vec2(2000.0, 1730.0)
        ship_angle = -math.pi / 2.0
        projected = chase_station_screen_points(mesh.back_ring, station, camera, ship_pos, ship_angle)
        self.assertIsNotNone(projected)
        assert projected is not None
        pts, r_px, _ = projected
        self.assertLessEqual(r_px, CHASE_STATION_MAX_R_PX + 0.01)
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        self.assertLessEqual(max(math.hypot(x - cx, y - cy) for x, y in pts), CHASE_STATION_MAX_R_PX + 0.01)

    def test_chase_draw_structured_silhouette(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.render.station_viz import draw_space_station_chase

        station = SpaceStation(
            pos=Vec2(2000.0, 1600.0),
            anchor=Vec2(2000.0, 1600.0),
            faction=StationFaction.FRIENDLY,
            station_label="RELAY",
        )
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        rig = LightRig.for_play(theme="rift", camera_mode=CameraMode.CHASE)
        draw_space_station_chase(
            canvas,
            station,
            camera,
            ship_pos=Vec2(2000.0, 1730.0),
            ship_angle=-math.pi / 2.0,
            elapsed=0.5,
            rig=rig,
        )
        item_count = len(canvas.find_all())
        self.assertGreater(item_count, 12)
        self.assertLess(item_count, 65)
        root.destroy()

    def test_chase_arms_project_with_ring(self) -> None:
        from gravity_ho_matey.render.station_viz import _chase_project_locals, _chase_station_frame

        station = SpaceStation(
            pos=Vec2(2000.0, 1600.0),
            anchor=Vec2(2000.0, 1600.0),
            faction=StationFaction.HOSTILE,
            station_label="DOCK",
        )
        mesh = mesh_for_station(station)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = Vec2(2000.0, 1730.0)
        ship_angle = -math.pi / 2.0
        frame = _chase_station_frame(station, mesh, camera, ship_pos, ship_angle)
        self.assertIsNotNone(frame)
        assert frame is not None
        ring = _chase_project_locals(mesh.back_ring, station, frame)
        arms = [_chase_project_locals(arm, station, frame) for arm in mesh.mid_arms]
        self.assertGreaterEqual(len(ring), 8)
        self.assertEqual(len(arms), 4)
        ring_span = max(math.hypot(x - frame.cx, y - frame.cy) for x, y in ring)
        arm_reach = max(math.hypot(x - frame.cx, y - frame.cy) for arm in arms for x, y in arm)
        self.assertGreater(arm_reach, ring_span * 0.55)


if __name__ == "__main__":
    unittest.main()
