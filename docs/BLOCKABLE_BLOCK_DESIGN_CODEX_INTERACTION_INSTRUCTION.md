# Blockable Block Design Codex 연동 지침

현재 프로그램 버전: `v1.3.1`
현재 JSON 스키마: `1.1.0`

## 0. 현재 기준 디자인 JSON

현재 Codex 연동의 기준 데이터는 다음 파일이다.

```text
examples/blockable_block_design.json
```

이 파일은 이전 Beta 출력물을 현행 계약으로 마이그레이션한 현재 기준
디자인이다. 문서에 적힌 수치보다 이 JSON의 실제 데이터가 우선한다.

현재 데이터 스냅샷:

- 블록: 28개
- 조합식: 45개
- 효과: 72개
- 효과 Type: `BASE_DAMAGE` 40개, `BASE_HIT_COUNT` 1개, `BLOCK` 18개,
  `DEBUFF` 2개, `DRAW` 5개, `RECOVERY` 5개, `STATUS_DAMAGE` 1개
- 효과 대상: `SELECTED` 43개, `all` 1개, `self` 28개
- Parameters ID: `NONE` 63개, `CURRENT_ACTION` 1개, `BLEEDING` 1개,
  `DAMAGE_TAKEN_INCREASE` 2개, `MAIN_DECK` 5개
- 검증 오류: 0개
- 검증 경고: 32개

경고는 분리된 블록 모양, 자체 효과 또는 기본 효과가 없는 항목, 조합식에서
사용되지 않는 블록에 관한 것이다. 이는 데이터를 삭제해야 한다는 의미가
아니며, 대상 게임 적용 시 의도된 설계인지 확인한다.

레거시 `conditional_effects` 3개와 `color_synergies` 4개는 새 조합식 런타임
필드로 변환하지 않았다. 원본 의미는 `metadata.migration_notes`에 기록되어
있으며, 본 게임 공통 판정 규칙으로 옮기기 전까지 원본 Beta JSON과 함께
검토한다.

## 1. 기준

Codex는 다음 순서로 읽는다.

