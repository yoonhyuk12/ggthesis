from pathlib import Path
import fitz,re,json,hashlib
from PIL import Image,ImageDraw
O=Path('tools/hwpx_transfer/staging/full_sync_261104');d=fitz.open(O/'resaved.pdf');b=fitz.open('tools/hwpx_transfer/staging/factcheck_hwpx_261104c/final.pdf')
# Match all page content, allowing a changed printed page number.
def digest(pg):
 pix=pg.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(0,0,pg.rect.width,650),alpha=False);return hashlib.sha256(pix.samples).hexdigest()
old={digest(pg):i+1 for i,pg in enumerate(b)};changes=[];same=[]
for i,pg in enumerate(d):
 h=digest(pg)
 if h in old:same.append({'new':i+1,'base':old[h]})
 else:changes.append(i+1)
for i in changes:
 pg=d[i-1];pg.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(O/f'page_{i}.png')
(O/'pdf_comparison.json').write_text(json.dumps({'pages':len(d),'base_pages':len(b),'unchanged_body_pixels':same,'changed':changes},indent=2),encoding='utf8')
print('pages',len(d),'unchanged',len(same),'changed',changes)
for i,pg in enumerate(d):
 t=re.sub(r'\s+','',pg.get_text())
 if ('논문개요' in t or '부록(도입현장)' in t or '부록(미도입현장)' in t) and i>7:print('heading',i+1,pg.get_text()[:80],pg.get_text()[-55:])
# Render batches only for changed pages; other pages inherit prior verified images.
for start in range(0,len(changes),4):
 sheet=Image.new('RGB',(1400,1900),'white');draw=ImageDraw.Draw(sheet)
 for j,pn in enumerate(changes[start:start+4]):
  im=Image.open(O/f'page_{pn}.png');im.thumbnail((690,910));x=j%2*700;y=j//2*950;sheet.paste(im,(x,y+30));draw.text((x,y),str(pn),fill='black')
 sheet.save(O/f'contact_{start//4}.png')
