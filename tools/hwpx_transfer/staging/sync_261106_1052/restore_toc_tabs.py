"""MAIN ONLY: restore five lost title/page tabs, preserving all existing TOC entries."""
from pathlib import Path
import sys,re,json,zipfile
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p,table_layout
O=Path(__file__).parent
def main():
 src=O/'image_ready.hwpx';out=O/'toc_restored.hwpx'
 plan=json.loads((O/'toc_tabs_plan.json').read_text(encoding='utf8'))
 with zipfile.ZipFile(src) as z:
  name='Contents/section1.xml';x=z.read(name).decode('utf8');u=p.Units(x,set());audit=[]
  assert sum('<hp:tab' in q['xml'] for q in u.items[:132])==112
  parts=[q['xml'] for q in u.items]
  for target in plan['targets']:
   i=target['unit_index'];q=u.items[i];old=q['xml'];assert q['text']==target['old_text'] and '<hp:tab' not in old
   m=re.search(r'(<hp:t>)([^<]+?)(\d+)(</hp:t>)',old);assert m
   title,page=m.group(2),m.group(3)
   assert title.strip()==target['title'] and page==target['page']
   # Same width formula as the established toc_line assembler; Hancom reflows it.
   width=max(0,36852-table_layout.text_width(title,11.0)-table_layout.text_width(page,11.0))
   tab=f'<hp:tab width="{int(width)}" leader="3" type="2"/>'
   new=old[:m.start()]+m.group(1)+title+tab+page+m.group(4)+old[m.end():]
   new=re.sub(r'<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>','',new,flags=re.S)
   parts[i]=new;audit.append({'unit_index':i,'title':title.strip(),'old_page':page,'tab_width':int(width)})
  newx=u.head+''.join(parts)+u.tail
  nu=p.Units(newx,set());assert [q['text'] for q in u.items]==[q['text'] for q in nu.items]
  assert sum('<hp:tab' in q['xml'] for q in nu.items[:132])==117
  assert [i for i,(a,b) in enumerate(zip(u.items,nu.items)) if a['xml']!=b['xml']]==[22,23,24,25,26]
  with zipfile.ZipFile(out,'w') as w:
   for zi in z.infolist():w.writestr(zi,newx.encode() if zi.filename==name else z.read(zi.filename))
 (O/'toc_tabs_audit.json').write_text(json.dumps({'changed':audit,'text_unchanged':True,'before_tab_entries':112,'after_tab_entries':117,'output':out.as_posix()},ensure_ascii=False,indent=2),encoding='utf8')
 print('PASS: restored 5 missing TOC tabs; 117 tabbed entries; all title/page text unchanged')
if __name__=='__main__':main()
