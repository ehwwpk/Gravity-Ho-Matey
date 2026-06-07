from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.explosions import ExplosionKind, spawn_explosion
from gravity_ho_matey.render.enemy_mesh import build_enemy_skiff_mesh, mesh_for_enemy
from gravity_ho_matey.render.enemy_viz import CHASE_ENEMY_MAX_R_PX


class EnemyMeshTests(unittest.TestCase):
    def test_mesh_has_layers(self) -> None:
        mesh = build_enemy_skiff_mesh(seed=42)
        self.assertGreaterEqual(len(mesh.hull), 6)
        self.assertGreaterEqual(len(mesh.left_wing), 4)
        self.assertGreaterEqual(len(mesh.weapon_pod), 4)

    def test_mesh_seed_stable(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(10, 20), Vec2(30, 20)), pos=Vec2(10, 20))
        a = mesh_for_enemy(enemy)
        b = mesh_for_enemy(enemy)
        self.assertEqual(a.hull, b.hull)

    def test_chase_cap_sane(self) -> None:
        self.assertGreater(CHASE_ENEMY_MAX_R_PX, 20.0)


class EnemyChaseDrawTests(unittest.TestCase):
    def test_patrol_enemy_chase_draw_does_not_raise(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.camera import CameraMode
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        root = tk.Tk()
        root.withdraw()
        try:
            scene = PlayScene("rift", CampaignState.new())
            ship = scene.world.ship.pos
            scene.world.enemies.append(
                PatrolEnemy(
                    waypoints=(ship + Vec2(180, 0), ship + Vec2(280, 0)),
                    pos=ship + Vec2(180, 0),
                )
            )
            scene.camera.cycle_mode()
            self.assertIs(scene.camera.mode, CameraMode.CHASE)
            canvas = tk.Canvas(root, width=960, height=640)
            TkRenderer(canvas).draw_world(
                scene.world,
                scene.campaign,
                scene.camera,
                scene.gravity_field,
            )
            self.assertGreater(len(canvas.find_all()), 0)
        finally:
            root.destroy()


class NovaBlastTests(unittest.TestCase):
    def test_nova_carries_aoe_radius(self) -> None:
        fx = spawn_explosion(ExplosionKind.NOVA_BLAST, Vec2(0, 0), aoe_radius_world=54.0)
        self.assertEqual(fx.kind, ExplosionKind.NOVA_BLAST)
        self.assertAlmostEqual(fx.aoe_radius_world, 54.0)
        self.assertGreater(len(fx.particles), 8)


if __name__ == "__main__":
    unittest.main()
