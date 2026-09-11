---
paths:
  - "00. hwpx/**"
  - "tools/hwpx_transfer/**"
  - ".claude/skills/hwpx-thesis-editing/**"
---

# Rule: hwpx Output Verification (hwpx 산출물은 한글이 열어야 완료다)

## Principle

**ZIP 무결성·XML 파싱·엔트리 대조를 통과해도 한글이 못 여는 hwpx가 나온다.** 산출물은 반드시 한글 COM(`HWPFrame.HwpObject`)으로 실제 개방까지 확인한 뒤에만 "완료"라고 말한다. 2026-09-11에 실제로 겪었다 — 검증 4단계를 전부 통과한 파일이 `Open=False`였다.

## 필수 절차 (hwpx를 만들거나 고쳤을 때)

1. **한글 COM 개방 시험.** `RegisterModule('FilePathCheckDLL','FilePathCheckerModule')` 후 `Open(path,'HWPX','forceopen:true')`가 `True`여야 한다. 검증 스크립트 예: `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1`.
2. **텍스트 길이가 바뀐 문단은 `<hp:linesegarray>`를 정리한다.** `lineseg`의 `textpos`가 새 본문 길이를 넘기면 한글이 파일을 아예 열지 못한다. 넘치는 lineseg를 잘라내고 최소 1개만 남기면 한글이 열 때 재조판한다. 이것이 위 1번 실패의 실제 원인이었다.
3. **한글로 재조판 저장(`SaveAs`)까지 한 뒤** 그 파일을 산출물로 삼는다. 재저장 후 charPr id가 바뀌므로 빨간 마커 검증은 `header.xml`의 `textColor="#FF0000"` charPr을 다시 읽어 판정한다.
4. 부분 치환 뒤에도 원본 파일 SHA256이 불변임을 보고한다.

## 표 쪽 넘김 규칙 (사용자 지시, 2026-09-11)

표가 쪽 경계를 넘을 때 처리 우선순위:

1. **새 페이지로 밀어 한 장에 담는다** — `<hp:tbl pageBreak="NONE">`(나누지 않음). 한글이 남은 공간에 못 들어가는 표를 통째로 다음 쪽으로 넘긴다.
2. 그래도 넘으면 **컬럼 폭을 조정**한다.
3. 그래도 넘으면 **표를 나눈다** — `pageBreak="TABLE"` + `repeatHeader="1"`(행 경계에서 나누고 머리행 반복).

기본값 `pageBreak="CELL"`(셀 단위 나눔)은 셀 중간이 잘리므로 **쓰지 않는다.** 표가 한 쪽에 들어가는지는 `<hp:cellSz height>` 행 높이 합 vs 본문 높이(`pagePr height` − 상·하 여백 − 머리말·꼬리말)로 계산한다. 판정 도구: `tools/hwpx_transfer/` 또는 세션 스크래치의 `tblplan.py` 방식.

## hwpx MCP 도구 사용 한계

- 학위논문 본문(`section2.xml` 약 2.5MB)에 `Get Document Text`/`Get Document Outline` 같은 **MCP 읽기 도구를 호출하면 40분 이상 응답 없이 멈춘다.** 본문 대조·분석은 파이썬 `zipfile`+`ElementTree`로 직접 읽는다.
- 루트 `hwpx-mcp-simple/`은 `.gitignore` 대상이라 새 PC에는 없다. 소스는 `기타/0. 논문작성 템플릿/0. 논문작성 템플릿/hwpx-mcp-simple/`이며, venv 재구축 시 `mcp==1.27.0`·`python-hwpx==2.9.1`로 핀을 내려야 기동한다(`pyproject.toml`은 하한 전용이라 최신 의존성이 API를 깨뜨린다).

## Anti-Patterns

- **Don't** ZIP·XML 검증만 하고 "한글에서 열린다"고 보고하기
- **Don't** `linesegarray`를 그대로 둔 채 문단 텍스트만 줄이기
- **Don't** `pageBreak="CELL"` 유지
- **Don't** 워커에게 hwpx MCP 읽기 도구로 본문을 읽게 하기 (금지 목록은 `subagent-write-guard.md`)
