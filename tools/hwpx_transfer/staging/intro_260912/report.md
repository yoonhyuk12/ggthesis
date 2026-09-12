# Intro transfer patch ready for coordinator execution

Prepared four files only in this staging directory. No HWPX was written, no applying code was executed/imported, and no COM or HWPX MCP/rhwp tool was used. Both scripts passed `ast.parse` syntax checks; read-only ZIP/XML analysis verified every replace/delete target is a root-level, plain, single-run paragraph with no controls or objects.

Base source: `00. hwpx/260912_1059_경기공학_건축안전_윤혁_논문작성_작성본.hwpx`. Pinned SHA256: `7fe34aa00395a50b30b63bda6361f572f3825f9bef15167d60eed8527f49afd3`. The authoritative dump was read first. Chapter 2 is section2 paragraph **62**, not 61; paragraph 61 is its preceding blank. The validator requires raw bytes from paragraph 61 to EOF to remain identical.

All nonempty current HWPX intro paragraphs occur verbatim in `git HEAD:01.docs/01_서론.md` after stripping the HWPX leading space and decoding Markdown HTML entities. No substantive HWPX-only intro prose was found. User formatting, existing heading gaps, figure placeholders, and all unaffected XML are retained byte-for-byte; no reverse synchronization is needed. This finding is recorded in `user_edits` in the plan.

The patch changes item1/item2 titles, removes obsolete item headings and their redundant gaps, replaces five item2 paragraphs, turns the purpose into six continuous paragraphs (1,804 characters excluding paragraph separators/leading spaces), adds one blank immediately before section2, and changes the section3 transition before removing obsolete section4. It preserves the existing blank before each other surviving section/item. The coordinator's TOC clarification is included: two item titles replaced and obsolete section1 item2/item4, all four purpose items, and section4 deleted. Existing finer TOC detail is otherwise retained.

| XML entry | Replacements | Deletions | Insertions | Paragraph count |
| --- | ---: | ---: | ---: | --- |
| Contents/section1.xml | 2 | 7 | 0 | 180 → 173 |
| Contents/section2.xml | 12 | 23 | 3 | 2608 → 2588 |

Run/text/cache deltas are explicit in `expected_deltas.xml_counts`: section1 run -7, text -7, linesegarray -9; section2 run -20, text -8, linesegarray -35. New paragraphs reuse existing body style (paraPr 46, charPr 36); body text retains the leading space. New IDs exceed every numeric XML ID in the package and are unique. Changed/inserted paragraphs have no linesegarray.

`apply_intro.py` uses Expat byte offsets and targeted paragraph splicing, without reserializing either section or the intro. A raw ZIP patch preserves unchanged compressed local records and central metadata bytes; only CRC/size/offset fields are updated where necessary. It retains entry order, compression method, names, timestamps, comments, extras, flags and permissions. The baseline contains 13 entries with flags/method combinations (0,0) and (4,8), both supported. Unsupported ZIP64, encrypted/data-descriptor or split archives fail closed. Output must be a fresh path and cannot equal base.

Run these exact commands from the repository root (coordinator only):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
python tools/hwpx_transfer/staging/intro_260912/apply_intro.py tools/hwpx_transfer/staging/intro_260912/base.hwpx tools/hwpx_transfer/staging/intro_260912/candidate.hwpx
python tools/hwpx_transfer/staging/intro_260912/validate_intro.py tools/hwpx_transfer/staging/intro_260912/base.hwpx tools/hwpx_transfer/staging/intro_260912/candidate.hwpx
```

Both commands must exit 0. A failed candidate must not be published. The validator compares current MD against its pinned hash and text, checks the exact expected surgical XML, every untouched ZIP entry and compressed local record, all table/object/control XML spans, unchanged chapter2+ suffix, TOC headings, exactly one preceding blank per surviving section/item, unique inserted IDs, intentional structural counts, and marker text/color associations read from header charPr mappings. It also verifies the retained intro marker text is fully red. The generic `verify_replace.py` unchanged-count gate does **not** apply to this structural patch.

The writer/validator have only been syntax-checked and statically reviewed, as required by the dispatch; runtime candidate generation and validation remain the coordinator's responsibility. No full-document validity, successful Hancom opening, or rendered layout success is claimed.

Read-only inspection found **no flowchart/figure object in the existing intro**: Figure 1-1/1-2 captions and red placeholders, and the Figure 1-3 caption are present. The existing absence is preserved; the fenced Markdown flowchart rendering is excluded from the nonempty-text comparison as instructed. All objects elsewhere, including nested appendix questionnaire tables, are protected by untouched bytes and object-span comparison.

After the strict candidate check, the coordinator must perform the repository's actual Hancom COM open, reflow SaveAs to a separate file, and PDF/rendered-page inspection before publication. Use `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1` for opening/PDF and `render-pdf.ps1` under Windows PowerShell 5.1 for affected pages; confirm the helper's SaveAs behavior or perform the required SaveAs separately. Inspect intro headings/page breaks, TOC and chapter2 boundary; avoid claiming unchanged page count because content length intentionally changes.

The strict validator is **pre-COM only**: COM can renumber charPr IDs, update caches and normalize table cells. Keep the candidate as byte-preservation evidence; validate the separately saved final file semantically against candidate/current MD, re-read its header color mapping, and inspect objects/table layout after reflow. A final COM file may legitimately fail this strict raw-byte validator, so do not conceal that difference or substitute a pre-COM pass for post-save verification.
