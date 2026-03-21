# Rune Crafter

Rune Crafter is a small puzzle game where you drag runes, snap them together, and use merge/attach operations to forge a target master rune.

## Run

```bash
uv run main.py
```

## Controls

### Level Mode (default startup)

- Left mouse: drag runes
- M: merge highlighted snapping runes
- A: attach highlighted snapping runes
- R: restart current level
- N: advance to next level after a win
- E: toggle editor mode
- Esc: quit

### Rune Editor Mode

- Left mouse: place first point, then second point to create stroke
- Right mouse: cancel pending point
- Use the panel to name and save runes

## Campaign

The game now starts directly in level mode and includes a guided 4-level campaign:

1. Apprentice Merge
2. Guided Attachment
3. Combo Craft
4. Master Rune Forge

Each level includes in-game tutorial hints and increases puzzle complexity.

## Tests

Run tests with:

```bash
uv run python -m unittest discover -s tests -v
```
