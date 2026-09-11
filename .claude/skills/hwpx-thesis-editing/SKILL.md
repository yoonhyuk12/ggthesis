---
name: hwpx-thesis-editing
description: Use when 논문 hwpx를 수정하거나 검증할 때 — MD 원고 내용을 학회논문·본논문 hwpx에 반영, 표·행 높이·여백 조정, 수정한 hwpx가 한글에서 열리는지와 레이아웃이 안 깨졌는지 확인, hwpx 내부 XML(cellSz·colSpan·secPr) 확인, 표가 다음 쪽으로 밀리거나 행이 재배치될 때.
---

# 논문 hwpx 부분 수정과 검증

## 핵심 원칙

**hwpx는 MD를 따라가는 사본이고, 작업은 생성이 아니라 부분 치환이다.** 사용자가 한글에서 직접 고친 내용이 hwpx에 들어 있으므로, MD 기준으로 다시 만들어 덮어쓰면 그 수정이 사라진다.

## 절대 규칙

1. **MD 먼저, hwpx 나중.** MD가 단일 원본이다.
2. **쓰기 전에 반드시 현재 hwpx 텍스트를 읽는다.** `find_text`·`get_paragraph_text`로 실제 상태를 확인한 뒤 타깃 치환만 한다.
3. **통째 재생성·덮어쓰기 금지.** hwpx에만 있고 MD에 없는 내용을 발견하면 삭제하지 말고, 그 내용을 MD로 역동기화한다.
4. **hwpx 쓰기는 메인 컨텍스트가 단독·순차로 한다.** 서브에이전트에 위임 금지, 같은 파일 병렬 쓰기 금지.

**이 스킬을 쓰지 않는 경우.** 백지에서 새 hwpx를 조립·생성하는 작업은 이 스킬의 대상이 아니다.

## MCP 도구 (이 저장소 `.mcp.json` 기준)

**쓰기 도구는 호출 즉시 대상 파일에 저장된다. 미리보기 단계가 없다.** `HWPX_MCP_AUTOBACKUP=1`이 켜져 있어 자동 백업은 남지만, 백업에 기대지 말고 위험한 작업은 `copy_document`로 사본을 만들어 먼저 시도한다.

| 용도 | 도구 |
|---|---|
| 읽기·탐색 | `find_text`, `get_paragraph_text`, `get_paragraphs_text`, `get_document_text`, `get_table_map`, `find_cell_by_label` |
| 텍스트 치환 | `search_and_replace`, `batch_replace` |
| 표 편집 | `set_table_cell_text`, `fill_by_path`, `merge_table_cells`, `format_table` |
| 사본 분리 | `copy_document` |

**경로는 저장소 상대경로로 넘긴다.** 서버가 저장소 루트로 샌드박스돼 있어 임시 폴더·스크래치패드 경로는 `path is outside sandbox root`로 거부된다.

`package_get_xml`·`validate_structure` 등 package 계열은 `HWPX_MCP_ADVANCED=1`일 때만 활성화되며 **현재 설정에는 없다.** 내부 XML이 필요하면 아래 unzip 방법을 쓴다.

**폴백.** MCP가 `open-safety verification: package validation failed`로 열기를 거부하면(과거 v2.18.1에서 전 파일 발생) Python `zipfile`로 `Contents/section0.xml`을 직접 치환한다. 이때 백업 생성·항목 순서·압축 방식을 유지하고, 표 셀 텍스트는 여러 문단/run으로 쪼개져 있을 수 있으니 전역 문자열 치환 전에 원문 XML 문맥을 확인한다.

## 기존 hwpx의 부분(타깃) 치환 — 표준 경로

문단 몇 개를 고치는 일상 작업의 표준 경로다. **전체 재조립은 사용자가 한글에서 직접 고친 내용을 지우므로 쓰지 않는다.** 도구는 전역 스킬의 `~/.claude/skills/hwpx/scripts/fill_hwpx.py replace`이며, 바뀐 ZIP 엔트리만 재작성하고 바뀐 문단의 줄배치 캐시(`<hp:linesegarray>`)만 제거한다.

### 0단계 — 최신본 복사 (원본 불변)

```bash
# 00. hwpx/ 에서 YYMMDD_HHMM 접두사가 가장 큰 파일이 최신본
cp "00. hwpx/<최신본>.hwpx" <스크래치>/base.hwpx
```

`00. hwpx/`의 파일은 **제자리 수정하지 않는다.** 작업은 복사본에서 하고, 검증을 다 통과한 결과만 `00. hwpx/YYMMDD_HHMM_논문명.hwpx`(Asia/Seoul)로 저장한다.

