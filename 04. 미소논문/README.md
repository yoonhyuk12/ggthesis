# 04. 미소논문 — 김미소 석사학위논문 hwpx 작성 작업 영역

2026-09-12 개설. 윤혁 논문의 MD→hwpx 조립 파이프라인을 복사해 미소 논문(건설현장 불시·단발성 작업 위험성평가 AI 자동생성 시스템 개발 및 효과성 분석: LLM-RAG 기법을 활용하여)을 같은 학교 양식으로 조립한다.

| 경로 | 역할 |
|---|---|
| `01.docs/` | 미소 MD 원고 **스냅샷**(원본: `11. 미소논문/0. 논문작성 템플릿/2. 논문 작성/`, 2026-09-12 14:22 복사) + `그림/*.png`. 원고가 바뀌면 다시 복사한다 |
| `00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx` | 양식(윤혁 최신본 사본, 읽기 전용). 산출물은 `YYMMDD_HHMM_미소논문.hwpx`(Asia/Seoul), 접두사가 가장 큰 파일이 최신본 |
| `tools/hwpx_transfer/` | 조립 파이프라인(미소용 개조판). `md_to_blocks.py` → `blocks_to_hwpx.py --style-map staging/style_map_miso.json` |
| `tools/hwpx_transfer/analysis/` | 양식 XML 추출본·문단 덤프 JSON·스타일 실측 기록 |
| `qa/` | 감사 보고서(목차 정합·MD 린트·인용 대조) |
| `03.plan/` | 워커 브리프. 메인 계획은 상위 `03.plan/260912_1422_미소논문_hwpx작성_오케스트레이션.md` |

규칙은 상위 저장소 CLAUDE.md의 hwpx 규칙(MD 먼저 → hwpx, 원본 불변, 한글이 열어야 완료, 빨간 마커, 타깃 치환)을 그대로 따른다.

## 현재 상태 (2026-09-12)

- 최신 수정본 `00. hwpx/260912_1825_미소논문_표열폭조정_점선목차.hwpx` (125쪽). 45표 감사 후 28표 열폭을 내용·줄수에 맞춰 배분하고 긴 2표를 반복 머리행과 함께 행 단위로 나눴다. 본문·서론·그림·마커 보존 및 목차 115항목 쪽번호 대조 완료. 원래 113쪽 문제 표는 현재 인쇄 108쪽. 검증: `tools/hwpx_transfer/staging/table_fit_260912/completion.json`.

- 이전 서론 수정본 `00. hwpx/260912_1802_미소논문_서론반영_점선목차.hwpx` (129쪽). 승인된 MD 서론을 부분 반영하고 일반·표·그림 목차 115항목에 점선과 실제 표시 쪽번호를 넣었다. 한글 Open·재저장 및 번호 전수 대조 완료. 기존 부록 설문 양식·그림·후속 장 내용과 원본 파일은 보존했다. 검증 기록: `tools/hwpx_transfer/staging/intro_toc_260912/completion.json`.
- 연구목적 5문단은 현행 양식의 본문 6~7쪽에 걸쳐 배치된다. MD는 이 작업영역에서 직접 수정되었으므로 외부 원본 스냅샷을 다시 복사할 때 승인 수정분을 덮어쓰지 않도록 대조한다.

- 이전 조립 기준본 `00. hwpx/260912_1613_미소논문.hwpx` (128쪽, 한컴 Open=True 검증; 부록 설문 표는 윤혁 설문 틀 클론, guide 문단 제외). 검증 기록 `tools/hwpx_transfer/staging/test_out/verify_report.md`·`verify_report_w7.md`, 조립기 변경 요약 `tools/hwpx_transfer/analysis/assembler_changes.md`.
- 재조립: `PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/md_to_blocks.py` → `blocks_to_hwpx.py --template "00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx" --style-map staging/style_map_miso.json --front staging/front.blocks.json --cover staging/cover_miso.json --blocks staging/ch01..ch06,apx1,apx2 --references staging/references.json --survey-layout staging/survey_layout.json --output "00. hwpx/YYMMDD_HHMM_미소논문.hwpx"`. 한글에서 직접 고친 내용이 쌓이기 시작하면 전체 재조립 대신 타깃 치환으로 전환한다.
- 감사 보고서: `qa/toc_audit.md`, `qa/md_lint.md`, `qa/citation_crosscheck.md`, `qa/md_normalize_report.md`.
- 렌더 규칙: `guide:true` 문단(`> …` 인용구 집필 안내)은 hwpx에 넣지 않는다(`--keep-guide`로만 복원). 대괄호 마커 6종만 빨간 글자.
