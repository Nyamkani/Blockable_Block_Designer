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
from blockable_block_designer.ui.effect_editor import EffectDialog


def _effect(
    effect_id: str,
    effect_type: str,
    value: int | float,
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


def test_combination_preview_uses_parameter_display_name_and_decimal_value() -> None:
    weakness = _effect("weakness", "DEBUFF", 0.1, "SELECTED")
    weakness.parameter_id = "ATTACK_REDUCTION"
    weakness.intensify = 3
    combination = Combination("weak_combo", "약화 조합", effects=[weakness])

    assert combination_effect_preview(Project(), combination) == [
        "약화 조합: 약화 0.1"
    ]


def test_combination_preview_shows_base_damage_and_total_hit_count() -> None:
    attack = _effect("six_hits", "BASE_HIT_COUNT", 5, "B1")
    attack.parameter_id = "CURRENT_ACTION"
    attack.duration = 0
    attack.intensify = 6
    combination = Combination("multi_hit", "연속 공격", effects=[attack])

    assert combination_effect_preview(Project(), combination) == [
        "연속 공격: 연속 기본 공격: B 5 × H 6 [기준+좌우 1칸]"
    ]


def test_combination_preview_handles_empty_selection() -> None:
    assert combination_effect_preview(Project(), None) == [
        "조합식을 선택하면 예상 효과가 표시됩니다."
    ]


def test_unimplemented_parameter_ids_are_labeled_without_changing_json_id() -> None:
    assert (
        EffectDialog._parameter_option_label("STATUS_DAMAGE", "POISON")
        == "POISON (미구현 ID)"
    )
    assert (
        EffectDialog._parameter_option_label("EXTRA_TURN", "PLAYER_TURN")
        == "PLAYER_TURN (미구현 ID)"
    )
    assert (
        EffectDialog._parameter_option_label("STATUS_DAMAGE", "BURN")
        == "BURN"
    )
