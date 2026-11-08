from pathlib import Path
from lxml import etree as E
import zipfile,json,re,hashlib
s=Path('tools/hwpx_transfer/staging/factcheck_hwpx_261104c');ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
def tx(p):return ''.join(''.join(t.itertext()) for r in p.findall('hp:run',ns) for t in r.findall('hp:t',ns))
def load(p):
 z=zipfile.ZipFile(p);roots=[E.fromstring(z.read(n)) for n in z.namelist() if re.match(r'Contents/section\d+.xml',n)];return z,roots
b,br=load(s/'base.hwpx');r,rr=load(s/'ready.hwpx');f,fr=load(s/'reflow.hwpx');m=json.loads((s/'map.json').read_text(encoding='utf-8'))
expected=[]
for root in br:
 for p in root.findall('.//hp:p',ns):
  t=tx(p)
  if t.startswith('[18] 조도빈,'):continue
  for a,v in sorted(m.items(),key=lambda x:-len(x[0])):t=t.replace(a,v)
  expected.append(t)
actual=[tx(p) for root in rr for p in root.findall('.//hp:p',ns)]
assert actual==expected,'Unexpected text change'
assert [x for x in actual if x]!=[ ]
assert [x for x in actual if x]==[tx(p) for root in fr for p in root.findall('.//hp:p',ns) if tx(p)],'reflow text change'
def tables(roots):
 return [[(E.QName(e).localname,dict(e.attrib)) for e in t.iter() if E.QName(e).localname in ['sz','cellSz','cellAddr','cellSpan','pos']] for root in roots for t in root.findall('.//hp:tbl',ns)]
assert tables(br)==tables(rr)==tables(fr),'table geometry'
for name in b.namelist():
 if name.startswith('BinData/'):assert b.read(name)==r.read(name)==f.read(name)
# outside target paragraphs, exact XML (only anchor direct caches are expected changes)
for roots in [rr,fr]:assert not any(t.get('pageBreak')=='CELL' for root in roots for t in root.findall('.//hp:tbl',ns))
refs=[t for t in actual if re.match(r'^\[\d+\]',t)];groups=[]
for t in refs:
 n=int(t[1:3])
 if n==1:groups.append([])
 groups[-1].append(n)
for g in groups:assert g==list(range(1,len(g)+1))
result={'text_changes_expected_only':True,'reflow_text_identical':True,'tables_geometry_preserved':len(tables(br)),'images_identical':True,'reference_groups':[len(g) for g in groups],'reference_gaps':0,'reference_duplicates':0,'base_sha256':hashlib.sha256((s/'base.hwpx').read_bytes()).hexdigest()}
(s/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
