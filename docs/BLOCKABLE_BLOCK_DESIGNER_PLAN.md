# Blockable Block Designer 구현 기획안

문서 버전: `1.1`
대상 프로그램: **Blockable Block Designer**
프로그램 형태: Python 데스크톱 제작 도구
출력 대상: React + Phaser 기반 Blockable 본 게임

---

## 1. 문서 목적

이 문서는 기존 Blockable 블록 디자인 파일과 Codex 작업 지침을 바탕으로
**블록 생성**과 **조합식 생성** 기능을 구현하기 위한 기준을 정의한다.

이 문서에서 가장 중요한 원칙은 다음과 같다.

> Designer는 콘텐츠 데이터를 만들고, 본 게임은 그 데이터를 해석하고 판정한다.

Designer는 블록과 조합식의 원본 데이터를 JSON으로 저장한다. 본 게임의 전투,
조합 탐색, 색상·등급 분석, 효과 실행 코드는 Designer에 구현하지 않는다.

---

## 2. 구현 범위

### 2.1 Designer가 제공하는 기능

1. 블록 생성·수정·복제·삭제
2. 블록 모양 좌표 편집
3. 블록의 등급과 색상 설정
4. 블록 자체의 `effects[]` 편집
5. 조합식 생성·수정·복제·삭제
6. 블록 인스턴스를 이용한 조합식 최종 모양 편집
7. 조합식별 회전·반전 허용 설정
8. 조합식의 기본 `effects[]` 편집
9. JSON 저장·불러오기
10. 저장 전 데이터 유효성 검사

### 2.2 Designer에서 제외하는 기능

- 실제 전투 실행
- 플레이어·몬스터 상태 계산
- 블록 드로우와 인벤토리 관리
- 거푸집 축소 규칙
- 완성된 조합식 자동 탐색
- 색상별·등급별 조합 효과 판정
- 효과의 실제 실행
- JSON 안의 임의 Python·JavaScript 코드 실행

---

## 3. Designer와 본 게임의 책임 분리

| 항목 | Designer | 본 게임 |
|---|---|---|
| 블록의 원본 모양 편집 | 담당 | 읽어서 렌더링 |
| 블록의 등급·색상 지정 | 담당 | 읽어서 분류·판정 |
| 블록 자체 효과 입력 | 담당 | 8장 공통 효과 규격으로 실행 |
| 조합식의 최종 모양 편집 | 담당 | 배치 결과와 비교 |
| 조합식별 회전·반전 허용 설정 | 담당 | 설정에 따라 좌표 변환·판정 |
| 조합식 기본 효과 입력 | 담당 | 조합 성공 시 실행 |
| 실제 참여 블록의 색상·등급 분석 | 제외 | 담당 |
| 같은 색·다른 색·특정 색 개수 판정 | 제외 | 담당 |
| 색상·등급에 따른 추가 효과 | 제외 | 담당 |
| 8장 공통 효과 실행 | 제외 | 담당 |

회전과 반전은 **설정과 실행의 책임을 분리**한다.

- Designer는 조합식마다 허용 여부를 JSON에 저장한다.
- 본 게임은 JSON을 읽고 회전·반전 좌표를 계산한다.
- 회전된 모든 좌표를 JSON에 중복 저장하지 않는다.

---

## 4. 핵심 데이터 모델

### 4.1 블록

```text
Block
├─ block_id
├─ block_name
├─ description
├─ block_type
│  ├─ type_id
│  ├─ type_name
│  ├─ grade
│  └─ color
├─ shape
│  └─ cells[]
├─ transform_rule
│  ├─ allow_rotation
│  └─ allow_reflection
└─ effects[]
```

### 4.2 조합식

```text
Combination
├─ combination_id
├─ combination_name
├─ description
├─ formula
│  └─ instances[]
│     ├─ instance_id
│     ├─ block_id
│     ├─ origin
│     ├─ rotation
│     └─ reflected
├─ transform_rule
│  ├─ allow_rotation
│  └─ allow_reflection
└─ effects[]
```

### 4.3 효과

피해, 방어도, 회복, 특수 효과와 효과별 추가 매개변수는 모두
**8장 공통 효과 규격**을 사용한다.

```text
Effect
├─ effect_id
├─ effect_name
├─ description
├─ target
├─ value
├─ type
└─ parameters
   ├─ id
   ├─ duration
   └─ intensify
```

`tag`는 현재 스키마에서 사용하지 않는다. 색상은 `block_type.color`, 등급은
`block_type.grade`, 효과 종류는 `effect.type`으로 표현한다.
이전 규격의 `reference_id`는 사용하지 않으며, 구체적인 적용 종류는
`parameters.id`로 표현한다.

---

## 5. JSON 구성 방침

### 5.1 최상위 구조

한 프로젝트의 블록과 조합식은 하나의 JSON 문서에 저장한다.

```json
{
  "schema_version": "1.1.0",
  "data_type": "blockable_block_design",
  "metadata": {
    "project_name": "Blockable",
    "designer_name": "Blockable Block Designer",
    "updated_at": "2026-07-29T00:00:00+09:00",
    "validation_status": "valid"
  },
  "blocks": [],
  "combinations": []
}
```

#### 최상위 필드 규칙

| 필드 | 형식 | 필수 | 규칙 |
|---|---|---:|---|
| `schema_version` | string | 예 | 의미가 바뀌는 스키마 변경을 추적한다. |
| `data_type` | string | 예 | 항상 `blockable_block_design`이다. |
| `metadata` | object | 예 | 파일 설명과 검증 결과를 저장한다. |
| `blocks` | array | 예 | 모든 블록 정의를 한 배열에 저장한다. |
| `combinations` | array | 예 | 모든 조합식을 최상위 배열에 저장한다. |

