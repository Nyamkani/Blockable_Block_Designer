from __future__ import annotations

from typing import Any

from ..domain.models import (
    DATA_TYPE,
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Color,
    Combination,
    Effect,
    EffectDefinition,
    EffectParameterDefinition,
    Project,
)

COLOR_HEX = {
    "steel": "#9E9E9E",
    "nature": "#43A047",
    "fire": "#E53935",
    "water": "#1E88E5",
    "none": "#64748B",
}

DEFAULT_PARAMETER_ID = {
    "BASE_DAMAGE": "NONE",
    "BASE_HIT_COUNT": "CURRENT_ACTION",
    "INDEPENDENT_DAMAGE": "NONE",
    "BLOCK": "NONE",
    "RECOVERY": "NONE",
    "EXTRA_TURN": "CURRENT_ACTION",
    "DECK_CAPACITY": "MAIN_DECK",
    "DRAW": "MAIN_DECK",
    "PLACEMENT_COUNT": "CURRENT_ACTION",
}


def _normalized_target(value: str) -> str:
    return {
        "SELF": "self",
        "ALL": "all",
        "LEFT": "L1",
        "RIGHT": "R1",
    }.get(value, value)


def _parameter_defaults(effect_type: str, reference_id: str | None = None) -> tuple[str, int, int]:
    parameter_id = reference_id or DEFAULT_PARAMETER_ID.get(effect_type, "NONE")
    if parameter_id in {"weakness", "weak"}:
        parameter_id = "ATTACK_REDUCTION"
    elif parameter_id in {"wound", "injury", "injry"}:
        parameter_id = "DAMAGE_TAKEN_INCREASE"
    elif parameter_id == "stun":
        parameter_id = "STUN"
    elif parameter_id in {"burn", "bleeding", "bleed"}:
        parameter_id = "BURN" if parameter_id == "burn" else "BLEEDING"
    duration = 1 if (effect_type, parameter_id) == ("CROWD_CONTROL", "STUN") else 0
    fixed_intensify = {
        ("CROWD_CONTROL", "STUN"),
        ("BASE_HIT_COUNT", "CURRENT_ACTION"),
        ("EXTRA_TURN", "CURRENT_ACTION"),
        ("DRAW", "MAIN_DECK"),
        ("PLACEMENT_COUNT", "CURRENT_ACTION"),
    }
    return parameter_id, duration, 1 if (effect_type, parameter_id) in fixed_intensify else 0


def _effect_from_new(data: dict[str, Any], migrate_missing: bool = False) -> Effect:
    known = {
        "effect_id", "effect_name", "description", "target", "value", "type",
        "reference_id", "parameters",
    }
    parameters = data.get("parameters")
    if not isinstance(parameters, dict):
        parameter_id, duration, intensify = _parameter_defaults(
            data.get("type", ""), data.get("reference_id")
        )
        missing_parameters = not migrate_missing
    else:
        default_id, default_duration, default_intensify = _parameter_defaults(
            data.get("type", ""), data.get("reference_id")
        )
        parameter_id = parameters.get(
            "id", default_id
        )
        duration = parameters.get("duration", default_duration)
        intensify = parameters.get("intensify", default_intensify)
        missing_parameters = any(
            key not in parameters for key in ("id", "duration", "intensify")
        ) and not migrate_missing
    return Effect(
        effect_id=data.get("effect_id", ""),
        description=data.get("description", ""),
        effect_name=data.get("effect_name", ""),
        target=_normalized_target(data.get("target", "")),
        value=data.get("value"),
        type=data.get("type", ""),
        parameter_id=parameter_id,
        duration=duration,
        intensify=intensify,
        reference_id=data.get("reference_id"),
        extra={
            **{key: value for key, value in data.items() if key not in known},
            **({"_missing_parameters": True} if missing_parameters else {}),
        },
    )


def _effect_to_new(effect: Effect) -> dict[str, Any]:
    result: dict[str, Any] = {
        "effect_id": effect.effect_id,
        "effect_name": effect.effect_name,
        "description": effect.description,
        "target": effect.target,
        "value": effect.value,
        "type": effect.type,
        "parameters": {
            "id": effect.parameter_id,
            "duration": effect.duration,
            "intensify": effect.intensify,
        },
    }
    return result


