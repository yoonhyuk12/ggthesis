# 김정년 양식 hwpx 내부 XML 실측 노트

- 대상: `00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx` (SHA256 `9bf1980a…1dfff3`)
- 입력: 추출본 `template_extracted/Contents__{header,section0,section1,section2}.xml`, 덤프 `dumps/template_kjn_paras.json`. hwpx 파일 자체는 열지 않았다.
- 실측일: 2026-10-08 (Task G). 산출: `style_map_kjn.json`(조립기 입력), 이 노트, `snippets/*.xml` 7개.
- 번호 표기: `s2:102` = section2.xml의 0부터 세는 **직계** 문단 102번(덤프 idx와 같다). 단위는 HWPUNIT(7200=25.4mm), 글자 크기 hu(1/100pt).
- 서식만 가져온다. 김정년의 제목·성명·본문·표·참고문헌·부록 내용은 한 줄도 산출물에 남기지 않는다(CLAUDE.md 🟦 항목). snippets에 들어 있는 김정년 문구는 구조 예시일 뿐이며 이식할 때 전부 바꾼다.

## 1. 섹션 역할

| 파일 | 직계 문단 | 역할 | 여백 L/R/T/B/머리/꼬리 | 쪽번호 |
| --- | ---: | --- | --- | --- |
| section0.xml | 2 | 겉표지·제출지(s0:0 한 run에 글자처럼 취급 표 2개), 인준지(s0:1 표 1개) | 8503/8503/8503/7086/0/0 (30/30/30/25/0/0mm) | 없음 |
| section1.xml | 134 | 목차 0–70 · 표목차 71–104 · 그림목차 105–110 · 감사의글 111–124 · 논문개요 125–133 | 8503/8503/9921/4251/0/4251 (30/30/35/15/0/15mm) | `ROMAN_SMALL`, 하단 가운데, `-` 곁문자, i부터 |
| section2.xml | 712 | 본문 0–537 · 참고문헌 538–651 · 부록 652–693 · Abstract 694–711 | 7086/7086/9921/4251/0/4251 (25/25/35/15/0/15mm) | `DIGIT`, 하단 가운데, 1부터, 첫 쪽 숨김 |

용지는 세 구역 모두 `width=53858 height=72567`(190.0×256.0mm), `landscape="WIDELY"`, `gutterType="LEFT_ONLY"`. 본문 가용 폭은 section1 36852(130mm), section2 39686(140mm)이다.

### 쪽번호 제어 위치 (`snippets/section1_first_para.xml`, `section2_first_para.xml`)

- **s1:0** — run[0]: `secPr`+`colPr`. run[1]: `<hp:pageNum pos="BOTTOM_CENTER" formatType="ROMAN_SMALL" sideChar="-"/>` 다음에 「목  차」 제목상자 표. **`newNum`은 그 표 둘째 행 셀 문단 안에 있다**(`<hp:ctrl><hp:newNum num="1" numType="PAGE"/></hp:ctrl>`). 제목상자를 새로 만들면 이 ctrl이 사라지므로 snippet을 통째로 이식한다.
- **s2:0** — run[0]: `colPr`+`secPr`. run[1]: `pageNum(DIGIT)` → `pageHiding hidePageNum="1"` → `제 1 장  서  론` → `newNum num="1"`. 본문 첫 장 제목 텍스트만 바꾼다.
- 머리말·꼬리말 개체는 없다. 각주 설정(`DIGIT`, 접미 `)`)만 secPr에 있고 각주 개체는 0건이다.

## 2. 제목·본문 스타일 실측

모든 대표 서식의 글꼴은 `fontRef hangul=6 latin=7` = 한양신명조. `styleIDRef`는 거의 전부 0(바탕글: 함초롬바탕 10pt)이므로 **paraPr/charPr을 문단·run에 직접 지정**해야 한다.

