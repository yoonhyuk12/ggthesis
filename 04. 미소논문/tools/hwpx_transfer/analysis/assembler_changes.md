# 조립기(`blocks_to_hwpx.py`) 변경 요약 — 미소 논문 260912 양식용

W4가 개조한 내용을 소스(`tools/hwpx_transfer/blocks_to_hwpx.py`)를 읽어 정리했다. 기준은 상위 저장소(윤혁 논문)의 같은 이름 스크립트다.

1. **새 CLI 옵션 2종.** `--front`(논문개요 블록 JSON `front.blocks.json`)와 `--cover`(표지 치환값 `cover_miso.json`). 기존 `--template/--style-map/--blocks/--references/--output/--smoke`에 더해졌고, `--image-root`(그림 기준 디렉토리, 기본 `<repo>/01.docs`)도 새로 생겼다. `--smoke`는 `--output` 없이 `staging/test_out/smoke.hwpx` + `assembly_report.md`로 뽑는다.
2. **양식 id·치수를 소스에서 전부 뺐다.** `Constants` 클래스가 `style_map.json`의 `constants` 블록만 읽는다. 필수 키는 `REQUIRED_CONSTANTS` 14종 — `TABLE_WIDTH`, `ROW_MIN_H`, `LINE_W`, `REF_TITLE`, `REF_CATEGORY`, `REF_ENTRY`, `APPENDIX_TITLE`, `BODY_BOLD_CHAR`, `CELL_BOLD_CHAR`, `BLANK_CHAR`, `TOC_BLANK_CHAR`, `TOC_ENTRY_CHAR`, `BORDER_INNER`, `BORDER_LEFT_EDGE`, `BORDER_RIGHT_EDGE`, `BORDER_CAPTION_ROW`. 하나라도 없으면 `SystemExit`으로 조립을 멈춘다. 양식이 바뀌면 style_map만 다시 실측하면 된다(양식 header 재저장으로 charPr 81·paraPr 64로 재번호된 이번 사고의 재발 방지).
3. **전면부 앵커 계약.** `style_map.front_matter`의 `s1_toc_title_idx`·`s1_lot_title_idx`·`s1_lof_title_idx`·`s1_thanks_range`·`s1_abstract_range`·`abstract_body`·`thanks_body` 7키가 필수다(`REQUIRED_FRONT_MATTER`). `_slice_front_matter()`가 idx 범위를 검사하고 앵커 문단이 실제로 `목 차`/`표 목 차`/`그 림 목 차`/`감사의 글`/`논 문 개 요`로 시작하는지 텍스트까지 대조한다(`FRONT_ANCHOR_TEXT`). 제목 상자 문단은 양식 XML을 **바이트 그대로** 옮기고, 목차·표목차·그림목차만 재생성한다. 감사의 글 본문은 `[확정 필요: 감사의 글 작성]` 자리표시자 + `2026 년  월`/`김 미 소`로 생성하고, 논문개요 본문은 `--front` 블록으로 채운다. section2 첫 문단은 `제1장`으로 시작하는지 검사(`SEC2_FIRST_ANCHOR`)한 뒤 양식 첫 문단의 `colPr·secPr·pageNum` 제어 블록을 이식해 페이지 설정을 보존한다.
4. **표지 치환 방식 — 텍스트만, run·charPr 보존.** `style_map.cover`의 앵커 목록(`section0_idx` + `run_ordinal` + `old` 원문)을 따라 해당 `<hp:run>`의 `<hp:t>` 텍스트만 바꾼다. 원문이 문단에서 안 보이거나 여러 번 나오는데 `run_ordinal`이 안 맞으면 즉시 중단하고, 치환 건수가 기대치와 다르면 실패로 처리한다. 문단을 재생성하지 않으므로 `linesegarray`를 건드릴 일이 없다. 이번 조립에서 role 7건(title 2, name 3, date 2, approval_title 1) 치환.
5. **새 블록 타입 2종.** `figure_image` — `path`(또는 `src`)의 PNG를 IHDR에서 픽셀 크기를 직접 읽어(`png_size`, 표준 라이브러리만) 96dpi 가정으로 HWPUNIT 환산(`PX_TO_HWPUNIT=75`)하고, 폭은 본문 줄 폭의 90%(`IMAGE_WIDTH_RATIO`)를 상한으로 비율 유지 축소한다. `BinData/imageN.png` 엔트리를 ZIP 뒤에 덧붙이고 `Contents/content.hpf`의 `</opf:manifest>` 앞에 `<opf:item … isEmbeded="1"/>`로 등록한다. 그림 문단은 `<hp:pic>` 필수 자식을 모두 갖춰 생성한다(빠지면 한글 크래시). `figure_placeholder`는 그림 없이 자리표시자만 낸다.
6. **guide 문단(문단 전체 빨강) 경로 신설.** 블록의 `guide:true`(MD 원고의 `> [작성 가이드] …` 인용구)이면 `runs_para(..., guide=True)`가 `red_of()`로 **문단의 모든 run charPr를 빨간 짝으로** 바꾼다. 마커 정규식 경로와는 별개다.
7. **마커 접두사 6종으로 확장.** `GUIDE_MARKER_RE`에 기존 5종(`DATA PENDING`/`확정 필요`/`CITE_TODO`/`그림 삽입 예정`/`UNVERIFIED`)에 더해 **`작성 가이드`**가 들어갔다. `marker_aware_runs()`가 run을 마커 앞·마커·마커 뒤로 쪼개고 `red_char_pr_id()`가 필요한 빨간 charPr를 header에 없을 때만 복제 생성한다(이번 조립은 양식에 이미 빨간 charPr 11종이 있어 신규 복제 0건).
8. **표 캡션 병합·셀 토큰.** 표 캡션(`table_caption`)은 바로 뒤에 표가 오면 표 첫 행에 병합하고(양식 관행), 캡션 뒤에 표가 없으면 일반 문단으로 낸다. 셀 텍스트의 `<br>`은 줄바꿈, `&emsp;`는 전각 공백(`　`)으로 치환한다.
9. **결과 리포트 자동 생성.** `assembly_report.md`에 전면부 앵커 idx, 표지 치환 표(기존→변경), 치환 후 표지 문단 텍스트, BinData 그림 표(원본·px·HWPUNIT), 빨간 마커 run 수와 신규 charPr 복제 수, 목차/표목차/그림목차 항목 수를 적는다.

