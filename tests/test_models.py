from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from models import LevelData, RuneData


class RuneDataTests(unittest.TestCase):
    def test_merge_combines_strokes(self) -> None:
        a = RuneData("a", [((0.0, 0.0), (1.0, 1.0))])
        b = RuneData("b", [((0.0, 1.0), (1.0, 0.0))])

        merged = RuneData.merge(a, b)

        self.assertEqual(merged.name, "a+b")
        self.assertEqual(len(merged.strokes), 2)

    def test_attach_offsets_second_rune(self) -> None:
        a = RuneData("a", [((0.0, 0.0), (0.0, 1.0))])
        b = RuneData("b", [((0.25, 0.5), (0.75, 0.5))])

        attached = RuneData.attach(a, b, (1, 0))

        self.assertIn(((1.25, 0.5), (1.75, 0.5)), attached.strokes)
        self.assertEqual(attached.name, "a|b")

    def test_matches_is_order_independent(self) -> None:
        left = RuneData(
            "left",
            [
                ((0.0, 0.0), (1.0, 0.0)),
                ((0.5, 0.0), (0.5, 1.0)),
            ],
        )
        right = RuneData(
            "right",
            [
                ((0.5, 0.0), (0.5, 1.0)),
                ((0.0, 0.0), (1.0, 0.0)),
            ],
        )

        self.assertTrue(left.matches(right))


class LevelDataRoundTripTests(unittest.TestCase):
    def test_save_and_load_preserves_tutorial_lines(self) -> None:
        level = LevelData(
            level_name="tutorial",
            starting_runes=[RuneData("a", [((0.0, 0.0), (1.0, 1.0))])],
            target_rune=RuneData("t", [((0.0, 1.0), (1.0, 0.0))]),
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


if __name__ == "__main__":
    unittest.main()
