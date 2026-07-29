from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

from ..domain.models import (
    EFFECT_PARAMETER_IDS,
    EFFECT_TYPES,
    Effect,
    EffectDefinition,
)

TYPE_LABELS = {
    "BASE_DAMAGE": "기본 공격",
    "BASE_HIT_COUNT": "이번 행동 연속 기본 공격",
    "INDEPENDENT_DAMAGE": "독립 공격",
    "BLOCK": "방어도",
    "RECOVERY": "회복",
    "STATUS_DAMAGE": "상태 피해",
    "DEBUFF": "디버프",
    "CROWD_CONTROL": "군중 제어",
    "BUFF": "버프",
    "EXTRA_TURN": "추가 턴",
    "DECK_CAPACITY": "덱 용량",
    "DRAW": "드로우",
    "PLACEMENT_COUNT": "배치 횟수",
}
PARAMETER_DETAILS = {
    ("BASE_HIT_COUNT", "CURRENT_ACTION"): "이번 행동 연속 기본 공격 · 구현",
    ("STATUS_DAMAGE", "BURN"): "화상 · 구현",
    ("STATUS_DAMAGE", "BLEEDING"): "출혈 · 구현",
    ("STATUS_DAMAGE", "POISON"): "독 · 미구현",
    ("DEBUFF", "ATTACK_REDUCTION"): "약화 · 구현",
    ("DEBUFF", "DAMAGE_TAKEN_INCREASE"): "상처 · 구현",
    ("CROWD_CONTROL", "STUN"): "기절 · 구현",
    ("CROWD_CONTROL", "FREEZE"): "냉동 · 미구현",
    ("CROWD_CONTROL", "ACTION_LOCK"): "행동 정지 · 미구현",
    ("BUFF", "DAMAGE_BONUS"): "데미지 직접 추가 · 처리기 연결",
    ("BUFF", "RAGE"): "분노 · 미구현 ID",
    ("BUFF", "ATTACK_MULTIPLIER"): "데미지 배율 증가 · 미구현",
    ("EXTRA_TURN", "CURRENT_ACTION"): "플레이어 추가 턴 · 임시 ID 구현",
    ("EXTRA_TURN", "PLAYER_TURN"): "플레이어 추가 턴 · 최종 후보 ID 미연결",
    ("DECK_CAPACITY", "MAIN_DECK"): "사용자 덱 용량 증가 · 값 보존만 지원",
    ("DRAW", "MAIN_DECK"): "주머니 추가 드로우 · 구현",
    ("PLACEMENT_COUNT", "CURRENT_ACTION"): "블록 배치 횟수 증가 · 임시 ID 구현",
    ("PLACEMENT_COUNT", "BLOCK_PLACEMENT"): "블록 배치 횟수 증가 · 최종 후보 ID 미연결",
}
UNIMPLEMENTED_PARAMETER_IDS = {
    ("STATUS_DAMAGE", "POISON"),
    ("CROWD_CONTROL", "FREEZE"),
    ("CROWD_CONTROL", "ACTION_LOCK"),
    ("BUFF", "RAGE"),
    ("BUFF", "ATTACK_MULTIPLIER"),
    ("EXTRA_TURN", "PLAYER_TURN"),
    ("PLACEMENT_COUNT", "BLOCK_PLACEMENT"),
}
TARGET_VALUES = ["SELECTED", "self", "L1", "R1", "B1", "all"]
FIXED_PARAMETERS = {
    "BASE_DAMAGE": ("NONE", 0, 0),
    "INDEPENDENT_DAMAGE": ("NONE", 0, 0),
    "BLOCK": ("NONE", 0, 0),
    "RECOVERY": ("NONE", 0, 0),
}


