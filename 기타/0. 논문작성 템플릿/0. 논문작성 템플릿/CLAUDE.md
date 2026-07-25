# CLAUDE.md

> **처음 설정하는 PC라면.** `.claude/skills/`가 비어 있거나 `.mcp.json`의 경로가 이 PC와 다르면 아직 초기 설정 전이다. 프로젝트 루트의 `시작하기.md`를 읽고 `setup.ps1`을 먼저 실행하라(스킬 정션 113개 재생성, hwpx MCP 가상환경 생성, `.mcp.json` 경로 갱신, 전역 CLAUDE.md 설치).

## 박종용 교수님 논문작성요령 — 논문 작성 최우선 지침

지도교수(박종용 교수님)의 논문작성요령 전문이 `3. 기타/박종용교수님_논문작성요령20260707.md`에 있다(원본은 같은 이름의 .hwpx). **논문 원고를 작성·수정·검토할 때는 이 지침을 다른 일반 지침보다 우선 적용하고, 작업 시작 전에 전문을 반드시 읽어라.** 장별 상세 템플릿(서론 절 구성, 문헌고찰 변수별 기술순서, 심사위원 예상 질문, 결론 5요소)과 세컨오더 팩터 4대 판단 기준은 전문에만 있다.

항상 지켜야 할 핵심 규칙.
- 작성 순서는 3장 → 2장 → 1장 → 4장 → 5장이며, 서론은 뒷장을 쓰면서 계속 수정한다.
- 두괄식으로 쓴다. 문단 하나에 주제어 하나, 문장은 3~5줄 이내, 동일 표현 반복 자제, 주어-서술어 일치.
- 능동형으로 서술한다. "보여진다"가 아니라 "보인다", "해석되어진다"가 아니라 "해석할 수 있다".
- 장이 끝날 때 다음 장으로 잇는 연결 길잡이 문장을 넣는다.
- 직접 인용은 5줄 이하, 짜깁기 금지. 내용을 이해한 뒤 핵심어구를 재조합하고 자기 논평·부연을 덧붙인다.
- 출처는 성실히 표기한다. 내주는 (이름, 연도; 이름, 연도), 국내연구자;국외연구자 순. 인용 위계는 국외학술지 > 국내학술지 > 박사학위논문.
- 선행연구는 경기대학교 박사졸업 논문과 안전문화학회 투고 논문을 인용한다. 양식은 경기대 박사학위 논문 양식.
- 논문 전체 흐름은 Why(왜 연구했나) → How(어떻게 연구했나) → What(무엇을 발견했나) → 발견한 의미이며, 심사 방어의 답은 논문 본문에 기술된 내용으로 제시할 수 있어야 한다.
- 통계는 jamovi 구조방정식(SEM). 인과관계 3대 조건(공변성, 시간적 우선성, 통제)을 논증하고, 통제변수는 이론적 근거와 함께 모형에 투입하되 분석 후 해석하지 않는다.

## 내 박사학위논문 — 주제와 작업 방식

> **[템플릿 — 아직 비어 있음]** 이 섹션은 초기 설정 인터뷰로 채운다(`시작하기.md`의 "프롬프트 2" 절차). 인터뷰로 확인할 항목: 연구자 이름, 논문 제목(가제), 대학원·학과, 지도교수, 연구모형(외생·매개·내생 변수와 하위요소), 연구문제와 가설 목록, 조사 방법(설문 대상·표본 규모·분석 도구), 목표 일정. 섹션을 채운 뒤에는 이 안내 블록을 삭제하라.

### 논문 개요
- 제목: (초기 설정 시 작성)
- 소속·연구자·지도교수: (초기 설정 시 작성)
- 연구모형: (초기 설정 시 작성)
- 연구문제·가설: (초기 설정 시 작성)
- 조사·분석 방법: (초기 설정 시 작성)

### 작업 위치와 원고 파일
**논문 작성·수정은 `2. 논문 작성/`의 장별 마크다운 파일에서 한다(작업 원고 = md).** hwpx 반영은 사용자가 명시적으로 "hwpx에 옮겨 달라"고 요청할 때만 수행하고, 그 전에는 md만 수정한다.

초기 설정 시 아래 뼈대 파일을 `2. 논문 작성/`에 생성한다. 각 파일에는 박종용 교수님 논문작성요령에 맞는 절 구성과 작성 가이드를 넣는다.

