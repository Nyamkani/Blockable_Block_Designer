from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from ..domain.models import (
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    Project,
)
from ..domain.transforms import normalize_cells, normalize_instances
from ..domain.validation import ValidationIssue, validate_project
from .json_codec import project_from_dict, project_to_dict
from ..services.effect_migration import migrate_effect_standard


class ProjectFileError(Exception):
    pass


def load_project(path: str | Path, strict: bool = False) -> Project:
    target = Path(path)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        project = project_from_dict(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ProjectFileError(f"프로젝트를 읽을 수 없습니다: {error}") from error
    if project.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ProjectFileError(
            f"지원하지 않는 schema_version입니다: {project.schema_version!r} "
            f"(지원: {', '.join(sorted(SUPPORTED_SCHEMA_VERSIONS))})"
        )
    migrate_effect_standard(project)
    project.schema_version = SCHEMA_VERSION
    errors = [item for item in validate_project(project) if item.severity == "error"]
    if errors and strict:
        summary = "\n".join(f"- {item.location}: {item.message}" for item in errors[:10])
        raise ProjectFileError(f"프로젝트 검증에 실패했습니다.\n{summary}")
    # 1.0 projects map naturally to exact-block slots and no synergy rules.
    return project


def prepare_for_save(project: Project) -> None:
    project.schema_version = SCHEMA_VERSION
    migrate_effect_standard(project)
    blocks = {item.id: item for item in project.blocks}
    for block in project.blocks:
        block.cells = normalize_cells(block.cells)
    for combination in project.combinations:
        combination.instances = normalize_instances(combination.instances, blocks)
    project.metadata["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")


def save_project(
    project: Project,
    path: str | Path,
    allow_warnings: bool = False,
    allow_errors: bool = False,
) -> list[ValidationIssue]:
    prepare_for_save(project)
    issues = validate_project(project)
    errors = [item for item in issues if item.severity == "error"]
    warnings = [item for item in issues if item.severity == "warning"]
    if any(item.message == "블록 인스턴스가 겹칩니다." for item in errors):
        raise ProjectFileError("조합식의 블록 인스턴스가 겹쳐 저장할 수 없습니다.")
    if errors and not allow_errors:
        raise ProjectFileError("검증 오류가 있어 저장할 수 없습니다.")
    if warnings and not allow_warnings:
        raise ProjectFileError("검증 경고를 확인해야 저장할 수 있습니다.")
    project.metadata["validation_status"] = "invalid" if errors else "valid"
    project.metadata["validation_error_count"] = len(errors)
    project.metadata["validation_warning_count"] = len(warnings)

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        project_to_dict(project), ensure_ascii=False, indent=2, allow_nan=False
    ) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.replace(temporary_name, target)
    except (OSError, TypeError, ValueError) as error:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise ProjectFileError(f"프로젝트를 저장할 수 없습니다: {error}") from error
    return issues