class EffectDialog(tk.Toplevel):
    def __init__(self, master, definitions=None, effect=None, used_effect_ids=None):
        super().__init__(master)
        self.title("7.4 공통 효과 편집")
        self.resizable(False, False)
        self.result: Effect | None = None
        self.used_effect_ids = set(used_effect_ids or ())
        if effect is not None:
            self.used_effect_ids.discard(effect.effect_id)
        self.definitions: list[EffectDefinition] = list(definitions or [])
        self.definition_by_label = {
            self._definition_label(item): item for item in self.definitions
        }
        selected_definition = next(
            (
                item
                for item in self.definitions
                if effect is not None and item.id == effect.effect_id
            ),
            None,
        )
        self.definition_value = tk.StringVar(
            value=(
                self._definition_label(selected_definition)
                if selected_definition is not None
                else ""
            )
        )
        self.effect_id = tk.StringVar(value=effect.effect_id if effect else "")
        self.effect_name = tk.StringVar(value=effect.effect_name if effect else "")
        self.type_value = tk.StringVar(value=effect.type if effect else "BASE_DAMAGE")
        self.target = tk.StringVar(value=effect.target if effect else "SELECTED")
        self.value = tk.StringVar(
            value="" if not effect or effect.value is None else str(effect.value)
        )
        self.parameter_id = tk.StringVar(
            value=effect.parameter_id if effect else "NONE"
        )
        self.parameter_display = tk.StringVar()
        self.parameter_label_to_id: dict[str, str] = {}
        self.duration = tk.StringVar(value=str(effect.duration if effect else 0))
        self.intensify = tk.StringVar(value=str(effect.intensify if effect else 0))
        self.description = tk.StringVar(value=effect.description if effect else "")

        body = ttk.Frame(self, padding=12)
        body.grid(sticky="nsew")
        ttk.Label(body, text="저장된 효과 설정").grid(
            row=0, column=0, sticky="w", pady=4
        )
        definition_combo = ttk.Combobox(
            body,
            textvariable=self.definition_value,
            values=list(self.definition_by_label),
            state="readonly",
            width=32,
        )
        definition_combo.grid(row=0, column=1, sticky="ew", pady=4)
        definition_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._definition_changed()
        )
        rows = [
            ("효과 ID", self.effect_id, "entry"),
            ("효과 이름", self.effect_name, "entry"),
            ("실행 Type", self.type_value, "type"),
            ("대상", self.target, "target"),
            ("값", self.value, "entry"),
            ("Parameters ID", self.parameter_id, "parameter_id"),
            ("지속 턴", self.duration, "entry"),
            ("강도/추가 스택", self.intensify, "entry"),
            ("설명", self.description, "entry"),
        ]
        for row, (label, variable, kind) in enumerate(rows, start=1):
            label_widget = ttk.Label(body, text=label)
            label_widget.grid(row=row, column=0, sticky="w", pady=4)
            if kind == "type":
                widget = ttk.Combobox(
                    body, textvariable=variable, values=sorted(EFFECT_TYPES),
                    state="readonly", width=32,
                )
            elif kind == "target":
                widget = ttk.Combobox(
                    body, textvariable=variable, values=TARGET_VALUES,
                    state="normal", width=32,
                )
            elif kind == "parameter_id":
                widget = ttk.Combobox(
                    body,
                    textvariable=self.parameter_display,
                    state="readonly",
                    width=32,
                )
                self.parameter_id_combo = widget
                widget.bind(
                    "<<ComboboxSelected>>",
                    lambda _event: self._parameter_selected(),
                )
            else:
                widget = ttk.Entry(body, textvariable=variable, width=35)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            if kind == "type":
                widget.bind("<<ComboboxSelected>>", lambda _event: self._type_changed())
            elif label == "지속 턴":
                self.duration_entry = widget
            elif label == "강도/추가 스택":
                self.intensify_entry = widget
                self.intensify_label = label_widget
            elif label == "값":
                self.value_label = label_widget
                self.value_entry = widget
        self.parameter_help_label = ttk.Label(body, foreground="#64748B")
        self.parameter_help_label.grid(
            row=len(rows) + 1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0),
        )
        ttk.Label(
            body,
            text="대상: SELECTED, self, Lx/Rx/Bx, all · 비율은 10 또는 0.1을 10%로 해석합니다.",
            foreground="#64748B",
        ).grid(row=len(rows) + 2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        buttons = ttk.Frame(body)
        buttons.grid(
            row=len(rows) + 3,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(12, 0),
        )
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="확인", command=self._accept).pack(side="right", padx=6)
        self.transient(master)
        self.grab_set()
        self._type_changed(preserve=True)

    @staticmethod
    def _definition_label(definition: EffectDefinition) -> str:
        return f"{definition.display_name} · {definition.id}"

    def _definition_changed(self) -> None:
        definition = self.definition_by_label.get(self.definition_value.get())
        if definition is None:
            return
        effect_id = definition.id
        suffix = 2
        while effect_id in self.used_effect_ids:
            effect_id = f"{definition.id}_{suffix}"
            suffix += 1
        self.effect_id.set(effect_id)
        self.effect_name.set(definition.display_name)
        self.description.set(definition.description)

    def _type_changed(self, preserve: bool = False) -> None:
        effect_type = self.type_value.get()
        options = sorted(EFFECT_PARAMETER_IDS.get(effect_type, set()))
        self.parameter_label_to_id = {
            self._parameter_option_label(effect_type, parameter_id): parameter_id
            for parameter_id in options
        }
        self.parameter_id_combo.configure(values=list(self.parameter_label_to_id))
        self.value_label.configure(
            text="기본 공격 1타의 B"
            if effect_type == "BASE_HIT_COUNT"
            else "값"
        )
        self.intensify_label.configure(
            text="총 공격 횟수 H"
            if effect_type == "BASE_HIT_COUNT"
            else "강도/추가 스택"
        )
        self.value_entry.configure(state="normal")
        fixed = FIXED_PARAMETERS.get(effect_type)
        if fixed:
            self._set_parameter_id(fixed[0])
            self.duration.set(str(fixed[1]))
            self.intensify.set(str(fixed[2]))
            self.parameter_id_combo.configure(state="disabled")
            self.duration_entry.configure(state="disabled")
            self.intensify_entry.configure(state="disabled")
        elif effect_type == "BASE_HIT_COUNT":
            self._set_parameter_id("CURRENT_ACTION")
            self.duration.set("0")
            self.parameter_id_combo.configure(state="disabled")
            self.duration_entry.configure(state="disabled")
            self.intensify_entry.configure(state="normal")
            try:
                hit_count = int(self.intensify.get())
            except ValueError:
                hit_count = 0
            if not preserve or hit_count < 1:
                self.intensify.set("1")
        else:
            self.parameter_id_combo.configure(state="readonly")
            self.duration_entry.configure(state="normal")
            self.intensify_entry.configure(state="normal")
            if not preserve or self.parameter_id.get() not in options:
                self._set_parameter_id(options[0] if options else "")
            else:
                self._set_parameter_id(self.parameter_id.get())
        self._parameter_changed()

    @staticmethod
    def _parameter_option_label(effect_type: str, parameter_id: str) -> str:
        suffix = (
            " (미구현 ID)"
            if (effect_type, parameter_id) in UNIMPLEMENTED_PARAMETER_IDS
            else ""
        )
        return f"{parameter_id}{suffix}"

    def _set_parameter_id(self, parameter_id: str) -> None:
        self.parameter_id.set(parameter_id)
        self.parameter_display.set(
            self._parameter_option_label(self.type_value.get(), parameter_id)
            if parameter_id
            else ""
        )

    def _parameter_selected(self) -> None:
        parameter_id = self.parameter_label_to_id.get(self.parameter_display.get())
        if parameter_id is not None:
            self.parameter_id.set(parameter_id)
        self._parameter_changed()

    def _parameter_changed(self) -> None:
        pair = (self.type_value.get(), self.parameter_id.get())
        self.parameter_help_label.configure(
            text=PARAMETER_DETAILS.get(pair, "Parameters ID를 사용하지 않는 Type입니다.")
        )
        if pair == ("CROWD_CONTROL", "STUN"):
            self.value.set("0")
            self.duration.set("1")
            self.intensify.set("1")
            self.value_entry.configure(state="disabled")
            self.duration_entry.configure(state="disabled")
            self.intensify_entry.configure(state="disabled")
            return
        self.value_entry.configure(state="normal")
        fixed_one = {
            ("EXTRA_TURN", "CURRENT_ACTION"),
            ("DRAW", "MAIN_DECK"),
            ("PLACEMENT_COUNT", "CURRENT_ACTION"),
        }
        if pair in fixed_one:
            self.duration.set("0")
            self.intensify.set("1")
            self.duration_entry.configure(state="disabled")
            self.intensify_entry.configure(state="disabled")
        elif self.type_value.get() not in FIXED_PARAMETERS:
            self.duration_entry.configure(state="normal")
            self.intensify_entry.configure(state="normal")

    def _accept(self) -> None:
        try:
            raw = self.value.get().strip()
            value = (
                int(raw)
                if all(character not in raw.lower() for character in ".e")
                else float(raw)
            )
            if not math.isfinite(value):
                raise ValueError("value는 유한한 숫자여야 합니다.")
            duration = int(self.duration.get())
            intensify = int(self.intensify.get())
            if not self.effect_id.get().strip():
                raise ValueError("효과 ID를 입력하세요.")
            if not self.effect_name.get().strip():
                raise ValueError("효과 이름을 입력하세요.")
            if self.type_value.get() == "BASE_HIT_COUNT" and intensify < 1:
                raise ValueError("이번 행동의 총 공격 횟수 H는 1 이상이어야 합니다.")
            integer_value_pairs = {
                ("EXTRA_TURN", "CURRENT_ACTION"),
                ("EXTRA_TURN", "PLAYER_TURN"),
                ("DECK_CAPACITY", "MAIN_DECK"),
                ("DRAW", "MAIN_DECK"),
                ("PLACEMENT_COUNT", "CURRENT_ACTION"),
                ("PLACEMENT_COUNT", "BLOCK_PLACEMENT"),
            }
            if (
                (self.type_value.get(), self.parameter_id.get())
                in integer_value_pairs
                and not isinstance(value, int)
            ):
                raise ValueError("횟수·용량 효과의 value는 정수여야 합니다.")
        except ValueError as error:
            messagebox.showerror("입력 오류", str(error), parent=self)
            return
        self.result = Effect(
            effect_id=self.effect_id.get().strip(),
            description=self.description.get().strip(),
            effect_name=self.effect_name.get().strip(),
            target=self.target.get(),
            value=value,
            type=self.type_value.get(),
            parameter_id=self.parameter_id.get(),
            duration=duration,
            intensify=intensify,
        )
        self.destroy()


