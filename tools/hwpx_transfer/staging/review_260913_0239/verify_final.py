"""Integration verification of the published candidate; Hancom and visual QA are separate."""
from pathlib import Path
import collections,hashlib,json,re,sys,zipfile
from lxml import etree as E
import fitz
import toc_refresh as T
from surgical_ops import MARK,H,P
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'figures_260912'))
from verify_content import tables,own
def main(name):
 report={};source=json.loads((Q/'source.json').read_text(encoding='utf8'))
 report['source_sha256']=hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()
 assert report['source_sha256']==source['sha256']
 with zipfile.ZipFile(Q/(name+'.hwpx')) as z:
  assert z.testzip() is None
  roots={n:E.fromstring(z.read(n)) for n in z.namelist() if n.endswith('.xml')}
 with zipfile.ZipFile(Q/'candidate.hwpx') as z:
  candidate=E.fromstring(z.read('Contents/section2.xml'))
 with zipfile.ZipFile(Q/'base.hwpx') as z:
  base={n:z.read(n) for n in z.namelist()}
 with zipfile.ZipFile(Q/'candidate.hwpx') as z:
  changed=[n for n in z.namelist() if z.read(n)!=base[n]]
 report['surgical_changed_zip_parts']=changed
 body=roots['Contents/section2.xml'];head=roots['Contents/header.xml']
 assert T.norm(''.join(own(p) for p in candidate.iter(P+'p')))==T.norm(''.join(own(p) for p in body.iter(P+'p')))
 with zipfile.ZipFile(Q/'layout_input.hwpx') as z:layout=E.fromstring(z.read('Contents/section2.xml'))
 assert tables(layout)==tables(body)
 report['body_text_and_table_grid_preserved_through_reflow']=True
 report['table_counts']={k:len(list(v.iter(P+'tbl'))) for k,v in roots.items() if re.fullmatch(r'Contents/section\d+\.xml',k)}
 for root in roots.values():
  for table in root.iter(P+'tbl'):
   assert table.get('pageBreak')!='CELL'
   width=int(table.find(P+'sz').get('width'));grid={}
   for row in table.findall(P+'tr'):
    for cell in row.findall(P+'tc'):
     a=cell.find(P+'cellAddr');s=cell.find(P+'cellSpan');w=int(cell.find(P+'cellSz').get('width'))
     rr,cc=int(a.get('rowAddr')),int(a.get('colAddr'));rs,cs=int(s.get('rowSpan')),int(s.get('colSpan'))
     for y in range(rr,rr+rs):
      for x in range(cc,cc+cs):
       assert (y,x) not in grid
       grid[y,x]=w/cs
   for y in range(int(table.get('rowCnt'))):assert abs(sum(grid[y,x] for x in range(int(table.get('colCnt'))))-width)<1
 report['all_table_grids_valid_and_no_CELL']=True
 ps=body.findall(P+'p');heading_count=0
 for i,p in enumerate(ps):
  if re.match(r'^제\d+[절항]\s',own(p).strip()):
   heading_count+=1;assert i and not own(ps[i-1]).strip() and ps[i-1].find('.//'+P+'tbl') is None
 report['heading_blank_verified']=heading_count
 colors={c.get('id'):c.get('textColor','').upper() for c in head.iter(H+'charPr')};markers=[]
 for p in body.iter(P+'p'):
  text='';cs=[]
  for r in p.findall(P+'run'):
   s=''.join(''.join(t.itertext()) for t in r.findall(P+'t'));text+=s;cs += [colors[r.get('charPrIDRef')]]*len(s)
  for m in MARK.finditer(text):
   markers.append(m.group());assert all(c=='#FF0000' for c in cs[m.start():m.end()]),m.group()
 report['red_markers']=len(markers)
 D=fitz.open(Q/(name+'.pdf'));pdfs=[T.norm(p.get_text()) for p in D];pdftext=''.join(pdfs)
 missing_markers=[(s,n,pdftext.count(s)) for s,n in collections.Counter(T.norm(m) for m in markers).items() if pdftext.count(s)<n]
 report['pdf_marker_multiplicity_missing']=missing_markers
 assert not missing_markers
 local=[]
 for k,tab in enumerate(tables(body)):
  paras=collections.Counter(T.norm(s) for c in tab['cells'] for s in c['paragraphs'] if s)
  scores=[sum(min(t.count(s),n)*min(len(s),50) for s,n in paras.items()) for t in pdfs]
  best=max(range(len(D)),key=lambda p:scores[p]);window=''.join(pdfs[max(0,best-1):min(len(D),best+2)])
  missing=[(s,n,window.count(s)) for s,n in paras.items() if window.count(s)<n]
  local.append({'table':k,'likely_page':best+1,'paragraph_count':sum(paras.values()),'missing':missing})
 assert not any(t['missing'] for t in local)
 report['body_table_local_text_multiplicity']=local
 toc=T.mapping(Q/(name+'.pdf'));assert len(toc['entries'])==132 and not toc['unresolved']
 current=[p for p in roots['Contents/section1.xml'].iter(P+'p') if p.find('.//'+P+'tab') is not None]
 assert len(current)==132
 for p,e in zip(current,toc['entries']):assert int(re.search(r'\d+$',own(p))[0])==e['printed'],e
 report['toc_printed_folios_verified']=132;report['pages']=len(D)
 (Q/(name+'_verification.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in report.items() if k!='body_table_local_text_multiplicity'},ensure_ascii=False))
if __name__=='__main__':main(sys.argv[1])
