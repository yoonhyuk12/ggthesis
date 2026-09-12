# Final PDF layout review: physical pages 61–120

Completed visual review of all 60 pages, 35 table pages and 39 source table objects (indices 9–47). The layout has issues: one high-severity bibliography collision group, one medium-severity table-placement group and two low-severity groups.

All 1001 nonempty source table paragraphs matched after whitespace normalization. Every final row was visually present; no table text clipping or footer intrusion was observed. This text check supplements, rather than replaces, rendered-page inspection.

## Inspected table pages

61, 63, 64, 65, 69, 72, 75, 77, 78, 79, 80, 81, 83, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119.

Continuation panels: 88, 94, 97. Nested Part-A survey tables: 111 and 117 (both outer frame and nested title table). Survey covers: 110 and 116. Figure 4-1 on page 70 is legible, complete, paired with its caption, and clear of the footer.

## Issues

### B01 — high — physical pages 108, 109

English reference continuation lines have severe horizontal character collisions. Page 108 Davis, Pisu and Podsakoff endings are compressed; page 109 the Yao continuation at the top is substantially unreadable, and the MonitorVLM ending also collides. Text extraction recovers strings but the rendered glyphs overlap.

Origin: unknown; no earlier rendered baseline inspected

Evidence: [p108.png](p108.png), [p109.png](p109.png), [crop_bibliography_108.png](crop_bibliography_108.png), [crop_bibliography_109_top.png](crop_bibliography_109_top.png), [crop_bibliography_109_bottom.png](crop_bibliography_109_bottom.png)

Action: Repair character spacing/line composition for these reference paragraphs and re-render the affected pages.

### B02 — medium — physical pages 80, 81, 85, 86, 90, 91

Table 4-4 occupies the top of page 81 between the final syllable sequence 건설현장에 on page 80 and 서 안전관리 업무를 수행하는 on page 81, splitting a sentence with an entire unrelated table. Table 5-1 appears on page 86 after the section-2 reliability heading at the end of page 85; Table 5-4 appears on page 91 after the section-4 ANCOVA heading at the end of page 90. These latter two tables visually fall under the following section rather than the demographics/homogeneity section they summarize.

Origin: unknown; no earlier rendered baseline inspected

Evidence: [sheet77.png](sheet77.png), [sheet81.png](sheet81.png), [sheet85.png](sheet85.png), [sheet89.png](sheet89.png)

Action: Place each floating table with its introducing paragraph and before the next section heading; avoid inserting tables inside a continued sentence.

### B03 — low — physical pages 87, 88, 93, 94, 96, 97

Table 5-2 panel B, Table 5-6 panel B and Table 5-8 panel B have their explanatory panel labels on pages 87, 93 and 96, while the corresponding grids start pages 88, 94 and 97 without a repeated table number, panel label or continuation indication. Column headings and all final rows are intact.

Origin: unknown; source tables 26,31,34 contain column headings but no standalone table/panel caption

Evidence: [sheet85.png](sheet85.png), [sheet93.png](sheet93.png), [sheet97.png](sheet97.png)

Action: Keep each panel label with its grid or repeat a compact table-number/panel caption on the continuation page.

### B04 — low — physical pages 112, 113, 114, 115, 118, 119

All six Likert tables show two empty subdivided grid bands beneath the three anchor labels; band boundaries do not align consistently with the five answer columns below, most conspicuously in Part C. Header positions 2 and 4 are blank, while the complete five-point wording remains in the instruction line above and all numbered answers 1-5 and final question rows are visible. This is a source-present header design defect, not demonstrated PDF text omission.

Origin: Source-present: tables.json indices 39,40,41,42,46,47 row 0 columns 4 and 8 have empty paragraphs; rows 1 and 2 are empty cells with mixed spans. No chronological claim that it predates the current editing task.

Evidence: [p113.png](p113.png), [sheet109.png](sheet109.png), [sheet113.png](sheet113.png), [sheet117.png](sheet117.png), [crop_survey_header_113.png](crop_survey_header_113.png)

Action: Simplify header to one row aligned with the five response columns, with consistently chosen anchor labels.

## Page and table evidence

Each page below was visually inspected. Source indices are zero-based in tables.json; printed page = physical page − 11. Full per-table final-row text and paragraph matching counts are in report.json.

