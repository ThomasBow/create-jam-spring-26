from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


# A stroke is two (x, y) points in normalised 0..1 space
Point = tuple[float, float]
Stroke = tuple[Point, Point]


@dataclass
class RuneData:
    name: str
    strokes: list[Stroke] = field(default_factory=list)

    def duplicate(self) -> RuneData:
        return RuneData(name=self.name, strokes=list(self.strokes))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"name": self.name, "strokes": self.strokes}, f, indent=2)

    @staticmethod
    def load(path: Path) -> RuneData:
        with open(path) as f:
            data = json.load(f)
        strokes: list[Stroke] = [
            ((s[0][0], s[0][1]), (s[1][0], s[1][1])) for s in data["strokes"]
        ]
        return RuneData(name=data["name"], strokes=strokes)

    def matches(self, other: RuneData) -> bool:
        """Compare runes by their strokes, order and endpoint direction independent.
        Also normalizes stroke positions so attachment order doesn't matter."""
        # Normalize strokes: ensure endpoints are consistently ordered and translate to canonical position
        def normalize_strokes(strokes: list[Stroke]) -> set[Stroke]:
            if not strokes:
                return set()
            
            # Find bounding box
            all_points = []
            for p1, p2 in strokes:
                all_points.extend([p1, p2])
            
            min_x = min(p[0] for p in all_points)
            min_y = min(p[1] for p in all_points)
            
            # Normalize: translate to origin and ensure consistent point ordering
            normalized = set()
            for stroke in strokes:
                p1, p2 = stroke
                # Translate to canonical position
                p1_norm = (p1[0] - min_x, p1[1] - min_y)
                p2_norm = (p2[0] - min_x, p2[1] - min_y)
                # Ensure consistent ordering of endpoints
                if p1_norm <= p2_norm:
                    normalized.add((p1_norm, p2_norm))
                else:
                    normalized.add((p2_norm, p1_norm))
            return normalized
        
        return normalize_strokes(self.strokes) == normalize_strokes(other.strokes)

    # --- Operations ---

    @staticmethod
    def merge(a: RuneData, b: RuneData) -> RuneData:
        """Combine strokes of two runes onto one slab."""
        return RuneData(
            name=f"{a.name}+{b.name}",
            strokes=a.strokes + b.strokes,
        )

    @staticmethod
    def attach(a: RuneData, b: RuneData, direction: tuple[int, int]) -> RuneData:
        """
        Attach b to an edge of a.
        direction: (1,0)=right, (-1,0)=left, (0,1)=down, (0,-1)=up
        b's strokes are offset by direction in normalised space.
        """
        dx, dy = direction
        shifted: list[Stroke] = [
            (
                (s[0][0] + dx, s[0][1] + dy),
                (s[1][0] + dx, s[1][1] + dy),
            )
            for s in b.strokes
        ]
        return RuneData(
            name=f"{a.name}|{b.name}",
            strokes=a.strokes + shifted,
        )


@dataclass
class LevelData:
    level_name: str
    starting_runes: list[RuneData]
    target_rune: RuneData
    allow_merge: bool = True
    allow_attach: bool = True
    tutorial_lines: list[str] = field(default_factory=list)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(
                {
                    "level_name": self.level_name,
                    "allow_merge": self.allow_merge,
                    "allow_attach": self.allow_attach,
                    "tutorial_lines": self.tutorial_lines,
                    "starting_runes": [
                        {"name": r.name, "strokes": r.strokes}
                        for r in self.starting_runes
                    ],
                    "target_rune": {
                        "name": self.target_rune.name,
                        "strokes": self.target_rune.strokes,
                    },
                },
                f,
                indent=2,
            )

    @staticmethod
    def load(path: Path) -> LevelData:
        with open(path) as f:
            data = json.load(f)

        def parse_rune(d: dict) -> RuneData:
            return RuneData(
                name=d["name"],
                strokes=[
                    ((s[0][0], s[0][1]), (s[1][0], s[1][1])) for s in d["strokes"]
                ],
            )

        return LevelData(
            level_name=data["level_name"],
            allow_merge=data.get("allow_merge", True),
            allow_attach=data.get("allow_attach", True),
            tutorial_lines=data.get("tutorial_lines", []),
            starting_runes=[parse_rune(r) for r in data["starting_runes"]],
            target_rune=parse_rune(data["target_rune"]),
        )
