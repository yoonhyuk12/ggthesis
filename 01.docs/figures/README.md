# 논문 삽입용 그림

2026-09-12 제작. 당시 `01.docs/` 원고를 기준으로 만든 도식 5개, 공식 통계 도표 2개, 기존 학회논문에서 추출한 실제 운영 화면 1개다.

> **현행 원고 안내(2026-10-03):** 아래 번호와 연구 도식 파일은 제작 당시 기록이다. 현행 연구 흐름도는 [제1장](../01_서론.md)의 그림 1-1 Mermaid 도식이며, 연구 모형의 기준은 [제4장](../04_연구설계.md)이다. 현장당 1명·총 60명, 연속 공변량 2개·범주형 요인 4개의 ANCOVA 및 일반선형모형을 따른다. 과거 연구 도식 PNG·SVG에는 당시 표본·분석 설명이 남아 있으므로 현행 도식으로 사용하지 않는다.

| 번호 | 그림 | 삽입용 PNG | 편집용 SVG |
|---|---|---|---|
| 1-1 | 산업별 업무상사고 사망재해 분포도 | [PNG](evidence/assets/fig_1_1_industry_fatalities_2024.png) | [SVG](evidence/assets/fig_1_1_industry_fatalities_2024.svg) |
| 1-2 | 연도별 업무상사고 사망재해 추이(2020–2024) | [PNG](evidence/assets/fig_1_2_construction_fatalities_2020_2024.png) | [SVG](evidence/assets/fig_1_2_construction_fatalities_2020_2024.svg) |
| 1-1 | 연구의 흐름도 | [PNG](research/figure_1-1_research_flow.png) | [SVG](research/figure_1-1_research_flow.svg) |
| 3-1 | YOLO-LLM 이중 캐스케이드 시스템 아키텍처 | [PNG](system/fig_3_1_architecture.png) | [SVG](system/fig_3_1_architecture.svg) |
| 3-2 | LLM 2차 검증 입출력 구조와 판정 흐름 | [PNG](system/fig_3_2_llm_verification.png) | [SVG](system/fig_3_2_llm_verification.svg) |
| 3-3 | RAG 기반 Few-shot 교정 절차 | [PNG](system/fig_3_3_rag_correction.png) | [SVG](system/fig_3_3_rag_correction.svg) |
| 3-4 | 시스템 운영 화면(AI CCTV Viewer) | [실제 화면 PNG](evidence/assets/fig_3_4_viewer_original.png) | 해당 없음 |
| 4-1 | 연구 모형 | [PNG](research/figure_4-1_research_model.png) | [SVG](research/figure_4-1_research_model.svg) |

한글에는 PNG를 가로 150 mm, 원본 비율 유지, 글자처럼 취급으로 삽입한다. 그림 번호와 캡션은 이미지 아래에 둔다. 도식 PNG는 300 dpi이며 SVG에는 편집 가능한 한글 텍스트가 들어 있다. SVG 편집 시 맑은 고딕 글꼴을 사용한다.

## 근거 및 한계

- [통계·운영 화면 근거](evidence/report.md): 산업재해 현황분석의 산재보상 승인자료 계열을 사용했다. 추이의 2020–2024년 건설업 사망자는 458·417·402·356·328명이다. 통계 대상연도와 책자 발행연도를 구분했다.
- [연구 도식 근거](research/report.md): 2026-09-12 당시 ANCOVA 모형의 제작 기록이며 H2 상호작용을 보조 분석으로 구분했다. 현행 조사 조건과의 차이는 해당 보고서 첫머리 안내를 따른다. 결과 수치를 생성하지 않았다.
- [시스템 도식 근거](system/report.md): 연구 원고에 기술된 구성을 표현한다. 외부 최신 프로그램 작업본과 연구 당시 버전의 정합은 별도 확인 사항이다.
- 운영 화면은 합성하지 않았다. 기존 학회논문의 실제 다중 카메라·LLM 판정 교정 장면이며 동적 위험구역 폴리곤과 위험 팝업이 모두 표시된 화면으로 주장하지 않는다.

생성 스크립트와 출처 데이터는 각 하위 폴더에 있다. 한글 삽입·재조판·목차·원본 보존 검증 자료는 `tools/hwpx_transfer/staging/figures_260912/`에 있다.
