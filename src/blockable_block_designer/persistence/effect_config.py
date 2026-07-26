from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from ..domain.models import EffectDefinition
from .json_codec import effect_definition_from_dict, effect_definition_to_dict

EFFECT_CONFIG_VERSION = "1.0.0"
EFFECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class EffectConfigError(Exception):
    pass


def _validate_definitions(definitions: list[EffectDefinition]) -> None:
    ids = [item.id for item in definitions]
    if any(not EFFECT_ID_PATTERN.fullmatch(item_id) for item_id in ids):
        raise ValueError("효과 ID는 영문 소문자 snake_case여야 합니다.")
    if len(ids) != len(set(ids)):
        raise ValueError("효과 ID가 중복되었습니다.")
    for definition in definitions:
        keys = [parameter.key for parameter in definition.parameters]
        if len(keys) != len(set(keys)):
            raise ValueError(f"'{definition.id}' 효과의 입력값 키가 중복되었습니다.")


def load_effect_config(path: str | Path) -> list[EffectDefinition]:
    target = Path(path)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("최상위 값은 객체여야 합니다.")
        if data.get("config_version") != EFFECT_CONFIG_VERSION:
            raise ValueError("지원하지 않는 config_version입니다.")
        raw_definitions = data.get("effect_definitions")
        if not isinstance(raw_definitions, list):
            raise ValueError("effect_definitions는 배열이어야 합니다.")
        if any(not isinstance(item, dict) for item in raw_definitions):
            raise ValueError("effect_definitions의 항목은 객체여야 합니다.")
        definitions = [effect_definition_from_dict(item) for item in raw_definitions]
        _validate_definitions(definitions)
        return definitions
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise EffectConfigError(f"효과 설정 파일을 읽을 수 없습니다: {error}") from error


def save_effect_config(
    definitions: list[EffectDefinition], path: str | Path
) -> None:
    target = Path(path)
    temporary_name: str | None = None
    try:
        _validate_definitions(definitions)
        data = {
            "config_version": EFFECT_CONFIG_VERSION,
            "effect_definitions": [
                effect_definition_to_dict(item) for item in definitions
            ],
        }
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
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
        temporary_name = None
    except (OSError, TypeError, ValueError) as error:
        raise EffectConfigError(f"효과 설정 파일을 저장할 수 없습니다: {error}") from error
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink()
            except OSError:
                pass
