# W7 — 부록 설문 양식을 윤혁 논문 설문 표 양식 그대로 입히기

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다. 사용자 지시(2026-09-12 15:35): **"설문 형태 표 양식도 내꺼(윤혁 논문)를 그대로 사용해주라."** 원고 MD 수정은 허용됐으나 이 작업에서는 아래 §3의 4줄 추가만 한다.

## 1. 양식(윤혁 논문) 설문 틀 — 실측 (section2, `analysis/section2_paras.json` idx · `analysis/extracted/Contents/section2.xml`)

앵커는 **텍스트로 찾는다**(idx 고정 금지). 세 틀 모두 `pageBreak="NONE"` 표다.

| 틀 | 앵커 | 구조 |
|---|---|---|
| **A. 설문지 표지 상자** | p594 — 3열 표이며 r1 셀 텍스트가 "안녕하십니까?"로 시작 | `rowCnt=2 colCnt=3 width=39232 inMargin 140`. r0: 빈 셀(w2192, bf26, pp34, cp51) / 제목 셀(w35127, bf26, pp42, 제목 2줄 cp41 bold + 부제 1줄 cp62) / 빈 셀(w1913, pp35, cp7). r1: colSpan 3 안내문 셀(w39232 h37789, bf26, pp54, cp36 본문·cp9 강조, 마지막 연월 문단 pp56 cp64). 표 다음에 pp30 문단 4개: `소    속 : …`, `지도교수 : …`, `연 구 자 : …`, `이 메 일 : …` (앞 전각공백 들여쓰기 그대로) |
| **B. Part A 인구통계 상자** | p600 — 1×1 표 안에 중첩 1×1 표 제목 "A. 실태조사 대상자 개요" | 바깥 `1x1 width=38402 bf6 noAdjust=1`, 셀 안 첫 문단(pp46)에 중첩 제목 표(`1x1 width=50179 h1948 bf19 pp53 cp66`), 이어 문항 문단들: 번호 run `cp9`(bold) " A-1)" + 질문 run `cp36`, 선택지 문단 `cp36` "   ① …   ② …", 모두 `pp52`. 미확정 표기는 cp70(빨강) |
| **C. 리커트 격자** | p605 — 12열 표, r0 셀 텍스트 "전혀그렇지않다" 포함 | `rowCnt=11 colCnt=12 width=39491`. r0: 변수명 셀(colSpan2 rowSpan3, w22968, bf7, pp26, cp40) + 척도 라벨 5셀(각 colSpan2 w3310, 마지막 w3283 bf9; 라벨 셀 bf8 pp24/29 cp18/16, 빈 라벨 셀 pp27) — 라벨 텍스트는 "전혀그렇지않다", "", "보통이다", "", "매우그렇다". r1·r2: 높이 1232 장식 행(bf11~18, pp33, cp37) — 척도 라벨 아래 눈금선 역할. r3~: 문항 행 = 번호(w2199 bf20 pp11 cp8) / 진술문(w20769 bf21 pp55 cp7) / ①~⑤(각 colSpan2 w3310, 마지막 w3283 bf22, pp11 cp8). 표 앞에 pp46 문단 2개: "※ 다음 Part B의 모든 문항은 리커트 5점 척도입니다. …" / "(① 전혀 그렇지 않다 — … ⑤ 매우 그렇다)". Part 제목("Part B. 안전관리 실효성")은 pp46 문단 |
| 끝맺음 | p621 | pp46 문단 " 끝까지 응답해 주셔서 진심으로 감사합니다." |

XML 원문은 §1의 idx로 `section2.xml`의 `byte_start~byte_end`를 잘라 본다. **`hp:tbl`은 중첩되므로 `</hp:tbl>` 첫 등장으로 자르지 말고 깊이를 세라.**

## 2. 미소 부록1(`staging/apx1.blocks.json`, 원고 `01.docs/07.부록.md`)에 입힐 대응

