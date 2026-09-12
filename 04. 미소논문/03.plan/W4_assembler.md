# W4 — 조립기 개조 (blocks_to_hwpx.py → 미소 논문 · 260912 양식)

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다. 메인 계획서의 계약: `../03.plan/260912_1422_미소논문_hwpx작성_오케스트레이션.md` §"style_map_miso.json 계약"·§"표지·전면부 치환값"(읽기만).

## 목표
`04. 미소논문/tools/hwpx_transfer/blocks_to_hwpx.py`(윤혁용 사본)를 고쳐 다음 명령이 한글에서 열리는 hwpx를 만들게 한다.

```
PYTHONIOENCODING=utf-8 python "04. 미소논문/tools/hwpx_transfer/blocks_to_hwpx.py" \
  --template "04. 미소논문/00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx" \
  --style-map "04. 미소논문/tools/hwpx_transfer/staging/style_map_miso.json" \
  --front "04. 미소논문/tools/hwpx_transfer/staging/front.blocks.json" \
  --cover "04. 미소논문/tools/hwpx_transfer/staging/cover_miso.json" \
  --blocks ch01 … ch06 apx1 apx2 (.blocks.json) \
  --references "04. 미소논문/tools/hwpx_transfer/staging/references.json" \
  --smoke   # → staging/test_out/smoke.hwpx
```

W1(파서)·W2(참고문헌)·W3(스타일 실측)이 병렬로 진행 중이다. 그들의 산출물이 아직 없으면 **직접 임시 입력을 만들어** 개발한다: 블록은 기존 파서 출력 형식(기준: `../tools/hwpx_transfer/staging/ch01.blocks.json` 형식 참고, `figure_image` 타입 추가), style_map은 계약 키에 아래 메인 표본 값을 임시로 넣은 `staging/style_map_dev.json`(**W3의 `style_map_miso.json`이 도착하면 그것으로 교체해 재검증**). 최종 검증 전 `orca orchestration check`로 코디네이터 메시지를 확인해 W1·W3 산출물 도착 여부를 본다.

메인 표본(임시 값): h1 paraPr 49/style 1/charPr 56 · h2 paraPr 46/charPr 60 · h3 charPr 39 · body paraPr 46/charPr 36 · caption paraPr 31/charPr 8 · 빨강 charPr 68(본문 36의 짝) · REF_TITLE paraPr 5 · REF_CATEGORY paraPr 12 · APPENDIX_TITLE paraPr 31. 나머지는 `analysis/extracted/Contents/header.xml`·`section2_paras.json`에서 스스로 실측해 임시 채움.

## 수정 사항
1. **하드코딩 id·상수 외부화.** `TABLE_WIDTH`, `ROW_MIN_H`, `LINE_W`, `REF_*`, `APPENDIX_TITLE`, `BODY_BOLD_CHAR`, `CELL_BOLD_CHAR`, `H4_FALLBACK_CHAR`, `blank("61")`·`blank("13")`의 61/13, `_char_heights()` 표, `border_fill()`의 6/45/46, 캡션 행 border "13", 목차 흑색 charPr "13", `SURVEY_COVER_*`의 41/63 등 소스 안의 **모든** 양식 id를 `style_map["constants"]`·`style_map["table"]`에서 읽게 바꾼다. 소스에 남는 숫자 id가 0개여야 한다(`grep -n '"[0-9]\+"' blocks_to_hwpx.py`로 증명, XML 속성 상수값 "0"/"1" 등은 제외).
2. **Template 전면부 슬라이스를 앵커 기반으로.** `_slice_front_matter()`의 `len(ps)!=112` 고정 검사를 없애고 `style_map["front_matter"]`의 idx·range를 쓴다. 안전장치: 앵커 문단 텍스트가 각각 "목  차"/"표 목 차"/"그 림 목 차"/"감사의 글"/"논 문  개 요"로 시작하는지 검사해 아니면 SystemExit.
3. **감사의 글 재구성.** 제목 상자 문단(p147, pageBreak=1)은 바이트 보존, 본문 문단들은 버리고 `thanks_body` 서식으로 `[확정 필요: 감사의 글 작성]` 1문단 + 빈 줄 + 말미 문단(`thanks_date` 서식 "2026 년  월", `thanks_name` 서식 "김 미 소")을 생성.
4. **논문개요 삽입.** `--front front.blocks.json`의 블록(p·h 등)을 `abstract_body` 서식으로 논문개요 제목 상자 문단 뒤에 넣는다. 굵게 run은 `BODY_BOLD_CHAR`, 마커는 빨강.
5. **표지(section0) 치환.** `--cover cover_miso.json` = `[{"role":"title","new":"…"}, …]`. `style_map["cover"]`의 `(section0_idx, run_ordinal, old, role)`로 위치를 찾아 `<hp:t>` 텍스트만 바꾼다(run·charPr 보존). 텍스트 길이가 바뀐 문단의 `<hp:linesegarray>`는 제거하거나 최소 1줄로 정리(한글이 재계산). 치환 건수를 리포트에 기록하고 기대 건수와 다르면 SystemExit. 메인 확정값(`cover_miso.json`은 네가 이 값으로 만든다):
   - title / submit_title: `건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여`
   - name: `김 미 소` · approval_title: `김 미 소의 석사학위논문을 인준함`
   - date: `2026년  월  일` · major: 변경 없음 · advisor: 변경 없음 · 학년도 "2026": 변경 없음
