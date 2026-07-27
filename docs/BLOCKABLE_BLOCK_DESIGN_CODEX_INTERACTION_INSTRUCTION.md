# Blockable Block Designer — Codex 작업 지침

현재 프로그램 버전: `v1.2.2`

이 문서는 Codex가 Blockable Block Designer를 수정하거나 출력 JSON을 Blockable
게임에 연동할 때 사용하는 작업 명령서다.

Designer 저장소와 Blockable 게임 저장소는 서로 다른 프로젝트일 수 있다. 이
문서의 모든 경로는 각 프로젝트 루트를 기준으로 한 상대 경로로 해석한다.

## 1. Codex에 처음 전달할 명령문

아래 내용을 새 Codex 세션의 첫 요청으로 전달한다.

```text
이 프로젝트는 Blockable Block Designer입니다.

작업을 계획하거나 파일을 수정하기 전에 프로젝트 루트의 AGENTS.md를 먼저
읽으세요. AGENTS.md가 지정한 필수 문서를 모두 끝까지 읽고 그 지침을 따르세요.

현재 프로그램 버전은 v1.2.2입니다.
Python 패키지는 src/blockable_block_designer입니다.
현재 기준 디자인 파일은 examples/blockable_block_design.json입니다.
이 파일을 직접 읽고 실제 ID, 배열 순서와 수치를 적용하세요.

기존 JSON 스키마와 사용자 데이터를 임의로 깨뜨리지 마세요. UI 코드와 도메인,
검증, 저장 코드를 분리하고 좌표 로직은 순수 함수로 유지하세요. 변경 후 관련
테스트를 추가하거나 수정하고 전체 pytest를 실행하세요.

본 게임 저장소 수정, Git 커밋과 푸시는 별도 허가 없이는 수행하지 마세요.
```
ㄱ
## 2. 필수 확인 순서

Codex는 매 작업마다 다음 순서를 지킨다.

1. `AGENTS.md`를 읽는다.
2. `AGENTS.md`의 Required documentation 목록을 확인한다.
3. 지정된 문서를 모두 읽는다.
4. 현재 파일 구조와 `git status --short`를 확인한다.
5. 사용자 요청 범위를 정리하고 작업한다.
6. 테스트와 문서 검사를 실행한다.
7. 변경 파일, 동작 결과, 남은 제한사항을 보고한다.

### JSON 기반 지침서 재작성 및 전달 절차

사용자가 새로 작성한 디자인 JSON을 지정하면 기존 지침서의 수치와 ID를 그대로
재사용하지 않는다. 다음 순서로 이 문서를 새 JSON 기준으로 다시 작성한 뒤 다른
프로젝트에 적용한다.

1. 지정된 JSON 전체를 파싱하고 `schema_version`과
   `metadata.validation_status`를 확인한다.
2. 색상, Type, 효과 정의, 블록, 조합식, 시너지의 개수와 실제 ID를 다시 집계한다.
3. 모든 참조, 회전값, 겹침, 효과 parameter와 조건을 편집기 검증기로 검사한다.
4. 이 문서의 현재 기준 파일 경로, 스냅샷, 실제 사용 ID와 주의사항을 새 결과로
   교체한다. 이전 JSON에서만 유효한 수치나 ID는 남기지 않는다.
5. JSON 원본과 갱신된 이 지침서를 하나의 전달 세트로 준비한다.
6. 대상 프로젝트에서 그 프로젝트의 `AGENTS.md`와 필수 문서를 먼저 읽는다.
7. 대상 프로젝트 구조에 맞는 상대 경로를 결정하고 JSON 로더, 타입, 판정과 효과
   dispatch를 연결한다.
8. 게임 수치와 조합을 코드에 중복 하드코딩하지 않고 전달된 JSON을 단일 데이터
   원본으로 사용한다.
9. 적용 테스트와 원본 JSON 대비 누락·변형 검사를 실행한다.

