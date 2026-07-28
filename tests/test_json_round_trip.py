import json
from pathlib import Path

import pytest

from blockable_block_designer.domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Combination,
    Effect,
    Project,
)
from blockable_block_designer.persistence.json_codec import project_from_dict, project_to_dict
from blockable_block_designer.persistence.project_file import (
    ProjectFileError,
    load_project,
    save_project,
)


def new_project() -> Project:
    project = Project(
        block_types=[
            BlockType("normal_fire", "일반 화염", grade="normal", color="fire")
        ],
        colors=[],
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
                    description="기본 피해 3",
                    effect_name="불꽃 점 피해",
                    target="SELECTED",
                    value=3,
                    type="BASE_DAMAGE",
                )
            ],
            description="한 칸 화염 블록",
        )
    ]
    project.combinations = [
        Combination(
            "fire_pair",
            "불꽃 쌍",
            [
                BlockInstance("piece_01", "fire_dot", Cell(0, 0)),
                BlockInstance("piece_02", "fire_dot", Cell(1, 0)),
            ],
            effects=[
                Effect(
                    "fire_pair_damage",
                    description="독립 피해 5",
                    effect_name="불꽃 쌍 피해",
                    target="all",
                    value=5,
                    type="INDEPENDENT_DAMAGE",
                )
            ],
            description="불꽃 점 두 개 조합",
        )
    ]
    return project


def test_new_schema_round_trip_preserves_contract_and_korean() -> None:
    encoded = project_to_dict(new_project())
    restored = project_from_dict(encoded)
    assert project_to_dict(restored) == encoded
    assert set(encoded) == {
        "schema_version", "data_type", "metadata", "blocks", "combinations"
    }
    assert encoded["data_type"] == "blockable_block_design"
    assert encoded["blocks"][0]["block_name"] == "불꽃 점"
    assert encoded["blocks"][0]["effects"][0] == {
        "effect_id": "fire_dot_damage",
        "effect_name": "불꽃 점 피해",
        "description": "기본 피해 3",
        "target": "SELECTED",
        "type": "BASE_DAMAGE",
        "value": 3,
        "parameters": {
            "id": "NONE",
            "duration": 0,
            "intensify": 0,
        },
    }


def test_unknown_schema_version_is_rejected(tmp_path: Path) -> None:
    data = project_to_dict(new_project())
    data["schema_version"] = "99.0.0"
    path = tmp_path / "future.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectFileError, match="schema_version"):
        load_project(path)


def test_legacy_schema_is_migrated_to_new_contract(tmp_path: Path) -> None:
    legacy = {
        "schema_version": "1.2.0",
        "metadata": {"project_name": "레거시"},
        "colors": [{"id": "fire", "display_name": "불", "hex": "#ff0000"}],
        "block_types": [{"id": "normal_fire", "display_name": "일반 화염"}],
        "effect_definitions": [],
        "status_definitions": [],
        "blocks": [
            {
                "id": "old_block",
                "display_name": "이전 블록",
                "type_id": "normal_fire",
                "color_id": "fire",
                "shape": {"cells": [{"x": 0, "y": 0}]},
                "transform": {"allow_rotation": True, "allow_mirroring": False},
                "effects": [
                    {
                        "effect_id": "deal_damage",
                        "order": 0,
                        "parameters": {"target": "enemy", "amount": 4},
                    }
                ],
                "description": "이전 데이터",
            }
        ],
        "combinations": [],
        "color_synergies": [],
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    effect = project.blocks[0].effects[0]
    assert project.schema_version == "1.1.0"
    assert project.data_type == "blockable_block_design"
    assert effect.type == "BASE_DAMAGE"
    assert effect.target == "SELECTED"
    assert effect.value == 4
    assert effect.parameter_id == "NONE"
    assert set(project_to_dict(project)) == {
        "schema_version", "data_type", "metadata", "blocks", "combinations"
    }


def test_invalid_draft_can_be_saved(tmp_path: Path) -> None:
    project = Project(colors=[], block_types=[], effect_definitions=[], status_definitions=[])
    project.combinations = [Combination("empty_recipe", "빈 조합")]
    path = tmp_path / "draft.json"
    issues = save_project(project, path, allow_warnings=True, allow_errors=True)
    assert any(item.severity == "error" for item in issues)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["metadata"]["validation_status"] == "invalid"
    assert data["data_type"] == "blockable_block_design"


def test_version_1_0_effect_is_upgraded_with_parameters(tmp_path: Path) -> None:
    data = project_to_dict(new_project())
    data["schema_version"] = "1.0.0"
    effect = data["blocks"][0]["effects"][0]
    effect.pop("parameters")
    effect["type"] = "BUFF"
    effect["target"] = "self"
    effect["reference_id"] = "DAMAGE_BONUS"
    path = tmp_path / "version-1.0.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    project = load_project(path)
    migrated = project.blocks[0].effects[0]
    assert project.schema_version == "1.1.0"
    assert migrated.parameter_id == "DAMAGE_BONUS"
    encoded = project_to_dict(project)["blocks"][0]["effects"][0]
    assert "reference_id" not in encoded
    assert encoded["parameters"] == {
        "id": "DAMAGE_BONUS", "duration": 0, "intensify": 0
    }


def test_version_1_0_base_hit_count_defaults_to_one_attack(tmp_path: Path) -> None:
    data = project_to_dict(new_project())
    data["schema_version"] = "1.0.0"
    effect = data["blocks"][0]["effects"][0]
    effect.pop("parameters")
    effect["type"] = "BASE_HIT_COUNT"
    effect["value"] = 8
    path = tmp_path / "version-1.0-hit-count.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    project = load_project(path)
    migrated = project.blocks[0].effects[0]

    assert migrated.value == 8
    assert migrated.parameter_id == "CURRENT_ACTION"
    assert migrated.duration == 0
    assert migrated.intensify == 1
