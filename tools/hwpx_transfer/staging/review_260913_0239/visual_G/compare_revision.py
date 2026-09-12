import fitz,json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
b=Path('tools/hwpx_transfer/staging/review_260913_0239'); name=sys.argv[1]; o=b/'visual_G'/Path(name).stem; o.mkdir(exist_ok=True)
a=fitz.open(b/'final.pdf'); d=fitz.open(b/name); old={hashlib.sha256(p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).samples).hexdigest():p.number+1 for p in a}; meta=[]
for n in range(101,len(d)+1):
 p=d[n-1]; pix=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)); pix.save(o/f'page_{n}.png'); digest=hashlib.sha256(pix.samples).hexdigest()
 meta.append({'page':n,'identical_initial_page':old.get(digest),'text':p.get_text(),'tables':[list(t.bbox) for t in p.find_tables().tables]})
for start in range(101,len(d)+1,8):
 sheet=Image.new('RGB',(1600,1180),'#ccc'); draw=ImageDraw.Draw(sheet)
 for k,n in enumerate(range(start,min(start+8,len(d)+1))):
  im=Image.open(o/f'page_{n}.png'); im.thumbnail((390,550)); x=k%4*400; y=k//4*590; sheet.paste(im,(x,y+25));draw.text((x+5,y+5),f'PHYSICAL PAGE {n}',fill='black')
 sheet.save(o/f'contact_{start}_{min(start+7,len(d))}.png')
(o/'extraction.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8'); print('pages',len(d));print('changed', [x['page'] for x in meta if not x['identical_initial_page']]);print('identical',[x['page'] for x in meta if x['identical_initial_page']])
