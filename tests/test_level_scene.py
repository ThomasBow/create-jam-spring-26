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
        # Position moved below anchor without overlap, so it detects bottom attach
        moved = RuneNode(RuneData("gamma", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + SLAB_SIZE))
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
        # Position moved to the left of anchor without overlap, so it detects left attach
        moved = RuneNode(RuneData("moved", [((0.0, 0.0), (1.0, 1.0))]), (300 - SLAB_SIZE, 220))
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

    def test_snap_to_merged_composite(self) -> None:
        """Test that a single rune can snap to a merged composite."""
        scene = self._make_scene()

        # Create a merged composite rune
        a_data = RuneData("a", [((0.0, 0.0), (0.5, 0.5))])
        b_data = RuneData("b", [((0.5, 0.5), (1.0, 1.0))])
        merged_data = RuneData.merge(a_data, b_data)
        
        # Create scene with merged composite and a single rune nearby
        merged_node = RuneNode(merged_data, (200, 200))
        c_node = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + SLAB_SIZE))
        
        scene.rune_nodes = [merged_node, c_node]
        scene.last_moved_node = c_node
        
        # Check if snap detects the attachment
        scene._check_snap_all()
        
        # Should detect a snap with c attached to merged_node
        self.assertIsNotNone(scene.active_snap, "Snap not detected when c is adjacent to merged composite")
        assert scene.active_snap is not None  # for type checker
        anchor, attached, direction = scene.active_snap
        
        # The anchor should be the merged composite, attached should be c
        self.assertIs(anchor, merged_node)
        self.assertIs(attached, c_node)
        # Direction should be downward since c is below
        self.assertEqual(direction, (0, 1))

    def test_apply_attach_to_merged_composite(self) -> None:
        """Test that attaching a rune to a merged composite works correctly."""
        scene = self._make_scene()

        # Create a merged composite rune
        a_data = RuneData("a", [((0.0, 0.0), (0.5, 0.5))])
        b_data = RuneData("b", [((0.5, 0.5), (1.0, 1.0))])
        merged_data = RuneData.merge(a_data, b_data)
        
        # Create scene with merged composite and a single rune
        merged_node = RuneNode(merged_data, (200, 200))
        c_node = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + SLAB_SIZE))
        
        scene.rune_nodes = [merged_node, c_node]
        scene.last_moved_node = c_node
        
        # Set up the snap
        scene._check_snap_all()
        self.assertIsNotNone(scene.active_snap)
        
        # Apply the attach operation
        scene.handle_key(pygame.K_a)
        
        # Should result in 1 node (the composite with the attachment)
        self.assertEqual(len(scene.rune_nodes), 1)
        
        result_node = scene.rune_nodes[0]
        # Should have 3 strokes: 2 from merged + 1 from c
        self.assertEqual(len(result_node.rune_data.strokes), 3)
        
        # The last_moved_node should be the result
        self.assertIs(scene.last_moved_node, result_node)

    def test_attach_merged_composite_to_single_rune(self) -> None:
        """Test that attaching a merged composite to a single rune works correctly."""
        scene = self._make_scene()

        # Create a merged composite rune
        a_data = RuneData("a", [((0.0, 0.0), (0.5, 0.5))])
        b_data = RuneData("b", [((0.5, 0.5), (1.0, 1.0))])
        merged_data = RuneData.merge(a_data, b_data)
        
        # Create scene with single rune and merged composite
        # The merged composite is the "moved" rune this time
        c_node = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (200, 200))
        merged_node = RuneNode(merged_data, (200, 200 + SLAB_SIZE))
        
        scene.rune_nodes = [c_node, merged_node]
        scene.last_moved_node = merged_node  # merged is the moved rune
        
        # Check if snap detects the attachment
        scene._check_snap_all()
        
        # Should detect a snap
        self.assertIsNotNone(scene.active_snap, "Snap not detected when merged composite is adjacent to single rune")
        assert scene.active_snap is not None  # for type checker
        anchor, attached, direction = scene.active_snap
        
        # Since merged_node is the last_moved, it should be the attached rune
        # And c_node should be the anchor
        self.assertIs(anchor, c_node)
        self.assertIs(attached, merged_node)
        self.assertEqual(direction, (0, 1))
        
        # Now apply the attach operation
        scene.handle_key(pygame.K_a)
        
        # Should result in 1 node (c with merged attached to it)
        self.assertEqual(len(scene.rune_nodes), 1)
        
        result_node = scene.rune_nodes[0]
        # Should have 3 strokes: 1 from c + 2 from merged
        self.assertEqual(len(result_node.rune_data.strokes), 3)

    def test_sequential_snap_after_merge_and_move(self) -> None:
        """Test snapping after a merge, when moving the merged composite."""
        scene = self._make_scene()

        a = RuneNode(RuneData("a", [((0.0, 0.0), (0.5, 0.5))]), (200, 200))
        b = RuneNode(RuneData("b", [((0.5, 0.5), (1.0, 1.0))]), (200 + SLAB_SIZE, 200))
        # c is at a position where it won't overlap with merged node
        c = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + 2 * SLAB_SIZE))

        scene.rune_nodes = [a, b, c]
        scene.last_moved_node = b

        # First, merge a and b
        scene._check_snap_all()
        self.assertIsNotNone(scene.active_snap)
        scene.handle_key(pygame.K_m)

        self.assertEqual(len(scene.rune_nodes), 2)
        merged_node = scene.last_moved_node
        self.assertIsNotNone(merged_node)

        # Now move the merged node to be adjacent to c (one SLAB_SIZE below)
        # Position it exactly at the snap distance without overlap
        merged_node.position = pygame.Vector2(200, 200 + SLAB_SIZE)
        scene.last_moved_node = merged_node

        scene._check_snap_all()

        # Should detect snap between merged and c
        self.assertIsNotNone(scene.active_snap, "No snap detected after repositioning merged node")
        snap_before = scene.active_snap
        assert snap_before is not None  # for type checker
        anchor, attached, direction = snap_before
        
        # merged should be attached, c should be anchor (since merged is the moved one)
        self.assertIs(anchor, c, f"Anchor should be c but is {anchor.rune_data.name}")
        self.assertIs(attached, merged_node, f"Attached should be merged but is {attached.rune_data.name}")
        # Direction should be upward since c is above merged node
        self.assertEqual(direction, (0, -1), f"Direction should be (0, -1) for up, but is {direction}")
        
        # Apply the attach
        scene.handle_key(pygame.K_a)
        
        # Should result in 1 node with 3 strokes
        self.assertEqual(len(scene.rune_nodes), 1, f"Expected 1 rune node after attach, got {len(scene.rune_nodes)}: {[n.rune_data.name for n in scene.rune_nodes]}")
        result = scene.rune_nodes[0]
        self.assertEqual(len(result.rune_data.strokes), 3)

    def test_snap_anchor_attached_consistency_with_merged(self) -> None:
        """Test that anchor/attached assignment is correct for merged composites.
        
        Bug check: Ensure that snap returns (anchor, attached, direction) correctly
        so that attach(anchor, attached, direction) will work.
        """
        scene = self._make_scene()

        # Create a merged composite
        a_data = RuneData("a", [((0.0, 0.0), (0.5, 0.5))])
        b_data = RuneData("b", [((0.5, 0.5), (1.0, 1.0))])
        merged_data = RuneData.merge(a_data, b_data)
        
        merged_node = RuneNode(merged_data, (200, 200))
        # Position c adjacent to merged (one SLAB_SIZE below)
        c_node = RuneNode(RuneData("c", [((0.0, 0.0), (1.0, 1.0))]), (200, 200 + SLAB_SIZE))
        
        scene.rune_nodes = [merged_node, c_node]
        scene.last_moved_node = merged_node
        
        scene._check_snap_all()
        self.assertIsNotNone(scene.active_snap, "Snap not detected")
        assert scene.active_snap is not None  # for type checker        
        anchor, attached, direction = scene.active_snap
        
        # Verify anchor/attached assignment
        self.assertIs(anchor, c_node, "Anchor should be c_node (stationary)")
        self.assertIs(attached, merged_node, "Attached should be merged_node (moved)")
        
        # Verify attach can be applied
        scene.handle_key(pygame.K_a)
        self.assertEqual(len(scene.rune_nodes), 1, "Attach should combine runes into 1 node")


class LevelSceneWinPermutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _make_scene_with_target(self, target: RuneData) -> LevelScene:
        level = LevelData(
            "win-permutations",
            starting_runes=[target.duplicate()],
            target_rune=target,
        )
        return LevelScene(pygame.Surface((720, 500)), level)

    def test_check_win_true_for_matching_three_rune_permutations(self) -> None:
        a = RuneData("A", [((0.0, 0.0), (0.5, 0.0))])
        b = RuneData("B", [((0.0, 0.5), (0.5, 0.5))])
        c = RuneData("C", [((0.0, 1.0), (0.5, 1.0))])

        # Define one canonical target and verify equivalent permutations win.
        target = RuneData.merge(RuneData.merge(a, b), c)
        scene = self._make_scene_with_target(target)

        permutations = [
            RuneData.merge(RuneData.merge(a, b), c),
            RuneData.merge(RuneData.merge(a, c), b),
            RuneData.merge(RuneData.merge(b, c), a),
            RuneData.merge(a, RuneData.merge(b, c)),
            RuneData.merge(b, RuneData.merge(a, c)),
            RuneData.merge(c, RuneData.merge(a, b)),
        ]

        for idx, combo in enumerate(permutations):
            scene.won = False
            scene.rune_nodes = [RuneNode(combo, (200, 200))]
            scene._check_win()
            self.assertTrue(scene.won, f"Permutation {idx} should win")

    def test_check_win_false_for_wrong_three_rune_combination(self) -> None:
        a = RuneData("A", [((0.0, 0.0), (0.5, 0.0))])
        b = RuneData("B", [((0.0, 0.5), (0.5, 0.5))])
        c = RuneData("C", [((0.0, 1.0), (0.5, 1.0))])

        target = RuneData.attach(RuneData.merge(a, b), c, (1, 0))
        scene = self._make_scene_with_target(target)

        # Same base runes, but different composition/layout than target.
        wrong_combo = RuneData.attach(c, RuneData.merge(a, b), (1, 0))

        scene.won = False
        scene.rune_nodes = [RuneNode(wrong_combo, (200, 200))]
        scene._check_win()

        self.assertFalse(scene.won)


if __name__ == "__main__":
    unittest.main()
