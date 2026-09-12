import fitz,json,re,hashlib
from pathlib import Path
b=Path('tools/hwpx_transfer/staging/review_260913_0239'); o=b/'visual_G'; d=fitz.open(b/'final.pdf')
checks={}
for n,letter,count in [(138,'B',8),(139,'C',4),(141,'D',8),(142,'E',4),(146,'B',8),(147,'C',4)]:
 p=d[n-1]; txt=p.get_text(); checks[n]={'rows':{f'{letter}-{i}':len(re.findall(fr'{letter}[-–]{i}(?![0-9])',txt)) for i in range(1,count+1)},'response_symbols':{s:txt.count(s) for s in '①②③④⑤'}}
 r=fitz.Rect(325,210 if n in [138,139,146,147] else 100 if n==141 else 165,522,355 if n in [139,147] else 310 if n in [138,146] else 195 if n==141 else 260)
 p.get_pixmap(matrix=fitz.Matrix(3,3),clip=r).save(o/f'header_detail_{n}.png')
checks['sha256']={name:hashlib.sha256((b/name).read_bytes()).hexdigest() for name in ['final.pdf','final.hwpx']}
(o/'row_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=True))
