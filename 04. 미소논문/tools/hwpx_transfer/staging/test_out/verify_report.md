# W5 — 조립 결과 검증 리포트

- 대상: `tools/hwpx_transfer/staging/test_out/smoke.hwpx` (878,702 bytes, 2026-09-12 15:14 조립본)
- 검증 시각: 2026-09-12 (Asia/Seoul), 조립기 `tools/hwpx_transfer/blocks_to_hwpx.py`는 **읽기만 했고 수정하지 않았다**
- 결론: **7단계 전부 통과.** 조립을 다시 돌릴 사유 없음. 아래 "발견한 문제"는 전부 조판 미세 사항(심각도 낮음)이다

## 1~7단계 결과표

| # | 검증 | 명령 | 결과 | 수치 |
| --- | --- | --- | --- | --- |
| 1 | 구조 검증 | `python ~/.claude/skills/hwpx/scripts/validate.py … smoke.hwpx` | **PASS** | `VALID: All structural checks passed.` |
| 2 | 무결성 | `extract_text.py --input smoke.hwpx --check-integrity` | **PASS** | XML 8개 파싱 성공, 문제 **0건**, 추출 텍스트 단위 1,897 |
| 2b | 블록 누락 대조 | `extract_text.py --verify-blocks ch01…ch06 apx1 apx2` | **PASS** | 대조 대상 텍스트 1,671, 누락 **0** |
| 3 | 빨간 마커 | 아래 §3 스니펫 | **PASS** | 마커 빨강 702 / **검정 0**, 빨간 run 943개(33,349자), guide 문단 **119/119 전부 빨강** |
| 4 | 표 쪽맞춤 | `tblplan.py smoke.hwpx` | **PASS(주석 1)** | 최상위 표 48, fits 48 / **not-fits 0**, 단독 한 쪽 초과 표 없음, 본문(section2) `pageBreak="CELL"` **0** |
| 5 | 한컴 개방 | `verify-hwpx.ps1 -HwpxPath … -PdfPath …` | **PASS** | **Open=True**, exit 0, 크래시 없음, SHA256 UNCHANGED=True, PDF 1,531,357 bytes |
| 6 | PNG 육안 | `render-pdf.ps1`(powershell.exe 5.1) 13쪽 렌더 | **PASS** | 표지 3면·목차·표목차·그림목차·감사의 글·논문개요·그림 1-1·표 2-1·참고문헌·부록 모두 정상 |
| 7 | 분량 기록 | PDF 쪽수 + 섹션별 문단 수 | **기록 완료** | **총 146쪽**, 본문 최상위 문단 866 |

## 3. 빨간 마커 상세

검사 스니펫은 이관 가이드 §4-5의 것을 쓰되 마커 목록에 `[작성 가이드`를 추가하고, run 텍스트는 `run.iter()`가 아니라 **직접 자식 `<hp:t>`만** 모아 표 셀 중복 계수를 피했다.

- 빨간 charPr id: `15, 32, 61, 67, 68, 69, 70, 71, 73, 74, 75` (header.xml에서 `textColor="#FF0000"`로 역추출)
- 마커 6종(`[DATA PENDING`, `[확정 필요`, `[CITE_TODO`, `[그림 삽입 예정`, `[UNVERIFIED`, `[작성 가이드`) 출현 **702건 전부 빨간 run 안**, 검정 **0건**
- guide 문단(블록 JSON의 `guide:true`) **119개**를 블록 텍스트로 hwpx에서 역조회 → 못 찾은 문단 0, 일부만 빨간 문단 0. **119/119 문단 전체 빨강** (파서 리포트 119개와 일치. 이 중 `[작성 가이드`로 시작하는 문단은 46개이고 나머지 73개는 인용구 연속 줄이라 마커 없이도 문단 전체가 빨갛다)
- **본문 대괄호 검정 유지 확인** — 검정 대괄호 총 61건, 유니크 32종이며 전부 실제 본문이다:
  `[01]`~`[31]`(참고문헌 번호, 55건), `[54]`(본문 내 참조번호 1건). 참조번호·신뢰구간·양식 라벨이 빨갛게 물든 사례 **없음**
- 육안 표본(PNG): 참고문헌 첫 쪽에서 `[03]`은 검정, 같은 줄의 `[UNVERIFIED — 학과·페이지수 미확인…]`은 빨강으로 분리돼 보인다(p110 PNG)

## 4. 표 쪽맞춤 상세

