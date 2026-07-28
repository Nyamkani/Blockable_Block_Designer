from __future__ import annotations

from collections import OrderedDict

from ..domain.models import Combination, Effect, Project


EFFECT_LABELS = {
    "BASE_DAMAGE": "공격력",
    "BASE_HIT_COUNT": "공격 횟수",
    "INDEPENDENT_DAMAGE": "독립 공격",
    "BLOCK": "방어",
    "RECOVERY": "회복",
    "STATUS_DAMAGE": "상태 피해",
    "DEBUFF": "디버프",
    "CROWD_CONTROL": "행동 제어",
    "BUFF": "버프",
    "EXTRA_TURN": "추가 턴",
    "DECK_CAPACITY": "덱 한도",
    "DRAW": "드로우",
    "PLACEMENT_COUNT": "배치 횟수",
}
ATTACK_EFFECT_TYPES = {
    "BASE_DAMAGE",
    "INDEPENDENT_DAMAGE",
    "STATUS_DAMAGE",
}


def _effect_label(effect: Effect) -> str:
    return EFFECT_LABELS.get(effect.type, effect.effect_name or effect.effect_id)


def _target_label(target: str) -> str:
    fixed = {
        "SELECTED": "선택 대상",
        "self": "자신",
        "all": "전체",
    }
    if target in fixed:
        return fixed[target]
    if len(target) >= 2 and target[0] in {"L", "R", "B"} and target[1:].isdigit():
        distance = int(target[1:])
        direction = {
            "L": "기준+왼쪽",
            "R": "기준+오른쪽",
            "B": "기준+좌우",
        }[target[0]]
        return f"{direction} {distance}칸"
    return target


def _summarize(effects: list[Effect]) -> str:
    totals: OrderedDict[tuple[str, str], int] = OrderedDict()
    consecutive_attacks: list[str] = []
    for effect in effects:
        if not isinstance(effect.value, int) or isinstance(effect.value, bool):
            continue
        if effect.type == "BASE_HIT_COUNT":
            target = _target_label(effect.target)
            consecutive_attacks.append(
                f"연속 공격: 데미지 {effect.value} × {effect.intensify}회"
                f"{f' [{target}]' if target else ''}"
            )
            continue
        label = _effect_label(effect)
        target = (
            _target_label(effect.target)
            if effect.type in ATTACK_EFFECT_TYPES
            else ""
        )
        key = (label, target)
        totals[key] = totals.get(key, 0) + effect.value
    summaries = [
        f"{label} {value}{f' [{target}]' if target else ''}"
        for (label, target), value in totals.items()
    ]
    summaries.extend(consecutive_attacks)
    return ", ".join(summaries)


def combination_effect_preview(
    project: Project, combination: Combination | None
) -> list[str]:
    """Return a design-time estimate without runtime color/grade synergies."""
    if combination is None:
        return ["조합식을 선택하면 예상 효과가 표시됩니다."]

    blocks = {block.id: block for block in project.blocks}
    block_effects = [
        effect
        for instance in combination.instances
        if (block := blocks.get(instance.block_id)) is not None
        for effect in block.effects
    ]
    lines: list[str] = []
    if summary := _summarize(block_effects):
        lines.append(summary)
    if summary := _summarize(combination.effects):
        name = combination.display_name or combination.id
        lines.append(f"{name}: {summary}")
    if not lines:
        lines.append("등록된 블록·조합식 효과가 없습니다.")
    return lines