### 1단계 — 대상 문구를 현재 hwpx에서 읽어 확정

MD가 아니라 **hwpx의 현재 텍스트**에서 키를 딴다(사용자 직접 수정분이 있을 수 있다). **본문이 2.5MB라 hwpx MCP 읽기 도구는 쓰지 않는다** — 응답 없이 40분 넘게 멈춘다. Python `zipfile`이나 아래 덤프를 쓴다.

```bash
python ~/.claude/skills/hwpx/scripts/map_preflight.py dump base.hwpx > paras.txt
```

키는 **문서 전체에서 유일**해야 한다. 유일성은 "문단이 직접 소유한 텍스트" 기준으로 센다 — 표를 감싼 바깥 문단이 셀 텍스트까지 끌어안아 멀쩡한 구절이 "2회"로 보인다.

### 2단계 — 치환 맵 작성

```json
{
  "제3장 제2절에서 서술한 탐지 파이프라인은": "제3장 제2절에서 서술한 탐지 파이프라인은(수정)",
  "표 4-4 최종 문항 구성": "표 4-4 최종 설문 문항 구성"
}
```

- 🔴 **빨간 마커(`[DATA PENDING`·`[확정 필요`·`[CITE_TODO`·`[그림 삽입 예정`·`[UNVERIFIED`)를 가로지르는 키를 쓰지 마라.** 마커 안쪽만, 또는 마커 바깥쪽만 잡는다. 가로지르면 치환기가 매칭 범위 전체를 첫 run에 몰아넣어 **오류 없이** 마커 앞부분을 검정으로 바꾼다.
- 같은 이유로 **글자모양이 섞인 구간(굵게·밑줄·각주 참조 등)을 통째로 잡지 마라.** 앞쪽 글자모양이 뒤쪽을 흡수한다.
- 한 키가 다른 키의 부분 문자열이어도 된다(긴 키부터 매칭한다).

### 3단계 — 사전검증 (필수)

```bash
python ~/.claude/skills/hwpx/scripts/map_preflight.py check base.hwpx --map map.json
# => "전부 매칭. replace 안전." 이 나와야 진행
```

### 4단계 — 치환

```bash
PYTHONIOENCODING=utf-8 python ~/.claude/skills/hwpx/scripts/fill_hwpx.py \
    replace base.hwpx out.hwpx --map map.json
echo $?    # 0 이어야 한다
```

**exit code가 0이 아니면 `out.hwpx`를 즉시 버린다.** 키 일부만 못 찾아도 exit 2가 나오는데, 그때도 파일은 **찾은 키만 적용된 반쪽짜리로 생성된다.** `--allow-unmatched`는 못 찾은 키를 알면서 넘길 때만 쓴다. (Windows 콘솔 cp949에서 진행 출력의 줄표 때문에 죽으므로 `PYTHONIOENCODING=utf-8`을 반드시 붙인다.)

### 5단계 — 검증 (순서대로, 전부 통과해야 완료)

| # | 검증 | 통과 기준 |
|---|---|---|
| 1 | ZIP 엔트리 목록·순서·압축 방식 | base와 동일 |
| 2 | 엔트리 SHA256 | 바꾼 섹션 외 전부 동일 |
| 3 | 문단 개수 | base와 동일 |
| 4 | 달라진 문단 수 | **의도한 개수와 정확히 일치** (초과분 = 오치환) |
| 5 | 달라진 문단의 `<hp:linesegarray>` | 제거됐거나 `textpos` 최댓값 ≤ 새 텍스트 길이 |
| 6 | 전체 `<hp:run>`·`<hp:t>` 개수 | base와 동일 |
| 7 | 빨간 charPr별 run 개수 | base와 동일 |
| 8 | **마커 접두사의 빨간 run 소속 횟수** | base와 동일 |
| 9 | `fill_hwpx.py check out.hwpx --strict` | `ok: true`, exit 0 |
| 10 | `~/.claude/skills/hwpx/scripts/validate.py out.hwpx` | `VALID` |
| 11 | `tools/hwpx_transfer/extract_text.py --input out.hwpx --check-integrity` | 문제 0건 |
| 12 | **한컴이 실제로 여는가** | 크래시 없음, 쪽수가 base와 동일 |

1~8은 저장소 스크립트 하나로 돌린다.

```bash
python tools/hwpx_transfer/verify_replace.py base.hwpx out.hwpx <기대 변경 문단 수>
# PASS = exit 0, FAIL = exit 1
```

