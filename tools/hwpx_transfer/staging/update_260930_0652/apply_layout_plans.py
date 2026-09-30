"""Coordinator-only application of checked layout plans to targeted anchors."""
from pathlib import Path
import sys,json,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H='{http://www.hancom.co.kr/hwpml/2011/head}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def main():
 source=Q/'toc3.hwpx'
 with zipfile.ZipFile(source) as z:raw=z.read('Contents/section2.xml');headraw=z.read('Contents/header.xml')
 root=E.fromstring(raw);header=E.fromstring(headraw);ps=list(root.iter(P+'p'));tables=list(root.iter(P+'tbl'));anchors=set();logs=[];header_changed=False
 def mark(p):
  ancestors=[p]+list(p.iterancestors(P+'p'));top=next(x for x in reversed(ancestors) if x.getparent()==root)
  anchors.add(ps.index(top))
  for x in top.iter(P+'p'):
   for n in x.findall(P+'linesegarray'):x.remove(n)
 for filename in (sys.argv[1:] or ('front_layout_plan.json','back_layout_plan.json')):
  plan=json.loads((Q/filename).read_text(encoding='utf-8'))
  for op in plan['tables']:
   if op.get('status')=='hold':continue
   table=tables[op['table_idx']];widths=op['widths'];total=sum(widths)
   assert len(widths)==int(table.get('colCnt'))
   if 'total_width' in op:assert total==op['total_width']
   if op['table_idx'] not in (44,51):assert total==int(table.find(P+'sz').get('width'))
   table.find(P+'sz').set('width',str(total))
   for row in table.findall(P+'tr'):
    for cell in row.findall(P+'tc'):
     addr=cell.find(P+'cellAddr');span=cell.find(P+'cellSpan');c=int(addr.get('colAddr'));n=int(span.get('colSpan'))
     if 'old_widths' in op:assert int(cell.find(P+'cellSz').get('width'))==sum(op['old_widths'][c:c+n])
     cell.find(P+'cellSz').set('width',str(sum(widths[c:c+n])))
     if op['table_idx'] in (8,15) and 'row_min_height_proposal' in op:
      rr=int(addr.get('rowAddr'));rs=int(span.get('rowSpan'))
      cell.find(P+'cellSz').set('height',str(sum(op['row_min_height_proposal'][rr:rr+rs])))
     if 'cell_margin_lr' in op:
      cell.set('hasMargin','1');m=cell.find(P+'cellMargin');m.set('left',str(op['cell_margin_lr']));m.set('right',str(op['cell_margin_lr']))
   if op['table_idx'] in (8,15) and 'row_min_height_proposal' in op:table.find(P+'sz').set('height',str(sum(op['row_min_height_proposal'])))
   mark(next(table.iterancestors(P+'p')));logs.append(op)
  for op in plan.get('paragraph_styles',[]):
   assert op['section']=='Contents/section2.xml';p=ps[op['idx']]
   assert p.get('paraPrIDRef')==str(op['old_paraPrIDRef'])
   if 'old_text' in op:assert own(p)==op['old_text']
   if 'precheck' in op:assert own(p)==op['precheck']['old_text']
   p.set('paraPrIDRef',str(op['new_paraPrIDRef']));mark(p)
  for xml in plan.get('new_paraPr_xml',[]):
   node=E.fromstring(xml.encode());lst=header.find('.//'+H+'paraProperties')
   assert not any(n.get('id')==node.get('id') for n in lst);lst.append(node);lst.set('itemCnt',str(len(lst)));header_changed=True
 nodes=[n for n in elements(raw) if n['name']=='hp:p']
 for idx in sorted(anchors,reverse=True):
  n=nodes[idx];raw=raw[:n['start']]+E.tostring(ps[idx],encoding='UTF-8',with_tail=False)+raw[n['end']:]
 updates={'Contents/section2.xml':raw}
 if header_changed:updates['Contents/header.xml']=E.tostring(header,encoding='UTF-8',xml_declaration=True,standalone=True)
 (Q/'layout2.hwpx').write_bytes(raw_zip_patch(source.read_bytes(),updates))
 (Q/'layout2_log.json').write_text(json.dumps(dict(anchors=sorted(anchors),tables=logs),ensure_ascii=False,indent=2),encoding='utf-8')
 print('Applied',len(logs),'tables;',len(anchors),'target anchors')
if __name__=='__main__':main()
