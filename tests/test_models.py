from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from models import LevelData, RuneData


class RuneDataTests(unittest.TestCase):
    def test_merge_combines_strokes(self) -> None:
        a = RuneData("a", [((0, 0), (100, 100))])
        b = RuneData("b", [((0, 100), (100, 0))])

        merged = RuneData.merge(a, b)

        self.assertEqual(merged.name, "a+b")
        self.assertEqual(len(merged.strokes), 2)

    def test_attach_offsets_second_rune(self) -> None:
        a = RuneData("a", [((0, 0), (0, 100))])
        b = RuneData("b", [((25, 50), (75, 50))])

        attached = RuneData.attach(a, b, (1, 0))

        self.assertIn(((125, 50), (175, 50)), attached.strokes)
        self.assertEqual(attached.name, "a|b")

    def test_matches_is_order_independent(self) -> None:
        left = RuneData(
            "left",
            [
                ((0, 0), (100, 0)),
                ((50, 0), (50, 100)),
            ],
        )
        right = RuneData(
            "right",
            [
                ((50, 0), (50, 100)),
                ((0, 0), (100, 0)),
            ],
        )

        self.assertTrue(left.matches(right))


class LevelDataRoundTripTests(unittest.TestCase):
    def test_save_and_load_preserves_tutorial_lines(self) -> None:
        level = LevelData(
            level_name="tutorial",
            starting_runes=[RuneData("a", [((0, 0), (100, 100))])],
            target_rune=RuneData("t", [((0, 100), (100, 0))]),
            allow_merge=True,
            allow_attach=False,
            tutorial_lines=["Line 1", "Line 2"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "level.json"
            level.save(path)
            loaded = LevelData.load(path)

        self.assertEqual(loaded.level_name, "tutorial")
        self.assertEqual(loaded.tutorial_lines, ["Line 1", "Line 2"])
        self.assertFalse(loaded.allow_attach)


class ThreeRunePermutationTests(unittest.TestCase):
    """Test that all permutations of combining three runes can create a target."""

    def setUp(self) -> None:
        """Set up three base runes for testing."""
        # Simple base runes with distinct strokes
        self.rune_a = RuneData("A", [((0, 0), (50, 0))])
        self.rune_b = RuneData("B", [((0, 50), (50, 50))])
        self.rune_c = RuneData("C", [((0, 100), (50, 100))])

    def test_all_merge_permutations(self) -> None:
        """Test that all merge orderings produce results with same stroke count."""
        # (A + B) + C
        result1 = RuneData.merge(RuneData.merge(self.rune_a, self.rune_b), self.rune_c)
        # (A + C) + B
        result2 = RuneData.merge(RuneData.merge(self.rune_a, self.rune_c), self.rune_b)
        # (B + C) + A
        result3 = RuneData.merge(RuneData.merge(self.rune_b, self.rune_c), self.rune_a)

        # All should have 3 strokes (one from each rune)
        self.assertEqual(len(result1.strokes), 3)
        self.assertEqual(len(result2.strokes), 3)
        self.assertEqual(len(result3.strokes), 3)

    def test_merge_then_attach_permutations(self) -> None:
        """Test merge followed by attach with different orderings."""
        # (A + B) with C attached to it on right
        result1 = RuneData.attach(RuneData.merge(self.rune_a, self.rune_b), self.rune_c, (1, 0))
        # (A + C) with B attached to it on right
        result2 = RuneData.attach(RuneData.merge(self.rune_a, self.rune_c), self.rune_b, (1, 0))
        # (B + C) with A attached to it on right
        result3 = RuneData.attach(RuneData.merge(self.rune_b, self.rune_c), self.rune_a, (1, 0))

        # All should have 3 strokes
        self.assertEqual(len(result1.strokes), 3)
        self.assertEqual(len(result2.strokes), 3)
        self.assertEqual(len(result3.strokes), 3)

    def test_attach_then_merge_permutations(self) -> None:
        """Test attach followed by merge with different orderings."""
        # (A attached to B) + C
        result1 = RuneData.merge(RuneData.attach(self.rune_a, self.rune_b, (1, 0)), self.rune_c)
        # (A attached to C) + B
        result2 = RuneData.merge(RuneData.attach(self.rune_a, self.rune_c, (1, 0)), self.rune_b)
        # (B attached to C) + A
        result3 = RuneData.merge(RuneData.attach(self.rune_b, self.rune_c, (1, 0)), self.rune_a)

        # All should have 3 strokes
        self.assertEqual(len(result1.strokes), 3)
        self.assertEqual(len(result2.strokes), 3)
        self.assertEqual(len(result3.strokes), 3)

    def test_sequential_attach_permutations(self) -> None:
        """Test sequential attach operations with different base orderings."""
        # ((A attached to B on right) attached to C on down)
        result1 = RuneData.attach(RuneData.attach(self.rune_a, self.rune_b, (1, 0)), self.rune_c, (0, 1))
        # ((A attached to B on right) attached to C on left)
        result2 = RuneData.attach(RuneData.attach(self.rune_a, self.rune_b, (1, 0)), self.rune_c, (-1, 0))
        # ((A attached to C on right) attached to B on down)
        result3 = RuneData.attach(RuneData.attach(self.rune_a, self.rune_c, (1, 0)), self.rune_b, (0, 1))

        # All should have 3 strokes
        self.assertEqual(len(result1.strokes), 3)
        self.assertEqual(len(result2.strokes), 3)
        self.assertEqual(len(result3.strokes), 3)

    def test_attach_is_asymmetric(self) -> None:
        """Test that attach is directional: the anchor and attached rune matter.
        
        In the game, you can attach a single rune to a merged pair,
        but you cannot attach a merged pair to a single rune in the same way.
        """
        # Pattern 1: Create merge(A, B), then attach C to it on right
        merged_ab = RuneData.merge(self.rune_a, self.rune_b)
        result1 = RuneData.attach(merged_ab, self.rune_c, (1, 0))

        # Pattern 2: Reverse: attach merged(A, B) to C on right
        # This puts the merged result at the right of C, not C on the right of merge
        result2 = RuneData.attach(self.rune_c, merged_ab, (1, 0))

        # Both have 3 strokes but the offset of A and B vs C is different
        self.assertEqual(len(result1.strokes), 3)
        self.assertEqual(len(result2.strokes), 3)
        
        # They should NOT match because the strokes have different offsets
        # result1: A and B at origin, C offset right by +1
        # result2: C at origin, A and B offset right by +1
        self.assertFalse(result1.matches(result2))

    def test_valid_three_rune_combinations(self) -> None:
        """Test that valid three-rune combinations work correctly."""
        # All these operations are valid and produce runes with 3 strokes
        valid_results = [
            # Pure merges work with any order
            RuneData.merge(RuneData.merge(self.rune_a, self.rune_b), self.rune_c),
            RuneData.merge(self.rune_a, RuneData.merge(self.rune_b, self.rune_c)),
            # Attaching a single rune to a merge works
            RuneData.attach(RuneData.merge(self.rune_a, self.rune_b), self.rune_c, (1, 0)),
            RuneData.attach(RuneData.merge(self.rune_a, self.rune_c), self.rune_b, (0, 1)),
            # Attaching then merging works
            RuneData.merge(RuneData.attach(self.rune_a, self.rune_b, (1, 0)), self.rune_c),
            # Sequential attach works
            RuneData.attach(RuneData.attach(self.rune_a, self.rune_b, (1, 0)), self.rune_c, (0, 1)),
        ]

        # All should have exactly 3 strokes
        for result in valid_results:
            self.assertEqual(
                len(result.strokes),
                3,
                f"Result {result.name} should have 3 strokes but has {len(result.strokes)}"
            )

    def test_attach_order_produces_different_results(self) -> None:
        """Test that reversing attach order produces different stroke layouts."""
        # Attaching C to merged(A, B)
        anchor_first = RuneData.attach(RuneData.merge(self.rune_a, self.rune_b), self.rune_c, (1, 0))
        
        # Attaching the merge to C gives a different layout
        single_first = RuneData.attach(self.rune_c, RuneData.merge(self.rune_a, self.rune_b), (1, 0))
        
        # Both have 3 strokes but different positions
        self.assertEqual(len(anchor_first.strokes), 3)
        self.assertEqual(len(single_first.strokes), 3)
        
        # The stroke positions should be different (asymmetric attach)
        self.assertFalse(anchor_first.matches(single_first))

    def test_attach_with_different_directions(self) -> None:
        """Test that attaching with different directions produces different results."""
        rune_ab = RuneData.merge(self.rune_a, self.rune_b)

        # Attach C in 4 different directions
        up = RuneData.attach(rune_ab, self.rune_c, (0, -1))
        down = RuneData.attach(rune_ab, self.rune_c, (0, 1))
        left = RuneData.attach(rune_ab, self.rune_c, (-1, 0))
        right = RuneData.attach(rune_ab, self.rune_c, (1, 0))

        # All should have 3 strokes
        for result in [up, down, left, right]:
            self.assertEqual(len(result.strokes), 3)

        # Results in different directions should NOT be equal (strokes are offset differently)
        self.assertFalse(up.matches(down))
        self.assertFalse(left.matches(right))
        self.assertFalse(up.matches(left))


if __name__ == "__main__":
    unittest.main()
