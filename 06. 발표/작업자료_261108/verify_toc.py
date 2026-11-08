from pathlib import Path
import json,win32com.client,pymupdf as f,hashlib
B=Path('06. 발표/작업자료_261108');r=json.loads((B/'toc_verification.json').read_text(encoding='utf-8'));app=win32com.client.Dispatch('PowerPoint.Application');p=app.Presentations.Open(r['output_pptx'],ReadOnly=True,Untitled=False,WithWindow=False)
assert p.Slides.Count==25
issues=[]
for s in p.Slides(2).Shapes:
 if s.HasTextFrame and s.TextFrame.HasText and s.TextFrame2.TextRange.BoundHeight>s.Height+1.5:issues.append({'shape':s.Id,'text':s.TextFrame.TextRange.Text})
p.SaveAs(r['output_pdf'],32);p.Close();pdf=f.open(r['output_pdf']);assert len(pdf)==25;pdf[1].get_pixmap(matrix=f.Matrix(1.4,1.4)).save(str(B/'toc_slide_02.png'))
assert not issues,issues
assert hashlib.sha256(Path(r['source_pptx']).read_bytes()).hexdigest()==r['source_sha256']
r['checks'].extend([{'powerpoint_open_slides':25},{'pdf_pages':25},{'new_toc_text_overflow':issues},{'pdf_export':'success'}]);(B/'toc_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS 25 slides; PDF25; new TOC overflow0; original unchanged')
