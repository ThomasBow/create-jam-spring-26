from __future__ import annotations

import unittest

from levels import build_campaign_levels


class CampaignTests(unittest.TestCase):
    def test_campaign_has_multiple_levels(self) -> None:
        levels = build_campaign_levels()
        self.assertGreaterEqual(len(levels), 4)

    def test_each_level_has_tutorial_and_target(self) -> None:
        levels = build_campaign_levels()
        for level in levels:
            self.assertTrue(level.tutorial_lines)
            self.assertTrue(level.starting_runes)
            self.assertTrue(level.target_rune.strokes)

    def test_difficulty_is_non_decreasing(self) -> None:
        levels = build_campaign_levels()

        def score(level) -> int:
            return len(level.starting_runes) + len(level.target_rune.strokes)

        scores = [score(level) for level in levels]
        self.assertEqual(scores, sorted(scores))


if __name__ == "__main__":
    unittest.main()