def _legacy_effect(
    data: dict[str, Any], owner_id: str, index: int
) -> Effect:
    legacy_id = data.get("effect_id", "")
    parameters = dict(data.get("parameters", {}))
    status_id = parameters.get("status_id") or parameters.get("buff_id")
    mapping = {
        "deal_damage": ("BASE_DAMAGE", "SELECTED", parameters.get("amount")),
        "gain_block": ("BLOCK", "self", parameters.get("amount", parameters.get("count"))),
        "gain_defense": ("BLOCK", "self", parameters.get("amount")),
        "heal": ("RECOVERY", "self", parameters.get("amount")),
        "draw_block": ("DRAW", "self", parameters.get("count")),
        "gain_extra_turn": ("EXTRA_TURN", "self", parameters.get("turns")),
    }
    if legacy_id in {"apply_status", "apply_buff"}:
        if status_id == "stun":
            effect_type = "CROWD_CONTROL"
        elif status_id in {"burn", "bleeding", "bleed"}:
            effect_type = "STATUS_DAMAGE"
        elif status_id in {"double_attack", "doubleAttack"}:
            effect_type = "BUFF"
        else:
            effect_type = "DEBUFF"
        target = "self" if effect_type == "BUFF" else "SELECTED"
        value = parameters.get("stacks", parameters.get("amount", 1))
    else:
        effect_type, target, value = mapping.get(
            legacy_id, ("", "", parameters.get("amount", parameters.get("value")))
        )
    legacy_target = parameters.get("target")
    if legacy_target in {"enemy", "player"}:
        target = "SELECTED"
    elif legacy_target == "all_enemies":
        target = "all"
    elif legacy_target == "self":
        target = "self"
    parameter_id, duration, intensify = _parameter_defaults(effect_type, status_id)
    if effect_type in {"STATUS_DAMAGE", "DEBUFF", "CROWD_CONTROL", "BUFF"}:
        duration = parameters.get("duration", 0)
        intensify = parameters.get("stacks", parameters.get("amount", 1))
    return Effect(
        effect_id=f"{owner_id}_{effect_type.lower()}_{index + 1:02d}",
        description=data.get("description", ""),
        effect_name=legacy_id or effect_type,
        target=target,
        value=value,
        type=effect_type,
        parameter_id=parameter_id,
        duration=duration,
        intensify=intensify,
        reference_id=status_id,
        extra={
            "_legacy_parameter_keys": sorted(
                set(parameters)
                - {
                    "target", "amount", "count", "status_id", "buff_id",
                    "status_name", "buff_name", "stacks", "duration", "turns",
                    "value", "range", "distance",
                }
            )
        },
    )


def _derived_grade(type_id: str) -> str:
    lowered = type_id.lower()
    if "curse" in lowered:
        return "curse"
    if "legend" in lowered:
        return "legend"
    if "special" in lowered:
        return "special"
    return "normal"


def _project_from_new(data: dict[str, Any]) -> Project:
    migrate_missing = data.get("schema_version") != "1.1.0"
    blocks: list[Block] = []
    type_map: dict[str, BlockType] = {}
    colors: dict[str, Color] = {}
    for item in data.get("blocks", []):
        block_type = item.get("block_type", {})
        type_id = block_type.get("type_id", "")
        color_id = block_type.get("color", "none")
        type_map.setdefault(
            type_id,
            BlockType(
                type_id,
                block_type.get("type_name", ""),
                grade=block_type.get("grade", ""),
                color=color_id,
            ),
        )
        colors.setdefault(
            color_id,
            Color(color_id, color_id, COLOR_HEX.get(color_id, "#64748B")),
        )
        blocks.append(
            Block(
                id=item.get("block_id", ""),
                display_name=item.get("block_name", ""),
                type_id=type_id,
                color_id=color_id,
                cells=[
                    Cell(cell.get("x", 0), cell.get("y", 0))
                    for cell in item.get("shape", {}).get("cells", [])
                ],
                allow_rotation=item.get("transform_rule", {}).get("allow_rotation", True),
                allow_mirroring=item.get("transform_rule", {}).get("allow_reflection", False),
                effects=[
                    _effect_from_new(effect, migrate_missing)
                    for effect in item.get("effects", [])
                ],
                description=item.get("description", ""),
            )
        )
    combinations = [
        Combination(
            id=item.get("combination_id", ""),
            display_name=item.get("combination_name", ""),
            instances=[
                BlockInstance(
                    instance_id=instance.get("instance_id", ""),
                    block_id=instance.get("block_id", ""),
                    origin=Cell(
                        instance.get("origin", {}).get("x", 0),
                        instance.get("origin", {}).get("y", 0),
                    ),
                    rotation=instance.get("rotation", 0),
                    mirrored=instance.get("reflected", False),
                )
                for instance in item.get("formula", {}).get("instances", [])
            ],
            allow_recipe_rotation=item.get("transform_rule", {}).get("allow_rotation", True),
            allow_recipe_mirroring=item.get("transform_rule", {}).get("allow_reflection", False),
            effects=[
                _effect_from_new(effect, migrate_missing)
                for effect in item.get("effects", [])
            ],
            description=item.get("description", ""),
        )
        for item in data.get("combinations", [])
    ]
    metadata = dict(data.get("metadata", {}))
    if migrate_missing:
        unknown_effect_fields = sorted(
            {
                key
                for effect in [
                    *(effect for block in blocks for effect in block.effects),
                    *(effect for combo in combinations for effect in combo.effects),
                ]
                for key in effect.extra
                if not key.startswith("_")
            }
        )
        if unknown_effect_fields:
            notes = list(metadata.get("migration_notes", []))
            notes.append(
                "1.0 효과의 추가 필드를 확인해야 합니다: "
                + ", ".join(unknown_effect_fields)
            )
            metadata["migration_notes"] = notes
    return Project(
        schema_version=data.get("schema_version", ""),
        data_type=data.get("data_type", ""),
        metadata=metadata,
        colors=list(colors.values()),
        block_types=list(type_map.values()),
        effect_definitions=[],
        status_definitions=[],
        blocks=blocks,
        combinations=combinations,
        color_synergies=[],
        extra={"migrated_from_legacy": True} if migrate_missing else {},
    )