블록 내부에 조합식을 중첩하지 않는다. 조합식은 여러 블록을 참조하므로 특정
블록의 하위 데이터가 아니다.

### 5.2 메타데이터

```json
{
  "project_name": "Blockable",
  "designer_name": "Blockable Block Designer",
  "updated_at": "2026-07-29T00:00:00+09:00",
  "validation_status": "valid"
}
```

- `updated_at`은 ISO 8601 형식으로 저장한다.
- 정상 저장은 `validation_status: "valid"`로 기록한다.
- 오류가 있는 초안 저장을 지원한다면 `"invalid"`로 기록하고 본 게임용
  내보내기는 차단한다.
- 배열 순서는 Designer에서 사용자가 정한 순서를 보존한다.

---

## 6. 블록 JSON 규격

### 6.1 전체 예시

```json
{
  "block_id": "fire_blade_01",
  "block_name": "불꽃 칼날",
  "description": "화염 속성의 일반 등급 블록이다.",
  "block_type": {
    "type_id": "normal_fire",
    "type_name": "일반 화염",
    "grade": "normal",
    "color": "fire"
  },
  "shape": {
    "cells": [
      { "x": 0, "y": 0 },
      { "x": 1, "y": 0 }
    ]
  },
  "transform_rule": {
    "allow_rotation": true,
    "allow_reflection": false
  },
  "effects": [
    {
      "effect_id": "fire_blade_damage",
      "effect_name": "불꽃 칼날 피해",
      "description": "선택한 대상에게 기본 피해 5를 적용한다.",
      "target": "SELECTED",
      "value": 5,
      "type": "BASE_DAMAGE",
      "parameters": {
        "id": "NONE",
        "duration": 0,
        "intensify": 0
      }
    }
  ]
}
```

### 6.2 블록 기본 필드

| 필드 | 형식 | 필수 | 규칙 |
|---|---|---:|---|
| `block_id` | string | 예 | 전체 `blocks`에서 유일한 ID |
| `block_name` | string | 예 | UI 표시 이름 |
| `description` | string | 예 | 빈 문자열 허용 |
| `block_type` | object | 예 | 등급과 색상을 포함하는 복합 데이터 |
| `shape` | object | 예 | 블록 원본 모양 |
| `transform_rule` | object | 예 | 개별 블록의 배치 변환 허용 규칙 |
| `effects` | array | 예 | 효과가 없으면 빈 배열 |

### 6.3 ID 규칙

- `block_id`는 영문 소문자 `snake_case`를 권장한다.
- 숫자를 사용할 수 있지만 공백과 한글은 사용하지 않는다.
- ID는 표시 이름과 분리한다.
- 이미 다른 조합식에서 참조 중인 블록 ID를 변경하면 모든 `block_id` 참조를
  함께 변경한다.
- 삭제하려는 블록이 조합식에서 사용 중이면 삭제를 차단하고 사용처를 표시한다.

### 6.4 `block_type`

`block_type`은 단순 문자열이 아니라 다음 네 필드를 가진다.

```json
{
  "type_id": "legend_fire",
  "type_name": "전설 화염",
  "grade": "legend",
  "color": "fire"
}
```

#### `grade` 허용값

```text
normal
special
legend
curse
```

#### `color` 초기 허용값

```text
steel
nature
fire
water
none
```

- 일반 블록은 보통 `grade: "normal"`과 네 기본 색상 중 하나를 사용한다.
- 고유·전설·저주 등급도 필요하면 색상을 가질 수 있다.
- 색상이 없는 블록은 `color: "none"`으로 명시한다.
- 누락과 무색을 구분하기 위해 `color`를 생략하거나 `null`로 저장하지 않는다.
- `type_id`는 `grade`와 `color` 조합을 식별하는 안정적인 ID다.
- `type_name`은 UI 표시용이며 판정 키로 사용하지 않는다.

예:

```json
{
  "type_id": "curse_none",
  "type_name": "무색 저주",
  "grade": "curse",
  "color": "none"
}
```

### 6.5 블록 좌표

```json
{
  "shape": {
    "cells": [
      { "x": 0, "y": 0 },
      { "x": 0, "y": 1 },
      { "x": 1, "y": 1 }
    ]
  }
}
```

좌표 저장 규칙:

1. 모든 좌표는 정수다.
2. 같은 `(x, y)`를 중복 저장하지 않는다.
3. 블록은 최소 한 칸을 가져야 한다.
4. 저장 직전에 최소 `x`와 최소 `y`가 각각 `0`이 되도록 정규화한다.
5. 셀 배열은 `y` 오름차순, 같은 `y`에서는 `x` 오름차순으로 저장한다.
6. 회전된 좌표는 별도 저장하지 않는다.
7. 좌표 연결성 제한은 현재 정책에 맞춰 검증한다. 분리된 모양을 허용할 경우
   경고만 표시하고 좌표 자체는 보존한다.

### 6.6 블록 변환 규칙

```json
{
  "transform_rule": {
    "allow_rotation": true,
    "allow_reflection": false
  }
}
```

- 이 설정은 블록 한 개를 거푸집이나 조합식 편집 화면에 배치할 때 적용한다.
- `allow_rotation: true`이면 0°, 90°, 180°, 270° 배치를 허용한다.
- `allow_reflection: true`이면 반전된 블록 배치를 허용한다.
- 실제 회전·반전 좌표 계산은 Designer의 미리보기 기능과 본 게임이 각각
  동일한 규칙으로 수행한다.

