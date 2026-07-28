from blockable_block_designer.domain.models import (
    Block,
    BlockInstance,
    Cell,
    Combination,
    Effect,
    Project,
)
from blockable_block_designer.services.effect_preview import (
    combination_effect_preview,
)


def _effect(
    effect_id: str,
    effect_type: str,
    value: int,
    target: str = "self",
) -> Effect:
    return Effect(
        effect_id=effect_id,
        effect_name=effect_id,
        type=effect_type,
        target=target,
        value=value,
    )


def test_combination_preview_sums_placed_blocks_and_combination_effects() -> None:
    block = Block(
        "corner",
        "ㄴ 블록",
        "normal",
        "steel",
        [Cell(0, 0)],
        effects=[
            _effect("attack", "BASE_DAMAGE", 5, "SELECTED"),
            _effect("defense", "BLOCK", 5),
        ],
    )
    combination = Combination(
        "shield",
        "미완성 방패",
        [
            BlockInstance("piece_1", "corner"),
            BlockInstance("piece_2", "corner"),
        ],
        effects=[
            _effect("shield_up", "BLOCK", 10),
            _effect("attack_down", "BASE_DAMAGE", -10, "B2"),
        ],
    )
    project = Project(blocks=[block], combinations=[combination])

    assert combination_effect_preview(project, combination) == [
        "공격력 10 [선택 대상], 방어 10",
        "미완성 방패: 방어 10, 공격력 -10 [기준+좌우 2칸]",
    ]


def test_combination_preview_keeps_different_attack_ranges_separate() -> None:
    combination = Combination(
        "ranged",
        "범위 공격",
        effects=[
            _effect("left_1", "BASE_DAMAGE", 3, "L1"),
            _effect("left_2", "BASE_DAMAGE", 2, "L1"),
            _effect("all", "BASE_DAMAGE", 4, "all"),
        ],
    )

    assert combination_effect_preview(Project(), combination) == [
        "범위 공격: 공격력 5 [기준+왼쪽 1칸], 공격력 4 [전체]"
    ]


def test_combination_preview_shows_consecutive_attack_damage_and_count() -> None:
    attack = _effect("triple", "BASE_HIT_COUNT", 7, "R2")
    attack.parameter_id = "CURRENT_ACTION"
    attack.intensify = 3
    combination = Combination("triple_combo", "삼연격", effects=[attack])

    assert combination_effect_preview(Project(), combination) == [
        "삼연격: 연속 공격: 데미지 7 × 3회 [기준+오른쪽 2칸]"
    ]


def test_combination_preview_handles_empty_selection() -> None:
    assert combination_effect_preview(Project(), None) == [
        "조합식을 선택하면 예상 효과가 표시됩니다."
    ]
