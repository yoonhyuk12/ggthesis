from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
base=Path('tools/hwpx_transfer/staging/review_260913_0239');out=base/'visual_E'/'layout_final';out.mkdir(exist_ok=True)
b=fitz.open(base/'layout_final.pdf');meta=[]
for i in range(55):
 p=b[i];p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(out/f'p{i+1:03}.png')
 tables=[]
 if len(p.get_drawings()) and i>11:
  for t in p.find_tables().tables:tables.append({'bbox':list(t.bbox),'rows':t.row_count,'cols':t.col_count,'cells':t.extract()})
 meta.append({'page':i+1,'text':p.get_text(),'tables':tables})
for s in range(0,55,6):
 sheet=Image.new('RGB',(1200,1740),'#aaaaaa');d=ImageDraw.Draw(sheet)
 for j in range(s,min(s+6,55)):
  im=Image.open(out/f'p{j+1:03}.png');im.thumbnail((590,550));x=(j-s)%2*600;y=(j-s)//2*580;sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'Layout final physical {j+1}',fill='black')
 sheet.save(out/f'contact_{s+1:03}_{min(s+6,55):03}.png')
r={'pages':len(b),'sha256':hashlib.sha256((base/'layout_final.pdf').read_bytes()).hexdigest(),'page_details':meta};(out/'audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('pages',len(b),'sha',r['sha256']);print('tables',[(m['page'],[(t['bbox'],t['rows'],t['cols']) for t in m['tables']]) for m in meta if m['tables']])
