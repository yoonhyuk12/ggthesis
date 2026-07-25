# 08. 활용 가능한 Agent Skills

> 자동화 워크플로우 호출, 스킬 신규 탐색 시 로드하세요.

## write-academic-report (논문 작성 스킬)

`claude-skill-write-academic-report/SKILL.md` — 병렬 에이전트로 40~100+ 페이지 학술 논문을 자동 작성하는 Claude Code 스킬.

- **출력 포맷:** Markdown (.md) → HWP/DOCX/PDF 변환
- **3-Wave 파이프라인:**
  - Wave 0: 데이터 준비 (코드베이스 분석, 통계, 그림 생성) — 5~6 병렬 에이전트
  - Wave 1: 챕터 작성 (각 장을 동시에 Markdown으로 작성) — 3~4 병렬 에이전트
  - Wave 2: 조립 (병합, 교차참조 감사, 품질 검토) — 1~2 순차 에이전트
- **핵심 규칙:** 인용문 절대 환각 금지 — CrossRef/Semantic Scholar/OpenAlex 3개 DB 자동 검증
- **보조 스크립트:** `scripts/citation_checker.py` (인용 검증), `scripts/cross_ref_audit.py` (교차참조 감사)

## awesome-agent-skills (스킬 레퍼런스)

`awesome-agent-skills/README.md` — 70+ Agent Skills을 카탈로그화한 큐레이션 문서. 실제 스킬 구현체가 아닌 참조/발견용 리포지토리.

- Claude Code, Codex, VS Code, Gemini CLI 등 다중 플랫폼 호환 스킬 목록
- 공식 스킬(Claude, OpenAI, HuggingFace) + 커뮤니티 스킬 분류
- 새 스킬 탐색이나 구조 참고 시 활용
- 한국어 버전: `README.ko.md`
