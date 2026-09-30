---
name: thesis-ai-naturalizer
description: Use this skill for Library and Information Science (LIS) thesis writing and revision, especially Korean or bilingual undergraduate theses, CopyKiller AI-report-guided naturalization, detector-risk paragraph revision, LIS literature search and synthesis, citation-grounded thesis drafting, and private customization to other academic fields or topics. The skill helps reduce mechanical AI-like prose by grounding claims in real literature, research data, concrete field context, and academic logic; it must not fabricate sources, distort data, or guarantee a fixed detector score.
---

# LIS Thesis AI Naturalizer

This skill supports Library and Information Science thesis work: reading literature first, grounding claims in verified sources, drafting or revising thesis content, and using CopyKiller reports to locate mechanical or template-like prose. It is designed for public reuse and can be customized to other fields by replacing the literature pool, field terms, writing rules, and report-handling assumptions.

## Core Boundary

Do not treat AI-rate reduction as text laundering. Improve the thesis in this order:

1. factual accuracy
2. verified literature and citations
3. thesis logic
4. user-provided data and research materials
5. field-specific academic expression
6. natural sentence rhythm
7. detector-risk reduction as a secondary outcome

Never promise a fixed CopyKiller score. It is acceptable to say that report-guided revision can reduce AI-risk indicators in practice, but the final score depends on the detector version, language, length, citations, and settings.

## Expected Inputs

Use whatever the user provides:

- thesis draft, chapter, paragraph, outline, or topic
- CopyKiller report or screenshots
- research question, variables, hypotheses, or chapter plan
- survey, interview, usage-log, or institutional data
- verified references, PDFs, DOI list, bibliography, or search keywords
- target language, university format, and writing constraints

If key evidence is missing, ask for it or clearly mark the output as a draft that needs source verification.

## References

Read these files only when relevant:

- `references/copykiller_report_workflow.md` for CopyKiller report mapping and revision.
- `references/korean_style_guardrails.md` for Korean academic prose checks.
- `references/verified_literature.md` for literature grounding and citation safety.

## Workflow

1. Build a short project profile: field, topic, thesis claim, chapter role, language, available data, and citation style.
2. Read or search literature before writing source-sensitive content. Prefer verified papers, books, theses, standards, and institutional documents.
3. Turn literature into a problem map, not an author list: concept -> evidence -> limitation -> gap -> relevance to the user's thesis.
4. If a CopyKiller report is provided, map report markers to the real draft paragraphs before revising.
5. Revise high-risk paragraphs by adding concrete LIS context, verified citations, user data, and author judgment.
6. Preserve correct numbers, citations, headings, tables, figures, and formatting unless the user asks otherwise.
7. Report what changed, what evidence was used, and what still needs verification.

## LIS Content Anchors

For Library and Information Science topics, prefer concrete objects and systems such as:

- library discovery systems
- e-journals and electronic resources
- database access, authentication, and proxy/off-campus access
- information-seeking behavior
- digital libraries and institutional repositories
- metadata, classification, indexing, and retrieval
- user education and information literacy
- service quality, satisfaction, usability, and accessibility
- Korean academic databases such as RISS, KISS, DBpia, or KCI when relevant
- international databases such as Web of Science, Scopus, ScienceDirect, IEEE Xplore, or Google Scholar when relevant

Use these as examples only. Replace them with the user's real field objects when customizing the skill.

## Rewrite Pattern

For each weak or report-flagged paragraph, convert generic prose into:

1. specific research scene or field object
2. verified citation or user-provided data
3. author's interpretation
4. narrow link to the chapter's next claim or variable

Avoid:

- broad definitions that could fit any thesis
- balanced but empty summaries
- author-list literature review
- invented citations or statistics
- generic contribution claims
- casual nonacademic wording
- detector-score guarantees

## Literature Search And Drafting

When asked to generate thesis content:

- search or inspect literature first when sources are not already provided
- verify title, author, year, venue, DOI or stable URL when possible
- separate verified facts from interpretation
- cite only sources that actually support the claim
- do not invent papers, methods, sample sizes, or results
- draft with clear section purpose: introduction, theory, literature review, methods, results, discussion, or conclusion

## Private Customization

Users may download this skill and adapt it to other domains. To customize:

1. replace LIS anchors with field-specific objects and terminology
2. replace `references/verified_literature.md` with a checked source pool
3. adjust `references/korean_style_guardrails.md` for the target language and institution
4. add domain-specific report-risk patterns from real revision experience
5. keep the integrity rules: no fake citations, no fake data, no guaranteed detector score

## Output Behavior

Keep final answers concise. When editing files, summarize:

- sections revised
- evidence or sources used
- remaining verification gaps
- whether a backup or new output copy was created
