from __future__ import annotations

from models import LevelData, RuneData


# Base rune vocabulary used by the campaign.
RUNE_ALPHA = RuneData(
    name="alpha",
    strokes=[
        ((25, 20), (75, 20)),
        ((25, 20), (50, 75)),
        ((75, 20), (50, 75)),
    ],
)

RUNE_BETA = RuneData(
    name="beta",
    strokes=[
        ((50, 20), (50, 80)),
        ((20, 50), (80, 50)),
    ],
)

RUNE_GAMMA = RuneData(
    name="gamma",
    strokes=[
        ((20, 75), (80, 75)),
        ((20, 75), (50, 25)),
        ((80, 75), (50, 25)),
    ],
)

RUNE_DELTA = RuneData(
    name="delta",
    strokes=[
        ((25, 25), (75, 25)),
        ((25, 25), (25, 75)),
        ((25, 75), (75, 75)),
    ],
)

RUNE_SIGMA = RuneData(
    name="sigma",
    strokes=[
        ((20, 20), (80, 20)),
        ((80, 20), (20, 80)),
        ((20, 80), (80, 80)),
    ],
)


def build_campaign_levels() -> list[LevelData]:
    """Create an ordered campaign with increasing puzzle complexity."""

    level_1_target = RuneData.merge(RUNE_ALPHA, RUNE_BETA)
    level_1_target.name = "alpha+beta"

    level_2_target = RuneData.attach(RUNE_ALPHA, RUNE_GAMMA, (1, 0))
    level_2_target.name = "alpha|gamma"

    left_pair = RuneData.merge(RUNE_ALPHA, RUNE_BETA)
    level_3_target = RuneData.attach(left_pair, RUNE_GAMMA, (0, 1))
    level_3_target.name = "(alpha+beta)|gamma"

    first_pair = RuneData.attach(RUNE_DELTA, RUNE_BETA, (0, -1))
    second_pair = RuneData.attach(RUNE_GAMMA, RUNE_SIGMA, (1, 0))
    level_4_target = RuneData.merge(first_pair, second_pair)
    level_4_target.name = "master-rune"

    return [
        LevelData(
            level_name="1. Apprentice Merge",
            starting_runes=[RUNE_ALPHA.duplicate(), RUNE_BETA.duplicate()],
            target_rune=level_1_target,
            allow_merge=True,
            allow_attach=False,
            tutorial_lines=[
                "Drag one rune so its edge glows green near the other.",
                "Press M to merge the highlighted pair.",
                "Match the target rune shown on the right.",
            ],
        ),
        LevelData(
            level_name="2. Guided Attachment",
            starting_runes=[RUNE_ALPHA.duplicate(), RUNE_GAMMA.duplicate()],
            target_rune=level_2_target,
            allow_merge=False,
            allow_attach=True,
            tutorial_lines=[
                "Attach moves one rune to a neighboring grid slab.",
                "Snap the runes and press A to attach.",
                "Try different sides until your shape matches the target.",
            ],
        ),
        LevelData(
            level_name="3. Combo Craft",
            starting_runes=[
                RUNE_ALPHA.duplicate(),
                RUNE_BETA.duplicate(),
                RUNE_GAMMA.duplicate(),
            ],
            target_rune=level_3_target,
            allow_merge=True,
            allow_attach=True,
            tutorial_lines=[
                "This level needs more than one operation.",
                "A common route: merge first, then attach the result.",
                "You can restart with R if your build drifts off target.",
            ],
        ),
        LevelData(
            level_name="4. Master Rune Forge",
            starting_runes=[
                RUNE_ALPHA.duplicate(),
                RUNE_BETA.duplicate(),
                RUNE_GAMMA.duplicate(),
                RUNE_DELTA.duplicate(),
                RUNE_SIGMA.duplicate(),
            ],
            target_rune=level_4_target,
            allow_merge=True,
            allow_attach=True,
            tutorial_lines=[
                "Final exam: build sub-shapes, then combine them.",
                "Use both A and M. Spatial planning matters now.",
                "Create the master rune to finish the campaign.",
            ],
        ),
    ]
