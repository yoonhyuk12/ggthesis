from pathlib import Path
import json,zipfile,hashlib,collections,re,sys
import xml.etree.ElementTree as E
import fitz
HERE=Path(__file__).resolve().parent
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H='{http://www.hancom.co.kr/hwpml/2011/head}'
def read(path):
 with zipfile.ZipFile(path) as z:
  head=E.fromstring(z.read('Contents/header.xml'));sec=E.fromstring(z.read('Contents/section2.xml'))
 return head,sec
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def tables(sec):
 out=[]
 for i,t in enumerate(sec.iter(P+'tbl')):
  cells=[]
  for row in t.findall(P+'tr'):
   for c in row.findall(P+'tc'):
    sub=c.find(P+'subList');texts=[own(p) for p in sub.findall(P+'p') if own(p)] if sub is not None else []
    cells.append({'addr':c.find(P+'cellAddr').attrib,'span':c.find(P+'cellSpan').attrib,'width':c.find(P+'cellSz').get('width'),'paragraphs':texts})
  out.append({'index':i,'rows':t.get('rowCnt'),'cols':t.get('colCnt'),'width':t.find(P+'sz').get('width'),'cells':cells})
 return out
def main():
 name=sys.argv[1] if len(sys.argv)>1 else 'final'
 bh,bs=read(HERE/'base_snapshot.hwpx');fh,fs=read(HERE/(name+'.hwpx'))
 old=tables(bs);new=tables(fs);table_equal=old==new
 (HERE/'tables.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
 bt=[own(p) for p in bs.iter(P+'p') if own(p)];ft=[own(p) for p in fs.iter(P+'p') if own(p)]
 manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
 expected=[t for t in bt if not t.startswith('[그림 삽입 예정:')]
 for i,t in enumerate(expected):
  for a,b in manifest['text_corrections']:t=t.replace(a,b)
  expected[i]=t
 note='자료: 기존 학회논문의 실제 모니터링·판정 교정 화면.'
 ft_no_note=[t for t in ft if t!=note]
 def markers(head,sec):
  colors={c.get('id'):c.get('textColor') for c in head.iter(H+'charPr')}
  return collections.Counter((own(p),tuple(colors.get(r.get('charPrIDRef')) for r in p.findall(P+'run'))) for p in sec.iter(P+'p') if any(s in own(p) for s in ['[DATA PENDING','[확정 필요','[CITE_TODO','[UNVERIFIED']))
 marker_equal=markers(bh,bs)==markers(fh,fs)
 report={'table_count':len(old),'all_table_cells_text_width_grid_equal':table_equal,'body_text_sequence_equal_except_intended_changes':expected==ft_no_note,'remaining_marker_colors_equal':marker_equal,'picture_count':len(list(fs.iter(P+'pic')))}
 if not table_equal:report['changed_tables']=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
 doc=fitz.open(HERE/(name+'.pdf'));report['pages']=len(doc)
 figure_pages=[]
 for i,p in enumerate(doc):
  if p.get_images():
   figure_pages.append(i+1);p.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(HERE/f'figure_page_{i+1}.png')
 report['figure_pdf_pages']=figure_pages
 (HERE/(name+'_verification.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
