from __future__ import annotations
import pygame
from models import RuneData, Point

# Colours
SLAB_BG = (30, 24, 16)
SLAB_BORDER = (140, 110, 60)
STROKE_COLOUR = (220, 205, 160)
PENDING_COLOUR = (255, 220, 0)
HIGHLIGHT_COL = (80, 160, 220)
TARGET_TINT = (200, 160, 40)
SNAP_COLOUR = (100, 200, 120)

SLAB_SIZE = 128  # pixels per rune cell
SNAP_DIST = 40  # pixels — how close to snap edges
GRID_STEPS = 4  # grid subdivisions (gives 4×4 grid)
STROKE_W = 3  # stroke line width


def norm_to_px(pt: Point, offset: tuple[int, int] = (0, 0)) -> tuple[int, int]:
    """Convert a normalised 0..1 point to pixel coords within a slab."""
    ox, oy = offset
    return (int(pt[0] * SLAB_SIZE + ox), int(pt[1] * SLAB_SIZE + oy))


class RuneNode:
    """
    A draggable, interactive rune tile.
    Owns one RuneData and renders it on screen.
    Can be merged or attached to another RuneNode.
    """

    def __init__(
        self,
        rune_data: RuneData,
        position: tuple[int, int],
        interactive: bool = True,
    ) -> None:
        self.rune_data = rune_data
        self.position = pygame.Vector2(position)
        self.interactive = interactive

        # Drag state
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)

        # Visual state
        self.highlighted = False  # hover / snap feedback
        self.snap_dir: tuple[int, int] | None = None  # which edge is snapping

    # ------------------------------------------------------------------ geometry

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.position.x), int(self.position.y), SLAB_SIZE, SLAB_SIZE
        )

    def centre(self) -> pygame.Vector2:
        return self.position + pygame.Vector2(SLAB_SIZE / 2, SLAB_SIZE / 2)

    # ------------------------------------------------------------------ input

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if the event was consumed."""
        if not self.interactive:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.drag_offset = self.position - pygame.Vector2(event.pos)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.position = pygame.Vector2(event.pos) + self.drag_offset
                return True

        return False

    # ------------------------------------------------------------------ snap logic

    def check_snap(
        self, others: list[RuneNode]
    ) -> tuple[RuneNode, tuple[int, int]] | None:
        """
        Returns (other_rune, direction) if this rune is close enough
        to snap to an edge of another rune. Direction is from self→other.
        """
        dirs: list[tuple[int, int]] = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for other in others:
            if other is self:
                continue
            for dx, dy in dirs:
                target = other.position - pygame.Vector2(dx * SLAB_SIZE, dy * SLAB_SIZE)
                if (self.position - target).length() < SNAP_DIST:
                    return (other, (dx, dy))
        return None

    # ------------------------------------------------------------------ drawing

    def draw(self, surface: pygame.Surface) -> None:
        x, y = int(self.position.x), int(self.position.y)

        # Slab background
        pygame.draw.rect(surface, SLAB_BG, self.rect)

        # Grid lines
        step = SLAB_SIZE // GRID_STEPS
        for i in range(GRID_STEPS + 1):
            gx = x + i * step
            gy = y + i * step
            pygame.draw.line(surface, (55, 45, 30), (gx, y), (gx, y + SLAB_SIZE))
            pygame.draw.line(surface, (55, 45, 30), (x, gy), (x + SLAB_SIZE, gy))

        # Strokes
        colour = TARGET_TINT if not self.interactive else STROKE_COLOUR

        def to_px(pt: Point) -> tuple[int, int]:
            if self.interactive:
                return norm_to_px(pt, (x, y))

            # Target preview can contain attached strokes beyond 0..1.
            # Fit full rune bounds into a slab with small margins.
            all_points: list[Point] = [p for s in self.rune_data.strokes for p in s]
            if not all_points:
                return (x, y)

            min_x = min(p[0] for p in all_points)
            max_x = max(p[0] for p in all_points)
            min_y = min(p[1] for p in all_points)
            max_y = max(p[1] for p in all_points)

            span_x = max(0.001, max_x - min_x)
            span_y = max(0.001, max_y - min_y)
            inner = SLAB_SIZE - 16
            scale = min(inner / span_x, inner / span_y)
            off_x = x + (SLAB_SIZE - span_x * scale) / 2
            off_y = y + (SLAB_SIZE - span_y * scale) / 2
            px = int(off_x + (pt[0] - min_x) * scale)
            py = int(off_y + (pt[1] - min_y) * scale)
            return (px, py)

        for stroke in self.rune_data.strokes:
            a = to_px(stroke[0])
            b = to_px(stroke[1])
            pygame.draw.line(surface, colour, a, b, STROKE_W)
            # Dots at endpoints
            pygame.draw.circle(surface, colour, a, 3)
            pygame.draw.circle(surface, colour, b, 3)

        # Border — highlighted when snap candidate
        border_col = SNAP_COLOUR if self.highlighted else SLAB_BORDER
        border_w = 3 if self.highlighted else 2
        pygame.draw.rect(surface, border_col, self.rect, border_w)

        # Label
        # (font is injected by the scene to avoid per-node font loading)

    def draw_label(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        label = font.render(self.rune_data.name, True, (160, 140, 100))
        surface.blit(
            label, (int(self.position.x), int(self.position.y) + SLAB_SIZE + 4)
        )
