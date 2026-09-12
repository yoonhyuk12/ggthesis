# TOC page mapping report

Resolved 132/132 entries: 96 headings, 28 tables, 8 figures. Unresolved: 0.

Base HWPX SHA256: `4beb9e5a422ec147f1d9e25d42dc6159876027d54c99efa1ec40df79548bdf97`

- PDF physical pages are 1-based. Physical13 is printed1 with suppressed visible folio. Every physical14..114 footer individually verified as printed2..102.
- TOC23/body290 starts physical35 (printed23) and continues physical36 (printed24); use heading start page. XML lineseg vertical reset independently confirms split.
- Repeated generic headings and appendix Parts A/B/C resolved by ordered XML and standalone PDF lines; no front matter or incidental prose references.
- TOC77 maps body1961: 도입 효과 비교 -> 도입 여부에 따른 집단 비교. TOC79 maps body1965: 도입 효과 차이 -> 집단 차이. Both uniquely numbered items in Chapter6 Section2; original TOC titles preserved.
- Whitespace normalized only for matching; all title strings retain original text and leading spaces.
- All table/figure entries identify actual captions, including nested cell paragraphs and figure captions with no image.
- Only page_map.json and mapping_report.md written; HWPX, PDF, dump and manuscripts not modified.

Nested table captions: 25/28. All 132 exact owned XML paragraph texts verified against the authoritative dump. PDF evidence records matching standalone lines and bounding boxes plus extracted printed labels. Matching within each kind follows increasing body paragraph and PDF position.

