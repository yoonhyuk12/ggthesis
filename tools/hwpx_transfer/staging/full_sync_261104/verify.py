from pathlib import Path
import sys,json,re,zipfile,hashlib,collections,html
from lxml import etree as E
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p,kjn_profile as k
O=Path('tools/hwpx_transfer/staging/full_sync_261104');HP='{'+k.NS['hp']+'}'
def load(f):
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None
  return {n:z.read(n) for n in z.namelist()}
info=json.loads((O/'base_info.json').read_text(encoding='utf8'));base=load(info['path']);fresh=load(O/'fresh.hwpx');out=load(O/'final.hwpx');parsed={n:E.fromstring(v) for n,v in out.items() if n.endswith(('.xml','.hpf'))}
def units(raw,s=2):return p.Units(raw[f'Contents/section{s}.xml'].decode(),set())
nu=units(out);fu=units(fresh)
nonempty=lambda u:[p.nows(v['text']) for v in u.items if v['text']]
assert nonempty(nu)==nonempty(fu),'Full section2 text mismatch'
# TOC titles and abstract/thanks agree; ignore only pagination.
def front(u):return [p.nows(k.plain_texts(v['xml'].split('<hp:tab')[0])) if '<hp:tab' in v['xml'] else p.nows(v['text']) for v in u.items if v['text']]
assert front(units(out,1))==front(units(fresh,1))
assert not any(v['text'].startswith(('부록 2.','부록 3.')) for v in nu.items)
def geometry(raw):
 result=[]
 for s in range(3):
  root=E.fromstring(raw[f'Contents/section{s}.xml'])
  for tbl in root.iter(HP+'tbl'):
   rows=[]
   for tr in tbl.findall(HP+'tr'):
    for tc in tr.findall(HP+'tc'):
     rows.append([dict(tc.find(HP+'cellAddr').attrib),dict(tc.find(HP+'cellSpan').attrib),tc.find(HP+'cellSz').get('width')])
   result.append([tbl.get('rowCnt'),tbl.get('colCnt'),tbl.find(HP+'sz').get('width'),rows])
 return result
assert geometry(base)==geometry(out),'Table geometry mismatch'
assert {n:v for n,v in base.items() if n.startswith('BinData/')}=={n:v for n,v in out.items() if n.startswith('BinData/')}
assert all(b'pageBreak="CELL"' not in v for n,v in out.items() if 'section' in n)
markers=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def markercheck(raw):
 h=E.fromstring(raw['Contents/header.xml']);colors={v.get('id'):v.get('textColor') for v in h.iter() if v.tag.endswith('}charPr')};entries=[]
 for s in range(3):
  r=E.fromstring(raw[f'Contents/section{s}.xml'])
  for pi,para in enumerate(r.iter(HP+'p')):
   txt='';col=[]
   for run in para.findall(HP+'run'):
    t=''.join(''.join(t.itertext()) for t in run.findall(HP+'t'));txt+=t;col.extend([colors.get(run.get('charPrIDRef'))]*len(t))
   for m in markers.finditer(txt):entries.append({'section':s,'paragraph':pi,'text':m[0],'red':all(c=='#FF0000' for c in col[m.start():m.end()])})
 return entries
actual=markercheck(out);expected=markercheck(fresh)
assert all(v['red'] for v in actual)
assert collections.Counter(v['text'] for v in actual)==collections.Counter(v['text'] for v in expected)
# Compare actual manuscript heading/caption order to current block assembly.
structure=lambda u:[v['text'] for v in u.items if re.match(r'^제\s*\d+\s*(장|절|항)|^<(표|그림)\s*\d+-\d+>',v['text']) and not v['tbl']]
assert structure(nu)==structure(fu)
assert hashlib.sha256(Path(info['path']).read_bytes()).hexdigest()==info['sha256']
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in info['md_sha256'].items())
report={'zip_xml':'PASS','full_section2_text_order_matches_MD_assembly':True,'front_abstract_thanks_and_toc_titles_match':True,'structure_items':len(structure(nu)),'table_geometry_preserved':len(geometry(out)),'BinData_preserved':True,'pageBreak_CELL':0,'markers_expected':expected,'markers_actual':actual,'base_unchanged':True,'MD_unchanged':True,'manual_reapply':[]}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
