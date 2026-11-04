from pathlib import Path
import sys,json,re,zipfile,hashlib,xml.etree.ElementTree as E
from collections import Counter
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
import kjn_profile as k
def raw(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  return {n:z.read(n) for n in z.namelist()}
info=json.loads((OUT/'base_info.json').read_text(encoding='utf8'));b=raw(ROOT/info['path']);n=raw(OUT/(sys.argv[1] if len(sys.argv)>1 else 'patched.hwpx'));f=raw(OUT/'assembled.hwpx')
def units(r):return p.Units(r['Contents/section2.xml'].decode(),set())
nu,fu=units(n),units(f)
def bounds(u,num):
 a=next(i for i,v in enumerate(u.items) if re.match(r'^제\s+'+str(num)+r'\s+장\s+',v['text']))
 e=next(i for i,v in enumerate(u.items[a+1:],a+1) if re.match(r'^제\s+\d+\s+장\s+',v['text']) or v['text']=='참고문헌')
 return a,e
chapters={}
for num in range(1,6):
 a,e=bounds(nu,num);fa,fe=bounds(fu,num)
 norm=lambda seq:[p.nows(v['text']) for v in seq if v['text'] and p.nows(v['text'])!='자료:연구자작성.']
 actual=norm(nu.items[a:e]);expected=norm(fu.items[fa:fe]);chapters[str(num)]=actual==expected
 assert actual==expected,('chapter mismatch',num)
assert not any(v['text'].startswith(('부록 2.','부록 3.')) for v in nu.items)
assert sum(v['text'].startswith('부 록 (') for v in nu.items)==2
assert sum(v['text']=='Abstract' for v in nu.items)==1
tables=[]
parsed={name:E.fromstring(v) for name,v in n.items() if name.endswith(('.xml','.hpf'))}
items={e.get('id'):e.get('href') for e in parsed['Contents/content.hpf'].iter() if e.tag.endswith('}item')}
refs=[e.get('binaryItemIDRef') for name,r in parsed.items() if '/section' in name for e in r.iter() if e.tag.endswith('}img')]
assert all(i in items and items[i] in n for i in refs)
red={e.get('id') for e in parsed['Contents/header.xml'].iter() if e.tag.endswith('}charPr') and e.get('textColor','').upper()=='#FF0000'}
bad=[];markers=0
for name,r in parsed.items():
 if '/section' not in name:continue
 for run in r.iter('{'+k.NS['hp']+'}run'):
  text=''.join(run.itertext())
  for marker in ['[DATA PENDING','[확정 필요','[CITE_TODO','[그림 삽입 예정','[UNVERIFIED','실험전']:
   if marker in text:
    markers+=text.count(marker)
    if run.get('charPrIDRef') not in red:bad.append(text[:100])
assert not bad,bad
report={'zip_xml':'PASS','chapter_text_matches_current_MD':chapters,'removed_appendices_absent':True,'surveys':2,'english_abstract':True,'original_table_grids_widths_preserved':tables,'image_references':len(refs),'all_image_references_resolved':True,'unused_images':sorted(set(v for v in items.values() if v.startswith('BinData/'))-set(items[i] for i in refs)),'red_markers':markers,'bad_red_markers':bad}
import fitz
pdf=fitz.open(OUT/(sys.argv[2] if len(sys.argv)>2 else 'resaved.pdf'))
norm=lambda s:re.sub(r'\s+','',s)
texts=[norm(page.get_text()) for page in pdf];alltext=''.join(texts)
tails=[];missing=[]
for ui,u in enumerate(nu.items):
 if not u['tbl']:continue
 for ci,c in enumerate(re.findall(r'<hp:tc\b.*?</hp:tc>',u['xml'],re.S)):
  t=norm(k.plain_texts(c))
  if not t:continue
  tail=t[-22:];hits=[i+1 for i,t in enumerate(texts) if tail in t]
  tails.append({'unit':ui,'cell':ci,'tail':tail,'pages':hits})
  if not hits:missing.append(tails[-1])
report.update(pdf_pages=len(pdf),table_cell_tails=len(tails),missing_cell_tails=missing)
(OUT/'cell_tail_pdf.json').write_text(json.dumps(tails,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'readonly_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='missing_cell_tails'},ensure_ascii=False));print('Missing tails:',len(missing))
# PDF verification contact sheets, no source image edits.
from PIL import Image,ImageDraw
pages=sorted(set(pn for t in tails for pn in t['pages']))
for batch in range(0,len(pages),12):
 sheet=Image.new('RGB',(1200,4*440),'white');draw=ImageDraw.Draw(sheet)
 for j,pn in enumerate(pages[batch:batch+12]):
  pix=pdf[pn-1].get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False)
  im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((390,410))
  x=(j%3)*400;y=(j//3)*440;sheet.paste(im,(x,y+22));draw.text((x+5,y+3),str(pn),fill='black')
 sheet.save(OUT/f'tables_contact_{batch//12+1:02}.png')
