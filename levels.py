from __future__ import annotations

import json
from pathlib import Path

from models import LevelData, RuneData

BASE_DIR = Path(__file__).resolve().parent
RUNE_CATALOG_PATH = BASE_DIR / "runes" / "catalog.json"
CAMPAIGN_PATH = BASE_DIR / "levels" / "campaign.json"


def _to_strokes(raw_strokes: list[list[list[int]]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    return [
        ((int(s[0][0]), int(s[0][1])), (int(s[1][0]), int(s[1][1])))
        for s in raw_strokes
    ]


def _load_rune_catalog(path: Path = RUNE_CATALOG_PATH) -> dict[str, RuneData]:
    with open(path) as f:
        data = json.load(f)

    catalog: dict[str, RuneData] = {}
    for item in data["runes"]:
        rune = RuneData(name=item["name"], strokes=_to_strokes(item["strokes"]))
        catalog[rune.name] = rune
    return catalog


def _parse_target(raw_target: dict, catalog: dict[str, RuneData]) -> RuneData:
    target_name = raw_target.get("name", "target")

    if "rune_name" in raw_target:
        base_name = raw_target["rune_name"]
        if base_name not in catalog:
            raise ValueError(f"Unknown target rune_name: {base_name}")
        rune = catalog[base_name].duplicate()
        rune.name = target_name
        return rune

    if "strokes" in raw_target:
        return RuneData(name=target_name, strokes=_to_strokes(raw_target["strokes"]))

    raise ValueError("target_rune must include either 'rune_name' or 'strokes'")


def build_campaign_levels(
    campaign_path: Path = CAMPAIGN_PATH,
    rune_catalog_path: Path = RUNE_CATALOG_PATH,
) -> list[LevelData]:
    """Load the campaign from JSON for data-driven scalability."""

    catalog = _load_rune_catalog(rune_catalog_path)
    with open(campaign_path) as f:
        campaign_data = json.load(f)

    levels: list[LevelData] = []
    for raw_level in campaign_data["levels"]:
        starting: list[RuneData] = []
        for name in raw_level["starting_runes"]:
            if name not in catalog:
                raise ValueError(f"Unknown starting rune: {name}")
            starting.append(catalog[name].duplicate())

        target = _parse_target(raw_level["target_rune"], catalog)

        levels.append(
            LevelData(
                level_name=raw_level["level_name"],
                starting_runes=starting,
                target_rune=target,
                allow_merge=raw_level.get("allow_merge", True),
                allow_attach=raw_level.get("allow_attach", True),
                tutorial_lines=raw_level.get("tutorial_lines", []),
            )
        )

    return levels
