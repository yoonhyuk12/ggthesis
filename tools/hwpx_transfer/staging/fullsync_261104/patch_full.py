"""Main-only full MD synchronization using preserved chapter/survey XML."""
from pathlib import Path
import sys,json,re,difflib,html,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'));sys.path.insert(0,str(OUT))
import patch_from_fresh as p,kjn_profile as k
from survey_patch import patch_surveys
info=json.loads((OUT/'base_info.json').read_text(encoding='utf8'))
base=ROOT/info['path'];assert hashlib.sha256(base.read_bytes()).hexdigest()==info['sha256']
pt=p.Patcher(str(base),str(OUT/'assembled.hwpx'),[],None)
bu=p.Units(pt.s2,set());fu=p.Units(pt.fresh_s2,set());changes=[]
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

def chapter_bounds(u,number):
 a=next(i for i,v in enumerate(u.items) if re.match(r'^제\s+'+str(number)+r'\s+장\s+',v['text']))
 e=next((i for i,v in enumerate(u.items[a+1:],a+1) if re.match(r'^제\s+\d+\s+장\s+',v['text']) or v['text']=='참고문헌'),len(u.items))
 return a,e
replacements=[]
for number in [1,2,5]:
 a,e=chapter_bounds(bu,number);fa,fe=chapter_bounds(fu,number);old=bu.items[a:e];new=fu.items[fa:fe];used=set();rendered=[]
 for v in new:
  candidates=[(i,o) for i,o in enumerate(old) if i not in used and o['tbl']==v['tbl'] and p.nows(o['text'])==p.nows(v['text']) and ('<hp:pic' in o['xml'])==('<hp:pic' in v['xml'])]
  if candidates and '<hp:pic' not in v['xml']:
   i,o=candidates[0];used.add(i);rendered.append(clean(o['xml']));continue
  if v['tbl']:
   compatible=[]
   for i,o in enumerate(old):
    if i in used or not o['tbl']:continue
    try:pairs=mapped_cells(o['xml'],v['xml'])
    except ValueError:continue
    score=difflib.SequenceMatcher(None,p.nows(o['text']),p.nows(v['text']),autojunk=False).ratio()
    if score>.45:compatible.append((score,i,o,pairs))
   if compatible:
    score,i,o,pairs=max(compatible,key=lambda x:x[0]);used.add(i);xml=o['xml']
    for before,after in pairs:xml=xml.replace(before,patchcell(before,after),1)
    rendered.append(clean(xml));changes.append({'kind':'table_preserved_grid','new':v['cap'],'old':o['cap'],'score':score});continue
   changes.append({'kind':'new_table','caption':v['cap']})
  rendered.append(pt.take_fresh(v['xml']))
 # Preserve original section controls on first chapter heading.
 if number==1:rendered[0]=old[0]['xml']
 replacements.append((bu.spans[a][0],bu.spans[e][0],''.join(rendered)))