| TOC idx | Kind | Body idx | PDF physical | Printed | Title |
|---:|---|---:|---:|---:|---|
| 3 | heading | 0 | 13 | 1 | 제1장 서론 |
| 4 | heading | 2 | 13 | 1 | 제1절 연구의 배경 및 필요성 |
| 5 | heading | 4 | 13 | 1 | 제1항 중소규모 건설현장의 안전관리 현황과 선행연구의 한계 |
| 6 | heading | 16 | 15 | 3 | 제2항 연구의 필요성 및 차별성과 기대효과 |
| 7 | heading | 24 | 16 | 4 | 제2절 연구의 목적 |
| 8 | heading | 33 | 18 | 6 | 제3절 연구의 범위 및 방법 |
| 9 | heading | 42 | 20 | 8 | 제2장 이론적 배경 |
| 10 | heading | 44 | 20 | 8 | 제1절 스마트 건설 안전관리와 AI 영상관제 기술 |
| 11 | heading | 46 | 20 | 8 | 제1항 개념 및 정의 |
| 12 | heading | 54 | 22 | 10 | 제2항 국내·외 선행연구 |
| 13 | heading | 155 | 25 | 13 | 제3항 시스템 기술 특성 하위요인 |
| 14 | heading | 223 | 29 | 17 | 제2절 안전관리 실효성 |
| 15 | heading | 225 | 30 | 18 | 제1항 개념 및 정의 |
| 16 | heading | 231 | 30 | 18 | 제2항 국내·외 선행연구 |
| 17 | heading | 237 | 31 | 19 | 제3절 경보 피로도 |
| 18 | heading | 239 | 32 | 20 | 제1항 개념 및 정의 |
| 19 | heading | 246 | 32 | 20 | 제2항 국내·외 선행연구 |
| 20 | heading | 252 | 33 | 21 | 제4절 안전관리 예산 제약성 |
| 21 | heading | 254 | 33 | 21 | 제1항 개념 및 정의 |
| 22 | heading | 284 | 35 | 23 | 제2항 국내·외 선행연구 |
| 23 | heading | 290 | 35 | 23 | 제5절 스마트 안전기술 도입 효과 선행연구 고찰 (연구가설 도출 근거) |
| 24 | heading | 292 | 36 | 24 | 제1항 스마트 안전기술 도입 효과에 관한 국내·외 선행연구 |
| 25 | heading | 301 | 37 | 25 | 제2항 안전관리 예산 제약성과 도입 효과의 관계 |
| 26 | heading | 307 | 38 | 26 | 제3항 경보 피로도 완화와 시스템 효과의 작동 메커니즘 |
| 27 | heading | 312 | 38 | 26 | 제4항 선행연구 종합 및 본 연구의 차별성 |
| 28 | heading | 385 | 40 | 28 | 제6절 소결 |
| 29 | heading | 392 | 42 | 30 | 제3장 YOLO-LLM 하이브리드 안전관제 시스템 개발 |
| 30 | heading | 394 | 42 | 30 | 제1절 시스템 개발 개요 |
| 31 | heading | 400 | 43 | 31 | 제2절 요구사항 분석 |
| 32 | heading | 439 | 45 | 33 | 제3절 시스템 아키텍처 설계 |
| 33 | heading | 473 | 47 | 35 | 제4절 1차 검출 모듈 설계: 고민감도 YOLO 객체 탐지 |
| 34 | heading | 479 | 48 | 36 | 제5절 2차 검증 모듈 설계: LLM 기반 문맥 검증 |
| 35 | heading | 483 | 48 | 36 | 제1항 검증 필요성과 입출력 구조 |
| 36 | heading | 491 | 49 | 37 | 제2항 프롬프트 엔지니어링과 통합 판정 로직 |
| 37 | heading | 497 | 50 | 38 | 제3항 RAG 기반 Few-shot 현장 적응 |
| 38 | heading | 505 | 51 | 39 | 제6절 실시간 경보 전파 설계 |
| 39 | heading | 511 | 52 | 40 | 제7절 시스템 구현 |
| 40 | heading | 545 | 54 | 42 | 제8절 시스템 검증 및 성능평가 |
| 41 | heading | 549 | 54 | 42 | 제1항 검증 데이터셋 구축 및 평가 지표 |
| 42 | heading | 589 | 56 | 44 | 제2항 LLM 백업 검증의 오경보 감소 효과 |
| 43 | heading | 637 | 58 | 46 | 제3항 RAG 기반 Few-shot 교정의 성능 실험 |
| 44 | heading | 675 | 59 | 47 | 제4항 적용 타당성 |
| 45 | heading | 697 | 61 | 49 | 제9절 소결: 시스템 기술 특성의 도출과 실증연구의 필요성 |
| 46 | heading | 703 | 63 | 51 | 제4장 연구설계 |
| 47 | heading | 705 | 63 | 51 | 제1절 연구모형 설계 |
| 48 | heading | 736 | 65 | 53 | 제2절 연구문제 및 연구가설 |
| 49 | heading | 770 | 66 | 54 | 제3절 변수의 조작적 정의 및 측정도구 구성 |
| 50 | heading | 772 | 66 | 54 | 제1항 변수의 조작적 정의 |
| 51 | heading | 780 | 68 | 56 | 제2항 측정도구의 구성 및 설문문항 도출 출처 |
| 52 | heading | 829 | 70 | 58 | 제4절 설문조사 설계 및 척도 검증 |
| 53 | heading | 831 | 70 | 58 | 제1항 설문조사의 개요 및 절차 |
| 54 | heading | 839 | 70 | 58 | 제2항 변수별 설문문항 요약 |
| 55 | heading | 980 | 74 | 62 | 제3항 본 설문지의 최종 구성 |
| 56 | heading | 1041 | 74 | 62 | 제5절 자료수집과 분석방법 |
| 57 | heading | 1043 | 74 | 62 | 제1항 데이터 수집 표본 설계 |
| 58 | heading | 1072 | 77 | 65 | 제2항 분석절차 |
| 59 | heading | 1088 | 79 | 67 | 제5장 실증분석 결과 |
| 60 | heading | 1091 | 79 | 67 | 제1절 조사대상자의 인구통계학적 특성 |
| 61 | heading | 1288 | 79 | 67 | 제2절 측정도구의 신뢰도 및 타당도 검증 |
| 62 | heading | 1392 | 83 | 71 | 제3절 기술통계 및 집단 동질성 검증 |
| 63 | heading | 1394 | 83 | 71 | 제1항 주요 변수의 기술통계 |
| 64 | heading | 1513 | 84 | 72 | 제2항 두 집단의 사전 특성 동질성 검증 |
| 65 | heading | 1583 | 84 | 72 | 제4절 가설 검정: 공분산분석(ANCOVA) |
| 66 | heading | 1585 | 85 | 73 | 제1항 공분산분석 가정 점검 |
| 67 | heading | 1673 | 87 | 75 | 제2항 안전관리 실효성에 대한 공분산분석 |
| 68 | heading | 1783 | 88 | 76 | 제3항 안전관리 실효성 하위영역별 공분산분석 |
| 69 | heading | 1840 | 89 | 77 | 제5절 탐색적 보조 분석 |
| 70 | heading | 1843 | 90 | 78 | 제1항 집단과 안전관리 예산 제약성의 상호작용 분석 |
| 71 | heading | 1914 | 91 | 79 | 제6절 연구결과 및 논의 |
| 72 | heading | 1916 | 91 | 79 | 제1항 연구결과 종합 |
| 73 | heading | 1941 | 92 | 80 | 제2항 논의 |
| 74 | heading | 1950 | 94 | 82 | 제6장 결론 |
| 75 | heading | 1952 | 94 | 82 | 제1절 연구결과의 요약 |
| 76 | heading | 1959 | 94 | 82 | 제2절 논의 |
| 77 | heading | 1961 | 95 | 83 | 1. AI 관제 시스템 도입 효과 비교 결과에 관한 논의 [DATA PENDING] |
| 78 | heading | 1963 | 95 | 83 | 2. 안전관리 실효성 하위영역 비교 결과에 관한 논의 [DATA PENDING] |
| 79 | heading | 1965 | 95 | 83 | 3. 예산 제약성에 따른 도입 효과 차이에 관한 탐색적 논의 [DATA PENDING] |
| 80 | heading | 1967 | 95 | 83 | 제3절 시사점 |
| 81 | heading | 1970 | 95 | 83 | 1. 실무적 시사점 |
| 82 | heading | 1975 | 96 | 84 | 2. 학술적 시사점 |
| 83 | heading | 1980 | 97 | 85 | 3. 정책적 시사점 |
| 84 | heading | 1985 | 97 | 85 | 제4절 연구의 한계 |
| 85 | heading | 1996 | 100 | 88 | 제5절 향후 연구방향 |
| 86 | heading | 2004 | 101 | 89 | 참고문헌 |
| 87 | heading | 2043 | 104 | 92 | 부 록 (도입 현장) |
| 88 | heading | 2063 | 105 | 93 | Part A. 인구통계학적 특성 |
| 89 | heading | 2084 | 106 | 94 | Part B. 안전관리 실효성 |
| 90 | heading | 2174 | 107 | 95 | Part C. 안전관리 예산 제약성 |
| 91 | heading | 2236 | 108 | 96 | 도입 현장 전용부 |
| 92 | heading | 2237 | 108 | 96 | Part D. 시스템 특성 인식 |
| 93 | heading | 2326 | 109 | 97 | Part E. 경보 피로도 완화 |
| 94 | heading | 2389 | 110 | 98 | 부 록 (미도입 현장) |
| 95 | heading | 2409 | 111 | 99 | Part A. 인구통계학적 특성 |
| 96 | heading | 2430 | 112 | 100 | Part B. 안전관리 실효성 |
| 97 | heading | 2520 | 113 | 101 | Part C. 안전관리 예산 제약성 |
| 98 | heading | 2584 | 114 | 102 | Abstract |
| 102 | table | 62 | 24 | 12 | <표 2-1> 시스템 기술 특성 하위요인 도출 매트릭스 |
| 103 | table | 168 | 27 | 15 | <표 2-2> 단일 YOLO 구조와 YOLO-LLM 캐스케이드 구조의 비교 |
| 104 | table | 189 | 29 | 17 | <표 2-3> 하위요인 관련 선행연구 요약 |
| 105 | table | 260 | 34 | 22 | <표 2-4> 상용 AI 관제 시스템과 본 연구 대상 시스템의 비용 비교 |
| 106 | table | 316 | 39 | 27 | <표 2-5> 스마트 안전기술 도입 효과 선행연구 종합 |
| 107 | table | 363 | 40 | 28 | <표 2-6> 선행연구와 본 연구의 차별성 |
| 108 | table | 408 | 45 | 33 | <표 3-1> 중소규모 건설현장 제약과 시스템 기능·비기능 요구사항 |
| 109 | table | 446 | 46 | 34 | <표 3-2> 시스템 모듈 구성과 역할 |
| 110 | table | 515 | 53 | 41 | <표 3-3> 시스템 구현 기술 스택 |
| 111 | table | 554 | 55 | 43 | <표 3-4> 정·오탐 라벨링 기준(혼동행렬 정의; 이기수, 2024) |
| 112 | table | 566 | 56 | 44 | <표 3-5> 성능평가 지표 정의와 측정 목적 |
| 113 | table | 594 | 57 | 45 | <표 3-6> 1차 단독 대 2단계 파이프라인 성능 비교(n=878, 196.8시간, 38대 카메라) |
| 114 | table | 641 | 58 | 46 | <표 3-7> 제로샷·고정-k·RAG의 성능 비교(n=202, 6개 카메라) |
| 115 | table | 680 | 59 | 47 | <표 3-8> 상용 솔루션 대비 첫해 도입 비용(TCO) 비교(단위: 만 원) |
| 116 | table | 714 | 64 | 52 | <표 4-1> 연구변수의 구성 |
| 117 | table | 755 | 66 | 54 | <표 4-2> 연구가설 종합 |
| 118 | table | 785 | 69 | 57 | <표 4-3> 변수의 조작적 정의와 측정도구의 구성 |
| 119 | table | 984 | 75 | 63 | <표 4-4> 설문지의 최종 구성 |
| 120 | table | 1050 | 77 | 65 | <표 4-5> 자료수집 개요 |
| 121 | table | 1095 | 80 | 68 | <표 5-1> 조사대상의 인구통계학적 특성 (집단별) |
| 122 | table | 1292 | 81 | 69 | <표 5-2> 측정도구의 신뢰도 검증 결과 |
| 123 | table | 1398 | 83 | 71 | <표 5-3> 주요 변수의 기술통계 (집단별) |
| 124 | table | 1517 | 85 | 73 | <표 5-4> 두 집단의 사전 특성 동질성 검증 결과 |
| 125 | table | 1590 | 86 | 74 | <표 5-5> 공분산분석 가정 점검 결과 (독립성·정규성·등분산성·회귀기울기 동질성) |
| 126 | table | 1676 | 87 | 75 | <표 5-6> 안전관리 실효성에 대한 공분산분석 결과 (조정 평균 포함) |
| 127 | table | 1787 | 89 | 77 | <표 5-7> 하위영역별 공분산분석 결과 |
| 128 | table | 1846 | 90 | 78 | <표 5-8> 탐색적 보조 분석 결과 |
| 129 | table | 1920 | 92 | 80 | <표 5-9> 연구가설 검증 결과 종합 |
| 134 | figure | 7 | 13 | 1 | <그림 1-1> 산업별 업무상사고 사망재해 분포도 |
| 135 | figure | 9 | 13 | 1 | <그림 1-2> 연도별 업무상사고 사망재해 추이 |
| 136 | figure | 39 | 19 | 7 | <그림 1-3> 연구의 흐름도 |
| 137 | figure | 442 | 46 | 34 | <그림 3-1> YOLO-LLM 이중 캐스케이드 시스템 아키텍처 |
| 138 | figure | 487 | 49 | 37 | <그림 3-2> LLM 2차 검증 입출력 구조와 판정 흐름 |
| 139 | figure | 501 | 51 | 39 | <그림 3-3> RAG 기반 Few-shot 교정 절차 |
| 140 | figure | 542 | 54 | 42 | <그림 3-4> 시스템 운영 화면(AI CCTV Viewer) |
| 141 | figure | 734 | 64 | 52 | <그림 4-1> 연구모형 |
