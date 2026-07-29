import pytest

from blockable_block_designer.domain.models import (
    EFFECT_PARAMETER_IDS,
    EFFECT_TYPES,
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Combination,
    Effect,
    Project,
)
from blockable_block_designer.domain.validation import validate_project
from blockable_block_designer.persistence.project_file import ProjectFileError, save_project


def valid_project() -> Project:
    project = Project(
        colors=[],
        block_types=[
            BlockType("normal_fire", "일반 화염", grade="normal", color="fire")
        ],
        effect_definitions=[],
        status_definitions=[],
    )
    project.blocks = [
        Block(
            "fire_dot",
            "불꽃 점",
            "normal_fire",
            "fire",
            [Cell(0, 0)],
            effects=[
                Effect(
                    "fire_dot_damage",
                    description="피해",
                    effect_name="불꽃 피해",
                    target="SELECTED",
                    value=1,
                    type="BASE_DAMAGE",
                )
            ],
            description="설명",
        )
    ]
    project.combinations = [
        Combination(
            "pair",
            "쌍",
            [
                BlockInstance("piece_01", "fire_dot", Cell(0, 0)),
                BlockInstance("piece_02", "fire_dot", Cell(1, 0)),
            ],
            effects=[
                Effect(
                    "pair_block",
                    description="방어",
                    effect_name="쌍 방어",
                    target="self",
                    value=2,
                    type="BLOCK",
                )
            ],
            description="설명",
        )
    ]
    return project


def errors(project: Project) -> list[str]:
    return [
        item.message for item in validate_project(project) if item.severity == "error"
    ]


def test_valid_project_has_no_errors() -> None:
    assert errors(valid_project()) == []


def test_effect_type_parameter_contract_matches_game_runtime() -> None:
    assert EFFECT_TYPES == {
        "BASE_DAMAGE",
        "BASE_HIT_COUNT",
        "INDEPENDENT_DAMAGE",
        "BLOCK",
        "RECOVERY",
        "STATUS_DAMAGE",
        "DEBUFF",
        "CROWD_CONTROL",
        "BUFF",
        "EXTRA_TURN",
        "DECK_CAPACITY",
        "DRAW",
        "PLACEMENT_COUNT",
    }
    assert EFFECT_PARAMETER_IDS == {
        "BASE_DAMAGE": {"NONE"},
        "BASE_HIT_COUNT": {"CURRENT_ACTION"},
        "INDEPENDENT_DAMAGE": {"NONE"},
        "BLOCK": {"NONE"},
        "RECOVERY": {"NONE"},
        "STATUS_DAMAGE": {"BURN", "BLEEDING", "POISON"},
        "DEBUFF": {"ATTACK_REDUCTION", "DAMAGE_TAKEN_INCREASE"},
        "CROWD_CONTROL": {"STUN", "FREEZE", "ACTION_LOCK"},
        "BUFF": {"DAMAGE_BONUS", "RAGE", "ATTACK_MULTIPLIER"},
        "EXTRA_TURN": {"CURRENT_ACTION", "PLAYER_TURN"},
        "DECK_CAPACITY": {"MAIN_DECK"},
        "DRAW": {"MAIN_DECK"},
        "PLACEMENT_COUNT": {"CURRENT_ACTION", "BLOCK_PLACEMENT"},
    }


def test_grade_and_color_follow_new_contract() -> None:
    project = valid_project()
    project.block_types[0].grade = "rare"
    project.blocks[0].color_id = "red"
    messages = errors(project)
    assert "허용되지 않은 grade입니다." in messages
    assert "허용되지 않은 color입니다." in messages


def test_effect_type_target_value_are_validated() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "deal_damage"
    effect.target = "enemy"
    effect.value = "많이"
    messages = errors(project)
    assert "7.4에서 허용하지 않은 type입니다." in messages
    assert "7.4에서 허용하지 않은 target입니다." in messages
    assert "이 효과 type에는 숫자 value가 필요합니다." not in messages


def test_effect_id_is_unique_across_project() -> None:
    project = valid_project()
    project.combinations[0].effects[0].effect_id = "fire_dot_damage"
    assert "effect_id가 중복되었습니다." in errors(project)


def test_target_range_patterns_are_validated() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    for target in ("SELECTED", "self", "L1", "R3", "B2", "all"):
        effect.target = target
        assert "7.4에서 허용하지 않은 target입니다." not in errors(project)
    effect.target = "L0"
    assert "7.4에서 허용하지 않은 target입니다." in errors(project)


def test_base_hit_count_uses_value_as_b_and_intensify_as_total_h() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "BASE_HIT_COUNT"
    effect.parameter_id = "CURRENT_ACTION"
    effect.value = 5
    effect.duration = 0
    effect.intensify = 6
    assert errors(project) == []
    effect.intensify = 0
    assert (
        "BASE_HIT_COUNT의 총 공격 횟수(intensify)는 1 이상이어야 합니다."
        in errors(project)
    )


def test_type_specific_parameter_id_is_checked() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "BUFF"
    effect.target = "self"
    effect.parameter_id = "DEFENSE"
    effect.duration = 2
    effect.intensify = 1
    assert "이 type에서 허용하지 않은 parameters.id입니다." in errors(project)


def test_deleted_hit_count_buff_is_rejected() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "BUFF"
    effect.target = "self"
    effect.parameter_id = "HIT_COUNT"
    effect.duration = 1
    effect.intensify = 1
    effect.value = 2

    assert "이 type에서 허용하지 않은 parameters.id입니다." in errors(project)


def test_deck_capacity_is_parsed_but_uses_fixed_instance_parameters() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "DECK_CAPACITY"
    effect.target = "self"
    effect.parameter_id = "MAIN_DECK"
    effect.value = 3
    effect.duration = 0
    effect.intensify = 1

    assert errors(project) == []


def test_percentage_value_accepts_integer_and_decimal_forms() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "DEBUFF"
    effect.parameter_id = "ATTACK_REDUCTION"
    effect.target = "SELECTED"
    effect.duration = -1
    effect.intensify = 1
    for value in (10, 0.1):
        effect.value = value
        assert errors(project) == []


def test_bleeding_is_canonical_status_damage_id() -> None:
    project = valid_project()
    effect = project.blocks[0].effects[0]
    effect.type = "STATUS_DAMAGE"
    effect.parameter_id = "BLEEDING"
    effect.duration = 2
    effect.intensify = 1
    assert errors(project) == []
    effect.parameter_id = "BLEED"
    assert "이 type에서 허용하지 않은 parameters.id입니다." in errors(project)


def test_overlap_cannot_be_saved_even_as_draft(tmp_path) -> None:
    project = valid_project()
    project.combinations[0].instances[1].origin = Cell(0, 0)
    with pytest.raises(ProjectFileError, match="겹쳐 저장할 수 없습니다"):
        save_project(
            project,
            tmp_path / "overlap.json",
            allow_warnings=True,
            allow_errors=True,
        )


def test_disconnected_block_is_warning() -> None:
    project = valid_project()
    project.blocks[0].cells = [Cell(0, 0), Cell(2, 0)]
    warnings = [
        item.message for item in validate_project(project) if item.severity == "warning"
    ]
    assert "블록 모양이 분리되어 있습니다." in warnings
