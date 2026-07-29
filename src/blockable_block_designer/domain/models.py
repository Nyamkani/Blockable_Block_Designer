from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "1.1.0"
DATA_TYPE = "blockable_block_design"
SUPPORTED_SCHEMA_VERSIONS = {"1.0.0", "1.1.0", "1.2.0"}
EFFECT_TYPES = {
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
EFFECT_TARGETS = {"SELECTED", "self", "all"}
EFFECT_PARAMETER_IDS = {
    "BASE_DAMAGE": {"NONE"},
    "BASE_HIT_COUNT": {"CURRENT_ACTION"},
    "INDEPENDENT_DAMAGE": {"NONE"},
    "BLOCK": {"NONE"},
    "RECOVERY": {"NONE"},
    "STATUS_DAMAGE": {"BURN", "BLEEDING", "POISON"},
    "DEBUFF": {"ATTACK_REDUCTION", "DAMAGE_TAKEN_INCREASE"},
    "CROWD_CONTROL": {"STUN", "FREEZE", "ACTION_LOCK"},
    "BUFF": {"DAMAGE_BONUS", "RAGE", "ATTACK_MULTIPLIER"},
    "EXTRA_TURN": {"CURRENT_ACTION", "PLAYER_TURN"},
    "DECK_CAPACITY": {"MAIN_DECK"},
    "DRAW": {"MAIN_DECK"},
    "PLACEMENT_COUNT": {"CURRENT_ACTION", "BLOCK_PLACEMENT"},
}
BLOCK_GRADES = {"normal", "special", "legend", "curse"}
BLOCK_COLORS = {"steel", "nature", "fire", "water", "none"}


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
    grade: str = "normal"
    color: str = "none"


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
    required_when: dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectDefinition:
    id: str
    display_name: str
    parameters: list[EffectParameterDefinition] = field(default_factory=list)
    description: str = ""


@dataclass
class StatusDefinition:
    id: str
    display_name: str
    category: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)


@dataclass
class Effect:
    effect_id: str
    order: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    effect_name: str = ""
    target: str = "self"
    value: int | float | None = None
    type: str = ""
    parameter_id: str = "NONE"
    duration: int = 0
    intensify: int = 0
    reference_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


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
        Color("steel", "강철", "#9E9E9E"),
        Color("nature", "자연", "#43A047"),
        Color("fire", "불", "#E53935"),
        Color("water", "물", "#1E88E5"),
        Color("none", "무색", "#64748B"),
    ]


def legacy_effect_definitions() -> list[EffectDefinition]:
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


STANDARD_EFFECT_IDS = {
    "deal_damage",
    "gain_block",
    "heal",
    "apply_status",
    "draw_block",
    "gain_gold",
    "modify_next_effect",
}


