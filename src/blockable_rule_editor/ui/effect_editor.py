from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..domain.models import Effect, EffectDefinition, EffectParameterDefinition


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
        self.initial_effect_id = effect.effect_id if effect else None
        self.initial_parameters = dict(effect.parameters) if effect else {}
        self.parameter_inputs: dict[
            str, tuple[EffectParameterDefinition, tk.Variable, dict[str, str]]
        ] = {}

        body = ttk.Frame(self, padding=12)
        body.grid(sticky="nsew")
        ttk.Label(body, text="효과").grid(row=0, column=0, sticky="w", pady=4)
        effect_combo = ttk.Combobox(
            body,
            textvariable=self.effect_id,
            values=list(self.effect_labels),
            state="readonly",
            width=34,
        )
        effect_combo.grid(row=0, column=1, sticky="ew")
        effect_combo.bind("<<ComboboxSelected>>", lambda _event: self._render_parameters())
        ttk.Label(body, text="효과 적용 순서").grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Entry(body, textvariable=self.order).grid(row=1, column=1, sticky="ew")
        ttk.Label(body, text="효과 값 설정").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 2)
        )
        self.parameter_frame = ttk.LabelFrame(body, text="선택한 효과의 입력값", padding=8)
        self.parameter_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Label(body, text="설명").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(body, textvariable=self.description).grid(row=4, column=1, sticky="ew")
        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="확인", command=self._accept).pack(side="right", padx=6)
        self._render_parameters()
        self.transient(master)
        self.grab_set()

    def _selected_definition(self) -> EffectDefinition | None:
        effect_id = self.effect_labels.get(self.effect_id.get())
        return next(
            (item for item in self.definitions if item.id == effect_id),
            None,
        )

    def _render_parameters(self) -> None:
        for child in self.parameter_frame.winfo_children():
            child.destroy()
        self.parameter_inputs.clear()
        definition = self._selected_definition()
        if not definition:
            ttk.Label(self.parameter_frame, text="먼저 효과를 선택하세요.").grid(
                row=0, column=0, sticky="w"
            )
            return
        values = (
            self.initial_parameters
            if definition.id == self.initial_effect_id
            else {}
        )
        specifications = list(definition.parameters)
        known_keys = {item.key for item in specifications}
        for key, value in values.items():
            if key not in known_keys:
                value_type = (
                    "boolean"
                    if isinstance(value, bool)
                    else "integer"
                    if isinstance(value, int)
                    else "number"
                    if isinstance(value, float)
                    else "string"
                )
                specifications.append(
                    EffectParameterDefinition(
                        key,
                        value_type,
                        False,
                        display_name=f"기존 값: {key}",
                    )
                )
        if not specifications:
            ttk.Label(
                self.parameter_frame,
                text="이 효과에는 별도의 입력값이 없습니다.",
            ).grid(row=0, column=0, sticky="w")
            return
        for row, specification in enumerate(specifications):
            required = " *" if specification.required else ""
            label = specification.display_name or specification.key
            ttk.Label(self.parameter_frame, text=f"{label}{required}").grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=3
            )
            current = values.get(specification.key, "")
            reverse_options: dict[str, str] = {}
            if specification.value_type == "boolean":
                variable: tk.Variable = tk.BooleanVar(
                    value=bool(current) if current != "" else False
                )
                widget = ttk.Checkbutton(self.parameter_frame, variable=variable)
            elif specification.value_type == "enum":
                labels = {
                    value: specification.option_labels.get(str(value), str(value))
                    for value in specification.options
                }
                reverse_options = {label: str(value) for value, label in labels.items()}
                selected = labels.get(current, "")
                variable = tk.StringVar(value=selected)
                widget = ttk.Combobox(
                    self.parameter_frame,
                    textvariable=variable,
                    values=list(reverse_options),
                    state="readonly",
                    width=28,
                )
            else:
                variable = tk.StringVar(value="" if current == "" else str(current))
                widget = ttk.Entry(
                    self.parameter_frame, textvariable=variable, width=31
                )
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            if specification.description:
                ttk.Label(
                    self.parameter_frame,
                    text=specification.description,
                    foreground="#64748B",
                ).grid(row=row, column=2, sticky="w", padx=(6, 0))
            self.parameter_inputs[specification.key] = (
                specification,
                variable,
                reverse_options,
            )
        self.parameter_frame.columnconfigure(1, weight=1)

    def _parameter_values(self) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, (specification, variable, reverse_options) in self.parameter_inputs.items():
            raw = variable.get()
            if specification.value_type == "boolean":
                if specification.required or raw:
                    result[key] = bool(raw)
                continue
            text = str(raw).strip()
            if not text:
                if specification.required:
                    raise ValueError(
                        f"'{specification.display_name or key}' 값을 입력하세요."
                    )
                continue
            if specification.value_type == "integer":
                result[key] = int(text)
            elif specification.value_type == "number":
                result[key] = float(text) if "." in text else int(text)
            elif specification.value_type == "enum":
                result[key] = reverse_options.get(text, text)
            else:
                result[key] = text
        return result

    def _accept(self) -> None:
        try:
            parameters = self._parameter_values()
            order = int(self.order.get())
            effect_id = self.effect_labels.get(self.effect_id.get())
            if not effect_id:
                raise ValueError("효과를 선택하세요.")
        except ValueError as error:
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
