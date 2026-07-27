from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import Effect, EffectDefinition, Project, RuleCondition
from .transforms import combination_cells, is_connected, normalize_cells

PROJECT_ID_PATTERN = re.compile(r"^\S+$")
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLOT_MATCH_KINDS = {
    "exact_block",
    "any_block",
    "type",
    "color",
    "tag",
}
CONDITION_KINDS = {
    "all_same_color",
    "all_different_colors",
    "contains_color",
    "color_count",
    "color_set",
    "same_type",
    "block_count",
    "tag_match",
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    location: str
    message: str


def _ids(items: list[Any], location: str, issues: list[ValidationIssue]) -> set[str]:
    seen: set[str] = set()
    for item in items:
        if not item.id:
            issues.append(ValidationIssue("error", location, "ID가 없습니다."))
        elif not PROJECT_ID_PATTERN.fullmatch(item.id):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{location}:{item.id}",
                    "ID에는 공백을 사용할 수 없습니다.",
                )
            )
        elif item.id in seen:
            issues.append(
                ValidationIssue("error", f"{location}:{item.id}", "ID가 중복되었습니다.")
            )
        seen.add(item.id)
        if not item.display_name.strip():
            issues.append(
                ValidationIssue("error", f"{location}:{item.id}", "표시 이름이 없습니다.")
            )
    return seen


def _validate_effects(
    effects: list[Effect],
    definitions: dict[str, EffectDefinition],
    status_ids: set[str],
    location: str,
    issues: list[ValidationIssue],
) -> None:
    for index, effect in enumerate(effects):
        effect_location = f"{location}.effects[{index}]"
        definition = definitions.get(effect.effect_id)
        if definition is None:
            issues.append(
                ValidationIssue("error", effect_location, "존재하지 않는 effect ID입니다.")
            )
            continue
        if not isinstance(effect.order, int) or isinstance(effect.order, bool) or effect.order < 0:
            issues.append(
                ValidationIssue("error", effect_location, "효과 적용 순서는 0 이상의 정수여야 합니다.")
            )
        specs = {item.key: item for item in definition.parameters}
        for unknown in sorted(set(effect.parameters) - set(specs)):
            issues.append(
                ValidationIssue(
                    "error", effect_location, f"정의되지 않은 parameter '{unknown}'가 있습니다."
                )
            )
        for spec in specs.values():
            condition_required = bool(spec.required_when) and all(
                effect.parameters.get(key) in values
                for key, values in spec.required_when.items()
            )
            if (spec.required or condition_required) and spec.key not in effect.parameters:
                issues.append(
                    ValidationIssue(
                        "error", effect_location, f"필수 parameter '{spec.key}'가 없습니다."
                    )
                )
                continue
            if spec.key not in effect.parameters:
                continue
            value = effect.parameters[spec.key]
            valid_type = {
                "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
                "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
                "string": lambda v: isinstance(v, str),
                "boolean": lambda v: isinstance(v, bool),
                "enum": lambda v: v in spec.options,
                "identifier": lambda v: isinstance(v, str)
                and bool(SNAKE_CASE_PATTERN.fullmatch(v)),
            }.get(spec.value_type, lambda _v: True)
            if not valid_type(value):
                issues.append(
                    ValidationIssue(
                        "error", effect_location, f"parameter '{spec.key}' 자료형이 다릅니다."
                    )
                )
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if (
                    spec.minimum is not None
                    and value < spec.minimum
                    and not (spec.allow_negative and value < 0)
                ):
                    issues.append(
                        ValidationIssue("error", effect_location, f"'{spec.key}'가 최소값보다 작습니다.")
                    )
                if spec.maximum is not None and value > spec.maximum:
                    issues.append(
                        ValidationIssue("error", effect_location, f"'{spec.key}'가 최대값보다 큽니다.")
                    )
        if (
            effect.effect_id == "apply_status"
            and effect.parameters.get("status_id") not in status_ids
        ):
            issues.append(
                ValidationIssue("error", effect_location, "존재하지 않는 status ID입니다.")
            )
        if effect.effect_id == "deal_damage":
            target = effect.parameters.get("target")
            attack_range = effect.parameters.get("range")
            distance = effect.parameters.get("distance")
            if target == "self" and (attack_range is not None or distance is not None):
                issues.append(
                    ValidationIssue("error", effect_location, "자기 대상 피해에는 range/distance를 사용하지 않습니다.")
                )
            if attack_range in {"single", "all"} and distance is not None:
                if attack_range == "all" or distance != 0:
                    issues.append(
                        ValidationIssue("error", effect_location, "single은 distance 0만, all은 생략만 허용합니다.")
                    )
            if attack_range in {"left", "right", "both"} and (
                not isinstance(distance, int) or isinstance(distance, bool) or distance < 1
            ):
                issues.append(
                    ValidationIssue("error", effect_location, "방향 범위의 distance는 1 이상이어야 합니다.")
                )


