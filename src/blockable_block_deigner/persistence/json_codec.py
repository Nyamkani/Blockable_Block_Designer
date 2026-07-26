from __future__ import annotations

from typing import Any

from ..domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Color,
    ColorSynergy,
    Combination,
    ConditionalEffect,
    Effect,
    EffectDefinition,
    EffectParameterDefinition,
    Project,
    RuleCondition,
    SlotMatch,
)

KNOWN_TOP_LEVEL = {
    "schema_version",
    "metadata",
    "colors",
    "block_types",
    "effect_definitions",
    "blocks",
    "combinations",
    "color_synergies",
}


def _effect_from_dict(data: dict[str, Any]) -> Effect:
    return Effect(
        effect_id=data.get("effect_id", ""),
        order=data.get("order", 0),
        parameters=dict(data.get("parameters", {})),
        description=data.get("description", ""),
    )


def _effect_to_dict(effect: Effect) -> dict[str, Any]:
    result: dict[str, Any] = {
        "effect_id": effect.effect_id,
        "order": effect.order,
        "parameters": effect.parameters,
    }
    if effect.description:
        result["description"] = effect.description
    return result


def _condition_from_dict(data: dict[str, Any]) -> RuleCondition:
    return RuleCondition(
        kind=data.get("kind", ""),
        parameters=dict(data.get("parameters", {})),
    )


def _condition_to_dict(condition: RuleCondition) -> dict[str, Any]:
    return {"kind": condition.kind, "parameters": condition.parameters}


def _conditional_effect_from_dict(data: dict[str, Any]) -> ConditionalEffect:
    return ConditionalEffect(
        condition=_condition_from_dict(data.get("condition", {})),
        effects=[_effect_from_dict(effect) for effect in data.get("effects", [])],
        description=data.get("description", ""),
    )


def _conditional_effect_to_dict(item: ConditionalEffect) -> dict[str, Any]:
    return {
        "condition": _condition_to_dict(item.condition),
        "effects": [_effect_to_dict(effect) for effect in item.effects],
        "description": item.description,
    }


def _slot_match_from_dict(data: dict[str, Any]) -> SlotMatch:
    return SlotMatch(
        kind=data.get("kind", "exact_block"),
        type_id=data.get("type_id"),
        color_id=data.get("color_id"),
        tag=data.get("tag"),
    )


def _slot_match_to_dict(match: SlotMatch) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": match.kind}
    if match.type_id:
        result["type_id"] = match.type_id
    if match.color_id:
        result["color_id"] = match.color_id
    if match.tag:
        result["tag"] = match.tag
    return result


def project_from_dict(data: dict[str, Any]) -> Project:
    if not isinstance(data, dict):
        raise ValueError("최상위 JSON 값은 객체여야 합니다.")
    colors = [
        Color(item.get("id", ""), item.get("display_name", ""), item.get("hex", ""))
        for item in data.get("colors", [])
    ]
    block_types = [
        BlockType(
            item.get("id", ""),
            item.get("display_name", ""),
            item.get("description", ""),
        )
        for item in data.get("block_types", [])
    ]
    effect_definitions = []
    for item in data.get("effect_definitions", []):
        parameters = [
            EffectParameterDefinition(
                key=parameter.get("key", ""),
                value_type=parameter.get("value_type", "string"),
                required=parameter.get("required", False),
                minimum=parameter.get("minimum"),
                maximum=parameter.get("maximum"),
                options=list(parameter.get("options", [])),
                display_name=parameter.get("display_name", ""),
                description=parameter.get("description", ""),
                option_labels=dict(parameter.get("option_labels", {})),
            )
            for parameter in item.get("parameters", [])
        ]
        effect_definitions.append(
            EffectDefinition(
                item.get("id", ""),
                item.get("display_name", ""),
                parameters,
                item.get("description", ""),
            )
        )
    blocks = [
        Block(
            id=item.get("id", ""),
            display_name=item.get("display_name", ""),
            type_id=item.get("type_id", ""),
            color_id=item.get("color_id", ""),
            cells=[
                Cell(cell.get("x", 0), cell.get("y", 0))
                for cell in item.get("shape", {}).get("cells", [])
            ],
            allow_rotation=item.get("transform", {}).get("allow_rotation", True),
            allow_mirroring=item.get("transform", {}).get("allow_mirroring", False),
            effects=[_effect_from_dict(effect) for effect in item.get("effects", [])],
            tags=list(item.get("tags", [])),
            description=item.get("description", ""),
        )
        for item in data.get("blocks", [])
    ]
    combinations = []
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
                        match=_slot_match_from_dict(instance.get("match", {})),
                    )
                    for instance in item.get("instances", [])
                ],
                allow_recipe_rotation=item.get("match_options", {}).get(
                    "allow_recipe_rotation", True
                ),
                allow_recipe_mirroring=item.get("match_options", {}).get(
                    "allow_recipe_mirroring", False
                ),
                effects=[_effect_from_dict(effect) for effect in item.get("effects", [])],
                conditional_effects=[
                    _conditional_effect_from_dict(effect)
                    for effect in item.get("conditional_effects", [])
                ],
                tags=list(item.get("tags", [])),
                description=item.get("description", ""),
            )
        )
    color_synergies = [
        ColorSynergy(
            id=item.get("id", ""),
            display_name=item.get("display_name", ""),
            condition=_condition_from_dict(item.get("condition", {})),
            effects=[_effect_from_dict(effect) for effect in item.get("effects", [])],
            description=item.get("description", ""),
            enabled=item.get("enabled", True),
        )
        for item in data.get("color_synergies", [])
    ]
    return Project(
        schema_version=data.get("schema_version", ""),
        metadata=dict(data.get("metadata", {})),
        colors=colors,
        block_types=block_types,
        effect_definitions=effect_definitions,
        blocks=blocks,
        combinations=combinations,
        color_synergies=color_synergies,
        extra={key: value for key, value in data.items() if key not in KNOWN_TOP_LEVEL},
    )


