from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from ..domain.models import Cell


class GridCanvas(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        columns: int = 12,
        rows: int = 12,
        cell_size: int = 36,
        on_click: Callable[[Cell], None] | None = None,
    ) -> None:
        super().__init__(
            master,
            width=columns * cell_size,
            height=rows * cell_size,
            background="#F8FAFC",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        self.columns = columns
        self.rows = rows
        self.cell_size = cell_size
        self.on_cell_click = on_click
        self.on_drag_start: Callable[[Cell], bool] | None = None
        self.on_drag_move: Callable[[Cell], None] | None = None
        self.on_drag_end: Callable[[Cell], None] | None = None
        self._press_cell: Cell | None = None
        self._dragging = False
        self.bind("<ButtonPress-1>", self._pressed)
        self.bind("<B1-Motion>", self._moved)
        self.bind("<ButtonRelease-1>", self._released)
        self.draw_grid()

    def _event_cell(self, event: tk.Event) -> Cell | None:
        x, y = event.x // self.cell_size, event.y // self.cell_size
        return Cell(x, y) if 0 <= x < self.columns and 0 <= y < self.rows else None

    def _pressed(self, event: tk.Event) -> None:
        self.focus_set()
        self._press_cell = self._event_cell(event)
        self._dragging = bool(
            self._press_cell and self.on_drag_start and self.on_drag_start(self._press_cell)
        )

    def _moved(self, event: tk.Event) -> None:
        cell = self._event_cell(event)
        if self._dragging and cell and self.on_drag_move:
            self.on_drag_move(cell)

    def _released(self, event: tk.Event) -> None:
        cell = self._event_cell(event)
        if self._dragging:
            if cell and self.on_drag_end:
                self.on_drag_end(cell)
        elif cell and self.on_cell_click:
            self.on_cell_click(cell)
        self._press_cell = None
        self._dragging = False

    def draw_grid(self) -> None:
        self.delete("all")
        for x in range(self.columns + 1):
            px = x * self.cell_size
            self.create_line(px, 0, px, self.rows * self.cell_size, fill="#CBD5E1")
        for y in range(self.rows + 1):
            py = y * self.cell_size
            self.create_line(0, py, self.columns * self.cell_size, py, fill="#CBD5E1")

    def fill_cell(
        self, cell: Cell, color: str, outline: str = "#334155", text: str = ""
    ) -> None:
        pad = 2
        x1, y1 = cell.x * self.cell_size + pad, cell.y * self.cell_size + pad
        x2, y2 = (cell.x + 1) * self.cell_size - pad, (cell.y + 1) * self.cell_size - pad
        self.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=2)
        if text:
            self.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="white")