def _validate_condition(
    condition: RuleCondition,
    color_ids: set[str],
    location: str,
    issues: list[ValidationIssue],
) -> None:
    if condition.kind not in CONDITION_KINDS:
        issues.append(ValidationIssue("error", location, "지원하지 않는 조건 종류입니다."))
        return
    parameters = condition.parameters
    if condition.kind in {"all_same_color", "contains_color", "color_count"}:
        color_id = parameters.get("color_id")
        if color_id is not None and color_id not in color_ids:
            issues.append(ValidationIssue("error", location, "조건의 색상 ID가 존재하지 않습니다."))
    if condition.kind == "color_count":
        count = parameters.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            issues.append(ValidationIssue("error", location, "색상 개수는 1 이상의 정수여야 합니다."))
    if condition.kind == "color_set":
        values = parameters.get("color_ids")
        if not isinstance(values, list) or not values:
            issues.append(ValidationIssue("error", location, "색상 집합이 비어 있습니다."))
        elif any(value not in color_ids for value in values):
            issues.append(ValidationIssue("error", location, "색상 집합에 없는 색상이 있습니다."))
    if condition.kind == "block_count":
        count = parameters.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            issues.append(ValidationIssue("error", location, "블록 개수는 1 이상의 정수여야 합니다."))
    if condition.kind == "tag_match" and not str(parameters.get("tag", "")).strip():
        issues.append(ValidationIssue("error", location, "조건 태그가 비어 있습니다."))


