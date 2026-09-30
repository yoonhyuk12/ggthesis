"""Integrated XML/PDF checks; visual page inspection is separately recorded."""
from pathlib import Path
import sys,json,re,zipfile,hashlib,collections
from lxml import etree as E
import fitz
import refresh_toc as T
Q=Path(__file__).resolve().parent
P=T.P;H='{http://www.hancom.co.kr/hwpml/2011/head}'
MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def xmls(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  return {n:E.fromstring(z.read(n)) for n in z.namelist() if n.endswith('.xml')}
def main(name):
 report={};source=json.loads((Q/'source.json').read_text(encoding='utf-8'))
 assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
 report['original_unchanged']=True
 base=xmls(Q/'base.hwpx');expected=xmls(Q/'candidate.hwpx');current=xmls(Q/(name+'.hwpx'))
 b=current['Contents/section2.xml'];header=current['Contents/header.xml']
 expected_text=T.norm(''.join(own(p) for p in expected['Contents/section2.xml'].iter(P+'p')))
 actual_text=T.norm(''.join(own(p) for p in b.iter(P+'p')))
 report['body_text_preserved_through_reflow']=expected_text==actual_text
 assert report['body_text_preserved_through_reflow']
 tabs=[]
 for sec,root in current.items():
  if not re.fullmatch(r'Contents/section\d+\.xml',sec):continue
  for i,table in enumerate(root.iter(P+'tbl')):
   assert table.get('pageBreak')!='CELL'
   width=int(table.find(P+'sz').get('width'));grid={}
   for row in table.findall(P+'tr'):
    for cell in row.findall(P+'tc'):
     a=cell.find(P+'cellAddr');s=cell.find(P+'cellSpan');w=int(cell.find(P+'cellSz').get('width'))
     rr,cc=int(a.get('rowAddr')),int(a.get('colAddr'));rs,cs=int(s.get('rowSpan')),int(s.get('colSpan'))
     for y in range(rr,rr+rs):
      for x in range(cc,cc+cs):assert (y,x) not in grid;grid[y,x]=w/cs
   for y in range(int(table.get('rowCnt'))):assert abs(sum(grid[y,x] for x in range(int(table.get('colCnt'))))-width)<2,(sec,i,y)
   tabs.append(dict(section=sec,table=i,width=width,rows=table.get('rowCnt'),cols=table.get('colCnt')))
 report['table_grids']=tabs
 colors={c.get('id'):c.get('textColor','').upper() for c in header.iter(H+'charPr')};markers=[]
 for sec,root in current.items():
  if not re.fullmatch(r'Contents/section\d+\.xml',sec):continue
  for p in root.iter(P+'p'):
   value='';cs=[]
   for r in p.findall(P+'run'):
    text=''.join(''.join(t.itertext()) for t in r.findall(P+'t'));value+=text;cs.extend([colors[r.get('charPrIDRef')]]*len(text))
   for m in MARK.finditer(value):
    markers.append(m.group());assert all(c=='#FF0000' for c in cs[m.start():m.end()]),(sec,m.group())
 report['red_marker_count']=len(markers)
 report['experiment_pending_count']=markers.count('실험전')
 doc=fitz.open(Q/(name+'.pdf'));pdfs=[T.norm(re.sub(r'(?m)^\s*-\s*\d+\s*-\s*$','',p.get_text())) for p in doc];pdftext=''.join(pdfs)
 missing=[dict(text=s,expected=n,actual=pdftext.count(s)) for s,n in collections.Counter(T.norm(x) for x in markers).items() if pdftext.count(s)<n]
 report['missing_marker_multiplicity']=missing
 local=[]
 for i,table in enumerate(b.iter(P+'tbl')):
  texts=[T.norm(own(p)) for p in table.iter(P+'p') if own(p).strip()]
  counts=collections.Counter(texts);scores=[sum(min(t.count(s),n)*min(len(s),70) for s,n in counts.items()) for t in pdfs]
  best=max(range(len(doc)),key=lambda k:scores[k]);window=''.join(pdfs[max(0,best-2):min(len(doc),best+3)])
  local.append(dict(table=i,likely_page=best+1,missing=[dict(text=s,expected=n,actual=window.count(s)) for s,n in counts.items() if window.count(s)<n]))
 report['tables_local_text']=local
 mapping=T.mapping(Q/(name+'.pdf'));report['toc_unresolved']=mapping['unresolved'];entries=mapping['entries']
 tps=[p for p in current['Contents/section1.xml'].iter(P+'p') if p.find('.//'+P+'tab') is not None]
 report['toc_wrong_folios']=[dict(text=e['body_text'],expected=e['printed'],actual=own(p)) for p,e in zip(tps,entries) if not re.search(r'\d+$',own(p)) or int(re.search(r'\d+$',own(p))[0])!=e['printed']]
 report['toc_count']=len(entries);report['pages']=len(doc)
 report['figure_count']=len(list(b.iter(P+'pic')))
 report['warnings']=dict(marker_missing=len(missing),table_text_missing=sum(bool(x['missing']) for x in local),toc_unresolved=len(mapping['unresolved']),toc_wrong=len(report['toc_wrong_folios']))
 (Q/(name+'_verification.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['table_grids','tables_local_text']},ensure_ascii=False,indent=2))
if __name__=='__main__':main(sys.argv[1])