def standard_effect_definitions() -> list[EffectDefinition]:
    target_self = ["self"]
    target_combat = ["self", "enemy"]
    ranges = ["single", "left", "right", "both", "all"]
    target_labels = {"self": "자신", "enemy": "적"}
    range_labels = {
        "single": "선택 대상 하나",
        "left": "중심과 왼쪽",
        "right": "중심과 오른쪽",
        "both": "중심과 좌우",
        "all": "모든 적",
    }
    return [
        EffectDefinition(
            "deal_damage",
            "피해",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_combat, display_name="대상",
                    option_labels=target_labels,
                ),
                EffectParameterDefinition(
                    "range",
                    "enum",
                    False,
                    options=ranges,
                    display_name="공격 범위",
                    option_labels=range_labels,
                    required_when={"target": ["enemy"]},
                ),
                EffectParameterDefinition(
                    "distance",
                    "integer",
                    False,
                    minimum=0,
                    display_name="범위 거리",
                    required_when={"range": ["left", "right", "both"]},
                ),
                EffectParameterDefinition(
                    "amount", "number", True, minimum=0, display_name="피해량"
                ),
            ],
            "지정된 대상에게 amount만큼 피해를 가합니다.",
        ),
        EffectDefinition(
            "gain_block",
            "방어도 획득",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_self, display_name="대상",
                    option_labels=target_labels, default="self"
                ),
                EffectParameterDefinition(
                    "amount", "integer", True, minimum=0, display_name="방어도"
                ),
            ],
            "대상의 현재 방어도에 amount를 더합니다.",
        ),
        EffectDefinition(
            "heal",
            "회복",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_self, display_name="대상",
                    option_labels=target_labels, default="self"
                ),
                EffectParameterDefinition(
                    "amount", "number", True, minimum=0, display_name="회복량"
                ),
            ],
            "대상의 현재 체력을 amount만큼 회복합니다.",
        ),
        EffectDefinition(
            "apply_status",
            "상태 효과 적용",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_combat, display_name="대상",
                    option_labels=target_labels,
                ),
                EffectParameterDefinition(
                    "status_id", "enum", True, display_name="상태 효과"
                ),
                EffectParameterDefinition(
                    "stacks", "integer", True, minimum=1, display_name="중첩 수", default=1
                ),
                EffectParameterDefinition(
                    "duration", "integer", False, minimum=1, display_name="지속 턴"
                ),
            ],
            "대상에게 status_id로 지정된 상태 효과를 부여합니다.",
        ),
        EffectDefinition(
            "draw_block",
            "블록 뽑기",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_self, display_name="대상",
                    option_labels=target_labels, default="self"
                ),
                EffectParameterDefinition(
                    "count", "integer", True, minimum=1, display_name="추가 블록 수"
                ),
            ],
            "다음 드로우에서 count만큼 블록을 추가로 뽑습니다.",
        ),
        EffectDefinition(
            "gain_gold",
            "골드 획득",
            [
                EffectParameterDefinition(
                    "target", "enum", True, options=target_self, display_name="대상",
                    option_labels=target_labels, default="self"
                ),
                EffectParameterDefinition(
                    "amount", "integer", True, minimum=0, display_name="골드"
                ),
            ],
            "플레이어가 보유한 런 골드를 amount만큼 증가시킵니다.",
        ),
        EffectDefinition(
            "modify_next_effect",
            "다음 효과 변경 (예약)",
            [
                EffectParameterDefinition(
                    "multiplier", "number", True, minimum=0, display_name="배율"
                )
            ],
            "런타임 적용 규칙이 확정되지 않은 예약 효과입니다.",
        ),
    ]


def default_status_definitions() -> list[StatusDefinition]:
    return [
        StatusDefinition("bleeding", "출혈", "debuff", "턴 종료 시 방어 무시 피해를 받고 스택이 감소합니다.", ["bleed"]),
        StatusDefinition("burn", "화상", "debuff", "턴 종료 시 피해를 받고 스택이 절반으로 감소합니다."),
        StatusDefinition("weakness", "약화", "debuff", "주는 피해가 스택당 감소합니다.", ["weak"]),
        StatusDefinition("wound", "상처", "debuff", "받는 피해가 스택당 증가합니다.", ["injury", "injry"]),
        StatusDefinition("stun", "기절", "crowd_control", "다음 행동을 취소하며 최대 1스택입니다."),
        StatusDefinition("double_attack", "연속 공격", "buff", "다음 공격 피해를 2배로 하고 1스택을 소비합니다.", ["doubleAttack"]),
    ]


def default_effect_definitions() -> list[EffectDefinition]:
    """Return the current canonical combat-effect definitions."""
    return standard_effect_definitions()


@dataclass
class Project:
    schema_version: str = SCHEMA_VERSION
    data_type: str = DATA_TYPE
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "project_name": "Blockable",
            "designer_name": "Blockable Block Designer",
        }
    )
    colors: list[Color] = field(default_factory=default_colors)
    block_types: list[BlockType] = field(default_factory=list)
    effect_definitions: list[EffectDefinition] = field(
        default_factory=list
    )
    status_definitions: list[StatusDefinition] = field(
        default_factory=list
    )
    blocks: list[Block] = field(default_factory=list)
    combinations: list[Combination] = field(default_factory=list)
    color_synergies: list[ColorSynergy] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)