def validate_project(project: Project) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    color_ids = _ids(project.colors, "colors", issues)
    type_ids = _ids(project.block_types, "block_types", issues)
    effect_ids = _ids(project.effect_definitions, "effect_definitions", issues)
    status_ids = _ids(project.status_definitions, "status_definitions", issues)
    block_ids = _ids(project.blocks, "blocks", issues)
    _ids(project.combinations, "combinations", issues)
    _ids(project.color_synergies, "color_synergies", issues)

    for color in project.colors:
        if not HEX_PATTERN.fullmatch(color.hex):
            issues.append(ValidationIssue("error", f"colors:{color.id}", "HEX 형식이 아닙니다."))

    definitions = {item.id: item for item in project.effect_definitions}
    for definition in project.effect_definitions:
        location = f"effect_definitions:{definition.id}"
        if definition.id and not SNAKE_CASE_PATTERN.fullmatch(definition.id):
            issues.append(
                ValidationIssue(
                    "error", location, "효과 ID는 영문 소문자 snake_case여야 합니다."
                )
            )
        parameter_keys = [parameter.key for parameter in definition.parameters]
        if len(parameter_keys) != len(set(parameter_keys)):
            issues.append(ValidationIssue("error", location, "효과 입력값 키가 중복되었습니다."))
    for status in project.status_definitions:
        location = f"status_definitions:{status.id}"
        if status.id and not SNAKE_CASE_PATTERN.fullmatch(status.id):
            issues.append(
                ValidationIssue("error", location, "상태 ID는 영문 소문자 snake_case여야 합니다.")
            )
        if status.category not in {"debuff", "buff", "crowd_control", "custom"}:
            issues.append(ValidationIssue("error", location, "지원하지 않는 상태 분류입니다."))
    used_types: set[str] = set()
    used_colors: set[str] = set()
    used_blocks: set[str] = set()
    signature_seen: set[tuple[Any, ...]] = set()
    for block in project.blocks:
        location = f"blocks:{block.id}"
        if block.type_id not in type_ids:
            issues.append(ValidationIssue("error", location, "존재하지 않는 type을 참조합니다."))
        else:
            used_types.add(block.type_id)
        if block.color_id not in color_ids:
            issues.append(ValidationIssue("error", location, "존재하지 않는 색상을 참조합니다."))
        else:
            used_colors.add(block.color_id)
        if not block.cells:
            issues.append(ValidationIssue("error", location, "블록 모양이 비어 있습니다."))
        elif len(set(block.cells)) != len(block.cells):
            issues.append(ValidationIssue("error", location, "블록 칸 좌표가 중복되었습니다."))
        elif not is_connected(block.cells):
            issues.append(
                ValidationIssue(
                    "warning",
                    location,
                    "블록 모양이 분리되어 있습니다. 의도한 모양인지 확인하세요.",
                )
            )
        signature = (
            block.type_id,
            block.color_id,
            tuple(normalize_cells(block.cells)),
        )
        if signature in signature_seen:
            issues.append(ValidationIssue("warning", location, "같은 모양, type, 색상의 블록이 있습니다."))
        signature_seen.add(signature)
        if not block.effects:
            issues.append(ValidationIssue("warning", location, "블록 자체 효과가 없습니다."))
        _validate_effects(block.effects, definitions, status_ids, location, issues)

    blocks = {item.id: item for item in project.blocks}
    for combination in project.combinations:
        location = f"combinations:{combination.id}"
        if not combination.instances:
            issues.append(ValidationIssue("error", location, "조합식에 블록이 없습니다."))
        instance_ids: set[str] = set()
        for instance in combination.instances:
            if instance.instance_id in instance_ids:
                issues.append(ValidationIssue("error", location, "인스턴스 ID가 중복되었습니다."))
            instance_ids.add(instance.instance_id)
            block = blocks.get(instance.block_id)
            if block is None:
                issues.append(ValidationIssue("error", location, "존재하지 않는 블록을 참조합니다."))
                continue
            used_blocks.add(instance.block_id)
            if instance.rotation and not block.allow_rotation:
                issues.append(ValidationIssue("error", location, "허용되지 않은 회전을 사용합니다."))
            if instance.rotation not in {0, 90, 180, 270}:
                issues.append(ValidationIssue("error", location, "회전값이 올바르지 않습니다."))
            if instance.mirrored and not block.allow_mirroring:
                issues.append(ValidationIssue("error", location, "허용되지 않은 반전을 사용합니다."))
            match = instance.match
            match_location = f"{location}.instances:{instance.instance_id}.match"
            if match.kind not in SLOT_MATCH_KINDS:
                issues.append(
                    ValidationIssue("error", match_location, "지원하지 않는 슬롯 조건입니다.")
                )
            elif match.kind == "type" and match.type_id not in type_ids:
                issues.append(
                    ValidationIssue("error", match_location, "슬롯 Type이 존재하지 않습니다.")
                )
            elif match.kind == "color" and match.color_id not in color_ids:
                issues.append(
                    ValidationIssue("error", match_location, "슬롯 색상이 존재하지 않습니다.")
                )
            elif match.kind == "tag" and not (match.tag or "").strip():
                issues.append(
                    ValidationIssue("error", match_location, "슬롯 태그가 비어 있습니다.")
                )
        occupied = combination_cells(combination.instances, blocks)
        claimed: set[Any] = set()
        for cells in occupied.values():
            if claimed & cells:
                issues.append(ValidationIssue("error", location, "블록 인스턴스가 겹칩니다."))
                break
            claimed.update(cells)
        if claimed:
            width = max(c.x for c in claimed) - min(c.x for c in claimed) + 1
            height = max(c.y for c in claimed) - min(c.y for c in claimed) + 1
            if width > 3 or height > 3:
                issues.append(ValidationIssue("warning", location, "최소 3×3 거푸집보다 큽니다."))
        _validate_effects(combination.effects, definitions, status_ids, location, issues)
        for index, conditional in enumerate(combination.conditional_effects):
            conditional_location = f"{location}.conditional_effects[{index}]"
            _validate_condition(
                conditional.condition, color_ids, conditional_location, issues
            )
            if not conditional.effects:
                issues.append(
                    ValidationIssue("error", conditional_location, "조건부 효과가 비어 있습니다.")
                )
            _validate_effects(
                conditional.effects, definitions, status_ids, conditional_location, issues
            )

    for synergy in project.color_synergies:
        location = f"color_synergies:{synergy.id}"
        _validate_condition(synergy.condition, color_ids, location, issues)
        if not synergy.effects:
            issues.append(ValidationIssue("error", location, "시너지 효과가 비어 있습니다."))
        _validate_effects(synergy.effects, definitions, status_ids, location, issues)

    for item_id in sorted(type_ids - used_types):
        issues.append(ValidationIssue("warning", f"block_types:{item_id}", "사용되지 않는 type입니다."))
    for item_id in sorted(color_ids - used_colors):
        issues.append(ValidationIssue("warning", f"colors:{item_id}", "사용되지 않는 색상입니다."))
    for item_id in sorted(block_ids - used_blocks):
        issues.append(ValidationIssue("warning", f"blocks:{item_id}", "조합식에 사용되지 않는 블록입니다."))
    if not effect_ids:
        issues.append(ValidationIssue("warning", "effect_definitions", "효과 정의가 없습니다."))
    return issues