class EffectList(ttk.LabelFrame):
    def __init__(
        self, master, effects_getter, definitions_getter, changed,
        definitions_changed=None, effect_ids_getter=None,
    ) -> None:
        super().__init__(master, text="7.4 공통 효과", padding=6)
        self.effects_getter = effects_getter
        self.definitions_getter = definitions_getter
        self.changed = changed
        self.open_definitions = definitions_changed
        self.effect_ids_getter = effect_ids_getter or (
            lambda: {effect.effect_id for effect in self.effects_getter()}
        )
        self.listbox = tk.Listbox(self, height=5)
        self.listbox.pack(fill="both", expand=True)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(buttons, text="추가", command=self.add).pack(side="left")
        ttk.Button(buttons, text="수정", command=self.edit).pack(side="left", padx=4)
        ttk.Button(buttons, text="삭제", command=self.delete).pack(side="left")
        ttk.Button(buttons, text="위", command=lambda: self.move(-1)).pack(side="left", padx=(8, 2))
        ttk.Button(buttons, text="아래", command=lambda: self.move(1)).pack(side="left")
        if self.open_definitions is not None:
            ttk.Button(
                buttons, text="효과 설정", command=self.open_definitions
            ).pack(side="right")
        self.listbox.bind("<Double-1>", lambda _event: self.edit())

    def refresh(self) -> None:
        self.listbox.delete(0, "end")
        for item in self.effects_getter():
            name = TYPE_LABELS.get(item.type, item.type)
            self.listbox.insert(
                "end", f"{item.effect_name} · {name} · {item.target} · {item.value}"
            )

    def add(self) -> None:
        dialog = EffectDialog(
            self,
            definitions=self.definitions_getter(),
            used_effect_ids=self.effect_ids_getter(),
        )
        self.wait_window(dialog)
        if dialog.result:
            self.effects_getter().append(dialog.result)
            self.changed()
            self.refresh()

    def edit(self) -> None:
        selection = self.listbox.curselection()
        effects = self.effects_getter()
        if not selection:
            return
        index = selection[0]
        dialog = EffectDialog(
            self,
            definitions=self.definitions_getter(),
            effect=effects[index],
            used_effect_ids=self.effect_ids_getter(),
        )
        self.wait_window(dialog)
        if dialog.result:
            effects[index] = dialog.result
            self.changed()
            self.refresh()

    def delete(self) -> None:
        selection = self.listbox.curselection()
        if selection:
            del self.effects_getter()[selection[0]]
            self.changed()
            self.refresh()

    def move(self, delta: int) -> None:
        selection = self.listbox.curselection()
        effects = self.effects_getter()
        if not selection:
            return
        source = selection[0]
        target = source + delta
        if target < 0 or target >= len(effects):
            return
        effects[source], effects[target] = effects[target], effects[source]
        self.changed()
        self.refresh()
        self.listbox.selection_set(target)
