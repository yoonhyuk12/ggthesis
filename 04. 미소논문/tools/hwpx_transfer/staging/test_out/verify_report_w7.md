# W7 — 부록 설문 양식 이식 + guide 문단 제외 검증 리포트

- 대상: `tools/hwpx_transfer/staging/test_out/smoke.hwpx` (2026-09-12 조립본)
- 조립 명령: README §현재 상태 + **`--survey-layout tools/hwpx_transfer/staging/survey_layout.json`**
- 결론: **9단계 전부 통과.** 한컴 `Open=True`, 총 **128쪽**, 설문 표 **8개**(표지 상자 1 · Part A 상자 2 ·
  리커트 4 · 평정 13열 1) 전부 양식대로 렌더, **guide 문단 119개 전량 제외(hwpx 잔존 0)**

## 0. 작업 중 내려온 결정 2건

### (가) Part A 상자 분할 (코디네이터 승인, A안)

미소 `2. 사전 설문`은 문항이 8개(안내문 1 + 문항 8 + 선택지 8 = 17문단·21줄)라 한 상자에 넣으면
상자 높이가 **59,746 > 본문 54,144 HWPUNIT** 으로 한 쪽을 넘는다(양식의 Part A 상자는 문항 7개 기준).
`pageBreak="NONE"` 상자는 한글이 쪼개지 않으므로 잘린다. 승인에 따라 **의미 단위로 두 상자에 나눴다** —
(1) 참여자 일반 사항: 안내문 + 문항 1~4(성별·연령·경력·직책), (2) 현장 및 사용 특성: 문항 5~8
(공종·규모·LLM 사용경험·작성 빈도). 두 상자 모두 중첩 제목 표를 두고 `pageBreak=NONE`을 유지했다.
분할 규칙은 코드가 아니라 `staging/survey_layout.json`의 `partA_boxes`에 **데이터로** 들어 있다.

### (나) guide 문단 hwpx 제외 (사용자 지시 15:40, 작업 중 수신)

"`[작성 가이드]` 인용구와 절·항 사이의 집필 안내 문단은 논문 hwpx에 넣지 마라."
블록 JSON의 `guide:true` 문단을 **렌더하지 않고 건너뛴다**. 빨간 문단 경로는 코드에 남겨 두고
`--keep-guide` 옵션으로만 켠다(기본 동작 = 제외). 제외 건수는 `assembly_report.md`에
`- guide 문단 제외: 119 (--keep-guide 로 살릴 수 있다)` 로 기록된다.

## 1~9단계 결과표

| # | 검증 | 명령 | 결과 | 수치 |
| --- | --- | --- | --- | --- |
| 1 | 파서 재실행 | `md_to_blocks.py` | **PASS** | exit 0, 9개 파일 전부 `missing=0`, total blocks 640 (apx1 144→**148**, §3의 4줄 반영) |
| 2 | 조립 | `blocks_to_hwpx.py … --survey-layout … --smoke` | **PASS** | exit 0, 본문 문단 **727**, 논문개요 5, 설문 틀 8개 적용, **guide 문단 제외 119** |
| 3a | 구조 검증 | `validate.py smoke.hwpx` | **PASS** | `VALID: All structural checks passed.` |
| 3b | 무결성 | `extract_text.py --check-integrity` | **PASS** | XML 8개 파싱 성공, 문제 **0건**, 텍스트 단위 1,890 |
| 3c | 블록 누락 대조 | `extract_text.py --verify-blocks` | **PASS(주석 1)** | 대조 1,675 · 순서 기준 누락 1,531 · **문서에 실제로 없음 134 = guide 118 + 설문 재구성 16** (유실 0) |
| 3d | guide 제외 확인 | `test_out/check_guide_absent.py` | **PASS** | **guide 문단 119개 · hwpx 안에 남은 것 0개** |
| 4a | 표 쪽맞춤 | `tblplan.py smoke.hwpx` | **PASS** | 최상위 표 51 · fits **51** · **not-fits 0** · 단독 한 쪽 초과 없음 |
| 4b | 본문 pageBreak | section2 스캔 | **PASS** | section2 `NONE 45 · CELL 0 · TABLE 0` (CELL 5는 전면부 양식 제목 상자 — 양식 원본과 동일) |
| 4c | 설문 표 격자 정합 | `test_out/check_survey_grid.py` | **PASS** | 설문 표 **8개 전부 OK** — 행별 `cellSz` 폭 합 = 표 폭, `colAddr/colSpan` 격자 구멍·중복 0 |
| 5 | 빨간 마커 | 아래 §4 스니펫 | **PASS** | 마커 출현 **342 · 빨강 342 · 검정 0** |
| 6 | 한컴 개방 | `verify-hwpx.ps1` | **PASS** | **Open=True**, exit 0, SHA256 UNCHANGED=True, PDF 1,423,200 bytes |
| 7 | PNG 육안 (부록1 전 쪽) | `render-pdf.ps1` 101–115쪽 15장 | **PASS** | §6 표 참조 — 양식(윤혁) 부록 쪽과 형태 일치 |
| 8 | 기존 동작 보존 | `--survey-layout` 없이 조립 | **PASS** | apx1 `--verify-blocks` **누락 0** (§7) |
| 9 | 분량 | PDF 쪽수 | **기록** | **총 128쪽** (직전 조립본 146쪽 → Part A 분할·설문 표 압축 −1, guide 119문단 제외 −17) |

