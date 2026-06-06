import unittest


class ImportSmokeTests(unittest.TestCase):
    def test_main_entrypoint_imports(self) -> None:
        from gravity_ho_matey.main import run

        self.assertTrue(callable(run))

    def test_app_and_scene_graph_import(self) -> None:
        from gravity_ho_matey.app import GravityHoMateyApp
        from gravity_ho_matey.scenes.game_flow import start_play
        from gravity_ho_matey.scenes.title import TitleScene

        self.assertIsNotNone(GravityHoMateyApp)
        self.assertIsNotNone(TitleScene)
        scene = start_play("cove")
        self.assertEqual(scene.level_id, "cove")


if __name__ == "__main__":
    unittest.main()
