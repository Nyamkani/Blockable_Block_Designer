from blockable_block_designer.domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Combination,
    Project,
)
from blockable_block_designer.services.block_service import rename_block
from blockable_block_designer.services.combination_service import move_instance


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


def test_move_instance_preserves_rotation_and_rejects_overlap() -> None:
    elbow = Block(
        "elbow", "ㄴ 블록", "normal", "red",
        [Cell(0, 0), Cell(0, 1), Cell(1, 1)],
    )
    first = BlockInstance("piece_1", "elbow", Cell(0, 0), rotation=90)
    second = BlockInstance("piece_2", "elbow", Cell(4, 0), rotation=180, mirrored=True)
    combination = Combination("pair", "맞물린 블록", [first, second])
    blocks = {elbow.id: elbow}

    assert move_instance(combination, "piece_2", Cell(2, 0), blocks)
    assert second.origin == Cell(2, 0)
    assert second.rotation == 180
    assert second.mirrored is True
    assert not move_instance(combination, "piece_2", Cell(0, 0), blocks)
    assert second.origin == Cell(2, 0)


def test_move_instance_may_temporarily_overlap_while_editing() -> None:
    dot = Block("dot", "점", "normal", "red", [Cell(0, 0)])
    first = BlockInstance("piece_1", "dot", Cell(0, 0))
    second = BlockInstance("piece_2", "dot", Cell(1, 0), rotation=270)
    combination = Combination("draft", "편집 중", [first, second])

    assert move_instance(
        combination,
        "piece_2",
        Cell(0, 0),
        {dot.id: dot},
        allow_overlap=True,
    )
    assert second.origin == Cell(0, 0)
    assert second.rotation == 270