---

## 7. 조합식 JSON 규격

### 7.1 전체 예시

```json
{
  "combination_id": "line_forge_03",
  "combination_name": "직선 단조",
  "description": "세 블록을 직선 형태로 완성하는 조합식이다.",
  "formula": {
    "instances": [
      {
        "instance_id": "piece_01",
        "block_id": "fire_blade_01",
        "origin": { "x": 0, "y": 0 },
        "rotation": 0,
        "reflected": false
      },
      {
        "instance_id": "piece_02",
        "block_id": "fire_blade_01",
        "origin": { "x": 2, "y": 0 },
        "rotation": 0,
        "reflected": false
      },
      {
        "instance_id": "piece_03",
        "block_id": "fire_blade_01",
        "origin": { "x": 4, "y": 0 },
        "rotation": 0,
        "reflected": false
      }
    ]
  },
  "transform_rule": {
    "allow_rotation": true,
    "allow_reflection": false
  },
  "effects": [
    {
      "effect_id": "line_forge_damage",
      "effect_name": "직선 단조 피해",
      "description": "조합 성공 시 기본 피해 10을 적용한다.",
      "target": "SELECTED",
      "value": 10,
      "type": "BASE_DAMAGE",
      "parameters": {
        "id": "NONE",
        "duration": 0,
        "intensify": 0
      }
    }
  ]
}
```

### 7.2 조합식 기본 필드

| 필드 | 형식 | 필수 | 규칙 |
|---|---|---:|---|
| `combination_id` | string | 예 | 전체 조합식에서 유일 |
| `combination_name` | string | 예 | UI 표시 이름 |
| `description` | string | 예 | 빈 문자열 허용 |
| `formula` | object | 예 | 최종 조합 모양을 이루는 블록 인스턴스 |
| `transform_rule` | object | 예 | 완성 조합식 전체의 변환 허용 규칙 |
| `effects` | array | 예 | 색상과 무관한 기본 효과만 저장 |

### 7.3 조합 인스턴스

조합식은 완성된 모양을 다시 편집할 수 있도록 블록 인스턴스 단위로 저장한다.

| 필드 | 형식 | 필수 | 규칙 |
|---|---|---:|---|
| `instance_id` | string | 예 | 해당 조합식 안에서만 유일 |
| `block_id` | string | 예 | `blocks[].block_id` 참조 |
| `origin.x` | integer | 예 | 변환된 블록의 배치 기준점 |
| `origin.y` | integer | 예 | 변환된 블록의 배치 기준점 |
| `rotation` | integer | 예 | `0`, `90`, `180`, `270`만 허용 |
| `reflected` | boolean | 예 | 해당 인스턴스의 반전 여부 |

같은 블록 정의를 한 조합식에 여러 번 배치할 수 있다. 각 배치는 별도의
`instance_id`를 가진다.

저장 전에는 모든 인스턴스가 차지하는 셀을 계산해 조합 전체의 최소 좌표가
`(0, 0)`이 되도록 모든 `origin`을 함께 이동한다. 인스턴스 사이의 빈 공간은
조합 모양의 일부이므로 제거하지 않는다.

`occupied_cells` 같은 파생 결과는 JSON에 저장하지 않는다. 본 게임은 참조 블록의
`shape.cells`, 인스턴스 변환, `origin`을 이용해 계산한다.

### 7.4 조합식 전체 변환 규칙

```json
{
  "transform_rule": {
    "allow_rotation": true,
    "allow_reflection": false
  }
}
```

이 설정은 블록 인스턴스의 회전 설정과 의미가 다르다.

- 인스턴스의 `rotation`과 `reflected`는 Designer에서 만든 원본 조합 모양을
  재현한다.
- 조합식의 `allow_rotation`은 원본 조합 모양 전체를 회전한 형태도 본 게임에서
  인정할지를 결정한다.
- 조합식의 `allow_reflection`은 원본 조합 모양 전체를 반전한 형태도 인정할지를
  결정한다.
- 허용 여부만 저장하며 4방향 조합식을 각각 별도 JSON 항목으로 만들지 않는다.

### 7.5 조합식에 저장하지 않는 조건

다음 항목은 조합식 JSON에 넣지 않는다.

- 특정 색상일 때의 추가 효과
- 모든 참여 블록이 같은 색인지
- 모든 참여 블록의 색이 다른지
- 특정 색상이 포함됐는지
- 특정 색상의 개수
- 참여 블록의 등급 조합
- 색상별로 복제한 조합식
- `conditional_effects`
- `color_synergies`
- 태그 기반 조건

이 정보는 실제 플레이 시 참여한 블록을 보고 본 게임의 공통 판정 시스템이
계산한다.

예를 들어 Designer에는 `line_forge_03` 하나만 저장한다. 본 게임은 같은 조합식에
실제로 참여한 블록을 분석해 화염, 물, 자연, 강철, 단색, 다색 등의 추가 결과를
판정한다.

---

## 8. 공통 효과 JSON 방침

### 8.1 기본 구조

```json
{
  "effect_id": "line_forge_damage",
  "effect_name": "직선 단조 피해",
  "description": "선택한 대상에게 기본 피해 10을 적용한다.",
  "target": "SELECTED",
  "value": 10,
  "type": "BASE_DAMAGE",
  "parameters": {
    "id": "NONE",
    "duration": 0,
    "intensify": 0
  }
}
```

기본 필드는 다음과 같다.

