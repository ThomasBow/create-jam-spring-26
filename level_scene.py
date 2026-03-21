from __future__ import annotations
import pygame
from models import LevelData, RuneData
from rune_node import RuneNode, SLAB_SIZE, SNAP_COLOUR, SNAP_DIST

BTN_COL = (55, 45, 32)
BTN_HOV = (85, 70, 48)
BTN_TXT = (210, 190, 140)
BORDER = (140, 110, 60)
WIN_COL = (80, 200, 120)
PANEL_COL = (18, 15, 10)
SIDE_PANEL_W = 220
TOP_MARGIN = 56
BOTTOM_PANEL_H = 92
EDGE_ANCHOR_COL = (100, 220, 140)
EDGE_ATTACHED_COL = (220, 180, 90)
MOVED_FOCUS_COL = (120, 170, 240)


class LevelScene:
    """
    Main gameplay scene.
    Shows starting runes (draggable) and a target rune (static, golden).
    Player merges / attaches runes to match the target.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        level_data: LevelData,
        level_index: int = 0,
        total_levels: int = 1,
    ) -> None:
        self.screen = screen
        self.level_data = level_data
        self.level_index = level_index
        self.total_levels = max(1, total_levels)
        self.font = pygame.font.SysFont("monospace", 14)
        self.big_font = pygame.font.SysFont("monospace", 20, bold=True)

        self.won = False
        self.rune_nodes: list[RuneNode] = []
        self.target_node: RuneNode | None = None
        self.active_snap: tuple[RuneNode, RuneNode, tuple[int, int]] | None = None
        self.last_moved_node: RuneNode | None = None

        self._spawn_runes()

    # ------------------------------------------------------------------ setup

    def _spawn_runes(self) -> None:
        workspace = self._workspace_rect()
        gap = 18
        cols = max(1, (workspace.width + gap) // (SLAB_SIZE + gap))
        x = workspace.x
        y = workspace.y
        col = 0

        for rd in self.level_data.starting_runes:
            node = RuneNode(rd.duplicate(), (x, y))
            self.rune_nodes.append(node)
            col += 1
            if col >= cols:
                col = 0
                x = workspace.x
                y += SLAB_SIZE + gap
            else:
                x += SLAB_SIZE + gap

        # Target — fixed in the right-hand panel.
        target_panel = self._target_panel_rect()
        tx = target_panel.centerx - SLAB_SIZE // 2
        ty = target_panel.y + 44
        tx = max(target_panel.left + 8, min(tx, target_panel.right - SLAB_SIZE - 8))
        ty = max(target_panel.top + 28, min(ty, target_panel.bottom - SLAB_SIZE - 28))
        self.target_node = RuneNode(
            self.level_data.target_rune,
            (tx, ty),
            interactive=False,
        )

    def _workspace_rect(self) -> pygame.Rect:
        sw, sh = self.screen.get_size()
        return pygame.Rect(
            12,
            TOP_MARGIN,
            sw - SIDE_PANEL_W - 24,
            sh - TOP_MARGIN - BOTTOM_PANEL_H - 12,
        )

    def _target_panel_rect(self) -> pygame.Rect:
        sw, sh = self.screen.get_size()
        return pygame.Rect(
            sw - SIDE_PANEL_W + 8,
            TOP_MARGIN,
            SIDE_PANEL_W - 16,
            sh - TOP_MARGIN - 8,
        )

    def _tutorial_panel_rect(self) -> pygame.Rect:
        workspace = self._workspace_rect()
        sh = self.screen.get_height()
        return pygame.Rect(
            workspace.x,
            sh - BOTTOM_PANEL_H,
            workspace.width,
            BOTTOM_PANEL_H - 10,
        )

    def _clamp_node_to_workspace(self, node: RuneNode) -> None:
        workspace = self._workspace_rect()
        min_x = workspace.left
        max_x = workspace.right - SLAB_SIZE
        min_y = workspace.top
        max_y = workspace.bottom - SLAB_SIZE
        node.position.x = min(max(node.position.x, min_x), max_x)
        node.position.y = min(max(node.position.y, min_y), max_y)

    # ------------------------------------------------------------------ events

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.won:
            return

        # Give drag priority to the topmost (last) rune
        for node in reversed(self.rune_nodes):
            if node.handle_event(event):
                self._clamp_node_to_workspace(node)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.last_moved_node = node
                break

        # On mouse-up, check snap / win
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._check_snap_all()
            self._check_win()

    # ------------------------------------------------------------------ logic

    def _check_snap_all(self) -> None:
        """
        Find the best snap candidate across all rune pairs and highlight only that pair.
        Prioritizes merging when slabs overlap (on top of each other).
        """
        for node in self.rune_nodes:
            node.highlighted = False
            node.snap_dir = None

        moved = self.last_moved_node
        if moved is None or moved not in self.rune_nodes or moved.dragging:
            self.active_snap = None
            return

        best_score: tuple[float, int, int] | None = None
        best: tuple[RuneNode, RuneNode, tuple[int, int]] | None = None

        # First priority: check for overlaps/merges (slabs on top of each other)
        for a in self.rune_nodes:
            if a is moved or a.dragging:
                continue
            b = moved
            
            # Check if slabs overlap (rectangles collide)
            if a.rect.colliderect(b.rect):
                if self.level_data.allow_merge:
                    overlap_distance = (b.position - a.position).length()
                    # Prefer denser anchor rune to avoid direction flips.
                    complexity_pref = -len(a.rune_data.strokes)
                    # Use priority 0 for merges (highest priority)
                    score = (0, overlap_distance, complexity_pref)
                    if best_score is None or score < best_score:
                        best_score = score
                        best = (a, b, (0, 0))
        
        # Second priority: check for edge snapping (if no merge candidate found)
        if best is None:
            dirs: list[tuple[int, int]] = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for a in self.rune_nodes:
                if a is moved or a.dragging:
                    continue
                b = moved
                for direction in dirs:
                    dx, dy = direction
                    expected_b = a.position + pygame.Vector2(dx * SLAB_SIZE, dy * SLAB_SIZE)
                    error = (b.position - expected_b).length()
                    if error > SNAP_DIST:
                        continue

                    # Prefer denser anchor rune to avoid direction flips.
                    complexity_pref = -len(a.rune_data.strokes)
                    # Use priority 1 for edge snaps (lower priority than merges)
                    score = (1, error, complexity_pref)
                    if best_score is None or score < best_score:
                        best_score = score
                        best = (a, b, direction)

        self.active_snap = None
        if best is None:
            return

        anchor, attached, direction = best
        self.active_snap = (anchor, attached, direction)
        anchor.highlighted = True
        anchor.snap_dir = direction
        attached.highlighted = True
        attached.snap_dir = (-direction[0], -direction[1])

    def _do_merge(self, a: RuneNode, b: RuneNode) -> None:
        merged_data = RuneData.merge(a.rune_data, b.rune_data)
        pos = (a.position + b.position) / 2
        new_node = RuneNode(merged_data, (int(pos.x), int(pos.y)))
        self.rune_nodes.remove(a)
        self.rune_nodes.remove(b)
        self.rune_nodes.append(new_node)
        self.last_moved_node = new_node
        self._check_snap_all()

    def _do_attach(self, a: RuneNode, b: RuneNode, direction: tuple[int, int]) -> None:
        attached_data = RuneData.attach(a.rune_data, b.rune_data, direction)
        new_node = RuneNode(attached_data, (int(a.position.x), int(a.position.y)))
        self.rune_nodes.remove(a)
        self.rune_nodes.remove(b)
        self.rune_nodes.append(new_node)
        self.last_moved_node = new_node
        self._check_snap_all()

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

        # Subtle vertical gradient for depth.
        for i in range(sh):
            c = 10 + (i * 12) // max(1, sh)
            pygame.draw.line(self.screen, (c, c - 2, c - 4), (0, i), (sw, i))

        # Header panel
        pygame.draw.rect(self.screen, PANEL_COL, pygame.Rect(0, 0, sw, 48))
        pygame.draw.line(self.screen, BORDER, (0, 48), (sw, 48), 1)

        title = self.big_font.render(
            f"Level {self.level_index + 1}/{self.total_levels}: {self.level_data.level_name}",
            True,
            (200, 180, 120),
        )
        self.screen.blit(title, (16, 12))

        ops: list[str] = []
        if self.level_data.allow_merge:
            ops.append("M: Merge")
        if self.level_data.allow_attach:
            ops.append("A: Attach")
        ops.append("R: Restart")
        ops.append("E: Editor")
        ops_txt = self.font.render("  |  ".join(ops), True, (110, 100, 70))
        self.screen.blit(ops_txt, (sw - ops_txt.get_width() - 16, 16))

        # Workspace and target panel framing
        workspace = self._workspace_rect()
        target_panel = self._target_panel_rect()
        pygame.draw.rect(self.screen, (15, 12, 9), workspace, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, workspace, 1, border_radius=8)
        pygame.draw.rect(self.screen, (14, 12, 9), target_panel, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, target_panel, 1, border_radius=8)

        # Target label
        if self.target_node:
            lbl = self.font.render("TARGET", True, (160, 130, 60))
            self.screen.blit(lbl, (target_panel.x + 12, target_panel.y + 10))
            self.target_node.draw(self.screen)
            self.target_node.draw_label(self.screen, self.font)

        # Tutorial / objective panel at bottom to avoid covering gameplay and target.
        panel_rect = self._tutorial_panel_rect()
        pygame.draw.rect(self.screen, (22, 18, 12), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, panel_rect, 1, border_radius=8)
        if self.level_data.tutorial_lines:
            for i, line in enumerate(self.level_data.tutorial_lines[:3]):
                line_txt = self.font.render(f"- {line}", True, (165, 145, 98))
                self.screen.blit(line_txt, (panel_rect.x + 10, panel_rect.y + 8 + i * 22))
        else:
            line_txt = self.font.render(
                "Align rune edges to highlight then press the operation key.",
                True,
                (165, 145, 98),
            )
            self.screen.blit(line_txt, (panel_rect.x + 10, panel_rect.y + 28))

        # Rune nodes
        for node in self.rune_nodes:
            node.draw(self.screen)
            node.draw_label(self.screen, self.font)

        # Show which rune the snap solver is currently anchored to.
        self._draw_last_moved_focus()

        # Keyboard hint for snapping runes and explicit edge preview.
        self._draw_attach_edge_preview()
        self._draw_snap_hints()

        # Win overlay
        if self.won:
            self._draw_win()

    def _draw_snap_hints(self) -> None:
        """Show M / A hints near snapping rune pairs."""
        if self.active_snap is None:
            return
        anchor, attached, direction = self.active_snap
        cx = int((anchor.position.x + attached.position.x) / 2 + SLAB_SIZE // 2)
        cy = int(min(anchor.position.y, attached.position.y) - 24)
        if self.level_data.allow_merge:
            merge_hint = "[M] Merge"
            if direction == (0, 0):
                merge_hint = "[M] Merge (overlay)"
            m = self.font.render(merge_hint, True, SNAP_COLOUR)
            self.screen.blit(m, (cx - m.get_width() // 2, cy))
        if self.level_data.allow_attach and direction != (0, 0):
            a = self.font.render("[A] Attach", True, (180, 220, 140))
            self.screen.blit(a, (cx - a.get_width() // 2, cy + 16))

    def _edge_segment(
        self, node: RuneNode, direction: tuple[int, int]
    ) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        nx, ny = int(node.position.x), int(node.position.y)
        dx, dy = direction
        if dx == 1:
            a, b = (nx + SLAB_SIZE, ny), (nx + SLAB_SIZE, ny + SLAB_SIZE)
        elif dx == -1:
            a, b = (nx, ny), (nx, ny + SLAB_SIZE)
        elif dy == 1:
            a, b = (nx, ny + SLAB_SIZE), (nx + SLAB_SIZE, ny + SLAB_SIZE)
        else:
            a, b = (nx, ny), (nx + SLAB_SIZE, ny)
        mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        return a, b, mid

    def _draw_attach_edge_preview(self) -> None:
        if self.active_snap is None:
            return
        anchor, attached, direction = self.active_snap
        if direction == (0, 0):
            return

        a0, a1, amid = self._edge_segment(anchor, direction)
        b0, b1, bmid = self._edge_segment(attached, (-direction[0], -direction[1]))

        pygame.draw.line(self.screen, EDGE_ANCHOR_COL, a0, a1, 4)
        pygame.draw.line(self.screen, EDGE_ATTACHED_COL, b0, b1, 4)
        pygame.draw.line(self.screen, SNAP_COLOUR, amid, bmid, 2)
        pygame.draw.circle(self.screen, EDGE_ANCHOR_COL, amid, 4)
        pygame.draw.circle(self.screen, EDGE_ATTACHED_COL, bmid, 4)

    def _draw_last_moved_focus(self) -> None:
        node = self.last_moved_node
        if node is None or node not in self.rune_nodes:
            return

        phase = (pygame.time.get_ticks() // 110) % 8
        pulse_w = 2 + (phase if phase <= 4 else 8 - phase)
        rect = node.rect.inflate(10, 10)
        pygame.draw.rect(
            self.screen,
            MOVED_FOCUS_COL,
            rect,
            pulse_w,
            border_radius=10,
        )

    def _draw_win(self) -> None:
        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        win_txt = self.big_font.render("Rune complete!", True, WIN_COL)
        self.screen.blit(win_txt, win_txt.get_rect(center=(sw // 2, sh // 2)))
        if self.level_index + 1 < self.total_levels:
            sub_msg = "Press N for next level  |  R to replay"
        else:
            sub_msg = "Campaign complete! Press R to replay this level"
        sub = self.font.render(sub_msg, True, (160, 200, 160))
        self.screen.blit(sub, sub.get_rect(center=(sw // 2, sh // 2 + 36)))

    # ------------------------------------------------------------------ keyboard actions

    def handle_key(self, key: int) -> None:
        """Called from main loop for M / A keypresses."""
        if self.won:
            return
        if self.active_snap is None:
            return

        anchor, attached, direction = self.active_snap
        if key == pygame.K_m and self.level_data.allow_merge:
            self._do_merge(anchor, attached)
            self._check_win()
            return
        if key == pygame.K_a and self.level_data.allow_attach and direction != (0, 0):
            self._do_attach(anchor, attached, direction)
            self._check_win()
            return