def _parameter_to_dict(parameter: EffectParameterDefinition) -> dict[str, Any]:
    result: dict[str, Any] = {
        "key": parameter.key,
        "value_type": parameter.value_type,
        "required": parameter.required,
    }
    if parameter.minimum is not None:
        result["minimum"] = parameter.minimum
    if parameter.maximum is not None:
        result["maximum"] = parameter.maximum
    if parameter.options:
        result["options"] = parameter.options
    if parameter.display_name:
        result["display_name"] = parameter.display_name
    if parameter.description:
        result["description"] = parameter.description
    if parameter.option_labels:
        result["option_labels"] = parameter.option_labels
    return result


def project_to_dict(project: Project) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": project.schema_version,
        "metadata": project.metadata,
        "colors": [
            {"id": item.id, "display_name": item.display_name, "hex": item.hex}
            for item in project.colors
        ],
        "block_types": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "description": item.description,
            }
            for item in project.block_types
        ],
        "effect_definitions": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "parameters": [_parameter_to_dict(p) for p in item.parameters],
                "description": item.description,
            }
            for item in project.effect_definitions
        ],
        "blocks": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "type_id": item.type_id,
                "color_id": item.color_id,
                "shape": {
                    "cells": [{"x": cell.x, "y": cell.y} for cell in item.cells]
                },
                "transform": {
                    "allow_rotation": item.allow_rotation,
                    "allow_mirroring": item.allow_mirroring,
                },
                "effects": [_effect_to_dict(effect) for effect in item.effects],
                "tags": item.tags,
                "description": item.description,
            }
            for item in project.blocks
        ],
        "combinations": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "instances": [
                    {
                        "instance_id": instance.instance_id,
                        "block_id": instance.block_id,
                        "origin": {
                            "x": instance.origin.x,
                            "y": instance.origin.y,
                        },
                        "rotation": instance.rotation,
                        "mirrored": instance.mirrored,
                        "match": _slot_match_to_dict(instance.match),
                    }
                    for instance in item.instances
                ],
                "match_options": {
                    "allow_recipe_rotation": item.allow_recipe_rotation,
                    "allow_recipe_mirroring": item.allow_recipe_mirroring,
                },
                "effects": [_effect_to_dict(effect) for effect in item.effects],
                "conditional_effects": [
                    _conditional_effect_to_dict(effect)
                    for effect in item.conditional_effects
                ],
                "tags": item.tags,
                "description": item.description,
            }
            for item in project.combinations
        ],
        "color_synergies": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "condition": _condition_to_dict(item.condition),
                "effects": [_effect_to_dict(effect) for effect in item.effects],
                "description": item.description,
                "enabled": item.enabled,
            }
            for item in project.color_synergies
        ],
    }
    result.update(project.extra)
    return result