| Physical page | Source table indices | Bottom drawing to footer gap (pt) | Issues | Render |
|---|---|---:|---|---|
| 61 | 9, 10 | 42.39 | None observed | [page](p061.png) |
| 62 | — | — | None observed | [page](p062.png) |
| 63 | 11 | 365.44 | None observed | [page](p063.png) |
| 64 | 12 | 398.28 | None observed | [page](p064.png) |
| 65 | 13 | 327.2 | None observed | [page](p065.png) |
| 66 | — | — | None observed | [page](p066.png) |
| 67 | — | — | None observed | [page](p067.png) |
| 68 | — | — | None observed | [page](p068.png) |
| 69 | 14 | 225.79 | None observed | [page](p069.png) |
| 70 | — | — | None observed | [page](p070.png) |
| 71 | — | — | None observed | [page](p071.png) |
| 72 | 15 | 208.53 | None observed | [page](p072.png) |
| 73 | — | — | None observed | [page](p073.png) |
| 74 | — | — | None observed | [page](p074.png) |
| 75 | 16 | 38.2 | None observed | [page](p075.png) |
| 76 | — | — | None observed | [page](p076.png) |
| 77 | 17, 18 | 42.51 | None observed | [page](p077.png) |
| 78 | 19 | 424.77 | None observed | [page](p078.png) |
| 79 | 20 | 144.64 | None observed | [page](p079.png) |
| 80 | 21 | 466.13 | B02 | [page](p080.png) |
| 81 | 22 | 168.73 | B02 | [page](p081.png) |
| 82 | — | — | None observed | [page](p082.png) |
| 83 | 23 | 383.18 | None observed | [page](p083.png) |
| 84 | — | — | None observed | [page](p084.png) |
| 85 | — | — | B02 | [page](p085.png) |
| 86 | 24 | 62.77 | B02 | [page](p086.png) |
| 87 | 25 | 216.68 | B03 | [page](p087.png) |
| 88 | 26 | 429.93 | B03 | [page](p088.png) |
| 89 | 27 | 80.27 | None observed | [page](p089.png) |
| 90 | — | — | B02 | [page](p090.png) |
| 91 | 28 | 367.48 | B02 | [page](p091.png) |
| 92 | 29 | 51.74 | None observed | [page](p092.png) |
| 93 | 30 | 126.06 | B03 | [page](p093.png) |
| 94 | 31 | 396.96 | B03 | [page](p094.png) |
| 95 | 32 | 284.53 | None observed | [page](p095.png) |
| 96 | 33 | 215.0 | B03 | [page](p096.png) |
| 97 | 34 | 483.27 | B03 | [page](p097.png) |
| 98 | 35 | 306.7 | None observed | [page](p098.png) |
| 99 | — | — | None observed | [page](p099.png) |
| 100 | — | — | None observed | [page](p100.png) |
| 101 | — | — | None observed | [page](p101.png) |
| 102 | — | — | None observed | [page](p102.png) |
| 103 | — | — | None observed | [page](p103.png) |
| 104 | — | — | None observed | [page](p104.png) |
| 105 | — | — | None observed | [page](p105.png) |
| 106 | — | — | None observed | [page](p106.png) |
| 107 | — | — | None observed | [page](p107.png) |
| 108 | — | — | B01 | [page](p108.png) |
| 109 | — | — | B01 | [page](p109.png) |
| 110 | 36 | 40.95 | None observed | [page](p110.png) |
| 111 | 37, 38 | 62.89 | None observed | [page](p111.png) |
| 112 | 39 | 53.15 | B04 | [page](p112.png) |
| 113 | 40 | 140.9 | B04 | [page](p113.png) |
| 114 | 41 | 47.16 | B04 | [page](p114.png) |
| 115 | 42 | 241.83 | B04 | [page](p115.png) |
| 116 | 43 | 41.76 | None observed | [page](p116.png) |
| 117 | 44, 45 | 63.7 | None observed | [page](p117.png) |
| 118 | 46 | 53.15 | B04 | [page](p118.png) |
| 119 | 47 | 140.9 | B04 | [page](p119.png) |
| 120 | — | — | None observed | [page](p120.png) |

## Method and limits

- Rendered all 60 physical pages with PyMuPDF/fitz at 1.6x (115.2 dpi), saved full-page PNGs and 15 four-page contact sheets, and visually inspected every sheet.
- Additional full-page inspection of 70,108,109,113; high-resolution crops retained for collisions and survey header.
- Matched every nonempty source table paragraph after whitespace normalization on its mapped rendered page, including all final-row source paragraphs.
- Collected page/footnote coordinates and large-drawing lower bounds as supporting footer-clearance evidence. Drawing lower bound includes non-table rules and is conservative, not an automatically inferred table bbox.
- Read-only PDF/source-JSON review; no HWPX reads/writes, MCP, COM or delegation.
- No earlier PDF baseline was inspected; no issue is labeled chronologically preexisting. Source-present evidence only identifies what was already encoded in supplied tables.json.
- This is a layout review, not a substantive statistical, citation or source-authenticity audit. Red pending markers and intentionally blank result values were not counted as clipping.

PDF SHA-256: `50b3290b239e9b2b06e4b9ccd4aebd680d353e2fa19920262576f31948d986c4`
