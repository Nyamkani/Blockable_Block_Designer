from __future__ import annotations

import copy
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..domain.models import (
    Block,
    BlockInstance,
    BlockType,
    Cell,
    Color,
    ColorSynergy,
    Combination,
    ConditionalEffect,
    Project,
    SlotMatch,
)
from ..domain.transforms import instance_cells
from ..domain.validation import ValidationIssue, validate_project
from ..persistence.project_file import ProjectFileError, load_project, save_project
from ..services.block_service import toggle_cell
from ..services.combination_service import can_place
from .effect_editor import EffectList
from .grid_canvas import GridCanvas
from .rule_editor import (
    ConditionalEffectDialog,
    ConditionalEffectList,
    condition_summary,
)

SLOT_KIND_LABELS = {
    "정확한 블록": "exact_block",
    "모양만 일치(색상·ID 무시)": "any_block",
    "같은 Type": "type",
    "같은 색상": "color",
    "태그": "tag",
}


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Blockable 블록·조합 규칙 편집기")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.project = Project()
        self.path: Path | None = None
        self.dirty = False
        self.current_block: Block | None = None
        self.current_combination: Combination | None = None
        self.selected_instance: BlockInstance | None = None
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.refresh_all()

    def run(self) -> None:
        self.root.mainloop()

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="새 프로젝트", accelerator="Ctrl+N", command=self.new_project)
        file_menu.add_command(label="열기…", accelerator="Ctrl+O", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="저장", accelerator="Ctrl+S", command=self.save)
        file_menu.add_command(label="다른 이름으로 저장…", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self._close)
        menu.add_cascade(label="파일", menu=file_menu)
        menu.add_command(label="전체 검사", command=self.run_validation)
        self.root.configure(menu=menu)

    def _bind_shortcuts(self) -> None:
        self.root.bind_all("<Control-n>", lambda _event: self.new_project())
        self.root.bind_all("<Control-o>", lambda _event: self.open_project())
        self.root.bind_all("<Control-s>", lambda _event: self.save())

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.project_tab = ttk.Frame(self.notebook, padding=16)
        self.type_tab = ttk.Frame(self.notebook, padding=10)
        self.color_tab = ttk.Frame(self.notebook, padding=10)
        self.block_tab = ttk.Frame(self.notebook, padding=10)
        self.combo_tab = ttk.Frame(self.notebook, padding=10)
        self.synergy_tab = ttk.Frame(self.notebook, padding=10)
        self.validation_tab = ttk.Frame(self.notebook, padding=10)
        for tab, name in [
            (self.project_tab, "프로젝트"),
            (self.type_tab, "Type 관리"),
            (self.color_tab, "색상 관리"),
            (self.block_tab, "블록 편집기"),
            (self.combo_tab, "조합식 편집기"),
            (self.synergy_tab, "색상 시너지"),
            (self.validation_tab, "검사 결과"),
        ]:
            self.notebook.add(tab, text=name)
        self._build_project_tab()
        self._build_simple_tab(self.type_tab, "type")
        self._build_simple_tab(self.color_tab, "color")
        self._build_block_tab()
        self._build_combo_tab()
        self._build_synergy_tab()
        self._build_validation_tab()

    def _build_project_tab(self) -> None:
        ttk.Label(
            self.project_tab,
            text="Blockable 규칙 프로젝트",
            font=("TkDefaultFont", 18, "bold"),
        ).pack(anchor="w", pady=(0, 16))
        self.project_path_label = ttk.Label(self.project_tab)
        self.project_path_label.pack(anchor="w", pady=4)
        self.project_status_label = ttk.Label(self.project_tab)
        self.project_status_label.pack(anchor="w", pady=4)
        form = ttk.LabelFrame(self.project_tab, text="메타데이터", padding=12)
        form.pack(fill="x", pady=16)
        self.project_name_var = tk.StringVar()
        self.ruleset_name_var = tk.StringVar()
        for row, (label, variable) in enumerate(
            [("프로젝트 이름", self.project_name_var), ("규칙 세트 이름", self.ruleset_name_var)]
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            entry = ttk.Entry(form, textvariable=variable, width=50)
            entry.grid(row=row, column=1, sticky="ew")
            entry.bind("<KeyRelease>", lambda _event: self._metadata_changed())
        form.columnconfigure(1, weight=1)
        buttons = ttk.Frame(self.project_tab)
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="새 프로젝트", command=self.new_project).pack(side="left")
        ttk.Button(buttons, text="JSON 열기", command=self.open_project).pack(side="left", padx=6)
        ttk.Button(buttons, text="저장", command=self.save).pack(side="left")
        ttk.Button(buttons, text="전체 검사", command=self.run_validation).pack(side="left", padx=6)

    def _build_simple_tab(self, tab: ttk.Frame, kind: str) -> None:
        listbox = tk.Listbox(tab, width=42)
        listbox.pack(side="left", fill="both", expand=True)
        controls = ttk.Frame(tab, padding=(10, 0))
        controls.pack(side="left", fill="y")
        ttk.Button(
            controls,
            text="추가",
            command=self.add_type if kind == "type" else self.add_color,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text="수정",
            command=self.edit_type if kind == "type" else self.edit_color,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text="삭제",
            command=self.delete_type if kind == "type" else self.delete_color,
        ).pack(fill="x", pady=3)
        if kind == "type":
            self.type_list = listbox
        else:
            self.color_list = listbox

    def _build_block_tab(self) -> None:
        left = ttk.Frame(self.block_tab)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="블록 목록").pack(anchor="w")
        self.block_list = tk.Listbox(left, width=28)
        self.block_list.pack(fill="y", expand=True, pady=5)
        self.block_list.bind("<<ListboxSelect>>", self._select_block)
        row = ttk.Frame(left)
        row.pack(fill="x")
        ttk.Button(row, text="추가", command=self.add_block).pack(side="left")
        ttk.Button(row, text="복제", command=self.clone_block).pack(side="left", padx=3)
        ttk.Button(row, text="삭제", command=self.delete_block).pack(side="left")

        center = ttk.Frame(self.block_tab, padding=(12, 0))
        center.pack(side="left", fill="both", expand=True)
        ttk.Label(center, text="격자를 클릭해 모양을 편집하세요.").pack(anchor="w")
        self.block_canvas = GridCanvas(center, 10, 10, 42, self._toggle_block_cell)
        self.block_canvas.pack(pady=6)

        right = ttk.Frame(self.block_tab)
        right.pack(side="left", fill="y")
        self.block_vars = {key: tk.StringVar() for key in ("id", "name", "type", "color", "tags")}
        for label, key in [
            ("ID", "id"),
            ("이름", "name"),
            ("Type", "type"),
            ("색상", "color"),
            ("태그(쉼표)", "tags"),
        ]:
            ttk.Label(right, text=label).pack(anchor="w")
            if key in {"type", "color"}:
                widget = ttk.Combobox(right, textvariable=self.block_vars[key], state="readonly")
                if key == "type":
                    self.block_type_combo = widget
                else:
                    self.block_color_combo = widget
            else:
                widget = ttk.Entry(right, textvariable=self.block_vars[key])
            widget.pack(fill="x", pady=(0, 5))
            widget.bind("<<ComboboxSelected>>", lambda _event: self._apply_block_form())
            widget.bind("<KeyRelease>", lambda _event: self._apply_block_form())
        self.block_rotation_var = tk.BooleanVar(value=True)
        self.block_mirror_var = tk.BooleanVar()
        ttk.Checkbutton(
            right, text="회전 허용", variable=self.block_rotation_var, command=self._apply_block_form
        ).pack(anchor="w")
        ttk.Checkbutton(
            right, text="좌우 반전 허용", variable=self.block_mirror_var, command=self._apply_block_form
        ).pack(anchor="w")
        ttk.Label(right, text="설명").pack(anchor="w", pady=(6, 0))
        self.block_description = tk.Text(right, width=28, height=4)
        self.block_description.pack(fill="x")
        self.block_description.bind("<KeyRelease>", lambda _event: self._apply_block_form())
        self.block_effects = EffectList(
            right,
            lambda: self.current_block.effects if self.current_block else [],
            lambda: self.project.effect_definitions,
            self.mark_dirty,
        )
        self.block_effects.pack(fill="both", expand=True, pady=(8, 0))

    def _build_combo_tab(self) -> None:
        left = ttk.Frame(self.combo_tab)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="조합식").pack(anchor="w")
        self.combo_list = tk.Listbox(left, width=27, height=12)
        self.combo_list.pack(fill="x", pady=4)
        self.combo_list.bind("<<ListboxSelect>>", self._select_combo)
        row = ttk.Frame(left)
        row.pack(fill="x")
        ttk.Button(row, text="추가", command=self.add_combo).pack(side="left")
        ttk.Button(row, text="삭제", command=self.delete_combo).pack(side="left", padx=3)
        ttk.Separator(left).pack(fill="x", pady=10)
        ttk.Label(left, text="배치할 블록").pack(anchor="w")
        self.palette_list = tk.Listbox(left, width=27, height=12)
        self.palette_list.pack(fill="x", pady=4)
        ttk.Label(left, text="블록 선택 후 격자를 클릭해 배치").pack(anchor="w")

        center = ttk.Frame(self.combo_tab, padding=(12, 0))
        center.pack(side="left", fill="both", expand=True)
        self.combo_canvas = GridCanvas(center, 12, 12, 36, self._combo_grid_click)
        self.combo_canvas.pack()
        instance_buttons = ttk.Frame(center)
        instance_buttons.pack(pady=6)
        ttk.Button(instance_buttons, text="선택 회전", command=self.rotate_instance).pack(side="left")
        ttk.Button(instance_buttons, text="선택 반전", command=self.mirror_instance).pack(
            side="left", padx=5
        )
        ttk.Button(instance_buttons, text="선택 삭제", command=self.delete_instance).pack(
            side="left"
        )
        self.instance_label = ttk.Label(center, text="선택 인스턴스: 없음")
        self.instance_label.pack()
        slot_frame = ttk.LabelFrame(center, text="선택 슬롯의 허용 조건", padding=6)
        slot_frame.pack(fill="x", pady=(8, 0))
        self.slot_kind_var = tk.StringVar(value="정확한 블록")
        self.slot_kind_combo = ttk.Combobox(
            slot_frame,
            textvariable=self.slot_kind_var,
            values=list(SLOT_KIND_LABELS),
            state="readonly",
            width=16,
        )
        self.slot_kind_combo.pack(side="left")
        self.slot_kind_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._slot_kind_changed()
        )
        self.slot_value_var = tk.StringVar()
        self.slot_value_combo = ttk.Combobox(
            slot_frame, textvariable=self.slot_value_var, width=20
        )
        self.slot_value_combo.pack(side="left", padx=5)
        ttk.Button(slot_frame, text="조건 적용", command=self.apply_slot_match).pack(
            side="left"
        )
        ttk.Button(
            center,
            text="전체 슬롯을 모양만 일치(색상·블록 ID 무시)",
            command=self.apply_shape_only_to_all_slots,
        ).pack(pady=(5, 0))
        ttk.Label(
            center,
            text="배치 블록은 슬롯 모양의 기준이며, 조건에 맞는 같은 모양 블록을 허용합니다.",
            wraplength=460,
        ).pack(pady=(4, 0))

        right = ttk.Frame(self.combo_tab)
        right.pack(side="left", fill="y")
        self.combo_vars = {key: tk.StringVar() for key in ("id", "name", "tags")}
        for label, key in [("ID", "id"), ("이름", "name"), ("태그(쉼표)", "tags")]:
            ttk.Label(right, text=label).pack(anchor="w")
            entry = ttk.Entry(right, textvariable=self.combo_vars[key], width=28)
            entry.pack(fill="x", pady=(0, 5))
            entry.bind("<KeyRelease>", lambda _event: self._apply_combo_form())
        self.recipe_rotation_var = tk.BooleanVar(value=True)
        self.recipe_mirror_var = tk.BooleanVar()
        ttk.Checkbutton(
            right,
            text="조합 전체 회전 인정",
            variable=self.recipe_rotation_var,
            command=self._apply_combo_form,
        ).pack(anchor="w")
        ttk.Checkbutton(
            right,
            text="조합 전체 반전 인정",
            variable=self.recipe_mirror_var,
            command=self._apply_combo_form,
        ).pack(anchor="w")
        ttk.Label(right, text="설명").pack(anchor="w", pady=(6, 0))
        self.combo_description = tk.Text(right, width=28, height=4)
        self.combo_description.pack(fill="x")
        self.combo_description.bind("<KeyRelease>", lambda _event: self._apply_combo_form())
        self.combo_effects = EffectList(
            right,
            lambda: self.current_combination.effects if self.current_combination else [],
            lambda: self.project.effect_definitions,
            self.mark_dirty,
        )
        self.combo_effects.pack(fill="both", expand=True, pady=(8, 0))
        self.combo_conditional_effects = ConditionalEffectList(
            right,
            lambda: (
                self.current_combination.conditional_effects
                if self.current_combination
                else []
            ),
            lambda: self.project.effect_definitions,
            self.mark_dirty,
        )
        self.combo_conditional_effects.pack(fill="both", expand=True, pady=(8, 0))

    def _build_synergy_tab(self) -> None:
        left = ttk.Frame(self.synergy_tab)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(
            left,
            text="모든 조합식에 공통으로 적용할 색상·구성 시너지",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            left,
            text=(
                "조합이 완성된 뒤 실제 참여 블록의 색상·Type·개수를 검사하여 "
                "추가 효과를 적용합니다."
            ),
        ).pack(anchor="w", pady=(2, 8))
        self.synergy_tree = ttk.Treeview(
            left,
            columns=("enabled", "id", "name", "condition", "effects"),
            show="headings",
        )
        for key, title, width in [
            ("enabled", "사용", 55),
            ("id", "ID", 160),
            ("name", "이름", 170),
            ("condition", "조건", 380),
            ("effects", "효과 수", 70),
        ]:
            self.synergy_tree.heading(key, text=title)
            self.synergy_tree.column(key, width=width, anchor="w")
        self.synergy_tree.pack(fill="both", expand=True)
        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="추가", command=self.add_synergy).pack(side="left")
        ttk.Button(buttons, text="수정", command=self.edit_synergy).pack(
            side="left", padx=4
        )
        ttk.Button(buttons, text="사용/해제", command=self.toggle_synergy).pack(
            side="left"
        )
        ttk.Button(buttons, text="삭제", command=self.delete_synergy).pack(
            side="left", padx=4
        )
        self.synergy_tree.bind("<Double-1>", lambda _event: self.edit_synergy())

    def _build_validation_tab(self) -> None:
        ttk.Button(self.validation_tab, text="검사 실행", command=self.run_validation).pack(
            anchor="w", pady=(0, 6)
        )
        self.validation_tree = ttk.Treeview(
            self.validation_tab,
            columns=("severity", "location", "message"),
            show="headings",
        )
        for key, title, width in [
            ("severity", "등급", 70),
            ("location", "위치", 240),
            ("message", "내용", 650),
        ]:
            self.validation_tree.heading(key, text=title)
            self.validation_tree.column(key, width=width, anchor="w")
        self.validation_tree.pack(fill="both", expand=True)

    def _metadata_changed(self) -> None:
        self.project.metadata["project_name"] = self.project_name_var.get()
        self.project.metadata["ruleset_name"] = self.ruleset_name_var.get()
        self.mark_dirty()

    def mark_dirty(self) -> None:
        self.dirty = True
        self._update_title()

    def _update_title(self) -> None:
        name = self.path.name if self.path else "새 프로젝트"
        self.root.title(f"{'*' if self.dirty else ''}{name} — Blockable 규칙 편집기")
        self.project_path_label.configure(text=f"파일: {self.path or '(저장되지 않음)'}")
        self.project_status_label.configure(
            text="상태: 저장되지 않은 변경 사항 있음" if self.dirty else "상태: 저장됨"
        )

    def refresh_all(self) -> None:
        self.project_name_var.set(self.project.metadata.get("project_name", ""))
        self.ruleset_name_var.set(self.project.metadata.get("ruleset_name", ""))
        self.type_list.delete(0, "end")
        for item in self.project.block_types:
            self.type_list.insert("end", f"{item.id} — {item.display_name}")
        self.color_list.delete(0, "end")
        for item in self.project.colors:
            self.color_list.insert("end", f"{item.id} — {item.display_name} ({item.hex})")
        self.block_list.delete(0, "end")
        self.palette_list.delete(0, "end")
        for item in self.project.blocks:
            label = f"{item.id} — {item.display_name}"
            self.block_list.insert("end", label)
            self.palette_list.insert("end", label)
        self.combo_list.delete(0, "end")
        for item in self.project.combinations:
            self.combo_list.insert("end", f"{item.id} — {item.display_name}")
        self._refresh_synergies()
        self.block_type_combo.configure(values=[item.id for item in self.project.block_types])
        self.block_color_combo.configure(values=[item.id for item in self.project.colors])
        self._draw_block()
        self._draw_combo()
        self._update_title()

    def _confirm_discard(self) -> bool:
        return not self.dirty or messagebox.askyesno(
            "저장되지 않은 변경", "저장되지 않은 변경을 버리시겠습니까?"
        )

    def new_project(self) -> None:
        if not self._confirm_discard():
            return
        self.project = Project()
        self.path = None
        self.dirty = False
        self.current_block = None
        self.current_combination = None
        self.selected_instance = None
        self.refresh_all()

    def open_project(self) -> None:
        if not self._confirm_discard():
            return
        filename = filedialog.askopenfilename(
            title="Blockable 규칙 열기", filetypes=[("JSON", "*.json"), ("모든 파일", "*")]
        )
        if not filename:
            return
        try:
            project = load_project(filename)
        except ProjectFileError as error:
            messagebox.showerror("열기 실패", str(error))
            return
        self.project = project
        self.path = Path(filename)
        self.dirty = False
        self.current_block = None
        self.current_combination = None
        self.selected_instance = None
        self.refresh_all()
        issues = validate_project(self.project)
        errors = [item for item in issues if item.severity == "error"]
        if errors:
            self._show_issues(issues)
            messagebox.showwarning(
                "오류가 있는 초안",
                (
                    f"이 파일에는 오류가 {len(errors)}개 있지만 편집을 위해 열었습니다.\n"
                    "게임에서 사용하기 전에 검사 결과의 오류를 수정하세요."
                ),
            )

    def save(self) -> None:
        if not self.path:
            self.save_as()
            return
        issues = validate_project(self.project)
        errors = [item for item in issues if item.severity == "error"]
        warnings = [item for item in issues if item.severity == "warning"]
        if errors:
            if not messagebox.askyesno(
                "오류가 있는 초안 저장",
                (
                    f"오류 {len(errors)}개와 경고 {len(warnings)}개가 있습니다.\n\n"
                    "게임에서 정상 규칙으로 사용할 수 없지만 작업 중인 초안으로 "
                    "저장할 수 있습니다. 그래도 저장하시겠습니까?"
                ),
            ):
                self._show_issues(issues)
                return
        elif warnings and not messagebox.askyesno(
            "검증 경고", f"경고가 {len(warnings)}개 있습니다. 그래도 저장하시겠습니까?"
        ):
            self._show_issues(issues)
            return
        try:
            save_project(
                self.project,
                self.path,
                allow_warnings=True,
                allow_errors=bool(errors),
            )
        except ProjectFileError as error:
            messagebox.showerror("저장 실패", str(error))
            return
        self.dirty = False
        self.refresh_all()
        if errors:
            messagebox.showinfo(
                "초안 저장 완료",
                (
                    "오류가 포함된 초안을 저장했습니다.\n"
                    "metadata.validation_status는 'invalid'로 기록되었습니다."
                ),
            )

    def save_as(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Blockable 규칙 저장",
            defaultextension=".json",
            initialfile="blockable_rules.json",
            filetypes=[("JSON", "*.json")],
        )
        if filename:
            self.path = Path(filename)
            self.save()

    def _simple_item_dialog(self, title: str, values: list[tuple[str, str]]) -> list[str] | None:
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        variables = [tk.StringVar(value=value) for _label, value in values]
        result: list[str] | None = None
        frame = ttk.Frame(dialog, padding=12)
        frame.pack()
        for row, ((label, _value), variable) in enumerate(zip(values, variables, strict=True)):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(frame, textvariable=variable, width=42).grid(row=row, column=1, pady=4)

        def accept() -> None:
            nonlocal result
            result = [variable.get().strip() for variable in variables]
            dialog.destroy()

        ttk.Button(frame, text="취소", command=dialog.destroy).grid(
            row=len(values), column=0, pady=(10, 0)
        )
        ttk.Button(frame, text="확인", command=accept).grid(
            row=len(values), column=1, sticky="e", pady=(10, 0)
        )
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result

    def add_type(self) -> None:
        values = self._simple_item_dialog("Type 추가", [("ID", ""), ("이름", ""), ("설명", "")])
        if values:
            self.project.block_types.append(BlockType(*values))
            self.mark_dirty()
            self.refresh_all()

    def edit_type(self) -> None:
        selection = self.type_list.curselection()
        if not selection:
            return
        item = self.project.block_types[selection[0]]
        values = self._simple_item_dialog(
            "Type 수정", [("ID", item.id), ("이름", item.display_name), ("설명", item.description)]
        )
        if values:
            old_id = item.id
            item.id, item.display_name, item.description = values
            for block in self.project.blocks:
                if block.type_id == old_id:
                    block.type_id = item.id
            self.mark_dirty()
            self.refresh_all()

    def delete_type(self) -> None:
        selection = self.type_list.curselection()
        if not selection:
            return
        item = self.project.block_types[selection[0]]
        users = [block.id for block in self.project.blocks if block.type_id == item.id]
        if users:
            messagebox.showerror("삭제 불가", f"사용 중인 블록: {', '.join(users)}")
            return
        del self.project.block_types[selection[0]]
        self.mark_dirty()
        self.refresh_all()

    def add_color(self) -> None:
        values = self._simple_item_dialog("색상 추가", [("ID", ""), ("이름", ""), ("HEX", "#")])
        if values:
            self.project.colors.append(Color(*values))
            self.mark_dirty()
            self.refresh_all()

    def edit_color(self) -> None:
        selection = self.color_list.curselection()
        if not selection:
            return
        item = self.project.colors[selection[0]]
        values = self._simple_item_dialog(
            "색상 수정", [("ID", item.id), ("이름", item.display_name), ("HEX", item.hex)]
        )
        if values:
            old_id = item.id
            item.id, item.display_name, item.hex = values
            for block in self.project.blocks:
                if block.color_id == old_id:
                    block.color_id = item.id
            self.mark_dirty()
            self.refresh_all()

    def delete_color(self) -> None:
        selection = self.color_list.curselection()
        if not selection:
            return
        item = self.project.colors[selection[0]]
        users = [block.id for block in self.project.blocks if block.color_id == item.id]
        if users:
            messagebox.showerror("삭제 불가", f"사용 중인 블록: {', '.join(users)}")
            return
        del self.project.colors[selection[0]]
        self.mark_dirty()
        self.refresh_all()

    def add_block(self) -> None:
        block = Block(
            f"block_{len(self.project.blocks) + 1}",
            "새 블록",
            self.project.block_types[0].id if self.project.block_types else "",
            self.project.colors[0].id if self.project.colors else "",
            [Cell(0, 0)],
        )
        self.project.blocks.append(block)
        self.current_block = block
        self.mark_dirty()
        self.refresh_all()
        self.block_list.selection_set(len(self.project.blocks) - 1)
        self._load_block_form()

    def clone_block(self) -> None:
        if not self.current_block:
            return
        clone = copy.deepcopy(self.current_block)
        clone.id = f"{clone.id}_copy"
        clone.display_name += " 복사본"
        self.project.blocks.append(clone)
        self.current_block = clone
        self.mark_dirty()
        self.refresh_all()

    def delete_block(self) -> None:
        if not self.current_block:
            return
        users = [
            combo.id
            for combo in self.project.combinations
            if any(item.block_id == self.current_block.id for item in combo.instances)
        ]
        if users:
            messagebox.showerror("삭제 불가", f"사용 중인 조합식: {', '.join(users)}")
            return
        self.project.blocks.remove(self.current_block)
        self.current_block = None
        self.mark_dirty()
        self.refresh_all()

    def _select_block(self, _event=None) -> None:
        selection = self.block_list.curselection()
        if selection:
            self.current_block = self.project.blocks[selection[0]]
            self._load_block_form()

    def _load_block_form(self) -> None:
        block = self.current_block
        if not block:
            return
        for key, value in [
            ("id", block.id),
            ("name", block.display_name),
            ("type", block.type_id),
            ("color", block.color_id),
            ("tags", ", ".join(block.tags)),
        ]:
            self.block_vars[key].set(value)
        self.block_rotation_var.set(block.allow_rotation)
        self.block_mirror_var.set(block.allow_mirroring)
        self.block_description.delete("1.0", "end")
        self.block_description.insert("1.0", block.description)
        self.block_effects.refresh()
        self._draw_block()

    def _apply_block_form(self) -> None:
        block = self.current_block
        if not block:
            return
        block.id = self.block_vars["id"].get().strip()
        block.display_name = self.block_vars["name"].get().strip()
        block.type_id = self.block_vars["type"].get()
        block.color_id = self.block_vars["color"].get()
        block.tags = [item.strip() for item in self.block_vars["tags"].get().split(",") if item.strip()]
        block.allow_rotation = self.block_rotation_var.get()
        block.allow_mirroring = self.block_mirror_var.get()
        block.description = self.block_description.get("1.0", "end").strip()
        self.mark_dirty()

    def _toggle_block_cell(self, cell: Cell) -> None:
        if self.current_block:
            toggle_cell(self.current_block, cell)
            self.mark_dirty()
            self._draw_block()

    def _draw_block(self) -> None:
        self.block_canvas.draw_grid()
        if not self.current_block:
            return
        color = next(
            (item.hex for item in self.project.colors if item.id == self.current_block.color_id),
            "#64748B",
        )
        for cell in self.current_block.cells:
            self.block_canvas.fill_cell(cell, color)

    def add_combo(self) -> None:
        combo = Combination(f"combination_{len(self.project.combinations) + 1}", "새 조합식")
        self.project.combinations.append(combo)
        self.current_combination = combo
        self.selected_instance = None
        self.mark_dirty()
        self.refresh_all()
        self.combo_list.selection_set(len(self.project.combinations) - 1)
        self._load_combo_form()

    def delete_combo(self) -> None:
        if self.current_combination:
            self.project.combinations.remove(self.current_combination)
            self.current_combination = None
            self.selected_instance = None
            self.mark_dirty()
            self.refresh_all()

    def _select_combo(self, _event=None) -> None:
        selection = self.combo_list.curselection()
        if selection:
            self.current_combination = self.project.combinations[selection[0]]
            self.selected_instance = None
            self._load_combo_form()

    def _load_combo_form(self) -> None:
        combo = self.current_combination
        if not combo:
            return
        self.combo_vars["id"].set(combo.id)
        self.combo_vars["name"].set(combo.display_name)
        self.combo_vars["tags"].set(", ".join(combo.tags))
        self.recipe_rotation_var.set(combo.allow_recipe_rotation)
        self.recipe_mirror_var.set(combo.allow_recipe_mirroring)
        self.combo_description.delete("1.0", "end")
        self.combo_description.insert("1.0", combo.description)
        self.combo_effects.refresh()
        self.combo_conditional_effects.refresh()
        self._draw_combo()

    def _apply_combo_form(self) -> None:
        combo = self.current_combination
        if not combo:
            return
        combo.id = self.combo_vars["id"].get().strip()
        combo.display_name = self.combo_vars["name"].get().strip()
        combo.tags = [item.strip() for item in self.combo_vars["tags"].get().split(",") if item.strip()]
        combo.allow_recipe_rotation = self.recipe_rotation_var.get()
        combo.allow_recipe_mirroring = self.recipe_mirror_var.get()
        combo.description = self.combo_description.get("1.0", "end").strip()
        self.mark_dirty()

    def _combo_grid_click(self, cell: Cell) -> None:
        combo = self.current_combination
        if not combo:
            return
        blocks = {item.id: item for item in self.project.blocks}
        for instance in reversed(combo.instances):
            block = blocks.get(instance.block_id)
            if block and cell in instance_cells(instance, block):
                self.selected_instance = instance
                self._load_slot_match()
                self._draw_combo()
                return
        selection = self.palette_list.curselection()
        if not selection:
            return
        block = self.project.blocks[selection[0]]
        candidate = BlockInstance(
            f"piece_{len(combo.instances) + 1}", block.id, cell
        )
        if not can_place(combo, candidate, blocks):
            messagebox.showwarning("배치 불가", "다른 블록과 겹칩니다.")
            return
        combo.instances.append(candidate)
        self.selected_instance = candidate
        self._load_slot_match()
        self.mark_dirty()
        self._draw_combo()

    def _draw_combo(self) -> None:
        self.combo_canvas.draw_grid()
        combo = self.current_combination
        if not combo:
            self.instance_label.configure(text="선택 인스턴스: 없음")
            return
        blocks = {item.id: item for item in self.project.blocks}
        colors = {item.id: item.hex for item in self.project.colors}
        for instance in combo.instances:
            block = blocks.get(instance.block_id)
            if not block:
                continue
            outline = "#0F172A" if instance is self.selected_instance else "#64748B"
            for cell in instance_cells(instance, block):
                self.combo_canvas.fill_cell(
                    cell, colors.get(block.color_id, "#64748B"), outline, instance.instance_id
                )
        self.instance_label.configure(
            text=(
                f"선택 인스턴스: {self.selected_instance.instance_id} "
                f"({self.selected_instance.block_id}) · "
                f"{self._slot_summary(self.selected_instance.match)}"
                if self.selected_instance
                else "선택 인스턴스: 없음"
            )
        )

    def _slot_summary(self, match: SlotMatch) -> str:
        label = next(
            (label for label, kind in SLOT_KIND_LABELS.items() if kind == match.kind),
            match.kind,
        )
        value = match.type_id or match.color_id or match.tag
        return f"{label}: {value}" if value else label

    def _load_slot_match(self) -> None:
        if not self.selected_instance:
            return
        match = self.selected_instance.match
        label = next(
            (label for label, kind in SLOT_KIND_LABELS.items() if kind == match.kind),
            "정확한 블록",
        )
        self.slot_kind_var.set(label)
        self._slot_kind_changed()
        self.slot_value_var.set(match.type_id or match.color_id or match.tag or "")

    def _slot_kind_changed(self) -> None:
        kind = SLOT_KIND_LABELS.get(self.slot_kind_var.get(), "exact_block")
        if kind == "type":
            self.slot_value_combo.configure(
                values=[item.id for item in self.project.block_types],
                state="readonly",
            )
        elif kind == "color":
            self.slot_value_combo.configure(
                values=[item.id for item in self.project.colors],
                state="readonly",
            )
        elif kind == "tag":
            tags = sorted({tag for block in self.project.blocks for tag in block.tags})
            self.slot_value_combo.configure(values=tags, state="normal")
        else:
            self.slot_value_combo.configure(values=[], state="disabled")
            self.slot_value_var.set("")

    def apply_slot_match(self) -> None:
        instance = self.selected_instance
        if not instance:
            messagebox.showinfo("슬롯 조건", "먼저 격자에서 블록 인스턴스를 선택하세요.")
            return
        kind = SLOT_KIND_LABELS.get(self.slot_kind_var.get(), "exact_block")
        value = self.slot_value_var.get().strip()
        if kind in {"type", "color", "tag"} and not value:
            messagebox.showerror("입력 오류", "조건 값을 선택하거나 입력하세요.")
            return
        instance.match = SlotMatch(
            kind=kind,
            type_id=value if kind == "type" else None,
            color_id=value if kind == "color" else None,
            tag=value if kind == "tag" else None,
        )
        self.mark_dirty()
        self._draw_combo()

    def apply_shape_only_to_all_slots(self) -> None:
        combination = self.current_combination
        if not combination or not combination.instances:
            messagebox.showinfo("모양 조합", "블록을 하나 이상 배치한 조합식을 선택하세요.")
            return
        for instance in combination.instances:
            instance.match = SlotMatch(kind="any_block")
        if self.selected_instance:
            self._load_slot_match()
        self.mark_dirty()
        self._draw_combo()

    def _change_instance(self, rotation_delta: int = 0, mirror: bool = False) -> None:
        combo, instance = self.current_combination, self.selected_instance
        if not combo or not instance:
            return
        block = next((item for item in self.project.blocks if item.id == instance.block_id), None)
        if not block:
            return
        if rotation_delta and not block.allow_rotation:
            messagebox.showwarning("변환 불가", "이 블록은 회전을 허용하지 않습니다.")
            return
        if mirror and not block.allow_mirroring:
            messagebox.showwarning("변환 불가", "이 블록은 반전을 허용하지 않습니다.")
            return
        candidate = copy.deepcopy(instance)
        candidate.rotation = (candidate.rotation + rotation_delta) % 360
        candidate.mirrored = not candidate.mirrored if mirror else candidate.mirrored
        blocks = {item.id: item for item in self.project.blocks}
        if not can_place(combo, candidate, blocks, instance.instance_id):
            messagebox.showwarning("변환 불가", "변환하면 다른 블록과 겹칩니다.")
            return
        instance.rotation, instance.mirrored = candidate.rotation, candidate.mirrored
        self.mark_dirty()
        self._draw_combo()

    def rotate_instance(self) -> None:
        self._change_instance(rotation_delta=90)

    def mirror_instance(self) -> None:
        self._change_instance(mirror=True)

    def delete_instance(self) -> None:
        if self.current_combination and self.selected_instance:
            self.current_combination.instances.remove(self.selected_instance)
            self.selected_instance = None
            self.mark_dirty()
            self._draw_combo()

    def _refresh_synergies(self) -> None:
        if not hasattr(self, "synergy_tree"):
            return
        for row in self.synergy_tree.get_children():
            self.synergy_tree.delete(row)
        for index, synergy in enumerate(self.project.color_synergies):
            self.synergy_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    "예" if synergy.enabled else "아니오",
                    synergy.id,
                    synergy.display_name,
                    condition_summary(synergy.condition),
                    len(synergy.effects),
                ),
            )

    def _selected_synergy(self) -> tuple[int, ColorSynergy] | None:
        selection = self.synergy_tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        return index, self.project.color_synergies[index]

    def add_synergy(self) -> None:
        values = self._simple_item_dialog(
            "색상 시너지 추가",
            [
                ("ID", f"color_synergy_{len(self.project.color_synergies) + 1}"),
                ("이름", "새 색상 시너지"),
                ("설명", ""),
            ],
        )
        if not values:
            return
        dialog = ConditionalEffectDialog(self.root, self.project.effect_definitions)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        self.project.color_synergies.append(
            ColorSynergy(
                values[0],
                values[1],
                dialog.result.condition,
                dialog.result.effects,
                values[2] or dialog.result.description,
            )
        )
        self.mark_dirty()
        self._refresh_synergies()

    def edit_synergy(self) -> None:
        selected = self._selected_synergy()
        if not selected:
            return
        _index, synergy = selected
        values = self._simple_item_dialog(
            "색상 시너지 수정",
            [
                ("ID", synergy.id),
                ("이름", synergy.display_name),
                ("설명", synergy.description),
            ],
        )
        if not values:
            return
        rule = ConditionalEffect(
            synergy.condition, synergy.effects, synergy.description
        )
        dialog = ConditionalEffectDialog(
            self.root, self.project.effect_definitions, rule
        )
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        synergy.id, synergy.display_name, synergy.description = values
        synergy.condition = dialog.result.condition
        synergy.effects = dialog.result.effects
        if dialog.result.description:
            synergy.description = dialog.result.description
        self.mark_dirty()
        self._refresh_synergies()

    def toggle_synergy(self) -> None:
        selected = self._selected_synergy()
        if selected:
            selected[1].enabled = not selected[1].enabled
            self.mark_dirty()
            self._refresh_synergies()

    def delete_synergy(self) -> None:
        selected = self._selected_synergy()
        if selected and messagebox.askyesno(
            "색상 시너지 삭제", f"'{selected[1].display_name}'을 삭제하시겠습니까?"
        ):
            del self.project.color_synergies[selected[0]]
            self.mark_dirty()
            self._refresh_synergies()

    def run_validation(self) -> None:
        issues = validate_project(self.project)
        self._show_issues(issues)
        errors = sum(item.severity == "error" for item in issues)
        warnings = sum(item.severity == "warning" for item in issues)
        if not issues:
            messagebox.showinfo("검사 완료", "오류와 경고가 없습니다.")
        else:
            messagebox.showinfo("검사 완료", f"오류 {errors}개, 경고 {warnings}개")

    def _show_issues(self, issues: list[ValidationIssue]) -> None:
        for row in self.validation_tree.get_children():
            self.validation_tree.delete(row)
        for item in issues:
            self.validation_tree.insert(
                "", "end", values=(item.severity.upper(), item.location, item.message)
            )
        self.notebook.select(self.validation_tab)

    def _close(self) -> None:
        if self._confirm_discard():
            self.root.destroy()
