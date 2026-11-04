from pathlib import Path
import json,re,zipfile,html,hashlib
import fitz
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
final=ROOT/'00. hwpx/261104_0817_경기공학_건축안전_윤혁_논문.hwpx'
prior=fitz.open(OUT/'final.pdf');pdf=fitz.open(OUT/'final_preserved.pdf')
assert len(prior)==len(pdf)
norm=lambda s:re.sub(r'\s+','',s)
changes=[]
for i in range(len(pdf)):
 a=norm(prior[i].get_text());b=norm(pdf[i].get_text())
 if a!=b:
  assert a.replace('자료:연구자작성.','',1)==b,(i+1,a[:100],b[:100])
  changes.append(i+1)
assert changes==[50],changes
m=json.loads((OUT/'toc_pages_completed.json').read_text(encoding='utf8'));want={t:v for d in m.values() for t,v in d.items()};used={};count=0
with zipfile.ZipFile(final) as z:
 assert z.testzip() is None;s=z.read('Contents/section1.xml').decode()
 for para in re.findall(r'<hp:p\b.*?</hp:p>',s,re.S):
  if '<hp:tab' not in para:continue
  before,after=para.split('<hp:tab',1);title=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip()
  actual=re.search(r'/>([^<]*)</hp:t>',after).group(1).strip();value=want[title];i=used.get(title,0);used[title]=i+1
  expected=value[min(i,len(value)-1)] if isinstance(value,list) else value
  assert actual==str(expected),(title,actual,expected)
  count+=1
source=json.loads((OUT/'targeted_report.json').read_text(encoding='utf8'));sha=hashlib.sha256((ROOT/source['base']).read_bytes()).hexdigest();assert sha==source['base_sha256']
pdf[49].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(OUT/'final_preserved_page50.png')
r={'final':str(final.relative_to(ROOT)),'pdf_pages':len(pdf),'changed_pdf_pages':[50],'only_removed_credit_text_difference':True,'toc_entries_verified':count,'base_sha256_unchanged':sha,'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
(OUT/'final_preserved_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