우선순위는 다음과 같다.

1. 대상 프로젝트의 `AGENTS.md`: 대상 저장소의 작업·경로·검증 규칙
2. 전달된 디자인 JSON: 블록, 조합, 효과와 수치의 실제 원본
3. 이 지침서: JSON 해석과 통합 방법

지침서와 JSON의 수치가 다르면 JSON을 우선하고, 지침서를 즉시 다시 생성하거나
갱신한다. 불일치를 임의 추측으로 보정하지 않는다.

현재 필수 문서:

- `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
- `docs/RULE_SCHEMA_1_1.md`
- `docs/BLOCKABLE_COMBAT_EFFECT_STANDARD.md`
- `docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md`

기획안, 프로그램 동작, JSON 계약, 프로젝트 경로, 실행 명령 또는 Codex 작업
절차가 변경되면 이 문서도 같은 작업에서 함께 수정한다.

`docs/BLOCKABLE_COMBAT_EFFECT_STANDARD.md`는 본 게임 Blockable이 소유하는
읽기 전용 기준 문서다. 이 저장소에서는 수정하지 않는다. 표준과 의미가 명확히
같은 사용자 정의 효과는 표준 ID·파라미터로 통합하고 중복 정의를 제거한다.
추가 동작이 있거나 의미가 애매한 효과는 추측해서 통합하지 않는다.

## 3. 프로젝트 식별 정보

| 항목 | 값 |
|---|---|
| 제품명 | `Blockable Block Designer` |
| 배포 패키지명 | `blockable-block-designer` |
| Python 패키지 | `blockable_block_designer` |
| Python 소스 | `src/blockable_block_designer/` |
| 현재 버전 | `v1.2.2` |
| 프로그램 저장 JSON 스키마 | `1.2.0` |
| 기본 저장 파일 | `blockable_block_design.json` |
| 현재 기준 디자인 JSON | `examples/blockable_block_design.json` |
| 최소 스키마 예제 | `examples/blockable_rules.example.json` |
| 효과 설정 예제 | `examples/blockable_effect_config.example.json` |

제품명과 패키지명에 `Deigner` 또는 `deigner`를 사용하지 않는다.

## 4. 현재 기준 디자인 JSON 스냅샷

Codex가 Blockable 게임 적용이나 규칙 분석을 수행할 때 사용하는 현재 데이터 원본은
`examples/blockable_block_design.json`이다. 다음 수치는 2026-07-26 저장본을
확인한 스냅샷이며, 작업할 때는 문서의 숫자를 신뢰하지 말고 JSON을 다시 집계한다.

| 항목 | 현재 값 |
|---|---|
| 원본 `schema_version` | `1.1.0` (Designer에서 열고 저장하면 `1.2.0`) |
| `metadata.validation_status` | `valid` |
| 색상 | 7개 |
| Block Type | 7개 |
| 효과 정의 | 8개 |
| 블록 | 28개 |
| 조합식 | 47개 |
| 공통 색상 시너지 | 0개 |
| 저장 당시 경고 | 66개 |

현재 색상 ID:

```text
fire, legendary, nature, water, steel, special, curse
```

현재 Type ID:

```text
fire, water, nature, special, legend, steel, curse
```

색상 `legendary`와 Type `legend`는 이름이 다르다. 표시 이름이나 유사한 철자를
근거로 동일 ID로 바꾸지 않는다.

원본 JSON의 효과 정의 ID:

```text
deal_damage, gain_block, heal, apply_status,
apply_buff, draw_block, gain_gold, modify_next_effect
```

게임 적용 전 Designer로 다시 저장하거나 동일한 마이그레이션을 수행한다.
`apply_buff`는 `apply_status`로 통합하고, 모든 효과 인스턴스는
`docs/BLOCKABLE_COMBAT_EFFECT_STANDARD.md`의 ID·파라미터·대상·범위 규칙을
따라야 한다. 사용자 정의 효과와 사용자 정의 상태는 보존하되, 게임 런타임에
해당 ID 처리기가 있는지 별도로 확인한다.

블록은 Type별로 다음과 같이 구성된다.

| Type | 블록 수 | 블록 ID |
|---|---:|---|
| `steel` | 3 | `s001`~`s003` |
| `fire` | 3 | `f001`~`f003` |
| `water` | 3 | `w001`~`w003` |
| `nature` | 3 | `n001`~`n003` |
| `legend` | 4 | `l001`~`l004` |
| `special` | 6 | `a001`~`a006` |
| `curse` | 6 | `c001`~`c006` |

조합식은 태그 기준 `3x3` 10개와 `4x4` 37개다. ID 접미사 기준으로 `steel`
25개, `fire` 11개, `water` 11개가 있다. 배열 순서는 설계자가 정한 우선순위일
수 있으므로 정렬하거나 재생성하지 않고 원본 순서를 보존한다.

현재 조합 슬롯은 `exact_block` 116개와 `any_block` 2개를 사용한다. 스키마가
지원하는 `type`, `color`, `tag` 슬롯이 현재 파일에 없다는 이유로 로더 지원을
제거해서는 안 된다. `conditional_effects`와 `color_synergies`가 현재 비어 있어도
스키마 필드와 판정 코드는 유지한다.

현재 파일은 편집기 검증에서 오류 0개, 경고 66개다. 분리된 블록, 효과가 없는
블록, 미사용 블록과 3×3보다 큰 조합식 경고는 의도된 설계일 수 있다. 경고를
없애기 위해 JSON을 임의로 수정하지 않는다.

## 5. 실행 및 테스트

### Linux

```bash
PYTHONPATH=src python -m blockable_block_designer
```

환경에 따라:

```bash
PYTHONPATH=src python3 -m blockable_block_designer
```

### Windows PowerShell

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python -m blockable_block_designer
```

