from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import Block, BlockInstance, Cell


def normalize_cells(cells: Iterable[Cell]) -> list[Cell]:
    cells = list(cells)
    if not cells:
        return []
    min_x = min(cell.x for cell in cells)
    min_y = min(cell.y for cell in cells)
    return sorted({Cell(cell.x - min_x, cell.y - min_y) for cell in cells})


def transform_cells(
    cells: Iterable[Cell], rotation: int = 0, mirrored: bool = False
) -> list[Cell]:
    if rotation not in {0, 90, 180, 270}:
        raise ValueError(f"지원하지 않는 회전값: {rotation}")
    result: list[Cell] = []
    for cell in cells:
        x, y = (-cell.x if mirrored else cell.x), cell.y
        for _ in range(rotation // 90):
            x, y = -y, x
        result.append(Cell(x, y))
    return normalize_cells(result)


def is_connected(cells: Iterable[Cell]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    visited: set[Cell] = set()
    stack = [next(iter(remaining))]
    while stack:
        cell = stack.pop()
        if cell in visited:
            continue
        visited.add(cell)
        stack.extend(
            neighbor
            for neighbor in (
                Cell(cell.x + 1, cell.y),
                Cell(cell.x - 1, cell.y),
                Cell(cell.x, cell.y + 1),
                Cell(cell.x, cell.y - 1),
            )
            if neighbor in remaining and neighbor not in visited
        )
    return visited == remaining


def instance_cells(instance: BlockInstance, block: Block) -> set[Cell]:
    return {
        Cell(cell.x + instance.origin.x, cell.y + instance.origin.y)
        for cell in transform_cells(block.cells, instance.rotation, instance.mirrored)
    }


def combination_cells(
    instances: Iterable[BlockInstance], blocks: Mapping[str, Block]
) -> dict[str, set[Cell]]:
    return {
        instance.instance_id: instance_cells(instance, blocks[instance.block_id])
        for instance in instances
        if instance.block_id in blocks
    }


def normalize_instances(
    instances: Iterable[BlockInstance], blocks: Mapping[str, Block]
) -> list[BlockInstance]:
    instances = list(instances)
    occupied = combination_cells(instances, blocks)
    all_cells = [cell for cells in occupied.values() for cell in cells]
    if not all_cells:
        return instances
    min_x = min(cell.x for cell in all_cells)
    min_y = min(cell.y for cell in all_cells)
    return [
        BlockInstance(
            item.instance_id,
            item.block_id,
            Cell(item.origin.x - min_x, item.origin.y - min_y),
            item.rotation,
            item.mirrored,
            item.match,
        )
        for item in instances
    ]