| 파일 | 내용 |
|---|---|
| `00.목차.md` | 표지, 목차, 논문개요(국문초록) |
| `01.서론.md` | 제1장: 연구 배경·필요성 / 목적 / 범위·방법 |
| `02.문헌고찰.md` | 제2장: 이론적 근거 / 변수별 문헌고찰 / 선행연구 |
| `03.연구방법.md` | 제3장: 연구모형 / 연구문제·가설 / 조작적 정의·측정도구 / 설문조사 / 분석절차 |
| `04.분석결과.md` | 제4장: 인구통계 / 요인분석·타당성 검증 / 기술통계·상관관계 / 구조모형 분석·가설검증 / 소결 |
| `05.결론.md` | 제5장: 결론(요약, 시사점, 한계, 후속연구 제언) |
| `06.부록.md` | 설문지 등 부록 |
| `07.참고문헌.md` | 참고문헌 목록 |

### 레퍼런스 자료 (본문 주장·인용의 근거)
논문에 활용하는 근거 자료(PDF 등)는 사용자가 `1. 레퍼런스 자료/`에 넣는다.

- 자료가 들어오면 `1. 레퍼런스 자료/00. 레퍼런스 논문 종합 요약.md`를 만들어 진입점으로 삼는다. 자료별 서지·방법·핵심 수치, 뒷받침하기 좋은 주장과 인용 위치(PDF 페이지 기준), 문서 간 공통 결론·차이·연구 공백, 인용 시 주의사항(표본 편향, 자기보고, 수치 불일치 등)을 정리한다. 이후 원문 PDF를 열기 전에 이 요약부터 읽어라.
- 요약의 페이지 번호는 PDF 뷰어 표시 기준이며 문서 내 인쇄 쪽수와 다를 수 있다. 법령·고시·금액 기준은 작성 당시 내용이므로 인용 전에 최신 원문을 재확인한다(`mark-unverified` 규칙 적용).

## 모델 역할 분담: Advisor / Worker

너는 Advisor다. 판단에 집중하고, 구현 노동은 Worker에게 위임하라.

적용 범위 — 실행 도구에 따라 다르다.
- **Worker를 Opus 모델로 지정하는 방식은 Claude Code(클로드 모델)에서만 가능하다.**
- Gemini CLI, Codex(GPT) 등 다른 도구가 이 지침을 읽는 경우, 모델 지정은 무시하고 동일 모델 안에서 업무 분담만 유지하라. 서브에이전트·병렬 실행 기능이 있으면 같은 모델로 위임하고, 없으면 Advisor의 판단 단계와 Worker의 구현 단계를 순서대로 직접 수행하라.

Advisor(너, 메인 세션)가 직접 하는 일:
- 요구사항 분석, 작업 분해, 설계 결정
- Worker에게 줄 작업 브리프 작성
- 결과 검증: diff 직접 확인, 테스트 직접 실행
- 최종 커밋 승인, 사용자 보고

Worker에게 위임하는 일:
- 코드 작성과 수정, 테스트 작성 등 구현 작업 전부
- Claude Code에서는 Agent 도구로 위임하고 model은 "opus"를 지정한다 (클로드 전용)
- 서로 독립적인 작업은 병렬로 위임한다

브리프 기준:
- 네가 이미 파악한 컨텍스트를 담아 Worker가 재탐색하지 않게 하라
- 파일 경로, 프로젝트 컨벤션, 알려진 함정, 완료 기준(통과해야 할 테스트)을 포함하라

경계:
- Worker의 완료 보고를 그대로 믿지 마라. diff와 테스트로 직접 확인한 뒤 승인하라
- 검증 실패는 수정 브리프로 재위임하라. 직접 수정은 사소한 마무리에만 허용된다
- 한두 줄 수정처럼 위임 오버헤드가 더 큰 작업은 직접 처리해도 된다

## Academic Research Skills (ARS) v3.15.0

학술 연구·논문 작성·피어리뷰 전용 스킬 모음이 이 프로젝트에 설치되어 있다.

설치 구조.
- 원본 저장소 전체: `academic-research-skills/` (git clone, `git pull`로 업데이트)
- 스킬 등록: `.claude/skills/` 의 4개 정션(junction)이 저장소의 스킬 폴더를 가리킨다
- 슬래시 명령: `.claude/commands/ars-*.md` 16개
- 스킬이 참조하는 공용 규약(`shared/`)과 검증 스크립트(`scripts/`)는 저장소 폴더 안에 있다. 스킬 문서가 `shared/...`, `scripts/...` 경로를 언급하면 `academic-research-skills/` 아래에서 찾아라

### 4개 스킬

| 스킬 | 용도 | 주요 모드 |
|------|------|-----------|
| `deep-research` | 13-에이전트 리서치 팀. 문헌 조사, 팩트체크, 체계적 문헌고찰 | full, quick, socratic, lit-review, fact-check, systematic-review |
| `academic-paper` | 12-에이전트 논문 작성. 초안, 개정, 초록, 인용 검증, 포맷 변환 | full, plan, outline-only, revision, revision-coach, abstract-only, citation-check |
| `academic-paper-reviewer` | 다관점 피어리뷰(리뷰어 5인 패널) | full, re-review, quick, methodology-focus, guided |
| `academic-pipeline` | 전체 파이프라인 오케스트레이터 (연구→작성→무결성 검사→리뷰→개정→최종화) | 위 스킬 전체 조율 |