- 최상위 표 48개 / 중첩 표 0개, **fits 48 · not-fits 0**, 단독으로 한 쪽을 넘는 표 없음
- `pageBreak` 분포: **NONE 43 · CELL 5**
- **CELL 5개는 전부 section1(전면부)의 양식 제목 상자**(1x1 3개, 2x1 1개, 1x1 1개 — 목차/표목차/그림목차/감사의 글/논문개요 제목 상자)이며, 양식 원본 `00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx`의 section1도 CELL 5로 **동일**하다. 조립기가 만든 표가 아니라 양식 바이트를 그대로 옮긴 것이고, 모두 `fits=예`(높이 282~5,951 HWPUNIT vs 쪽 36,284)라 쪽 넘김 위험이 없다. 이관 가이드 §4-6도 "전면부 제목 상자는 그대로 둔다"고 지시한다
- 본문 section2는 **CELL 0 · NONE 40**으로 회귀 없음

## 5. 한컴 COM 개방 (1회만 실행)

```
한글: C:\Program Files (x86)\Hnc\Office 2022\HOffice120\Bin\Hwp.exe
SHA256(before)=SHA256(after)=25B94101…56BE  → UNCHANGED: True
RegisterModule=False  (WARN: FilePathCheckDLL 등록 실패)
Open=True
PDF OK: <스크래치>/w5/smoke.pdf (1,531,357 bytes)
RESULT: OK / EXIT=0
```

`RegisterModule=False` 경고는 이번 실행에서 보안 모듈 등록에 실패했다는 뜻이지만, 그 뒤 `Open=True`와 PDF 저장이 모두 성공했으므로 판정에는 영향이 없다. 입력 hwpx는 SHA256이 그대로였다(쓰기 없음 증명).

## 6. PNG 육안 확인

