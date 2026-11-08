from pathlib import Path
from lxml import etree as E
import zipfile,json,re
s=Path('tools/hwpx_transfer/staging/factcheck_hwpx_261104c');ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
def text(p):return ''.join(''.join(t.itertext()) for r in p.findall('hp:run',ns) for t in r.findall('hp:t',ns))
with zipfile.ZipFile(s/'patched.hwpx') as z:
 data=z.read('Contents/section2.xml');root=E.fromstring(data);ps=root.findall('.//hp:p',ns)
 stack=[];spans=[]
 for m in re.finditer(rb'<hp:p\b[^>]*>|</hp:p>',data):
  if m.group().startswith(b'</'):
   j=stack.pop();spans[j][1]=m.end()
  else:
   stack.append(len(spans));spans.append([m.start(),None])
 assert len(spans)==len(ps)
 changes=json.loads((s/'changes.json').read_text(encoding='utf-8'));keys=[c['new'] for c in changes if c['status']=='applied'];anchor_indices=set();edits=[]
 for i,p in enumerate(ps):
  if text(p).startswith('[18] 조도빈,'):edits.append((*spans[i],b''));deleted=text(p)
  if any(k in text(p) for k in keys) and p.getparent().tag.endswith('}subList'):
   for a in p.iterancestors('{'+ns['hp']+'}p'):anchor_indices.add(ps.index(a))
 # anchor's direct lineseg is after the last nested paragraph
 for i in anchor_indices:
  a,b=spans[i];part=data[a:b];last=part.rfind(b'</hp:p>')
  caches=list(re.finditer(rb'<hp:linesegarray>.*?</hp:linesegarray>',part,re.S))
  if ps[i].find('hp:linesegarray',ns) is not None:
   c=caches[-1];edits.append((a+c.start(),a+c.end(),b''))
 for a,b,v in sorted(edits,reverse=True):data=data[:a]+v+data[b:]
 E.fromstring(data)
 with zipfile.ZipFile(s/'ready.hwpx','w') as out:
  for info in z.infolist():out.writestr(info,data if info.filename=='Contents/section2.xml' else z.read(info.filename))
 (s/'structural.json').write_text(json.dumps({'deleted':deleted,'anchor_indices':sorted(anchor_indices)},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Deleted bibliography paragraph, anchors',anchor_indices)
