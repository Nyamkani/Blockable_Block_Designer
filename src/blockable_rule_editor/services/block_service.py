from __future__ import annotations

from ..domain.models import Block, Cell
from ..domain.transforms import is_connected, normalize_cells


def toggle_cell(block: Block, cell: Cell) -> None:
    cells = set(block.cells)
    if cell in cells:
        cells.remove(cell)
    else:
        cells.add(cell)
    block.cells = sorted(cells)


def can_save_shape(block: Block) -> bool:
    return bool(block.cells) and is_connected(block.cells)


def normalize_shape(block: Block) -> None:
    block.cells = normalize_cells(block.cells)

