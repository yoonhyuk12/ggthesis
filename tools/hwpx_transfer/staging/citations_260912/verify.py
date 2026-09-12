from pathlib import Path
import json,re,sys,zipfile,hashlib,collections
from lxml import etree as E
import fitz
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'figures_260912'));from verify_content import tables
sys.path.insert(0,str(HERE));from update_toc import mapping
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}';H='{http://www.hancom.co.kr/hwpml/2011/head}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def norm(s):return re.sub(r'\s+','',s).replace('·','ㆍ')
def read(f):
 with zipfile.ZipFile(HERE/(f+'.hwpx')) as z:return {n:z.read(n) for n in z.namelist()}
b,c,f=map(read,('base','candidate','final'))
report={};man=json.loads((HERE/'patch_manifest.json').read_text(encoding='utf8'))
cs,fs=E.fromstring(c['Contents/section2.xml']),E.fromstring(f['Contents/section2.xml'])
cp=[own(p) for p in cs.iter(P+'p') if own(p)];fp=[own(p) for p in fs.iter(P+'p') if own(p)]
report['reflow_text_preserved']=cp==fp
bt,ct,ft=map(tables,(E.fromstring(b['Contents/section2.xml']),cs,fs))
report['tables']=len(ft);report['reflow_tables_text_width_grid_preserved']=ct==ft
def geometry(t):return {**t,'cells':[{k:v for k,v in cell.items() if k!='paragraphs'} for cell in t['cells']]}
report['base_table_geometry_preserved']=[geometry(t) for t in bt]==[geometry(t) for t in ft]
report['pictures']=len(list(fs.iter(P+'pic')))
report['binary_images_unchanged']=all(v==f[n] for n,v in b.items() if n.startswith('BinData/'))
report['unrelated_zip_parts_candidate_unchanged']=all(v==c[n] for n,v in b.items() if n not in man['changed_parts'])
report['forbidden_cell_breaks']=len(fs.xpath('//*[local-name()="tbl" and @pageBreak="CELL"]'))
head=E.fromstring(f['Contents/header.xml']);colors={n.get('id'):n.get('textColor') for n in head.iter(H+'charPr')}
bad=[];markcount=0
for p in fs.iter(P+'p'):
 text=own(p);styles=[]
 for r in p.findall(P+'run'):styles.extend([colors[r.get('charPrIDRef')]]*len(''.join(''.join(t.itertext()) for t in r.findall(P+'t'))))
 for m in re.finditer(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|UNVERIFIED|그림 삽입 예정)[^\]]*\]',text):
  markcount+=1
  if set(styles[m.start():m.end()])!={'#FF0000'}:bad.append(m[0])
report['marker_count']=markcount;report['marker_color_errors']=bad
source=json.loads((HERE/'source.json').read_text(encoding='utf8'))
report['original_hash_unchanged']=hashlib.sha256((ROOT/source['source']).read_bytes()).hexdigest()==source['sha256']
doc=fitz.open(HERE/'final.pdf');report['pdf_pages']=len(doc)
pages=[norm(p.get_text()) for p in doc];alltext=''.join(pages)
tablepages=set();missing=[];tablechecks=[]
for i,t in enumerate(ft):
 texts=[x for cell in t['cells'] for x in cell['paragraphs'] if x]
 foundpages=set();absent=[]
 for text in texts:
  n=norm(text);hits=[j+1 for j,p in enumerate(pages[11:],start=11) if n in p]
  if hits and len(n)>12:foundpages.update(hits)
  if n not in alltext:absent.append(text)
 # Use long, distinct paragraphs to locate table pages, including its final row.
 tablepages.update(foundpages);tablechecks.append({'table':i,'pages':sorted(foundpages),'missing_paragraphs':absent,'last_cell':t['cells'][-1]['paragraphs']})
 if absent:missing.append({'table':i,'texts':absent})
report['pdf_missing_table_paragraphs']=missing
toc=mapping(HERE/'final.pdf');report['toc_mapped']=len(toc['entries']);report['toc_unresolved']=toc['unresolved']
ps=list(E.fromstring(f['Contents/section1.xml']).iter(P+'p'));tocps=[p for p in ps if p.find('.//'+P+'tab') is not None]
errors=[]
for p,e in zip(tocps,toc['entries']):
 text=own(p);page=int(re.search(r'(\d+)$',text)[1])
 if page!=e['printed']:errors.append([text,e['printed']])
report['toc_page_errors']=errors
(HERE/'table_checks.json').write_text(json.dumps(tablechecks,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
# Contact sheets include every table page and the full bibliography.
tablepages.update(range(106,113));selected=sorted(tablepages)
for offset in range(0,len(selected),6):
 batch=selected[offset:offset+6];canvas=Image.new('RGB',(1500,2180),'#aaaaaa');draw=ImageDraw.Draw(canvas)
 for k,number in enumerate(batch):
  page=doc[number-1];pix=page.get_pixmap(matrix=fitz.Matrix(1.25,1.25));im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((748,695))
  x=(k%2)*750;y=(k//2)*726;canvas.paste(im,(x+(750-im.width)//2,y+24));draw.text((x+10,y+5),f'PDF page {number}',fill='black')
 canvas.save(HERE/f'contact_{offset//6+1:02}.png')
print('CONTACT_PAGES',selected)
