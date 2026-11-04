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
 a=next(i for i,u in enumerate(units.items) if re.match(r'^제\s*4\s*장\s',u['text']))
 b=next((i for i,u in enumerate(units.items[a+1:],a+1) if re.match(r'^제\s*5\s*장\s',u['text']) or u['text'].replace(' ','').startswith('참고문헌')),len(units.items))
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
TABLE_MAP={1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:None,12:13,13:14,14:15,15:17}
for ni,n in enumerate(new):
 candidates=[(i,o) for i,o in enumerate(old) if i not in used and o['tbl']==n['tbl'] and p.nows(o['text'])==p.nows(n['text']) and ('<hp:pic' in o['xml'])==('<hp:pic' in n['xml'])]
 if candidates and '<hp:pic' not in n['xml']:
  i,o=candidates[0];used.add(i);output.append(clean(o['xml']));continue
 if n['tbl']:
  number=int(re.search(r'4-(\d+)',n['cap']).group(1));target=TABLE_MAP[number]
  candidates=[(i,o) for i,o in enumerate(old) if i not in used and o['tbl'] and '<hp:pic' not in o['xml'] and o['cap']==f'<표4-{target}>'] if target else []
  compatible=False;reason='new correlation table'
  if candidates:
   assert len(candidates)==1
   i,o=candidates[0]
   try:pairs=mapped_cells(o['xml'],n['xml']);compatible=True
   except ValueError as ex:reason=str(ex)
  if compatible:
   used.add(i);xml=o['xml']
   for before,after in pairs:xml=xml.replace(before,patchcell(before,after),1)
   output.append(clean(xml));changes.append({'kind':'table_cells','caption':n['cap'],'old_caption':o['cap'],'grid_preserved':True})
  else:
   output.append(pt.take_fresh(n['xml']));changes.append({'kind':'new_or_restructured_table','caption':n['cap'],'old_caption':f'<표4-{target}>' if target else None,'reason':reason})
  continue
 output.append(pt.take_fresh(n['xml']));changes.append({'kind':'fresh_changed_or_new','text':n['text']})
start=bu.spans[ba][0];end=bu.spans[bb][0]
prefix,suffix=pt.s2[:start],pt.s2[end:]
pt.s2=prefix+''.join(output)+suffix
assert pt.s2.startswith(prefix) and pt.s2.endswith(suffix)
assert '<hp:tbl' not in ''.join(output) or 'pageBreak="CELL"' not in ''.join(output)
# Replace only chapter4 TOC group and its table/figure entries using existing format.
def title(u):return html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',u['xml'].split('<hp:tab',1)[0]))).strip()
def chapter_toc(items):
 inside=False;result=[]
 for u in items:
  t=title(u)
  if re.match(r'^제\s*4\s*장',t):inside=True
  elif re.match(r'^제\s*\d+\s*장',t):inside=False
  if inside and '<hp:tab' in u['xml']:result.append(u)
 return result
bu1=p.Units(pt.s1,set())
headings=[u['text'] for u in new if re.match(r'^제\s+\d+\s+(장|절|항)\s+',u['text'])]
groups=[(chapter_toc(bu1.items),headings)]
for kind in ['표','그림']:
 olds=[u for u in bu1.items if re.match(r'^<'+kind+r'\s*4-\d+>',title(u)) and '<hp:tab' in u['xml']]
 targets=[u['text'] for u in new if re.match(r'^<'+kind+r'\s*4-\d+>',u['text']) and not u['tbl']]
 groups.append((olds,targets))
for olds,targets in groups:
 assert olds
 rendered=[]
 for i,t in enumerate(targets):
  template=olds[min(i,len(olds)-1)];q=template['xml'];ot=title(template)
  q=p.replace_literal_text(q,ot,t,1);q=pt.renumber(clean(q))
  rendered.append(q)
 first=olds[0]['xml'];pt.s1=pt.s1.replace(first,''.join(rendered),1)
 for u in olds[1:]:pt.s1=pt.s1.replace(u['xml'],'',1)
 changes.append({'kind':'toc_group','old_count':len(olds),'new_count':len(targets)})
report={'base':str(base.relative_to(ROOT)),'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'old_units':len(old),'new_units':len(new),'changes':changes,'retired_or_replaced':[o['text'] for i,o in enumerate(old) if i not in used and o['text']],'other_chapters_exact':True,'user_change_resolution':'3 groups reviewed by main; current MD takes precedence; deleted notes are not restored as notes; moderator hypothesis not restored'}
(OUT/'targeted_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if '--dry-run' not in sys.argv:pt.write(str(OUT/'patched.hwpx'))
print(json.dumps({'written':'patched.hwpx','changes':len(changes),'other_chapters_exact':True},ensure_ascii=False))
