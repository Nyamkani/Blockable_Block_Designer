from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from ..domain.models import (
    Effect,
    EffectDefinition,
    Project,
    STANDARD_EFFECT_IDS,
    default_effect_definitions,
    default_status_definitions,
)

EFFECT_ID_ALIASES = {
    "damage": "deal_damage",
    "deal_damage_effect": "deal_damage",
    "gain_defense": "gain_block",
    "gain_defence": "gain_block",
    "defense": "gain_block",
    "defence": "gain_block",
    "recovery": "heal",
    "restore_health": "heal",
    "apply_buff": "apply_status",
    "add_status": "apply_status",
    "draw": "draw_block",
    "draw_blocks": "draw_block",
    "gold": "gain_gold",
    "add_gold": "gain_gold",
}

EFFECT_DISPLAY_NAME_ALIASES = {
    "피해": "deal_damage",
    "데미지": "deal_damage",
    "방어 획득": "gain_block",
    "방어도 획득": "gain_block",
    "회복": "heal",
    "치유": "heal",
    "상태 적용": "apply_status",
    "상태 효과 적용": "apply_status",
    "상태·디버프 적용": "apply_status",
    "버프 적용": "apply_status",
    "블록 뽑기": "draw_block",
    "블록 드로우": "draw_block",
    "골드 획득": "gain_gold",
}

COMPATIBLE_PARAMETER_KEYS = {
    "deal_damage": {"target", "range", "distance", "amount", "value", "damage"},
    "gain_block": {"target", "amount", "value", "count"},
    "heal": {"target", "amount", "value", "heal"},
    "apply_status": {
        "target", "status_id", "status_name", "stacks", "duration",
        "buff_id", "buff_name", "amount",
    },
    "draw_block": {"target", "count", "amount"},
    "gain_gold": {"target", "amount", "value", "count"},
    "modify_next_effect": {"multiplier"},
}

STATUS_ALIASES = {
    "bleed": "bleeding",
    "weak": "weakness",
    "injury": "wound",
    "injry": "wound",
    "doubleAttack": "double_attack",
}


def iter_effects(project: Project) -> Iterable[Effect]:
    for block in project.blocks:
        yield from block.effects
    for combination in project.combinations:
        yield from combination.effects
        for conditional in combination.conditional_effects:
            yield from conditional.effects
    for synergy in project.color_synergies:
        yield from synergy.effects


def _canonical_definition_id(definition: EffectDefinition) -> str | None:
    if definition.id in STANDARD_EFFECT_IDS:
        return definition.id
    candidate = EFFECT_ID_ALIASES.get(definition.id)
    if candidate is None:
        # Exact display-name matches are intentionally conservative. Extended
        # effects such as "매 턴 피해" must retain their custom semantics.
        candidate = EFFECT_DISPLAY_NAME_ALIASES.get(definition.display_name.strip())
    if candidate is None:
        return None
    parameter_keys = {item.key for item in definition.parameters}
    if not parameter_keys <= COMPATIBLE_PARAMETER_KEYS[candidate]:
        return None
    return candidate


def _migrate_effect(effect: Effect, definition_aliases: dict[str, str]) -> None:
    parameters = effect.parameters
    original_effect_id = effect.effect_id
    effect.effect_id = definition_aliases.get(effect.effect_id, effect.effect_id)
    if original_effect_id == "apply_buff" or "buff_id" in parameters:
        if "buff_id" in parameters and "status_id" not in parameters:
            parameters["status_id"] = parameters.pop("buff_id")
        if "amount" in parameters and "stacks" not in parameters:
            parameters["stacks"] = parameters.pop("amount")
        parameters.pop("buff_name", None)
    if effect.effect_id in {"deal_damage", "gain_block", "heal", "gain_gold"}:
        for old_key in ("value", "damage", "heal", "count"):
            if old_key in parameters and "amount" not in parameters:
                parameters["amount"] = parameters.pop(old_key)
    if effect.effect_id == "draw_block" and "amount" in parameters:
        parameters.setdefault("count", parameters.pop("amount"))
    if effect.effect_id == "gain_block" and "count" in parameters:
        parameters.setdefault("amount", parameters.pop("count"))
    if parameters.get("target") == "player":
        parameters["target"] = "enemy"
    if parameters.get("target") == "all_enemies":
        parameters["target"] = "enemy"
        parameters["range"] = "all"
    if effect.effect_id in {"gain_block", "heal", "draw_block", "gain_gold"}:
        parameters["target"] = "self"
    elif effect.effect_id == "deal_damage":
        parameters.setdefault("target", "enemy")
        if parameters["target"] == "enemy":
            parameters.setdefault("range", "single")
            if parameters["range"] in {"single", "all"}:
                parameters.pop("distance", None)
        else:
            parameters.pop("range", None)
            parameters.pop("distance", None)
    elif effect.effect_id == "apply_status":
        parameters.pop("status_name", None)
        status_id = parameters.get("status_id")
        if isinstance(status_id, str):
            parameters["status_id"] = STATUS_ALIASES.get(status_id, status_id)
        parameters.setdefault("stacks", 1)
        parameters.setdefault(
            "target",
            "self" if parameters.get("status_id") == "double_attack" else "enemy",
        )
        if parameters.get("status_id") == "stun":
            parameters["stacks"] = 1


def migrate_effect_standard(project: Project) -> None:
    """Normalize legacy data and install the immutable combat-effect standard."""
    definition_aliases = {
        definition.id: canonical
        for definition in project.effect_definitions
        if (canonical := _canonical_definition_id(definition)) is not None
    }
    defined_ids = {definition.id for definition in project.effect_definitions}
    for legacy_id, canonical in EFFECT_ID_ALIASES.items():
        if legacy_id not in defined_ids:
            definition_aliases[legacy_id] = canonical
    for effect in iter_effects(project):
        _migrate_effect(effect, definition_aliases)

    standard = {item.id: item for item in default_effect_definitions()}
    custom = [
        item
        for item in project.effect_definitions
        if item.id not in definition_aliases
    ]
    project.effect_definitions = [deepcopy(item) for item in standard.values()] + custom

    statuses = {item.id: deepcopy(item) for item in default_status_definitions()}
    for item in project.status_definitions:
        if item.id not in statuses:
            statuses[item.id] = item
    project.status_definitions = list(statuses.values())

    status_ids = [item.id for item in project.status_definitions]
    status_labels = {item.id: item.display_name for item in project.status_definitions}
    apply_status = next(
        item for item in project.effect_definitions if item.id == "apply_status"
    )
    status_parameter = next(
        item for item in apply_status.parameters if item.key == "status_id"
    )
    status_parameter.options = status_ids
    status_parameter.option_labels = status_labels
