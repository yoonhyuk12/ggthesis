# 양식(260912_1059) 스타일 실측 보고 — style_map_miso.json 근거

측정일 2026-09-12 · 대상 `04. 미소논문/00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx`의 압축 해제본 `analysis/extracted/Contents/*.xml` · 재실행 `PYTHONIOENCODING=utf-8 python analysis/probe_style_map.py`

> 한글 재저장으로 header가 정규화돼 id가 전부 재번호됐다(charPr 81 · paraPr 64 · borderFill 29 · tabPr 6 · style 40). 기준 파일 `staging/style_map_yoonhyuk_reference.json`의 **값은 하나도 쓸 수 없고**, 키 이름만 물려받았다.

## 1. 문단 스타일 (section2 본문)

| 키 | 실측 근거(문단 idx·텍스트) | style | paraPr | charPr | paraPr 정의 | charPr 정의 |
| --- | --- | --- | --- | --- | --- | --- |
| `h1_chapter` | s2 p0 `제1장 서론` | 1 | 49 | 56 | LEFT·줄간격 PERCENT 170 | 16pt 한양신명조 bold |
| `h2_section` | s2 p2 `제1절 연구의 배경 및 필요성` | 0 | 46 | 60 | JUSTIFY·줄간격 PERCENT 170 | 15pt 한양신명조 bold |
| `h3_item` | s2 p4 `제1항 연구제목과 관련된 사회 현상` | 0 | 46 | 39 | JUSTIFY·줄간격 PERCENT 170 | 14pt 한양신명조 bold |
| `body` | s2 p6 ` 건설업은 우리나라 전체 산업 가운데 사망재해 위험이 ` | 0 | 46 | 36 | JUSTIFY·줄간격 PERCENT 170 | 11pt 한양신명조 |
| `caption` | s2 p7 `<그림 1-1> 산업별 업무상사고 사망재해 분포도` | 0 | 31 | 8 | CENTER·줄간격 PERCENT 170 | 11pt 한양신명조 |
| (빨강 마커 run) | s2 p8 `[그림 삽입 예정: 고용노동부(2024) 산업재` | 0 | 46 | 68 | 본문과 동일 | 11pt 빨강 #FF0000 |

빈 문단(s2 p1·p3·p5)은 run이 하나도 없고 paraPr 46만 있다 — `BLANK_CHAR`는 본문 charPr 36로 대신한다.

## 2. 목차·전면부 (section1)

| 키 | 근거 | style/paraPr/charPr | 비고 |
| --- | --- | --- | --- |
| `toc_entry` | s1 p2 `제1장 서론` (p2~p104 동일) | 0/47/13 | paraPr의 tabPr 4 = RIGHT 36852 leader DASH. **인라인 탭·쪽번호는 문서 전체 0건** |
| `toc_lot_entry` | s1 p107 `<표 2-1> …` · p138 `<그림 1-1> …` | 0/47/36 | 목차와 같은 paraPr, charPr만 본문 11pt |
| `s1_toc_title_idx` = 0 | s1 p0 `목  차` | 0/26/56 | 제목 상자 표(has_tbl=True), pageBreak=0 |
| `s1_lot_title_idx` = 106 | s1 p106 `표 목 차` | 0/25/15 | 제목 상자 표(has_tbl=True), pageBreak=1 |
| `s1_lof_title_idx` = 136 | s1 p136 `그 림 목 차` | 0/26/56 | 제목 상자 표(has_tbl=True), pageBreak=1 |
| `s1_thanks_range` = [147, 171] | p147 제목 상자 → p148 본문 → p149~p169 빈 문단 21개 → p170 `2026 년 12 월` → p171 `윤   혁` | 본문 0/46/61 | 사용자 작성분, 문단 경계 유지 |
| `s1_abstract_range` = [172, 173] | p172 `논 문  개 요` 제목 상자 + p173 공백 본문 자리 | 본문 0/46/8 | 국문초록은 p173 자리 |

메인이 추정한 앵커 `0 / 106 / 136 / [147,171] / [172,173]`은 덤프 실측과 **전부 일치**했다.

### 전면부에 섞인 빨간 charPr (양식 그대로 옮기면 안 되는 곳)

| 위치 | 실측 charPr | 색 | 검은 짝 |
| --- | --- | --- | --- |
| 표목차 제목 s1 p106 | 15 | #FF0000 | 79 |
| 감사의 글 본문 s1 p148 | 61 | #FF0000 | 8 |

