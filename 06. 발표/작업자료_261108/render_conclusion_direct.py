from pathlib import Path
import json,win32com.client
from PIL import Image,ImageDraw
b=Path('06. 발표/작업자료_261108');r=json.loads((b/'conclusion_only_verification.json').read_text(encoding='utf-8'));app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(r['output_pptx'],ReadOnly=True,Untitled=False,WithWindow=False);issues=[]
for no in [27,28,29]:
 s=d.Slides(no)
 for sh in s.Shapes:
  if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append({'slide':no,'shape':sh.Id,'text':sh.TextFrame.TextRange.Text,'bound':sh.TextFrame2.TextRange.BoundHeight,'height':sh.Height})
 s.Export(str((b/f'conclusion_direct_{no}.png').resolve()),'PNG',1200,900)
d.Close()
r['checks'].extend([{'powerpoint_open_slides':33},{'changed_text_height_overflow':issues},{'render':'PowerPoint Slides.Export PNG directly; no PDF'}]);(b/'conclusion_only_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(issues,ensure_ascii=False))
sheet=Image.new('RGB',(1440,380),'#d2d7df');draw=ImageDraw.Draw(sheet)
for j,no in enumerate([27,28,29]):
 im=Image.open(b/f'conclusion_direct_{no}.png');im.thumbnail((480,360));sheet.paste(im,(j*480,20));draw.text((j*480+5,3),str(no),fill='black')
sheet.save(b/'conclusion_direct_contact.png')