| 키 | paraPr | charPr | 크기·굵기 | 정렬·줄간격 | 근거 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| h1_chapter | 46 | 56 | 16pt 굵게 | 왼쪽 170% | s2:36·259·361 | pageBreak=1. s2:0만 paraPr23(secPr 문단) |
| h2_section | 42 | 60 | 15pt 굵게 | 왼쪽 170% | s2:2·15·83 | 장 첫 절 0, 나머지 pageBreak=1 (14/17) |
| h3_item | 42 | 36 | 14pt 굵게 | 왼쪽 170% | s2:40·63·85 | 15/33이 pageBreak=1(수동 나눔으로 판단) |
| h4_sub `1.` | 42 | 62 | 11pt 굵게 | 왼쪽 170% | s2:468·476·500 | 뒤에 빈 문단 없음 |
| body | 43 | 55 | 11pt | 양쪽 170% | s2:4·9·17 | 첫머리 U+0020 2칸, 들여쓰기 0 |
| table_caption | 52 | 55 | 11pt | 가운데 170%, keepWithNext=1 | s2:5·90·101 | **표 밖·표 위** |
| figure_caption | 52 | 55 | 11pt | 같음 | s2:30·48·269 | **그림 위** |
| source_note | 42 | 31 | **9pt** | 왼쪽 170% | s2:7·32·188 | `주)` → `자료:` 순 |
| toc_entry / toc_lot_entry | 44 | 54 | 11pt | 양쪽 170%, tabPr7 | s1:7·8·14 / 73·107 | 장 0칸·절 1칸·항 2칸 공백 |
| ref_heading | 4 | 56 | 16pt 굵게 | 가운데 180% | s2:538 | pageBreak=1 |
| ref_category | 11 | 32 | 13pt 굵게 | 양쪽 180% | s2:540·563·632 | 앞에 빈 문단(11/32) |
| ref_item | 47 | 64 | 11pt 자간 −2% | 양쪽 180%, 내어쓰기 | s2:541·564·633 | `[01]`부터 분류별 |
| appendix_heading | 58 | 12 | 16pt 굵게 | 가운데 170% | s2:652 | `부    록`, pageBreak=1 |
| abstract_heading | 4 | 56 | 16pt 굵게 | 가운데 180% | s2:694 | pageBreak=1 |
| abstract_meta | 25 | 55 | 11pt | 가운데 170% | s2:696·697·700·703 | |
| abstract_body | 43 | 55 | 11pt | 양쪽 170% | s2:705·706·711 | Keywords 행 없음 |
| blank_para | 43 | 55 | — | — | s2:1·3·37 | 빈 run `<hp:run charPrIDRef="55"/>` |

- **charPr 서명**(header.xml): 55=11pt bf3, 54=11pt bf2(목차), 56=16pt 굵게 bf2, 12=16pt 굵게 bf3, 60=15pt 굵게, 36=14pt 굵게, 62=11pt 굵게 bf8, 8=11pt 굵게 bf3(55와 굵게 외 동일), 31=9pt, 32=13pt 굵게, 64=11pt 자간−2, 16=10pt bf2(표 셀), 68=10pt 굵게 bf2(16과 굵게 외 동일), 51=9pt 장평79(밀도 표 예외), 63=9pt 굵게, 47=11pt 굵게 **#FF0000** bf2.
- **paraPr 핵심**: 43 양쪽170, 42 왼쪽170, 46 왼쪽170, 52 가운데170+keepWithNext, 25 가운데170, 44 양쪽170 tabPr7, 4 가운데180, 11 양쪽180, 47 양쪽180 들여쓰기 −2414(HwpUnitChar 분기)/−4828(default 분기), 58 가운데170, 49/50/51 왼쪽/가운데/오른쪽 130(표 셀). pageBreakBefore는 70개 paraPr 전부 0이다.
- **본문 굵게**: 본문 직계 run에서 굵은 11pt는 0건이다. `body_bold_charPr=8`은 55와 굵게 외 동일한 charPr을 고른 **추정값**이다.

