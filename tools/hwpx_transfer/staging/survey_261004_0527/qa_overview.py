"""One-pass XML/PDF inventory for this output, with reviewable page images."""
from pathlib import Path
import collections,hashlib,json,re,sys,unicodedata,zipfile
from lxml import etree as E
import fitz
from PIL import Image,ImageDraw,ImageFont
Q=Path(__file__).resolve().parent;ROOT=Q.parents[3]
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}';H='{http://www.hancom.co.kr/hwpml/2011/head}'
MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-').replace('ㆍ','·')
def roots(file):
 with zipfile.ZipFile(file) as z:return {n:E.fromstring(z.read(n)) for n in z.namelist() if re.fullmatch(r'Contents/(?:section\d+|header)\.xml',n)}
def main(name):
 current=roots(Q/(name+'.hwpx'));candidate=roots(Q/'candidate.hwpx');report={};ps={sec:list(root.iter(P+'p')) for sec,root in current.items() if 'section' in sec}
 report['text_unchanged_on_reflow']={sec:norm(''.join(own(p) for p in paras))==norm(''.join(own(p) for p in candidate[sec].iter(P+'p'))) for sec,paras in ps.items()}
 colors={c.get('id'):c.get('textColor','').upper() for c in current['Contents/header.xml'].iter(H+'charPr')}
 markers=[];badcolors=[];tabledata=[];griderrors=[]
 for sec,paras in ps.items():
  for i,p in enumerate(paras):
   value=own(p);cs=[]
   for r in p.findall(P+'run'):cs.extend([colors[r.get('charPrIDRef')]]*sum(len(''.join(t.itertext())) for t in r.findall(P+'t')))
   for m in MARK.finditer(value):
    markers.append(m.group())
    if any(c!='#FF0000' for c in cs[m.start():m.end()]):badcolors.append(dict(section=sec,idx=i,marker=m.group()))
  for ti,t in enumerate(current[sec].iter(P+'tbl')):
   grid={};w=int(t.find(P+'sz').get('width'));rows=int(t.get('rowCnt'));cols=int(t.get('colCnt'))
   cells=[]
   for tr in t.findall(P+'tr'):
    for c in tr.findall(P+'tc'):
     a=c.find(P+'cellAddr');s=c.find(P+'cellSpan');sz=c.find(P+'cellSz');r,cc=int(a.get('rowAddr')),int(a.get('colAddr'));rs,cs=int(s.get('rowSpan')),int(s.get('colSpan'));cw=int(sz.get('width'))
     for y in range(r,r+rs):
      for x in range(cc,cc+cs):
       if (y,x) in grid:griderrors.append((sec,ti,'overlap',y,x))
       grid[y,x]=cw/cs
     cells.append({'row':r,'col':cc,'text':'\n'.join(own(p) for p in c.find(P+'subList').findall(P+'p')).strip()})
   if len(grid)!=rows*cols:griderrors.append((sec,ti,'coverage',len(grid),rows*cols))
   for y in range(rows):
    if abs(sum(grid.get((y,x),0) for x in range(cols))-w)>3:griderrors.append((sec,ti,'width',y))
   if t.get('pageBreak')=='CELL':griderrors.append((sec,ti,'CELL'))
   tabledata.append({'section':sec,'table':ti,'width':w,'rows':rows,'cols':cols,'cells':cells})
 doc=fitz.open(Q/(name+'.pdf'));texts=[];pageinfo=[];allspans=[]
 for i,page in enumerate(doc):
  text=page.get_text();texts.append(norm(re.sub(r'(?m)^\s*-\s*\d+\s*-\s*$','',text)))
  spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
  numbers=[int(m.group(1)) for s in spans if s['bbox'][1]>page.rect.height*.88 and (m:=re.fullmatch(r'-\s*(\d+)\s*-',s['text'].strip()))]
  body=[s for s in spans if not re.fullmatch(r'\s*-\s*\d+\s*-\s*',s['text']) and s['text'].strip()]
  pageinfo.append({'physical':i+1,'printed':numbers[0] if numbers else None,'body_bottom':round(max((s['bbox'][3] for s in body),default=0),2),'page_height':page.rect.height,'images':len(page.get_images()),'drawing_count':len(page.get_drawings())})
  allspans.extend({'page':i+1,**s} for s in spans)
 for t in tabledata:
  vals=[norm(c['text']) for c in t['cells'] if len(norm(c['text']))>=5]
  samples=sorted(set(vals),key=len,reverse=True)[:12]
  scores=[sum(min(len(s),70) for s in samples if s in text) for text in texts]
  strongest=max(scores,default=0);pages=[i+1 for i,s in enumerate(scores) if s>=max(12,strongest*.28)]
  if not pages and samples:
   scores=[sum(min(len(s),70) for s in samples if s in (texts[i]+texts[i+1] if i+1<len(texts) else texts[i])) for i in range(len(texts))]
   best=max(range(len(scores)),key=scores.__getitem__);pages=[best+1,best+2] if scores[best] else []
  t['likely_pages']=pages
  window=''.join(texts[max(0,min(pages)-2):min(len(texts),max(pages)+1)]) if pages else ''.join(texts)
  t['missing_long_cells']=[v for v in samples if v not in window]
 counts=collections.Counter(norm(m) for m in markers);full=''.join(texts)
 report.update(pages=len(doc),marker_count=len(markers),pending_count=markers.count('실험전'),marker_color_errors=badcolors,grid_errors=griderrors,missing_markers=[{'marker':s,'expected':n,'actual':full.count(s)} for s,n in counts.items() if full.count(s)<n],page_info=pageinfo,tables=tabledata)
 src=json.loads((Q/'source_manifest.json').read_text(encoding='utf-8'));report['original_unchanged']=hashlib.sha256((ROOT/src['source']).read_bytes()).hexdigest()==src['source_sha256']
 report['red_pdf_spans']=sum(s['color']==0xff0000 for s in allspans)
 (Q/(name+'_qa.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (Q/(name+'_pdf_text.txt')).write_text('\n\n'.join(f'PAGE {i+1}\n'+page.get_text() for i,page in enumerate(doc)),encoding='utf-8')
 visual=Q/(name+'_visual');visual.mkdir(exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
 for start in range(0,len(doc),6):
  sheet=Image.new('RGB',(1200,1740),'#dddddd');draw=ImageDraw.Draw(sheet)
  for k in range(start,min(start+6,len(doc))):
   pix=doc[k].get_pixmap(matrix=fitz.Matrix(.76,.76),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((380,825))
   x=(k-start)%3*400+10;y=(k-start)//3*870+33;sheet.paste(im,(x,y));draw.text((x,y-28),f'PDF {k+1}',fill='black',font=font)
  sheet.save(visual/f'sheet_{start+1:03d}.jpg',quality=90)
 print(json.dumps({k:v for k,v in report.items() if k not in ['tables','page_info']},ensure_ascii=False,indent=2))
 print('table count',len(tabledata),'tables with long-cell warnings',sum(bool(t['missing_long_cells']) for t in tabledata))
if __name__=='__main__':main(sys.argv[1])
