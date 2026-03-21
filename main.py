"""
Rune Game — main entry point
=============================
Run with:  python main.py

Controls:
  Rune Editor (default start screen):
    Left click  — place stroke point (click twice = one stroke)
    Right click — cancel pending point
    M key       — merge two snapping runes
    A key       — attach two snapping runes
    E key       — toggle editor / level mode
    R key       — restart current level
"""

from __future__ import annotations
import sys
import pygame
from pathlib import Path

from models import RuneData, LevelData
from rune_editor import RuneEditorScene
from level_scene import LevelScene

SCREEN_W = 720
SCREEN_H = 500
FPS = 60
RUNE_DIR = Path("runes")
LEVEL_DIR = Path("levels")


def make_demo_level() -> LevelData:
    """
    A built-in starter level so the game is playable immediately
    without needing to author runes first.
    """
    rune_a = RuneData(
        name="alpha",
        strokes=[
            ((0.25, 0.25), (0.75, 0.25)),
            ((0.25, 0.25), (0.5, 0.75)),
            ((0.75, 0.25), (0.5, 0.75)),
        ],
    )
    rune_b = RuneData(
        name="beta",
        strokes=[
            ((0.5, 0.25), (0.5, 0.75)),
            ((0.25, 0.5), (0.75, 0.5)),
        ],
    )
    # Target = merge of both
    target = RuneData.merge(rune_a, rune_b)
    target.name = "alpha+beta"

    return LevelData(
        level_name="Tutorial — merge the runes",
        starting_runes=[rune_a, rune_b],
        target_rune=target,
        allow_merge=True,
        allow_attach=True,
    )


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Rune Game")
    clock = pygame.time.Clock()

    RUNE_DIR.mkdir(exist_ok=True)
    LEVEL_DIR.mkdir(exist_ok=True)

    # Start in the editor; press E to switch to the level
    editor_scene = RuneEditorScene(screen, RUNE_DIR)
    level_scene = LevelScene(screen, make_demo_level())

    mode: str = "editor"  # "editor" | "level"

    font_small = pygame.font.SysFont("monospace", 12)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break

                # Switch modes
                if event.key == pygame.K_e:
                    mode = "level" if mode == "editor" else "editor"
                    continue

                # Level-specific keys
                if mode == "level":
                    if event.key == pygame.K_r:
                        level_scene = LevelScene(screen, make_demo_level())
                    else:
                        level_scene.handle_key(event.key)

            # Pass events to active scene
            if mode == "editor":
                editor_scene.handle_event(event)
            else:
                level_scene.handle_event(event)

        # Draw
        if mode == "editor":
            editor_scene.draw()
        else:
            level_scene.draw()

        # Mode indicator
        mode_txt = font_small.render(
            f"[E] {'→ Play level' if mode == 'editor' else '→ Editor'}   [ESC] Quit",
            True,
            (80, 70, 50),
        )
        screen.blit(mode_txt, (8, SCREEN_H - 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