| 필드 | 형식 | 필수 | 의미 |
|---|---|---:|---|
| `effect_id` | string | 예 | 효과 인스턴스의 고유 ID |
| `effect_name` | string | 예 | 표시 이름 |
| `description` | string | 예 | 사람이 읽는 설명 |
| `target` | enum/string | 예 | 8.1에서 정한 적용 대상 |
| `value` | integer | 예 | 실제 계산에 사용하는 피해·회복·증감·횟수 |
| `type` | enum | 예 | 실제 실행 방식 |
| `parameters` | object | 예 | `id`, `duration`, `intensify`를 가진 공통 매개변수 |

모든 효과는 같은 형태의 `parameters` 객체를 저장한다. 해당 `type`에서 사용하지
않는 값은 각각 `NONE`, `0`, `0`으로 저장한다. 빈 객체나 필드 생략을 허용하지
않아 Designer 입력 양식과 본 게임 파서가 항상 같은 구조를 받도록 한다.

#### `target`

```text
SELECTED
self
L1, L2, L3 ...
R1, R2, R3 ...
B1, B2, B3 ...
all
```

| 값 | 적용 범위 |
|---|---|
| `SELECTED` | 사용자가 선택한 기준 대상 하나 |
| `self` | 효과 사용자 자신 |
| `Lx` | 기준 대상과 왼쪽 `x`개 |
| `Rx` | 기준 대상과 오른쪽 `x`개 |
| `Bx` | 기준 대상과 좌우 각각 `x`개 |
| `all` | 선택 가능한 대상 전체 |

`Lx`, `Rx`, `Bx`는 기준 대상도 효과 범위에 포함한다. Designer는 허용 형식을
검사해 저장하고, 실제 대상 목록 계산은 본 게임이 담당한다.

#### `value`

- 정수형이며 양수, `0`, 음수를 허용한다.
- 실제 피해량, 회복량, 능력치 증감량 또는 횟수를 뜻한다.
- 비율은 부동소수점 대신 정수 퍼센트로 저장한다. 예를 들어 `50`은 `+50%`다.

#### `parameters`

```text
parameters
├─ id          // 무엇을 적용하는가
├─ duration    // 얼마나 오래 적용하는가
└─ intensify   // 어느 강도·스택으로 적용하는가
```

| 필드 | 형식 | 의미 |
|---|---|---|
| `id` | enum/string | `type` 안에서 본 게임의 구체적인 처리 규칙을 선택하는 키 |
| `duration` | integer | `0`: 즉시, `1+`: 지속 턴, `-1`: 전투 종료까지, `-2`: 영구 |
| `intensify` | integer | `0`: 강도 미사용, `1+`: 추가할 스택 또는 효과 단계 |

`value`는 실제 계산 수치이고 `intensify`는 상태의 단계 또는 이번에 추가할
스택 수다. 예를 들어 `value: 10`, `intensify: 2`인 약화는 1스택당 10%의
감쇄를 제공하는 약화 2스택을 뜻한다.

### 8.2 권장 `type`

```text
BASE_DAMAGE
BASE_HIT_COUNT
INDEPENDENT_DAMAGE
BLOCK
RECOVERY
STATUS_DAMAGE
DEBUFF
CROWD_CONTROL
BUFF
EXTRA_TURN
DECK_CAPACITY
DRAW
PLACEMENT_COUNT
```

### 8.3 `type`별 매개변수

| `type` | `value` | `parameters.id` | `duration` | `intensify` |
|---|---|---|---:|---:|
| `BASE_DAMAGE` | 이번 기본 공격에 더할 기초 공격력 | `NONE` | `0` | `0` |
| `BASE_HIT_COUNT` | 1회당 연속 공격 데미지 | `CURRENT_ACTION` | `0` | 연속 공격 횟수(1+) |
| `INDEPENDENT_DAMAGE` | 별도로 실행할 독립 공격 기준값 | `NONE` | `0` | `0` |
| `BLOCK` | 획득할 소모형 방어도 | `NONE` | `0` | `0` |
| `RECOVERY` | 회복량 | `NONE` | `0` | `0` |
| `STATUS_DAMAGE` | 스택당 피해 계수 또는 상태별 계산값 | `BURN`, `BLEED`, `POISON` | 지속 턴 | 추가 스택·강도 |
| `DEBUFF` | 1스택당 감소량 또는 비율 | `ATTACK_REDUCTION`, `DAMAGE_TAKEN_INCREASE` | 지속 턴 | 추가 스택·강도 |
| `CROWD_CONTROL` | 별도 계산값이 있을 때 사용 | `STUN`, `FREEZE`, `ACTION_LOCK` | 지속 턴 | 추가 스택·강도 |
| `BUFF` | 1스택당 증가량 또는 비율 | `DAMAGE_BONUS`, `HIT_COUNT`, `ATTACK_MULTIPLIER` | 지속 턴 | 추가 스택·강도 |
| `EXTRA_TURN` | 추가 턴 수 | `PLAYER_TURN` | `0` | 필요 시 강도 |
| `DECK_CAPACITY` | 덱 용량 증감값 | `MAIN_DECK` | 적용 기간 | 필요 시 강도 |
| `DRAW` | 드로우 개수 | `MAIN_DECK` | `0` | 필요 시 강도 |
| `PLACEMENT_COUNT` | 배치 횟수 증감값 | `BLOCK_PLACEMENT` | 적용 기간 | 필요 시 강도 |

`BASE_HIT_COUNT`는 런타임 상태로 저장하지 않고 `value` 데미지의 공격을
`parameters.intensify` 횟수만큼 실행하는 현재 행동의 연속 공격으로 해석한다.
반대로 `BUFF + HIT_COUNT`는 자신 상태 갱신 목록 `S`에 등록된 뒤 이후 행동의
공격 횟수 계산에 참여한다. Designer와 본 게임은 두 효과를 서로 대체하거나
같은 의미로 취급하면 안 된다.

