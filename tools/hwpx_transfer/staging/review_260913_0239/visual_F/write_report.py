from pathlib import Path
import fitz,json
out=Path('tools/hwpx_transfer/staging/review_260913_0239/visual_F'); d=fitz.open(out.parent/'final.pdf')
nums=[63,65,66,67,69,71,75,78,82,84,85,87,88,89,91,98,100]
rows=[]
for n in nums:
 p=d[n-1]; tabs=p.find_tables().tables
 rows.append({'page':n,'tables':[{'bbox':t.bbox,'rows':t.extract()} for t in tabs]})
(out/'table_cells.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# Visual F review — initial final.pdf, awaiting final2.pdf

Read-only PDF layout review, physical pages 56–100. All 45 pages visually inspected via five 3×3 contact sheets. Table pages enlarged and read: 63, 65, 66, 67, 69, 71, 75, 78, 82, 84, 85, 87, 88, 89, 91, 98, 100 (17 pages; page 85 has B and C tables). Automated table detection misses page 71 and subdivides some tables; visual inventory governs. No nested tables occur in this range. Diagram/image pages 57, 60, 64, 76 enlarged and inspected.

Explicit inspected physical page list: 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100.

## Results

No clipped last rows, overlapping cell text, footer/page-number intrusion, or missing visible row endings found. All tables in scope are contained on single pages; repeated continuation headers are not applicable to these tables. Extracted cell/row evidence is in table_cells.json; complete page text in extraction.json. Source/statistical design not re-reviewed; empty result cells are visibly intentional templates, not inferred clipping. Diagrams have readable labels, complete boxes/arrows and captions; screenshot p64 is lower-resolution source imagery but is not cut off.

## Initial pagination/readability findings

Coordinates below are PDF points, top-left origin, approximate full affected regions.

- p84 (printed 72), bbox (78,540,513,560): B-question heading is separated from its table on p85. Keep the heading with the B-table. Evidence page_084.png and page_085.png.
- p85–86 (printed 73–74): C-table note begins below table on p85, bbox (78,671,520,690), with its final phrase alone on otherwise empty p86, bbox (78,108,275,123). This is a conspicuous orphan-note page, not text loss. Evidence page_085.png and page_086.png.
- p99–100 (printed 87–88): table 5-2 caption and panel A introduction are on p99, approximately (78,382,513,421), but the table starts at p100 y111. Keep caption/panel intro with table. Evidence page_099.png and page_100.png.
- p69 (printed 57): narrow English headers split Precision, Recall, Accuracy; Recall is Recal / l, approximately (224,153,265,195). Readable but poor wrapping; widen header columns within preserved overall table width if feasible. Evidence page_069.png.
- p100 (printed 88): Cronbach header breaks apostrophe/s and isolates final parenthesis, bbox (332,111,395,196). Readable but poor header wrapping. Evidence page_100.png.
- p84 subsection heading has no visual preceding blank line; coordinator has already announced a global heading-blank correction, so final2 must supersede this observation.

## Evidence

- contact_56_64.png, contact_65_73.png, contact_74_82.png, contact_83_91.png, contact_92_100.png: all assigned pages.
- page_056.png through page_100.png: 1.6× raster evidence (about 115 dpi).
- extraction.json, table_cells.json: PDF text and detected row/cell content.
- hashes.json: input hashes taken before rendering.
- render.py: reproducible render script; only visual_F artifacts changed.

Final acceptance pending coordinator-requested final2 review. No HWPX, COM, manuscript or source edits made.
'''
(out/'report.md').write_text(report,encoding='utf-8')
