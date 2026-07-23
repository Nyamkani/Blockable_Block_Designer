from __future__ import annotations

from collections.abc import Mapping

from ..domain.models import Block, BlockInstance, Cell, Combination
from ..domain.transforms import instance_cells


def can_place(
    combination: Combination,
    candidate: BlockInstance,
    blocks: Mapping[str, Block],
    ignore_instance_id: str | None = None,
) -> bool:
    block = blocks.get(candidate.block_id)
    if block is None:
        return False
    candidate_cells = instance_cells(candidate, block)
    for existing in combination.instances:
        if existing.instance_id == ignore_instance_id:
            continue
        existing_block = blocks.get(existing.block_id)
        if existing_block and candidate_cells & instance_cells(existing, existing_block):
            return False
    return True


def move_instance(
    combination: Combination,
    instance_id: str,
    origin: Cell,
    blocks: Mapping[str, Block],
) -> bool:
    instance = next(
        (item for item in combination.instances if item.instance_id == instance_id), None
    )
    if instance is None:
        return False
    candidate = BlockInstance(
        instance.instance_id,
        instance.block_id,
        origin,
        instance.rotation,
        instance.mirrored,
        instance.match,
    )
    if not can_place(combination, candidate, blocks, instance_id):
        return False
    instance.origin = origin
    return True