현재 전투에는 별도 방어력 능력치가 없고 소모형 방어도만 존재하므로
`BUFF/DEBUFF + DEFENSE`는 허용하지 않는다. 방어도 획득은 `BLOCK`으로 저장한다.

### 8.4 전투 계산 변수 연결

본 게임의 전투 계산 변수는 다음과 같다.

| 변수 | 의미 | 효과 데이터 연결 |
|---|---|---|
| `B` | 기초 공격력 | 이번 행동의 모든 `BASE_DAMAGE.value` 합 |
| `P` | 버프 데미지 추가 값 | 기존 `BUFF + DAMAGE_BONUS` 상태 |
| `H` | 연속 공격 횟수 | 각 `BASE_HIT_COUNT.parameters.intensify` 또는 기존 `BUFF + HIT_COUNT` |
| `A` | 독립 공격 기준값 | 각 `INDEPENDENT_DAMAGE.value` |
| `M` | 공격력 배율 | 기존 `BUFF + ATTACK_MULTIPLIER` 상태 |
| `D` | 공격력 감쇄 계수 | 공격자의 기존 `DEBUFF + ATTACK_REDUCTION` 상태 |
| `W` | 받는 피해 증가 계수 | 실제 피격 대상의 기존 `DEBUFF + DAMAGE_TAKEN_INCREASE` 상태 |
| `S` | 자신 상태 갱신 목록 | 이번 행동으로 부여하는 `BUFF` |
| `C` | 상대 상태 갱신 목록 | 이번 행동으로 부여하는 `DEBUFF`, `STATUS_DAMAGE`, `CROWD_CONTROL` |

`B`, `P`, `H`, `A`, `M`, `D`, `W`는 피해 계산기의 입력값이다. `S`와 `C`는
단일 숫자가 아니라 공격 처리 후 런타임 상태에 반영할 효과 객체의 목록이다.

```text
BASE_DAMAGE                     → B
BASE_HIT_COUNT                  → value 데미지 × intensify회 연속 공격
INDEPENDENT_DAMAGE              → A
BUFF + DAMAGE_BONUS             → S → 이후 P
BUFF + HIT_COUNT                → S → 이후 H
BUFF + ATTACK_MULTIPLIER        → S → 이후 M
DEBUFF + ATTACK_REDUCTION       → C → 이후 D
DEBUFF + DAMAGE_TAKEN_INCREASE  → C → 이후 W
STATUS_DAMAGE / CROWD_CONTROL   → C → 전용 처리기
```

기본 계산 규칙:

```text
B = Σ(BASE_DAMAGE.value)

P = Σ(DAMAGE_BONUS.value × 현재 스택)

BASE_HIT_COUNT 연속 공격 피해
  = value × parameters.intensify

기존 HIT_COUNT 버프가 적용된 기본 공격 횟수
  = baseHitCount + Σ(기존 HIT_COUNT.value × 현재 스택)

개별 공격력 배율 = 1 + (value × 현재 스택 / 100)
M = Π(개별 공격력 배율)

D = max(0, 1 - Σ(ATTACK_REDUCTION.value × 현재 스택 / 100))

W = 1 + Σ(DAMAGE_TAKEN_INCREASE.value × 현재 스택 / 100)
```

독립 공격이 여러 개이면 `A`를 하나로 합치지 않는다. 각
`INDEPENDENT_DAMAGE`를 `target`과 배열 순서를 유지한 별도 공격 항목으로
등록해 순서대로 실행한다. `W`는 공격자가 아니라 실제 피격 대상마다 다시
계산한다.

상태 피해는 `B~W` 공식에 직접 합산하지 않는다. `STATUS_DAMAGE`를 `C`에
등록해 대상 상태에 반영한 뒤, 본 게임이 턴 종료 시 `parameters.id`에 맞는
전용 규칙을 실행한다. 예를 들어 `BURN`과 `BLEED`의 서로 다른 계산법은
Designer가 아니라 본 게임의 효과 실행기가 선택한다.

### 8.5 효과 예시

#### 현재 행동의 기본 공격 횟수 증가

```json
{
  "effect_id": "double_strike_01",
  "effect_name": "3연속 공격",
  "description": "선택한 대상에게 데미지 5의 공격을 3회 적용한다.",
  "target": "SELECTED",
  "value": 5,
  "type": "BASE_HIT_COUNT",
  "parameters": {
    "id": "CURRENT_ACTION",
    "duration": 0,
    "intensify": 3
  }
}
```

#### 데미지 추가 버프

```json
{
  "effect_id": "rage_01",
  "effect_name": "분노",
  "description": "자신에게 3턴 동안 분노 2스택을 부여한다.",
  "target": "self",
  "value": 1,
  "type": "BUFF",
  "parameters": {
    "id": "DAMAGE_BONUS",
    "duration": 3,
    "intensify": 2
  }
}
```

이 효과는 이번 행동의 `S`에 등록된다. 적용된 이후에는 현재 스택마다
`value`만큼 `P`를 증가시킨다.

#### 공격력 감쇄 디버프

```json
{
  "effect_id": "weakness_01",
  "effect_name": "약화",
  "description": "대상에게 공격력 10% 감쇄 효과를 2스택 부여한다.",
  "target": "SELECTED",
  "value": 10,
  "type": "DEBUFF",
  "parameters": {
    "id": "ATTACK_REDUCTION",
    "duration": 2,
    "intensify": 2
  }
}
```