## 2. 설문 양식 적용 표 (assembly_report.md)

| 틀 | 대상 | 규모 |
| --- | --- | --- |
| 표지 상자 | 1. 연구 설명문 및 참여 안내 | 안내문 5문단 · 라벨 4줄 |
| Part A 상자 | 2. 사전 설문 (1) 참여자 일반 사항 | 문항 4 · 선택지 4 |
| Part A 상자 | 2. 사전 설문 (2) 현장 및 사용 특성 | 문항 4 · 선택지 4 |
| 리커트 격자 | J. 사고예방 효과 | 문항 4 |
| 리커트 격자 | K. 위험인지 향상 | 문항 4 |
| 리커트 격자 | L. 안전행동 개선 | 문항 4 |
| 리커트 격자 | M. 관리효율성 향상 | 문항 4 |
| 리커트 격자(13열) | 평가서 품질 평정 | 문항 4 |

## 3. 블록 누락의 정체 (주석 1)

`extract_text.py --verify-blocks`는 **순서를 지키는 커서 방식**이라, (가) guide 문단을 통째로 빼고
(나) 설문 표의 MD 머리행(`번호 | 진술문 | ① … ⑤`)이 척도 라벨 행으로 바뀌면 커서가 어긋나
그 뒤가 전부 "누락"으로 찍힌다. 실제 유실 여부는 **문서 전체 텍스트에 존재하는지**로 따로 확인했다.

```
guide 문단 119개 · hwpx 안에 남은 것 0개
대조 1675 · 순서 기준 누락 1531 · 문서에 실제로 없음 134 (guide 118 · 설문 양식 재구성 16)
```

- **guide 118** — 지시대로 제외한 집필 안내 문단(나머지 1건은 `front.blocks.json`에 있어 이 대조
  대상에 안 들어간다. 합계 119는 파서 리포트와 일치)
- **설문 양식 재구성 16** — 브리프 §2가 지시한 변형이며 변형된 형태로 문서에 있다

| 유형 | 건수 | 변형 |
| --- | --- | --- |
| 라벨 4줄 | 4 | `소속: …` → `                      소    속 : …` (양식 pp30 라벨 정렬) |
| Part A 문항 8개 | 8 | `1. 귀하의 성별은…` → 번호 run ` 1)`(bold cp9) + 질문 run cp36 |
| J/K/L/M 변수명 문단 | 4 | 굵은 부분 `J. 사고예방 효과`는 표 변수명 셀로, 나머지 `(자체 개발 — …) [CITE_TODO …]`는 표 앞 문단으로 분리 |

## 4. 빨간 마커 상세

