import unittest

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.explosions import ExplosionKind
from gravity_ho_matey.gameplay.jewel_config import TREASURY_FLASH_SECONDS
from gravity_ho_matey.gameplay.jewel_pickup import spawn_scattered_jewels
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay
from gravity_ho_matey.scenes.play import PlayScene


class _FakeInput:
    def to_control_intent(self) -> ControlIntent:
        return ControlIntent()


class _FakeHost:
    input_state = _FakeInput()

    def set_scene(self, _scene: object) -> None:
        pass


class JewelHudTests(unittest.TestCase):
    def test_play_scene_flashes_treasury_on_collect(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene._on_jewels_collected_hud(3)
        self.assertAlmostEqual(scene.treasury_flash_ttl, TREASURY_FLASH_SECONDS)

    def test_treasury_flash_expires(self) -> None:
        scene = PlayScene("solar", CampaignState.new())
        scene._on_jewels_collected_hud(1)
        scene.update(_FakeHost(), TREASURY_FLASH_SECONDS + 0.1)
        self.assertEqual(scene.treasury_flash_ttl, 0.0)

    def test_playfield_top_ignores_jewel_collect(self) -> None:
        top = SciFiHudOverlay.playfield_top()
        self.assertEqual(top, float(SciFiHudOverlay.PANEL_H))

    def test_jewel_collect_spawns_spark_fx(self) -> None:
        world = build_level("cove")
        wire_world_for_campaign(world, CampaignState.new())
        world.jewels = spawn_scattered_jewels(world.ship.pos, 1)
        for _ in range(40):
            world.update(0.05, ControlIntent())
            if not world.jewels:
                break
        kinds = {fx.kind for fx in world.explosions.active}
        self.assertIn(ExplosionKind.JEWEL_COLLECT, kinds)

    def test_treasury_hud_draw_smoke(self) -> None:
        try:
            import tkinter as tk

            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        overlay = SciFiHudOverlay()
        world = build_level("solar")
        campaign = CampaignState.new()
        campaign.jewels = 12
        overlay.draw(
            canvas,
            world,
            campaign,
            treasury_flash_ttl=TREASURY_FLASH_SECONDS,
        )
        root.destroy()


if __name__ == "__main__":
    unittest.main()
