import json
from pathlib import Path

import pytest

from blockable_block_deigner.domain.models import BlockType, Combination, Project
from blockable_block_deigner.persistence.json_codec import project_from_dict, project_to_dict
from blockable_block_deigner.persistence.project_file import (
    ProjectFileError,
    load_project,
    save_project,
)


EXAMPLE = Path(__file__).parents[1] / "examples" / "blockable_rules.example.json"


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
    assert project.schema_version == "1.1.0"
    assert project.combinations[0].instances[0].match.kind == "exact_block"


def test_loading_enriches_builtin_effect_input_metadata() -> None:
    project = load_project(EXAMPLE)
    definitions = {item.id: item for item in project.effect_definitions}
    assert "apply_buff" in definitions
    damage_parameters = {
        item.key: item for item in definitions["deal_damage"].parameters
    }
    assert damage_parameters["amount"].display_name == "값(피해량)"
    buff_parameters = {
        item.key: item for item in definitions["apply_buff"].parameters
    }
    assert buff_parameters["buff_name"].display_name == "버프명(한글 설명)"
    assert buff_parameters["buff_id"].value_type == "identifier"


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