- 빨간 charPr id: `15, 32, 61, 67, 68, 69, 70, 71, 73, 74, 75` (신규 복제 **0건**)
- 마커 6종(`[DATA PENDING`, `[확정 필요`, `[CITE_TODO`, `[그림 삽입 예정`, `[UNVERIFIED`, `[작성 가이드`)
  출현 **342건 전부 빨간 run 안**, 검정 **0건**
  (직전 조립본 427건 → guide 문단 제외로 85건 줄었다. 남은 342건은 전부 본문 문단·표 셀 안의 마커다)
- 설문 틀 안쪽 문단에는 마커가 들어가지 않았고(0건), 표지 상자 **뒤** pp30 라벨의
  `[확정 필요: 연구자 이메일]`은 charPr 61(빨강)로 나간다 — PNG 102쪽에서 빨강 확인

## 5. 설문 표 격자 정합 (check_survey_grid.py)

```
OK   건설현장 불시·단발성 작업 위험성평가AI 자동생성    2x3  표폭=39232  열폭합=39232
OK   2. 사전 설문 (1) 참여자 일반 사항다음은 참여   1x1  표폭=38402  열폭합=38402
OK   2. 사전 설문 (2) 현장 및 사용 특성 5) 귀   1x1  표폭=38402  열폭합=38402
OK   J. 사고예방 효과전혀그렇지않다보통이다매우그렇다J1   7x12 표폭=39491  열폭합=39491
OK   K. 위험인지 향상전혀그렇지않다보통이다매우그렇다K1   7x12 표폭=39491  열폭합=39491
OK   L. 안전행동 개선전혀그렇지않다보통이다매우그렇다L1   7x12 표폭=39491  열폭합=39491
OK   M. 관리효율성 향상전혀그렇지않다보통이다매우그렇다M   7x12 표폭=39491  열폭합=39491
OK   평가서 품질 평정매우미흡보통매우우수Q1위험요인의 적   7x13 표폭=39491  열폭합=39491
설문 표 8개 — OK 8 / FAIL 0
```

행별 `cellSz.width` 합이 표 폭과 일치하고, `rowCnt×colCnt` 격자에 구멍·중복이 없다.
13열 평정 표는 진술문 열(20,769)을 `5,500 + 15,269`로 쪼갠 것이며 합이 원래 폭과 같다.

## 6. PNG 육안 대조 — 부록 1 전 쪽 (PDF 101~115, 15장)

