from __future__ import annotations

import re
import tkinter as tk
from tkinter import messagebox, ttk

from ..domain.models import EffectDefinition, EffectParameterDefinition


VALUE_TYPES = ("number", "integer", "string", "identifier", "boolean", "enum")
EFFECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def _parse_scalar(text: str, value_type: str):
    text = text.strip()
    if not text:
        return None
    if value_type == "integer":
        return int(text)
    if value_type == "number":
        return float(text) if "." in text else int(text)
    if value_type == "boolean":
        return text.lower() in {"true", "1", "예", "yes"}
    return text


class ParameterDefinitionDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, parameter: EffectParameterDefinition | None = None) -> None:
        super().__init__(master)
        self.title("효과 입력값 편집")
        self.result: EffectParameterDefinition | None = None
        parameter = parameter or EffectParameterDefinition("", "number")
        self.values = {
            "key": tk.StringVar(value=parameter.key),
            "display_name": tk.StringVar(value=parameter.display_name),
            "value_type": tk.StringVar(value=parameter.value_type),
            "default": tk.StringVar(
                value="" if parameter.default is None else str(parameter.default)
            ),
            "minimum": tk.StringVar(
                value="" if parameter.minimum is None else str(parameter.minimum)
            ),
            "maximum": tk.StringVar(
                value="" if parameter.maximum is None else str(parameter.maximum)
            ),
            "options": tk.StringVar(value=", ".join(str(item) for item in parameter.options)),
            "description": tk.StringVar(value=parameter.description),
        }
        self.required = tk.BooleanVar(value=parameter.required)
        self.allow_negative = tk.BooleanVar(value=parameter.allow_negative)
        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        fields = [
            ("영문 키", "key"), ("한글 이름", "display_name"), ("값 형식", "value_type"),
            ("기본값", "default"), ("최솟값", "minimum"), ("최댓값", "maximum"),
            ("선택값(쉼표)", "options"), ("간단한 설명", "description"),
        ]
        for row, (label, key) in enumerate(fields):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=3)
            if key == "value_type":
                widget = ttk.Combobox(
                    body, textvariable=self.values[key], values=VALUE_TYPES, state="readonly"
                )
            else:
                widget = ttk.Entry(body, textvariable=self.values[key], width=42)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
        checks = ttk.Frame(body)
        checks.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(checks, text="필수 입력", variable=self.required).pack(side="left")
        ttk.Checkbutton(checks, text="음수 허용", variable=self.allow_negative).pack(
            side="left", padx=10
        )
        buttons = ttk.Frame(body)
        buttons.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="확인", command=self._accept).pack(side="right", padx=5)
        body.columnconfigure(1, weight=1)
        self.transient(master)
        self.grab_set()

    def _accept(self) -> None:
        try:
            value_type = self.values["value_type"].get()
            key = self.values["key"].get().strip()
            if not key:
                raise ValueError("영문 키를 입력하세요.")
            minimum = _parse_scalar(self.values["minimum"].get(), "number")
            maximum = _parse_scalar(self.values["maximum"].get(), "number")
            default = _parse_scalar(self.values["default"].get(), value_type)
            options = [
                item.strip()
                for item in self.values["options"].get().split(",")
                if item.strip()
            ]
        except ValueError as error:
            messagebox.showerror("입력 오류", str(error), parent=self)
            return
        self.result = EffectParameterDefinition(
            key=key,
            value_type=value_type,
            required=self.required.get(),
            minimum=minimum,
            maximum=maximum,
            options=options,
            display_name=self.values["display_name"].get().strip(),
            description=self.values["description"].get().strip(),
            default=default,
            allow_negative=self.allow_negative.get(),
        )
        self.destroy()


class EffectDefinitionDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, definition: EffectDefinition | None = None) -> None:
        super().__init__(master)
        self.title("사용자 정의 효과 편집")
        self.geometry("680x500")
        self.result: EffectDefinition | None = None
        self.effect_id = tk.StringVar(value=definition.id if definition else "")
        self.display_name = tk.StringVar(value=definition.display_name if definition else "")
        self.description = tk.StringVar(value=definition.description if definition else "")
        self.parameters = [
            EffectParameterDefinition(**vars(item))
            for item in (definition.parameters if definition else [])
        ]
        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        for row, (label, variable) in enumerate([
            ("효과 ID(영문)", self.effect_id), ("효과명(한글)", self.display_name),
            ("간단한 설명", self.description),
        ]):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(body, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Label(body, text="효과 입력값").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.listbox = tk.Listbox(body, height=12)
        self.listbox.grid(row=4, column=0, columnspan=2, sticky="nsew")
        controls = ttk.Frame(body)
        controls.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Button(controls, text="입력값 추가", command=self._add).pack(side="left")
        ttk.Button(controls, text="수정", command=self._edit).pack(side="left", padx=4)
        ttk.Button(controls, text="삭제", command=self._delete).pack(side="left")
        footer = ttk.Frame(body)
        footer.grid(row=6, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(footer, text="취소", command=self.destroy).pack(side="right")
        ttk.Button(footer, text="확인", command=self._accept).pack(side="right", padx=5)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(4, weight=1)
        self._refresh()
        self.transient(master)
        self.grab_set()

    def _refresh(self) -> None:
        self.listbox.delete(0, "end")
        for item in self.parameters:
            flags = "필수" if item.required else "선택"
            if item.allow_negative:
                flags += ", 음수 허용"
            self.listbox.insert(
                "end",
                f"{item.display_name or item.key} ({item.key}: {item.value_type}, {flags})",
            )

    def _add(self) -> None:
        dialog = ParameterDefinitionDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.parameters.append(dialog.result)
            self._refresh()

    def _edit(self) -> None:
        selected = self.listbox.curselection()
        if not selected:
            return
        dialog = ParameterDefinitionDialog(self, self.parameters[selected[0]])
        self.wait_window(dialog)
        if dialog.result:
            self.parameters[selected[0]] = dialog.result
            self._refresh()

    def _delete(self) -> None:
        selected = self.listbox.curselection()
        if selected:
            del self.parameters[selected[0]]
            self._refresh()

    def _accept(self) -> None:
        effect_id = self.effect_id.get().strip()
        display_name = self.display_name.get().strip()
        if not effect_id or not display_name:
            messagebox.showerror("입력 오류", "효과 ID와 효과명을 입력하세요.", parent=self)
            return
        if not EFFECT_ID_PATTERN.fullmatch(effect_id):
            messagebox.showerror(
                "입력 오류",
                "효과 ID는 영문 소문자 snake_case로 입력하세요.",
                parent=self,
            )
            return
        keys = [item.key for item in self.parameters]
        if len(keys) != len(set(keys)):
            messagebox.showerror("입력 오류", "입력값 키가 중복되었습니다.", parent=self)
            return
        self.result = EffectDefinition(
            effect_id, display_name, self.parameters, self.description.get().strip()
        )
        self.destroy()
