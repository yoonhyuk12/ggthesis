from pathlib import Path
import json,win32com.client,pymupdf as f,hashlib,re
from pptx import Presentation
from PIL import Image,ImageDraw
B=Path('06. 발표/작업자료_261108');r=json.loads((B/'divider_verification.json').read_text(encoding='utf-8'));app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(r['output_pptx'],ReadOnly=True,Untitled=False,WithWindow=False);assert d.Slides.Count==31;issues=[]
for no in r['divider_slides']:
 for s in d.Slides(no).Shapes:
  if s.HasTextFrame and s.TextFrame.HasText and s.TextFrame2.TextRange.BoundHeight>s.Height+1.5:issues.append({'slide':no,'shape':s.Id,'text':s.TextFrame.TextRange.Text})
d.SaveAs(r['output_pdf'],32);d.Close();pdf=f.open(r['output_pdf']);assert len(pdf)==31
sheet=Image.new('RGB',(1440,780),'#d2d7df');draw=ImageDraw.Draw(sheet)
for j,no in enumerate(r['divider_slides']):
 path=B/f'divider_slide_{no:02d}.png';pdf[no-1].get_pixmap(matrix=f.Matrix(1.4,1.4)).save(str(path));im=Image.open(path);im.thumbnail((480,360));x=(j%3)*480;y=(j//3)*390;sheet.paste(im,(x,y+25));draw.text((x+5,y+5),str(no),fill='black')
sheet.save(B/'divider_contact.png')
p=Presentation(r['output_pptx']);nums=[next(x.text for x in s.shapes if x.shape_id==13) for s in list(p.slides)[1:]];assert nums==list(map(str,range(2,32)))
labels=[];texts=[]
for i,s in enumerate(p.slides,1):
 texts.append(s.notes_slide.notes_text_frame.text)
 for x in s.shapes:
  if x.has_text_frame:texts.append(x.text)
  if x.has_table:texts.extend(c.text for row in x.table.rows for c in row.cells)
for no in r['divider_slides']:
 labels.append(next(x.text for x in p.slides[no-1].shapes if x.shape_id==2))
assert labels==['제1장','제2장','제3장','제4장','제5장']
assert not re.search(r'\b(WHY|HOW|WHAT)\b|A-9|과정지표|지시 전달 소요시간','\n'.join(texts),re.I)
assert not issues,issues
assert hashlib.sha256(Path(r['source_pptx']).read_bytes()).hexdigest()==r['source_sha256']
r['checks'].extend([{'powerpoint_open_slides':31},{'pdf_pages':31},{'new_divider_text_overflow':issues},{'page_numbers_continuous':'2–31'},{'chapter_divider_order':labels},{'excluded_terms_absent':True}]);(B/'divider_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS31; dividers3,6,9,17,24; overflow0; numbers2-31; PDF31; originals unchanged')
