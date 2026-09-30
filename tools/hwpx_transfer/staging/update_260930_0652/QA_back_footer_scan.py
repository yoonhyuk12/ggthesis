# QA_back: PNG에서 본문 하단(약 y=885px, 72.39 HU/px) 아래 꼬리말 영역 침범 픽셀 검사
import sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
for p in range(int(sys.argv[1]),int(sys.argv[2])+1):
    im=Image.open(f'visual/p{p:03d}.png').convert('L'); W,H=im.size; px=im.load()
    dark=[sum(1 for x in range(W) if px[x,y]<160) for y in range(H)]
    rows=[y for y in range(H) if dark[y]>0]
    body_last=max([y for y in rows if y<=885] or [0])
    band=[y for y in rows if 886<=y<=924]
    pn=[y for y in rows if 925<=y<=950]
    below=[y for y in rows if y>950]
    print(p,'body_last',body_last,'band',(band[0],band[-1],max(dark[band[0]:band[-1]+1])) if band else '-','pn',(pn[0],pn[-1]) if pn else '-','below',(below[0],below[-1]) if below else '-','INTRUDE' if band or below else '')
