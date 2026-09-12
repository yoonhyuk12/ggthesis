from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239');out=base/'visual_E'/'final2';out.mkdir(exist_ok=True)
a=fitz.open(base/'final.pdf');b=fitz.open(base/'final2.pdf');changes=[]
for i in range(55):
 old=a[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5));new=b[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
 new.save(out/f'p{i+1:03}.png')
 if old.samples!=new.samples:changes.append(i+1)
for s in range(0,55,6):
 sheet=Image.new('RGB',(1200,1740),'#aaaaaa');d=ImageDraw.Draw(sheet)
 for j in range(s,min(s+6,55)):
  im=Image.open(out/f'p{j+1:03}.png');im.thumbnail((590,550));x=(j-s)%2*600;y=(j-s)//2*580;sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'Final2 physical {j+1}',fill='black')
 sheet.save(out/f'contact_{s+1:03}_{min(s+6,55):03}.png')
r={'pages':len(b),'changed_pages_1_55':changes,'sha256':hashlib.sha256((base/'final2.pdf').read_bytes()).hexdigest()};(out/'comparison.json').write_text(json.dumps(r,indent=2));print(r)
