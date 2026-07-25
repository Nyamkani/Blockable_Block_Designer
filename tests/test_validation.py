from blockable_rule_editor.domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Combination,
    ConditionalEffect,
    Effect,
    Project,
    RuleCondition,
    SlotMatch,
)
from blockable_rule_editor.domain.validation import validate_project


def valid_project() -> Project:
    project = Project(block_types=[BlockType("normal", "일반")])
    project.blocks = [
        Block(
            "red_dot",
            "붉은 점",
            "normal",
            "red",
            [Cell(0, 0)],
            effects=[Effect("deal_damage", parameters={"amount": 1})],
        )
    ]
    project.combinations = [
        Combination(
            "pair",
            "쌍",
            [
                BlockInstance("piece_1", "red_dot", Cell(0, 0)),
                BlockInstance("piece_2", "red_dot", Cell(1, 0)),
            ],
        )
    ]
    return project


def errors(project: Project) -> list[str]:
    return [
        issue.message for issue in validate_project(project) if issue.severity == "error"
    ]


def warnings(project: Project) -> list[str]:
    return [
        issue.message
        for issue in validate_project(project)
        if issue.severity == "warning"
    ]


def test_valid_project_has_no_errors() -> None:
    assert errors(valid_project()) == []


def test_disconnected_block_is_warning_but_broken_reference_is_error() -> None:
    project = valid_project()
    project.blocks[0].cells = [Cell(0, 0), Cell(2, 0)]
    project.blocks[0].type_id = "missing"
    messages = errors(project)
    assert not any("블록 모양이 분리" in message for message in messages)
    assert "존재하지 않는 type을 참조합니다." in messages
    assert any("블록 모양이 분리" in message for message in warnings(project))


def test_overlap_is_error() -> None:
    project = valid_project()
    project.combinations[0].instances[1].origin = Cell(0, 0)
    assert "블록 인스턴스가 겹칩니다." in errors(project)


def test_effect_parameter_is_checked() -> None:
    project = valid_project()
    project.blocks[0].effects[0].parameters = {"amount": "많이"}
    assert "parameter 'amount' 자료형이 다릅니다." in errors(project)


def test_invalid_ids_and_duplicate_ids_are_errors() -> None:
    project = valid_project()
    project.blocks.append(
        Block("red_dot", "중복", "normal", "red", [Cell(0, 0)])
    )
    project.block_types[0].id = "Not Valid"
    messages = errors(project)
    assert "ID가 중복되었습니다." in messages
    assert "ID에는 공백을 사용할 수 없습니다." in messages


def test_project_ids_may_start_with_number_uppercase_or_korean() -> None:
    project = valid_project()
    project.block_types[0].id = "1일반-Type"
    project.blocks[0].type_id = "1일반-Type"
    project.blocks[0].id = "블록A"
    for instance in project.combinations[0].instances:
        instance.block_id = "블록A"
    project.combinations[0].id = "2HitCombo"
    assert errors(project) == []


def test_slot_type_and_conditional_color_are_validated() -> None:
    project = valid_project()
    project.combinations[0].instances[0].match = SlotMatch(
        kind="type", type_id="missing"
    )
    project.combinations[0].conditional_effects = [
        ConditionalEffect(
            RuleCondition(
                "color_count", {"color_id": "missing", "count": 0}
            ),
            [Effect("deal_damage", parameters={"amount": 2})],
        )
    ]
    messages = errors(project)
    assert "슬롯 Type이 존재하지 않습니다." in messages
    assert "조건의 색상 ID가 존재하지 않습니다." in messages
    assert "색상 개수는 1 이상의 정수여야 합니다." in messages


def test_buff_identifier_must_be_snake_case() -> None:
    project = valid_project()
    project.blocks[0].effects.append(
        Effect(
            "apply_buff",
            order=1,
            parameters={
                "buff_name": "강철 피부",
                "buff_id": "강철 피부",
            },
        )
    )
    assert "parameter 'buff_id' 자료형이 다릅니다." in errors(project)


def test_shape_only_slot_is_valid() -> None:
    project = valid_project()
    for instance in project.combinations[0].instances:
        instance.match = SlotMatch(kind="any_block")
    assert errors(project) == []
