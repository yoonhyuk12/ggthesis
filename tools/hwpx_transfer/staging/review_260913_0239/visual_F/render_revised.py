from pathlib import Path
import fitz,json,sys,hashlib
from PIL import Image,ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239'); src=base/sys.argv[1];out=base/'visual_F'/'revised';out.mkdir(exist_ok=True)
d=fitz.open(src);info=[]
for n in range(56,101):
 p=d[n-1]; p.get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(out/f'page_{n:03}.png'); info.append({'page':n,'text':p.get_text(),'tables':[{'bbox':t.bbox,'rows':t.extract()} for t in p.find_tables().tables]})
for start in range(56,101,9):
 sh=Image.new('RGB',(1200,1740),'#ddd'); dr=ImageDraw.Draw(sh)
 for j,n in enumerate(range(start,min(start+9,101))):
  im=Image.open(out/f'page_{n:03}.png');im.thumbnail((390,550));x=j%3*400;y=j//3*580;sh.paste(im,(x,y+25));dr.text((x+10,y+5),f'PHYSICAL PAGE {n}',fill='black')
 sh.save(out/f'contact_{start}_{min(start+8,100)}.png')
(out/'extraction.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'source.json').write_text(json.dumps({'file':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pages':len(d)},indent=2))
print([(i['page'],len(i['tables'])) for i in info])
