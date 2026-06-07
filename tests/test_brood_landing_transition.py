from __future__ import annotations

import unittest

try:
    import tkinter as tk
except tk.TclError:
    tk = None  # type: ignore[assignment]

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.brood_moon_layout import LANDING_CHARGE_SECONDS, build_brood_moon_orbital_layout
from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase
from gravity_ho_matey.scenes.play import PlayScene


@unittest.skipIf(tk is None, "Tk unavailable")
class BroodLandingTransitionTests(unittest.TestCase):
    def test_landing_cinematic_loads_gif_with_canvas_master(self) -> None:
        scene = PlayScene("brood_moon", CampaignState.new())
        layout = build_brood_moon_orbital_layout()
        toward = layout.planet.center - scene.world.ship.pos
        scene.world.ship.pos = layout.planet.center + toward.normalized() * (layout.planet.surface_radius + 100.0)
        bm = scene.world.brood_moon
        assert bm is not None
        bm.landing_charge = LANDING_CHARGE_SECONDS
        scene.world.update(0.016, ControlIntent(), interaction_hold=True)
        self.assertEqual(bm.phase, BroodPhase.LANDING_CINEMATIC)

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            scene._ensure_transition_sequence(canvas)
            self.assertIsNotNone(scene._transition_sequence)
            assert scene._transition_sequence is not None
            self.assertGreater(scene._transition_sequence.frame_count, 0)
            scene._tick_brood_transition(0.05)
        finally:
            root.destroy()

    def test_transition_overlay_draws_without_error(self) -> None:
        from gravity_ho_matey.gameplay.brood_moon_mission import BroodMoonState, BroodPhase
        from gravity_ho_matey.render.brood_moon_transition_overlay import BroodMoonTransitionOverlay

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            bm = BroodMoonState(phase=BroodPhase.LANDING_CINEMATIC, cinematic_kind="landing")
            BroodMoonTransitionOverlay().draw(canvas, bm=bm, frame_image=None)
            self.assertGreater(len(canvas.find_all()), 4)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