검증 결과는 `staging/test_out/verify_report.md` 참조(7단계 전부 통과, Open=True, 146쪽).

## 설문 양식 (W7, 2026-09-12 추가)

사용자 지시 "설문 형태 표 양식도 내꺼(윤혁 논문)를 그대로 사용해주라"에 따라, 부록 설문을 새로 그리지
않고 **양식 XML을 통째로 복제해 텍스트만 갈아끼우는 클론 경로**를 넣었다.

10. **새 CLI 옵션 `--survey-layout`.** `staging/survey_layout.json`을 받으면 설문 틀을 입히고, 주지
    않으면 기존대로 일반 표로 조립한다(회귀 없음 — 옵션 없이 조립하면 apx1 `--verify-blocks` 누락 0).
11. **`Template._slice_survey_templates()` — 텍스트 앵커로 자른다.** 양식 section2의 최상위 문단에서
    `SURVEY_ANCHORS` 4종(`안녕하십니까?` 표지 상자 · `A. 실태조사 대상자 개요` Part A 상자 ·
    `전혀그렇지않다` 리커트 12열 · `소    속 :` pp30 라벨 문단)을 찾아 문단 XML을 통째로 보관한다.
    문단 idx를 박지 않으므로 양식이 조금 바뀌어도 따라간다. 못 찾으면 `SystemExit`.
12. **중첩 표를 견디는 XML 헬퍼 5종.** `tbl_spans`/`tr_spans`/`tc_spans`는 `hp:tbl` 깊이를 세어 제
    층의 요소만 잘라낸다(Part A 상자는 표 안에 제목 표가 들어 있어 `</hp:tbl>` 첫 등장으로 자르면
    깨진다). `cell_addr`/`set_cell_size`/`set_cell_addr`는 **마지막** `cellAddr/cellSz/cellSpan`이
    자기 값이라는 규칙으로 중첩 셀을 건드리지 않는다. `renumber_ids`가 복제본의 `hp:p`·`hp:tbl` id를
    IdGen으로 전부 재발급하고, `strip_linesegarray`가 레이아웃 캐시를 지운다.
13. **`Assembler.survey_cover_box` / `survey_partA_box` / `survey_likert`.** 셀의 첫 문단을 서식
    표본으로 삼아 복제하므로 정렬·글꼴·테두리·굵기(cp9/cp16)가 양식 그대로 따라온다. 굵은 run,
    빨간 마커(`marker_aware_runs`), guide 문단 규칙도 상자 안에서 그대로 적용된다.
    `survey_likert(split=[w1,w2])`는 진술문 열(20,769)을 두 열로 쪼개 **13열 격자**를 만든다
    (7.2 평정 양식). 쪼갠 폭의 합이 원래 열 폭과 다르면 `SystemExit`으로 멈춘다.
