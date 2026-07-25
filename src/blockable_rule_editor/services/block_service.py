from __future__ import annotations

from ..domain.models import Block, Cell, Project
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


def rename_block(project: Project, block: Block, new_id: str) -> None:
    previous_id = block.id
    block.id = new_id
    if previous_id == new_id:
        return
    for combination in project.combinations:
        for instance in combination.instances:
            if instance.block_id == previous_id:
                instance.block_id = new_id
