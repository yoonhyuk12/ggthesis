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

`package_get_xml`·`validate_structure` 등 package 계열은 `HWPX_MCP_ADVANCED=1`일 때만 활성화되며 **현재 설정에는 없다.** 내부 XML이 필요하면 아래 unzip 방법을 쓴다.

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
