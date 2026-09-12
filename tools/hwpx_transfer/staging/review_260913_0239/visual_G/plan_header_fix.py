import json
from pathlib import Path
p=Path('tools/hwpx_transfer/staging/review_260913_0239/visual_G'); d=json.loads((p/'nested_xml.json').read_text(encoding='utf-8')); out=[]
for t in d['final.hwpx']:
 rows=t['rows']; title=rows[0][0]; h=int(rows[0][1]['size']['height']); delta=int(title['size']['height'])-h
 assert all(not c['text'].strip() and not c['nested'] for row in rows[1:3] for c in row)
 newrows=[rows[0]]+rows[3:]; occupied=set()
 for r,row in enumerate(newrows):
  for c in row:
   ca=int(c['addr']['colAddr']); cs=int(c['span']['colSpan']); rs=1 if r==0 else int(c['span']['rowSpan'])
   for rr in range(r,r+rs):
    for cc in range(ca,ca+cs):
     assert (rr,cc) not in occupied; occupied.add((rr,cc))
 assert len(occupied)==len(newrows)*12
 out.append({'id':t['attrs']['id'],'section':t['section'],'index_in_final':t['index'],'title':title['text'],'rowCnt_before':len(rows),'rowCnt_after':len(newrows),'colCnt_preserve':12,'width_preserve':t['size']['width'],'new_header_height':h,'removed_header_height':delta,'table_height_before':t['size']['height'],'table_height_after':int(t['size']['height'])-delta,'empty_cells_removed':sum(len(r) for r in rows[1:3]),'grid_simulation_pass':True})
(p/'header_fix_plan.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=True,indent=2))
