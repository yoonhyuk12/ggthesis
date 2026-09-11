# T4 브리프 — `tools/hwpx_transfer/tblplan.py` 표 쪽맞춤 판정기 작성

담당: claude (opus). 상위 계획: `03.plan/260912_0714_hwpx도구개선_오케스트레이션.md`.

## 배경 (재탐색 금지)

- `.claude/rules/hwpx-output-verification.md` 표 쪽 넘김 절은 ① `<hp:tbl pageBreak="NONE">`(통째로 다음 쪽) → ② 열 폭 조정 → ③ `pageBreak="TABLE"` + `repeatHeader="1"` 순서를 정하고, "표가 한 쪽에 들어가는지는 `<hp:cellSz height>` 행 높이 합 vs 본문 높이(`pagePr height` − 상·하 여백 − 머리말·꼬리말)로 계산한다. 판정 도구: `tools/hwpx_transfer/` 또는 세션 스크래치의 `tblplan.py` 방식"이라고 적었다. **그 `tblplan.py`는 존재하지 않는다.** 이번에 실제로 만든다.
- 단위는 HWPUNIT(1/7200 inch). 이전 실측: 이 논문 양식의 본문 높이 = 72567 − 9921 − 4251 − 4251 = **54,144** HWPUNIT (pagePr height − margin top − margin bottom − header − footer). 이 값을 **하드코딩하지 말고** 파일에서 유도한 뒤 일치 여부를 보고한다. `hp:pagePr`의 `width`/`height`/`landscape`, 자식 `hp:margin`의 `header`/`footer`/`left`/`right`/`top`/`bottom`/`gutter` 속성을 쓴다. 정확한 속성명은 실제 XML에서 확인한다.
- 표 XML: `<hp:tbl … pageBreak="…" repeatHeader="…" rowCnt="…" colCnt="…">` 아래 `<hp:tr>` → `<hp:tc>` → `<hp:cellAddr colAddr rowAddr>` · `<hp:cellSpan colSpan rowSpan>` · `<hp:cellSz width height>`. 셀 안에 표가 또 있을 수 있다(중첩).
- 대상 문서: `00. hwpx/260911_1101_경기공학_건축안전_윤혁_논문작성_작성본.hwpx` (읽기 전용, section2.xml 약 2.5MB). 스모크 산출물 `tools/hwpx_transfer/staging/test_out/smoke.hwpx`는 **다른 워커(T1)가 동시에 재생성 중**일 수 있다 — 없거나 잠겨 있으면 건너뛰고 그렇다고 적는다.

## 사양

```
python tools/hwpx_transfer/tblplan.py <hwpx> [--json <out.json>] [--section N] [--selftest]
```

- 표준 라이브러리만(`zipfile`, `xml.etree.ElementTree` 또는 `iterparse`, `argparse`, `json`). 2.5MB 파일에서 5초 이내.
- 섹션마다 `secPr/pagePr`에서 본문 높이·본문 폭을 계산해 출력한다.
- **최상위 표**마다(셀 안 중첩 표는 판정 대상에서 빼되 개수는 보고): 문서 순서 idx, 섹션, 소속 문단 idx, 첫 셀 텍스트 미리보기(30자), `rowCnt`/`colCnt`, `pageBreak`, `repeatHeader`, 행별 높이(그 행에서 시작하고 `rowSpan==1`인 셀들의 `cellSz height` 최댓값; 그런 셀이 없으면 표시), 행 높이 합, 열 폭 합 vs 본문 폭, `fits`(합 ≤ 본문 높이).
- 권고(규칙 3단계 그대로): fits & `NONE` → `OK`; fits & `CELL` → `pageBreak를 NONE으로`; not fits → `단독으로 한 쪽 초과: ② 열 폭·행 높이 축소 검토 → ③ pageBreak=TABLE + repeatHeader=1`. "현재 위치에서 남은 공간에 들어가는가"는 조판 없이는 알 수 없으므로 판정하지 않는다고 출력 머리말에 명시한다.
- stdout에 사람이 읽는 표(고정폭), `--json`이면 같은 내용을 JSON으로. 파일 쓰기는 `encoding="utf-8"`. stdout 출력은 `PYTHONIOENCODING=utf-8` 없이도 죽지 않게 `sys.stdout.reconfigure(encoding="utf-8")` 처리.
- `--selftest`: 메모리에서 작은 합성 section XML(표 2개 — 하나는 들어가고 하나는 넘침, 중첩 표 1개 포함)을 만들어 판정을 assert하고 `OK`를 찍는다.

## 시험 (증거를 그대로 붙여라)

- `--selftest` 통과 출력
- 운영본 실행 결과 요약: 본문 높이(54,144와 일치 여부), 최상위 표 수, 중첩 표 수, fits/not-fits 개수, `pageBreak` 값 분포, 단독 초과 표 목록(있으면), 실행 시간
- `smoke.hwpx`가 있으면 같은 요약
- 코드에서 정규식으로 XML을 파싱하지 않았음(ElementTree 사용)을 확인

## 편집 허용 범위

`tools/hwpx_transfer/tblplan.py` **신규 생성 한 파일만.** 다른 파일은 읽기만.

## Scope of action — DO NOT do these things

- Do NOT run `git add`, `git commit`, `git push`, or any git write command.
- Do NOT call any `mcp__hwpx__*` tool, read or write. 2.5MB 본문에서 40분 멈춘다.
- Do NOT write to `00. hwpx/**` or `tools/hwpx_transfer/staging/**`.
- Do NOT edit `blocks_to_hwpx.py`, `md_to_blocks.py`, `extract_text.py`, `.claude/**`, `MEMORY.md`, `CLAUDE.md`, `03.plan/**`, `01.docs/**`.
- If a step fails, stop, report the exact error output, and do not improvise outside scope.