윤혁 양식에서는 미완성 표시로 빨강을 쓴 자리가 전면부에도 남아 있다. 미소 논문 본문으로 채울 때는 검은 짝 charPr를 쓰고, 빨강은 프로젝트 규칙대로 `[확정 필요`·`[작성 가이드` 같은 마커에만 남긴다.

## 3. 표 (section2 본문 표 46개 전수)

- 표 폭 `sz.width`: 39142(36개), 39491(6개), 39232(2개), 38402(2개) → `TABLE_WIDTH`
- `pageBreak`: 실측도 전부 `NONE`(46/46) → 규칙대로 `NONE` 고정
- `cellSz.height` 최빈 1565(1425회) → `ROW_MIN_H`
- 본문 `linesegarray/@horzsize` 전 문단 동일 39684 → `LINE_W`
- 셀 여백 `cellMargin` 최빈 {'left': '510', 'right': '510', 'top': '141', 'bottom': '141'} (1466회)
- 대표 표: 대표 표(<표 2-1> 시스템 기술 특성 하위요인 도출 매트릭스, s2 p81) colCnt=6 rowCnt=16, 데이터 행 열폭 ['8504', '10485', '4259', '6240', '5391', '4263'] 합=39142=표 폭 39142. 모든 행의 cellSz.width 합이 표 폭과 일치해야 한다(rowSpan 셀은 해당 행에서 제외). cellSz.height는 참고값(최빈 1565, 한글이 재계산).

| 위치 | borderFill 최빈 | 정의 |
| --- | --- | --- |
| 내부 셀 (`BORDER_INNER`) | **6** (906회) | left SOLID 0.12 mm / right SOLID 0.12 mm / top SOLID 0.12 mm / bottom SOLID 0.12 mm |
| 왼쪽 끝 열 (`BORDER_LEFT_EDGE`) | **28** (246회) | left NONE 0.12 mm / right SOLID 0.12 mm / top SOLID 0.12 mm / bottom SOLID 0.12 mm |
| 오른쪽 끝 열 (`BORDER_RIGHT_EDGE`) | **29** (279회) | left SOLID 0.12 mm / right NONE 0.12 mm / top SOLID 0.12 mm / bottom SOLID 0.12 mm |
| 캡션 행(전 열 병합) (`BORDER_CAPTION_ROW`) | **13** (25회) | left NONE 0.12 mm / right NONE 0.12 mm / top NONE 0.12 mm / bottom SOLID 0.12 mm |
| 회색 머리행 (`BORDER_HEADER_GRAY`) | **7** (대체값) | left NONE 0.25 mm / right SOLID 0.25 mm / top SOLID 0.4 mm / bottom SOLID 0.25 mm / 배경 #BBBBBB |

