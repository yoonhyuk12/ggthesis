from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239'); out=base/'visual_E'; out.mkdir(exist_ok=True)
doc=fitz.open(base/'final.pdf'); meta=[]
for i in range(55):
 p=doc[i]; pix=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)); pix.save(out/f'p{i+1:03}.png')
 meta.append({'page':i+1,'size':list(p.rect),'text':p.get_text(),'drawings':len(p.get_drawings())})
for s in range(0,55,6):
 sheet=Image.new('RGB',(1200,1740),'#aaaaaa'); d=ImageDraw.Draw(sheet)
 for j in range(s,min(s+6,55)):
  im=Image.open(out/f'p{j+1:03}.png'); im.thumbnail((590,550)); x=(j-s)%2*600;y=(j-s)//2*580; sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'Physical page {j+1}',fill='black')
 sheet.save(out/f'contact_{s+1:03}_{min(s+6,55):03}.png')
(out/'pages.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print('pages',len(doc));print([(m['page'],m['drawings']) for m in meta]); print('sha256',hashlib.sha256((base/'final.pdf').read_bytes()).hexdigest())
