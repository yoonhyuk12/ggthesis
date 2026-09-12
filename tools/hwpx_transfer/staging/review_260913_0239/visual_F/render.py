from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239'); out=base/'visual_F'; out.mkdir(exist_ok=True)
doc=fitz.open(base/'final.pdf'); info=[]
for n in range(56,101):
 p=doc[n-1]; pix=p.get_pixmap(matrix=fitz.Matrix(1.6,1.6)); pix.save(out/f'page_{n:03}.png')
 tabs=p.find_tables().tables
 info.append({'page':n,'tables':[list(t.bbox) for t in tabs],'text':p.get_text()})
for start in range(56,101,9):
 sheet=Image.new('RGB',(1200,1740),'#ddd'); d=ImageDraw.Draw(sheet)
 for j,n in enumerate(range(start,min(start+9,101))):
  im=Image.open(out/f'page_{n:03}.png'); im.thumbnail((390,550)); x=(j%3)*400;y=(j//3)*580;sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'PHYSICAL PAGE {n}',fill='black')
 sheet.save(out/f'contact_{start}_{min(start+8,100)}.png')
(out/'extraction.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'hashes.json').write_text(json.dumps({f:hashlib.sha256((base/f).read_bytes()).hexdigest() for f in ['final.pdf','final.hwpx']},indent=2))
print([(i['page'],len(i['tables'])) for i in info]);print('pages',len(doc))