렌더 경로: `<스크래치>/w7/png2/pdf-page1NN.png` · 양식 비교본 `<스크래치>/w7/tpng/pdf-page10N.png`
전체 경로 = `C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Documents-2026------03--------\2973c0be-d92f-4efc-9051-9db86797b20e\scratchpad\w7\`

| PDF 쪽 | 인쇄 쪽 | 내용 | 양식 대응 | 판정 |
| --- | --- | --- | --- | --- |
| 101 | 89 | 부록 1 제목 + 개요 문단 + h2 `1. 연구 설명문 및 참여 안내` | — | OK (주석 2) |
| **102** | 90 | **표지 상자** — 3열 제목행(좌우 빈 셀 + 가운데 제목 2줄 bold + 부제 1줄), 안내문 5문단(굵게 run 포함), 우측 `2026년  월`, 상자 뒤 pp30 라벨 4줄 | **t106** | **OK — 양식과 동일 형태.** 라벨 자간(`소    속 :` / `연 구 자 :` / `이 메 일 :`)까지 일치, 이메일 자리표시자 빨강 |
| 103 | 91 | 진행 순서 표 + 안내 문단 + 참여 동의 | — | OK, IRB 자리표시자 빨강 |
| **104** | 92 | **Part A 상자 (1)** — 바깥 테두리 + 진회색 중첩 제목 표 `2. 사전 설문 (1) 참여자 일반 사항` + 안내문 + 문항 1~4 | **t107** | **OK — 양식과 동일 형태**(테두리·제목 바·번호 bold·선택지 들여쓰기). 주석 3 |
| **105** | 93 | **Part A 상자 (2)** `2. 사전 설문 (2) 현장 및 사용 특성` + 문항 5~8, 이어서 h2 `3. 실험 시나리오`(guide 문단은 제외되어 사라짐) | **t107** | **OK** |
| 106 | 94 | 3.1 시나리오 A + 3.2 시나리오 B 시작 | — | OK, `[확정 필요: …]` 자리표시자 빨강 · §3 앞 guide 인용구는 제외됨 |
| 107 | 95 | 3.2 잔여 + 3.3 조건별 안내 표 | — | OK |
| **108** | 96 | h2 `4. 조건별 인식 설문` + 안내 문단 + J 설명 문단(CITE_TODO 빨강) + **리커트 격자 J** | **t108** | **OK — 양식과 동일**: 회색 변수명 셀(colSpan 2·rowSpan 3), 척도 라벨 5셀(전혀/그렇지/않다 … 매우/그렇다), 눈금 장식 2행, 문항 행 번호·진술문·①~⑤ |
| **109** | 97 | **리커트 격자 K·L** | t108 | **OK** |
| **110** | 98 | **리커트 격자 M** + h2 `5. 개방형 의견` + 끝인사 | t108 | **OK** |
| 111 | 99 | h2 `6. 세션 기록지` + 기본 사항/1차/2차 표 3개(기존 일반 표 유지) | — | OK |
| 112 | 100 | 설문 실시 확인 표 + 특이사항 + `7. 전문가 평정표` + 7.1 평정 지침 | — | OK |
| 113 | 101 | 7.1 잔여 + h3 `7.2 평정 양식` + 평정 대상/평정자/일자/척도 안내 | — | OK |
| **114** | 102 | **평정 격자(13열)** — 회색 변수명 셀 `평가서 품질 평정`(colSpan 3), 척도 라벨 `매우/미흡`·`보통`·`매우/우수`, 번호·평정 항목(bold cp16)·설명·①~⑤ + h2 `8. 현장 정보 시트` | t108 변형 | **OK — 진술문 열을 5,500+15,269로 쪼갠 13열 격자가 정렬대로 렌더됨** |
| 115 | 103 | 8. 현장 정보 시트 문항 3~6 (끝 guide 문단은 제외됨) | — | OK |

## 7. 기존 동작 보존 확인

`--survey-layout` 없이 같은 블록으로 조립한 결과(`<스크래치>/w7/nolayout.hwpx`, 검증 후 삭제):

```
## 설문 양식 적용 (--survey-layout)
- 적용하지 않음(--survey-layout 미지정) — 설문 표도 일반 표로 조립
apx1 대조 대상 텍스트: 303, 누락: 0
```

## 8. 한컴 COM

```
[출력 1차(설문 양식만)]  Open=True / SHA256 UNCHANGED=True / PDF 1,536,528 bytes / EXIT=0
[양식 비교용]            Open=True / SHA256 UNCHANGED=True / PDF 1,040,258 bytes / EXIT=0
[출력 2차(guide 제외 반영, 최종본)] Open=True / SHA256 UNCHANGED=True / PDF 1,423,200 bytes / EXIT=0
```

브리프는 "출력 1회 + 양식 비교용 1회"였으나, 작업 도중 guide 문단 제외 지시가 내려와 **내용이 바뀐
최종 산출물을 다시 열어 확인해야 했으므로 출력 개방을 한 번 더 했다**(총 3회, 타임아웃은 기본값 유지).
`RegisterModule=False`는 보안 모듈 등록 실패 경고이며, 그 뒤 `Open=True`와 PDF 저장이 모두 성공했으므로
판정에 영향이 없다(W5와 동일). 입력 hwpx는 세 번 모두 SHA256이 그대로였다(쓰기 없음 증명).

## 발견한 문제

| # | 심각도 | 내용 | 근거 | 제안 |
| --- | --- | --- | --- | --- |
| 1 | 낮음 | **Part A 선택지 긴 줄이 두 줄로 감기며 들여쓰기가 풀린다.** 예: 104쪽 문항 2의 `④ 50세 이상`이 다음 줄 왼쪽 끝에서 시작 | 104·105쪽 PNG | 양식의 pp52에는 내어쓰기가 없어 생기는 현상이고, 윤혁 양식은 긴 선택지를 MD에서 두 줄로 나눠 피했다. 고치려면 원고 MD에서 해당 선택지 줄을 둘로 쪼개야 하므로 **W7 범위(§3의 4줄 추가만) 밖으로 두고 보고만 한다** |
| 2 | 낮음 | **101쪽 아래 절반이 빈다.** h2 `1. 연구 설명문 및 참여 안내` 뒤 표지 상자(43,096 HWPUNIT)가 남은 공간에 안 들어가 102쪽으로 밀림 | 101·102쪽 PNG | 한글의 정상 동작(표 전체가 안 들어가면 다음 쪽). W5가 보고한 그림 1-1 밀림과 같은 유형 |
| 3 | 정보 | **`--verify-blocks` 누락 수는 도구의 순서 대조 한계**이며 실제 유실 0 | §3 | guide 제외와 설문 표를 쓰는 문서에서는 `check_guide_absent.py`(존재 확인 방식)를 함께 돌려야 판정할 수 있다 |
| 4 | 정보 | Part A 상자를 두 개로 나눈 것은 양식(한 Part = 한 상자)과 다른 점 | §0(가) | 코디네이터 승인 사항. 문항이 줄면 `survey_layout.partA_boxes`를 하나로 되돌리면 된다 |
| 5 | 정보 | guide 문단 제외로 **원고 MD와 hwpx의 내용이 의도적으로 달라졌다** | §0(나) | MD는 단일 원본 그대로 두고 hwpx만 걸러내는 설계다. 심사용으로 안내 문단을 다시 보려면 `--keep-guide`로 조립한다 |

## 재현 명령 모음

```bash
cd "04. 미소논문"
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/md_to_blocks.py
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/blocks_to_hwpx.py \
  --template "00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx" \
  --style-map tools/hwpx_transfer/staging/style_map_miso.json \
  --front tools/hwpx_transfer/staging/front.blocks.json \
  --cover tools/hwpx_transfer/staging/cover_miso.json \
  --survey-layout tools/hwpx_transfer/staging/survey_layout.json \
  --blocks tools/hwpx_transfer/staging/ch0{1,2,3,4,5,6}.blocks.json \
           tools/hwpx_transfer/staging/apx1.blocks.json tools/hwpx_transfer/staging/apx2.blocks.json \
  --references tools/hwpx_transfer/staging/references.json --smoke
