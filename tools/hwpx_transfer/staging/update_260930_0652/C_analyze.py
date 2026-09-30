"""old MD / new MD / base HWPX 표 3자 대조 진단 출력 (읽기 전용)."""
import sys
from C_common import *

# new MD 표 (장 접두사, new group 순번) -> (old group 순번, base table_idx)
MAP = {
    '02': [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 5, 5), (5, None, None), (6, 4, 4)],
    '03': [(i, i, 6 + i) for i in range(8)],
    '04': [(i, i, 14 + i) for i in range(10)],
    '05': [(i, i, 24 + i) for i in range(16)],
}


def dump(prefix, nj, oj, ti):
    k = key(prefix)
    b = new[k][nj]
    a = old[key(prefix)][oj] if oj is not None else None
    t = tables[ti] if ti is not None else None
    print(f'\n=== {k[:8]} new#{nj} {b["caption"][:50]} | old#{oj} base t{ti}')
    if t is None:
        return
    if a and a['caption'] != b['caption']:
        print('  CAPTION old:', a['caption'], '\n          new:', b['caption'], '\n          base:', caption_text(t))
    cm = cellmap(t)
    bm, am = b['matrix'], a['matrix']
    print('  shape old', len(am), 'x', len(am[0]), ' new', len(bm), 'x', len(bm[0]), ' base', t['rows'] - offset(t), 'x', t['cols'])
    for ri in range(max(len(am), len(bm))):
        for ci in range(max(len(bm[0]), len(am[0]))):
            v = am[ri][ci] if ri < len(am) and ci < len(am[ri]) else None
            w = bm[ri][ci] if ri < len(bm) and ci < len(bm[ri]) else None
            c = cm.get((ri, ci))
            x = ctext(c) if c else None
            if v != w or (x is not None and v is not None and norm(x) != norm(v)):
                tag = []
                if v != w: tag.append('MD')
                if x is not None and v is not None and norm(x) != norm(v): tag.append('BASE!=OLD')
                print(f'  [{ri},{ci}] {"/".join(tag)}\n     old={v!r}\n     new={w!r}\n    base={x!r}')


if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for p, lst in MAP.items():
        if only and p != only:
            continue
        for nj, (oj, ti) in enumerate([(o, t) for _, o, t in lst]):
            dump(p, lst[nj][0], oj, ti)