이 효과는 `C`에 등록되며, 대상의 이후 공격에서 `D` 계산에 참여한다.

#### 화상 상태 피해

```json
{
  "effect_id": "burn_04",
  "effect_name": "화상 부여",
  "description": "대상에게 화상 4스택을 부여한다.",
  "target": "R1",
  "value": 1,
  "type": "STATUS_DAMAGE",
  "parameters": {
    "id": "BURN",
    "duration": 0,
    "intensify": 4
  }
}
```

이 효과는 `C`에 등록되며, 본 게임은 `id: BURN`을 파싱해 화상 전용
스택·피해·감소 규칙을 실행한다.

### 8.6 본 게임 파싱 계약

본 게임은 효과 배열을 다음 순서로 해석한다.

```text
1. BASE_DAMAGE를 모아 B 계산
2. 공격자의 기존 BUFF에서 P, H, M 계산
3. BASE_HIT_COUNT마다 `value` 데미지의 공격을 `intensify`회 실행
4. 공격자의 기존 DEBUFF에서 D 계산
5. 기본 공격을 H회 실행하고 실제 대상마다 W 계산
6. INDEPENDENT_DAMAGE를 각각 별도 실행하고 실제 대상마다 W 계산
7. BUFF를 S에 등록
8. DEBUFF, STATUS_DAMAGE, CROWD_CONTROL을 C에 등록
9. S와 C를 대상 런타임 상태에 반영
10. EXTRA_TURN과 자원 관련 효과 처리
11. 턴 종료 시 STATUS_DAMAGE를 parameters.id별 규칙으로 실행
```

Designer는 이 계산을 실행하지 않지만, 위 순서를 표현할 수 있는 데이터를
손실 없이 저장해야 한다.

### 8.7 효과 저장 원칙

1. Designer는 8장이 허용한 `target`, `type`, `parameters`만 입력받는다.
2. `description`을 분석해서 효과를 실행하지 않는다.
3. `effect_name`을 실행 키로 사용하지 않는다.
4. `tag`는 저장하지 않는다.
5. `type`별 필수 필드는 저장 전에 검사한다.
6. 효과가 여러 개면 배열 순서대로 보존한다.
7. 모든 효과에 `parameters.id`, `duration`, `intensify`를 저장한다.
8. `reference_id`는 읽기 호환 외에는 사용하거나 새로 저장하지 않는다.
9. `parameters.id`는 표시 문자열이 아니라 본 게임 파서가 전용 처리기를
   선택하는 키이므로 허용 목록으로 관리한다.
10. Designer가 임의의 효과 실행 형식이나 새로운 의미를 추측해 만들지 않는다.

블록의 `effects[]`는 해당 블록 자체 효과이고, 조합식의 `effects[]`는 색상과
무관하게 조합 성공 시 항상 발생하는 기본 효과다.

---

## 9. 좌표 변환 공통 규칙

좌표 관련 코드는 UI와 분리한 순수 함수로 구현한다.

### 9.1 회전

90° 단위 회전은 다음 규칙을 사용한다.

```text
(x, y) → (-y, x)
```

회전 후에는 최소 좌표가 `(0, 0)`이 되도록 정규화한다.

### 9.2 반전

반전축은 구현 전체에서 하나로 통일한다. 기본 정책은 좌우 반전이다.

```text
(x, y) → (-x, y)
```

반전 후에도 좌표를 정규화한다.

### 9.3 인스턴스 점유 셀 계산 순서

1. 참조 블록의 `shape.cells`를 읽는다.
2. `reflected`가 참이면 반전한다.
3. `rotation` 값만큼 회전한다.
4. 변환된 블록 좌표를 정규화한다.
5. 인스턴스의 `origin`을 더한다.
6. 모든 인스턴스의 점유 셀을 합친다.
7. 조합 전체를 저장할 때 전체 좌표를 다시 정규화한다.

Designer와 본 게임은 이 순서를 동일하게 사용해야 한다.

---

## 10. 화면 구성

### 10.1 프로젝트 화면

- 새 프로젝트
- JSON 열기
- 저장
- 다른 이름으로 저장
- 유효성 검사
- 마지막 저장 시각과 변경 여부 표시
- 저장되지 않은 변경 내용 경고

### 10.2 블록 편집 화면

- 왼쪽: 블록 목록, 검색, 추가, 복제, 삭제
- 가운데: 블록 모양 격자
- 오른쪽: 기본 정보, `block_type`, 변환 규칙, 효과 목록

필수 동작:

1. 격자 셀 클릭으로 활성·비활성 전환
2. 등급과 색상 선택
3. 회전·반전 미리보기
4. 효과 추가·수정·삭제·순서 이동
5. 저장 전 좌표 정규화와 중복 검사

### 10.3 조합식 편집 화면

- 왼쪽: 생성된 블록 목록
- 가운데: 조합식 배치 격자
- 오른쪽: 조합식 정보, 전체 변환 규칙, 기본 효과 목록

필수 동작:

1. 블록을 선택해 인스턴스로 배치
2. 인스턴스 이동·삭제
3. 블록 자체가 허용하는 범위에서 인스턴스 회전·반전
4. 같은 블록 여러 번 배치
5. 겹치는 셀 실시간 표시
6. 조합식 전체 회전·반전 미리보기
7. 조합식의 기본 효과 편집

색상별 효과와 조건을 입력하는 UI는 만들지 않는다.

### 10.4 공통 효과 편집기

블록과 조합식은 같은 효과 편집기 컴포넌트를 사용한다.

