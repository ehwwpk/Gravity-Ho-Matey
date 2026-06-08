import unittest

from gravity_ho_matey.gameplay.space_junk_prefabs import MAX_PREFAB_VERTS, PREFAB_REGISTRY, instantiate_junk
from gravity_ho_matey.core.vector import Vec2


class SpaceJunkPrefabTests(unittest.TestCase):
    def test_registry_has_nine_distinct_prefabs(self) -> None:
        self.assertEqual(len(PREFAB_REGISTRY), 9)
        self.assertEqual(len(set(PREFAB_REGISTRY)), 9)

    def test_all_prefabs_have_positive_radius(self) -> None:
        for prefab_id in PREFAB_REGISTRY:
            junk = instantiate_junk(prefab_id, Vec2(100, 100))
            self.assertGreater(junk.approximate_radius(), 0.0, prefab_id)

    def test_vert_count_within_budget(self) -> None:
        for prefab in PREFAB_REGISTRY.values():
            self.assertLessEqual(len(prefab.local_verts), MAX_PREFAB_VERTS, prefab.id)

    def test_instantiate_copies_verts(self) -> None:
        a = instantiate_junk("girder_a", Vec2(0, 0))
        b = instantiate_junk("girder_a", Vec2(50, 50))
        self.assertIsNot(a.local_verts, b.local_verts)
        self.assertNotEqual(a.local_verts[0].x, b.local_verts[0].x + 50)


if __name__ == "__main__":
    unittest.main()
