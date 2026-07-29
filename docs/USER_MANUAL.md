# Blockable Block Designer 사용 설명서

현재 프로그램 버전: `v1.3.1`

## 1. 용도

이 프로그램은 Blockable 본 게임이 읽을 블록과 조합식 데이터를 제작합니다.
전투 실행, 조합 탐색, 실제 참여 블록의 색상·등급 보너스 판정은 본 게임이
담당합니다.

## 2. 실행

프로젝트 최상위 폴더에서 실행합니다.

Linux:

```bash
PYTHONPATH=src python -m blockable_block_designer
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python -m blockable_block_designer
```

Windows 명령 프롬프트:

```bat
set PYTHONPATH=src
python -m blockable_block_designer
```

`python` 명령이 Microsoft Store 별칭으로 연결되어 `Python`만 출력된다면
Python 3.12 설치 경로의 실행 파일을 직접 사용하거나 Windows 앱 실행 별칭에서
`python.exe` 별칭을 해제합니다.

## 3. 새 프로젝트와 저장

- `Ctrl+N`: 새 프로젝트
- `Ctrl+O`: JSON 열기
- `Ctrl+S`: 저장
- 기본 파일명: `blockable_block_design.json`

새 파일은 다음 최상위 구조로 저장됩니다.

```json
{
  "schema_version": "1.1.0",
  "data_type": "blockable_block_design",
  "metadata": {},
  "blocks": [],
  "combinations": []
}
```

오류가 있는 데이터는 초안으로 저장할 수 있지만
`metadata.validation_status`가 `invalid`가 됩니다. 조합 인스턴스가 겹친
상태는 초안으로도 저장할 수 없습니다.

## 4. 블록 Type 관리

Type에는 다음 네 값이 있습니다.

- Type ID: 영문 소문자 `snake_case`
- Type 이름: 화면 표시용 이름
- 등급: `normal`, `special`, `legend`, `curse`
- 색상: `steel`, `nature`, `fire`, `water`, `none`

색상이 없다는 의미는 필드 누락이 아니라 `none`입니다.

## 5. 블록 편집

1. `블록 Type 관리`에서 Type을 만듭니다.
2. `블록 편집기`에서 `추가`를 누릅니다.
3. 블록 ID, 이름, Type과 색상을 설정합니다.
4. 가운데 격자를 클릭해 원본 모양을 만듭니다.
5. 블록 단위 회전·반전 허용 여부를 설정합니다.
6. 설명과 7.4 효과를 입력합니다.
7. 목록의 `저장`으로 현재 입력을 적용하고, 상단 저장으로 JSON에 기록합니다.

블록 좌표는 저장할 때 최소 좌표가 `(0, 0)`이 되도록 정규화됩니다. 분리된
모양은 경고지만 저장할 수 있습니다.

## 6. 7.4 공통 효과 편집

효과의 공통 필드는 다음과 같습니다.

- 효과 ID: 효과 인스턴스의 고유한 `snake_case` ID
- 효과 이름: 사람이 보는 이름
- 설명: 실행 판정에 사용하지 않는 설명
- 대상: `SELECTED`, `self`, `L1/R1/B1` 같은 방향 범위, `all`
- 값: 피해, 방어, 회복, 스택 또는 증감 수치
- Type
- Parameters ID: Type 안에서 구체적인 처리 규칙을 고르는 값
- 지속 턴: `0` 즉시, 양수는 지속 턴, `-1` 전투 종료까지, `-2` 영구
- 강도/추가 스택: 사용하지 않으면 `0`, 사용하면 `1` 이상

허용 Type:

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

모든 효과는 `parameters.id`, `duration`, `intensify`를 빠짐없이 저장합니다.
`BASE_DAMAGE`, `INDEPENDENT_DAMAGE`, `BLOCK`, `RECOVERY`는
`NONE/0/0`으로 자동 고정됩니다.
`BASE_HIT_COUNT`는 이번 행동에만 적용되는 연속 기본 공격입니다.
`value`에는 기본 공격 1타의 B, `intensify`에는 이번 행동의 총 공격 횟수 H를
입력하며 `CURRENT_ACTION/duration: 0`으로 고정됩니다.
`BUFF + HIT_COUNT`는 삭제된 구성이므로 사용할 수 없습니다.
`value`는 정수 또는 소수를 입력할 수 있으며, 비율은 임시 호환 규칙으로
`10`과 `0.1`을 모두 10%로 해석합니다. 추가 횟수·용량처럼 개수를 나타내는
효과의 `value`는 정수여야 합니다.
`effect_name`이나 `description`을 게임 실행 키로 사용하면 안 됩니다.

## 7. 재사용 효과 설정

상단의 `효과 설정` 탭에서 자주 사용하는 효과의 ID, 이름, 설명을 한 번
등록할 수 있습니다.

1. `효과 설정` 탭에서 `추가`를 누릅니다.
2. 효과 ID, 효과명과 설명을 입력합니다.
3. 블록 또는 조합식의 효과 목록에서 `추가`를 누릅니다.
4. `저장된 효과 설정` 드롭다운에서 등록한 효과를 선택합니다.
5. 실행 Type, 대상, 값과 Parameters를 해당 사용 위치에 맞게 설정합니다.

같은 설정을 여러 번 선택하면 전역 중복을 피하도록 효과 ID 뒤에 `_2`, `_3`
같은 번호가 자동으로 붙습니다.

