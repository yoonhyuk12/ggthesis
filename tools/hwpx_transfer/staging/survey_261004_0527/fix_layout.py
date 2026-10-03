"""Apply only layout corrections established by review of the first reflow PDF."""
from pathlib import Path
import copy,json,re,sys,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent;sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}';H='{http://www.hancom.co.kr/hwpml/2011/head}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def ser(e):return re.sub(rb'\sxmlns(?::[\w-]+)?="[^"]*"',b'',E.tostring(e,encoding='utf-8',with_tail=False))
src=Q/'reflowed.hwpx';original=src.read_bytes()
with zipfile.ZipFile(src) as z:raw=z.read('Contents/section2.xml');hraw=z.read('Contents/header.xml')
root=E.fromstring(raw);header=E.fromstring(hraw);ps=list(root.iter(P+'p'));ts=list(root.iter(P+'tbl'));pns=[n for n in elements(raw) if n['name']=='hp:p'];touched=set();evidence=[]
pps={p.get('id'):p for p in header.iter(H+'paraPr')};style_cache={}
def top(p):
 while p.getparent() is not root:p=p.getparent()
 return p
def clear(p):
 for a in list(p.iter(P+'linesegarray')):a.getparent().remove(a)
def touch(p):touched.add(top(p));clear(top(p))
def spacing(p,value):
 old=p.get('paraPrIDRef');key=(old,value)
 if key not in style_cache:
  cp=copy.deepcopy(pps[old]);cid=str(max(map(int,pps))+1);cp.set('id',cid)
  for e in cp.iter():
   if e.tag.endswith('}lineSpacing'):e.set('value',str(value))
  parent=pps[old].getparent();parent.append(cp);parent.set('itemCnt',str(len(parent)));pps[cid]=cp;style_cache[key]=cid
 p.set('paraPrIDRef',style_cache[key]);touch(p)
def compact_table(ti,line=None):
 t=ts[ti];t.set('pageBreak','NONE');t.find(P+'pos').set('treatAsChar','1')
 if line:
  for p in t.iter(P+'p'):
   if own(p).strip():spacing(p,line)
  for c in t.iter(P+'tc'):c.find(P+'cellSz').set('height','1600')
  t.find(P+'sz').set('height',str(int(t.get('rowCnt'))*1600))
 touch(t)
# Put small result tables on one page instead of leaving isolated headers.
for ti in [26,27,32,33,34,35,37,38,39,41,43]:compact_table(ti)
evidence.append({'tables':[26,27,32,33,34,35,37,38,39,41,43],'change':'one-page table flow; widths and text preserved'})
# The two chapter-four notes must follow their tables in the reading flow.
for ti in [18,24]:compact_table(ti)
evidence.append({'tables':[18,24],'change':'inline whole tables keep following notes after the table'})
# Long table 2-6 remains row-splittable; start it with room for its first data row.
anchor=top(ts[6]);anchor.set('pageBreak','1');touch(anchor)
evidence.append({'table':6,'change':'start on a fresh page; retain existing row splitting'})
# The A blocks inherited 220/230 percent spacing from the paper response form.
# Keep the 11-point type and nested heading, use a readable 150 percent spacing,
# and let Hangeul determine actual height instead of keeping the old minimum.
for ti in [46,53]:
 t=ts[ti]
 for p in list(t.iter(P+'p')):
  if own(p).strip() and not own(p).startswith('A. '):spacing(p,150)
  elif not own(p).strip() and p.find('.//'+P+'tbl') is None:
   parent=p.getparent()
   if len(parent.findall(P+'p'))>1:parent.remove(p)
 for c in t.findall('./'+P+'tr/'+P+'tc'):c.find(P+'cellSz').set('height','1600')
 t.find(P+'sz').set('height','1600');touch(t)
evidence.append({'tables':[46,53],'change':'150% paragraph spacing, unchanged fonts/text/nested grids; remove empty spacer paragraph and reset obsolete minimum height'})
# Both cover disclosures have grown; preserve their wording and 11-point text.
for ti in [45,52]:
 t=ts[ti]
 for p in list(t.iter(P+'p')):
  text=own(p)
  if len(text)>25 and not any(s in text for s in ['중소규모 건설현장을 위한','안전관제 시스템 개발 및 실증 연구',': 도입 현장과']):spacing(p,140)
  if text.startswith('응답에는 정답이 없으며'):
   styles=[]
   for r in p.findall(P+'run'):styles.extend([r.get('charPrIDRef')]*sum(len(''.join(t.itertext())) for t in r.findall(P+'t')))
   bold=next(r.get('charPrIDRef') for r in p.findall(P+'run') if '학술 연구를 위한 통계 분석에만' in ''.join(''.join(t.itertext()) for t in r.findall(P+'t')))
   for phrase in ['자발적','학술 연구를 위한 통계 분석에만']:
    start=text.index(phrase);styles[start:start+len(phrase)]=[bold]*len(phrase)
   for r in list(p.findall(P+'run')):p.remove(r)
   start=0
   while start<len(text):
    end=start+1
    while end<len(text) and styles[end]==styles[start]:end+=1
    r=E.SubElement(p,P+'run',charPrIDRef=styles[start]);E.SubElement(r,P+'t').text=text[start:end];start=end
   touch(p)
 # A surplus empty paragraph before the date is spacing, not authored text.
 for c in t.findall('./'+P+'tr/'+P+'tc'):
  sub=c.find(P+'subList')
  if any(own(p).startswith('응답에는 정답이 없으며') for p in sub.findall(P+'p')):
   for p in list(sub.findall(P+'p')):
    if not own(p).strip() and p.find('.//'+P+'tbl') is None:sub.remove(p)
  c.find(P+'cellSz').set('height','1600')
 t.find(P+'sz').set('height','3200');touch(t)
evidence.append({'tables':[45,52],'change':'140% disclosure spacing; restore MD voluntary-participation bold; preserve full cover wording and contacts'})
# D/E have an added NA column. Remove obsolete fixed row minima, without
# shrinking characters or omitting the experience guide or scale labels.
for ti in [50,51]:compact_table(ti,140)
evidence.append({'tables':[50,51],'change':'140% spacing and content-driven heights; preserve fourteen-column merged grids and all NA labels'})
edits=[]
for p in touched:
 i=ps.index(p);node=pns[i];edits.append((node['start'],node['end'],ser(p)))
for a,b,val in sorted(edits,reverse=True):raw=raw[:a]+val+raw[b:]
E.fromstring(raw)
newheader=E.tostring(header,encoding='utf-8',xml_declaration=True,standalone=True)
out=Q/'layout_fixed.hwpx';assert not out.exists();out.write_bytes(raw_zip_patch(original,{'Contents/section2.xml':raw,'Contents/header.xml':newheader}))
assert ''.join(own(p) for p in E.fromstring(raw).iter(P+'p'))==''.join(own(p) for p in root.iter(P+'p'))
(Q/'layout_changes.json').write_text(json.dumps({'changes':evidence,'touched_root_paragraphs':len(touched),'added_paragraph_styles':len(style_cache)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'touched_root_paragraphs':len(touched),'added_paragraph_styles':len(style_cache)},ensure_ascii=False))