필수 입력 항목:

1. `effect_id`
2. `effect_name`
3. `description`
4. `target`
5. `value`
6. `type`
7. `parameters.id`
8. `parameters.duration`
9. `parameters.intensify`

편집기 동작:

- `type`을 먼저 선택하면 해당 타입에서 허용하는 `parameters.id`만 표시한다.
- 사용하지 않는 매개변수도 숨겨서 누락하지 않고 정해진 기본값으로 고정한다.
- `BASE_HIT_COUNT`를 선택하면 `value`를 데미지,
  `intensify`를 1 이상의 연속 공격 횟수로 입력하게 하고,
  `id: CURRENT_ACTION`, `duration: 0`은 수정할 수 없게 한다.
- `BASE_DAMAGE`, `INDEPENDENT_DAMAGE`, `BLOCK`, `RECOVERY`는
  `id: NONE`, `duration: 0`, `intensify: 0`을 자동 설정한다.
- `BUFF`, `DEBUFF`, `STATUS_DAMAGE`, `CROWD_CONTROL`은 `id`, `duration`,
  `intensify`를 사용자가 명시적으로 입력하게 한다.
- `ATTACK_MULTIPLIER`, `ATTACK_REDUCTION`,
  `DAMAGE_TAKEN_INCREASE`의 `value` 입력란에는 정수 퍼센트 단위임을 표시한다.
- 효과 목록에서 배열 순서를 위·아래로 이동할 수 있어야 하며, 저장 시 그
  순서를 보존한다.
- UI 표시 설명은 저장된 필드로부터 미리보기를 만들 수 있지만,
  `description` 문장을 역으로 분석해 필드를 채우거나 실행 의미를 결정하지 않는다.

---

## 11. 유효성 검사

### 11.1 저장을 차단하는 오류

- 중복된 `block_id`
- 중복된 `combination_id`
- 한 조합식 안의 중복 `instance_id`
- 빈 `block_id`, `block_name`, `combination_id`, `combination_name`
- 허용되지 않은 `grade` 또는 `color`
- 빈 블록 모양
- 중복된 블록 셀 좌표
- 존재하지 않는 `block_id`를 참조하는 조합 인스턴스
- `rotation`이 0, 90, 180, 270 중 하나가 아님
- 회전 금지 블록 인스턴스에 0이 아닌 회전 사용
- 반전 금지 블록 인스턴스에 `reflected: true` 사용
- 서로 다른 조합 인스턴스의 점유 셀 겹침
- 8장 효과의 필수 필드 누락
- 8장에서 허용하지 않은 `target`, `type` 또는 `parameters.id`
- `parameters.id`, `duration`, `intensify` 누락
- `BASE_HIT_COUNT`의 `id`, `duration`이 `CURRENT_ACTION`, `0`과 다름
- `BASE_HIT_COUNT.intensify`가 1 미만
- 즉시 효과의 사용하지 않는 매개변수가 `NONE`, `0`, `0` 규칙과 다름
- 비율 효과의 `value`가 정수가 아님

### 11.2 경고

- 블록 설명 또는 조합식 설명이 비어 있음
- 블록에 효과가 없음
- 조합식에 기본 효과가 없음
- 어떤 조합식에서도 참조되지 않는 블록
- 서로 연결되지 않은 블록 셀
- 조합 인스턴스 사이에 빈 공간이 있음
- `color: "none"`인 블록

경고는 저장을 막지 않는다. 설계 의도일 수 있는 데이터를 경고 제거 목적으로
자동 변경하지 않는다.

---

## 12. 저장·불러오기 정책

1. UTF-8로 저장한다.
2. JSON 들여쓰기는 2칸을 사용한다.
3. 객체 키 이름은 이 문서의 스키마를 따른다.
4. 좌표와 배열 순서는 정해진 규칙으로 안정적으로 저장한다.
5. 파일 전체를 임시 파일에 먼저 쓴 뒤 교체하는 원자적 저장을 권장한다.
6. 저장 전에 전체 유효성 검사를 실행한다.
7. 알 수 없는 상위 버전의 JSON은 조용히 덮어쓰지 않는다.
8. 읽기→저장 왕복 과정에서 의미 있는 데이터가 사라지면 안 된다.
9. 스키마 구조나 필드 의미를 바꾸면 `schema_version`을 변경한다.
10. JSON과 화면 모델 사이의 변환은 UI 코드와 분리한다.

---

## 13. 기존 JSON 마이그레이션 방침

기존 디자인 파일에는 다음과 같은 이전 구조가 있을 수 있다.

```text
colors[]
block_types[]
blocks[].type_id
blocks[].color_id
blocks[].tags
combinations[].conditional_effects
color_synergies
match.kind = exact_block | any_block | type | color | tag
```

새 구조로 전환할 때의 원칙:

1. 기존 `type_id`와 `color_id`를 이용해 각 블록의 복합 `block_type`을 만든다.
2. 기존 분류가 일반 색상인지 등급인지 사람이 확인할 수 있도록 변환 결과를
   미리 표시한다.
3. `special`, `legend`, `curse`는 자동으로 색상이라고 단정하지 않는다.
4. 판단할 수 없는 색상은 사용자 확인 후 `none`으로 지정한다.
5. `tags`는 새 JSON에 저장하지 않되, 제거 전 변환 보고서에 사용처를 표시한다.
6. `conditional_effects`와 `color_synergies`는 Designer 조합식에서 제거 대상이지만
   본 게임의 공통 색상 판정 규칙으로 이전하기 전에는 데이터를 폐기하지 않는다.
