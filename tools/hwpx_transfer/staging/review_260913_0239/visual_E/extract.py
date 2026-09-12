from pathlib import Path
import fitz,json
base=Path('tools/hwpx_transfer/staging/review_260913_0239');out=base/'visual_E'; d=fitz.open(base/'final.pdf')
a=[]
for n in [26,29,30,38,44,45,51,53]:
 p=d[n-1];ts=p.find_tables().tables
 a.append({'page':n,'tables':[{'bbox':list(t.bbox),'rows':t.row_count,'cols':t.col_count,'cells':t.extract()} for t in ts]})
(out/'table_cells.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
