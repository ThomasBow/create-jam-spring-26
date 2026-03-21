from __future__ import annotations
import pygame
from models import LevelData, RuneData
from rune_node import RuneNode, SLAB_SIZE, SNAP_COLOUR

BTN_COL = (55, 45, 32)
BTN_HOV = (85, 70, 48)
BTN_TXT = (210, 190, 140)
BORDER = (140, 110, 60)
WIN_COL = (80, 200, 120)
PANEL_COL = (18, 15, 10)


class LevelScene:
    """
    Main gameplay scene.
    Shows starting runes (draggable) and a target rune (static, golden).
    Player merges / attaches runes to match the target.
    """

    def __init__(self, screen: pygame.Surface, level_data: LevelData) -> None:
        self.screen = screen
        self.level_data = level_data
        self.font = pygame.font.SysFont("monospace", 14)
        self.big_font = pygame.font.SysFont("monospace", 20, bold=True)

        self.won = False
        self.rune_nodes: list[RuneNode] = []
        self.target_node: RuneNode | None = None

        self._spawn_runes()

    # ------------------------------------------------------------------ setup

    def _spawn_runes(self) -> None:
        sw, sh = self.screen.get_size()
        x = 60
        y = sh // 2 - SLAB_SIZE // 2

        for rd in self.level_data.starting_runes:
            node = RuneNode(rd.duplicate(), (x, y))
            self.rune_nodes.append(node)
            x += SLAB_SIZE + 30

        # Target — top right, non-interactive, golden tint
        tx = sw - SLAB_SIZE - 40
        ty = 60
        self.target_node = RuneNode(
            self.level_data.target_rune,
            (tx, ty),
            interactive=False,
        )

    # ------------------------------------------------------------------ events

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.won:
            return

        # Give drag priority to the topmost (last) rune
        for node in reversed(self.rune_nodes):
            if node.handle_event(event):
                break

        # On mouse-up, check snap / win
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._check_snap_all()
            self._check_win()

    # ------------------------------------------------------------------ logic

    def _check_snap_all(self) -> None:
        """
        After a drop, look for any rune pair close enough to snap.
        Offer merge or attach based on level settings.
        """
        for node in self.rune_nodes:
            if node.dragging:
                continue
            result = node.check_snap(self.rune_nodes)
            if result is None:
                node.highlighted = False
                node.snap_dir = None
                continue
            other, direction = result
            node.highlighted = True
            node.snap_dir = direction

    def _do_merge(self, a: RuneNode, b: RuneNode) -> None:
        merged_data = RuneData.merge(a.rune_data, b.rune_data)
        pos = (a.position + b.position) / 2
        new_node = RuneNode(merged_data, (int(pos.x), int(pos.y)))
        self.rune_nodes.remove(a)
        self.rune_nodes.remove(b)
        self.rune_nodes.append(new_node)

    def _do_attach(self, a: RuneNode, b: RuneNode, direction: tuple[int, int]) -> None:
        attached_data = RuneData.attach(a.rune_data, b.rune_data, direction)
        new_node = RuneNode(attached_data, (int(a.position.x), int(a.position.y)))
        self.rune_nodes.remove(a)
        self.rune_nodes.remove(b)
        self.rune_nodes.append(new_node)

    def _check_win(self) -> None:
        if not self.target_node:
            return
        target = self.level_data.target_rune
        for node in self.rune_nodes:
            if node.rune_data.matches(target):
                self.won = True
                return

    # ------------------------------------------------------------------ draw

    def draw(self) -> None:
        self.screen.fill((10, 8, 6))
        sw, sh = self.screen.get_size()

        # Header panel
        pygame.draw.rect(self.screen, PANEL_COL, pygame.Rect(0, 0, sw, 48))
        pygame.draw.line(self.screen, BORDER, (0, 48), (sw, 48), 1)

        title = self.big_font.render(
            f"Level: {self.level_data.level_name}", True, (200, 180, 120)
        )
        self.screen.blit(title, (16, 12))

        ops: list[str] = []
        if self.level_data.allow_merge:
            ops.append("M: Merge")
        if self.level_data.allow_attach:
            ops.append("A: Attach")
        ops_txt = self.font.render("  |  ".join(ops), True, (110, 100, 70))
        self.screen.blit(ops_txt, (sw - ops_txt.get_width() - 16, 16))

        # Target label
        if self.target_node:
            lbl = self.font.render("TARGET", True, (160, 130, 60))
            self.screen.blit(lbl, (int(self.target_node.position.x), 36))
            self.target_node.draw(self.screen)
            self.target_node.draw_label(self.screen, self.font)

        # Divider between target area and workspace
        pygame.draw.line(
            self.screen,
            BORDER,
            (sw - SLAB_SIZE - 80, 56),
            (sw - SLAB_SIZE - 80, sh),
            1,
        )

        # Snap indicators — draw lines between snapping pairs
        for node in self.rune_nodes:
            if node.highlighted and node.snap_dir:
                dx, dy = node.snap_dir
                # Draw a glowing edge on the snapping side
                nx, ny = int(node.position.x), int(node.position.y)
                if dx == 1:
                    pts = [(nx + SLAB_SIZE, ny), (nx + SLAB_SIZE, ny + SLAB_SIZE)]
                elif dx == -1:
                    pts = [(nx, ny), (nx, ny + SLAB_SIZE)]
                elif dy == 1:
                    pts = [(nx, ny + SLAB_SIZE), (nx + SLAB_SIZE, ny + SLAB_SIZE)]
                else:
                    pts = [(nx, ny), (nx + SLAB_SIZE, ny)]
                pygame.draw.line(self.screen, SNAP_COLOUR, pts[0], pts[1], 3)

        # Rune nodes
        for node in self.rune_nodes:
            node.draw(self.screen)
            node.draw_label(self.screen, self.font)

        # Keyboard hint for snapping runes
        self._draw_snap_hints()

        # Win overlay
        if self.won:
            self._draw_win()

    def _draw_snap_hints(self) -> None:
        """Show M / A hints near snapping rune pairs."""
        for node in self.rune_nodes:
            if not node.highlighted or not node.snap_dir:
                continue
            cx = int(node.position.x + SLAB_SIZE // 2)
            cy = int(node.position.y) - 24
            if self.level_data.allow_merge:
                m = self.font.render("[M] Merge", True, SNAP_COLOUR)
                self.screen.blit(m, (cx - m.get_width() // 2, cy))
            if self.level_data.allow_attach:
                a = self.font.render("[A] Attach", True, (180, 220, 140))
                self.screen.blit(a, (cx - a.get_width() // 2, cy + 16))

    def _draw_win(self) -> None:
        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        win_txt = self.big_font.render("✦  Rune complete!  ✦", True, WIN_COL)
        self.screen.blit(win_txt, win_txt.get_rect(center=(sw // 2, sh // 2)))
        sub = self.font.render(
            "Press R to restart  |  N for next level", True, (160, 200, 160)
        )
        self.screen.blit(sub, sub.get_rect(center=(sw // 2, sh // 2 + 36)))

    # ------------------------------------------------------------------ keyboard actions

    def handle_key(self, key: int) -> None:
        """Called from main loop for M / A keypresses."""
        if self.won:
            return
        # Find any highlighted pair
        for node in self.rune_nodes:
            if not node.highlighted or not node.snap_dir:
                continue
            result = node.check_snap(self.rune_nodes)
            if result is None:
                continue
            other, direction = result
            if key == pygame.K_m and self.level_data.allow_merge:
                self._do_merge(node, other)
                self._check_win()
                return
            if key == pygame.K_a and self.level_data.allow_attach:
                self._do_attach(node, other, direction)
                self._check_win()
                return