| 미소 절(h2/h3) | 적용 틀 | 세부 |
|---|---|---|
| `1. 연구 설명문 및 참여 안내` | **A 표지 상자** | 제목 셀: `건설현장 불시·단발성 작업 위험성평가` / `AI 자동생성 시스템 개발 및 효과성 분석`(cp41) + `: LLM-RAG 기법을 활용하여`(cp62). 안내문 셀: 이 절의 p 문단들(굵게 run은 cp9)을 "안녕하십니까." 부터 `참여에는 약 65분이 소요되며…` 문단까지, 마지막에 연월 문단 `2026년  월`(cp64). 표 뒤 pp30 4줄(§3에서 MD에 추가). 이후 진행 순서 표(순서/내용/소요)와 나머지 문단은 기존 일반 표·문단 그대로 |
| `2. 사전 설문` | **B 인구통계 상자** | 중첩 제목 표 텍스트 `2. 사전 설문 (참여자 일반 사항)`. 안내 문단("다음은 참여자의 일반 사항에 …")은 상자 안 첫 문단(pp52 cp36). 굵게 문항 `**1. 귀하의 성별은 무엇입니까?**` → 번호 run cp9 ` 1)` + 질문 run cp36; 선택지 문단 `① 남성　② 여성` → cp36 pp52, 앞에 공백 3칸. 절 끝의 guide 인용구(`> 문항 1·3·4·7·8은 …`)는 상자 **밖**에 guide 빨강 문단으로 |
| `4. 조건별 인식 설문` J/K/L/M 표 4개 | **C 리커트 격자** | 표 판정: header가 `번호 | 진술문 | ① | ② | ③ | ④ | ⑤`. 변수명 셀 = 직전 굵게 문단의 굵게 부분(`J. 사고예방 효과`); 그 문단의 나머지(괄호 설명·CITE_TODO)는 표 앞 일반 문단으로 남긴다. 척도 라벨 5종은 양식 그대로. 문항 행 번호 `J1`, 진술문 그대로, ①~⑤ 셀 텍스트 ①②③④⑤. 절 도입의 안내 문단·`(① 전혀 그렇지 않다　… ⑤ 매우 그렇다)` 문단은 pp46 일반 문단 그대로(양식의 ※ 문단은 만들지 않는다 — 원고 문장을 쓴다) |
| `7.2 평정 양식` 표 | **C 변형(13열)** | header `번호 | 평정 항목 | 설명 | ①~⑤`. 진술문 열(20769)을 `평정 항목 5500` + `설명 15269`로 나눈 13열 격자(변수명 셀 colSpan 3, cellAddr/colSpan 전부 재계산, 열폭 합 = 39491). 변수명 셀 텍스트 `평가서 품질 평정`, 척도 라벨 `매우미흡` `` `보통` `` `매우우수`. 평정 항목 셀은 cp16(bold 계열이 없으면 CELL_BOLD_CHAR) |
| 그 밖의 표(진행 순서, 조건별 안내, 세션 기록지, 확인표) · 부록2 표 | 기존 일반 표 | 변경 없음 |
| `5. 개방형 의견` 끝 "설문에 응답하여 주셔서 진심으로 감사드립니다." | 끝맺음 | pp46 문단(기존 본문 서식으로 충분하면 그대로) |

## 3. MD 추가(허용된 유일한 원고 수정)
`01.docs/07.부록.md`의 `## 1. 연구 설명문 및 참여 안내` 절에서 "참여에는 **약 65분**이 소요되며…" 문단 **앞**에 다음 4줄을 넣는다(연구자·이메일은 확정 필요 마커).
```
소속: 경기대학교 공학대학원 건축·안전공학전공
지도교수: 박 종 용
연구자: 김 미 소
이메일: [확정 필요: 연구자 이메일]
```
조립기는 표지 상자 모드에서 이 4줄을 pp30 문단(`소    속 : …` 형식으로 라벨 정렬)으로 렌더한다. 파서는 재실행한다(`md_to_blocks.py`, 커버리지 누락 0 유지).

