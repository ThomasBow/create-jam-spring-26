from __future__ import annotations

import os
import unittest

import pygame

from level_scene import LevelScene
from models import LevelData, RuneData
from rune_node import RuneNode, SLAB_SIZE


class LevelSceneSnapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _make_scene(self) -> LevelScene:
        a = RuneData("a", [((0.0, 0.0), (1.0, 0.0)), ((0.5, 0.0), (0.5, 1.0))])
        b = RuneData("b", [((0.0, 0.0), (1.0, 1.0))])
        level = LevelData("test", [a, b], target_rune=RuneData.merge(a, b))
        return LevelScene(pygame.Surface((720, 500)), level)

    def test_snap_prefers_recently_moved_rune_as_attached(self) -> None:
        scene = self._make_scene()

        anchor = RuneNode(RuneData("combo", [((0.0, 0.0), (1.0, 0.0)), ((0.0, 0.5), (1.0, 0.5))]), (200, 200))
        moved = RuneNode(RuneData("gamma", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + SLAB_SIZE - 8))
        scene.rune_nodes = [anchor, moved]
        scene.last_moved_node = moved

        scene._check_snap_all()

        self.assertIsNotNone(scene.active_snap)
        snap_anchor, snap_attached, direction = scene.active_snap  # type: ignore[misc]
        self.assertIs(snap_anchor, anchor)
        self.assertIs(snap_attached, moved)
        self.assertEqual(direction, (0, 1))

    def test_snap_detects_left_side_without_direction_bias(self) -> None:
        scene = self._make_scene()

        anchor = RuneNode(RuneData("anchor", [((0.0, 0.0), (1.0, 0.0))]), (300, 220))
        moved = RuneNode(RuneData("moved", [((0.0, 0.0), (1.0, 1.0))]), (300 - SLAB_SIZE + 6, 220 + 3))
        scene.rune_nodes = [anchor, moved]
        scene.last_moved_node = moved

        scene._check_snap_all()

        self.assertIsNotNone(scene.active_snap)
        _, _, direction = scene.active_snap  # type: ignore[misc]
        self.assertEqual(direction, (-1, 0))

    def test_overlap_enables_merge_candidate(self) -> None:
        scene = self._make_scene()

        anchor = RuneNode(RuneData("anchor", [((0.0, 0.0), (1.0, 0.0))]), (280, 240))
        moved = RuneNode(
            RuneData("moved", [((0.0, 0.0), (1.0, 1.0))]),
            (284, 244),
        )
        scene.rune_nodes = [anchor, moved]
        scene.last_moved_node = moved

        scene._check_snap_all()

        self.assertIsNotNone(scene.active_snap)
        _, _, direction = scene.active_snap  # type: ignore[misc]
        self.assertEqual(direction, (0, 0))

        before = len(scene.rune_nodes)
        scene.handle_key(pygame.K_a)
        self.assertEqual(len(scene.rune_nodes), before)

        scene.handle_key(pygame.K_m)
        self.assertEqual(len(scene.rune_nodes), 1)

    def test_only_last_moved_rune_is_used_for_snap(self) -> None:
        scene = self._make_scene()

        # a and b are close to each other, but c is the last moved rune.
        a = RuneNode(RuneData("a", [((0.0, 0.0), (1.0, 0.0))]), (140, 140))
        b = RuneNode(RuneData("b", [((0.0, 0.0), (1.0, 1.0))]), (140 + SLAB_SIZE - 6, 140))
        c = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (360, 320))

        scene.rune_nodes = [a, b, c]
        scene.last_moved_node = c

        scene._check_snap_all()

        self.assertIsNone(scene.active_snap)
        self.assertFalse(a.highlighted)
        self.assertFalse(b.highlighted)


if __name__ == "__main__":
    unittest.main()