프로젝트를 editable 모드로 설치하면:

```powershell
python -m pip install -e .
python -m blockable_block_designer
```

### 테스트

```bash
PYTHONPATH=src python -m pytest -q
```

캐시를 만들 수 없는 읽기 전용 환경에서는:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q -p no:cacheprovider
```

## 6. 주요 파일 책임

| 경로 | 책임 |
|---|---|
| `domain/models.py` | 블록, 효과, 조합식, 시너지 데이터 모델 |
| `domain/transforms.py` | 회전, 반전, 좌표 정규화, 점유 칸 계산 |
| `domain/validation.py` | 오류와 경고 검증 |
| `persistence/json_codec.py` | 모델과 JSON 객체 변환 |
| `persistence/project_file.py` | 스키마 확인, 안전 저장, 불러오기 |
| `services/` | UI와 분리된 편집 동작 |
| `ui/` | tkinter 화면과 입력 처리 |
| `tests/` | 도형, 검증, 저장 왕복 및 서비스 테스트 |

tkinter 객체를 `domain`, `persistence`, `services`에 전달하지 않는다.

## 7. 데이터 변경 원칙

- Block Definition과 Combination의 Block Instance를 구분한다.
- 모든 블록은 하나의 `blocks` 배열에서 관리하고 `type_id`로 분류한다.
- 효과는 실행 코드가 아니라 `effect_id + parameters`로 저장한다.
- 게임 동작을 JSON의 `description`이나 표시 이름으로 추측하지 않는다.
- ID 참조를 변경할 때 모든 사용처를 함께 갱신한다.
- 스키마를 변경하면 `schema_version`, 예제 JSON, 스키마 문서와 테스트를 함께
  갱신한다.
- 알 수 없는 최신 필드를 조용히 삭제하지 않는다.
- UTF-8, JSON 들여쓰기 2칸과 원자적 저장 방식을 유지한다.

## 8. 현재 편집 규칙

- 프로젝트 ID는 공백 없이 자유롭게 지정할 수 있다.
- 효과·버프·상태의 내부 ID는 영문 소문자 `snake_case`를 사용한다.
- 분리된 블록 모양은 허용하며 경고만 표시한다.
- 조합식의 블록 인스턴스는 서로 붙어 있지 않아도 된다.
- 인스턴스 사이의 빈 공간은 조합식 도면의 일부로 보존한다.
- 인스턴스가 겹치면 오류다.
- 조합식 인스턴스는 드래그로 이동하며 기존 회전·반전·슬롯 조건을 유지한다.
- 편집 중 겹침은 허용하고 빨간색으로 표시하지만 파일 저장은 항상 차단한다.
- 조합식에서 선택한 인스턴스는 `R` 키로 CCW 90도 회전한다.
- 블록과 조합식 배열 순서는 편집기의 목록 이동 결과를 보존한다.
- 오류가 있어도 사용자 확인 후 `validation_status: invalid`인 초안으로 저장할
  수 있다.
- 정상 게임 데이터는 `metadata.validation_status`가 `invalid`가 아니어야 한다.

## 9. 조합 슬롯 판정 계약

`combination.instances[].match.kind`는 다음을 지원한다.

| kind | 의미 |
|---|---|
| `exact_block` | 지정 `block_id`만 허용 |
| `any_block` | 색상·ID와 관계없이 같은 모양 허용 |
| `type` | 같은 모양이며 지정 Type인 블록 허용 |
| `color` | 같은 모양이며 지정 색상인 블록 허용 |
| `tag` | 같은 모양이며 지정 태그가 있는 블록 허용 |

조건형 슬롯에서도 `block_id`는 모양 템플릿으로 사용한다.

블록 셀 변환 순서:

1. 좌우 반전
2. 90도 단위 회전: `(x, y) -> (-y, x)`
3. 최소 좌표가 `(0, 0)`이 되도록 정규화
4. 인스턴스 `origin` 추가

조합식 전체의 `allow_recipe_rotation`, `allow_recipe_mirroring`도 판정한다.

## 10. 효과 및 시너지 적용

권장 처리 순서:

1. 참여 블록의 자체 효과
2. 조합식 기본 효과
3. 조합식 조건부 효과
4. 활성화된 프로젝트 공통 색상 시너지
5. 본 게임의 최종 수치 보정

같은 단계에서는 `order` 오름차순으로 처리한다. `order`는 효과 수치가 아니라
효과 적용 순서다.

지원 조건:

- `all_same_color` (`color_id`가 있으면 지정 색상의 단일 시너지)
- `all_different_colors`
- `contains_color`
- `color_count`
- `color_set`
- `same_type`
- `block_count`
- `tag_match`

알 수 없는 효과 ID와 조건은 조용히 무시하지 말고 개발 환경에서 오류를
보고한다.

`effect_definitions`는 편집기에서 사용자가 추가·수정할 수 있다. 정의의
`display_name`과 `description`은 설명용이며 실행은 `id`로 연결한다. 숫자
parameter의 `allow_negative: true`를 존중하여 공격·방어·회복의 음수 보정값도
최종 합산에 포함한다. `default`는 편집기 입력 초기값이다.
블록과 조합의 공격·방어·회복 최종 수치는 규칙 JSON을 단일 원본으로 사용하고
본 게임 코드에 같은 수치를 중복 하드코딩하지 않는다.

각 효과 값 편집 대화상자는 기존 정의 드롭다운과 별도의 새 효과 만들기 기능을
제공한다. 효과 정의는 `blockable_effect_config.json`으로 가져오고 내보낼 수
있으며 형식은 `config_version: "1.0.0"`과 `effect_definitions` 배열이다. 이
공유 파일에는 실제 블록·조합식 효과 인스턴스 값이 아니라 정의 양식만 저장한다.

## 11. 변경 유형별 Codex 명령 예시

### 기능 추가

```text
AGENTS.md와 필수 문서를 먼저 읽으세요. 요청 기능이 JSON 스키마에 영향을 주는지
분석하고, 도메인 모델과 순수 로직을 먼저 구현한 뒤 UI를 연결하세요. 관련 테스트와
문서를 갱신하고 전체 pytest 결과를 보고하세요.
```

### 버그 수정

```text
AGENTS.md와 필수 문서를 먼저 읽으세요. 버그를 재현하거나 원인을 확인한 뒤 최소
범위로 수정하세요. 같은 문제가 재발하지 않도록 테스트를 추가하고 전체 회귀 테스트
결과를 보고하세요.
```

### JSON을 본 게임에 적용

```text
AGENTS.md와 스키마 문서를 읽고 examples/blockable_block_design.json을 데이터 원본으로
사용하세요. 수치를 게임 코드에 중복 하드코딩하지 말고 ID Map, 좌표 변환, 슬롯
조건, 조합 전체 변환, 효과 dispatch, 조건부 효과와 시너지를 구현하세요. 설명
문자열을 실행 로직으로 해석하지 마세요. 게임 저장소 안의 대상 경로는 저장소
구조를 먼저 확인한 뒤 프로젝트 상대 경로로 정하고, 원본 JSON은 임의로 수정하지
마세요.
```

### 문서만 수정

```text
AGENTS.md와 필수 문서를 먼저 읽으세요. 기능 코드는 변경하지 말고 현재 프로그램
이름, 버전, 패키지 경로와 실제 동작을 기준으로 관련 문서를 모두 일관되게
수정하세요. 이전 이름과 깨진 링크가 남지 않았는지 전체 검색하세요.
```

## 12. Blockable 게임 적용 절차

Designer의 기본 저장 파일명은 `blockable_block_design.json`이며, 이 저장소의
현재 기준 파일은 `examples/blockable_block_design.json`이다. 게임 저장소에서 규칙 파일을 관리하는 권장
위치는 `docs/references/designs/blockable_block_design.json`이다. 실제 게임
저장소의 구조나 `AGENTS.md`에서 다른 경로를 지정하면 그 지침을 우선한다.

Codex는 게임 적용 작업을 다음 순서로 수행한다.

1. 게임 저장소의 `AGENTS.md`와 필수 문서를 읽는다.
2. 대상 JSON을 직접 읽고 `schema_version`과 `metadata.validation_status`를
   확인한다.
3. JSON을 한 번 로드한 뒤 `colors`, `block_types`, `effect_definitions`, `blocks`,
   `combinations`, `color_synergies`를 ID Map으로 구성한다.
4. 수치와 조합 규칙을 게임 코드에 다시 하드코딩하지 않는다.
5. 블록 좌표 변환, 슬롯 조건, 조합 전체 변환, 효과 dispatch, 조건부 효과와
   공통 시너지를 구현한다.
6. JSON 원본은 명시적인 데이터 수정 요청이 없으면 변경하지 않는다.
7. 적용 완료 후 대상 프로젝트의 로더가 원본 JSON의 배열 개수, ID와 배열 순서를
   보존했는지 비교한다.

`metadata.validation_status`가 `invalid`인 파일은 편집 초안이다. 게임 빌드나
런타임 데이터로 조용히 받아들이지 말고 명확한 오류로 거부한다.

## 13. ID와 표시 문자열

- 게임 로직, 저장 데이터와 참조에는 `id`만 사용한다.
- `display_name`, `name`, `description`은 UI 표시 전용이다.
- 색상 ID와 Type ID는 별도 이름 공간으로 취급한다.
- 한글 효과명과 설명은 표시할 수 있지만 실행할 효과는 `effect_id`로 판정한다.
- `description`에 적힌 수치나 의미를 실제 효과처럼 추론하지 않는다.

JSON의 배열 개수와 ID 목록은 버전마다 달라질 수 있다. 이 문서에 개수를
하드코딩하지 말고 적용 대상 JSON을 직접 집계한다.

## 14. 최소 런타임 타입 예시

TypeScript 게임이라면 최소한 다음과 같은 경계를 둔다. 실제 필드의 선택 여부와
세부 타입은 대상 JSON 및 `docs/RULE_SCHEMA_1_1.md`를 기준으로 보완한다.

```ts
type Cell = { x: number; y: number };