6. **그림 BinData 삽입.** 블록 `{"type":"figure_image","path":"그림/….png","alt":"…"}` → (a) ZIP에 `BinData/image{N}.png` 추가(엔트리 순서: 양식 엔트리 뒤에 추가, 압축 STORED), (b) `Contents/content.hpf`의 `<opf:manifest>`에 `<opf:item id="image{N}" href="BinData/image{N}.png" media-type="image/png" isEmbeded="1"/>` 추가, (c) 가운데 정렬(캡션 paraPr) 문단에 `<hp:pic>` 컨트롤. 크기: PNG IHDR에서 px를 읽고 폭을 `LINE_W` 이하(기본 `LINE_W`의 90%)로 맞춰 비율 유지, 단위 HWPUNIT(96dpi 가정: 1px = 75 HWPUNIT). `<hp:pic>` 필수 자식(`hp:offset`·`hp:orgSz`·`hp:curSz`·`hp:flip`·`hp:rotationInfo`·`hp:renderingInfo`·`hc:img binaryItemIDRef`·`hp:imgRect`·`hp:imgClip`·`hp:inMargin`·`hp:imgDim`·`hp:effects`, 그리고 `</hp:pic>` 뒤 `<hp:t/>`) 누락 시 한글이 크래시한다 — `~/.claude/skills/hwpx/references/xml-structure.md` §"이미지 삽입 (BinData)"과 `~/.claude/skills/hwpx/scripts/hwpx_helpers.py`의 `make_image_para`/`add_images_to_hwpx`/`update_content_hpf`를 읽고 그 구조를 따른다(이 스크립트를 import하지 말고 필요한 XML 조각을 이 조립기 안에 옮겨 적는다 — 파이프라인은 표준 라이브러리·단일 파일 원칙). `write_hwpx()`는 지금 양식 엔트리만 쓰므로 추가 엔트리를 받도록 확장. 이미지 파일 경로는 블록 JSON `source`가 있는 `01.docs/` 기준.
7. **부록 처리.** 윤혁용 `SURVEY_COVER_TITLE` 설문지 표지 로직·`is_survey` 판정을 제거(미소 부록1은 "부록 1. 실험 도구"). 부록 h1은 `APPENDIX_TITLE`(pageBreak), 부록 안 `## 1. …`은 h2_section, `### 3.1 …`은 h3_item, `####`은 h4로 렌더. `add_placeholder_section` 기본 꼬리는 `Abstract` 하나만(`[확정 필요: 영문초록 작성]`), 부록 3 자리는 만들지 않는다. 참고문헌 삽입 위치는 지금처럼 첫 부록 파일 앞.
8. **빨간 마커 접두사에 `작성 가이드` 추가** — `GUIDE_MARKER_RE`와 `tools/hwpx_transfer/verify_replace.py`의 마커 목록 **둘 다**. `Template.red_char_pr_id()`는 유지(양식에 이미 있는 빨간 charPr는 `RED_CHAR_BY_BASE`로 재사용, 없으면 복제).
9. **section2 첫 문단·secPr 이식**(`_slice_sec2_controls`)은 그대로 두되 p0가 "제1장"으로 시작하는지 검사.
10. `build_report()`에 표지 치환 내역·이미지 삽입 내역(파일, px, HWPUNIT)·마커 run 수를 추가.

## 완료 기준 (증거 첨부)
- `--smoke` 실행 exit 0, `staging/test_out/smoke.hwpx` 생성
- `PYTHONIOENCODING=utf-8 python "04. 미소논문/tools/hwpx_transfer/extract_text.py" --input smoke.hwpx --check-integrity` 문제 0건(이 스크립트도 새 엔트리 BinData를 허용하도록 필요 시 수정)
- `python ~/.claude/skills/hwpx/scripts/validate.py smoke.hwpx` → VALID
- 빨간 마커 검증 스니펫(`../03.plan/260912_0837_hwpx노하우_동기이관_가이드.md` §4-5의 코드, 마커 목록에 `[작성 가이드` 추가) → 검정 0
- **한컴 개방 시험**: `pwsh ../.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1 -HwpxPath <smoke.hwpx 절대경로> -PdfPath <스크래치>/smoke.pdf` → `Open=True`, 크래시 없음. 이 단계는 CPU를 독점하므로 다른 무거운 작업과 겹치지 않게 한 번만 돌린다. 실패하면 원인(대개 `<hp:pic>` 자식 누락 또는 linesegarray textpos 초과)을 고쳐 재시도
- `powershell.exe -NoProfile -File ../.claude/skills/hwpx-thesis-editing/scripts/render-pdf.ps1 -PdfPath smoke.pdf -OutDir <스크래치>/png -Pages "1-3,<그림 1-1이 있는 쪽>"`로 PNG를 만들어 Read로 열어 표지 치환·그림 삽입을 눈으로 확인(쪽 번호는 PDF 쪽수로 찾는다)
- 소스에 양식 id 하드코딩 0개 grep 증거

## 산출물
- `tools/hwpx_transfer/blocks_to_hwpx.py`(수정), `tools/hwpx_transfer/verify_replace.py`(마커 목록만), 필요 시 `extract_text.py`, `staging/cover_miso.json`, 개발용 `staging/style_map_dev.json`(W3 도착 전), `staging/test_out/smoke.hwpx`·`assembly_report.md`, 변경 요약 `analysis/assembler_changes.md`