12는 아래 "검증 루프"의 `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1`로 한다. **ZIP·XML 검증만 통과한 파일이 한글에서 `Open=False`였던 사고가 실제로 있었다(2026-09-11). 한글이 열어야 완료다.** 남의 Hwp 프로세스는 죽이지 않는다.

**검증 8이 이 절차의 핵심이다.** 치환 키가 run 경계를 가로지르면 빨간 마커 앞부분이 검정으로 바뀌는데, run 개수·`<hp:t>` 개수·빨간 run 개수가 전부 그대로라 1~7로는 잡히지 않고 `fill_hwpx.py`는 exit 0, `check --strict`와 `validate.py`도 통과한다. 8이 FAIL이면 키를 마커 한쪽으로 좁혀 다시 치환한다.

### 6단계 — 산출

검증 전부 통과 후에만 `00. hwpx/YYMMDD_HHMM_논문명.hwpx`로 복사한다. 그 전에 MD(`01.docs/`)가 먼저 수정돼 있어야 한다.

## 검증 루프 (필수 — 이거 없이 "완료" 금지)

한컴오피스 2020 경로. `C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Bin\Hwp.exe`

```powershell
# 1) 크래시 게이트 + PDF 변환
.\.claude\skills\hwpx-thesis-editing\scripts\verify-hwpx.ps1 `
    -HwpxPath "학회논문\학회2_....hwpx" -PdfPath "$env:TEMP\check.pdf"

# 2) 바뀐 쪽만 PNG로 렌더해 육안 확인 (Windows PowerShell 5.1로 실행)
powershell.exe -NoProfile -File .\.claude\skills\hwpx-thesis-editing\scripts\render-pdf.ps1 `
    -PdfPath "$env:TEMP\check.pdf" -OutDir "$env:TEMP\png" -Pages "3-5"
```

`-Pages`는 `all`, `5`, `2-7`, `1,4,9-11` 형식을 받는다. 렌더한 PNG를 Read로 직접 열어 표 정렬·줄바꿈·쪽 넘김을 눈으로 확인한다.

**콜드 스타트 오탐 주의.** 한글은 세션 첫 실행이 12초를 넘겨 뜬다. 고정 대기 후 `Get-Process Hwp`로 판정하면 **멀쩡한 파일이 CRASHED로 나온다**(실측 확인). `verify-hwpx.ps1`은 워밍업 후 폴링하는 방식이라 이 오탐이 없으므로, 크래시 판정은 직접 명령을 짜지 말고 이 스크립트를 쓴다.

## 표·치수 함정

- **셀 명시 폭이 열 그리드(`colAddr`/`colSpan`)와 어긋나면 한글이 행을 재배치해 행 전체가 깨진다.** 셀 폭은 반드시 그리드 열폭 합산으로 도출한다.
- **행 높이 선언값은 최소값이다.** 내용이 길면 자라고, 넘치면 표 전체가 다음 쪽으로 밀린다. 늘릴 때는 소폭씩 한다.
- 치수 단위는 HWPUNIT. 1mm = 283.465, 1pt = 100. A4 세로 = 59528 × 84188. 줄 전진 높이 ≈ 글자크기 × 130%(10pt → 1300), 셀 상하 패딩 282.

## 정답 XML 확보

레이아웃이 미세하게 어긋날 때 스크린샷으로 픽셀을 추정하지 마라. **사용자가 한글에서 직접 고친 파일이 최고의 스펙이다.** 그 파일을 풀어 실제 값을 이식한다.

```powershell
Copy-Item "대상.hwpx" "$env:TEMP\doc.zip" -Force
Expand-Archive "$env:TEMP\doc.zip" -DestinationPath "$env:TEMP\doc" -Force
# Contents/section0.xml 에서 cellSz·colSpan·colAddr·secPr 확인
```

## 흔한 실수

| 실수 | 결과 | 대신 |
|---|---|---|
| MD 기준으로 hwpx 재생성 | 사용자 직접 수정분 소실 | 타깃 치환만 |
| 현재 텍스트 안 읽고 치환 | 매칭 실패 또는 엉뚱한 곳 치환 | `find_text` 먼저 |
| 고정 12초 대기로 크래시 판정 | 정상 파일을 CRASHED로 오탐 | `verify-hwpx.ps1` |
| `render-pdf.ps1`을 pwsh로 실행 | WinRT 타입 로드 실패 | `powershell.exe`(5.1) |
| 표 셀 폭만 바꿈 | 행 전체 깨짐 | 그리드 열폭과 함께 정합 |
