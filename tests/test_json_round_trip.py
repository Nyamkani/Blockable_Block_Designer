import json
from pathlib import Path

import pytest

from blockable_rule_editor.domain.models import BlockType, Project
from blockable_rule_editor.persistence.json_codec import project_from_dict, project_to_dict
from blockable_rule_editor.persistence.project_file import ProjectFileError, load_project


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
