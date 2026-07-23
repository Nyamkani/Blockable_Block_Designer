from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from ..domain.models import ConditionalEffect, Effect, EffectDefinition, RuleCondition
from .effect_editor import EffectDialog

CONDITION_LABELS = {
    "모두 같은 색": "all_same_color",
    "모두 다른 색": "all_different_colors",
    "특정 색 포함": "contains_color",
    "특정 색 개수": "color_count",
    "지정 색상 구성": "color_set",
    "모두 같은 Type": "same_type",
    "블록 개수": "block_count",
    "태그 일치": "tag_match",
}


def condition_summary(condition: RuleCondition) -> str:
    label = next(
        (label for label, kind in CONDITION_LABELS.items() if kind == condition.kind),
        condition.kind,
    )
    if condition.parameters:
        compact = json.dumps(condition.parameters, ensure_ascii=False, separators=(",", ":"))
        return f"{label} {compact}"
    return label


class ConditionalEffectDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        definitions: list[EffectDefinition],
        rule: ConditionalEffect | None = None,
    ) -> None:
        super().__init__(master)
        self.title("조건부 효과 편집")
        self.geometry("560x520")
        self.result: ConditionalEffect | None = None
        self.definitions = definitions
        self.effects = [
            Effect(
                effect.effect_id,
                effect.order,
                dict(effect.parameters),
                effect.description,
            )
            for effect in (rule.effects if rule else [])
        ]
        selected_label = next(
            (
                label
                for label, kind in CONDITION_LABELS.items()
                if rule and kind == rule.condition.kind
            ),
            "모두 같은 색",
        )
        self.condition_label = tk.StringVar(value=selected_label)
        self.description = tk.StringVar(value=rule.description if rule else "")

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="조건").pack(anchor="w")
        ttk.Combobox(
            body,
            textvariable=self.condition_label,
            values=list(CONDITION_LABELS),
            state="readonly",
        ).pack(fill="x", pady=(2, 8))
        ttk.Label(body, text="조건 Parameters (JSON 객체)").pack(anchor="w")
        self.parameters = tk.Text(body, height=7)
        self.parameters.pack(fill="x", pady=(2, 8))
        self.parameters.insert(
            "1.0",
            json.dumps(
                rule.condition.parameters if rule else {},
                ensure_ascii=False,
                indent=2,
            ),
        )
        ttk.Label(
            body,
            text=(
                "예: 특정 색 포함 {\"color_id\":\"red\"}, 색 개수 "
                "{\"color_id\":\"red\",\"count\":2}, 지정 색상 구성 "
                "{\"color_ids\":[\"red\",\"blue\"]}"
            ),
            wraplength=520,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(body, text="조건이 맞을 때 추가할 효과").pack(anchor="w")
        self.effect_list = tk.Listbox(body, height=7)
        self.effect_list.pack(fill="both", expand=True, pady=2)
        buttons = ttk.Frame(body)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="효과 추가", command=self._add_effect).pack(side="left")
        ttk.Button(buttons, text="효과 수정", command=self._edit_effect).pack(
            side="left", padx=4
        )
        ttk.Button(buttons, text="효과 삭제", command=self._delete_effect).pack(side="left")
        ttk.Label(body, text="설명").pack(anchor="w", pady=(8, 0))
        ttk.Entry(body, textvariable=self.description).pack(fill="x")
        footer = ttk.Frame(body)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(footer, text="확인", command=self._accept).pack(side="right", padx=5)
        self._refresh_effects()
        self.transient(master)
        self.grab_set()

    def _effect_name(self, effect_id: str) -> str:
        definition = next(
            (item for item in self.definitions if item.id == effect_id), None
        )
        return definition.display_name if definition else effect_id

    def _refresh_effects(self) -> None:
        self.effect_list.delete(0, "end")
        for effect in sorted(self.effects, key=lambda item: item.order):
            self.effect_list.insert(
                "end",
                f"{effect.order}: {self._effect_name(effect.effect_id)} "
                f"({effect.effect_id})",
            )

    def _add_effect(self) -> None:
        dialog = EffectDialog(self, self.definitions)
        self.wait_window(dialog)
        if dialog.result:
            self.effects.append(dialog.result)
            self._refresh_effects()

    def _selected_effect(self) -> tuple[int, Effect] | None:
        selection = self.effect_list.curselection()
        if not selection:
            return None
        ordered = sorted(enumerate(self.effects), key=lambda pair: pair[1].order)
        return ordered[selection[0]]

    def _edit_effect(self) -> None:
        selected = self._selected_effect()
        if not selected:
            return
        index, effect = selected
        dialog = EffectDialog(self, self.definitions, effect)
        self.wait_window(dialog)
        if dialog.result:
            self.effects[index] = dialog.result
            self._refresh_effects()

    def _delete_effect(self) -> None:
        selected = self._selected_effect()
        if selected:
            del self.effects[selected[0]]
            self._refresh_effects()

    def _accept(self) -> None:
        try:
            parameters = json.loads(self.parameters.get("1.0", "end").strip() or "{}")
            if not isinstance(parameters, dict):
                raise ValueError("조건 Parameters는 JSON 객체여야 합니다.")
            if not self.effects:
                raise ValueError("추가 효과를 하나 이상 지정하세요.")
        except (json.JSONDecodeError, ValueError) as error:
            messagebox.showerror("입력 오류", str(error), parent=self)
            return
        self.result = ConditionalEffect(
            RuleCondition(CONDITION_LABELS[self.condition_label.get()], parameters),
            self.effects,
            self.description.get().strip(),
        )
        self.destroy()


class ConditionalEffectList(ttk.LabelFrame):
    def __init__(
        self,
        master: tk.Misc,
        rules_getter,
        definitions_getter,
        changed,
        title: str = "조건부 보너스",
    ) -> None:
        super().__init__(master, text=title, padding=6)
        self.rules_getter = rules_getter
        self.definitions_getter = definitions_getter
        self.changed = changed
        self.listbox = tk.Listbox(self, height=5)
        self.listbox.pack(fill="both", expand=True)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(buttons, text="추가", command=self.add).pack(side="left")
        ttk.Button(buttons, text="수정", command=self.edit).pack(side="left", padx=4)
        ttk.Button(buttons, text="삭제", command=self.delete).pack(side="left")
        self.listbox.bind("<Double-1>", lambda _event: self.edit())

    def refresh(self) -> None:
        self.listbox.delete(0, "end")
        for rule in self.rules_getter():
            self.listbox.insert(
                "end", f"{condition_summary(rule.condition)} → {len(rule.effects)}개 효과"
            )

    def add(self) -> None:
        dialog = ConditionalEffectDialog(self, self.definitions_getter())
        self.wait_window(dialog)
        if dialog.result:
            self.rules_getter().append(dialog.result)
            self.changed()
            self.refresh()

    def edit(self) -> None:
        selection = self.listbox.curselection()
        rules = self.rules_getter()
        if not selection:
            return
        dialog = ConditionalEffectDialog(
            self, self.definitions_getter(), rules[selection[0]]
        )
        self.wait_window(dialog)
        if dialog.result:
            rules[selection[0]] = dialog.result
            self.changed()
            self.refresh()

    def delete(self) -> None:
        selection = self.listbox.curselection()
        if selection:
            del self.rules_getter()[selection[0]]
            self.changed()
            self.refresh()