렌더 경로: `<스크래치>/w5/png/pdf-pageNNN.png` (Width 1100)
전체 경로 = `C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Documents-2026------03--------\b56ccd20-ebe9-4797-a370-36c89891da7d\scratchpad\w5\png\`

| PDF 쪽 | PNG | 확인 내용 | 판정 |
| --- | --- | --- | --- |
| 1 | pdf-page001.png | 표지 — 제목 3줄("건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여"), 지도교수 박 종 용, **김 미 소** | OK |
| 2 | pdf-page002.png | 제출면 — 제목·`2026년  월  일`·김 미 소 | OK |
| 3 | pdf-page003.png | 인준면 — "**김 미 소**의 석사학위논문을 인준함", 심사위원 3란, `2026년  월  일` | OK |
| 4 | pdf-page004.png | 목차 첫 쪽 — 장·절·항 3단 들여쓰기 정상 (쪽번호 열은 설계상 없음) | OK |
| 8 | pdf-page008.png | 표목차 — `<표 1-1>`~`<표 5-14>` **22항목** (assembly_report의 22와 일치) | OK |
| 9 | pdf-page009.png | 그림목차 — `<그림 1-1>`~`<그림 4-1>` **6항목** | OK |
| 10 | pdf-page010.png | 감사의 글 — 자리표시자 `[확정 필요: 감사의 글 작성]`이 **빨강**, 아래 `2026 년  월 / 김 미 소`는 검정 | OK |
| 11 | pdf-page011.png | 논문개요 — 첫 문단 `[작성 가이드]…` **문단 전체 빨강**, 이어지는 "연구 배경./연구 방법." 본문은 검정·볼드 정상 | OK |
| 13 | pdf-page013.png | 제1장 시작 — 장/절/항 제목 서식 구분됨, guide 문단 전체 빨강, 본문 검정 | OK |
| 14 | pdf-page014.png | **그림 1-1 실제로 보임**(막대그래프 1.59/0.78, 약 2.04배). 폭이 본문 폭 안(LINE_W의 90%), 캡션 `<그림 1-1> …`이 그림 아래 중앙 | OK |
| 28 | pdf-page028.png | **표 2-1** — 캡션이 표 위, 머리행(종류/근거 조문/실시 시기/주요 내용) 테두리 정상, 4행 전부 한 쪽 안, 셀 줄바꿈 정상 | OK(주석 2) |
| 110 | pdf-page110.png | 참고문헌 첫 쪽 — "참고문헌" 제목, "가. 학위논문" 분류, `[01]`~`[10]` 번호 검정·행간 hanging indent 적용, `[UNVERIFIED …]`만 빨강 | OK |
| 117 | pdf-page117.png | 부록 1 첫 쪽 — "부록 1. 실험 도구" 제목, 소절 "1. 연구 설명문 및 참여 안내", 볼드 강조 정상 | OK |

## 7. 분량 기록

- **PDF 총 쪽수: 146쪽** (전면부 로마자 i~xii + 본문 아라비아 1~ 기준)
- 주요 위치(PDF 쪽): 표지 1~3 · 목차 4~7 · 표목차 8 · 그림목차 9 · 감사의 글 10 · 논문개요 11~12 · 제1장 13 · 제2장 25 · 제3장 44 · 제4장 61 · 제5장 78 · 제6장 103 · 참고문헌 110 · 부록1 117 · 부록2 134
- 섹션별 문단 수(최상위 문단 / 표 셀 포함 전체 / 표 / 그림)

| 섹션 | 최상위 문단 | 전체 문단 | 표 | 그림 |
| --- | --- | --- | --- | --- |
| section0 (표지) | 3 | 53 | 3 | 0 |
| section1 (전면부) | 143 | 149 | 5 | 0 |
| section2 (본문) | **866** | 2,102 | 40 | 6 |
| 합계 | 1,012 | 2,304 | 48 | 6 |

- ZIP 엔트리 19개, `BinData/image1.png`~`image6.png` 6개 삽입 확인(content.hpf manifest 등록 포함)

## 발견한 문제 (전부 심각도 낮음 — 조립 재실행 불요)

| # | 심각도 | 내용 | 재현 | 원인 추정 / 제안 |
| --- | --- | --- | --- | --- |
| 1 | 낮음 | **표 2-1 자료 주석이 쪽을 넘어간다.** 28쪽 맨 아래 `*자료: 「사업장 위험성평가에 관한 지침」(고용노동부고시 제2024-76호) 제` 에서 잘려 29쪽 첫 줄이 `15조를 재구성.`으로 시작 | `pdftotext smoke.pdf` 28·29쪽 / pdf-page028.png | 표 바로 아래 자료 주석 문단이 표와 묶여 있지 않다. 표 자체는 fits이지만 주석 한 줄이 남는 높이가 없어 밀림. `tblplan.py`는 선언 행높이만 보므로 잡지 못하는 유형이다. 조립기 구조 수정(주석 문단을 표와 keep-with-previous 처리)이 필요하므로 **W5 범위 밖으로 두고 보고만 한다** |
| 2 | 낮음 | **본문 첫 쪽(PDF 13쪽)에 쪽번호가 찍히지 않는다.** 14쪽은 `- 2 -`로 정상 | pdf-page013.png vs pdf-page014.png | 양식 section2 첫 문단의 `secPr`/`pageNum` 제어 블록을 바이트 그대로 이식하는 설계(docstring 참조)의 결과로, 양식의 "구역 첫 쪽 쪽번호 감춤"이 그대로 따라온 것으로 보인다. 양식 원본의 동작이므로 조립기 결함이 아니다 |
| 3 | 정보 | 목차·표목차·그림목차에 **쪽번호 열이 없다**(브리프에도 명시됨) | pdf-page004/008/009.png | 설계상 미구현. 최종본 제출 전 채워야 할 항목으로 남는다 |
| 4 | 정보 | 그림 1-1이 13쪽 본문 뒤가 아니라 14쪽 머리로 밀려 13쪽 하단에 여백이 남는다 | pdf-page013/014.png | 그림 높이가 남은 공간보다 커서 한글이 다음 쪽으로 민 정상 동작 |
| 5 | 정보 | `references.json`의 flagged 33건은 본문에 넣지 않았다(assembly_report 메모) | — | 지시대로이며 검증 대상 아님 |

## 수정 사항

**없음.** `blocks_to_hwpx.py`를 포함해 어떤 파일도 수정하지 않았다(허용된 한두 줄 수정도 불필요). 산출물은 `verify_report.md`와 `analysis/assembler_changes.md` 두 개뿐이다.

## 재현 명령 모음

```bash
cd "04. 미소논문"
PYTHONIOENCODING=utf-8 python ~/.claude/skills/hwpx/scripts/validate.py tools/hwpx_transfer/staging/test_out/smoke.hwpx
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/extract_text.py --input tools/hwpx_transfer/staging/test_out/smoke.hwpx --check-integrity
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/extract_text.py --input tools/hwpx_transfer/staging/test_out/smoke.hwpx \
  --verify-blocks tools/hwpx_transfer/staging/ch0{1,2,3,4,5,6}.blocks.json tools/hwpx_transfer/staging/apx1.blocks.json tools/hwpx_transfer/staging/apx2.blocks.json
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/tblplan.py tools/hwpx_transfer/staging/test_out/smoke.hwpx
pwsh -NoProfile -File "../.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1" -HwpxPath "<abs>/smoke.hwpx" -PdfPath "<scratch>/smoke.pdf"
powershell.exe -NoProfile -File "../.claude/skills/hwpx-thesis-editing/scripts/render-pdf.ps1" -PdfPath "<scratch>/smoke.pdf" -OutDir "<scratch>/png" -Pages "1,2,3,4,8,9,10,11,13,14,28,110,117" -Width 1100
```
