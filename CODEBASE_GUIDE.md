# Rune Crafter Codebase Guide

This guide describes how the project is structured and how the game currently works.

## 1. High-Level Architecture

The project is a small pygame application with two runtime scenes:

- Level mode: play campaign puzzles by moving, merging, and attaching runes.
- Editor mode: draw and save rune definitions.

Core architecture style:

- Data model layer in `models.py`.
- Scene/controller layer in `main.py`, `level_scene.py`, `rune_editor.py`.
- Visual/game object layer in `rune_node.py`.
- Static campaign definition in `levels.py`.
- Unit tests in `tests/`.

## 2. Entry Point and Runtime Loop

File: `main.py`

Main responsibilities:

- Initializes pygame and creates the window.
- Builds campaign levels via `build_campaign_levels()`.
- Starts in level mode (not editor mode).
- Handles global controls:
  - `Esc` quit
  - `E` toggle level/editor
- Handles level controls:
  - `R` restart current level
  - `N` next level (only after win)
  - `M`/`A` are delegated to `LevelScene.handle_key()`
- Routes per-frame event handling and drawing to the active scene.

Runtime flow each frame:

1. Process input events.
2. Route event to current scene.
3. Draw current scene.
4. Draw bottom mode indicator.
5. `pygame.display.flip()` and tick clock.

## 3. Data Model Layer

File: `models.py`

### `RuneData`

Represents a rune as line segments in normalized space.

- `name: str`
- `strokes: list[Stroke]`
- `Stroke = ((x1, y1), (x2, y2))`

Key behavior:

- `duplicate()` creates a shallow duplicate for independent editing.
- `matches(other)` compares sorted stroke lists so order does not matter.
- `merge(a, b)` combines stroke lists directly.
- `attach(a, b, direction)` offsets rune `b` strokes by unit direction and appends them.

### `LevelData`

Represents one puzzle level.

- `level_name`
- `starting_runes`
- `target_rune`
- `allow_merge`
- `allow_attach`
- `tutorial_lines`

Also supports JSON `save()` and `load()`.

## 4. Campaign Definition

File: `levels.py`

Campaign is hardcoded by `build_campaign_levels()` and returns a list of `LevelData`.

Current campaign:

1. Apprentice Merge
2. Guided Attachment
3. Combo Craft
4. Master Rune Forge

Notes:

- Difficulty is designed to increase by more pieces/operations.
- Level targets are built by calling `RuneData.merge()` and `RuneData.attach()`.
- Starting runes use `.duplicate()` to avoid accidental shared-state mutation.

## 5. Level Gameplay Scene

File: `level_scene.py`

`LevelScene` manages puzzle gameplay.

### Setup and layout

- Spawns interactive runes in a wrapped grid in the workspace area.
- Creates a non-interactive target node in the right panel.
- Uses helper rects:
  - workspace rectangle
  - target panel rectangle
  - tutorial panel rectangle

### Input handling

- Dragging is managed by each `RuneNode`.
- Runes are clamped to workspace bounds during drag.
- On mouse release, scene stores `last_moved_node` and recomputes snap candidate.

### Snap selection model (current behavior)

The active operation candidate is intentionally narrow:

- Only pairs involving `last_moved_node` are considered.
- Candidate is selected as the closest valid relation to one other rune.
- Edge-adjacent relations use directions `(1,0)`, `(-1,0)`, `(0,1)`, `(0,-1)`.
- Overlap candidate `(0,0)` is allowed for merge-only behavior.
- Attach is blocked for overlap candidate.

This is stored in:

- `active_snap: (anchor_node, moved_node, direction) | None`

### Operations

- Merge (`M`): `_do_merge(anchor, moved)` -> new node with combined strokes.
- Attach (`A`): `_do_attach(anchor, moved, direction)` -> new node with shifted moved strokes.

After operations:

- Original nodes removed.
- New node appended.
- `last_moved_node` becomes new node.
- Snap recomputed.
- Win check executed.

### Win condition

- Player wins when any node matches `level_data.target_rune` by `RuneData.matches()`.

### UI rendering

Draw passes include:

- Header bar with level index and controls.
- Workspace panel.
- Right-side target panel.
- Bottom tutorial panel.
- Rune nodes and labels.
- Active moved-node focus pulse.
- Attach-edge preview lines and snap hints.
- Win overlay.

## 6. Rune Node Object

File: `rune_node.py`

`RuneNode` is the drawable/draggable tile wrapper around `RuneData`.

### Responsibilities

- Stores position and drag state.
- Consumes mouse events for drag start/move/end.
- Draws slab, grid, strokes, border, and label.

### Interactive vs target rendering

- Interactive nodes draw points in direct normalized slab mapping.
- Non-interactive target nodes fit all stroke coordinates into slab bounds with margin.
  - This avoids target previews going offscreen when runes contain attached offsets outside `0..1`.

## 7. Rune Editor Scene

File: `rune_editor.py`

Editor allows authoring rune JSON files.

Flow:

- Left-click one grid point to start stroke.
- Left-click second point to finish stroke.
- Right-click cancels pending point.
- Name input + Save/Undo/Clear buttons.
- Save writes `runes/<name>.json` via `RuneData.save()`.

Editor is currently separate from campaign content generation.

## 8. Tests

Directory: `tests/`

Current test modules:

- `test_models.py`
  - merge behavior
  - attach offset behavior
  - order-independent matching
  - LevelData save/load with tutorial lines
- `test_campaign.py`
  - campaign has multiple levels
  - each level has tutorial/target/starting runes
  - simple non-decreasing difficulty metric
- `test_level_scene.py`
  - moved-rune snap preference
  - direction detection
  - overlap merge candidate behavior
  - snap ignores unrelated non-moved pairs

Run tests:

```bash
uv run python -m unittest discover -s tests -v
```

## 9. Common Change Workflows

### Add a new level

1. Open `levels.py`.
2. Define any needed base runes/targets.
3. Append a new `LevelData` entry in `build_campaign_levels()`.
4. Include `tutorial_lines` and operation flags.
5. Run tests.

### Change snap behavior

1. Update `_check_snap_all()` in `level_scene.py`.
2. Keep `active_snap` contract consistent.
3. Update or add tests in `test_level_scene.py`.
4. Run full suite.

### Add new rune operations

1. Add operation logic to `RuneData` (data behavior).
2. Integrate key handling in `LevelScene.handle_key()` (scene behavior).
3. Add visuals/hints where appropriate.
4. Add tests for data and scene behavior.

## 10. Known Constraints

- Main loop is scene-driven and intentionally simple; no formal state machine framework.
- Campaign content is code-defined, not loaded from external level files.
- Editor saves runes, but campaign assembly still happens manually in `levels.py`.
- Matching is exact by stroke coordinates after sort, not fuzzy/epsilon matching.

## 11. Quick File Map

- `main.py`: app startup and mode switching
- `models.py`: core dataclasses and rune operations
- `levels.py`: campaign construction
- `level_scene.py`: gameplay scene and puzzle logic
- `rune_node.py`: draggable rune tile rendering/input
- `rune_editor.py`: rune authoring tool
- `tests/`: unit and behavior tests
