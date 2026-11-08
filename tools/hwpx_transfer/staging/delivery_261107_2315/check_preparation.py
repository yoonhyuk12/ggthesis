"""Exercise prepared text-only edits against supplied XML dumps; no HWPX I/O."""
from pathlib import Path
import ast,json,re,sys,hashlib
from lxml import etree as E
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O.parents[3]/'tools/hwpx_transfer'))
import kjn_profile as k
HP='{'+k.NS['hp']+'}'
a=json.loads((O/'change_audit.json').read_text(encoding='utf8'))
u=json.loads((O/'base_section2.json').read_text(encoding='utf8'))
report={'compiled':[],'text_only_tables':[],'appendix_question_counts':[],'scope':'dump XML and Python syntax only; no HWPX opened or written'}
for filename in ['prepare_inputs.py','assemble.py','resolve_patch.py','verify_current.py']:
 ast.parse((O/filename).read_text(encoding='utf-8-sig'));report['compiled'].append(filename)
for item in a['tables']:
 if item['status']!='text_only':continue
 raw=next(x['xml'] for x in u if x['tbl'] and x['cap']==item['caption'])
 root=E.fromstring(k._wrap(raw).encode());table=next(root.iter(HP+'tbl'))
 before=[(dict(x.find(HP+'cellAddr').attrib),dict(x.find(HP+'cellSpan').attrib),dict(x.find(HP+'cellSz').attrib)) for x in table.iter(HP+'tc')]
 for c in item['changes']:
  cell=next(x for x in table.iter(HP+'tc') if x.find(HP+'cellAddr').get('rowAddr')==str(c['row']) and x.find(HP+'cellAddr').get('colAddr')==str(c['col']))
  txt=''.join(t.text or '' for t in cell.iter(HP+'t'));assert re.sub(r'\s+','',txt)==re.sub(r'\s+','',c['old'])
  ts=list(cell.iter(HP+'t'));assert ts
  ts[0].text=re.sub(r'<br\s*/?>','',c['new'])
  for x in list(ts[0]):ts[0].remove(x)
  for t in ts[1:]:t.text=''
  for seg in list(cell.iter(HP+'linesegarray')):seg.getparent().remove(seg)
 after=[(dict(x.find(HP+'cellAddr').attrib),dict(x.find(HP+'cellSpan').attrib),dict(x.find(HP+'cellSz').attrib)) for x in table.iter(HP+'tc')]
 assert before==after
 report['text_only_tables'].append({'caption':item['caption'],'changed_cells':len(item['changes']),'geometry_preserved':True})
start=next(i for i,x in enumerate(u) if re.sub(r'\s+','',x['text']).startswith('부록(도입현장)'))
end=next(i for i in range(start,len(u)) if u[i]['text']=='Abstract')
txt=re.sub(r'\s+','',''.join(x['text'] for x in u[start:end]))
blocks=json.loads((O/'apx1.blocks.json').read_text(encoding='utf8'))['blocks']
for b in blocks:
 if b['type']=='table':
  for row in b['rows']:
   if not re.fullmatch(r'[BCD]-\d+',row[0]):continue
   wanted=2 if row[0].startswith('B-') else 1
   actual=txt.count(re.sub(r'\s+','',row[1]));assert actual==wanted,(row[0],actual,wanted)
   report['appendix_question_counts'].append({'question':row[0],'expected':wanted,'actual':actual})
report['ok']=True
(O/'preparation_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
