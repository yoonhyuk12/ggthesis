# QA_back_final_check: 내용 기반으로 대상 표 쪽을 찾아 잘림·꼬리말 침범·실험전 줄바꿈/색·중첩 폭·부록 표지를 검사(읽기 전용)
import sys, json, re
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
PDF = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else 'final'
DPI = 130; S = DPI / 72
# HWPX 쪽(53858×72567 HU)이 PDF A4 폭에 맞춰 균일 확대됨: 배율 = 595/538.58
BODY_BOTTOM = (9921 + 54144) / 100.0 * (595.0 / 538.58)   # ≈707.8pt (본문 하한)
T = json.load(open('QA_back_final_targets.json', encoding='utf-8'))
doc = pymupdf.open(PDF)
norm = lambda s: re.sub(r'\s+', '', s)
ptxt = [norm(p.get_text()) for p in doc]
def find(sub, start):
    for i in range(start, len(doc)):
        if sub in ptxt[i]: return i
    return None
def lines(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            txt = ''.join(s['text'] for s in l['spans'])
            out.append((txt, l['bbox'], l['spans']))
    return out
def pn_top(page):
    for txt, bb, _ in lines(page):
        if re.fullmatch(r'\s*-\s*\d+\s*-\s*', txt) and bb[1] > BODY_BOTTOM: return bb[1], txt.strip()
    return None, None
def footer_intrusion(i):
    page = doc[i]; top, pn = pn_top(page)
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    W, H = pix.width, pix.height; sm = pix.samples
    y0 = int(BODY_BOTTOM * S) + 2; y1 = int((top if top else BODY_BOTTOM + 30) * S) - 2
    hits = [y for y in range(y0, y1) if any(sm[y * W + x] < 160 for x in range(0, W, 2))]
    # 본문 영역 마지막 잉크 행
    last = max([y for y in range(int(90 * S), y0) if any(sm[y * W + x] < 160 for x in range(0, W, 3))] or [0])
    return dict(page=i + 1, pageno=pn, body_last_px=last, body_bottom_px=round(BODY_BOTTOM * S, 1),
                band_px=(hits[0], hits[-1]) if hits else None)
def marker_stats(i):
    n = 0; split = []; nonred = 0
    for txt, bb, spans in lines(doc[i]):
        c = txt.replace(' ', ''); n += c.count('실험전')
        r = c.replace('실험전', '')
        if re.search(r'실험$|^험전|^전$|^실$|^험$|실$', r) and ('실' in r or '험' in r or r == '전'):
            split.append((round(bb[1] / 1 * S), c[:30]))
        for s in spans:
            if '실험' in s['text'] or s['text'].strip() in ('실', '험', '전', '험전'):
                if s['color'] != 0xFF0000 and ((s['color'] >> 16) & 255) < 200: nonred += 1
    return n, split, nonred
def nested(i):
    page = doc[i]; dr = page.get_drawings(); out = []
    for g in dr:
        f = g.get('fill')
        if f and abs(f[0]-f[1]) < .02 and .2 < f[0] < .9 and g['rect'].width > 150:
            y = (g['rect'].y0 + g['rect'].y1) / 2
            vx = sorted({round(x['rect'].x0, 1) for x in dr if x['rect'].width < 2 and x['rect'].height > 10
                         and x['rect'].y0 <= y <= x['rect'].y1})
            left = max([v for v in vx if v < g['rect'].x0] or [None], key=lambda v: v or 0)
            right = min([v for v in vx if v > g['rect'].x1] or [9999])
            out.append(dict(page=i + 1, gray=[round(g['rect'].x0, 1), round(g['rect'].x1, 1)], parent_left=left,
                            parent_right=None if right == 9999 else right, page_w=page.rect.width,
                            gap_left=round(g['rect'].x0 - left, 1) if left else None,
                            gap_right=None if right == 9999 else round(right - g['rect'].x1, 1)))
    return out
res = []; cur = 0
for d in T:
    key = d['head']
    s = find(key[:16], cur)
    if s is None: res.append(dict(table=d['table_idx'], error='head not found')); continue
    e = find(d['lastrow_tail'], s) if d['lastrow_tail'] else s
    r = dict(table=d['table_idx'], caption=d['caption'][:30], start=s + 1, end=(e + 1) if e is not None else None,
             expect_실험전=d['n_실험전'])
    if d['n_실험전']:
        tot = 0; sp = []; nr = 0
        for i in range(s, (e if e is not None else s) + 1):
            n, split, nonred = marker_stats(i); tot += n; sp += [(i + 1,) + x for x in split]; nr += nonred
        r.update(found_실험전_on_pages=tot, split_lines=sp[:12], n_split=len(sp), nonred_spans=nr)
    r['footer'] = [footer_intrusion(i) for i in range(s, (e if e is not None else s) + 1)]
    if d['table_idx'] in (44, 51): r['nested'] = nested(s)
    if d['table_idx'] in (42, 49):
        title = '부록(도입현장)' if d['table_idx'] == 42 else '부록(미도입현장)'
        tp = find(title, max(cur - 1, 0)); r['title_page'] = tp + 1 if tp is not None else None
    res.append(r); cur = s if d['parent'] is None else cur
    if d['parent'] is None: cur = s
json.dump(res, open(f'QA_back_{TAG}_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in res: print(json.dumps(r, ensure_ascii=False))
