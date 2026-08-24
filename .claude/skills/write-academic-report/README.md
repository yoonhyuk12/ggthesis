# write-academic-report

**Claude Code skill** that writes 40-100+ page academic reports (FYP, thesis, dissertation) using parallel subagents — **3-4x faster** than sequential writing.

> Research repo in → Markdown thesis out. Convert to HWP/DOCX/PDF at the end.

## What it does

Point it at your research repo. It launches parallel agents to extract data, write chapters simultaneously in Markdown, and audit cross-references:

```
Wave 0: Data Preparation    Wave 1: Chapter Writing    Wave 2: Assembly
(5-6 parallel agents)       (3-4 parallel agents)      (sequential)

Codebase analysis            Ch1-2 (Intro + Lit Review)  Merge .md files
Experiment data              Ch3 (Methodology)           Cross-ref audit
Statistics                   Ch4-5 (Setup + Results)     Quality review
Figure generation            Ch6 (Conclusion)            (Optional) Convert to HWP/DOCX
```

**3-4x faster** than sequential writing. Validated on an 86-page FYP report produced in ~6 hours.

**Output format:** Markdown (.md) — write fast, review easily, convert to HWP/DOCX/PDF last.

## Install

### As a Claude Code skill

```bash
# Copy to your skills directory
cp -r . ~/.claude/skills/write-report/

# Or symlink
ln -s $(pwd) ~/.claude/skills/write-report
```

### Dependencies

```bash
# Python 3.10+ for scripts (included)
pip install requests   # for citation_checker.py
python3 scripts/cross_ref_audit.py --help
python3 scripts/citation_checker.py --help

# Optional: pandoc for format conversion
# brew install pandoc    # macOS
# choco install pandoc   # Windows
```

## Usage

Invoke with `/write-report` in Claude Code, or describe your report needs and the skill will be suggested.

### Quick start

1. Have your research repo with code + results ready
2. Tell Claude: "Write my thesis report based on this repo"
3. Claude will execute the 3-wave pipeline automatically
4. Output: Markdown files in `report/chapters/`
5. Convert to HWP/DOCX when ready for submission

### Citation verification

Verify all citations against 3 academic databases before submission. Catches AI-hallucinated references (6-55% of AI-generated citations are fabricated):

```bash
# Check all .bib files
python3 scripts/citation_checker.py path/to/report/

# JSON output for CI
python3 scripts/citation_checker.py references.bib --json
```

Cascading pipeline: CrossRef (140M+ DOIs) -> Semantic Scholar (200M+ papers) -> OpenAlex (240M+ works). Detects fully fabricated, chimeric (blended), and modified-real hallucinations.

### Cross-reference audit

After parallel agents write chapters, catch inconsistencies:

```bash
python3 scripts/cross_ref_audit.py path/to/report/
```

## What's included

```
write-academic-report/
  SKILL.md                              # Main skill definition
  README.md                             # This file
  references/
    writing-guide.md                    # Academic writing philosophy
    citation-workflow.md                # Citation verification pipeline
    parallel-pipeline.md                # Wave architecture documentation
  templates/
    university-thesis/                  # Generic thesis template (Markdown)
  scripts/
    citation_checker.py                 # Multi-source citation verifier (CrossRef + S2 + OpenAlex)
    cross_ref_audit.py                  # Cross-reference + consistency checker
```

## Output format

**Markdown-first workflow:**
1. Write all chapters as `.md` files (fast, diff-friendly, agent-friendly)
2. Review and iterate in Markdown
3. Convert to final format when ready:
   - **HWP**: Import DOCX into 한글, apply university styles
   - **DOCX**: `pandoc main.md -o thesis.docx`
   - **PDF**: `pandoc main.md -o thesis.pdf --pdf-engine=xelatex`

## Writing philosophy

Inherited from [ml-paper-writing](https://github.com/Orchestra-Research/ml-paper-writing):

- **Narrative Principle** (Nanda): One story, one contribution, surgical precision
- **Sentence Clarity** (Gopen & Swan): 7 principles of reader expectations
- **Word Choice** (Lipton, Steinhardt): Specific, confident, consistent
- **Citation Safety**: Never hallucinate references. Always fetch programmatically.

Adapted for thesis:
- 40-100+ pages vs 8-12 page conference papers
- Full Literature Review chapter vs Related Work section
- Project schedule / Gantt chart
- Honest limitations (Claude undersells by default)

## Key lessons

1. **Markdown first, format last** -- write fast, convert to HWP/DOCX at the end
2. **Data before prose** -- agents write poorly without concrete numbers
3. **Cross-ref audit is mandatory** -- parallel agents create inconsistencies
4. **Figure pipeline separate** -- generate all figures first, reference later
5. **Consistent numbering** -- use chapter prefixes: `그림 3-1`, `표 4-2`

## License

MIT
