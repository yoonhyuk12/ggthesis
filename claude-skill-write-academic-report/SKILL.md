---
name: write-academic-report
description: "Write 40-100+ page academic reports (FYP, thesis, dissertation) with parallel Claude Code subagents. 3-wave pipeline: Wave 0 extracts data from your research repo, Wave 1 writes chapters in parallel (3-4x faster), Wave 2 merges Markdown files with automated cross-reference auditing. Output as Markdown for easy conversion to HWP/DOCX/PDF. Inherits academic writing standards from Nanda, Gopen & Swan, Lipton."
version: 2.0.0
author: Haoyang Pang
license: MIT
tags: [Academic Report, Thesis Writing, FYP, Dissertation, Markdown, Parallel Agents, Claude Code Skill]
dependencies: []
---

# Academic Report Writer: 40-100+ Page Thesis/FYP with Parallel Agents

Turn a research repository into a **publication-quality Markdown thesis** in 2-4 hours instead of 8-12 — using a **3-wave parallel agent pipeline** purpose-built for academic reports.

**What this skill does:** You point it at your research repo (code + experiment results). It launches parallel agents to extract data, write chapters simultaneously, then assembles a complete Markdown report with proper cross-references, figures, and bibliography.

**Output format:** Markdown (.md) — easily convertible to HWP (한글), DOCX, or PDF via pandoc or manual paste.