### 목차 리더 탭 구조 (`snippets/toc_entry_example.xml`)

```xml
<hp:p paraPrIDRef="44" styleIDRef="0" pageBreak="0"><hp:run charPrIDRef="54">
  <hp:t> 제 1 절 연구의 배경 및 필요성<hp:tab width="19812" leader="3" type="2"/>1</hp:t>
</hp:run><hp:linesegarray>…</hp:linesegarray></hp:p>
```

- 탭이 `hp:t` **안**에 섞여 있다. `width`는 한글이 재계산하는 캐시다. tabPr7 = `RIGHT pos=36852 leader=DASH`(autoTabRight=1), 36852는 section1 본문 폭이다.
- 쪽수는 직접 입력한 텍스트다. 장 묶음 사이에 빈 문단(44/54)이 하나씩 있다. 표목차·그림목차 항목도 같은 44/54다.

### 앞부분 제목 상자 (신규 키 `front_heading_box`)

목차·표목차·그림목차·감사의글·논문개요 제목은 **2행×1열 무테 표**(tbl bf5, 셀 bf4=선 NONE, 폭 36284, treatAsChar=1, horzRelTo=COLUMN)다. 1행은 제목(paraPr10 가운데160 / charPr12 16pt 굵게), 2행은 높이 확보용 빈 문단(paraPr22 / charPr0). 앵커 문단은 s1:0·105가 paraPr25, s1:71이 24, s1:111이 45, s1:125가 27(styleIDRef=1)이며 s1:0 외에는 pageBreak=1이다. 제목 문자열은 `목  차`·`표 목 차`·`그 림 목 차`·`감사의 글`·`논 문  개 요`. 제목상자의 표 `pageBreak="CELL"`은 바꿔야 한다.

## 3. 표 구조 (`snippets/table_example.xml` = s2:102 <표 2-2>)

