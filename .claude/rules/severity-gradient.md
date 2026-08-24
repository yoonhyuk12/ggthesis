---
paths:
  - "01.docs/**"
  - "학회논문/**"
---

# Rule: Severity Gradient

## Principle

**Calibrate critique intensity to the document's maturity.** Early drafts need encouragement and direction; 투고 직전 원고 needs adversarial scrutiny. The same issue that's a "note for later" in Discovery is a "must-fix blocker" in Pre-submission.

## Phases

| Phase | Tone | Issue Reporting | Threshold |
|-------|------|-----------------|-----------|
| **Discovery** (초안 구상) | Encouraging, directional | Skip Minor. Report Critical and Major only. Focus on structural and conceptual issues. | 60/100 |
| **Drafting** (집필 중) | Constructive, thorough | Report all tiers. Frame fixes as improvements, not failures. | 70/100 |
| **Pre-submission** (투고 직전) | Strict, adversarial | Report all tiers. No mercy — every issue is a reviewer attack surface. | 90/100 |
| **Peer Review** (심사 대응) | Adversarial, formal | Full Reviewer 2 mode. Score hard. Flag anything a hostile reviewer could exploit. | 90/100 |

## Phase Detection

Detect the phase from context clues. Use the **first matching** signal:

| Signal | Phase |
|--------|-------|
| User says "초안", "막 시작", "구상 중" | Discovery |
| User says "작성 중", "쓰고 있는" | Drafting |
| User says "투고 직전", "최종 점검", "제출 전" | Pre-submission |
| User says "심사 코멘트", "수정 요청", "답변서" | Peer Review |
| 원고에 초록이 없거나 서론이 미완성 | Discovery |
| 전 장이 있으나 TODO/placeholder 존재 | Drafting |
| 참고문헌까지 완결된 원고 | Pre-submission |

**When ambiguous:** Default to Drafting. If the user corrects you, adjust immediately.

## Phase Banner

Every review report **must** include a Phase Banner immediately after the header:

```markdown
**Phase:** [Discovery | Drafting | Pre-submission | Peer Review]
**Detected from:** [signal that triggered phase detection]
**Threshold:** [XX/100]
```

This makes the calibration transparent and overridable.

## Override

The user can override the detected phase at any time:
- "투고한다 생각하고 봐줘" → Pre-submission regardless of signals
- "초안이니까 살살" → Discovery regardless of signals
- "Reviewer 2 모드로" → Peer Review regardless of signals

## Count Calibration

**A sanity check on how many issues get reported.** It catches over-compression (merging distinct issues into one) and over-reporting (ghost issues, paraphrase duplicates, listing every sentence as a flaw).

| Tier | Typical count for a **publishable** paper | Signal if out of band |
|------|-------------------------------------------|----------------------|
| Major | **3–7** | <3 → likely over-merged or too lenient; >7 → either the paper is genuinely weak, or moderate issues are mis-tiered as major |
| Moderate + Minor (combined) | remainder, up to **~25** | — |
| **Total issues** | **15–30** | <15 → suspect over-merging; >30 → suspect over-reporting |

1. Count findings by tier after producing the report.
2. If outside the expected band, **flag and reconsider the tiering** — don't silently ship an anomalous count.
3. Root-cause merge Major issues (two symptoms, one fault = one Major). Keep independent Moderate/Minor separate.
4. Earlier phases skew Major-heavy — expected, not a calibration failure.

## When This Applies

Any task producing a scored quality report on 논문 원고 (피어리뷰 시뮬레이션, 원고 검수, 디펜스 리허설). **Skip** for mechanical tasks (형식 검사, 참고문헌 대조) or non-scored tasks.
