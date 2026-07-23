from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from ..domain.models import Effect, EffectDefinition


class EffectDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        definitions: list[EffectDefinition],
        effect: Effect | None = None,
    ) -> None:
        super().__init__(master)
        self.title("효과 편집")
        self.resizable(False, False)
        self.result: Effect | None = None
        self.definitions = definitions
        self.effect_labels = {
            f"{item.display_name} ({item.id})": item.id for item in definitions
        }
        selected_label = next(
            (
                label
                for label, effect_id in self.effect_labels.items()
                if effect and effect_id == effect.effect_id
            ),
            "",
        )
        self.effect_id = tk.StringVar(value=selected_label)
        self.order = tk.StringVar(value=str(effect.order if effect else 0))
        self.description = tk.StringVar(value=effect.description if effect else "")

        body = ttk.Frame(self, padding=12)
        body.grid(sticky="nsew")
        ttk.Label(body, text="효과").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            body,
            textvariable=self.effect_id,
            values=list(self.effect_labels),
            state="readonly",
            width=34,
        ).grid(row=0, column=1, sticky="ew")
        ttk.Label(body, text="순서").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(body, textvariable=self.order).grid(row=1, column=1, sticky="ew")
        ttk.Label(body, text="Parameters (JSON 객체)").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 2)
        )
        self.parameters = tk.Text(body, width=48, height=9)
        self.parameters.grid(row=3, column=0, columnspan=2)
        self.parameters.insert("1.0", json.dumps(effect.parameters if effect else {}, ensure_ascii=False, indent=2))
        ttk.Label(body, text="설명").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(body, textvariable=self.description).grid(row=4, column=1, sticky="ew")
        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="확인", command=self._accept).pack(side="right", padx=6)
        self.transient(master)
        self.grab_set()

    def _accept(self) -> None:
        try:
            parameters = json.loads(self.parameters.get("1.0", "end").strip() or "{}")
            if not isinstance(parameters, dict):
                raise ValueError("parameters는 JSON 객체여야 합니다.")
            order = int(self.order.get())
            effect_id = self.effect_labels.get(self.effect_id.get())
            if not effect_id:
                raise ValueError("효과를 선택하세요.")
        except (json.JSONDecodeError, ValueError) as error:
            messagebox.showerror("입력 오류", str(error), parent=self)
            return
        self.result = Effect(
            effect_id, order, parameters, self.description.get().strip()
        )
        self.destroy()


class EffectList(ttk.LabelFrame):
    def __init__(
        self,
        master: tk.Misc,
        effects_getter,
        definitions_getter,
        changed,
    ) -> None:
        super().__init__(master, text="효과", padding=6)
        self.effects_getter = effects_getter
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
        effects = self.effects_getter()
        for item in sorted(effects, key=lambda effect: effect.order):
            definition = next(
                (
                    definition
                    for definition in self.definitions_getter()
                    if definition.id == item.effect_id
                ),
                None,
            )
            name = definition.display_name if definition else item.effect_id
            self.listbox.insert("end", f"{item.order}: {name} ({item.effect_id})")

    def add(self) -> None:
        effects = self.effects_getter()
        dialog = EffectDialog(self, self.definitions_getter())
        self.wait_window(dialog)
        if dialog.result:
            effects.append(dialog.result)
            self.changed()
            self.refresh()

    def edit(self) -> None:
        selection = self.listbox.curselection()
        effects = self.effects_getter()
        if not selection or not effects:
            return
        ordered = sorted(enumerate(effects), key=lambda pair: pair[1].order)
        original_index, effect = ordered[selection[0]]
        dialog = EffectDialog(self, self.definitions_getter(), effect)
        self.wait_window(dialog)
        if dialog.result:
            effects[original_index] = dialog.result
            self.changed()
            self.refresh()

    def delete(self) -> None:
        selection = self.listbox.curselection()
        effects = self.effects_getter()
        if selection and effects:
            ordered = sorted(enumerate(effects), key=lambda pair: pair[1].order)
            del effects[ordered[selection[0]][0]]
            self.changed()
            self.refresh()