def _project_from_legacy(data: dict[str, Any]) -> Project:
    type_names = {
        item.get("id", ""): item.get("display_name", "")
        for item in data.get("block_types", [])
    }
    colors_by_id = {
        item.get("id", ""): Color(
            item.get("id", ""), item.get("display_name", ""), item.get("hex", "#64748B")
        )
        for item in data.get("colors", [])
    }
    blocks: list[Block] = []
    type_map: dict[str, BlockType] = {}
    for item in data.get("blocks", []):
        type_id = item.get("type_id", "")
        old_color = item.get("color_id", "")
        color_id = old_color if old_color in COLOR_HEX else "none"
        type_map.setdefault(
            type_id,
            BlockType(
                type_id,
                type_names.get(type_id, type_id),
                grade=_derived_grade(type_id),
                color=color_id,
            ),
        )
        blocks.append(
            Block(
                id=item.get("id", ""),
                display_name=item.get("display_name", ""),
                type_id=type_id,
                color_id=color_id,
                cells=[
                    Cell(cell.get("x", 0), cell.get("y", 0))
                    for cell in item.get("shape", {}).get("cells", [])
                ],
                allow_rotation=item.get("transform", {}).get("allow_rotation", True),
                allow_mirroring=item.get("transform", {}).get("allow_mirroring", False),
                effects=[
                    _legacy_effect(effect, item.get("id", "block"), index)
                    for index, effect in enumerate(item.get("effects", []))
                ],
                description=item.get("description", ""),
            )
        )
    combinations: list[Combination] = []
    for item in data.get("combinations", []):
        combinations.append(
            Combination(
                id=item.get("id", ""),
                display_name=item.get("display_name", ""),
                instances=[
                    BlockInstance(
                        instance_id=instance.get("instance_id", ""),
                        block_id=instance.get("block_id", ""),
                        origin=Cell(
                            instance.get("origin", {}).get("x", 0),
                            instance.get("origin", {}).get("y", 0),
                        ),
                        rotation=instance.get("rotation", 0),
                        mirrored=instance.get("mirrored", False),
                    )
                    for instance in item.get("instances", [])
                ],
                allow_recipe_rotation=item.get("match_options", {}).get(
                    "allow_recipe_rotation", True
                ),
                allow_recipe_mirroring=item.get("match_options", {}).get(
                    "allow_recipe_mirroring", False
                ),
                effects=[
                    _legacy_effect(effect, item.get("id", "combination"), index)
                    for index, effect in enumerate(item.get("effects", []))
                ],
                description=item.get("description", ""),
            )
        )
    notes: list[str] = []
    conditional_count = sum(
        len(item.get("conditional_effects", []))
        for item in data.get("combinations", [])
    )
    if conditional_count:
        notes.append(
            f"레거시 conditional_effects {conditional_count}개는 새 조합식 스키마의 대상이 아닙니다."
        )
    if data.get("color_synergies"):
        notes.append(
            f"레거시 color_synergies {len(data['color_synergies'])}개는 본 게임 공통 판정으로 이전해야 합니다."
        )
    ambiguous_effects = [
        effect.effect_id
        for block in blocks
        for effect in block.effects
        if not effect.type
    ]
    ambiguous_effects.extend(
        effect.effect_id
        for combination in combinations
        for effect in combination.effects
        if not effect.type
    )
    if ambiguous_effects:
        notes.append(
            "7.4 의미를 확정할 수 없는 레거시 효과: "
            + ", ".join(ambiguous_effects)
        )
    legacy_parameter_keys = sorted(
        {
            key
            for effect in [
                *(effect for block in blocks for effect in block.effects),
                *(effect for combo in combinations for effect in combo.effects),
            ]
            for key in effect.extra.get("_legacy_parameter_keys", [])
        }
    )
    if legacy_parameter_keys:
        notes.append(
            "자동 이전하지 않은 레거시 효과 parameter 키: "
            + ", ".join(legacy_parameter_keys)
        )
    metadata = dict(data.get("metadata", {}))
    metadata["designer_name"] = "Blockable Block Designer"
    if notes:
        metadata["migration_notes"] = notes
    return Project(
        schema_version=data.get("schema_version", ""),
        data_type=DATA_TYPE,
        metadata=metadata,
        colors=list(colors_by_id.values()),
        block_types=list(type_map.values()),
        effect_definitions=[],
        status_definitions=[],
        blocks=blocks,
        combinations=combinations,
        color_synergies=[],
        extra={"migrated_from_legacy": True},
    )