`BORDER_HEADER_GRAY` 주의 — 이 양식에는 '사방 실선 + 회색 배경' borderFill이 **없다**. winBrush faceColor를 가진 정의는 borderFill 7, 19, 27뿐이고, 그중 표 셀에 실제로 쓰인 것은 7(배경 #BBBBBB)이다. 본문 표의 머리행은 회색 배경 없이 좌우 개방 테두리(28/29)와 bold charPr 16로만 구분한다.

| 셀 서식 | 값 | 근거 |
| --- | --- | --- |
| `cell_paraPr` | 55 | 셀 문단 1429회로 최빈 (CENTER·줄간격 PERCENT 160) |
| `cell_charPr` | 7 | 셀 run 988회로 최빈 (10pt 한양신명조) |
| 캡션 행 | borderFill 13 / paraPr 11 / charPr 53 | 캡션 셀 25개 전수 동일 (charPr 53는 10pt 굴림) |

## 4. constants

| 키 | 값 | 근거 |
| --- | --- | --- |
| `TABLE_WIDTH` | 39142 | 본문 표 36/46개의 sz.width |
| `ROW_MIN_H` | 1565 | cellSz.height 최빈값(1425회) |
| `LINE_W` | 39684 | section2 본문 lineseg horzsize 전건 동일 |
| `BODY_BOLD_CHAR` | 9 | charPr 9는 본문 charPr 36와 11pt·한양신명조·borderFill 2가 같고 bold만 다른 짝(문서 내 48회 사용). |
| `CELL_BOLD_CHAR` | 16 | charPr 16는 셀 기본 charPr 7(10pt)의 bold 짝(36회 사용). |
| `H4_FALLBACK_CHAR` | 9 | = BODY_BOLD_CHAR (양식에 h4 대응 서식 없음) |
| `BLANK_CHAR` | 36 | 빈 문단에는 run이 없어 charPr를 잴 수 없으므로 본문 charPr를 그대로 쓴다. |
| `TOC_BLANK_CHAR` | 36 | 목차 영역 빈 문단(s1 p1·p105·p135·p146)도 run이 없다. 이 문단들의 paraPr는 46(본문과 동일)이므로 charPr도 본문 값을 쓴다. |
| `TOC_ENTRY_CHAR` | 13 | s1 p2~p104 목차 항목 run charPr(문서 전체 105회) |
| `BORDER_INNER` | 6 | 내부 셀 최빈 906회 |
| `BORDER_LEFT_EDGE` | 28 | colAddr=0 셀 최빈 246회 |
| `BORDER_RIGHT_EDGE` | 29 | 마지막 열 셀 최빈 279회 |
| `BORDER_CAPTION_ROW` | 13 | 캡션 행 최빈 25회 |
| `BORDER_HEADER_GRAY` | 7 | 대체값 — 위 3절 주의 참조 |
| `REF_TITLE` | style 0 / para 5 / char 56 | s2 p554 `참고문헌` |
| `REF_CATEGORY` | style 0 / para 12 / char 35 | s2 p556 `가. 학위논문` |
| `REF_ENTRY` | style 0 / para 50 / char 8 | s2 p558 `[01] 김윤헌, 「건설현장 위험상황 이해 및 대응을 위한 인공지` |
| `APPENDIX_TITLE` | style 0 / para 31 / char 14 | s2 p593 `부   록 (도입 현장)` |

### RED_CHAR_BY_BASE — 검은 charPr → 빨간 charPr (19쌍)

| 검정 | 서식 | 빨강 | 사용 횟수(검정/빨강) |
| --- | --- | --- | --- |
| 7 | 10pt 한양신명조 | 69 | 992 / 515 |
| 8 | 11pt 한양신명조 | 61 | 270 / 1 |
| 9 | 11pt 한양신명조 bold | 70 | 48 / 3 |
| 13 | 12pt 한양신명조 | 67 | 105 / 1 |
| 14 | 16pt 한양신명조 bold | 32 | 8 / 2 |
| 36 | 11pt 한양신명조 | 68 | 603 / 103 |
| 38 | 11pt 한양신명조 | 68 | 9 / 103 |
| 39 | 14pt 한양신명조 bold | 71 | 49 / 3 |
| 48 | 10pt 한양신명조 | 69 | 3 / 515 |
| 49 | 10pt 한양신명조 | 69 | 1 / 515 |
| 56 | 16pt 한양신명조 bold | 15 | 11 / 1 |
| 64 | 10pt 한양신명조 | 69 | 3 / 515 |
| 65 | 12pt 한양신명조 | 67 | 4 / 1 |
| 72 | 11pt 한양신명조 bold | 70 | 1 / 3 |
| 76 | 12pt 한양신명조 | 67 | 1 / 1 |
| 77 | 12pt 한양신명조 | 67 | 1 / 1 |
| 78 | 12pt 한양신명조 | 67 | 1 / 1 |
| 79 | 16pt 한양신명조 bold | 15 | 1 / 1 |
| 80 | 10pt 한양신명조 | 69 | 1 / 515 |

본문 charPr 36의 빨강 짝은 68이며, 이는 메인 표본(s2 p8 `[그림 삽입 예정…]` charPr 68)과 일치한다.

`CHAR_HEIGHTS`는 header.xml의 charPr 81개 전수를 id→height(hu)로 담았다.

## 5. 표지 치환 대상 (section0)

section0의 최상위 문단은 3개뿐이고 실제 텍스트는 전부 표 셀 안이므로 `section0.xml`을 직접 파싱해 run 순서(`run_ordinal` = 문단 안 `<hp:run>` 문서 순서, 0-base)로 위치를 잡았다. `splittable=true`는 바꿀 문자열이 **하나의 `<hp:t>` 안에 통째로** 들어 있어 run·charPr 구조를 그대로 두고 텍스트만 치환할 수 있다는 뜻이다.

| s0 문단 | run# | charPr | role | 현재 텍스트 | 그 run의 `<hp:t>` 수 | splittable |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 2 | 31 | `year` | `2026` | 1 | 예 |
| 0 | 6 | 47 | `title` | `중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입` | 1 | 예 |
| 0 | 8 | 21 | `advisor` | `지도교수 : 박 종 용` | 1 | 예 |
| 0 | 12 | 22 | `major` | `건축ㆍ안전공학전공` | 1 | 예 |
| 0 | 14 | 24 | `name` | `윤   혁` | 1 | 예 |
| 1 | 3 | 47 | `title` | `중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입` | 1 | 예 |
| 1 | 5 | 25 | `submit_title` | `이 논문을 석사학위논문으로 제출함` | 1 | 예 |
| 1 | 6 | 26 | `date` | `2026년 12월  일` | 1 | 예 |
| 1 | 10 | 22 | `major` | `건축․안전공학전공` | 1 | 예 |
| 1 | 12 | 24 | `name` | `윤   혁` | 1 | 예 |
| 2 | 2 | 29 | `approval_title` | `윤   혁의 석사학위논문을 인준함` | 1 | 예 |
| 2 | 25 | 26 | `date` | `2026년 12월  일` | 1 | 예 |

주의 1 — 겉표지(s0 p0)의 전공은 `건축ㆍ안전공학전공`(U+318D 아래아), 속표지(s0 p1)는 `건축․안전공학전공`(U+2024 ONE DOT LEADER)로 **가운뎃점 문자가 서로 다르다**. 원문을 그대로 두지 말고 W4가 지정한 값으로 통일해야 한다. 인준서(s0 p2)에는 전공 줄이 없다.

주의 2 — `name`은 겉표지·속표지 2회이고, 인준서의 `윤   혁의 석사학위논문을 인준함`은 성명이 문장 안에 박혀 있어 별도 role `approval_title`로 뒀다(브리프의 '성명 3회'에 해당). `date`는 속표지·인준서 2회, `title`은 겉표지·속표지 2회, `major`는 2회다.

주의 3 — `run_ordinal`은 **표 셀 안 run까지 포함한** 문단 내 `<hp:run>` 등장 순서다(표지 문단은 통째로 표 1개라 최상위 run이 표를 감싸고 실제 글자는 셀 안 run에 들어 있다). 위 좌표는 정규식 파싱과 ElementTree 파싱 두 방법으로 교차검증했다(`probe_style_map.py` 검증 5단계).

주의 4 — 겉표지 `2026학년도`는 `2026`(run 2, charPr 31)과 `학년도`가 서로 다른 run이다. 학년도를 바꿀 때는 숫자 run의 `<hp:t>`만 손댄다.

## 6. 쪽 설정

| 구역 | 여백 left/right/top/bottom/footer | 쪽번호 |
| --- | --- | --- |
| section0_cover | 8503/8503/8503/7086/0 | 없음(표지) |
| section1_front | 8503/8503/9921/4251/4251 | BOTTOM_CENTER ROMAN_SMALL `-` newNum=None |
| section2_body | 7086/7086/9921/4251/4251 | BOTTOM_CENTER DIGIT `-` newNum=1 |

용지 53858 x 72567 HWPUNIT (190.0 x 256.0 mm), landscape=WIDELY, gutterType=LEFT_ONLY. 각주 번호 DIGIT) · 번호 매김 CONTINUOUS · 구분선 0.12 mm.

