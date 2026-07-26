from blockable_block_designer.domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Combination,
    Project,
)
from blockable_block_designer.services.block_service import rename_block


def test_rename_block_updates_combination_references() -> None:
    block = Block("old_id", "블록", "normal", "red", [Cell(0, 0)])
    project = Project(
        block_types=[BlockType("normal", "일반")],
        blocks=[block],
        combinations=[
            Combination(
                "recipe",
                "조합",
                [BlockInstance("piece_1", "old_id")],
            )
        ],
    )
    rename_block(project, block, "새블록")
    assert block.id == "새블록"
    assert project.combinations[0].instances[0].block_id == "새블록"