def project_from_dict(data: dict[str, Any]) -> Project:
    if not isinstance(data, dict):
        raise ValueError("최상위 JSON 값은 객체여야 합니다.")
    if "data_type" in data and data.get("data_type") != DATA_TYPE:
        raise ValueError("지원하지 않는 data_type입니다.")
    if data.get("data_type") == DATA_TYPE:
        return _project_from_new(data)
    return _project_from_legacy(data)


def project_to_dict(project: Project) -> dict[str, Any]:
    types = {item.id: item for item in project.block_types}
    blocks = []
    for item in project.blocks:
        block_type = types.get(
            item.type_id,
            BlockType(item.type_id, item.type_id, grade="normal", color=item.color_id),
        )
        blocks.append(
            {
                "block_id": item.id,
                "block_name": item.display_name,
                "description": item.description,
                "block_type": {
                    "type_id": item.type_id,
                    "type_name": block_type.display_name,
                    "grade": block_type.grade,
                    "color": item.color_id,
                },
                "shape": {
                    "cells": [{"x": cell.x, "y": cell.y} for cell in item.cells]
                },
                "transform_rule": {
                    "allow_rotation": item.allow_rotation,
                    "allow_reflection": item.allow_mirroring,
                },
                "effects": [_effect_to_new(effect) for effect in item.effects],
            }
        )
    return {
        "schema_version": project.schema_version,
        "data_type": DATA_TYPE,
        "metadata": project.metadata,
        "blocks": blocks,
        "combinations": [
            {
                "combination_id": item.id,
                "combination_name": item.display_name,
                "description": item.description,
                "formula": {
                    "instances": [
                        {
                            "instance_id": instance.instance_id,
                            "block_id": instance.block_id,
                            "origin": {"x": instance.origin.x, "y": instance.origin.y},
                            "rotation": instance.rotation,
                            "reflected": instance.mirrored,
                        }
                        for instance in item.instances
                    ]
                },
                "transform_rule": {
                    "allow_rotation": item.allow_recipe_rotation,
                    "allow_reflection": item.allow_recipe_mirroring,
                },
                "effects": [_effect_to_new(effect) for effect in item.effects],
            }
            for item in project.combinations
        ],
    }


# Effect definition config helpers are retained only for importing legacy config files.
def _parameter_to_dict(parameter: EffectParameterDefinition) -> dict[str, Any]:
    return {
        "key": parameter.key,
        "value_type": parameter.value_type,
        "required": parameter.required,
        "minimum": parameter.minimum,
        "maximum": parameter.maximum,
        "options": parameter.options,
        "display_name": parameter.display_name,
        "description": parameter.description,
        "option_labels": parameter.option_labels,
        "default": parameter.default,
        "allow_negative": parameter.allow_negative,
        "required_when": parameter.required_when,
    }


def effect_definition_from_dict(data: dict[str, Any]) -> EffectDefinition:
    return EffectDefinition(
        data.get("id", ""),
        data.get("display_name", ""),
        [
            EffectParameterDefinition(
                key=item.get("key", ""),
                value_type=item.get("value_type", "string"),
                required=item.get("required", False),
                minimum=item.get("minimum"),
                maximum=item.get("maximum"),
                options=list(item.get("options", [])),
                display_name=item.get("display_name", ""),
                description=item.get("description", ""),
                option_labels=dict(item.get("option_labels", {})),
                default=item.get("default"),
                allow_negative=item.get("allow_negative", False),
                required_when=dict(item.get("required_when", {})),
            )
            for item in data.get("parameters", [])
        ],
        data.get("description", ""),
    )


def effect_definition_to_dict(definition: EffectDefinition) -> dict[str, Any]:
    return {
        "id": definition.id,
        "display_name": definition.display_name,
        "parameters": [_parameter_to_dict(item) for item in definition.parameters],
        "description": definition.description,
    }