7. 색상별로 복제된 동일 모양 조합식은 자동 병합하지 않는다. 모양과 효과가
   실제로 같은지 확인한 뒤 사용자가 병합을 승인해야 한다.
8. 기존 조합식의 인스턴스 좌표, 회전, 반전, 배열 순서는 보존한다.
9. 마이그레이션 원본은 덮어쓰지 않고 새 파일로 저장한다.
10. 기존 `reference_id`는 대응하는 `parameters.id`로 이동한다.
11. 기존 효과에 `parameters`가 없으면 `type`별 규칙에 따라
    `id`, `duration`, `intensify`를 생성한다.
12. 의미를 확정할 수 없는 이전 추가 필드는 자동 폐기하지 않고 변환 보고서에
    표시해 사용자가 확인하게 한다.

---

## 14. 권장 코드 구조

```text
src/blockable_block_designer/
├─ domain/
│  ├─ models.py
│  ├─ transforms.py
│  └─ validation.py
├─ persistence/
│  ├─ json_codec.py
│  └─ project_file.py
├─ services/
│  ├─ block_service.py
│  └─ combination_service.py
└─ ui/
   ├─ project_view.py
   ├─ block_editor.py
   ├─ combination_editor.py
   └─ effect_editor.py
```

구현 원칙:

- `domain`은 tkinter를 참조하지 않는다.
- 좌표 계산은 `transforms.py`의 순수 함수로 둔다.
- JSON 변환은 `json_codec.py` 한곳에서 관리한다.
- 유효성 검사는 UI 이벤트와 분리한다.
- 효과 편집기는 8장 스키마를 입력 양식으로 표현할 뿐 효과를 실행하지 않는다.
- `type`을 선택하면 허용되는 `parameters.id` 후보와 기본값을 결정한다.
- `BASE_HIT_COUNT`는 `CURRENT_ACTION`, `duration: 0`으로 고정하고,
  `intensify`에 1 이상의 연속 공격 횟수를 저장한다.

---

## 15. 테스트 기준

### 15.1 좌표 테스트

- 블록 좌표 정규화
- 90°, 180°, 270° 회전
- 좌우 반전
- 반전 후 회전
- 인스턴스 원점 적용
- 조합 전체 정규화
- 인스턴스 겹침 검출

### 15.2 JSON 테스트

- 최소 프로젝트 저장·불러오기
- 블록과 조합식 전체 왕복
- `block_type.grade`와 `block_type.color` 보존
- 빈 `effects[]` 보존
- 모든 효과의 `parameters.id`, `duration`, `intensify` 보존
- `BASE_HIT_COUNT` 왕복 보존
- `reference_id`를 새 JSON에 다시 저장하지 않음
- 배열 순서 보존
- 상위 스키마 버전 차단

### 15.3 검증 테스트

- 중복 ID
- 끊어진 블록 참조
- 잘못된 회전값
- 금지된 회전·반전 사용
- 겹치는 조합 인스턴스
- 잘못된 등급·색상
- 8장 효과 필수 필드 누락
- `type`별 허용되지 않은 `parameters.id`
- `BASE_HIT_COUNT`의 고정 ID·duration 또는 연속 공격 횟수 위반
- `value`, `duration`, `intensify` 형식 오류

---

## 16. 구현 순서

### 1단계: 데이터 계약 확정

- 이 문서의 블록·조합식 JSON 모델 확정
- 8장 공통 효과의 필드, `type`, `parameters.id` enum 연결
- `B·P·H·A·M·D·W·S·C`와 효과 타입 연결 확정
- 기존 JSON 마이그레이션 규칙 확정

### 2단계: 도메인과 저장 계층

- dataclass 모델
- 좌표 변환 순수 함수
- 검증기
- JSON codec
- 저장·불러오기 왕복 테스트

### 3단계: 블록 생성 기능

- 블록 목록
- 좌표 편집
- 등급·색상 편집
- 변환 규칙
- 8장 효과 편집

### 4단계: 조합식 생성 기능

- 블록 인스턴스 배치
- 이동·회전·반전·삭제
- 겹침 표시와 저장 차단
- 조합식 전체 변환 설정
- 기본 효과 편집

### 5단계: 기존 데이터 전환

- 이전 스키마 읽기
- 변환 미리보기
- 중복 조합식 검토
- 새 JSON으로 별도 저장

### 6단계: 본 게임 연동 준비

- JSON 로더 입력 계약 제공
- 블록 등록에 필요한 필드 확인
- 조합 좌표 판정 계약 제공
- 8장 실행기에 전달할 효과 구조와 파싱 순서 확인

본 게임의 로더, 조합 판정기, 효과 실행기 자체는 별도 작업으로 남긴다.

---

## 17. 최종 산출물

Block Designer 완성 시 다음 결과를 제공해야 한다.

1. 실행 가능한 Python Designer
2. 블록 생성 기능
3. 조합식 생성 기능
4. 유효성 검사기
5. 새 스키마의 JSON 출력
6. 기존 디자인 JSON 마이그레이션 기능 또는 변환 지침
7. 좌표·저장·검증 테스트

최종 데이터 책임은 다음과 같이 고정한다.

```text
블록
= 기본 정보 + 등급·색상 + 원본 좌표 + 블록 변환 설정 + 8장 효과

조합식
= 기본 정보 + 블록 인스턴스로 만든 최종 모양
  + 조합식 전체 회전·반전 설정 + 색상 무관 기본 8장 효과

본 게임
= 조합 탐색 + 회전·반전 계산 + 실제 참여 블록 분석
  + 색상·등급 추가 판정 + 8장 효과 실행
```