# 집필 안내 문단까지 넣고 싶으면 위 명령에 --keep-guide 를 붙인다

PYTHONIOENCODING=utf-8 python ~/.claude/skills/hwpx/scripts/validate.py tools/hwpx_transfer/staging/test_out/smoke.hwpx
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/extract_text.py --input tools/hwpx_transfer/staging/test_out/smoke.hwpx --check-integrity
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/tblplan.py tools/hwpx_transfer/staging/test_out/smoke.hwpx
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/staging/test_out/check_survey_grid.py tools/hwpx_transfer/staging/test_out/smoke.hwpx
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/staging/test_out/check_guide_absent.py tools/hwpx_transfer/staging/test_out/smoke.hwpx

pwsh -NoProfile -File "../.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1" \
  -HwpxPath "<abs>/smoke.hwpx" -PdfPath "<scratch>/w7/smoke2.pdf"
# render-pdf.ps1 은 PdfPath/OutDir 에 **백슬래시 Windows 절대경로**를 줘야 한다
# (슬래시 경로를 주면 PageCount가 0으로 잡혀 "렌더할 페이지가 없음"으로 죽는다)
powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File "..\.claude\skills\hwpx-thesis-editing\scripts\render-pdf.ps1" \
  -PdfPath "<scratch>\w7\smoke2.pdf" -OutDir "<scratch>\w7\png2" -Pages "101-115" -Width 1100
```
