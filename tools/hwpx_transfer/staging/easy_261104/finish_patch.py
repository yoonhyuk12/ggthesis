"""Main-only: apply approved bibliography delta and clear affected table caches."""
from pathlib import Path
import sys,json,re,zipfile,html,xml.etree.ElementTree as E
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import verify_replace as vr
import patch_from_fresh as pf
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
delta=json.loads((OUT/'refs_delta.json').read_text(encoding='utf8'))
assert not delta['unresolved']
with zipfile.ZipFile(OUT/'text_patched.hwpx') as z:entries=[(i,z.read(i.filename)) for i in z.infolist()]
data=dict((i.filename,v) for i,v in entries)
s=data['Contents/section2.xml'].decode();spans=vr.paragraph_spans(s)
ps=list(E.fromstring(s).iter(HP+'p'))
def own(p):return ''.join(''.join(t.itertext()) for run in p.findall(HP+'run') for t in run.findall(HP+'t'))
def frag(idx):
 a,b,c,d=spans[idx];return s[a:d]
def replace(xml,value):
 matches=list(re.finditer(r'(<hp:t>)(.*?)(</hp:t>)',xml,re.S));assert matches
 for j,m in reversed(list(enumerate(matches))):xml=xml[:m.start(2)]+(html.escape(value,quote=False) if j==0 else '')+xml[m.end(2):]
 return re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',xml,flags=re.S)
repl={}
for x in delta['replace']:
 assert own(ps[x['idx']])==x['old'];repl[x['idx']]=replace(frag(x['idx']),x['new'])
for x in delta['delete']:
 assert own(ps[x['idx']])==x['old'];repl[x['idx']]=''
nextid=max(int(p.get('id','0')) for p in ps)+1
for x in sorted(delta['insert_after'],key=lambda x:(x['idx'],x['order'])):
 template=frag(x['template_idx']);assert '<hp:tbl' not in template and '<hp:pic' not in template
 addition=replace(template,x['text'])
 addition=re.sub(r'(<hp:p\b[^>]*\bid=")\d+(")',lambda m:m[1]+str(nextid)+m[2],addition,count=1);nextid+=1
 assert 'pageBreak="1"' not in addition
 repl[x['idx']]=repl.get(x['idx'],frag(x['idx']))+addition
for idx,value in sorted(repl.items(),reverse=True):
 a,b,c,d=spans[idx];s=s[:a]+value+s[d:]
# Same table layout, but the anchor and all affected cell layouts need reflow.
with zipfile.ZipFile(OUT/'base.hwpx') as z:base=z.read('Contents/section2.xml').decode()
bu=pf.Units(base,set());nu=pf.Units(s,set())
bt=[v for v in bu.items if v['tbl']];nt=[v for v in nu.items if v['tbl']];assert len(bt)==len(nt)
cleared=[]
for i,(a,b) in enumerate(zip(bt,nt)):
 if a['text']!=b['text']:
  new=re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',b['xml'],flags=re.S)
  assert s.count(b['xml'])==1;s=s.replace(b['xml'],new,1);cleared.append(i)
E.fromstring(s)
data['Contents/section2.xml']=s.encode()
with zipfile.ZipFile(OUT/'patched.hwpx','w') as z:
 for i,v in entries:z.writestr(i,data[i.filename],compress_type=i.compress_type)
report={'reference_replace':len(delta['replace']),'reference_delete':len(delta['delete']),'reference_insert':len(delta['insert_after']),'affected_tables_caches_cleared':cleared,'paragraph_delta':1,'intentional_deleted_UNVERIFIED_total':2}
(OUT/'finish_patch_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(report)