## 4. 구현 방식 (`tools/hwpx_transfer/blocks_to_hwpx.py`)
- `Template`에 `_slice_survey_templates()` 추가: §1 앵커로 표지 상자 표 XML·Part A 상자 XML·리커트 표 XML·pp30 문단 XML을 문자열로 보관. 없으면 SystemExit.
- `Assembler`에 `survey_cover_box(title_lines, subtitle, paras, date_text)`, `survey_partA_box(title, items)`, `survey_likert(var_name, labels, rows, split_desc=None)` 추가. **클론 방식**: 양식 XML의 행/셀을 템플릿으로 삼아 텍스트만 바꾸고(`<hp:t>` 치환, run charPr 유지), 문항 행은 r3 XML을 복제해 `cellAddr rowAddr`·`rowCnt`·`sz height`·`cellSz height` 재계산. `hp:tbl id`·`hp:p id`는 `IdGen`으로 새로 발급. `linesegarray`는 제거하거나 1줄로 정리.
- 적용 규칙은 코드에 박지 말고 `staging/survey_layout.json`으로 뺀다: `{"cover_section": "1. 연구 설명문 및 참여 안내", "cover_title_lines": [...], "cover_subtitle": "...", "partA_sections": ["2. 사전 설문"], "likert_header": ["번호","진술문","①","②","③","④","⑤"], "likert_labels": [...], "rating": {"header": [...], "var_name": "...", "labels": [...], "split": [5500, 15269]}}`. `--survey-layout` 옵션으로 받고, 없으면 기존 동작.
- 격자 정합: 모든 행의 `cellSz.width` 합 = 표 폭, `colAddr`/`colSpan`이 12(또는 13)열 그리드와 일치. 안 맞으면 한글이 행을 재배치한다(과거 실제 사고). `tblplan.py`가 통과해야 한다.
- 빨간 마커 규칙(`marker_aware_runs`)과 guide 문단 규칙은 상자 안 문단에도 적용.

## 5. 검증 (전부 통과해야 완료)
1. 파서 재실행 exit 0, 누락 0.
2. 조립 `--smoke` exit 0 (명령은 `README.md` §현재 상태 + `--survey-layout staging/survey_layout.json`).
3. `validate.py` VALID · `extract_text.py --check-integrity` 0건 · `--verify-blocks` 누락 0(설문 상자 안 텍스트도 대조되는지 확인, 안 되면 누락 목록이 상자 텍스트뿐임을 보임).
4. `tblplan.py smoke.hwpx`: not-fits 0, 본문 CELL 0. 새 설문 표 5개(표지·PartA·J·K·L·M·평정 = 7개)의 열폭 합 검사 스크립트 출력.
5. 빨간 마커 검정 0(이관 가이드 §4-5 스니펫 + `[작성 가이드`).
6. `verify-hwpx.ps1` → Open=True, PDF. 한 번만.
7. `render-pdf.ps1`(powershell.exe 5.1)로 **부록1 전 쪽** PNG 렌더 → Read로 열어 표지 상자·Part A 상자·리커트 4표·평정표가 양식(윤혁 260912_1059 본의 부록 쪽)과 같은 모양인지 확인. 비교용으로 양식 원본도 `verify-hwpx.ps1`로 PDF를 만들어 부록 쪽 3~4장만 렌더해 나란히 본다(양식 COM 개방은 2.2MB라 30초 이상 걸릴 수 있음, 타임아웃 축소 금지).
8. 총 쪽수 기록.

## 6. 산출물
- `tools/hwpx_transfer/blocks_to_hwpx.py`(수정), `staging/survey_layout.json`, `01.docs/07.부록.md`(4줄 추가), 재생성된 `staging/*.blocks.json`·`parse_report.md`, `staging/test_out/smoke.hwpx`·`assembly_report.md`, 검증 기록 `staging/test_out/verify_report_w7.md`(PNG 경로·양식 대비 육안 결과·문제 목록), `analysis/assembler_changes.md`에 "설문 양식" 절 추가

## 7. 금지
- `00. hwpx/` 수정·복사 금지(최종 저장은 코디네이터). §3 외 원고 MD 수정 금지. git·hwpx MCP 금지. 다른 워커 산출물(qa/, references.json, style_map_miso.json) 수정 금지.
