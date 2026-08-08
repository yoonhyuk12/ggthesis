---
name: recording-learnings
description: Use when a correction is discovered and must be recorded to MEMORY.md — 사용자가 세션 중 무언가를 바로잡았을 때, 심사·지도교수 코멘트가 반복 실수를 드러냈을 때, 인용·수치·법령·표기·hwpx 도구 사용법이 틀렸다고 확인됐을 때. `[LEARN:category]` 태그 형식, 카테고리 선택, 중복 점검, MEMORY.md 기록 위치를 다룬다.
---

# Recording Learnings with [LEARN] Tags

## Format

```
[LEARN:category] Incorrect → Correct — applies when: {context}
```

The `— applies when:` suffix is **required** for `method` and `domain` categories (where context determines applicability). It is **optional** for `notation` and `citation` (which are typically universal).

Examples:
```
[LEARN:domain] "산업안전보건관리비" → "산업안전보건관리비(산안비)" 첫 언급 시 약어 병기 — applies when: 본문 첫 등장
[LEARN:method] 매개효과 유의성은 Sobel test → 부트스트랩 신뢰구간으로 판단 — applies when: PROCESS macro 분석
[LEARN:citation] ref 28 인용 페이지는 인쇄 쪽수 기준 → PDF 인덱스와 2쪽 차이
```

## Categories

| Category | What to record |
|----------|---------------|
| `notation` | 표기·용어 규칙 (변수 기호 X/M/W/Y, 약어 병기, 문체) |
| `citation` | 서지·인용 이슈 (페이지 불일치, 표기 형식) |
| `method` | 통계·방법론 교정 |
| `domain` | 도메인 지식 교정 (법령·고시, 건설현장 제도, 시스템 사양) |
| `hwpx` | hwpx MCP 도구 함정과 안전한 사용 패턴 |

## When to Record

- **Immediately** when a correction is discovered — do not batch
- When the user corrects something during a session
- When a 심사·지도교수 코멘트 reveals a recurring mistake

## Dedup Check (before writing)

Before appending a new entry to MEMORY.md, **grep the file for the key terms** in your learning. If an existing entry covers the same topic:

- **Same correction:** Skip — it's already recorded.
- **Updated correction:** Replace the old entry (don't append a duplicate).
- **Contradictory:** Replace the old entry, add `[SUPERSEDED YYYY-MM-DD]` note explaining what changed.

## Where to Write

Append to `MEMORY.md` in the project root, under the matching category section. If `MEMORY.md` does not exist, create it with sections: Notation Registry(변수·용어 규칙), Key Decisions(결정·근거·날짜), Citations(인용 교정), Anti-Patterns(방법·도메인 교정), hwpx Pitfalls.

## Important

One line per learning, wrong → right direction explicit. Entries accumulate and inform future sessions.
