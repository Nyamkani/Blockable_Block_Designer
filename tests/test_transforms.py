from blockable_block_designer.domain.models import Block, BlockInstance, Cell
from blockable_block_designer.domain.transforms import (
    instance_cells,
    is_connected,
    normalize_cells,
    transform_cells,
)


def test_normalize_cells_moves_top_left_to_origin() -> None:
    assert normalize_cells([Cell(4, 3), Cell(5, 3)]) == [Cell(0, 0), Cell(1, 0)]


def test_rotation_is_normalized() -> None:
    cells = [Cell(0, 0), Cell(1, 0), Cell(0, 1)]
    assert transform_cells(cells, 90) == [Cell(0, 0), Cell(1, 0), Cell(1, 1)]
    assert transform_cells(cells, 180) == [Cell(0, 1), Cell(1, 0), Cell(1, 1)]
    assert transform_cells(cells, 270) == [Cell(0, 0), Cell(0, 1), Cell(1, 1)]


def test_mirroring_is_normalized() -> None:
    cells = [Cell(0, 0), Cell(0, 1), Cell(1, 1)]
    assert transform_cells(cells, mirrored=True) == [
        Cell(0, 1),
        Cell(1, 0),
        Cell(1, 1),
    ]


def test_connection_uses_cardinal_neighbors() -> None:
    assert is_connected([Cell(0, 0), Cell(1, 0)])
    assert not is_connected([Cell(0, 0), Cell(1, 1)])
    assert not is_connected([])


def test_instance_cells_apply_transform_and_origin() -> None:
    block = Block("l", "L", "normal", "red", [Cell(0, 0), Cell(1, 0)])
    instance = BlockInstance("piece_1", "l", Cell(3, 4), rotation=90)
    assert instance_cells(instance, block) == {Cell(3, 4), Cell(3, 5)}
