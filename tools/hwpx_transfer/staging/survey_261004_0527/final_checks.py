"""Verify the final Hangeul-saved artifact and the 120 printed TOC folios."""
from pathlib import Path
import collections,hashlib,json,re,zipfile,sys
from lxml import etree as E
import fitz
Q=Path(__file__).resolve().parent;ROOT=Q.parents[3]
sys.path.insert(0,str(Q));import refresh_toc as T
P=T.P;H='{http://www.hancom.co.kr/hwpml/2011/head}'
MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def read(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  result={n:E.fromstring(z.read(n)) for n in z.namelist() if n.endswith('.xml')}
 return result
def formats(roots):
 head=roots['Contents/header.xml'];faces={f.get('lang'):{c.get('id'):c.get('face') for c in f} for f in head.iter(H+'fontface')};styles={}
 for c in head.iter(H+'charPr'):
  ref=c.find(H+'fontRef');styles[c.get('id')]=[c.get('height'),c.get('textColor'),[(lang,faces.get(lang,{}).get(ref.get(key))) for lang,key in [('HANGUL','hangul'),('LATIN','latin')]],c.find(H+'bold') is not None,c.find(H+'italic') is not None,dict(c.find(H+'ratio').attrib),dict(c.find(H+'spacing').attrib)]
 return styles
def body_signature(roots):
 styles=formats(roots);parts=[]
 for p in roots['Contents/section2.xml'].iter(P+'p'):
  for r in p.findall(P+'run'):
   text=''.join(''.join(t.itertext()) for t in r.findall(P+'t'))
   if text:parts.extend((ch,styles[r.get('charPrIDRef')]) for ch in text)
 return hashlib.sha256(json.dumps(parts,ensure_ascii=False).encode()).hexdigest()
def main():
 report={};source=json.loads((Q/'source_manifest.json').read_text(encoding='utf-8'))
 report['original_unchanged']=hashlib.sha256((ROOT/source['source']).read_bytes()).hexdigest()==source['source_sha256']
 report['md_sources_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in source['md_sha256'].items())
 final=read(Q/'final.hwpx');ready=read(Q/'ready.hwpx');candidate=read(Q/'candidate.hwpx')
 report['body_text_matches_transfer']=T.norm(''.join(own(p) for p in final['Contents/section2.xml'].iter(P+'p')))==T.norm(''.join(own(p) for p in candidate['Contents/section2.xml'].iter(P+'p')))
 report['body_resolved_fonts_and_styles_preserved']=body_signature(final)==body_signature(ready)
 doc=fitz.open(Q/'final.pdf');before=fitz.open(Q/'ready.pdf');report['pages']=len(doc);assert len(doc)==len(before)
 mapping=T.mapping(Q/'final.pdf');report['toc_unresolved']=mapping['unresolved'];report['toc_entries']=len(mapping['entries'])
 tps=[p for p in final['Contents/section1.xml'].iter(P+'p') if p.find('.//'+P+'tab') is not None]
 report['wrong_toc_folios']=[{'title':e['body_text'],'expected':e['printed'],'actual':own(p)} for p,e in zip(tps,mapping['entries']) if not re.search(r'\d+$',own(p)) or int(re.search(r'\d+$',own(p))[0])!=e['printed']]
 assert len(tps)==len(mapping['entries'])==120
 body_start=min(e['physical'] for e in mapping['entries'])
 changed=[]
 for i,(p,q) in enumerate(zip(doc,before)):
  if p.get_pixmap(matrix=fitz.Matrix(.6,.6),alpha=False).samples!=q.get_pixmap(matrix=fitz.Matrix(.6,.6),alpha=False).samples:changed.append(i+1)
 report['pdf_changed_pages_after_toc']=changed;report['all_body_pages_pixel_identical']=all(i<body_start for i in changed)
 styles=formats(final);bad=[];markers=[];tables=0;grid_errors=[]
 for sec,root in final.items():
  if not re.fullmatch(r'Contents/section\d+\.xml',sec):continue
  for p in root.iter(P+'p'):
   text=own(p);colors=[]
   for r in p.findall(P+'run'):colors.extend([styles[r.get('charPrIDRef')][1].upper()]*sum(len(''.join(t.itertext())) for t in r.findall(P+'t')))
   for m in MARK.finditer(text):
    markers.append(m.group())
    if any(c!='#FF0000' for c in colors[m.start():m.end()]):bad.append(m.group())
  for ti,t in enumerate(root.iter(P+'tbl')):
   tables+=1;w=int(t.find(P+'sz').get('width'));grid={};nr=int(t.get('rowCnt'));nc=int(t.get('colCnt'))
   for tr in t.findall(P+'tr'):
    for c in tr.findall(P+'tc'):
     a=c.find(P+'cellAddr');s=c.find(P+'cellSpan');sz=c.find(P+'cellSz');rr,cc=int(a.get('rowAddr')),int(a.get('colAddr'));rs,cs=int(s.get('rowSpan')),int(s.get('colSpan'))
     for y in range(rr,rr+rs):
      for x in range(cc,cc+cs):
       if (y,x) in grid:grid_errors.append((sec,ti,'overlap'))
       grid[y,x]=int(sz.get('width'))/cs
   if len(grid)!=nr*nc or any(abs(sum(grid.get((y,x),0) for x in range(nc))-w)>3 for y in range(nr)) or t.get('pageBreak')=='CELL':grid_errors.append((sec,ti,'geometry'))
 report.update(table_count=tables,grid_errors=grid_errors,marker_count=len(markers),pending_count=markers.count('실험전'),marker_color_errors=bad)
 full=T.norm(''.join(re.sub(r'(?m)^\s*-\s*\d+\s*-\s*$','',p.get_text()) for p in doc))
 report['missing_markers']=[{'text':s,'expected':n,'actual':full.count(s)} for s,n in collections.Counter(T.norm(m) for m in markers).items() if full.count(s)<n]
 footer_warnings=[]
 for i,page in enumerate(doc):
  spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans']]
  foot=[s for s in spans if s['bbox'][1]>page.rect.height*.88 and re.fullmatch(r'\s*-\s*\d+\s*-\s*',s['text'])]
  if foot:
   limit=min(s['bbox'][1] for s in foot)-2
   badbody=[s['text'] for s in spans if s['text'].strip() and s not in foot and s['bbox'][3]>limit]
   if badbody:footer_warnings.append({'physical':i+1,'text':badbody})
 report['body_text_footer_overlap']=footer_warnings
 report['ok']=all(report[k] for k in ['original_unchanged','md_sources_unchanged','body_text_matches_transfer','body_resolved_fonts_and_styles_preserved','all_body_pages_pixel_identical']) and not any(report[k] for k in ['toc_unresolved','wrong_toc_folios','grid_errors','marker_color_errors','missing_markers','body_text_footer_overlap'])
 (Q/'final_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2));assert report['ok']
if __name__=='__main__':main()
