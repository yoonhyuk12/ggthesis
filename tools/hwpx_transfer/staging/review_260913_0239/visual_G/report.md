# FINAL REVIEW — layout_final.pdf, physical pages 101–146

**Table visual verification PASS; one remaining pagination defect.** This supersedes the initial-PDF findings below. Coordinator requested this stable revision and will independently pixel-compare the later publication PDF body.

Explicit final inspected pages: 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146. All 46 pages viewed in newly rendered contact sheets; all table/form pages additionally opened at readable full-page zoom.

Final table/form pages inspected at zoom: 102, 103, 104, 107, 109, 110 (two panels), 111, 112, 113 (two panels), 114, 115, 132, 135, 136, 137, 139, 140, 141, 143, 144, 145. No diagrams in this range. No blank numbered-only page remains.

Resolved: table 5-3 caption and panel-A lead-in now share page 102 with the table; all six B/C/D/E empty header grids are gone (136,137,139,140,144,145); M/SD headers on 102,103,109 are properly separated and readable. Every last row, bottom border, body cell and following paragraph is visible; no overlap, clipping or footer intrusion. Panel continuations retain their own relevant headers. Body note continuations on following pages remain readable. All expected B/C/D/E row identifiers occur once and all five response symbols have exact row-count-plus-legend multiplicity; see layout_final/row_checks.json.

**Remaining failure, physical 132–133 (printed 120–121):** email contact line appears alone on page 133, separated from affiliation/advisor/researcher on page 132. Email bbox approximately (211,111,410,123) PDF points. Evidence: layout_final/page_132.png and page_133.png. The introductory form itself is intact and within bounds. This orphan contact line was sent to the coordinator before completion; main owns correction or acceptance. Keep the contact block with the introductory form and reflow, without deleting contact text.

Minor residual cosmetic wrapping: physical 111 has `차이 B(SE` then a lone closing parenthesis; physical 114 personal-n header also puts its closing parenthesis on a separate line. Text is intact and these are not clipping failures.

Final evidence: layout_final/page_101.png through page_146.png; six layout_final/contact_*.png sheets; layout_final/extraction.json; layout_final/row_checks.json (hashes and occurrence evidence). Full final PDF/HWPX SHA256 values are preserved there. Original final.pdf/final.hwpx hashes still match row_checks.json, confirming initial targets unchanged during this worker review. All worker writes remain within visual_G.

This is a completed read-only visual review with findings, not approval to publish and not a claim that the remaining contact-line pagination defect is fixed. No COM or HWPX writes were performed.

---

# Visual G — physical pages 101–148

Initial target: `../final.pdf` (148 pages); read-only review, no COM or HWPX mutation. Final revision validation is recorded above.

## Inspection coverage

Visually inspected physical pages: 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148.

Full-page readable zoom inspection of all table/form pages: 101, 103, 104, 105, 108, 110, 111 (two panels), 112, 113, 114, 115 (two panels), 117, 135, 137, 138, 139, 141, 142, 143, 145, 146, 147. Table detector missed the enclosing single-cell forms on 137 and 145; these were nevertheless visually inspected. No diagrams occur in this range.

## Findings

Coordinates are PDF points, origin at physical page top-left, approximate unless in extraction.json.

1. **Layout failure: orphan caption.** Physical 102, printed 90, caption `<표 5-3> 주요 변수의 기술통계(집단별)` and panel A lead-in at approximately (80,286,514,316); actual table starts physical 103 at (80,111,512,577). Large unused space remains on 102. Keep caption/panel lead-in with table. Evidence: page_102.png and page_103.png.
2. **Layout defect: extra nested header grid.** Physical 138 and 146 at (333,272,498,299), 139 and 147 at (333,288,498,346), 141 at (333,161,498,188), 142 at (333,223,498,250). An empty two-row grid appears below the scale labels; its vertical boundaries sit halfway across the response columns instead of aligning with them. This is visible in every B/C/D/E response grid in this range. The labels above and the numbered answer cells below remain readable; this is a header geometry defect, not demonstrated text loss. Evidence: six header_detail_*.png crops and respective page PNGs.
3. **Layout defect: numbered empty pages.** Physical 116 (printed 104) and 129 (printed 117) contain only footer page numbers. Physical 116 lies between analysis and the next section; physical 129 precedes references. Confirm whether these are intentional; otherwise remove excess breaks. Evidence: page_116.png, page_129.png; extraction confirms only footer text.
4. **Minor header wrapping failure.** Physical 103 header `평균(M)` remains on one line; physical 104 `표준편차(` / `SD)` splits the opening parenthesis from its unit, and physical 110 `원표준편차(S` / `D)` breaks SD. This conflicts with the required label/new-paragraph-unit layout. Example bboxes: 103 (285,111,344,153); 104 (447,173,512,215); 110 (322,453,373,500). Several narrow labels elsewhere also wrap awkwardly but remain readable.

