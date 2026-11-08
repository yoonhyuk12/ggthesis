"""MAIN ONLY: after PDF review, keep two one-page tables intact on a new page."""
from pathlib import Path
import sys,re,json,zipfile
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p
O=Path(__file__).parent
TARGETS={'<표3-2>':'1234908531','<표4-4>':'1238233566'}
def main():
 src=O/'toc_restored.hwpx';out=O/'layout_ready.hwpx';audit=[]
 with zipfile.ZipFile(src) as z:
  name='Contents/section2.xml';x=z.read(name).decode('utf8');u=p.Units(x,set());parts=[]
  for i,q in enumerate(u.items):
   raw=q['xml']
   if q['tbl'] and q['cap'] in TARGETS:
    m=re.search(r'<hp:tbl\b[^>]*>',raw);assert m
    assert f'id="{TARGETS[q["cap"]]}"' in m.group()
    assert 'pageBreak="TABLE"' in m.group()
    modified=raw[:m.start()]+m.group().replace('pageBreak="TABLE"','pageBreak="NONE"')+raw[m.end():]
    modified=re.sub(r'<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>','',modified,flags=re.S)
    # Strip cache on both sides to prove the only structural edit is one attribute.
    clean=lambda s:re.sub(r'<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>','',s,flags=re.S)
    assert clean(raw).replace('pageBreak="TABLE"','pageBreak="NONE"',1)==modified
    audit.append({'caption':q['cap'],'table_id':TARGETS[q['cap']],'input_unit_index':i,'pageBreak':['TABLE','NONE'],'width_grid_text_font_unchanged':True,'removed_lineseg_arrays':raw.count('<hp:linesegarray')})
    raw=modified
   parts.append(raw)
  assert len(audit)==2
  newx=u.head+''.join(parts)+u.tail
  assert [q['text'] for q in u.items]==[q['text'] for q in p.Units(newx,set()).items]
  with zipfile.ZipFile(out,'w') as w:
   for zi in z.infolist():w.writestr(zi,newx.encode() if zi.filename==name else z.read(zi.filename))
 (O/'keep_two_tables_audit.json').write_text(json.dumps({'changes':audit,'scope':'Only table3-2 and4-4 pageBreak plus their paragraph caches; caption keepWithNext preserved','output':out.as_posix(),'needs_Hancom_PDF_verification':True},ensure_ascii=False,indent=2),encoding='utf8')
 print('PASS: two table pageBreak flags TABLE -> NONE, text and geometry unchanged; PDF check required')
if __name__=='__main__':main()
