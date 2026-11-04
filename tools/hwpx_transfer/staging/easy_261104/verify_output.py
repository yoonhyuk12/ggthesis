"""Read-only content, table and PDF checks for this transfer."""
from pathlib import Path
import sys,re,json,zipfile,hashlib,xml.etree.ElementTree as E
from collections import Counter
import fitz
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
norm=lambda s:re.sub(r'\s+','',s)
def load(p):
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  return {n:z.read(n) for n in z.namelist()}
def sections(d):
 return {n:E.fromstring(v) for n,v in d.items() if re.fullmatch(r'Contents/section\d+\.xml',n)}
def own(p):
 return ''.join(''.join(t.itertext()) for run in p.findall(HP+'run') for t in run.findall(HP+'t'))
def paras(d):return {(n,i):own(p) for n,r in sections(d).items() for i,p in enumerate(r.iter(HP+'p'))}
def tables(d):
 result=[]
 for n,r in sections(d).items():
  for t in r.iter(HP+'tbl'):
   size=t.find(HP+'sz')
   cells=[]
   for row in t.findall(HP+'tr'):
    for c in row.findall(HP+'tc'):
     cells.append({'addr':c.find(HP+'cellAddr').attrib,'span':c.find(HP+'cellSpan').attrib,
                   'width':c.find(HP+'cellSz').get('width')})
   result.append({'section':n,'rows':t.get('rowCnt'),'cols':t.get('colCnt'),
                  'width':size.get('width') if size is not None else None,'cells':cells})
 return result
src=OUT/sys.argv[1];pdfpath=OUT/sys.argv[2]
expected=OUT/(sys.argv[3] if len(sys.argv)>3 else 'patched.hwpx')
info=json.loads((OUT/'base_info.json').read_text(encoding='utf8'))
assert hashlib.sha256((ROOT/info['path']).read_bytes()).hexdigest()==info['sha256']
b=load(OUT/'base.hwpx');d=load(src);ex=load(expected)
report={'file':str(src.relative_to(ROOT)),'original_sha_unchanged':True,
        'table_grid_widths_preserved':tables(b)==tables(d),'tables':len(tables(d))}
assert report['table_grid_widths_preserved']
# Hancom may add empty cell paragraphs; compare the ordered nonempty text sequence.
for n,r in sections(d).items():
 a=[norm(own(p)) for p in r.iter(HP+'p') if norm(own(p))]
 er=sections(ex)[n];ee=[norm(own(p)) for p in er.iter(HP+'p') if norm(own(p))]
 assert a==ee,('text_changed_during_resave',n)
report['text_preserved_during_resave']=True
report['bindata_preserved']=all(d.get(n)==v for n,v in b.items() if n.startswith('BinData/'))
assert report['bindata_preserved']
head=E.fromstring(d['Contents/header.xml'])
red={e.get('id') for e in head.iter() if e.tag.endswith('}charPr') and e.get('textColor','').upper()=='#FF0000'}
bad=[];markers=0
for n,r in sections(d).items():
 for run in r.iter(HP+'run'):
  text=''.join(''.join(t.itertext()) for t in run.findall(HP+'t'))
  for m in ['[DATA PENDING','[확정 필요','[CITE_TODO','[그림 삽입 예정','[UNVERIFIED','실험전']:
   if m in text:
    markers+=text.count(m)
    if run.get('charPrIDRef') not in red:bad.append((n,text))
report.update(red_markers=markers,bad_red_markers=bad)
assert not bad,bad
pdf=fitz.open(pdfpath);texts=[norm(p.get_text()) for p in pdf]
tails=[];missing=[];tablepages=set()
for n,r in sections(d).items():
 for ti,t in enumerate(r.iter(HP+'tbl')):
  for ci,c in enumerate(t.findall('./'+HP+'tr/'+HP+'tc')):
   text=norm(''.join(own(p) for p in c.iter(HP+'p')))
   if not text:continue
   tail=text[-22:];hits=[i+1 for i,x in enumerate(texts) if tail in x]
   rec={'section':n,'table':ti,'cell':ci,'tail':tail,'pages':hits};tails.append(rec)
   if not hits:missing.append(rec)
   else:tablepages.update(hits)
report.update(pdf_pages=len(pdf),cell_tails=len(tails),missing_cell_tails=missing)
# Include every page with rules, not only matching cell tails, to see continuations.
for i,p in enumerate(pdf):
 if any(x['rect'].width>60 for x in p.get_drawings()):tablepages.add(i+1)
(OUT/'cell_tails.json').write_text(json.dumps(tails,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'output_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
pages=sorted(tablepages)
for batch in range(0,len(pages),9):
 sheet=Image.new('RGB',(1500,3*720),'white');draw=ImageDraw.Draw(sheet)
 for j,pn in enumerate(pages[batch:batch+9]):
  pix=pdf[pn-1].get_pixmap(matrix=fitz.Matrix(.85,.85),alpha=False)
  im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((490,690))
  x=j%3*500;y=j//3*720;sheet.paste(im,(x,y+25));draw.text((x+8,y+5),str(pn),fill='black')
 sheet.save(OUT/f'tables_contact_{batch//9+1:02}.png')
print(json.dumps(report,ensure_ascii=False));print('contact sheets',(len(pages)+8)//9)