## Clipping/continuation checks

PASS: all inspected table bottom borders, last rows, and final cell sentences remain visible, with no table/body overlap or footer/page-number intrusion. B-8 (138/146), C-4 (139/147), D-8 (141), E-4 (142), and A-6 options (137/145) are complete. Lowest B-table border is y=690.09 points; the footer is below it with visible clearance. Introductory enclosing forms on 135/143 and nested title frames fit their bounds.

Panels on 103–104, 110–111, 112–113, 114–115 are separate panels with their own column headers; no body row is split across these pages. Panel introductions/notes can cross pages (110 panel B introduction to 111, 114 note to 115), but no repeated same-table header omission is demonstrated within this range. Page 101 begins a table whose preceding caption is outside the assigned range, so cross-boundary caption validation belongs to the adjacent reviewer.

Supplemental text extraction: each expected B/C/D/E row identifier occurs exactly once per table page. Each response symbol ①–⑤ occurs eight times on D page 141, nine times on B pages (eight rows plus instruction legend), and five times on C/E pages (four rows plus legend); no row/symbol loss. `row_checks.json` preserves exact counts. Main owns complete HWPX-to-PDF marker multiplicity/source-preservation verification; this report does not claim an independent full-document source audit.

## Evidence

- Six contact sheets: contact_101_108.png, contact_109_116.png, contact_117_124.png, contact_125_132.png, contact_133_140.png, contact_141_148.png.
- Individual readable 108-dpi page PNGs: page_101.png through page_148.png.
- Header detail crops at 216 dpi: header_detail_138/139/141/142/146/147.png.
- extraction.json: PDF text and detected table bounds per page.
- row_checks.json: row/response occurrence checks and reviewed PDF/HWPX SHA256 values.
- render.py and check_rows.py reproduce evidence; all writes are confined to visual_G.

No statistical design or approved calculations were re-reviewed. Initial review retained below for traceability; final revision results supersede initial findings.

## Exact header fix diagnosis (coordinator-requested)

`nested_xml.json` compares base.hwpx and final.hwpx. These six response tables are actually flat 12-column tables with a three-row header, not nested hp:tbl objects. The unwanted geometry already exists in base.hwpx: row 0 title spans rows 0–2, five response labels each span two columns; rows 1 and 2 contain 19 entirely empty cells, exposing half-width columns with alternating borders. This is inherited template geometry rather than content loss introduced by the transfer.

Minimal structural fix, only on the six stable table IDs in `header_fix_plan.json`:

1. Assert direct rows 1 and 2 contain no hp:t text, nested tables, images, or nonempty controls. Our text/nested checks pass; main should guard other controls before removal.
2. Remove only these two empty hp:tr elements. Change rowCnt from 11 to 9 for B/D and 7 to 5 for C/E. Keep colCnt=12 and all colAddr/colSpan values and all cell widths unchanged.
3. Change row 0 title cell rowSpan from 3 to 1; set its minimum height to the existing row-0 response-label cell height (4532; C tables 5947). Preserve every header text run/font and its paragraph style.
4. For original body rows 3 onward, subtract 2 from every cellAddr.rowAddr. Preserve question text, response symbols, cell spans, borders, heights, paragraph order and fonts.
5. Adjust table hp:sz.height by the removed header height (2464; C tables 5294), then remove affected header/anchor linesegarray caches and let Hancom reflow. Do not shrink body rows or alter width 39491.
6. Simulated resulting occupancy grids are complete and nonoverlapping for all six tables. Main must perform actual COM save/PDF export and verify header/bottom positions. Exact before/after sizes and IDs are in header_fix_plan.json.

A blanket column rewrite is unnecessary: existing response-label and numbered answer columns already align. Removing the empty rows removes the offset half-column grid while retaining the established widths and all nonempty content.
