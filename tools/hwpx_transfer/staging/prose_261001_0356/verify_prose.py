"""Read-only verification of coordinator-generated candidate; no COM or PDF."""
import sys
sys.dont_write_bytecode=True
import json,zipfile,re,io
import xml.etree.ElementTree as ET
from apply_prose import HERE,P,load,prepare,check_sources,owned,MARKER
from raw_support import require,sha,raw_zip_patch
def verify(candidate):
 s=load();check_sources(s);changed,failures,evidence=prepare(s);require(not failures,str(failures))
 expected=raw_zip_patch((HERE/'base.hwpx').read_bytes(),changed)
 require(candidate==expected,'candidate differs from exact approved byte-fragment patch / ZIP metadata preservation')
 actual_changes=[]
 with zipfile.ZipFile(HERE/'base.hwpx') as a,zipfile.ZipFile(io.BytesIO(candidate)) as b:
  require(a.namelist()==b.namelist(),'ZIP order differs');require(b.testzip() is None,'CRC failure')
  bykey={(r['section'],r['idx']):r for r in s['replacements']}
  require(len(bykey)==len(s['replacements']),'duplicate paragraph targets')
  for name in a.namelist():
   old,new=a.read(name),b.read(name)
   if name not in changed: require(old==new,'unrelated entry changed');continue
   x,y=ET.fromstring(old),ET.fromstring(new)
   for tag in ('p','run','t'):
    require(len(list(x.iter(P+tag)))==len(list(y.iter(P+tag))),tag+' count changed')
   require([r.attrib for r in x.iter(P+'run')]==[r.attrib for r in y.iter(P+'run')],'run style attributes changed')
   for idx,(op,np) in enumerate(zip(x.iter(P+'p'),y.iter(P+'p'))):
    ot,nt=owned(op),owned(np);r=bykey.get((name,idx))
    if r:
     require(nt==r['new_hwpx'],'specified new text absent');require(np.find(P+'linesegarray') is None,'changed paragraph cache retained')
     actual_changes.append((name,idx))
    else:require(ot==nt,'unrequested paragraph changed')
    require(MARKER.findall(ot)==MARKER.findall(nt),'marker text changed')
    def marker_styles(p):
     text='';styles=[]
     for run in p.findall(P+'run'):
      t=''.join(''.join(e.itertext()) for e in run.findall(P+'t'));text+=t;styles.extend([run.get('charPrIDRef')]*len(t))
     return [(m.group(),styles[m.start():m.end()]) for m in MARKER.finditer(text)]
    require(marker_styles(op)==marker_styles(np),'marker char styles changed')
 require(len(actual_changes)==len(s['replacements']),'changed count differs')
 check_sources(s)
 return dict(ok=True,changed_paragraphs=len(actual_changes),md_dispositions=s['counts'],base_sha256=s['base_sha256'],candidate_sha256=sha(candidate),checks=['exact surgical bytes and raw ZIP records','all specified paragraph text','p/run/t counts','charPr refs','marker text and per-character style','unaffected text and controls','changed paragraph cache removal','source and all MD SHA256'])
if __name__=='__main__':
 result=verify((HERE/'candidate.hwpx').read_bytes());print(json.dumps(result,ensure_ascii=False,indent=2))
