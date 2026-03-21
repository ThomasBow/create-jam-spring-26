from __future__ import annotations
import pygame
from pathlib import Path
from models import RuneData, Stroke, Point
from rune_node import (
    SLAB_SIZE,
    SLAB_BG,
    SLAB_BORDER,
    STROKE_COLOUR,
    PENDING_COLOUR,
    GRID_STEPS,
    norm_to_px,
)

EDITOR_OFFSET = (80, 80)  # top-left corner of the slab on screen
PANEL_X = 240  # x position of the right-hand UI panel
UI_BG = (20, 18, 14)
BTN_COL = (60, 50, 35)
BTN_HOV = (90, 75, 50)
BTN_TXT = (210, 190, 140)
INPUT_BG = (40, 34, 22)
INPUT_ACTIVE = (60, 52, 35)
MSG_OK = (100, 200, 100)
MSG_ERR = (220, 80, 80)


class Button:
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font) -> None:
        self.rect = rect
        self.label = label
        self.font = font

    def draw(self, surface: pygame.Surface) -> None:
        mouse = pygame.mouse.get_pos()
        col = BTN_HOV if self.rect.collidepoint(mouse) else BTN_COL
        pygame.draw.rect(surface, col, self.rect, border_radius=6)
        pygame.draw.rect(surface, SLAB_BORDER, self.rect, 1, border_radius=6)
        txt = self.font.render(self.label, True, BTN_TXT)
        tr = txt.get_rect(center=self.rect.center)
        surface.blit(txt, tr)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class RuneEditorScene:
    """
    Interactive rune drawing tool.
    Click two grid points to place a stroke.
    Right-click to cancel a pending first point.
    """

    def __init__(self, screen: pygame.Surface, save_dir: Path) -> None:
        self.screen = screen
        self.save_dir = save_dir
        self.font = pygame.font.SysFont("monospace", 14)
        self.big_font = pygame.font.SysFont("monospace", 18, bold=True)

        self.strokes: list[Stroke] = []
        self.pending: Point | None = None  # first click waiting for second
        self.name_text: str = ""
        self.name_active: bool = False
        self.message: str = ""
        self.message_colour: tuple[int, int, int] = MSG_OK
        self.message_timer: int = 0

        ox, oy = EDITOR_OFFSET
        self.btn_save = Button(
            pygame.Rect(PANEL_X, 80, 140, 36), "Save rune", self.font
        )
        self.btn_undo = Button(
            pygame.Rect(PANEL_X, 126, 140, 36), "Undo stroke", self.font
        )
        self.btn_clear = Button(
            pygame.Rect(PANEL_X, 172, 140, 36), "Clear all", self.font
        )
        self.name_rect = pygame.Rect(PANEL_X, 36, 140, 32)

    # ------------------------------------------------------------------ helpers

    def _snap_to_grid(self, pos: tuple[int, int]) -> Point | None:
        """Convert screen pos to normalised grid point, or None if outside slab."""
        ox, oy = EDITOR_OFFSET
        lx = pos[0] - ox
        ly = pos[1] - oy
        if lx < 0 or ly < 0 or lx > SLAB_SIZE or ly > SLAB_SIZE:
            return None
        step = SLAB_SIZE / GRID_STEPS
        gx = round(lx / step) / GRID_STEPS
        gy = round(ly / step) / GRID_STEPS
        gx = max(0.0, min(1.0, gx))
        gy = max(0.0, min(1.0, gy))
        return (gx, gy)

    def _show_message(self, text: str, ok: bool = True) -> None:
        self.message = text
        self.message_colour = MSG_OK if ok else MSG_ERR
        self.message_timer = 120  # frames

    # ------------------------------------------------------------------ events

    def handle_event(self, event: pygame.event.Event) -> None:
        # Name input box
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.name_active = self.name_rect.collidepoint(event.pos)

        if self.name_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name_text = self.name_text[:-1]
            elif event.key == pygame.K_RETURN:
                self.name_active = False
            elif event.unicode.isprintable():
                self.name_text += event.unicode
            return

        # Buttons
        if self.btn_save.is_clicked(event):
            self._save()
            return
        if self.btn_undo.is_clicked(event):
            if self.strokes:
                self.strokes.pop()
            self.pending = None
            return
        if self.btn_clear.is_clicked(event):
            self.strokes.clear()
            self.pending = None
            return

        # Grid clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pt = self._snap_to_grid(event.pos)
                if pt is not None:
                    if self.pending is None:
                        self.pending = pt
                    else:
                        if pt != self.pending:
                            self.strokes.append((self.pending, pt))
                        self.pending = None
            elif event.button == 3:
                self.pending = None

    def _save(self) -> None:
        name = self.name_text.strip()
        if not name:
            self._show_message("Enter a name first!", ok=False)
            return
        if not self.strokes:
            self._show_message("Draw something first!", ok=False)
            return
        rd = RuneData(name=name, strokes=list(self.strokes))
        path = self.save_dir / f"{name}.json"
        rd.save(path)
        self._show_message(f"Saved: {name}.json")

    # ------------------------------------------------------------------ draw

    def draw(self) -> None:
        self.screen.fill((12, 10, 8))
        ox, oy = EDITOR_OFFSET

        # Slab background
        slab_rect = pygame.Rect(ox, oy, SLAB_SIZE, SLAB_SIZE)
        pygame.draw.rect(self.screen, SLAB_BG, slab_rect)

        # Grid
        step = SLAB_SIZE // GRID_STEPS
        for i in range(GRID_STEPS + 1):
            gx = ox + i * step
            gy = oy + i * step
            pygame.draw.line(self.screen, (55, 45, 30), (gx, oy), (gx, oy + SLAB_SIZE))
            pygame.draw.line(self.screen, (55, 45, 30), (ox, gy), (ox + SLAB_SIZE, gy))

        # Grid dots
        for ix in range(GRID_STEPS + 1):
            for iy in range(GRID_STEPS + 1):
                px = ox + ix * step
                py = oy + iy * step
                pygame.draw.circle(self.screen, (80, 65, 45), (px, py), 3)

        # Completed strokes
        for stroke in self.strokes:
            a = norm_to_px(stroke[0], (ox, oy))
            b = norm_to_px(stroke[1], (ox, oy))
            pygame.draw.line(self.screen, STROKE_COLOUR, a, b, 3)
            pygame.draw.circle(self.screen, STROKE_COLOUR, a, 4)
            pygame.draw.circle(self.screen, STROKE_COLOUR, b, 4)

        # Pending first point
        if self.pending is not None:
            pp = norm_to_px(self.pending, (ox, oy))
            pygame.draw.circle(self.screen, PENDING_COLOUR, pp, 6)
            pygame.draw.circle(self.screen, PENDING_COLOUR, pp, 6, 2)
            # Line to mouse
            mouse = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, (*PENDING_COLOUR, 100), pp, mouse, 1)

        # Slab border
        pygame.draw.rect(self.screen, SLAB_BORDER, slab_rect, 2)

        # --- Right panel ---
        panel = pygame.Rect(PANEL_X - 10, 20, 180, 300)
        pygame.draw.rect(self.screen, UI_BG, panel, border_radius=8)
        pygame.draw.rect(self.screen, SLAB_BORDER, panel, 1, border_radius=8)

        # Title
        title = self.big_font.render("Rune Editor", True, (200, 180, 120))
        self.screen.blit(title, (PANEL_X, 8))

        # Name input
        inp_col = INPUT_ACTIVE if self.name_active else INPUT_BG
        pygame.draw.rect(self.screen, inp_col, self.name_rect, border_radius=4)
        pygame.draw.rect(self.screen, SLAB_BORDER, self.name_rect, 1, border_radius=4)
        placeholder = self.name_text if self.name_text else "rune name..."
        txt_col = (210, 190, 140) if self.name_text else (100, 90, 65)
        inp_txt = self.font.render(placeholder, True, txt_col)
        self.screen.blit(inp_txt, (self.name_rect.x + 6, self.name_rect.y + 9))

        # Buttons
        self.btn_save.draw(self.screen)
        self.btn_undo.draw(self.screen)
        self.btn_clear.draw(self.screen)

        # Stroke count
        count_txt = self.font.render(
            f"Strokes: {len(self.strokes)}", True, (120, 110, 80)
        )
        self.screen.blit(count_txt, (PANEL_X, 220))

        # Instructions
        instrs = [
            "Left click: place point",
            "Click again: finish stroke",
            "Right click: cancel point",
        ]
        for i, line in enumerate(instrs):
            t = self.font.render(line, True, (90, 80, 60))
            self.screen.blit(t, (PANEL_X, 250 + i * 18))

        # Message
        if self.message_timer > 0:
            msg = self.font.render(self.message, True, self.message_colour)
            self.screen.blit(msg, (ox, oy + SLAB_SIZE + 16))
            self.message_timer -= 1