효과 설정은 디자인 JSON과 분리된 프로젝트 상대 경로의
`blockable_effect_config.json`에 자동 저장됩니다. 따라서 다른 디자인 JSON을
열거나 새 프로젝트를 만들어도 계속 사용할 수 있습니다. `효과 설정 가져오기`
및 `효과 설정 내보내기`로 다른 작업 환경과 공유할 수도 있습니다.

효과 설정은 ID·이름·설명을 다시 입력하는 작업을 줄이는 편집용 프리셋입니다.
실제 게임 실행 의미는 각 블록·조합식 효과에 저장되는 7.4 Type, 대상, 값과
Parameters가 결정합니다.

## 8. 조합식 편집

1. 조합식을 추가합니다.
2. 왼쪽 팔레트에서 블록을 선택하고 격자를 클릭해 배치합니다.
3. 배치된 블록을 드래그해 이동합니다.
4. 선택 블록은 `R` 키 또는 버튼으로 CCW 90° 회전할 수 있습니다.
5. 필요한 경우 인스턴스를 반전합니다.
6. 조합식 전체 회전·반전 인정 여부를 설정합니다.
7. 색상과 무관하게 항상 실행할 기본 7.4 효과만 입력합니다.

편집 중 겹침은 빨간색으로 표시됩니다. 겹침을 해소해야 저장할 수 있습니다.

조합판 아래의 `예상 효과`에는 현재 배치한 블록들의 효과 합계와 조합식 자체
효과가 다음처럼 표시됩니다.

```text
공격력 10 [선택 대상], 방어 10
미완성 방패: 방어 10, 공격력 -10 [기준+좌우 2칸]
```

같은 블록을 여러 번 배치하면 배치 수만큼 블록 효과를 합산합니다. 이 표시는
Designer JSON에 저장된 블록·조합식 효과만 계산하는 편집 보조 정보입니다.
실제 참여 색상, 등급, 상태, 대상 상황에 따라 본 게임에서 판정하는 시너지는
포함하지 않습니다.

공격 효과에는 `[선택 대상]`, `[자신]`, `[전체]`, `[기준+왼쪽 1칸]`,
`[기준+오른쪽 1칸]`, `[기준+좌우 2칸]`처럼 저장된 `target` 범위를 함께
표시합니다. Type이 같아도 공격 범위가 다르면 서로 합산하지 않고 별도 항목으로
표시합니다.

예상 효과는 Type뿐 아니라 Parameters ID의 표시명도 사용합니다. 예를 들어
`STATUS_DAMAGE + BURN`은 `화상`, `DEBUFF + ATTACK_REDUCTION`은 `약화`,
`BASE_HIT_COUNT + CURRENT_ACTION`은 다음처럼 표시합니다.

```text
연속 기본 공격: B 5 × H 6 [선택 대상]
```

미구현·미연결 Parameters ID는 드롭다운에서 `(미구현 ID)`가 함께 표시됩니다.
JSON에는 괄호 문구 없이 원래 ID만 저장됩니다.

새 JSON에는 다음 항목을 저장하지 않습니다.

- `match`
- `tags`
- `conditional_effects`
- `color_synergies`
- 특정 색상·등급 조건

실제 참여 블록의 색상과 등급에 따른 추가 판정은 본 게임에서 수행합니다.

## 9. 이전 JSON 불러오기

이전 Designer JSON을 열면 새 구조로 변환합니다.

- 최상위 Type/색상 → 각 블록의 `block_type`
- `id/display_name` → `block_id/block_name`
- `transform` → `transform_rule`
- `instances` → `formula.instances`
- `mirrored` → `reflected`
- 이전 효과 ID와 값 → 8장 공통 효과 구조
- 이전 `reference_id` → `parameters.id`
- 매개변수가 없는 1.0 효과 → Type별 `id/duration/intensify` 기본값

이전 `conditional_effects`와 `color_synergies`가 있으면
`metadata.migration_notes`에 이전 필요 수량을 기록합니다. 이 데이터는 본 게임
공통 판정으로 옮길 항목이므로 자동으로 새 조합식 효과로 추측하지 않습니다.

레거시 파일은 원본 보호를 위해 저장 경로가 비워진 상태로 열립니다. 저장 시 새
파일명을 선택해야 합니다.

## 10. 검사 기준

저장을 막는 주요 오류:

- 중복되거나 올바르지 않은 블록·조합식·인스턴스·효과 ID
- 허용되지 않은 등급, 색상, 효과 Type, 대상 또는 Parameters ID
- 유한한 숫자 `value` 누락
- `parameters.id/duration/intensify` 누락 또는 Type별 고정값 위반
- 횟수·용량 효과의 `value`가 정수가 아님
- `BASE_HIT_COUNT`의 `CURRENT_ACTION/duration: 0/intensify: 1+` 규칙 위반
- `STUN`, 현재 행동 추가 턴, 드로우, 현재 행동 배치 효과의 고정 매개변수 위반
- 빈 블록 모양
- 존재하지 않는 블록 참조
- 허용되지 않은 회전·반전
- 조합 인스턴스 겹침

경고는 설명 누락, 효과 누락, 분리된 모양, 사용되지 않는 블록처럼 설계 의도일
수 있는 항목입니다.
