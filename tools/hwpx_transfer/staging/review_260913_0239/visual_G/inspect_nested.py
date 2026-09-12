import zipfile,xml.etree.ElementTree as E,json
from pathlib import Path
b=Path('tools/hwpx_transfer/staging/review_260913_0239'); ns={'h':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
out={}
for name in ['base.hwpx','final.hwpx']:
 data=[]
 with zipfile.ZipFile(b/name) as z:
  for sec in [s for s in z.namelist() if s.startswith('Contents/section')]:
   root=E.fromstring(z.read(sec)); parents={c:p for p in root.iter() for c in p}
   for idx,t in enumerate(root.findall('.//h:tbl',ns)):
    txt=''.join(t.itertext())
    if '전혀' not in txt or not ('B-1' in txt or 'C-1' in txt or 'D-1' in txt or 'E-1' in txt): continue
    rows=[]
    for ri,r in enumerate(t.findall('h:tr',ns)):
     cells=[]
     for c in r.findall('h:tc',ns):
      cells.append({'attrs':c.attrib,'addr':c.find('h:cellAddr',ns).attrib,'span':c.find('h:cellSpan',ns).attrib,'size':c.find('h:cellSz',ns).attrib,'text':''.join(c.itertext()),'nested':[E.tostring(x,encoding='unicode') for x in c.findall('.//h:tbl',ns)]})
     rows.append(cells)
    data.append({'section':sec,'index':idx,'attrs':t.attrib,'size':t.find('h:sz',ns).attrib,'rows':rows})
 out[name]=data
(b/'visual_G/nested_xml.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for name,ts in out.items():
 print(name)
 for t in ts:
  print(t['section'],t['index'],t['attrs'],t['size'])
  for r in t['rows'][:3]:
   print([{k:v for k,v in c.items() if k!='nested'}|{'nested_count':len(c['nested'])} for c in r])
