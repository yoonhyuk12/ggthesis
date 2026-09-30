import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = json.load(open('base_paras.json', encoding='utf-8'))
S2 = [p for p in P if p['section'] == 'Contents/section2.xml']
BY = {p['idx']: p for p in S2}
NB = json.load(open('new_blocks.json', encoding='utf-8'))
OB = json.load(open('old_blocks.json', encoding='utf-8'))
def btext(b):
    if 'runs' in b: return ''.join(r['text'] for r in b['runs'])
    return b.get('text', '')
import re, difflib
def norm(s):
    return re.sub(r'\s+', '', s or '')
CH = {'04': ('04_연구설계.md', 738, 1135), '05': ('05_실증분석결과.md', 1135, 2108),
      '06': ('06_결론.md', 2108, 2172), '부록1': ('부록1_설문지_양식.md', 2225, 2654)}
def hw_items(lo, hi, include_tables=False):
    out = []
    for p in S2:
        if lo <= p['idx'] < hi:
            if p['top_level']:
                if 'tbl' in p['controls'] and 'cellAddr' in p['controls']:
                    out.append(('TABLE', p['idx'], p['text']))
                elif norm(p['text']):
                    out.append(('P', p['idx'], p['text']))
            elif include_tables and norm(p['text']):
                out.append(('CELL', p['idx'], p['text']))
    return out
def blocks(B, key):
    out = []
    for i, b in enumerate(B[key]):
        out.append((b['type'], i, '[TABLE]' if b['type'] == 'table' else btext(b)))
    return out
def align(hw, bl):
    """greedy-ordered fuzzy alignment: returns list of (block_i, hw_idx, ratio)"""
    res = []
    j0 = 0
    for bt, bi, btx in bl:
        if bt == 'table':
            # next TABLE in hw
            for j in range(j0, len(hw)):
                if hw[j][0] == 'TABLE':
                    res.append((bi, hw[j][1], 1.0, j)); j0 = j + 1; break
            else:
                res.append((bi, None, 0, None))
            continue
        best = (0, None)
        for j in range(j0, min(len(hw), j0 + 25)):
            if hw[j][0] == 'TABLE': continue
            r = difflib.SequenceMatcher(None, norm(btx), norm(hw[j][2]), autojunk=False).ratio()
            if r > best[0]: best = (r, j)
        if best[0] >= 0.55:
            j = best[1]; res.append((bi, hw[j][1], best[0], j)); j0 = j + 1
        else:
            res.append((bi, None, best[0], None))
    return res
def hw_items2(lo, hi):
    out = []
    for p in S2:
        if lo <= p['idx'] < hi and norm(p['text']):
            if p['top_level']:
                out.append(('P', p['idx'], p['text']))
            elif re.match(r'\s*<(표|그림)\s*\d', p['text']):
                out.append(('CAP_IN_TABLE', p['idx'], p['text']))
    return out
def sim(a, b):
    a, b = norm(a), norm(b)
    if a == b: return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
def dp_align(hw, bl, thr=0.5):
    bl = [b for b in bl if b[0] != 'table']
    n, m = len(bl), len(hw)
    S = [[0.0]*(m+1) for _ in range(n+1)]
    B = [[None]*(m+1) for _ in range(n+1)]
    simc = {}
    for i in range(1, n+1):
        for j in range(1, m+1):
            best = (S[i-1][j], 'u'); 
            if S[i][j-1] > best[0]: best = (S[i][j-1], 'l')
            # quick length filter
            la, lb = len(norm(bl[i-1][2])), len(norm(hw[j-1][2]))
            if la and lb and min(la, lb) / max(la, lb) > 0.3:
                s = sim(bl[i-1][2], hw[j-1][2])
                if s >= thr and S[i-1][j-1] + s > best[0]:
                    best = (S[i-1][j-1] + s, 'd'); simc[(i, j)] = s
            S[i][j], B[i][j] = best
    i, j = n, m; pairs = {}
    while i > 0 and j > 0:
        if B[i][j] == 'd': pairs[bl[i-1][1]] = (hw[j-1][1], simc[(i, j)]); i -= 1; j -= 1
        elif B[i][j] == 'u': i -= 1
        else: j -= 1
    return pairs  # block index -> (hw idx, sim)
