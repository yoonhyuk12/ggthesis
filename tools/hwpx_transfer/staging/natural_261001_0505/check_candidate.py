"""Read-only XML checks: base.hwpx vs candidate.hwpx against spec.json (replace + insert)."""
import json, re, sys, zipfile, hashlib
from pathlib import Path
from lxml import etree as E
Q = Path(__file__).resolve().parent
P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'; H = '{http://www.hancom.co.kr/hwpml/2011/head}'
MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def own(p): return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def load(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        infos = [(i.filename, i.compress_type) for i in z.infolist()]
        return infos, {n: z.read(n) for n in z.namelist()}
def reds(header):
    return {c.get('id') for c in E.fromstring(header).iter(H+'charPr') if c.get('textColor', '').upper() == '#FF0000'}
def marker_colors(root, red):
    out = []
    for p in root.iter(P+'p'):
        colors = []
        for r in p.findall(P+'run'):
            colors += [r.get('charPrIDRef') in red] * len(''.join(''.join(t.itertext()) for t in r.findall(P+'t')))
        v = own(p)
        out += [(m.group(), all(colors[m.start():m.end()])) for m in MARK.finditer(v)]
    return out
def main():
    spec = json.loads((Q/'spec.json').read_text(encoding='utf-8')); rep = {}
    rep['base_sha_unchanged'] = hashlib.sha256((Q/'base.hwpx').read_bytes()).hexdigest() == spec['base_sha256']
    bi, bd = load(Q/'base.hwpx'); ci, cd = load(Q/'candidate.hwpx')
    rep['zip_entries_same_order_and_compression'] = bi == ci
    changed = [n for n in bd if bd[n] != cd[n]]; rep['changed_entries'] = changed
    sec = 'Contents/section2.xml'
    b = list(E.fromstring(bd[sec]).iter(P+'p')); c = list(E.fromstring(cd[sec]).iter(P+'p'))
    rep['para_count'] = [len(b), len(c)]
    ins = {}
    for op in spec['insert']: ins.setdefault(op['anchor_idx'], []).append(op)
    rpl = {op['idx']: op for op in spec['replace']}
    errs = []; j = 0; changed_paras = 0
    for i, p in enumerate(b):
        q = c[j]
        if i in rpl:
            if own(q) != rpl[i]['new']: errs.append(('replace text', i))
            if q.find(P+'linesegarray') is not None: errs.append(('cache kept', i))
            if q.get('paraPrIDRef') != p.get('paraPrIDRef'): errs.append(('paraPr', i))
            changed_paras += 1
        elif own(q) != own(p) or q.get('paraPrIDRef') != p.get('paraPrIDRef'):
            errs.append(('unexpected change', i, own(p)[:40]))
        # a replaced table-less body paragraph cannot contain nested paragraphs, so j tracks 1:1
        j += 1
        for op in sorted(ins.get(i, []), key=lambda o: o['order']):
            q = c[j]
            if own(q) != op['text']: errs.append(('insert text', i, op['order']))
            if q.get('paraPrIDRef') != p.get('paraPrIDRef'): errs.append(('insert paraPr', i))
            if q.find(P+'linesegarray') is not None: errs.append(('insert cache', i))
            j += 1
    rep['walk_complete'] = j == len(c)
    rep['changed_paragraphs'] = changed_paras; rep['inserted_paragraphs'] = sum(len(v) for v in ins.values())
    rep['errors'] = errs
    bm = marker_colors(E.fromstring(bd[sec]), reds(bd['Contents/header.xml']))
    cm = marker_colors(E.fromstring(cd[sec]), reds(cd['Contents/header.xml']))
    rep['markers'] = [len(bm), len(cm)]; rep['markers_not_red'] = [m for m, ok in cm if not ok]
    rep['marker_multiset_equal'] = sorted(m for m, _ in bm) == sorted(m for m, _ in cm)
    rep['runs_t'] = [(len(list(E.fromstring(x[sec]).iter(P+'run'))), len(list(E.fromstring(x[sec]).iter(P+'t')))) for x in (bd, cd)]
    ok = (rep['base_sha_unchanged'] and rep['zip_entries_same_order_and_compression'] and not errs and rep['walk_complete']
          and changed_paras == len(rpl) and rep['para_count'][1] == rep['para_count'][0] + rep['inserted_paragraphs']
          and not rep['markers_not_red'] and rep['marker_multiset_equal'])
    rep['ok'] = ok
    (Q/'check_candidate.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(rep, ensure_ascii=False)[:1500]); sys.exit(0 if ok else 1)
if __name__ == '__main__': main()
