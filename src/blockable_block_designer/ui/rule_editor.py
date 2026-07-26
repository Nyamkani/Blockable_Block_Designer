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
        condition_combo = ttk.Combobox(
            body,
            textvariable=self.condition_label,
            values=list(CONDITION_LABELS),
            state="readonly",
        )
        condition_combo.pack(fill="x", pady=(2, 8))
        condition_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._render_condition_inputs()
        )
        self.condition_input_frame = ttk.LabelFrame(
            body, text="조건 값", padding=8
        )
        self.condition_input_frame.pack(fill="x", pady=(0, 8))
        self.condition_inputs: dict[str, tk.StringVar] = {}
        self.initial_condition_parameters = (
            dict(rule.condition.parameters) if rule else {}
        )
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
        self._render_condition_inputs()
        self._refresh_effects()
        self.transient(master)
        self.grab_set()

    def _effect_name(self, effect_id: str) -> str:
        definition = next(
            (item for item in self.definitions if item.id == effect_id), None
        )
        return definition.display_name if definition else effect_id

    def _render_condition_inputs(self) -> None:
        for child in self.condition_input_frame.winfo_children():
            child.destroy()
        self.condition_inputs.clear()
        kind = CONDITION_LABELS[self.condition_label.get()]
        fields: list[tuple[str, str]] = []
        if kind == "contains_color":
            fields = [("color_id", "색상 ID")]
        elif kind == "color_count":
            fields = [("color_id", "색상 ID"), ("count", "개수")]
        elif kind == "color_set":
            fields = [("color_ids", "색상 ID 목록(쉼표 구분)")]
        elif kind == "block_count":
            fields = [("count", "블록 개수")]
        elif kind == "tag_match":
            fields = [("tag", "태그")]
        if not fields:
            ttk.Label(
                self.condition_input_frame,
                text="이 조건은 추가 입력값이 필요하지 않습니다.",
            ).grid(row=0, column=0, sticky="w")
            return
        for row, (key, label) in enumerate(fields):
            current = self.initial_condition_parameters.get(key, "")
            if isinstance(current, list):
                current = ", ".join(str(item) for item in current)
            variable = tk.StringVar(value=str(current))
            ttk.Label(self.condition_input_frame, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=3
            )
            ttk.Entry(
                self.condition_input_frame, textvariable=variable, width=35
            ).grid(row=row, column=1, sticky="ew", pady=3)
            self.condition_inputs[key] = variable
        self.condition_input_frame.columnconfigure(1, weight=1)

    def _condition_parameters(self) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, variable in self.condition_inputs.items():
            value = variable.get().strip()
            if not value:
                raise ValueError("조건 값을 모두 입력하세요.")
            if key == "count":
                result[key] = int(value)
            elif key == "color_ids":
                values = [item.strip() for item in value.split(",") if item.strip()]
                if not values:
                    raise ValueError("색상 ID를 하나 이상 입력하세요.")
                result[key] = values
            else:
                result[key] = value
        return result

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
            parameters = self._condition_parameters()
            if not self.effects:
                raise ValueError("추가 효과를 하나 이상 지정하세요.")
        except ValueError as error:
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