**Validated:** 86-page FYP report, 6 chapters + 3 appendices + 15 figures, produced in ~6 hours. Writing philosophy inherited from [ml-paper-writing](https://github.com/Orchestra-Research/ml-paper-writing) (Nanda, Farquhar, Gopen & Swan, Lipton, Steinhardt, Perez).

---

## CRITICAL: Never Hallucinate Citations

**This rule is inherited from ml-paper-writing and is non-negotiable.**

### The Problem (Backed by Data)

| Statistic | Source |
|-----------|--------|
| **6-55%** of AI-generated citations are fabricated | Multiple studies (varies by model/domain) |
| **100+** hallucinated refs in NeurIPS 2025 accepted papers | GPTZero analysis, Jan 2026 |
| **50+** hallucinated refs in ICLR 2026 submissions | GPTZero analysis, Feb 2026 |
| Only **26.5%** of AI-generated references are entirely accurate | Paper-Checker 2026 survey |
| **206+** legal sanctions for AI-hallucinated citations in courts | As of July 2025 |
| **3 types**: fully fabricated, chimeric (blended), modified real | CheckIfExist (arXiv 2602.15871) |

Universities increasingly treat fake citations as **academic misconduct** — failed assignments, course failure, or expulsion.

### The Rule

**NEVER generate citation entries from memory. ALWAYS fetch programmatically.**

```
IF you cannot programmatically fetch a citation:
    → Mark it as [CITATION NEEDED] or [PLACEHOLDER - VERIFY]
    → Tell the author explicitly
    → NEVER invent a plausible-sounding reference
```

### Automated Verification: citation_checker.py

After writing, **always run the citation checker** before submission:

```bash
# Check a single .bib file
python scripts/citation_checker.py references.bib

# Check all .bib files in a report directory
python scripts/citation_checker.py path/to/report/

# JSON output (for CI pipelines)
python scripts/citation_checker.py references.bib --json
```

The checker uses a **cascading 3-source verification pipeline**:

```
CrossRef (140M+ DOIs) → Semantic Scholar (200M+ papers) → OpenAlex (240M+ works)
```

For each citation it:
1. Searches by DOI (if available) or title
2. Computes title similarity + author overlap
3. Flags red flags (invalid DOI, generic title, missing fields, chimeric blends)
4. Reports: **verified** (2+ sources), **suspicious** (1 source), or **not found** (likely hallucinated)

**Red flag detection catches:**
- Fully fabricated citations (no match in any database)
- Chimeric hallucinations (title matches but authors don't)
- Invalid DOI formats
- Suspiciously generic titles common in AI output
- Missing critical fields (authors, year)
- Future publication years

See [references/citation-workflow.md](references/citation-workflow.md) for the full API documentation and Python CitationManager class.

---

## When to Use This Skill

| Scenario | Use This Skill | Use ml-paper-writing Instead |
|----------|:-:|:-:|
| FYP / Final Year Project report | Yes | |
| MSc / PhD dissertation | Yes | |
| Technical report (20+ pages) | Yes | |
| Conference paper (8-12 pages) | | Yes |
| Workshop paper (4-6 pages) | | Yes |

**Key difference**: This skill orchestrates **parallel subagents** for long documents. Conference papers are short enough to write sequentially.

---

## Core Architecture: 3-Wave Pipeline

```
Wave 0: DATA PREPARATION          Wave 1: CHAPTER WRITING          Wave 2: ASSEMBLY
(5-6 parallel agents)             (3-4 parallel agents)            (1-2 sequential agents)

┌─ Agent 0A: Data consolidation   ┌─ Agent 1: Template + Ch1-2     ┌─ Agent 6: Merge + cross-ref
├─ Agent 0B: Codebase analysis    ├─ Agent 2: Ch3 (core work)      └─ Agent 7: Review + finalize
├─ Agent 0C: System analysis      ├─ Agent 3: Ch4-5 (results)
├─ Agent 0D: Experiment history   └─ Agent 4: Ch6 + Appendices
├─ Agent 0E: Statistics
└─ Agent 0F: Figure generation
```

**Why waves?** Data must exist before prose. Prose must exist before assembly. Violating this order produces agents that hallucinate numbers or write without evidence.

---

## Wave 0: Data Preparation (Before Writing)

**Goal**: Produce all data artifacts that chapter-writing agents will reference. Every claim in the report must trace back to a Wave 0 artifact.

### What Wave 0 Agents Produce

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| **0A: Data Consolidation** | Raw result files (JSON, CSV) | `data/final_results.json` | Single source of truth for all numbers |
| **0B: Codebase Analysis** | Source code | `data/codebase_analysis.md` | Module map, LOC, complexity, key snippets |
| **0C: System Analysis** | Architecture, pipeline code | `data/system_analysis.md` | How components connect, data flow |
| **0D: Experiment History** | All experiment logs | `data/experiment_history.md` | Timeline, what changed, why |
| **0E: Statistics** | Result files | `data/statistics.md` | Aggregate stats, distributions |
| **0F: Figure Generation** | Data artifacts + style config | `figures/*.png` | All publication-quality figures |

### Agent 0F: Figure Pipeline (Special)

Figures deserve a dedicated agent because:
1. They must be **consistent** (same color palette, font sizes, style)
2. They must be **high-resolution** (PNG 300+ DPI)
3. They must be **colorblind-safe** (Okabe-Ito or Paul Tol palette)
4. They must be **self-contained** (captions tell the full story)

```python
# Recommended figure style
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (6.5, 4),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

# Colorblind-safe palette (Okabe-Ito)
COLORS = ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
          '#0072B2', '#D55E00', '#CC79A7', '#000000']
```

**Output format**: `figure_name.png` (300+ DPI). Optionally also `figure_name.svg` for vector diagrams.

### Wave 0 Completion Gate

**Do NOT proceed to Wave 1 until:**
- [ ] All data files exist and are non-empty
- [ ] All figures render correctly (PNG)
- [ ] Numbers in `final_results.json` match known ground truth
- [ ] Each agent's output has been spot-checked

---

## Wave 1: Chapter Writing (Parallel, After Wave 0)

### Chapter Dependency Graph

```
Independent (can parallelize):
  Ch1 (Introduction) ←→ Ch2 (Literature Review)  [no dependency]
  Ch3 (System/Methods) [needs 0B, 0C]
  Ch6 (Conclusion) [needs 0A summary only]

Sequential (must wait):
  Ch4 (Experimental Setup) → Ch5 (Results) [Ch5 needs Ch4's definitions]
  Ch5 needs: 0A (data), 0D (history), 0E (stats), 0F (figures)
```

### Recommended Agent Assignment

| Agent | Chapters | Depends On | Approx Pages |
|-------|----------|------------|:---:|
| **Agent 1** | Front matter + Ch1 + Ch2 | Plan only | 15-20 |
| **Agent 2** | Ch3 (System Design) | 0B, 0C | 12-18 |
| **Agent 3** | Ch4 + Ch5 (Setup + Results) | 0A, 0D, 0E, 0F | 15-25 |
| **Agent 4** | Ch6 + Appendices | 0A (summary) | 5-10 |

### Writing Philosophy (Inherited)

These principles from ml-paper-writing apply to every chapter:

**The Narrative Principle** (Nanda): Your report tells one story. Every chapter advances that story. If a section doesn't connect to the core contribution, cut it.

**Sentence-Level Clarity** (Gopen & Swan):

| Principle | Rule | Mnemonic |
|-----------|------|----------|
| Subject-verb proximity | Keep subject and verb close | "Don't interrupt yourself" |
| Stress position | Emphasis at sentence end | "Save the best for last" |
| Topic position | Context at sentence start | "First things first" |
| Old before new | Familiar then unfamiliar | "Build on known ground" |
| One unit, one function | Each paragraph = one point | "One idea per container" |
| Action in verb | Use verbs, not nominalizations | "Verbs do, nouns sit" |
| Context before new | Explain before presenting | "Set the stage first" |

**Word Choice** (Lipton, Steinhardt):
- Be specific: "accuracy" not "performance"
- Eliminate hedging: drop "may" and "can" unless genuinely uncertain
- Consistent terminology: pick one term per concept, stick with it
- Delete filler: "actually," "very," "basically," "essentially"

**Micro-Level Tips** (Perez):
- Minimize pronouns: "This result shows..." not "This shows..."
- Position verbs early in sentences
- Active voice always: "We show..." not "It is shown..."
- One idea per sentence

### Thesis-Specific Adaptations (Beyond ml-paper-writing)

| Conference Paper | Thesis/Report |
|-----------------|---------------|
| 1-1.5 page intro | 3-5 page intro with motivation + scope |
| Related Work section | Full Literature Review chapter |
| 8-12 pages total | 40-100+ pages total |
| 5-sentence abstract | 250-400 word abstract |
| Contribution bullets | Objectives & scope section |
| No project timeline | Gantt chart / project schedule |
| No appendices (usually) | 2-5 appendices with supplementary material |

### Chapter Templates (Markdown)

Each chapter is a separate `.md` file. Use consistent heading hierarchy:
- `#` = Chapter title (H1) — one per file
- `##` = Section (H2)
- `###` = Subsection (H3)
- `####` = Sub-subsection (H4) — use sparingly

#### Chapter 1: Introduction (3-5 pages)

```markdown
# I. 서론
<!-- Chapter file: chapters/ch1_introduction.md -->

## 1. 연구의 배경 및 필요성
<!-- 1-2 pages: Establish the problem domain -->
<!-- Start specific, not generic. No "AI has revolutionized..." -->

## 2. 연구의 목적
<!-- 0.5-1 page: Why this problem matters NOW -->
<!-- Clear, numbered research objectives -->

## 3. 연구의 범위 및 방법
<!-- 0.5 page: Scope boundaries + methodology overview -->
<!-- Explicitly state what is IN and OUT of scope -->
```

#### Chapter 2: Literature Review (8-15 pages)

```markdown
# II. 이론적 배경
<!-- Chapter file: chapters/ch2_literature_review.md -->

<!-- Organize METHODOLOGICALLY, not paper-by-paper -->
<!-- Group: "One line of work uses X (저자, 연도) whereas we use Y because..." -->

## 1. 주제영역 1
## 2. 주제영역 2
## 3. 주제영역 3
## 4. 선행연구 종합 및 연구 공백
<!-- Explicitly state what's missing and how you fill it -->
<!-- Include positioning figure/table if helpful -->
```

#### Chapter 3: System Design / Methodology (10-18 pages)

```markdown
# III. 연구방법
<!-- Chapter file: chapters/ch3_methodology.md -->

## 1. 연구모형
<!-- Architecture/model diagram (FIGURE — from Wave 0) -->

## 2. 연구가설
<!-- Numbered hypotheses with rationale -->

## 3. 조작적 정의 및 측정도구
<!-- Tables defining each variable and its survey items -->

## 4. 자료수집 및 분석방법
<!-- Statistical methods table: which test, why, assumptions -->
```

#### Chapter 4: Results and Analysis (8-15 pages)

```markdown
# IV. 연구결과
<!-- Chapter file: chapters/ch4_results.md -->

<!-- For EACH result, explicitly state: -->
<!-- 1. What claim it supports -->
<!-- 2. The specific numbers -->
<!-- 3. Statistical significance -->

## 1. 인구통계학적 특성
## 2. 타당도 및 신뢰도 분석
## 3. 기술통계 및 상관관계 분석

## 4. 가설검증
<!-- FIGURE + TABLE for each hypothesis test -->

## 5. 소결
<!-- What worked, what didn't, WHY -->
```

#### Chapter 5: Conclusion (3-5 pages)

```markdown
# V. 결론
<!-- Chapter file: chapters/ch5_conclusion.md -->

## 1. 연구 요약
<!-- 3-5 numbered contributions, each 2-3 sentences -->

## 2. 논의 및 시사점
<!-- Compare with prior research, practical/academic/policy implications -->

## 3. 연구의 한계 및 향후 연구방향
<!-- HONEST assessment. Claude undersells weaknesses by default. -->
<!-- Explicitly prompt: "What are the real limitations?" -->
<!-- Pre-empt criticisms. Honesty builds trust. -->
<!-- 2-4 concrete, actionable future directions -->
```

### Limitations Section Guidance (Critical)

**Claude has a documented tendency to understate limitations.** When writing the limitations section:

1. Ask yourself: "What would a skeptical examiner criticize?"
2. List ALL weaknesses, not just minor ones
3. Quantify where possible: "Judge variance is ~5pp between re-judgings"
4. Explain WHY the limitation doesn't invalidate the core contribution
5. Distinguish between "fundamental limitation" and "scope limitation"

---

## Wave 2: Assembly & Finalization

### Step 1: Merge Chapters

Concatenate all chapter Markdown files into a single document or keep them as separate files linked from an index:

```markdown
<!-- main.md — Master document -->

# [논문 제목]

<!-- Front matter -->
[목차는 최종 HWP/DOCX 변환 시 자동 생성]

---

<!-- Include chapters in order -->
<!-- Option A: Separate files (recommended for parallel writing) -->
<!-- chapters/ch1_introduction.md -->
<!-- chapters/ch2_literature_review.md -->
<!-- chapters/ch3_methodology.md -->
<!-- chapters/ch4_results.md -->
<!-- chapters/ch5_conclusion.md -->

<!-- Option B: Merge into single file for final review -->
<!-- Copy-paste each chapter sequentially -->

---

## 참고문헌
<!-- Bibliography entries in citation format -->

---

## 부록
<!-- appendices/appendix_a.md -->
<!-- appendices/appendix_b.md -->
```

**Recommended directory structure:**

```
report/
├── main.md                    # Master index / merged document
├── chapters/
│   ├── ch1_introduction.md
│   ├── ch2_literature_review.md
│   ├── ch3_methodology.md
│   ├── ch4_results.md
│   └── ch5_conclusion.md
├── appendices/
│   ├── appendix_a.md
│   └── appendix_b.md
├── figures/
│   ├── fig1_research_model.png
│   ├── fig2_architecture.png
│   └── ...
├── data/                      # Wave 0 outputs
│   ├── final_results.json
│   ├── codebase_analysis.md
│   ├── system_analysis.md
│   ├── experiment_history.md
│   └── statistics.md
└── references.bib             # Bibliography (for citation checker)
```

### Step 2: Cross-Reference Audit (Mandatory)

With parallel agents writing chapters independently, **inconsistencies are inevitable**.

Run the automated audit script (adapted for Markdown):

```bash
python scripts/cross_ref_audit.py report_dir/
```

For Markdown, the audit checks:
- Duplicate heading titles across chapters
- Broken image links (`![](path)` pointing to missing files)
- Inconsistent figure/table numbering (e.g., "표 3" in Ch2 and "표 3" in Ch4)
- Orphaned figures (files in `figures/` never referenced)
- Citation key consistency (author, year) format
- Terminology consistency across chapters

### Step 3: Format Conversion (Optional)

Markdown is the intermediate format. Convert to final submission format:

**To DOCX (for HWP import):**
```bash
# Using pandoc
pandoc main.md -o thesis.docx --reference-doc=template.docx

# Or merge chapters first, then convert
cat chapters/ch*.md > merged.md && pandoc merged.md -o thesis.docx
```

**To PDF (for review):**
```bash
pandoc main.md -o thesis.pdf --pdf-engine=xelatex -V mainfont="Malgun Gothic"
```

**To HWP (한글):**
- Import DOCX into 한글 and apply university template styles
- Or copy-paste Markdown content directly and format in 한글
- Tables and figures may need manual adjustment after import

### Step 4: Quality Review

Final quality checks:

```
Post-Assembly Checklist:
- [ ] All figure images exist and render correctly
- [ ] No broken image links
- [ ] Figure/table numbering is sequential and consistent
- [ ] Citations use consistent format: (저자, 연도)
- [ ] No duplicate section headings
- [ ] Terminology is consistent across all chapters
- [ ] Each chapter flows into the next (transition sentences)
- [ ] Bibliography entries are complete
- [ ] Appendices are properly labeled
- [ ] No placeholder text remains ([CITATION NEEDED], [TODO], etc.)
```

---

## Tables and Figures

### Tables (Markdown)

Use standard Markdown tables with clear headers:

```markdown
**<표 1> 조건별 비교 결과 (최고값 굵게 표시)**

| 조건 | 성공률 (↑) | p-value |
|:-----|:----------:|:-------:|
| 기본 조건 | 25.6% | --- |
| 요약 제공 | 27.8% | 0.839 |
| **URL 제공** | **50.0%** | **<0.001** |
| **도구 제공** | **50.0%** | **<0.001** |
```

**Rules:**
- Bold best value per metric
- Include direction symbols (higher/lower is better): ↑ or ↓
- Align numerical columns to center or right
- Consistent decimal precision
- Caption (표 제목) ABOVE table
- Number sequentially within each chapter: 표 1, 표 2, ...

### Figures (Markdown)

```markdown
![그림 1. 시스템 아키텍처. 5개 핵심 모듈의 데이터 흐름을 나타냄. 좌측 브라우저 자동화에서 우측 출력 그래프까지의 처리 과정을 표시.](figures/fig1_architecture.png)
```

**Rules:**
- **PNG 300+ DPI** for all figures
- **SVG** for vector diagrams when possible
- **Colorblind-safe palettes** (Okabe-Ito recommended)
- **No title inside figure** — the caption serves this function
- **Self-contained captions** — reader should understand without main text
- Caption format: `그림 N. 제목. 설명.`
- Number sequentially within each chapter

### Citation Format (Inline)

Use parenthetical author-year format consistently:

```markdown
<!-- Single author -->
선행연구에 따르면 (홍길동, 2024), ...

<!-- Two authors -->
(김철수, 이영희, 2023)

<!-- Three or more authors -->
(박연구 외, 2025)

<!-- Multiple citations -->
(홍길동, 2024; 김철수, 이영희, 2023)

<!-- Direct quote -->
홍길동(2024)은 "인용 문구"라고 주장하였다.
```

---

## University Template Handling

### Markdown-First Workflow

Since most Korean universities require HWP submission:

1. **Write everything in Markdown first** — clean, reviewable, version-controllable
2. **Review and iterate** in Markdown (easier diffs, faster agent rewrites)
3. **Convert to HWP last** — apply university formatting in 한글 word processor

### Adapting to Your University

| University Feature | How to Handle in Markdown |
|-------------------|--------------------------|
| Title page format | Write content in front matter section; format in HWP |
| Margin/font requirements | Apply in HWP after conversion (not in Markdown) |
| Citation style | Use consistent (저자, 연도) inline; format bibliography in HWP |
| Figure/table numbering | Use sequential numbering per chapter in Markdown |
| Appendix format | Separate `.md` files, lettered or numbered per university spec |
| Page headers/footers | Apply in HWP (not possible in Markdown) |

---

## Workflow: End-to-End

### Step-by-Step Execution

```
1. UNDERSTAND THE PROJECT
   - Read the codebase, results, existing docs
   - Identify the core contribution

2. PLAN THE REPORT
   - Define chapter structure
   - Map: which data → which chapter
   - Identify figures needed
   - Create the execution plan

3. WAVE 0: DATA PREPARATION
   - Launch 5-6 parallel agents
   - Wait for ALL to complete
   - Verify outputs (spot-check numbers)

4. WAVE 1: CHAPTER WRITING
   - Launch 3-4 parallel agents
   - Each agent gets: chapter template + relevant Wave 0 data
   - Each agent writes a .md file
   - Independent chapters can run in parallel

5. WAVE 2: ASSEMBLY
   - Merge chapter .md files
   - Run cross_ref_audit.py
   - Fix inconsistencies, broken links
   - Quality review
   - (Optional) Convert to DOCX/HWP

6. ITERATE
   - Author reviews output
   - Targeted revisions (specific chapters/sections)
   - Re-run audit and verify
```

### Time Estimates (Based on Validated Run)

| Wave | Agents | Typical Duration | Notes |
|------|:------:|:----------------:|-------|
| Wave 0 | 5-6 | 30-60 min | Depends on codebase size |
| Wave 1 | 3-4 | 60-90 min | Longest wave |
| Wave 2 | 1-2 | 15-30 min | Faster without LaTeX compilation |
| **Total** | | **2-3 hours** | For ~80 page report |

Without parallel agents, the same report takes 8-12 hours.

---

## Key Lessons (From Production Use)

1. **Data before prose**: Agents write poorly without concrete numbers. Wave 0 is essential.
2. **Markdown first, format last**: Write in Markdown for speed and reviewability. Apply HWP/DOCX formatting only at the end.
3. **Cross-ref audit is mandatory**: Parallel agents create inconsistencies. Automated script catches them.
4. **Figure pipeline separate**: Generate all figures first, reference later. Don't embed matplotlib in chapter agents.
5. **Honest limitations**: Explicitly prompt for limitations — Claude undersells weaknesses by default.
6. **Plan file as source of truth**: Write the full execution plan before launching any agents.
7. **Spot-check Wave 0**: Don't blindly pass data artifacts to writing agents. Verify key numbers.
8. **Consistent numbering convention**: Agree on figure/table numbering before Wave 1 (e.g., "그림 3-1" = Ch3 Fig1).

---

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Inconsistent heading levels across chapters | Agree on convention: `#` = chapter, `##` = section, `###` = subsection |
| Duplicate figure/table numbers | Use chapter prefix: 표 3-1, 그림 4-2 |
| Broken image links | Run `cross_ref_audit.py`; ensure all `figures/*.png` exist |
| Inconsistent citation format | Search for all `(` patterns; normalize to (저자, 연도) |
| Terminology drift across chapters | Create a terminology glossary in Wave 0; each agent references it |
| Agent writes without evidence | Wave 0 completion gate — never skip data preparation |
| Tables render poorly after HWP conversion | Simplify Markdown tables; complex tables may need manual HWP formatting |
| Examiner criticizes missing limitations | Use the explicit limitations prompting strategy |
| Placeholder text left in final draft | Search for `[CITATION NEEDED]`, `[TODO]`, `[PLACEHOLDER]` before submission |

---

## References

### Inherited from ml-paper-writing

| Document | Contents |
|----------|----------|
| [references/writing-guide.md](references/writing-guide.md) | Gopen & Swan 7 principles, micro-tips, word choice |
| [references/citation-workflow.md](references/citation-workflow.md) | Citation APIs, Python code, BibTeX management |

### New for write-report

| Document | Contents |
|----------|----------|
| [references/parallel-pipeline.md](references/parallel-pipeline.md) | Wave architecture, agent orchestration, dependency graph |
| [scripts/cross_ref_audit.py](scripts/cross_ref_audit.py) | Automated cross-reference and consistency checker |
| [scripts/citation_checker.py](scripts/citation_checker.py) | Multi-source citation verifier (CrossRef + S2 + OpenAlex) |