1. 대상 프로젝트의 `AGENTS.md`
2. `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
3. `docs/BLOCKABLE_COMBAT_SYSTEM.md`, 특히 7.4
4. 사용자가 지정한 Block Designer JSON

JSON 데이터가 문서의 예시 개수나 ID와 다르면 JSON을 우선한다. Combat
System의 실행 의미를 Designer나 이 지침에서 임의로 바꾸지 않는다.

## 2. 파일 식별

```json
{
  "schema_version": "1.1.0",
  "data_type": "blockable_block_design"
}
```

최상위 런타임 필드는 `metadata`, `blocks`, `combinations`다. 이전 스키마의
`colors`, `block_types`, `effect_definitions`, `status_definitions`,
`conditional_effects`, `color_synergies`를 새 런타임 계약으로 간주하지 않는다.

Designer의 재사용 효과 설정은 디자인 JSON이 아니라 프로젝트 상대 경로의
`blockable_effect_config.json`에 별도로 저장되는 편집용 프리셋이다. 이 설정은
효과 ID·이름·설명 입력을 재사용하기 위한 것이며, 본 게임은 이 파일을 런타임
규칙으로 읽지 않는다. 실제 실행 의미는 디자인 JSON 효과의 7.4 `type`,
`target`, `value`, `parameters`를 따른다.

## 3. 블록

각 `blocks[]` 항목에서 다음을 읽는다.

- `block_id`, `block_name`, `description`
- `block_type.type_id`, `type_name`, `grade`, `color`
- `shape.cells`
- `transform_rule.allow_rotation`, `allow_reflection`
- `effects[]`

등급은 `normal`, `special`, `legend`, `curse`이고 색상은 `steel`, `nature`,
`fire`, `water`, `none`이다. `none`을 누락이나 `null`로 바꾸지 않는다.

## 4. 조합식

`combinations[].formula.instances[]`로 원본 완성 모양을 계산한다.

1. 참조 블록의 `shape.cells`를 읽는다.
2. `reflected`를 적용한다.
3. `rotation`을 적용한다.
4. 변환 좌표를 정규화한다.
5. `origin`을 더한다.

조합식의 `transform_rule`은 완성 모양 전체의 회전·반전 허용 여부다. 회전별
조합식을 복제하지 않는다. 색상·등급 추가 판정은 실제 참여 블록을 이용해 본
게임 공통 시스템에서 수행한다.

Designer의 조합판 아래 `예상 효과`는 배치 인스턴스가 참조하는 블록 효과와
조합식 자체 효과의 숫자 `value`를 Type과 Parameters ID별로 합산한 편집용 표시다. 이 화면
문구를 JSON 필드나 런타임 결과로 읽지 않는다. 색상·등급 시너지와 전투 상태에
따른 최종 결과는 포함하지 않으며, 본 게임이 JSON 원본으로 다시 계산한다.
공격 계열 Type은 저장된 `target`을 한글 범위로 함께 표시하며, 서로 다른
`target`의 값은 합치지 않는다.

## 5. 공통 효과

모든 효과는 같은 구조를 가진다.

```json
{
  "effect_id": "double_strike_01",
  "effect_name": "6연속 기본 공격",
  "description": "선택한 대상에게 B 5의 기본 공격을 6회 실행한다.",
  "target": "SELECTED",
  "value": 5,
  "type": "BASE_HIT_COUNT",
  "parameters": {
    "id": "CURRENT_ACTION",
    "duration": 0,
    "intensify": 6
  }
}
```

필수 규칙:

- `value`는 음수·0·양수를 허용하는 유한한 숫자다.
- 비율은 임시로 `10`과 `0.1`을 모두 10%로 해석한다.
- 횟수·용량 효과의 `value`는 정수다.
- 대상은 `SELECTED`, `self`, `Lx`, `Rx`, `Bx`, `all` 형식이다.
- 모든 효과에 `parameters.id`, `duration`, `intensify`가 존재해야 한다.
- `duration`: `0` 즉시, `1+` 지속 턴, `-1` 전투 종료까지, `-2` 영구
- `intensify`: `0` 미사용, `1+` 추가 스택 또는 강도
- `reference_id`는 새로 저장하지 않는다.
- 배열 순서는 실행 표현 순서이므로 보존한다.

허용 Type과 Parameters ID:

| Type | 허용 `parameters.id` |
|---|---|
| `BASE_DAMAGE` | `NONE` |
| `BASE_HIT_COUNT` | `CURRENT_ACTION` |
| `INDEPENDENT_DAMAGE` | `NONE` |
| `BLOCK` | `NONE` |
| `RECOVERY` | `NONE` |
| `STATUS_DAMAGE` | `BURN`, `BLEEDING`, `POISON` |
| `DEBUFF` | `ATTACK_REDUCTION`, `DAMAGE_TAKEN_INCREASE` |
| `CROWD_CONTROL` | `STUN`, `FREEZE`, `ACTION_LOCK` |
| `BUFF` | `DAMAGE_BONUS`, `RAGE`, `ATTACK_MULTIPLIER` |
| `EXTRA_TURN` | `CURRENT_ACTION`, `PLAYER_TURN` |
| `DECK_CAPACITY` | `MAIN_DECK` |
| `DRAW` | `MAIN_DECK` |
| `PLACEMENT_COUNT` | `CURRENT_ACTION`, `BLOCK_PLACEMENT` |

`BASE_DAMAGE`, `INDEPENDENT_DAMAGE`, `BLOCK`, `RECOVERY`는 `NONE/0/0`을
사용한다.
`BASE_HIT_COUNT`는 `value`를 기본 공격 1타의 B,
`parameters.intensify`를 이번 행동의 총 공격 횟수 H로 사용하며
`CURRENT_ACTION/duration: 0`으로 고정한다. `BUFF + HIT_COUNT`는 삭제된
구성이므로 만들지 않는다.

본 게임 연결 기준:

- 구현: `BURN`, `BLEEDING`, `ATTACK_REDUCTION`,
  `DAMAGE_TAKEN_INCREASE`, `STUN`, `BASE_HIT_COUNT + CURRENT_ACTION`,
  `DRAW + MAIN_DECK`
- 처리기 연결: `DAMAGE_BONUS`
- 임시 ID 구현: `EXTRA_TURN + CURRENT_ACTION`,
  `PLACEMENT_COUNT + CURRENT_ACTION`
- 파싱·값 보존만 지원: `DECK_CAPACITY + MAIN_DECK`
- 미구현 또는 최종 ID 미연결: `POISON`, `FREEZE`, `ACTION_LOCK`, `RAGE`,
  `ATTACK_MULTIPLIER`, `EXTRA_TURN + PLAYER_TURN`,
  `PLACEMENT_COUNT + BLOCK_PLACEMENT`

`STUN`은 `duration: 1/intensify: 1`을 사용한다.
`EXTRA_TURN + CURRENT_ACTION`, `DRAW + MAIN_DECK`,
`PLACEMENT_COUNT + CURRENT_ACTION`은 `duration: 0/intensify: 1`을 사용한다.
미구현·미연결 ID는 Designer에서 `(미구현 ID)`로 표시하지만 JSON에는 원래
ID만 저장한다. 알 수 없는 Type이나 Parameters ID는 조용히 무시하지 않고
오류로 보고한다.

## 6. 레거시 변환

- 1.0 공통 효과에 parameters가 없으면 Type별 기본값을 생성한다.
- `reference_id`가 있으면 대응 가능한 경우 `parameters.id`로 이동한다.
- 더 오래된 `effect_id + parameters` 구조는 의미가 확정되는 경우에만 새 Type과
  공통 parameters로 변환한다.
- 의미가 불명확한 효과와 이전 조건·시너지는 `metadata.migration_notes`로
  보고하고 추측해서 실행 의미를 만들지 않는다.
- 원본 파일을 덮어쓰지 않고 새 이름으로 저장한다.

## 7. 적용 전 검사

- `schema_version`과 `data_type`이 맞는가
- 블록·조합식·인스턴스·효과 ID가 유일한가
- 모든 조합 인스턴스가 존재하는 블록을 참조하는가
- 등급과 색상이 허용값인가
- 대상과 Type, Parameters ID가 허용값인가
- `value`가 유한한 숫자이고 횟수·용량 값만 정수인가
- `duration`, `intensify`가 정수인가
- 즉시 효과의 고정 매개변수가 맞는가
- `BASE_HIT_COUNT`가 `CURRENT_ACTION/duration: 0/intensify: 1+` 규칙을
  지키는가
- 효과별 고정 `duration`, `intensify`가 맞는가
- 효과 배열 순서를 보존하는가
