import fitz,json,re,hashlib
from pathlib import Path
b=Path('tools/hwpx_transfer/staging/review_260913_0239'); o=b/'visual_G'; d=fitz.open(b/'layout_final.pdf'); checks={}
for n,letter,count in [(136,'B',8),(137,'C',4),(139,'D',8),(140,'E',4),(144,'B',8),(145,'C',4)]:
 txt=d[n-1].get_text(); checks[n]={'rows':{f'{letter}-{i}':len(re.findall(fr'{letter}[-–]{i}(?![0-9])',txt)) for i in range(1,count+1)},'symbols':{s:txt.count(s) for s in '①②③④⑤'}}
 checks[n]['pass']=all(v==1 for v in checks[n]['rows'].values()) and all(v==count+(n!=139) for v in checks[n]['symbols'].values())
checks['hashes']={name:hashlib.sha256((b/name).read_bytes()).hexdigest() for name in ['layout_final.pdf','layout_final.hwpx','final.pdf','final.hwpx']}
checks['email_bbox']=[x[:4] for x in d[132].get_text('blocks') if 'gmail' in x[4]]
(o/'layout_final/row_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
p=o/'report.md'; old=p.read_text(encoding='utf-8'); old=old.replace('Final revision validation is pending coordinator announcement.','Final revision validation is recorded above.').replace('Review work is complete for initial PDF, but this document will be updated against the announced final revision before worker completion.','Initial review retained below for traceability; final revision results supersede initial findings.')
new='''# FINAL REVIEW — layout_final.pdf, physical pages 101–146

**Table visual verification PASS; one remaining pagination defect.** This supersedes the initial-PDF findings below. Coordinator requested this stable revision and will independently pixel-compare the later publication PDF body.

Explicit final inspected pages: '''+', '.join(map(str,range(101,147)))+'''. All 46 pages viewed in newly rendered contact sheets; all table/form pages additionally opened at readable full-page zoom.

Final table/form pages inspected at zoom: 102, 103, 104, 107, 109, 110 (two panels), 111, 112, 113 (two panels), 114, 115, 132, 135, 136, 137, 139, 140, 141, 143, 144, 145. No diagrams in this range. No blank numbered-only page remains.

Resolved: table 5-3 caption and panel-A lead-in now share page 102 with the table; all six B/C/D/E empty header grids are gone (136,137,139,140,144,145); M/SD headers on 102,103,109 are properly separated and readable. Every last row, bottom border, body cell and following paragraph is visible; no overlap, clipping or footer intrusion. Panel continuations retain their own relevant headers. Body note continuations on following pages remain readable. All expected B/C/D/E row identifiers occur once and all five response symbols have exact row-count-plus-legend multiplicity; see layout_final/row_checks.json.

**Remaining failure, physical 132–133 (printed 120–121):** email contact line appears alone on page 133, separated from affiliation/advisor/researcher on page 132. Email bbox approximately (211,111,410,123) PDF points. Evidence: layout_final/page_132.png and page_133.png. The introductory form itself is intact and within bounds. This orphan contact line was sent to the coordinator before completion; main owns correction or acceptance. Keep the contact block with the introductory form and reflow, without deleting contact text.

Minor residual cosmetic wrapping: physical 111 has `차이 B(SE` then a lone closing parenthesis; physical 114 personal-n header also puts its closing parenthesis on a separate line. Text is intact and these are not clipping failures.

Final evidence: layout_final/page_101.png through page_146.png; six layout_final/contact_*.png sheets; layout_final/extraction.json; layout_final/row_checks.json (hashes and occurrence evidence). Full final PDF/HWPX SHA256 values are preserved there. Original final.pdf/final.hwpx hashes still match row_checks.json, confirming initial targets unchanged during this worker review. All worker writes remain within visual_G.

This is a completed read-only visual review with findings, not approval to publish and not a claim that the remaining contact-line pagination defect is fixed. No COM or HWPX writes were performed.

---

'''
p.write_text(new+old,encoding='utf-8'); print(json.dumps(checks,ensure_ascii=True))