## 7. 미해결·주의 사항

1. **회색 머리행 정의가 없다.** 이 양식에는 `사방 실선 + 회색 배경` borderFill이 없다(faceColor를 가진 borderFill은 7, 19, 27 셋뿐이고 사방 실선이 아니다). `BORDER_HEADER_GRAY`는 대체값이므로, W4가 머리행을 회색으로 칠하려면 header.xml에 borderFill을 새로 추가해야 한다(= id 재번호 위험). 양식 관행대로 **회색 없이 bold charPr 16**로 머리행을 구분하는 편을 권한다.
2. **목차 리더·쪽번호가 없다.** `<hp:tab>`이 section1/section2 통틀어 0건이다. 쪽번호를 넣으려면 paraPr 47의 tabPr 4(RIGHT 36852, leader DASH)에 맞춰 인라인 탭을 새로 만들어야 한다. `toc_entry.inline_tab`은 그때 쓸 관례값이다.
3. **문단 덤프의 `byte_start`/`byte_end`는 사실 문자 오프셋**이다. bytes로 슬라이스하면 조각이 어긋난다(이 스크립트는 UTF-8 디코드 후 문자 슬라이스를 쓴다). W4도 같은 함정에 주의.
4. `noAdjust`는 표 46개 중 38개가 `0`, 8개가 `1`이다. 최빈값 `0`을 기본으로 뒀다.
5. `table.borderFills`에는 조립기가 실제로 쓰는 5종만 담았다. 양식에는 borderFill이 29개 있고 표 셀에 쓰인 것만 해도 21종이지만(2중선 26 = 부록 설문지 제목 상자 등), 나머지는 사용자가 직접 만든 설문지 표의 국소 서식이라 조립 대상이 아니다.
