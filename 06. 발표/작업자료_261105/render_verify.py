import json, pathlib,win32com.client,time
base=pathlib.Path(__file__).resolve().parent;r=json.loads((base/'verification.json').read_text(encoding='utf-8'))
app=win32com.client.Dispatch('PowerPoint.Application')
p=app.Presentations.Open(r['output_pptx'],ReadOnly=False,Untitled=False,WithWindow=False)
print('OPEN',p.Slides.Count)
issues=[]
for i in range(1,p.Slides.Count+1):
 sl=p.Slides(i)
 for sh in sl.Shapes:
  if sh.HasTextFrame and sh.TextFrame.HasText:
   tf=sh.TextFrame2
   if tf.TextRange.BoundHeight>sh.Height+1.5:issues.append({'slide':i,'shape':sh.Id,'text':sh.TextFrame.TextRange.Text[:90],'bound_height':tf.TextRange.BoundHeight,'shape_height':sh.Height})
p.SaveAs(r['output_pdf'],32)
p.Close()
r['checks'].extend([{'powerpoint_open_slides':27},{'powerpoint_text_height_overflow':issues},{'pdf_export':'success'}])
(base/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(issues,ensure_ascii=False,indent=2))
import pymupdf as fitz
from PIL import Image,ImageDraw
pdf=fitz.open(r['output_pdf']);imgs=[]
for i,page in enumerate(pdf):
 pix=page.get_pixmap(matrix=fitz.Matrix(1.1,1.1));pix.save(str(base/f'slide_{i+1:02d}.png'))
 im=Image.open(base/f'slide_{i+1:02d}.png');im.thumbnail((480,360));imgs.append(im.copy())
for start in range(0,len(imgs),9):
 c=Image.new('RGB',(1440,1140),'#d2d7df');d=ImageDraw.Draw(c)
 for j,im in enumerate(imgs[start:start+9]):
  x=(j%3)*480;y=(j//3)*380;c.paste(im,(x,y+20));d.text((x+5,y+3),str(start+j+1),fill='black')
 c.save(base/f'contact_{start+1:02d}.png')
print('PDF_PAGES',len(pdf))
