# W5 — 조립 결과 검증 (Wave 2)

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다. 조립기 개조(W4)는 끝났고 터미널이 운영자에 의해 닫혀 검증 단계만 남았다. **이 작업은 검증과 사소한 마무리만 한다.** 조립기에 구조적 결함이 있으면 고치지 말고 원인·재현 명령을 보고한다(한두 줄 수정은 허용).

## 입력
- 조립 명령(저장소 `04. 미소논문/` 에서 실행):
```
PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/blocks_to_hwpx.py --template "00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx" --style-map tools/hwpx_transfer/staging/style_map_miso.json --front tools/hwpx_transfer/staging/front.blocks.json --cover tools/hwpx_transfer/staging/cover_miso.json --blocks tools/hwpx_transfer/staging/ch01.blocks.json … ch06 apx1 apx2 --references tools/hwpx_transfer/staging/references.json --smoke
```
  → `tools/hwpx_transfer/staging/test_out/smoke.hwpx` + `assembly_report.md`. 코디네이터가 방금 한 번 돌려 놓았다(블록은 W6 정규화·W1b guide 반영 후 재생성한 최신본).
- 검증 도구: 상위 저장소 `../.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1`, `render-pdf.ps1`(Windows PowerShell 5.1 `powershell.exe`로만), `~/.claude/skills/hwpx/scripts/validate.py`, `tools/hwpx_transfer/extract_text.py`, `tools/hwpx_transfer/tblplan.py`, 빨간 마커 검사 스니펫(`../03.plan/260912_0837_hwpx노하우_동기이관_가이드.md` §4-5 — 마커 목록에 `[작성 가이드` 추가하고, **guide 문단은 마커가 아니라 문단 전체가 빨강**이므로 별도로 guide 문단 수(파서 리포트 119개 기준)와 빨간 run 수를 대조).

## 검증 순서 (전부 통과해야 완료)
1. `validate.py smoke.hwpx` → VALID
2. `extract_text.py --input smoke.hwpx --check-integrity` → 문제 0건; `--verify-blocks`(있으면) 로 블록 누락 0건. 누락이 있으면 블록 타입·텍스트 앞 40자 목록.
3. 빨간 마커 검사 → 마커 검정 0; 빨간 run 총수 기록. 대괄호 본문(참조번호 `[54]`, `![그림` alt 등)이 빨갛지 않은지 표본 5개 확인.
4. `tblplan.py smoke.hwpx` → `pageBreak="CELL"` 0, not-fits 표 목록(있으면 표 캡션·행 수 보고).
5. **한컴 개방**: `pwsh ../.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1 -HwpxPath "<smoke.hwpx 절대경로>" -PdfPath "<스크래치>/smoke.pdf"` → `Open=True`, 크래시 없음, PDF 생성. 콜드 스타트가 12초를 넘길 수 있으니 스크립트 기본 타임아웃(300초)을 줄이지 마라. 다른 무거운 작업과 겹치지 않게 한 번만. 실패하면 원인(linesegarray textpos 초과, `<hp:pic>` 자식 누락, charPr id 부재 등)을 XML에서 특정해 보고.
6. **PNG 육안**: `powershell.exe -NoProfile -File ../.claude/skills/hwpx-thesis-editing/scripts/render-pdf.ps1 -PdfPath smoke.pdf -OutDir <스크래치>/png -Pages "1-6"` 로 표지 3면·목차 첫 쪽·표목차·그림목차를, 그리고 그림 1-1이 있는 쪽(제1장 시작 부근)·<표 2-1>이 있는 쪽·참고문헌 첫 쪽·부록 첫 쪽을 렌더해 Read로 열어 확인: 표지 치환(제목·김 미 소·날짜), 그림이 실제로 보이는지·폭이 본문 폭 안인지, 표 머리행·테두리, 빨간 글자가 마커·guide 문단에만 있는지, 감사의 글 자리표시자, 논문개요 본문. 쪽 번호는 PDF 쪽수로 찾는다(목차에 쪽번호가 없으니 본문에서 `pdftotext` 대신 PNG 몇 장을 훑어 찾아도 된다).
7. 총 쪽수(PDF)와 section별 문단 수를 기록.

## 산출물
- `tools/hwpx_transfer/staging/test_out/verify_report.md` — 항목 1~7 결과 표(통과/실패·수치·PNG 경로), 발견한 문제 목록(심각도·재현·원인 추정), 수정했다면 diff 요약
- `tools/hwpx_transfer/analysis/assembler_changes.md` — W4가 남기지 못한 변경 요약: `blocks_to_hwpx.py`의 새 옵션(--front/--cover)·새 블록(figure_image·guide)·외부화된 상수 키·전면부 앵커 방식·표지 치환 방식을 소스를 읽고 10~20줄로 정리

## 금지
- `00. hwpx/` 수정·복사 금지(최종 산출물 저장은 코디네이터가 한다). 원고 MD 수정 금지. git·hwpx MCP 금지.
