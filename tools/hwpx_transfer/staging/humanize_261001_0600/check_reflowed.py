"""Main only: reflowed.hwpx/.pdf vs candidate.hwpx and base PDF. Writes check_reflowed.json + png/ contact sheets of changed pages."""
import json, re, sys, zipfile, hashlib
from pathlib import Path
from lxml import etree as E
import fitz
from PIL import Image, ImageDraw
Q = Path(__file__).resolve().parent; ROOT = Q.parents[3]
P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'; H = '{http://www.hancom.co.kr/hwpml/2011/head}'
MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def own(p): return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def load(path):
    with zipfile.ZipFile(path) as z: return {n: z.read(n) for n in z.namelist()}
def reds(header): return {c.get('id') for c in E.fromstring(header).iter(H+'charPr') if c.get('textColor', '').upper() == '#FF0000'}
def markers(d):
    red = reds(d['Contents/header.xml']); out = []
    for p in E.fromstring(d['Contents/section2.xml']).iter(P+'p'):
        colors = []
        for r in p.findall(P+'run'): colors += [r.get('charPrIDRef') in red] * len(''.join(''.join(t.itertext()) for t in r.findall(P+'t')))
        v = own(p); out += [(m.group(), all(colors[m.start():m.end()])) for m in MARK.finditer(v)]
    return out
def main(base_pdf, name='reflowed', ref='candidate'):
    cd = load(Q/f'{ref}.hwpx'); rd = load(Q/f'{name}.hwpx'); rep = {}
    ct = [own(p) for p in E.fromstring(cd['Contents/section2.xml']).iter(P+'p') if own(p).strip()]
    rt = [own(p) for p in E.fromstring(rd['Contents/section2.xml']).iter(P+'p') if own(p).strip()]
    rep['text_preserved'] = ct == rt; rep['nonempty_paras'] = [len(ct), len(rt)]
    if ct != rt:
        import difflib; rep['text_diff'] = [x[:200] for x in difflib.unified_diff(ct, rt, lineterm='', n=0)][:40]
    rm = markers(rd); rep['markers'] = len(rm); rep['markers_not_red'] = [m for m, ok in rm if not ok]
    rs = E.fromstring(rd['Contents/section2.xml'])
    rep['tables'] = len(list(rs.iter(P+'tbl'))); rep['pics'] = len(list(rs.iter(P+'pic')))
    rep['cell_break'] = rd['Contents/section2.xml'].count(b'pageBreak="CELL"')
    a = fitz.open(base_pdf); b = fitz.open(Q/f'{name}.pdf'); rep['pages'] = [len(a), len(b)]
    changed = []; intr = []
    for i in range(len(b)):
        pb = b[i]; hgt = pb.rect.height
        for blk in pb.get_text('dict')['blocks']:
            for l in blk.get('lines', []):
                t = ''.join(s['text'] for s in l['spans']).strip()
                if l['bbox'][3] > hgt*0.905 and t and not re.fullmatch(r'[-–]\s*\d+\s*[-–]', t): intr.append((i+1, round(l['bbox'][3]), t[:50]))
        if i < len(a) and a[i].get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).samples != pb.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).samples: changed.append(i+1)
    rep['changed_pages'] = changed; rep['footer_intrusions'] = intr
    out = Q/'png'; out.mkdir(exist_ok=True); sheets = []
    for s in range(0, len(changed), 6):
        grp = changed[s:s+6]; sheet = Image.new('RGB', (1200, 1740), '#aaaaaa'); d = ImageDraw.Draw(sheet)
        for j, pg in enumerate(grp):
            pm = b[pg-1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)); im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples); im.thumbnail((590, 550))
            x = j % 2 * 600; y = j // 2 * 580; sheet.paste(im, (x, y+25)); d.text((x+10, y+5), f'{name} p{pg}', fill='black')
        f = out/f'{name}_sheet_{s//6+1:02}.png'; sheet.save(f); sheets.append(f.name)
    rep['sheets'] = sheets; rep['pdf_sha256'] = hashlib.sha256((Q/f'{name}.pdf').read_bytes()).hexdigest()
    (Q/f'check_{name}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'text_diff'}, ensure_ascii=False))
if __name__ == '__main__': main(*sys.argv[1:])