### 사용 시나리오별 라우팅

- 막연한 연구 아이디어를 연구 질문으로 다듬기 → `deep-research` socratic 모드
- 빠른 문헌 요약 → `deep-research` quick 모드
- PRISMA 체계적 문헌고찰 → `deep-research` systematic-review 모드
- 논문 처음부터 작성 → `academic-paper` full 모드 (장별 계획부터 하려면 plan 모드)
- 논문 리뷰 받기 → `academic-paper-reviewer` full 모드 (대화형 학습은 guided 모드)
- 리뷰어 코멘트만 있고 답변서가 없으면 → `academic-paper` revision-coach. 코멘트+답변서 초안이 둘 다 있으면 → rebuttal-audit
- 연구→작성→리뷰→개정→출판 전 과정 → `academic-pipeline` ("완성된 논문을 만들고 싶다"고 하면 10단계 파이프라인 가동, 2~4시간 소요)
- 단일 기능만 필요하면 pipeline을 거치지 말고 해당 스킬을 직접 호출하라

상세 라우팅 규칙(교차 단계 자료 처리, 명확화 프로토콜 등)은 `academic-research-skills/.claude/CLAUDE.md`의 "Routing Discipline" 섹션을 따른다.

### 슬래시 명령 (16개)

`/ars-full`(논문 전체 작성), `/ars-plan`(장별 계획), `/ars-outline`(개요), `/ars-abstract`(초록), `/ars-lit-review`(문헌 리뷰), `/ars-3w`(3단계 리서치), `/ars-reviewer`(피어리뷰), `/ars-revision`(개정), `/ars-revision-coach`(개정 코칭), `/ars-rebuttal-audit`(반박문 검수), `/ars-citation-check`(인용 검증), `/ars-format-convert`(포맷 변환), `/ars-disclosure`(AI 사용 공개문), `/ars-mark-read`·`/ars-unmark-read`(읽음 표시), `/ars-cache-invalidate`(인용 캐시 무효화)

### 핵심 원칙

- 모든 주장에 인용 필수. 증거 위계 준수(메타분석 > RCT > 코호트 > 사례 보고 > 전문가 의견)
- 인용 실재 여부는 4개 색인(Semantic Scholar·OpenAlex·Crossref·arXiv) 교차 검증으로 확인
- 모순되는 증거는 품질 비교와 함께 공개. 모든 보고서에 AI 사용 공개(disclosure) 포함
- 출력 언어는 사용자 입력 언어를 따른다 (이 프로젝트에서는 한국어)

## claude-research 연구 인프라 (flonat/claude-research)

학술 연구자용 Claude Code 인프라(스킬 109개 + 에이전트 15개 + 규칙 18개)가 설치되어 있다. ARS가 "논문 생산 파이프라인"이라면, 이것은 문헌 관리·논문 품질 검수·연구 재현성 등 개별 작업 도구 모음이다.

설치 구조.
- 원본 저장소: `claude-research/` (git clone, `git pull`로 업데이트)
- 스킬: `.claude/skills/`의 정션 109개가 저장소 `skills/`를 가리킨다. 스킬 문서가 `skills/shared/...`를 참조하면 `claude-research/skills/shared/`에서 찾아라
- 에이전트: `.claude/agents/`에 15개 (Agent 도구의 subagent_type으로 사용)
- 규칙: `.claude/rules/`에 18개 — 대부분 `paths:` 글롭으로 스코프되어 해당 파일(.tex, .bib 등) 작업 시에만 적용된다

### 주요 스킬 (용도별)

- 문헌·서지 관리: `/literature`(문헌 탐색·종합), `/gather-readings`, `/bib-validate`(cite 키 대조), `/bib-parse`, `/bib-coverage`, `/review-cluster`
- 논문 품질 검수(읽기 전용 감사): `/proofread`(11개 범주 교정), `/weakness-scanner`, `/devils-advocate`, `/grill-me`(구두 심사 모의), `/multi-perspective`, `/method-audit`, `/pre-submission-report`(제출 전 종합 점검)
- 리뷰 대응·재투고: `/review-response`, `/synthesise-reviews`, `/strategic-revision`, `/retarget-journal`, `/venue-fork`
- LaTeX 전용: `/latex-scaffold`, `/latex-polish`, `/latex-health-check`, `/latex-diff`, `/tikz`, `/beamer-deck`, `/camera-ready`, `/preprint` (LaTeX을 쓰지 않으면 무시)
- 연구 설계·재현성: `/experiment-design`, `/causal-design`, `/preregister`, `/replication-audit`, `/replication-package`, `/numerical-check`, `/verify-math`
- 문서 변환: `/docx`, `/xlsx`, `/pdf`, `/split-pdf`
- 프로젝트·세션 관리: `/init-project-research`, `/checkpoint`, `/handoff`, `/session-close`, `/save-context`

