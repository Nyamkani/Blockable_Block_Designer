# Blockable 규칙 JSON 1.1 및 1.2 추가 계약

이 문서는 `schema_version: "1.1.0"`에서 추가된 조건 슬롯과 시너지 필드를
설명합니다. 기존 필드는 `BLOCKABLE_BLOCK_DESIGNER_PLAN.md`를 따릅니다.

## 1.2 전투 효과 표준

`schema_version: "1.2.0"`은 최상위 `status_definitions`와 조건부 필수 효과
파라미터 메타데이터인 `required_when`을 추가합니다. 효과 ID, 상태 ID, 대상,
범위 및 마이그레이션 규칙은
`BLOCKABLE_COMBAT_EFFECT_STANDARD.md`를 단일 기준으로 사용합니다.

프로그램은 1.0/1.1 파일을 열 때 다음 대표 변환을 수행하고, 다음 저장 때
1.2.0으로 기록합니다.

- `apply_buff` → `apply_status`
- `buff_id` → `status_id`, `amount` → `stacks`
- `gain_defense` → `gain_block`, `gain_block.count` → `amount`
- `target: player` → `enemy`
- `target: all_enemies` → `target: enemy`, `range: all`
- 이전 상태 별칭(`bleed`, `weak`, `injury`, `injry`, `doubleAttack`) → 표준 상태 ID

표준 효과 정의는 프로그램에서 수정·삭제할 수 없습니다. 사용자 정의 효과와
사용자 정의 상태는 별도로 추가할 수 있습니다.

## 조건 슬롯

조합식의 각 `instances` 항목에는 `match`가 추가됩니다. `block_id`는 도면의
모양 템플릿이며, 게임은 실제 후보 블록의 변환된 모양이 이 템플릿과 같은지도
검사해야 합니다.

```json
{
  "instance_id": "piece_1",
  "block_id": "red_domino",
  "origin": {"x": 0, "y": 0},
  "rotation": 0,
  "mirrored": false,
  "match": {
    "kind": "type",
    "type_id": "normal"
  }
}
```

지원하는 `kind`:

| kind | 추가 필드 | 의미 |
|---|---|---|
| `exact_block` | 없음 | `block_id`와 같은 블록만 허용 |
| `any_block` | 없음 | 모양만 일치하면 색상과 블록 ID에 관계없이 허용 |
| `type` | `type_id` | 같은 모양이며 지정 Type인 블록 허용 |
| `color` | `color_id` | 같은 모양이며 지정 색상인 블록 허용 |
| `tag` | `tag` | 같은 모양이며 지정 태그가 있는 블록 허용 |

## 조합별 조건부 효과

`conditional_effects`는 조합식에만 적용되는 보너스입니다.

```json
{
  "condition": {
    "kind": "all_same_color",
    "parameters": {}
  },
  "effects": [
    {
      "effect_id": "deal_damage",
      "order": 1,
      "parameters": {"amount": 3}
    }
  ],
  "description": "참여 블록의 색상이 같으면 추가 피해"
}
```

## 공통 시너지

최상위 `color_synergies`는 완성된 모든 조합에 적용할 수 있습니다.

```json
{
  "id": "red_pair_bonus",
  "display_name": "붉은 쌍 보너스",
  "condition": {
    "kind": "color_count",
    "parameters": {
      "color_id": "red",
      "count": 2
    }
  },
  "effects": [
    {
      "effect_id": "deal_damage",
      "order": 10,
      "parameters": {"amount": 2}
    }
  ],
  "description": "",
  "enabled": true
}
```

## 조건 종류

| kind | parameters |
|---|---|
| `all_same_color` | `{}` 또는 `{"color_id": "red"}` |
| `all_different_colors` | `{}` |
| `contains_color` | `{"color_id": "red"}` |
| `color_count` | `{"color_id": "red", "count": 2}` |
| `color_set` | `{"color_ids": ["red", "blue"]}` |
| `same_type` | `{}` |
| `block_count` | `{"count": 2}` |
| `tag_match` | `{"tag": "weapon"}` |

`color_set`은 참여 블록의 색상 구성과 비교합니다. 중복 색상 개수까지 구분해야
한다면 게임 구현에서 배열을 정렬한 뒤 다중 집합으로 비교하는 것을 권장합니다.

`all_same_color`의 `color_id`는 선택 항목입니다. 값이 있으면 참여 블록이 모두
같으면서 그 색상 ID와도 일치해야 합니다. 값이 없으면 이전 버전과 같이 색상
종류와 무관하게 참여 블록의 색상이 모두 같은지만 검사합니다.

## 적용 순서

편집기는 적용 순서를 실행하지 않고 데이터만 저장합니다. 게임에서는 다음
순서를 권장합니다.

1. 블록 자체 효과
2. 조합식 기본 `effects`
3. 조합식 `conditional_effects`
4. 활성화된 최상위 `color_synergies`
5. 게임의 최종 수치 보정

동일한 효과의 합산·곱연산·상한 처리 방식은 본 게임 규칙에서 별도로 확정해야
합니다.

## 효과 입력 폼 메타데이터

`effect_definitions.parameters`에는 편집기에서 일반 입력칸을 만들기 위한 선택
필드가 포함될 수 있습니다.

```json
{
  "key": "buff_id",
  "value_type": "identifier",
  "required": true,
  "display_name": "버프 ID(영문 JSON 값)",
  "description": ""
}
```

- `display_name`: 사용자에게 보여줄 한글 입력 항목명
- `description`: 입력 도움말
- `option_labels`: enum의 영문 값에 대응하는 한글 표시 이름
- `identifier`: 영문 소문자 `snake_case` ID 입력
- `default`: 새 효과를 추가할 때 입력칸에 표시할 기본값
- `allow_negative`: 숫자 입력에서 음수를 정상 값으로 허용할지 여부

효과 정의 자체에는 편집자와 게임 개발자가 용도를 확인할 수 있도록 한글
`display_name`과 자유 형식 `description`을 함께 저장할 수 있습니다.

이 메타데이터는 편집 화면에만 영향을 주며 실제 효과 JSON은 기존처럼
`effect_id + parameters` 형태로 저장됩니다.

공격, 방어와 회복을 포함한 조합 최종 수치의 원본은 이 규칙 JSON입니다. 본
게임은 같은 수치를 별도로 하드코딩하지 않고 블록 효과, 조합 기본 효과, 조건부
효과와 공통 시너지를 순서대로 합산해야 합니다. 음수 값도 보정값으로 포함합니다.

## 공유 효과 설정 파일

효과 정의만 다른 프로젝트와 공유할 때 기본 파일명은
`blockable_effect_config.json`입니다. 이 파일은 프로젝트 규칙 JSON이 아니며
다음 구조를 사용합니다.
예제는 `examples/blockable_effect_config.example.json`에서 확인할 수 있습니다.

```json
{
  "config_version": "1.0.0",
  "effect_definitions": []
}
```

가져올 때 새로운 ID는 추가하고, 기존 ID와 충돌하면 사용자가 전체 덮어쓰기 또는
중복 건너뛰기를 선택합니다. 블록·조합식에 설정한 실제 효과 값은 이 파일에
포함하지 않습니다.

조합식 인스턴스 겹침은 편집기의 임시 상태로만 허용됩니다. 겹침이 있는 프로젝트는
`validation_status: invalid` 초안으로도 파일에 저장할 수 없습니다.
