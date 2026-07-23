# Blockable 규칙 JSON 1.1 추가 계약

이 문서는 `schema_version: "1.1.0"`에서 추가된 조건 슬롯과 시너지 필드를
설명합니다. 기존 필드는 `BLOCKABLE_RULE_EDITOR_PLAN.md`를 따릅니다.

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
| `all_same_color` | `{}` |
| `all_different_colors` | `{}` |
| `contains_color` | `{"color_id": "red"}` |
| `color_count` | `{"color_id": "red", "count": 2}` |
| `color_set` | `{"color_ids": ["red", "blue"]}` |
| `same_type` | `{}` |
| `block_count` | `{"count": 2}` |
| `tag_match` | `{"tag": "weapon"}` |

`color_set`은 참여 블록의 색상 구성과 비교합니다. 중복 색상 개수까지 구분해야
한다면 게임 구현에서 배열을 정렬한 뒤 다중 집합으로 비교하는 것을 권장합니다.

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

이 메타데이터는 편집 화면에만 영향을 주며 실제 효과 JSON은 기존처럼
`effect_id + parameters` 형태로 저장됩니다.
