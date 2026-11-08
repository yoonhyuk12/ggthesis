from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,hashlib,shutil
s=Path('tools/hwpx_transfer/staging/factcheck_hwpx_261104c')
b=Path('00. hwpx/261104_1839_경기공학_건축안전_윤혁_논문.hwpx')
shutil.copy2(b,s/'base.hwpx')
(s/'base.sha256').write_text(hashlib.sha256(b.read_bytes()).hexdigest())
ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
rows=[]
with zipfile.ZipFile(b) as z:
 for n in z.namelist():
  if n.startswith('Contents/section'):
   r=E.fromstring(z.read(n))
   for i,p in enumerate(r.findall('.//hp:p',ns)):
    t=''.join(''.join(x.itertext()) for run in p.findall('hp:run',ns) for x in run.findall('hp:t',ns))
    rows.append({'section':n,'i':i,'text':t})
(s/'paras.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for x in rows:
 if any(k in x['text'] for k in ['류수영','조도빈','정·오탐 라벨링 기준','김현수(2026)가 보고한','반면 사건 검토','피드백을 얻었다']):print(x)
