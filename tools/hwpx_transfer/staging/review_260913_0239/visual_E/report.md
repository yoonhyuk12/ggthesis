# FINAL verdict — layout_final.pdf physical pages 1–55: PASS

Final inspected target: `../layout_final.pdf`, 146 pages, SHA256 `8c9e61fbf8cc9bd443f713be3d55237378881217bdd621c889b00287b9c1f708`.

All physical pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55 were actually inspected in the final contact sheets. All eight final table pages (26, 29, 30, 38, 44, 45, 50, 52) and four figure pages (13, 14, 21, 51) were also individually opened at readable resolution.

Final evidence: `layout_final/contact_001_006.png` through `layout_final/contact_055_055.png` (10 sheets), `layout_final/p001.png` through `layout_final/p055.png`, and `layout_final/audit.json` (page text and cell extraction). Final tables 2-1 through 2-6 and 3-1 through 3-2 each remain wholly on one page; no nested tables or table continuation/header-repeat cases occur in this range. Last rows, merged labels, complete cells, notes, following body text and footer separation PASS.

|Physical|Printed|Table|Final bbox (PDF points, top-left origin)|Result|
|---|---|---|---|---|
|26|14|2-1|(80, 149, 512, 644)|PASS|
|29|17|2-2|(82, 273, 512, 432)|PASS|
|30|18|2-3|(80, 335, 512, 677)|PASS|
|38|26|2-4|(80, 128, 512, 333)|PASS|
|44|32|2-5|(80, 128, 512, 655)|PASS|
|45|33|2-6|(80, 244, 512, 550)|PASS|
|50|38|3-1|(80, 128, 512, 372)|PASS|
|52|40|3-2|(80, 211, 511, 446)|PASS|

The lowest final table is physical page 30 (2-3), bottom y=677; footer starts about y=742, leaving 65 points. Its final row (이동건/Chong, 노력기대·PEOU가 수용의도에 정(+) 영향) and the following body line are fully visible. Figure 1-1, 1-2, 1-3 and 3-1 labels, arrows/branches, source notes and captions PASS.

Initial observations are RESOLVED: chapter 2 now begins at the top of physical page 22; the previously blank physical page 47 now contains the chapter 3 opening. Sparse carryover pages 31, 35, 43 and 54 remain legible and are not clipping failures. No concrete unresolved table/figure defect found in assigned range.

Scope limit: coordinator will export `publication.pdf` after frontmatter CELL-to-NONE correction and owns pixel equivalence verification of that later export. This report certifies the stated layout_final hash, not an unseen later PDF. HWPX/COM, manuscript, source calculations and statistical design were not modified or re-reviewed.

---

## Historical initial-export evidence (superseded by final verdict above)

# Visual review E — physical PDF pages 1–55

Initial target: `../final.pdf` (148 pages), SHA256 `db39454f96fdd488e798f13f3d7b4fbfa76d4b53ef6a50e3226be25c6d9e7d73`.
Status: initial inspection complete; coordinator requested final2 reflow validation before settlement.

## Coverage and evidence

Actually inspected physical pages: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55.

All pages rendered using PyMuPDF at 108 dpi to `p001.png`–`p055.png`. All ten `contact_*.png` sheets were visually inspected. Table pages 26, 29, 30, 38, 44, 45, 51, 53 and figure pages 13, 14, 21, 52 were additionally opened individually at legible resolution. `pages.json` contains page text; `table_cells.json` contains extracted row/cell content, including last rows. No source, calculations or statistical design were re-reviewed. No HWPX or COM operations performed.

## Tables: PASS

Coordinates below are PDF points from upper-left. Each table is wholly on one page, with no continuation requiring header repetition; no nested tables appear within this assigned range. Headers, merged cells, last rows, notes and following paragraphs are visibly intact. No clipped row, overlapping cell text, table/footer intrusion or hidden following paragraph found.

| Physical page | Printed page | Table | Bounding box | Last-row check |
|---|---|---|---|---|
|26|14|2-1|(80,128,512,623)|김용선(2022), 구축·운영, ○ ○ — — intact|
|29|17|2-2|(82,232,512,391)|경보 피로 and both comparison cells intact|
|30|18|2-3|(80,294,512,635)|이동건(2024); Chong et al.(2023), 정(+) 영향 intact; merged first-column continuation intact|
|38|26|2-4|(80,128,512,333)|연간 유지보수 / 도입가의 8% / 인건비 별도 intact|
|44|32|2-5|(80,128,512,655)|Zhou et al.(2023), H2의 근거 intact; following paragraph safely below table|
|45|33|2-6|(80,244,512,550)|보조 분석 / H2 탐색적 intact|
|51|39|3-1|(80,128,512,372)|위험 대응 적시성 / R5 / 검증 분리 설계 intact|
|53|41|3-2|(80,211,511,446)|지속성·감사부 / JSON / SQLite(WAL) intact|

Footer text begins approximately y=742 points. Even the lowest table (page 44, y=655) leaves about 87 points to the footer, and its following body text remains separate. Long author/header wrapping on pages 26 and 30 is readable, although the closing parenthesis in the long institutional author on page 26 occupies a separate line.

## Figures: PASS

Physical 13 / figure 1-1: bars, labels, source note and caption visible. Physical 14 / figure 1-2: full trend plot, date annotations, source note and caption visible. Physical 21 / figure 1-3: all five boxes, connecting arrows, concluding note and caption readable. Physical 52 / figure 3-1: four-stage pipeline, SEND/BLOCK branches, history box and caption readable without overlap or clipping.

## Other layout observations for main

- Physical page 47 / printed 35 is completely blank except the footer (extraction exactly `- 35 -`). Evidence: `p047.png`, `contact_043_048.png`. Review whether this is intentional; this is not a table failure.
- Physical page 21 / printed 9 starts chapter 2 near the bottom after figure 1-3 and its preceding-chapter closing paragraph. Chapter heading bbox approximately (78,610,235,626), first section heading (78,655,470,675), then first subsection begins on physical 22. Evidence `p021.png`; flag for main's chapter-opening layout judgement.
- Pages 31, 35, 43 and 55 contain short carryover text and large whitespace. Content is visible; no clipping detected.
