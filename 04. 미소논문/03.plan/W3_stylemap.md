# W3 — 양식(260912_1059) 스타일 실측 → style_map_miso.json

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다.

## 배경
조립기 `blocks_to_hwpx.py`는 양식 hwpx의 charPr/paraPr/borderFill/tabPr id를 `style_map.json`과 소스 상수로 갖는다. 그런데 이번 양식(`양식원본_260912_1059_윤혁작성본.hwpx`)은 한글 재저장으로 header가 정규화돼 **id가 전부 재번호**됐다(charPr 81, paraPr 64, borderFill 29, tabPr 6, style 40). 기준 파일 `staging/style_map_yoonhyuk_reference.json`·`analysis/template_analysis_yoonhyuk_reference.md`의 값은 무효이고, 키 이름과 실측 방법만 참고한다.

메인이 확인한 표본(검산용): section2 p0 "제1장 서론" paraPr 49/style 1/charPr 56 · p2 "제1절…" paraPr 46/charPr 60 · p4 "제1항…" charPr 39 · p6 본문 paraPr 46/charPr 36 · p7 그림 캡션 paraPr 31/charPr 8 · p8 `[그림 삽입 예정…]` 빨강 charPr 68 · p554 "참고문헌" paraPr 5 pageBreak=1 · p556 "가. 학위논문" paraPr 12 · p593 "부   록" paraPr 31 pageBreak=1.

## 할 일
`tools/hwpx_transfer/analysis/extracted/Contents/header.xml`과 `section{0,1,2}_paras.json`(필요 시 `section*.xml`의 byte_start~byte_end 구간)을 읽어 `tools/hwpx_transfer/staging/style_map_miso.json`을 만든다.

1. 기준 파일의 **모든 키를 같은 이름으로 유지**하고 값을 실측한다: `h1_chapter`, `h2_section`, `h3_item`, `body`, `caption`, `toc_entry`(tabPrIDRef·inline_tab 포함), `toc_lot_entry`, `table`(`tbl_attrs` 전체, `borderFills`, `cell_paraPr`, `cell_paraPr_variants`, `cell_charPr`, `cell_charPr_variants`, `cell_padding`, `_grid`). 표는 section2의 본문 표(예: <표 2-1>이 든 문단)를 실측하고, `tbl_attrs.pageBreak`는 실측값과 무관하게 **"NONE"** 으로 둔다(규칙).
2. 추가 키 `constants`(메인 계획서 계약 그대로):
   - `TABLE_WIDTH`(대표 표 sz.width), `ROW_MIN_H`(최소 cellSz height), `LINE_W`(본문 linesegarray horzsize)
   - `REF_TITLE`·`REF_CATEGORY`·`REF_ENTRY`(참고문헌 제목/분류/서지 항목 문단의 style·para·char), `APPENDIX_TITLE`
   - `BODY_BOLD_CHAR`(본문 charPr와 bold만 다른 짝), `CELL_BOLD_CHAR`(셀 charPr의 bold 짝), `H4_FALLBACK_CHAR`(= BODY_BOLD_CHAR), `BLANK_CHAR`(본문 빈 줄 run의 charPr — 빈 문단은 run이 없을 수 있으니 본문 charPr로), `TOC_BLANK_CHAR`, `TOC_ENTRY_CHAR`(목차 항목 흑색 charPr; section1 p2~p104 실측)
   - `BORDER_INNER`, `BORDER_LEFT_EDGE`, `BORDER_RIGHT_EDGE`, `BORDER_CAPTION_ROW`, `BORDER_HEADER_GRAY` — header의 `<hh:borderFill>`을 읽어 "사방 실선", "왼쪽만 없음", "오른쪽만 없음", "아래만 실선", "회색 배경" 정의를 찾아 id를 적는다. 없으면 가장 가까운 것을 적고 `_note`에 사유
   - `RED_CHAR_BY_BASE`: `textColor="#FF0000"`인 charPr 각각에 대해 색만 다른 원본 charPr id를 짝지은 맵(예: {"36":"68"})
   - `CHAR_HEIGHTS`: 이 문서에서 쓰이는 모든 charPr id → `height`(hu) 맵 (header 전수)
3. 추가 키 `front_matter`: section1 앵커 `s1_toc_title_idx`, `s1_lot_title_idx`, `s1_lof_title_idx`, `s1_thanks_range`, `s1_abstract_range`(덤프 idx 기준으로 실측해 확정; 메인 추정은 0/106/136/[147,171]/[172,173]), `abstract_body`·`thanks_body`·`thanks_date`·`thanks_name`(각 문단의 style/para/char)
4. 추가 키 `cover`: section0 문단별 텍스트에서 치환 대상 run을 찾아 `[{"section0_idx":i, "run_ordinal":k, "old":"…", "role":"title|name|major|date|advisor|submit_title|approval_title"}]`로 나열. 표지 3면(겉표지·속표지/제출서·인준서)의 제목 2회, 성명 3회("윤   혁", "윤   혁의 석사학위논문을 인준함"), 날짜 2회("2026년 12월  일"), 전공 2회, 학년도 "2026" 등. 표 셀 안 문단이라 `section0_paras.json` 덤프(최상위 3문단)로는 부족하니 `section0.xml`을 직접 파싱해 `<hp:t>` 단위로 위치를 잡고, **치환 시 run·charPr 구조를 보존해도 되는지**(한 `<hp:t>` 안에 통째로 들어 있는지) 확인해 `splittable` 여부를 적는다.
5. `analysis/template_analysis_miso.md`: 위 값의 실측 근거(문단 idx·XML 발췌)를 표로 남긴다.

## 완료 기준
- `style_map_miso.json`이 JSON으로 로드되고, 기준 파일의 키 집합 ⊆ 새 파일 키 집합임을 `python`으로 비교한 출력
- 실측 id가 header.xml에 실제로 존재함을 검사한 출력(모든 charPr/paraPr/borderFill/tabPr id 존재 확인, 0건 누락)
- 메인 표본 9건과 일치

## 산출물
- `tools/hwpx_transfer/staging/style_map_miso.json`, `tools/hwpx_transfer/analysis/template_analysis_miso.md`, 실측 스크립트 `tools/hwpx_transfer/analysis/probe_style_map.py`(재실행 가능)
