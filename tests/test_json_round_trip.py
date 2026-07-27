import json
from pathlib import Path

import pytest

from blockable_block_designer.domain.models import BlockType, Combination, Project
from blockable_block_designer.domain.models import EffectDefinition, EffectParameterDefinition
from blockable_block_designer.persistence.json_codec import project_from_dict, project_to_dict
from blockable_block_designer.persistence.effect_config import (
    load_effect_config,
    save_effect_config,
)
from blockable_block_designer.persistence.project_file import (
    ProjectFileError,
    load_project,
    save_project,
)


EXAMPLE = Path(__file__).parents[1] / "examples" / "blockable_rules.example.json"
EFFECT_CONFIG_EXAMPLE = (
    Path(__file__).parents[1] / "examples" / "blockable_effect_config.example.json"
)


def test_example_round_trip_preserves_meaning_and_korean() -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    project = project_from_dict(data)
    encoded = project_to_dict(project)
    assert encoded == data
    assert encoded["blocks"][0]["display_name"] == "붉은 2칸 블록"
    json.dumps(encoded, ensure_ascii=False, allow_nan=False)


def test_unknown_top_level_fields_are_preserved() -> None:
    data = project_to_dict(Project(block_types=[BlockType("normal", "일반")]))
    data["future_field"] = {"enabled": True}
    restored = project_from_dict(data)
    assert project_to_dict(restored)["future_field"] == {"enabled": True}


def test_unknown_schema_version_is_rejected(tmp_path: Path) -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["schema_version"] = "99.0.0"
    path = tmp_path / "future.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectFileError, match="schema_version"):
        load_project(path)


def test_version_1_project_is_migrated_to_exact_slots(tmp_path: Path) -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["schema_version"] = "1.0.0"
    data.pop("color_synergies")
    for combination in data["combinations"]:
        combination.pop("conditional_effects")
        for instance in combination["instances"]:
            instance.pop("match")
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    assert project.schema_version == "1.2.0"
    assert project.combinations[0].instances[0].match.kind == "exact_block"


def test_loading_migrates_to_combat_effect_standard() -> None:
    project = load_project(EXAMPLE)
    definitions = {item.id: item for item in project.effect_definitions}
    assert "apply_buff" not in definitions
    assert "apply_status" in definitions
    damage_parameters = {
        item.key: item for item in definitions["deal_damage"].parameters
    }
    assert damage_parameters["amount"].display_name == "피해량"
    assert damage_parameters["range"].required_when == {"target": ["enemy"]}
    assert {item.id for item in project.status_definitions} >= {
        "bleeding", "burn", "weakness", "wound", "stun", "double_attack"
    }


def test_legacy_effect_ids_and_parameters_are_migrated(tmp_path: Path) -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["blocks"][0]["effects"] = [
        {
            "effect_id": "apply_buff",
            "order": 0,
            "parameters": {"buff_id": "doubleAttack", "amount": 2, "buff_name": "연속 공격"},
        },
        {
            "effect_id": "gain_defense",
            "order": 1,
            "parameters": {"amount": 7},
        },
    ]
    path = tmp_path / "legacy-effects.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    first, second = project.blocks[0].effects
    assert first.effect_id == "apply_status"
    assert first.parameters == {
        "status_id": "double_attack", "stacks": 2, "target": "self"
    }
    assert second.effect_id == "gain_block"
    assert second.parameters == {"amount": 7, "target": "self"}


def test_equivalent_custom_effect_is_merged_into_standard(tmp_path: Path) -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["effect_definitions"].append(
        {
            "id": "my_damage",
            "display_name": "피해",
            "parameters": [
                {"key": "damage", "value_type": "number", "required": True}
            ],
            "description": "표준 피해와 같은 사용자 정의 효과",
        }
    )
    data["blocks"][0]["effects"] = [
        {
            "effect_id": "my_damage",
            "order": 0,
            "parameters": {"damage": 9},
        }
    ]
    path = tmp_path / "equivalent-custom.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    effect = project.blocks[0].effects[0]
    assert effect.effect_id == "deal_damage"
    assert effect.parameters == {
        "amount": 9, "target": "enemy", "range": "single"
    }
    assert "my_damage" not in {item.id for item in project.effect_definitions}


def test_extended_custom_effect_is_not_merged(tmp_path: Path) -> None:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["effect_definitions"].append(
        {
            "id": "damage_each_turn",
            "display_name": "매 턴 피해",
            "parameters": [
                {"key": "amount", "value_type": "number", "required": True},
                {"key": "duration", "value_type": "integer", "required": True},
            ],
            "description": "표준 피해보다 확장된 사용자 정의 효과",
        }
    )
    path = tmp_path / "extended-custom.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    assert "damage_each_turn" in {item.id for item in project.effect_definitions}


def test_invalid_draft_can_be_saved_and_reopened(tmp_path: Path) -> None:
    project = Project(block_types=[BlockType("normal", "일반")])
    project.blocks = []
    project.combinations = [Combination("empty_recipe", "빈 조합")]
    path = tmp_path / "invalid_draft.json"
    issues = save_project(
        project,
        path,
        allow_warnings=True,
        allow_errors=True,
    )
    assert any(item.severity == "error" for item in issues)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["metadata"]["validation_status"] == "invalid"
    assert data["metadata"]["validation_error_count"] >= 1
    reopened = load_project(path)
    assert reopened.combinations[0].id == "empty_recipe"
    with pytest.raises(ProjectFileError, match="검증에 실패"):
        load_project(path, strict=True)


def test_custom_effect_description_and_negative_metadata_round_trip() -> None:
    project = Project(
        effect_definitions=[
            EffectDefinition(
                "damage_each_turn",
                "매 턴 피해",
                [
                    EffectParameterDefinition(
                        "amount", "number", True,
                        display_name="턴당 피해량",
                        description="매 턴 적용할 수치",
                        default=0,
                        allow_negative=True,
                    )
                ],
                "지정한 턴 동안 매 턴 피해를 줍니다.",
            )
        ]
    )
    encoded = project_to_dict(project)
    restored = project_from_dict(encoded)
    definition = restored.effect_definitions[0]
    assert definition.description == "지정한 턴 동안 매 턴 피해를 줍니다."
    assert definition.parameters[0].description == "매 턴 적용할 수치"
    assert definition.parameters[0].default == 0
    assert definition.parameters[0].allow_negative is True


def test_effect_config_can_be_shared_between_projects(tmp_path: Path) -> None:
    definition = EffectDefinition(
        "custom_damage",
        "사용자 피해",
        [
            EffectParameterDefinition(
                "amount", "number", True, display_name="피해량", allow_negative=True
            )
        ],
        "공유할 사용자 정의 효과",
    )
    path = tmp_path / "blockable_effect_config.json"
    save_effect_config([definition], path)
    restored = load_effect_config(path)
    assert restored == [definition]


def test_effect_config_example_is_loadable() -> None:
    definitions = load_effect_config(EFFECT_CONFIG_EXAMPLE)
    assert definitions[0].id == "custom_damage_each_turn"
    assert definitions[0].description
