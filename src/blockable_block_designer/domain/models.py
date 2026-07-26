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
    display_name: str = ""
    description: str = ""
    option_labels: dict[str, str] = field(default_factory=dict)
    default: Any = None
    allow_negative: bool = False


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
                EffectParameterDefinition(
                    "amount", "number", True, display_name="값(피해량)", allow_negative=True
                ),
                EffectParameterDefinition(
                    "target",
                    "enum",
                    False,
                    options=["enemy", "all_enemies"],
                    display_name="대상",
                    option_labels={"enemy": "적 1명", "all_enemies": "모든 적"},
                ),
            ],
        ),
        EffectDefinition(
            "gain_block",
            "블록 획득",
            [EffectParameterDefinition("count", "integer", True, minimum=1, display_name="값(개수)")],
        ),
        EffectDefinition(
            "heal",
            "회복",
            [
                EffectParameterDefinition(
                    "amount", "number", True, display_name="값(회복량)", allow_negative=True
                )
            ],
        ),
        EffectDefinition(
            "gain_defense",
            "방어 획득",
            [
                EffectParameterDefinition(
                    "amount", "number", True, display_name="값(방어량)", allow_negative=True
                )
            ],
        ),
        EffectDefinition(
            "apply_status",
            "상태·디버프 적용",
            [
                EffectParameterDefinition(
                    "status_name", "string", True, display_name="상태명(한글 설명)"
                ),
                EffectParameterDefinition(
                    "status_id", "identifier", True, display_name="상태 ID(영문 JSON 값)"
                ),
                EffectParameterDefinition(
                    "stacks", "integer", False, minimum=1, display_name="값(중첩 수)"
                ),
                EffectParameterDefinition(
                    "duration", "integer", False, minimum=1, display_name="지속 턴"
                ),
            ],
        ),
        EffectDefinition(
            "apply_buff",
            "버프 적용",
            [
                EffectParameterDefinition(
                    "buff_name", "string", True, display_name="버프명(한글 설명)"
                ),
                EffectParameterDefinition(
                    "buff_id", "identifier", True, display_name="버프 ID(영문 JSON 값)"
                ),
                EffectParameterDefinition(
                    "amount", "number", False, display_name="값(버프 수치)", allow_negative=True
                ),
                EffectParameterDefinition(
                    "duration", "integer", False, minimum=1, display_name="지속 턴"
                ),
            ],
        ),
        EffectDefinition(
            "draw_block",
            "블록 뽑기",
            [EffectParameterDefinition("count", "integer", True, minimum=1, display_name="값(개수)")],
        ),
        EffectDefinition(
            "gain_gold",
            "골드 획득",
            [
                EffectParameterDefinition(
                    "amount", "integer", True, display_name="값(골드)", allow_negative=True
                )
            ],
        ),
        EffectDefinition(
            "modify_next_effect",
            "다음 효과 변경",
            [
                EffectParameterDefinition(
                    "multiplier", "number", True, minimum=0, display_name="값(배율)"
                )
            ],
        ),
        EffectDefinition(
            "gain_extra_turn",
            "추가 턴 진행",
            [
                EffectParameterDefinition(
                    "turns", "integer", True, minimum=1, display_name="추가 턴 수", default=1
                )
            ],
            "현재 행동 뒤에 지정한 수만큼 추가 턴을 진행합니다.",
        ),
        EffectDefinition(
            "repeat_each_turn",
            "매 턴 효과 반복",
            [
                EffectParameterDefinition(
                    "effect_id", "identifier", True, display_name="반복 효과 ID",
                    description="매 턴 실행할 별도 효과의 영문 ID입니다.",
                ),
                EffectParameterDefinition(
                    "amount", "number", False, display_name="매 턴 값", allow_negative=True
                ),
                EffectParameterDefinition(
                    "duration", "integer", True, minimum=1, display_name="지속 턴", default=1
                ),
                EffectParameterDefinition(
                    "target",
                    "string",
                    False,
                    display_name="대상",
                    description="게임에서 해석할 대상 ID입니다.",
                ),
            ],
            "지정한 효과를 일정 턴 동안 매 턴 실행합니다.",
        ),
        EffectDefinition(
            "deal_damage_each_turn",
            "매 턴 공격",
            [
                EffectParameterDefinition(
                    "amount", "number", True, display_name="턴당 피해량", allow_negative=True
                ),
                EffectParameterDefinition(
                    "duration", "integer", True, minimum=1, display_name="반복 턴", default=1
                ),
                EffectParameterDefinition("target", "string", False, display_name="대상"),
            ],
            "지정한 턴 동안 매 턴 대상에게 피해를 줍니다.",
        ),
        EffectDefinition(
            "gain_defense_each_turn",
            "매 턴 방어 획득",
            [
                EffectParameterDefinition(
                    "amount", "number", True, display_name="턴당 방어량", allow_negative=True
                ),
                EffectParameterDefinition(
                    "duration", "integer", True, minimum=1, display_name="반복 턴", default=1
                ),
            ],
            "지정한 턴 동안 매 턴 방어를 획득합니다.",
        ),
        EffectDefinition(
            "heal_each_turn",
            "매 턴 회복",
            [
                EffectParameterDefinition(
                    "amount", "number", True, display_name="턴당 회복량", allow_negative=True
                ),
                EffectParameterDefinition(
                    "duration", "integer", True, minimum=1, display_name="반복 턴", default=1
                ),
            ],
            "지정한 턴 동안 매 턴 체력을 회복합니다.",
        ),
        EffectDefinition(
            "apply_status_each_turn",
            "매 턴 상태이상 부여",
            [
                EffectParameterDefinition(
                    "status_name", "string", True, display_name="상태명(한글 설명)"
                ),
                EffectParameterDefinition(
                    "status_id", "identifier", True, display_name="상태 ID(영문 JSON 값)"
                ),
                EffectParameterDefinition(
                    "stacks", "integer", False, minimum=1, display_name="매 턴 중첩 수"
                ),
                EffectParameterDefinition(
                    "repeat_turns", "integer", True, minimum=1, display_name="반복 턴", default=1
                ),
                EffectParameterDefinition(
                    "status_duration", "integer", False, minimum=1, display_name="상태 지속 턴"
                ),
                EffectParameterDefinition("target", "string", False, display_name="대상"),
            ],
            "지정한 턴 동안 매 턴 대상에게 상태이상을 부여합니다.",
        ),
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