# References: replace old reference region, survey section remains untouched here.
ba=next(i for i,v in enumerate(bu.items) if v['text']=='참고문헌');be=next(i for i,v in enumerate(bu.items[ba+1:],ba+1) if v['text'].startswith('부 록 (도입'))
fa=next(i for i,v in enumerate(fu.items) if v['text']=='참고문헌');fe=next(i for i,v in enumerate(fu.items) if v['text']=='Abstract')
replacements.append((bu.spans[ba][0],bu.spans[be][0],''.join(pt.take_fresh(v['xml']) for v in fu.items[fa:fe])))
# User explicitly removed detailed-results and raw-output appendices; add MD English abstract.
ba=next(i for i,v in enumerate(bu.items) if v['text'].startswith('부록 2.'))
end=bu.spans[-1][1]
replacements.append((bu.spans[ba][0],end,''.join(pt.take_fresh(v['xml']) for v in fu.items[fe:])))
for start,end,xml in sorted(replacements,reverse=True):pt.s2=pt.s2[:start]+xml+pt.s2[end:]
pt.s2,survey_report=patch_surveys(pt.s2)
# Remove the one obsolete reference-variable row from table4-3 without rebuilding the table.
u=p.Units(pt.s2,set());v=next(v for v in u.items if v['tbl'] and v['cap']=='<표4-3>')
rows=list(re.finditer(r'<hp:tr\b.*?</hp:tr>',v['xml'],re.S));hits=[m for m in rows if '참고변수' in p.nows(k.plain_texts(m.group()))]
assert len(hits)==1
row=hits[0];ridx=int(re.search(r'rowAddr="(\d+)"',row.group()).group(1));height=max(int(x) for x in re.findall(r'<hp:cellSz[^>]*height="(\d+)"',row.group()))
xml=v['xml'][:row.start()]+v['xml'][row.end():]
xml=re.sub(r'rowCnt="(\d+)"',lambda m:'rowCnt="'+str(int(m[1])-1)+'"',xml,count=1)
xml=re.sub(r'rowAddr="(\d+)"',lambda m:'rowAddr="'+str(int(m[1])-(int(m[1])>ridx))+'"',xml)
xml=re.sub(r'(<hp:sz[^>]*height=")(\d+)(")',lambda m:m[1]+str(max(1,int(m[2])-height))+m[3],xml,count=1)
pt.s2=pt.s2.replace(v['xml'],clean(xml),1)
# Rebuild only tabbed contents entries using original formatting, then current thanks/abstract bodies.
def title(v):return html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',v['xml'].split('<hp:tab',1)[0]))).strip()
u=p.Units(pt.s2,set());b1=p.Units(pt.s1,set());f1=p.Units(pt.fresh_s1,set())
alltabs=[v for v in b1.items if '<hp:tab' in v['xml']]
regular=[v for v in alltabs if not title(v).startswith('<')]
lot=[v for v in alltabs if title(v).startswith(('<표','<부표'))];lof=[v for v in alltabs if title(v).startswith('<그림')]
keepfront=[title(v) for v in regular if title(v) in ['표 목 차','표목차','그림목차','그림 목 차','감사의 글','논문개요']]
heads=[]
for v in u.items:
 t=v['text']
 if re.match(r'^제\s+\d+\s+(장|절|항)\s+',t) or t in ['참고문헌','Abstract'] or t.startswith(('부 록 (','Part ')):heads.append(t)
for olds,targets in [(regular,keepfront+heads),(lot,[v['text'] for v in u.items if re.match(r'^<표\s*\d+-\d+>',v['text']) and not v['tbl']]),(lof,[v['text'] for v in u.items if re.match(r'^<그림\s*\d+-\d+>',v['text']) and not v['tbl']])]:
 templates={p.nows(title(v)):v for v in olds};rendered=[]
 for i,t in enumerate(targets):
  v=templates.get(p.nows(t),olds[min(i,len(olds)-1)]);xml=p.replace_literal_text(v['xml'],title(v),t,1);rendered.append(pt.renumber(clean(xml)))
 pt.s1=pt.s1.replace(olds[0]['xml'],''.join(rendered),1)
 for v in olds[1:]:pt.s1=pt.s1.replace(v['xml'],'',1)
# Keep original heading boxes but substitute their complete MD prose.
b1=p.Units(pt.s1,set())
def locate(units,name):return next(i for i,v in enumerate(units.items) if p.nows(v['text'])==name and '<hp:tab' not in v['xml'])
ba=locate(b1,'감사의글');be=locate(b1,'논문개요');fa=locate(f1,'감사의글');fe=locate(f1,'논문개요')
for start,end,xml in sorted([(b1.spans[ba+1][0],b1.spans[be][0],''.join(pt.take_fresh(v['xml']) for v in f1.items[fa+1:fe] if p.nows(v['text'])!='감사의글')),(b1.spans[be+1][0],b1.spans[-1][1],''.join(pt.take_fresh(v['xml']) for v in f1.items[fe+1:]))],reverse=True):pt.s1=pt.s1[:start]+xml+pt.s1[end:]
report={'changes':changes,'survey':survey_report,'reference_count':sum(len(v) for v in json.loads((OUT/'references.json').read_text(encoding='utf8'))['categories'].values()),'removed_appendices':[2,3],'removed_table4_3_row':ridx,'base_sha256':info['sha256']}
(OUT/'patch_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if '--dry-run' not in sys.argv:pt.write(str(OUT/'patched.hwpx'))
print(json.dumps(report,ensure_ascii=False))
