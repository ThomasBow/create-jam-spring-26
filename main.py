"""
Rune Game — main entry point
=============================
Run with:  python main.py

Controls:
    Rune Editor:
    Left click  — place stroke point (click twice = one stroke)
    Right click — cancel pending point
    M key       — merge two snapping runes
    A key       — attach two snapping runes
    E key       — toggle editor / level mode
    R key       — restart current level
        N key       — next level (after victory)
"""

from __future__ import annotations

import asyncio
import sys
import pygame
from pathlib import Path

from rune_editor import RuneEditorScene
from level_scene import LevelScene
from levels import build_campaign_levels

SCREEN_W = 720
SCREEN_H = 500
FPS = 60
RUNE_DIR = Path("runes")
LEVEL_DIR = Path("levels")


async def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Rune Game")
    clock = pygame.time.Clock()

    RUNE_DIR.mkdir(exist_ok=True)
    LEVEL_DIR.mkdir(exist_ok=True)

    campaign_levels = build_campaign_levels()
    level_idx = 0

    # Start in level mode; press E to switch to editor.
    editor_scene = RuneEditorScene(screen, RUNE_DIR)
    level_scene = LevelScene(
        screen,
        campaign_levels[level_idx],
        level_index=level_idx,
        total_levels=len(campaign_levels),
    )

    mode: str = "level"  # "editor" | "level"

    font_small = pygame.font.SysFont("monospace", 12)

    def load_level(index: int) -> LevelScene:
        return LevelScene(
            screen,
            campaign_levels[index],
            level_index=index,
            total_levels=len(campaign_levels),
        )

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
                        level_scene = load_level(level_idx)
                    elif event.key == pygame.K_n and level_scene.won:
                        if level_idx + 1 < len(campaign_levels):
                            level_idx += 1
                            level_scene = load_level(level_idx)
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
            (
                f"[E] {'-> Play level' if mode == 'editor' else '-> Editor'}"
                f"   [ESC] Quit   Campaign {level_idx + 1}/{len(campaign_levels)}"
            ),
            True,
            (80, 70, 50),
        )
        screen.blit(mode_txt, (8, SCREEN_H - 20))

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)  # ← this is the critical Pygbag hook

    pygame.quit()
    raise SystemExit  # ← instead of sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
