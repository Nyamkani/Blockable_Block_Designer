from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from .models import (
    BLOCK_COLORS,
    BLOCK_GRADES,
    DATA_TYPE,
    EFFECT_TARGETS,
    EFFECT_TYPES,
    EFFECT_PARAMETER_IDS,
    Effect,
    Project,
)
from .transforms import combination_cells, is_connected, normalize_cells

ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
TARGET_PATTERN = re.compile(r"^(?:SELECTED|self|all|[LRB][1-9][0-9]*)$")


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    location: str
    message: str


def _ids(items: list[Any], label: str, issues: list[ValidationIssue]) -> set[str]:
    seen: set[str] = set()
    for item in items:
        location = f"{label}:{item.id}"
        if not item.id:
            issues.append(ValidationIssue("error", label, "ID가 없습니다."))
        elif not ID_PATTERN.fullmatch(item.id):
            issues.append(
                ValidationIssue("error", location, "ID는 영문 소문자 snake_case여야 합니다.")
            )
        elif item.id in seen:
            issues.append(ValidationIssue("error", location, "ID가 중복되었습니다."))
        seen.add(item.id)
        if not item.display_name.strip():
            issues.append(ValidationIssue("error", location, "표시 이름이 없습니다."))
    return seen


def _validate_effects(
    effects: list[Effect],
    location: str,
    effect_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    value_types = {
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
    for index, effect in enumerate(effects):
        here = f"{location}.effects[{index}]"
        if not effect.effect_id or not ID_PATTERN.fullmatch(effect.effect_id):
            issues.append(
                ValidationIssue("error", here, "effect_id는 영문 소문자 snake_case여야 합니다.")
            )
        elif effect.effect_id in effect_ids:
            issues.append(ValidationIssue("error", here, "effect_id가 중복되었습니다."))
        effect_ids.add(effect.effect_id)
        if not effect.effect_name.strip():
            issues.append(ValidationIssue("error", here, "effect_name이 없습니다."))
        if effect.type not in EFFECT_TYPES:
            issues.append(ValidationIssue("error", here, "7.4에서 허용하지 않은 type입니다."))
        if not TARGET_PATTERN.fullmatch(effect.target):
            issues.append(ValidationIssue("error", here, "7.4에서 허용하지 않은 target입니다."))
        if effect.type in value_types and (
            not isinstance(effect.value, (int, float))
            or isinstance(effect.value, bool)
            or not math.isfinite(effect.value)
        ):
            issues.append(ValidationIssue("error", here, "효과 value는 유한한 숫자여야 합니다."))
        if effect.extra.get("_missing_parameters"):
            issues.append(
                ValidationIssue(
                    "error", here, "parameters.id, duration, intensify가 모두 필요합니다."
                )
            )
        unknown_fields = [key for key in effect.extra if not key.startswith("_")]
        if unknown_fields:
            issues.append(
                ValidationIssue(
                    "error", here, "공통 효과 구조에 없는 추가 필드가 있습니다."
                )
            )
        allowed_parameter_ids = EFFECT_PARAMETER_IDS.get(effect.type, set())
        if effect.type in EFFECT_TYPES and effect.parameter_id not in allowed_parameter_ids:
            issues.append(
                ValidationIssue("error", here, "이 type에서 허용하지 않은 parameters.id입니다.")
            )
        if not isinstance(effect.duration, int) or isinstance(effect.duration, bool):
            issues.append(ValidationIssue("error", here, "parameters.duration은 정수여야 합니다."))
        elif effect.duration < -2:
            issues.append(ValidationIssue("error", here, "duration은 -2 이상이어야 합니다."))
        if (
            not isinstance(effect.intensify, int)
            or isinstance(effect.intensify, bool)
            or effect.intensify < 0
        ):
            issues.append(
                ValidationIssue("error", here, "parameters.intensify는 0 이상의 정수여야 합니다.")
            )
        fixed = {
            "BASE_DAMAGE": ("NONE", 0, 0),
            "INDEPENDENT_DAMAGE": ("NONE", 0, 0),
            "BLOCK": ("NONE", 0, 0),
            "RECOVERY": ("NONE", 0, 0),
        }.get(effect.type)
        if fixed and (effect.parameter_id, effect.duration, effect.intensify) != fixed:
            issues.append(
                ValidationIssue("error", here, "즉시 효과의 parameters 기본값 규칙과 다릅니다.")
            )
        integer_value_pairs = {
            ("EXTRA_TURN", "CURRENT_ACTION"),
            ("EXTRA_TURN", "PLAYER_TURN"),
            ("DECK_CAPACITY", "MAIN_DECK"),
            ("DRAW", "MAIN_DECK"),
            ("PLACEMENT_COUNT", "CURRENT_ACTION"),
            ("PLACEMENT_COUNT", "BLOCK_PLACEMENT"),
        }
        if (
            (effect.type, effect.parameter_id) in integer_value_pairs
            and (not isinstance(effect.value, int) or isinstance(effect.value, bool))
        ):
            issues.append(
                ValidationIssue("error", here, "횟수·용량 효과의 value는 정수여야 합니다.")
            )
        fixed_parameters = {
            ("CROWD_CONTROL", "STUN"): (1, 1),
            ("EXTRA_TURN", "CURRENT_ACTION"): (0, 1),
            ("DRAW", "MAIN_DECK"): (0, 1),
            ("PLACEMENT_COUNT", "CURRENT_ACTION"): (0, 1),
        }
        expected = fixed_parameters.get((effect.type, effect.parameter_id))
        if expected and (effect.duration, effect.intensify) != expected:
            issues.append(
                ValidationIssue(
                    "error",
                    here,
                    (
                        f"{effect.type} + {effect.parameter_id}는 "
                        f"duration {expected[0]}, intensify {expected[1]}을 사용해야 합니다."
                    ),
                )
            )
        if effect.type == "BASE_HIT_COUNT":
            if effect.parameter_id != "CURRENT_ACTION" or effect.duration != 0:
                issues.append(
                    ValidationIssue(
                        "error",
                        here,
                        "BASE_HIT_COUNT는 CURRENT_ACTION, duration 0을 사용해야 합니다.",
                    )
                )
            if (
                not isinstance(effect.intensify, int)
                or isinstance(effect.intensify, bool)
                or effect.intensify < 1
            ):
                issues.append(
                    ValidationIssue(
                        "error",
                        here,
                        "BASE_HIT_COUNT의 총 공격 횟수(intensify)는 1 이상이어야 합니다.",
                    )
                )


def validate_project(project: Project) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if project.data_type != DATA_TYPE:
        issues.append(
            ValidationIssue("error", "data_type", "data_type은 blockable_block_design이어야 합니다.")
        )
    block_ids = _ids(project.blocks, "blocks", issues)
    _ids(project.combinations, "combinations", issues)
    types = {item.id: item for item in project.block_types}
    used_blocks: set[str] = set()
    effect_ids: set[str] = set()

    for block in project.blocks:
        location = f"blocks:{block.id}"
        block_type = types.get(block.type_id)
        if block_type is None:
            issues.append(ValidationIssue("error", location, "block_type 정보가 없습니다."))
        else:
            if block_type.grade not in BLOCK_GRADES:
                issues.append(ValidationIssue("error", location, "허용되지 않은 grade입니다."))
            if block.color_id not in BLOCK_COLORS:
                issues.append(ValidationIssue("error", location, "허용되지 않은 color입니다."))
            if block_type.color != block.color_id:
                issues.append(
                    ValidationIssue(
                        "error", location, "block_type의 color와 블록 color가 일치하지 않습니다."
                    )
                )
        if not block.cells:
            issues.append(ValidationIssue("error", location, "블록 모양이 비어 있습니다."))
        elif len(set(block.cells)) != len(block.cells):
            issues.append(ValidationIssue("error", location, "블록 칸 좌표가 중복되었습니다."))
        elif not is_connected(block.cells):
            issues.append(ValidationIssue("warning", location, "블록 모양이 분리되어 있습니다."))
        if not block.description:
            issues.append(ValidationIssue("warning", location, "블록 설명이 비어 있습니다."))
        if not block.effects:
            issues.append(ValidationIssue("warning", location, "블록 자체 효과가 없습니다."))
        _validate_effects(block.effects, location, effect_ids, issues)

    blocks = {item.id: item for item in project.blocks}
    for combination in project.combinations:
        location = f"combinations:{combination.id}"
        if not combination.instances:
            issues.append(ValidationIssue("error", location, "조합식에 블록이 없습니다."))
        instance_ids: set[str] = set()
        for instance in combination.instances:
            if not instance.instance_id or not ID_PATTERN.fullmatch(instance.instance_id):
                issues.append(
                    ValidationIssue("error", location, "instance_id는 snake_case여야 합니다.")
                )
            elif instance.instance_id in instance_ids:
                issues.append(ValidationIssue("error", location, "instance_id가 중복되었습니다."))
            instance_ids.add(instance.instance_id)
            block = blocks.get(instance.block_id)
            if block is None:
                issues.append(ValidationIssue("error", location, "존재하지 않는 block_id입니다."))
                continue
            used_blocks.add(instance.block_id)
            if instance.rotation not in {0, 90, 180, 270}:
                issues.append(ValidationIssue("error", location, "회전값이 올바르지 않습니다."))
            if instance.rotation and not block.allow_rotation:
                issues.append(ValidationIssue("error", location, "허용되지 않은 회전을 사용합니다."))
            if instance.mirrored and not block.allow_mirroring:
                issues.append(ValidationIssue("error", location, "허용되지 않은 반전을 사용합니다."))
        occupied = combination_cells(combination.instances, blocks)
        claimed: set[Any] = set()
        for cells in occupied.values():
            if claimed & cells:
                issues.append(ValidationIssue("error", location, "블록 인스턴스가 겹칩니다."))
                break
            claimed.update(cells)
        if not combination.description:
            issues.append(ValidationIssue("warning", location, "조합식 설명이 비어 있습니다."))
        if not combination.effects:
            issues.append(ValidationIssue("warning", location, "조합식 기본 효과가 없습니다."))
        _validate_effects(combination.effects, location, effect_ids, issues)

    for block_id in sorted(block_ids - used_blocks):
        issues.append(ValidationIssue("warning", f"blocks:{block_id}", "조합식에서 사용되지 않습니다."))
    return issues