| 항목 | 실측 |
| --- | --- |
| 배치 | 표 제목 문단(52/55) → 표 앵커 문단(paraPr25/charPr16, 표 뒤 빈 `<hp:t/>`) → [`주)`] → `자료:`(42/31) → 빈 문단(42/31) → 설명 본문 |
| tbl | `numberingType=TABLE textWrap=TOP_AND_BOTTOM textFlow=BOTH_SIDES lock=0 repeatHeader=1 cellSpacing=0 borderFillIDRef=9 noAdjust=0`, 관찰 `pageBreak=CELL`(→ `NONE`으로) |
| pos | **`treatAsChar=0`**, flowWithText=1, vertRelTo=PARA, horzRelTo=PARA, vertAlign=TOP, horzAlign=LEFT, 오프셋 0 |
| 여백 | outMargin 141×4, inMargin·cellMargin 510/510/141/141(1.8/0.5mm), hasMargin=0 |
| 폭 | 본문 번호표 32개 중 31개 39684(140.0mm), <표 1-1>만 39118. 부록 설문 격자 39491 |
| 대표 격자 | colCnt 5, 열폭 [5260, 9056, 7260, 9054, 9054] 합 39684 = sz.width |
| 머리행 | 첫 행 전 셀 `header="1"`, borderFill 좌→우 **28 · 30… · 29**(#D9D9D9, 위 0.4mm, 바깥 좌우 개방) |
| 본문 행 | **7 · 5… · 6**(0.12mm, 첫 열 왼쪽·끝 열 오른쪽 개방). tbl 자체 bf9 = 위·아래 0.12mm |
| 셀 문단 | 50 가운데130(머리행) / 49 왼쪽130(설명) / 51 오른쪽130(수치). 양쪽정렬 셀 없음 |
| 셀 글자 | charPr16 10pt(머리행 포함, 굵게 아님). 밀도 표 s2:390·413·434만 51(9pt 79%)·63(9pt 굵게) |
| subList | vertAlign=CENTER, HORIZONTAL, lineWrap=BREAK |

### borderFill 팔레트

| id | 선 | 채움 | 용도 |
| --- | --- | --- | --- |
| 28 | 왼 NONE / 오·아래 0.12 / 위 0.4 | #D9D9D9 | 머리행 첫 열 |
| 30 | 좌우·아래 0.12 / 위 0.4 | #D9D9D9 | 머리행 가운데 |
| 29 | 오 NONE / 왼·아래 0.12 / 위 0.4 | #D9D9D9 | 머리행 끝 열 |
| 7 | 왼 NONE / 나머지 0.12 | — | 본문 첫 열 |
| 5 | 사방 0.12 | — | 본문 가운데 셀, 표지·도식 표 tbl |
| 6 | 오 NONE / 나머지 0.12 | — | 본문 끝 열 |
| 9 | 위·아래 0.12 | — | 본문 표 tbl |
| 4 / 10 | 전부 NONE | — | 제목상자 셀 / 표지 셀 |
| 11 | DOUBLE_SLIM 0.5 | — | 부록 안내 표 |
| 13–26 | 0.25/0.4 혼합 | 13만 #BBBBBB | 부록 설문 격자 전용 |
| 1·2·3·8 | NONE 0.1 | none/없음 | 문단·글자 기본 |

## 4. 그림 (`snippets/figure_example.xml` = s2:31)

- 순서: 캡션 s2:30(52/55, **그림 위**) → 그림 문단 s2:31(paraPr25/charPr55) → `자료: 연구자 작성.` s2:32(42/31) → 빈 문단.
- `hp:pic`: numberingType=PICTURE, textWrap=TOP_AND_BOTTOM, **treatAsChar=1**, horzRelTo=COLUMN, horzAlign=CENTER, sz.width 39684(본문 폭), `binaryItemIDRef="image1"` ↔ `content.hpf`의 `<opf:item id="image1" href="BinData/image1.png" …/>`.
- 실제 이미지 개체는 2개(image1, image2 s2:270). <그림 2-1>·<그림 2-2>는 문단과 1×N 표(tbl bf5)로 만든 도식이다.

## 5. 표지류 치환 슬롯 (`snippets/cover_section0.xml` = section0.xml 전체)

경로는 `cover.section0[].para_idx` 문단의 `tbl_run_idx`번 run 안 `tbl_idx`번 표 기준 `tbl/tr[i]/tc[j]/p[k]/run[m]`이다(s0:0은 한 run에 표 2개).

| 쪽 | 슬롯(역할: 경로, 현재 charPr) |
| --- | --- |
| 겉표지 s0:0 표0 (10×1, 폭36744) | 연월 `tr[0]/tc[0]/p[0]/run[0]` '2026'(28) + 기타 run[1] '학년도'(27) · 학위문구 `tr[0]…p[1]/run[0]`(17) · 제목 `tr[1]…p[0]/run[1]`(45, 22pt 자간−8) · 부제 `tr[1]…p[1]/run[0]`(61, 18pt) · 지도교수 `tr[3]`(18) · 대학원 `tr[5]`(20, 21pt) · 전공 `tr[7]`(19, 15pt) · 성명 `tr[9]`(21, 17pt) |
| 제출지 s0:0 표1 (11×1, 폭36742) | 제목 `tr[1]…run[1]` · 부제 `tr[1]…p[1]` · 학위문구 `tr[3]` '이 논문을 석사학위논문으로 제출함'(22) · 연월 `tr[4]` '2026년 12월  일'(23) · 대학원 `tr[6]` · 전공 `tr[8]` · 성명 `tr[10]` |
| 인준지 s0:1 (13×4, 열폭 10415/11636/12491/1634) | 성명 `tr[1]` '김 정 년의 석사학위논문을 인준함'(26) — 성명 부분만 교체 · 라벨 `tr[3~5]/tc[1]`(22, 배분정렬) · 심사위원 서명란 `tr[3~5]/tc[2]`(29, 공백) · 연월 `tr[9]` · 대학원 `tr[11]` |

빈 행(높이만 있는 셀)은 세로 위치 조정용이므로 그대로 둔다. 제목 셀 p[0]/run[0]은 빈 run이다. 성명·지도교수의 글자 사이 공백은 실제 공백 문자다.

## 6. 참고문헌 서식

- s2:538 `참고문헌`(4/56, pageBreak=1) → s2:539 빈 문단(11/32) → `가. 학위논문`(11/32) → 항목(47/64) … 분류 사이 빈 문단(11/32).
- 7분류: 가. 학위논문 · 나. 학술지 · 다. 보고서 · 라. 관련법 · 마. 기타 · 바. 국외 단행본 · 사. 국외 학술지. 분류마다 `[01]`부터 다시 번호.
- 항목 예(`snippets/ref_item_example.xml`): `[01] 저자(연도), “제목”, 대학교 대학원 박사학위논문`. 연도는 저자 바로 뒤 괄호.
- 내어쓰기는 paraPr47의 두 분기(−2414/−4828)가 서로 다르므로 수치를 새로 만들지 말고 47을 재사용한다.

## 7. 복제 금지 항목 (`template_leftovers_to_strip`)

| 항목 | 실측 | 처리 |
| --- | --- | --- |
| 빨간 안내문 | charPr47 문단 42개(s1:70·130, s2 40개) | 문단째 제거 |
| `[입력` 빈자리 | 73개 문단 | 김정년 내용과 함께 교체 |
| 밀도 표 9pt·장평79% | s2:390·413·434 | 기본 표 서식으로 쓰지 않음 |
| `pageBreak="CELL"` | 표 55개 중 51개 | NONE → 열폭 재배분 → TABLE+repeatHeader |
| 수동 목차 쪽수 | s1:2–69, 73–104, 107–110 | 재조판 후 인쇄 쪽수로 갱신 |
| 참고문헌 `*…*` 문자 | 24개 항목 | 서식이 아니라 문자 — 복제 금지 |
| 빨간 charPr 47 자체 | 11pt **굵게** bf2, 69와 색만 다름 | 재사용 금지. 본문 55 복제 + 색만 #FF0000 (표 셀은 16 복제) |

## 8. 옛 `style_map.json`(윤혁 260725 양식)과 달라지는 핵심

| # | 항목 | 옛 윤혁 양식 | 김정년 양식 |
| --- | --- | --- | --- |
| 1 | 표 제목 위치 | 표 첫 행 병합 셀 안, 굴림 10pt(charPr58)·bf13 | **표 밖·위 독립 문단** 52/55, 11pt 가운데, keepWithNext |
| 2 | 머리행 | 흰 바탕, header 플래그 없음 | **header="1" + #D9D9D9 + 위선 0.4mm**, bf 28/30/29 |
| 3 | 바깥 좌우선 | 셀 45/46으로 개방, tbl bf6 사방 | 본문 7/6·머리 28/29로 개방, **tbl bf9 위·아래만** |
| 4 | 표 배치 | treatAsChar=1 | **treatAsChar=0**, horzRelTo=PARA, 앵커 25/16 |
| 5 | 셀 서식 | paraPr75 가운데160, charPr7 | **50/49/51 (가운데/왼쪽/오른쪽 130%)**, charPr16 |
| 6 | 자료·주 | 본문 11pt 양쪽 | **9pt 왼쪽** 42/31, 뒤에 빈 문단 |
| 7 | 그림 캡션 | 그림 아래 31/62 | **그림 위** 52/55 |
| 8 | 목차 탭 | paraPr25(tabPr3 pos39684) 12pt, 장 항목 빨강 charPr116 | **paraPr44(tabPr7 pos36852) 11pt 170%**, 장·절·항 같은 charPr54, 공백 들여쓰기 |
| 9 | 참고문헌 | 전용 키 없음(5분류·번호 혼재) | **ref_heading 4/56 · ref_category 11/32 · ref_item 47/64**, 7분류 `[01]` |
| 10 | 전면부 범위 | 목차 s1 0–77 … 논문개요 110–111(제목만), 문단 112개 | **목차 0–70 · 표목차 71–104 · 그림목차 105–110 · 감사의글 111–124 · 논문개요 125–133**, 문단 134개 |
| 11 | 표지 슬롯 | s0 문단 3개(표지·제출서·인준서 각 1문단) | **s0 문단 2개** — s0:0 한 run에 표 2개, 슬롯 경로에 tbl_idx 필요 |
| 12 | 제목 문단 | 장 57/63, 절·항 paraPr51 양쪽 | 장 46/56, 절·항·소제목 **42 왼쪽**, 번호 `제 1 장`(띄어쓰기) |
| 13 | 본문 | 51/61 | **43/55** (charPr ID 체계 전면 변경 — 옛 ID 재사용 시 다른 서식을 가리킴) |

`header_counts`도 다르다: 옛 charPr 134·paraPr 115·borderFill 73·tabPr 9 → 김정년 70·70·30·8(style 40은 같다).

## 9. 조립기(Task H) 주의점

1. **ID 혼동 금지**: 옛 style_map ID를 그대로 쓰면 다른 서식이 된다(예: 옛 본문 charPr61 → 김정년 61은 18pt 자간−8 부제). 모든 ID를 `style_map_kjn.json`에서 읽는다.
2. **secPr 문단 보존**: s1:0·s2:0은 snippet 통째로 이식한다. s1의 newNum은 제목상자 표 셀 안에 있다.
3. **새 charPr 추가 시** header.xml `charProperties itemCnt`를 갱신한다. 빨간 마커는 55(본문)·16(표 셀) 복제본에 색만 바꾼다.
4. **표**: tbl_attrs.pageBreak는 `NONE`으로 시작한다(관찰값 CELL 금지). 첫 행 셀만 `header="1"`, 열 위치에 따라 28/30/29·7/5/6을 고른다. 1열 표는 좌우 모두 개방 셀이 필요한데 양식에 그런 borderFill이 없다(머리행: 좌우 NONE+위0.4+회색 / 본문: 위·아래만) — 필요하면 새 borderFill을 추가하고 보고한다(estimate).
5. **treatAsChar=0** 표는 앵커 문단 뒤에 오는 본문과의 배치를 재조판 PDF로 확인한다. 나눔이 필요하면 TABLE+repeatHeader.
6. **빈 줄**: 양식은 절·항 앞에 빈 줄이 없지만 저장소 규칙이 우선한다(이미 빈 줄이 있거나 pageBreak=1이면 생략).
7. **목차**: 탭은 `hp:t` 안 인라인 `<hp:tab width=… leader="3" type="2"/>`. width 캐시는 아무 값이나 넣고 linesegarray를 지워 한글이 재계산하게 한다.
8. **표지**: 인준지 성명 run은 '…의 석사학위논문을 인준함'까지 한 run이다. 성명만 바꾼다.
9. **김정년 내용 제거 확인**: 원제목·'김 정 년'·'안전시설물'·'떨어짐 사고위험'·'k2kim2002' grep 0건이 완료 조건이다(감사의글·논문개요·부록 안내 표·Abstract 메타 포함).

## 10. 추정으로 남긴 값

- `body_bold_charPr=8`(본문 굵은 run 미관찰), `table.cell_charPr.bold10=68`, `small9=31`(셀에서 미사용), `cell_paraPr.text_justify=49`(양쪽정렬 셀 없음).
- `h3_item.pageBreak_rule` — 항 제목 15/33의 pageBreak=1을 수동 나눔으로 해석.
- `ref_item` 내어쓰기 실제 적용값(두 분기 상이). 화면 결과는 분석 문서에서 PDF로 확인됐다.
