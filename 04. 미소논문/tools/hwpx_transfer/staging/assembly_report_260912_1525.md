# 조립 리포트

- 양식: `00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx`
- style_map: `tools/hwpx_transfer/staging/style_map_miso.json`
- 출력: `C:\Users\User\Documents\2026 개발관련\03. 경기대 논문\04. 미소논문\tools\hwpx_transfer\staging\test_out\smoke.hwpx`
- 본문 문단 수: 866 (section2)
- 논문개요 문단 수: 6 (section1)
- 목차 항목: 94 (장 10)
- 표 목차 항목: 22 / 그림 목차 항목: 6
- 빨간 마커 run: 426
- 빨간 charPr 신규 복제: 0 

## 전면부 앵커 (style_map.front_matter)

- toc: 0
- lot: 106
- lof: 136
- thanks: [147, 171]
- abstract: [172, 173]

## 표지(section0) 치환

| section0 p | run | role | 기존 | 변경 |
| --- | --- | --- | --- | --- |
| 0 | 6 | title | 중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로 | 건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여 |
| 0 | 10 | name | 윤   혁 | 김 미 소 |
| 1 | 2 | title | 중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로 | 건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여 |
| 1 | 4 | date | 2026년 12월  일 | 2026년  월  일 |
| 1 | 7 | name | 윤   혁 | 김 미 소 |
| 2 | 1 | approval_title | 윤   혁의 석사학위논문을 인준함 | 김 미 소의 석사학위논문을 인준함 |
| 2 | 11 | date | 2026년 12월  일 | 2026년  월  일 |

- 치환 건수: 7

### 치환 후 표지 문단 텍스트

- section0 p0: 2026 학년도 석사학위논문 건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여 지도교수 : 박 종 용 경기대학교 공학대학원 건축ㆍ안전공학전공 김 미 소
- section0 p1: 건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여 이 논문을 석사학위논문으로 제출함 2026년  월  일 경기대학교 공학대학원 건축․안전공학전공 김 미 소
- section0 p2: 김 미 소의 석사학위논문을 인준함 심 사 위 원 장 인 심 사 위 원 인 심 사 위 원 인 2026년  월  일 경기대학교 공학대학원

## 그림 삽입 (BinData)

| 항목 id | ZIP 엔트리 | 원본 | px | HWPUNIT |
| --- | --- | --- | --- | --- |
| image1 | BinData/image1.png | 그림1-1_국가별사고사망만인율.png | 1393x860 | 35715x22049 |
| image2 | BinData/image2.png | 그림1-2_연구흐름도.png | 1796x768 | 35715x15272 |
| image3 | BinData/image3.png | 그림3-1_캐스케이드파이프라인.png | 2075x768 | 35715x13219 |
| image4 | BinData/image4.png | 그림3-2_LLM폴백흐름.png | 1641x1045 | 35715x22744 |
| image5 | BinData/image5.png | 그림3-3_양식자동채움모형.png | 1889x799 | 35715x15107 |
| image6 | BinData/image6.png | 그림4-1_실험설계모형.png | 1890x1261 | 35715x23829 |

## 메모

- 논문개요(--front)의 h1 '국문초록'는 제목 상자와 중복이라 넣지 않았다.
- references.json의 flagged 33건은 지시대로 본문에 넣지 않았다.
