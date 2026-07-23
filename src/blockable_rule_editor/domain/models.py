from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "1.1.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0.0", SCHEMA_VERSION}


@dataclass(frozen=True, order=True)
class Cell:
    x: int
    y: int


@dataclass
class Color:
    id: str
    display_name: str
    hex: str


@dataclass
class BlockType:
    id: str
    display_name: str
    description: str = ""


@dataclass
class EffectParameterDefinition:
    key: str
    value_type: str
    required: bool = False
    minimum: float | None = None
    maximum: float | None = None
    options: list[Any] = field(default_factory=list)


@dataclass
class EffectDefinition:
    id: str
    display_name: str
    parameters: list[EffectParameterDefinition] = field(default_factory=list)
    description: str = ""


@dataclass
class Effect:
    effect_id: str
    order: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class Block:
    id: str
    display_name: str
    type_id: str
    color_id: str
    cells: list[Cell] = field(default_factory=list)
    allow_rotation: bool = True
    allow_mirroring: bool = False
    effects: list[Effect] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class BlockInstance:
    instance_id: str
    block_id: str
    origin: Cell = field(default_factory=lambda: Cell(0, 0))
    rotation: int = 0
    mirrored: bool = False
    match: SlotMatch = field(default_factory=lambda: SlotMatch())


@dataclass
class SlotMatch:
    """A recipe slot constraint. The instance block remains its shape template."""

    kind: str = "exact_block"
    type_id: str | None = None
    color_id: str | None = None
    tag: str | None = None


@dataclass
class RuleCondition:
    kind: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionalEffect:
    condition: RuleCondition
    effects: list[Effect] = field(default_factory=list)
    description: str = ""


@dataclass
class Combination:
    id: str
    display_name: str
    instances: list[BlockInstance] = field(default_factory=list)
    allow_recipe_rotation: bool = True
    allow_recipe_mirroring: bool = False
    effects: list[Effect] = field(default_factory=list)
    conditional_effects: list[ConditionalEffect] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ColorSynergy:
    id: str
    display_name: str
    condition: RuleCondition
    effects: list[Effect] = field(default_factory=list)
    description: str = ""
    enabled: bool = True


def default_colors() -> list[Color]:
    return [
        Color("red", "빨간색", "#E53935"),
        Color("orange", "주황색", "#FB8C00"),
        Color("yellow", "노란색", "#FDD835"),
        Color("green", "초록색", "#43A047"),
        Color("blue", "파란색", "#1E88E5"),
        Color("indigo", "남색", "#3949AB"),
        Color("purple", "보라색", "#8E24AA"),
    ]


def default_effect_definitions() -> list[EffectDefinition]:
    return [
        EffectDefinition(
            "deal_damage",
            "피해",
            [
                EffectParameterDefinition("amount", "number", True, minimum=0),
                EffectParameterDefinition(
                    "target", "enum", False, options=["enemy", "all_enemies"]
                ),
            ],
        ),
        EffectDefinition("gain_block", "블록 획득"),
        EffectDefinition("heal", "회복"),
        EffectDefinition("apply_status", "상태 적용"),
        EffectDefinition("draw_block", "블록 뽑기"),
        EffectDefinition("gain_gold", "골드 획득"),
        EffectDefinition("modify_next_effect", "다음 효과 변경"),
    ]


@dataclass
class Project:
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, Any] = field(
        default_factory=lambda: {"project_name": "Blockable", "ruleset_name": "prototype"}
    )
    colors: list[Color] = field(default_factory=default_colors)
    block_types: list[BlockType] = field(default_factory=list)
    effect_definitions: list[EffectDefinition] = field(
        default_factory=default_effect_definitions
    )
    blocks: list[Block] = field(default_factory=list)
    combinations: list[Combination] = field(default_factory=list)
    color_synergies: list[ColorSynergy] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)
