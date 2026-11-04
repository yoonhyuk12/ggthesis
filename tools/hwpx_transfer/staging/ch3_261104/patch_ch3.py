"""Main-only targeted chapter patch; preserve original table grids and other chapters."""
from pathlib import Path
import sys,json,re,difflib,html,zipfile,hashlib
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
import kjn_profile as k
base=sorted((ROOT/'00. hwpx').glob('[0-9]*.hwpx'))[-1]
pt=p.Patcher(str(base),str(OUT/'assembled.hwpx'),[],None)
bu=p.Units(pt.s2,set()); fu=p.Units(pt.fresh_s2,set())
def bounds(units):
 a=next(i for i,u in enumerate(units.items) if re.match(r'^제\s*3\s*장\s',u['text']))
 b=next((i for i,u in enumerate(units.items[a+1:],a+1) if re.match(r'^제\s*4\s*장\s',u['text']) or u['text'].replace(' ','').startswith('참고문헌')),len(units.items))
 return a,b
ba,bb=bounds(bu);fa,fb=bounds(fu)
old=bu.items[ba:bb]; new=fu.items[fa:fb]
used=set(); output=[];changes=[]
def clean(x):return re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',x,flags=re.S)
def cells(x):return re.findall(r'<hp:tc\b.*?</hp:tc>',x,re.S)
def shape(x):
 return [re.findall(r'<hp:cell(?:Addr|Span)\b[^>]*/>',c) for c in cells(x)]
def addr(c):
 return tuple(int(re.search(a+'="(\\d+)"',c).group(1)) for a in ['rowAddr','colAddr'])
def mapped_cells(old,new):
 oc=cells(old);nc={addr(c):c for c in cells(new)}
 usedcoords=set();pairs=[]
 for c in oc:
  rc=addr(c)
  if rc not in nc:raise ValueError('missing cell origin '+str(rc))
  pairs.append((c,nc[rc]));usedcoords.add(rc)
  row,col=rc
  rs=int(re.search(r'rowSpan="(\d+)"',c).group(1));cs=int(re.search(r'colSpan="(\d+)"',c).group(1))
  for r in range(row,row+rs):
   for cc in range(col,col+cs):
    if (r,cc)==rc:continue
    if (r,cc) in nc:
     if p.nows(text(nc[(r,cc)])):raise ValueError('nonempty merged continuation '+str((r,cc)))
     usedcoords.add((r,cc))
 if set(nc)!=usedcoords:raise ValueError('unmapped new cells')
 return pairs
def text(x):return k.plain_texts(x)
def patchcell(old,new):
 if p.nows(text(old))==p.nows(text(new)):return old
 value=text(new)
 matches=list(re.finditer(r'(<hp:t(?:\s[^>]*)?>)(.*?)(</hp:t>)',old,re.S))
 if not matches:raise ValueError('Changed empty cell requires explicit handling')
 for j,m in reversed(list(enumerate(matches))):
  old=old[:m.start()]+m.group(1)+(p.esc(value) if j==0 else '')+m.group(3)+old[m.end():]
 return clean(old)
for ni,n in enumerate(new):
 candidates=[(i,o) for i,o in enumerate(old) if i not in used and o['tbl']==n['tbl'] and p.nows(o['text'])==p.nows(n['text']) and ('<hp:pic' in o['xml'])==('<hp:pic' in n['xml'])]
 if candidates and '<hp:pic' not in n['xml']:
  i,o=candidates[0];used.add(i);output.append(clean(o['xml']));continue
 if n['tbl']:
  if n['cap']=='<표3-9>':
   output.append(pt.take_fresh(n['xml']))
   changes.append({'kind':'new_applicability_table','caption':n['cap'],'replaces':'old cost table; intentional new grid'})
   continue
  candidates=[]
  for i,o in enumerate(old):
   if i in used or not o['tbl'] or o['cap']!=n['cap']:continue
   mapped_cells(o['xml'],n['xml'])
   candidates.append((difflib.SequenceMatcher(None,p.nows(o['text']),p.nows(n['text']),autojunk=False).ratio(),i,o))
  if not candidates:raise ValueError('No compatible original grid for '+n['cap'])
  fixed=[c for c in candidates if c[2]['cap']==n['cap']]
  score,i,o=fixed[0] if n['cap']=='<표3-4>' and fixed else max(candidates,key=lambda z:z[0])
  if score<.35 and n['cap']!='<표3-4>':raise ValueError('Ambiguous table '+n['cap'])
  used.add(i);xml=o['xml']
  for before,after in mapped_cells(xml,n['xml']):xml=xml.replace(before,patchcell(before,after),1)
  output.append(clean(xml));changes.append({'kind':'table_cells','caption':n['cap'],'old_caption':o['cap'],'similarity':score});continue
 output.append(pt.take_fresh(n['xml']))
 changes.append({'kind':'fresh_changed_or_new','text':n['text']})
start=bu.spans[ba][0];end=bu.spans[bb][0]
prefix,suffix=pt.s2[:start],pt.s2[end:]
pt.s2=prefix+''.join(output)+suffix
assert pt.s2.startswith(prefix) and pt.s2.endswith(suffix)
assert '<hp:tbl' not in ''.join(output) or 'pageBreak="CELL"' not in ''.join(output)
def toc_title(u):
 return k.plain_texts(u['xml'].split('<hp:tab',1)[0]).strip()
def toc_keys(units):
 result={};inside=False;sec=''
 for u in units.items:
  title=toc_title(u)
  if re.match(r'^제\s*3\s*장',title):inside=True
  elif re.match(r'^제\s*\d+\s*장',title):inside=False
  cap=re.match(r'^<(표|그림)\s*3-\d+>',title)
  if cap:key=p.nows(cap.group())
  elif inside:
   h=re.match(r'^제\s*(\d+)\s*(장|절|항)',title)
   if not h:continue
   if h[2]=='절':sec=h[1]
   key='toc:'+sec+':'+h[2]+h[1]
  else:continue
  result[key]=(u,title)
 return result
bt=toc_keys(p.Units(pt.s1,set()));ft=toc_keys(p.Units(pt.fresh_s1,set()))
for key,(u,title) in bt.items():
 if key not in ft:
  pt.s1=pt.s1.replace(u['xml'],'',1);changes.append({'kind':'toc_remove','title':title});continue
 target=ft[key][1]
 if p.nows(title)==p.nows(target):continue
 before,sep,after=u['xml'].partition('<hp:tab')
 matches=list(re.finditer(r'(<hp:t(?:\s[^>]*)?>)(.*?)(</hp:t>)',before,re.S))
 if not matches:raise ValueError('TOC title cannot target '+key)
 for j,m in reversed(list(enumerate(matches))):
  before=before[:m.start()]+m.group(1)+(p.esc(target) if j==0 else '')+m.group(3)+before[m.end():]
 pt.s1=pt.s1.replace(u['xml'],clean(before+sep+after),1)
 changes.append({'kind':'toc_title','old':title,'new':target})
report={'base':str(base.relative_to(ROOT)),'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'old_units':len(old),'new_units':len(new),'changes':changes,'retired_or_replaced':[o['text'] for i,o in enumerate(old) if i not in used and o['text']],'other_chapters_exact':True,'user_change_resolution':'4 groups reviewed by main; current MD authorized; deleted source credit/cost not restored; table3-12 note placed before table per latest instruction'}
(OUT/'targeted_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
pt.write(str(OUT/'patched.hwpx'))
print(json.dumps({'written':'patched.hwpx','changes':len(changes),'other_chapters_exact':True},ensure_ascii=False))