전체 목록은 `claude-research/docs/skills.md` 참조.

### 주요 에이전트 (Agent 도구로 호출)

`peer-reviewer`(타인 논문 리뷰), `referee2-reviewer`(적대적 심사), `paper-critic`(LaTeX 논문 감사), `proposal-reviewer`(연구계획서 리뷰), `claim-verify`(인용 주장이 원문과 일치하는지 검증), `domain-reviewer`, `fatal-error-check`, `blindspot`, `fixer`(비평 보고서 기반 수정 실행), `reproducibility-auditor`, `artifact-coherence-auditor`, `code-paper-auditor`, `code-review`(연구 스크립트 리뷰). `codex-research`·`gemini-research`는 각각 Codex CLI·Gemini CLI가 설치된 경우에만 동작한다.

### 미설치 구성 요소 (별도 설정 필요)

- 훅 9종(파괴적 git 방지 등): `claude-research/hooks/` 참조, settings.json 연결 필요
- Notion 연동·Research Vault·Council 모드(다중 모델 심의)·Biblio MCP(OpenAlex/Scopus 검색): API 키와 추가 도구 필요. 설정법은 `claude-research/docs/` 참조

### ARS와의 역할 구분

- 논문을 처음부터 만들거나 전체 파이프라인 실행 → ARS (`academic-paper`, `academic-pipeline`)
- 이미 있는 원고의 품질 점검, 서지 검증, 리뷰 대응, 재현성 감사 → claude-research 스킬
- 안 쓰는 스킬은 `.claude\skills\<이름>` 정션을 삭제하면 비활성화된다 (원본은 `claude-research/`에 남는다)

## HWPX 문서 읽기·쓰기 (hwpx MCP 서버)

한글 HWPX 문서를 한/글 프로그램 없이 읽고 쓸 수 있는 MCP 서버(`hwpx`)가 연결되어 있다. `.hwpx` 파일 작업은 반드시 이 서버의 `mcp__hwpx__*` 도구를 사용하라. 텍스트 도구(Read/Write)로 `.hwpx`를 직접 열지 마라 (zip 기반 바이너리라 깨진다).

설치 구조.
- 서버 본체: 프로젝트 루트의 `hwpx-mcp-simple\` (Kang-T/hwpx-mcp-simple 클론, 전용 venv 포함, 프로젝트별 개별 설치)
- 프로젝트 연결: 프로젝트 루트의 `.mcp.json`
- 신규 PC 최초 설정: 프로젝트 루트의 `setup.ps1`이 venv 생성·서버 설치와 `.mcp.json` 경로 갱신을 수행한다
- 업데이트: `hwpx-mcp-simple\`에서 `git pull` 후 `.venv\Scripts\pip install .` 재실행

### 도구 (9개)

읽기 (원본을 변경하지 않음).
- `get_document_info` — 문서 메타데이터와 구조 요약 조회
- `get_document_text` — 문서 전체 텍스트 추출
- `get_document_outline` — 제목/개요 구조 조회
- `hwpx_to_markdown` — HWPX를 Markdown으로 변환 (payload/URL 기반)
- `hwpx_extract_json` — HWPX에서 구조화된 JSON 추출 (payload/URL 기반)

쓰기 (호출 즉시 파일에 저장됨).
- `create_document` — 새 HWPX 문서 생성
- `create_proposal_document` — proposal_spec 기반 제안서형 HWPX 문서 생성
- `search_and_replace` — 텍스트 치환 (스타일 보존)
- `inspect_document_quality` — 생성된 문서를 제안서 품질 루브릭으로 점검

### 안전 원칙

- 먼저 읽기 도구로 문서를 파악한 뒤 수정하라 (read first)
- 쓰기 도구는 호출 즉시 저장된다. 원본 보존이 필요하면 파일을 먼저 복사한 뒤 사본에서 작업하라
- 자동 백업이 켜져 있어(`HWPX_MCP_AUTOBACKUP=1`) 저장 전 `.bak` 파일이 생성된다
- 서버는 실행 위치(이 프로젝트 루트)를 샌드박스 루트로 삼는다. **프로젝트 폴더 밖의 hwpx 파일은 접근이 거부되므로**, 외부 파일은 프로젝트 안으로 복사한 뒤 작업하라
- `search_and_replace`의 파라미터는 `find_text` / `replace_text`다
- 바이너리 `.hwp` 포맷은 지원하지 않는다. `.hwpx`만 가능하며, `.hwp`는 한/글에서 `.hwpx`로 저장한 뒤 작업하라
