# Blockable Block Designer

현재 버전: `v1.3.1`

Blockable 본 게임에서 사용할 블록과 조합식 JSON을 제작하는 Python 데스크톱
도구입니다. 데이터 계약은 `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`와
`docs/BLOCKABLE_COMBAT_SYSTEM.md` 7.4를 따릅니다.

주요 기능:

- 블록 Type의 `grade`와 `color` 관리
- 블록 원본 좌표와 회전·반전 허용 설정
- 블록 인스턴스로 조합식 최종 모양 편집
- 조합식 전체 회전·반전 허용 설정
- 8장/Combat System 7.4 공통 효과의 ID, 대상, 정수 값, Type과 공통 parameters 편집
- UTF-8 JSON 검증과 원자적 저장
- 이전 Designer JSON을 새 계약으로 불러오기

Designer는 실제 조합 탐색, 색상·등급 보너스 판정이나 전투 효과 실행을 하지
않습니다. `conditional_effects`, `color_synergies`, 태그 기반 조건은 새 조합식
JSON에 저장하지 않습니다.

## 실행

Python 3.12 이상과 `tkinter`가 필요합니다.

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

## 테스트

```bash
PYTHONPATH=src python -m pytest
```

기본 저장 파일명은 `blockable_block_design.json`입니다. 현재 스키마는
`1.1.0`이며, 새 JSON 계약의 최소
예제는 `examples/blockable_rules.example.json`에 있습니다.

## 문서

- 구현 기획 및 JSON 계약: `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
- 본 게임 전투 규칙과 7.4 효과: `docs/BLOCKABLE_COMBAT_SYSTEM.md`
- 사용자 설명서: `docs/USER_MANUAL.md`
- Codex 연동 지침: `docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md`
- 변경 내역: `update.txt`