type Effect = {
  effect_id: string;
  order: number;
  parameters: Record<string, unknown>;
};

type SlotMatch = {
  kind: "exact_block" | "any_block" | "type" | "color" | "tag";
  type_id?: string;
  color_id?: string;
  tag?: string;
};

type BlockInstance = {
  block_id: string;
  origin: Cell;
  rotation: 0 | 90 | 180 | 270;
  mirrored: boolean;
  match?: SlotMatch;
};
```

최상위 규칙 객체에는 최소한 다음 컬렉션을 읽을 수 있어야 한다.

```ts
type BlockableRules = {
  schema_version: string;
  metadata?: { validation_status?: string };
  colors: unknown[];
  block_types: unknown[];
  effect_definitions: unknown[];
  blocks: unknown[];
  combinations: unknown[];
  color_synergies: unknown[];
};
```

## 15. 조합 판정 세부 규칙

### 블록 셀 변환

각 인스턴스는 참조 블록의 셀을 가져와 다음 순서로 변환한다.

1. `mirrored`가 참이면 x축 좌표의 부호를 바꾼다.
2. `rotation` 횟수만큼 `(x, y) -> (-y, x)`를 적용한다.
3. 변환된 셀의 최소 x와 최소 y가 0이 되도록 정규화한다.
4. 인스턴스 `origin`을 더해 조합식 좌표에 배치한다.

블록 정의의 허용 회전·반전 정책과 조합식의
`allow_recipe_rotation`·`allow_recipe_mirroring`을 각각 확인한다.

### 슬롯 조건

- `exact_block`: `block_id`가 같은 블록만 통과한다.
- `any_block`: `block_id`는 모양 템플릿이며 실제 블록의 색상과 ID는 묻지 않는다.
- `type`: 템플릿과 모양이 같고 `type_id`가 같은 블록만 통과한다.
- `color`: 템플릿과 모양이 같고 `color_id`가 같은 블록만 통과한다.
- `tag`: 템플릿과 모양이 같고 지정 태그를 가진 블록만 통과한다.

조건형 슬롯에서도 `block_id`를 무시하지 않는다. 이는 정확한 블록 강제가 아니라
슬롯이 요구하는 모양의 템플릿이다.

### 전체 판정

- 모든 인스턴스의 셀 합집합을 기준으로 비교한다.
- 분리된 블록, 인스턴스 사이의 빈 공간과 블록 내부 빈칸을 허용한다.
- 인스턴스끼리 점유 셀이 겹치면 실패한다.
- 편집기는 겹친 임시 배치를 표시할 수 있지만 저장 파일과 게임 로더는 거부한다.
- 전체 조합 좌표의 최소 x와 y가 0이 되도록 정규화한 뒤 비교한다.
- 조합식 전체 회전과 반전을 허용한 경우 가능한 변형을 모두 검사한다.
- 여러 조합식이 동시에 일치하면 임의로 하나를 고르지 않는다. 게임의 우선순위
  정책이 없다면 일치 목록을 반환하고 선택 정책을 별도 결정한다.

## 16. 조건부 효과 판정

조합 참여 블록의 실제 색상, Type, 태그와 개수를 기준으로 판정한다.

| 조건 | 의미 |
|---|---|
| `all_same_color` | 참여 블록의 색상 ID가 모두 같다. 선택적 `color_id`가 있으면 그 색상이어야 한다. |
| `all_different_colors` | 참여 블록의 색상 ID가 모두 다르다. |
| `contains_color` | 지정 `color_id`가 하나 이상 포함된다. |
| `color_count` | 지정 색상의 개수가 요구값과 정확히 같다. |
| `color_set` | 요구 색상 목록과 실제 색상 목록을 중복 포함 멀티셋으로 비교한다. |
| `same_type` | 참여 블록의 Type ID가 모두 같다. |
| `block_count` | 참여 블록 수가 요구값과 정확히 같다. |
| `tag_match` | 참여 블록 중 하나 이상이 지정 태그를 가진다. |

색상이나 Type을 표시 이름으로 비교하지 않는다. `color_id` 없는 `all_same_color`가 참이라고 해서
자동으로 불 속성 등의 특정 색상 효과로 해석해서도 안 된다.

## 17. 효과 dispatch와 적용 순서

`effect_definitions` 배열은 효과 정의 사전이고, 블록·조합식·시너지에서는 `effect_id`와
`parameters`를 통해 이를 참조한다. 게임은 지원하는 `effect_id`별 handler를
명시적으로 등록한다. 대상 JSON에 처음 보는 ID가 있으면 조용히 무시하지 말고
개발 단계에서 오류를 낸다.

적용 순서는 다음과 같다.

1. 참여 블록 자체 효과
2. 조합식 기본 효과
3. 조건을 통과한 조합식 추가 효과
4. 조건을 통과한 프로젝트 공통 색상 시너지
5. 게임의 최종 수치 보정

각 단계 내부에서는 `order` 오름차순으로 정렬한다. `order`가 같다면 JSON 배열
순서를 유지하는 안정 정렬을 사용한다. `order`는 효과의 값이 아니며 실제 수치는
`parameters`에서 읽는다. 버프 효과는 버프 내부 ID를 로직에 사용하고 한글 버프명은
표시에만 사용한다.

## 18. 최소 로더 검증

게임 로더는 적어도 다음 항목을 검사한다.

- 지원하는 `schema_version`인가?
- `metadata.validation_status`가 `invalid`가 아닌가?
- 모든 `block.type_id`가 존재하는 Type을 참조하는가?
- 모든 색상 참조가 존재하는가?
- 모든 `effect_id`가 정의되어 있고 게임 handler가 지원하는가?
- 모든 `combination.instances[].block_id`가 존재하는가?
- 조합식 인스턴스의 점유 셀이 겹치지 않는가?
- 회전 값과 좌표 값이 지원 범위와 정수 조건을 만족하는가?

경고가 존재하는 것과 로딩 실패는 구분한다. 분리된 블록과 떨어진 조합 구조는
허용된 데이터이므로 그것만으로 오류 처리하지 않는다.

## 19. 완료 전 확인 목록

- [ ] `AGENTS.md`와 필수 문서를 읽었는가?
- [ ] 사용자 요청 외의 게임 규칙을 임의로 확정하지 않았는가?
- [ ] 기존 사용자 변경과 관련 없는 파일을 보존했는가?
- [ ] 제품명과 경로에 `Deigner/deigner`가 남지 않았는가?
- [ ] JSON 호환성을 유지했는가?
- [ ] 적용 대상 JSON의 실제 배열과 ID를 직접 확인했는가?
- [ ] 표시 문자열이 아니라 ID와 `parameters`로 동작하는가?
- [ ] 분리된 모양과 떨어진 조합 구조를 허용하는가?
- [ ] 회전·반전·정규화와 슬롯 조건 테스트가 있는가?
- [ ] 조건부 효과와 공통 시너지의 적용 순서를 검증했는가?
- [ ] 필요한 테스트를 추가하거나 수정했는가?
- [ ] 전체 `pytest`가 통과했는가?
- [ ] `git diff --check`가 통과했는가?
- [ ] Git 커밋이나 푸시를 사용자 허가 없이 수행하지 않았는가?
