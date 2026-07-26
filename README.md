# Blockable Block Designer

현재 버전: `v1.2.2`

Blockable 웹 게임에서 사용할 블록과 조합 규칙을 시각적으로 만들고 JSON으로
저장하는 Python 데스크톱 디자인 도구입니다.

주요 기능:

- 사용자 정의 Type, 색상 및 블록 모양
- 정확한 블록, Type, 색상, 태그 또는 임의 블록을 받는 조합 슬롯
- 모든 슬롯을 한 번에 모양 전용 조합으로 변경
- 조합의 기본 효과와 같은 색 등 조건부 보너스
- 모든 조합에 공통 적용할 색상 시너지
- 회전·반전을 유지하는 조합 블록 드래그 이동
- 선택 블록 `R` 키 CCW 회전과 편집 중 겹침 하이라이트
- 색상별 단일 속성 시너지와 사용자 정의 효과 관리
- `blockable_effect_config.json` 효과 정의 가져오기·내보내기
- 블록·조합식 목록 순서 편집과 음수 효과 값
- JSON을 몰라도 사용할 수 있는 효과별 값 입력 폼과 버프 전용 입력
- 오류가 있어도 작업을 보존할 수 있는 초안 저장 및 재편집
- 블록·조합식별 입력 적용 버튼과 ID 변경 참조 자동 갱신
- JSON 검증, 안전 저장 및 `1.0.0` 규칙 파일 호환 로딩

## 실행

Python 3.12 이상이 필요합니다.

패키지를 설치한 환경에서는 `python -m blockable_block_designer`로 실행할 수
있습니다.

소스 체크아웃에서 설치하지 않고 실행하려면 프로젝트 최상위 폴더에서 다음
명령을 사용합니다.

Linux:

```bash
PYTHONPATH=src python -m blockable_block_designer
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m blockable_block_designer
```

Windows 명령 프롬프트:

```bat
set PYTHONPATH=src
python -m blockable_block_designer
```

## 테스트

```bash
PYTHONPATH=src python -m pytest
```

규칙 파일은 UTF-8 JSON이며 기본 파일명은 `blockable_block_design.json`입니다. 예제는
`examples/blockable_rules.example.json`에서 확인할 수 있습니다.

## 문서

- 기획 및 개발 기준: `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
- 사용자 설명서: `docs/USER_MANUAL.md`
- JSON 1.1 추가 계약: `docs/RULE_SCHEMA_1_1.md`
- 업데이트 내역: `update.txt`
- Codex 작업 지침: `docs/Blockable_Block_Design_Codex_Interaction_Instruction.md`
- 효과 설정 예제: `examples/blockable_effect_config.example.json`
