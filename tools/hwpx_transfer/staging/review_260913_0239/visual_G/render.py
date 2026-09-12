import fitz, json
from pathlib import Path
from PIL import Image, ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239'); out=base/'visual_G'; doc=fitz.open(base/'final.pdf')
meta=[]
for n in range(101,149):
 p=doc[n-1]; pix=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)); pix.save(out/f'page_{n}.png')
 text=p.get_text(); tables=p.find_tables().tables
 meta.append({'page':n,'text':text,'tables':[list(t.bbox) for t in tables]})
for start in range(101,149,8):
 sheet=Image.new('RGB',(1600,2300),'#cccccc'); d=ImageDraw.Draw(sheet)
 for k,n in enumerate(range(start,min(start+8,149))):
  im=Image.open(out/f'page_{n}.png'); im.thumbnail((390,1080)); x=(k%4)*400; y=(k//4)*1150; sheet.paste(im,(x,y+35)); d.text((x+10,y+8),f'PHYSICAL PAGE {n}',fill='black')
 sheet.save(out/f'contact_{start}_{min(start+7,148)}.png')
(out/'extraction.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print('pages',len(doc)); print([(m['page'],len(m['tables'])) for m in meta])