14. **줄 수·행 높이는 양식에서 실측한다.** `lineseg_metrics()`가 표본 문단의 첫 `hp:lineseg`에서
    줄 높이(vertsize+spacing)·줄 폭·글자 높이를, 두 번째 `hp:lineseg`의 `textpos`에서 "한 줄에 몇
    글자"를 읽는다(힌트가 없으면 줄 폭÷(글자 높이×0.9)). 셀 높이는 `줄 수 × 줄 높이 + cellMargin`
    으로 잡는다 — 양식의 선언 높이를 그대로 쓰면 슬랙까지 따라와 `tblplan` 판정이 흐려진다.
15. **격자 정합은 열 격자에서 유도한다.** 열 폭은 양식 r1(눈금 장식 행)의 개별 셀 폭에서 읽고,
    모든 행의 `cellSz.width` 합 = 표 폭, `colAddr/colSpan`이 12(또는 13)열 격자와 맞게 계산한다.
    어긋나면 한글이 행을 재배치한다. 검사기는 `staging/test_out/check_survey_grid.py`.
16. **Part A 상자 분할은 데이터로.** 미소 사전 설문은 문항 8개라 한 상자가 한 쪽을 넘으므로
    (59,746 > 54,144 HWPUNIT) `survey_layout.partA_boxes`의 규칙대로 의미 단위 4문항씩 두 상자로
    나눈다. 규칙이 없으면 한 상자로 낸다. 문항 수가 규칙을 넘으면 마지막 상자에 붙이고 `notes`에
    경고를 남긴다.
17. **리커트 변수명은 앞 문단의 굵은 run에서 가져온다.** `**J. 사고예방 효과** (자체 개발 — …)`
    처럼 굵은 부분 뒤에 표가 오면 굵은 텍스트를 표의 변수명 셀로 올리고, 나머지 설명은 표 앞
    문단으로 남긴다. 평정 양식(13열)의 변수명·척도 라벨은 `survey_layout.rating`에서 읽는다.

검증 결과는 `staging/test_out/verify_report_w7.md` 참조(8단계 전부 통과, Open=True, 145쪽,
설문 표 8개 격자 정합 OK).

## guide 문단 제외 (W7 추가 지시, 2026-09-12 15:40)

사용자 지시 "`[작성 가이드]` 인용구와 절·항 사이의 집필 안내 문단은 논문 hwpx에 넣지 마라"에 따라
기본 동작을 **제외**로 바꿨다.

18. **`guide:true` 문단은 렌더하지 않는다.** `Document.add_blocks`와 `add_front_blocks`의 `p` 분기에서
    건너뛰고 `doc.guide_skipped`를 센다. 빨간 문단 경로(`runs_para(guide=True)` → `red_of`)는 코드에
    그대로 두고, **`--keep-guide`** 옵션을 줄 때만 켠다. 이번 조립에서 **119문단 제외**
    (ch01 5 · ch02 5 · ch03 8 · ch04 12 · ch05 71 · ch06 11 · apx1 6 · front 1).
19. **조립 리포트에 `- guide 문단 제외: N` 줄이 추가된다.** `--keep-guide`를 쓰면 "빨간 문단으로 유지"로
    표기가 바뀐다.
20. **부수 효과 — 빈 줄 중복이 줄어든다.** 제목 뒤 빈 줄과 다음 제목 사이에 guide 문단만 있던 자리는
    `blank_before_heading()`의 중복 방지가 걸려 빈 줄이 하나 덜 나간다(본문 문단 852 → 727: guide 118 +
    빈 줄 7). 의도한 동작이다.
21. **검증 방식이 바뀐다.** `--verify-blocks`는 순서 커서 방식이라 guide 문단을 통째로 빼면 그 뒤가
    전부 누락으로 찍힌다. 판정은 `staging/test_out/check_guide_absent.py`(guide 텍스트가 hwpx에
    0건 존재 + 누락 목록을 guide/설문 재구성으로 분류)로 한다.

**MD와 hwpx가 의도적으로 달라진다.** MD가 단일 원본이라는 규칙은 그대로이며, hwpx 쪽에서만 걸러낸다.
심사용으로 안내 문단을 보려면 `--keep-guide`로 다시 조립한다.
