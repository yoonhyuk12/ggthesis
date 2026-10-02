"""Read-only prep: base paragraph/table dump + current MD blocks (no writes outside this folder)."""
from pathlib import Path
import sys, json, importlib.util
Q = Path(__file__).resolve().parent
sys.path.insert(0, str(Q.parent/'review_260913_0239'))
import surgical_ops as S
P = S.P

ed = S.Surgical(Q/'base.hwpx')
paras, tables = [], []
for sec, ps in ed.paras.items():
    root = ed.roots[sec]
    tbls = ed.tables[sec]
    tpos = {id(t): i for i, t in enumerate(tbls)}
    for idx, p in enumerate(ps):
        tbl = next(p.iterancestors(P+'tbl'), None)
        runs = [[r.get('charPrIDRef'), S.own_run(r)] for r in p.findall(P+'run')]
        red = [c for c, _ in runs if ed.chars[c].get('textColor', '').upper() == '#FF0000']
        paras.append(dict(section=sec, idx=idx, text=S.own(p),
                          table_idx=tpos[id(tbl)] if tbl is not None else None,
                          top_level=p.getparent() is root,
                          has_table=bool(list(p.iter(P+'tbl'))),
                          has_pic=bool(list(p.iter(P+'pic'))),
                          runs=runs, red_runs=len(red)))
    pidx = {id(p): i for i, p in enumerate(ps)}
    for ti, t in enumerate(tbls):
        anchor = next(a for a in t.iterancestors(P+'p'))
        rows = []
        for tr in t.findall(P+'tr'):
            row = []
            for tc in tr.findall(P+'tc'):
                ca = tc.find(P+'cellAddr'); sp = tc.find(P+'cellSpan')
                cps = [p for p in tc.iter(P+'p') if next(p.iterancestors(P+'tbl')) is t]
                row.append(dict(row=int(ca.get('rowAddr')), col=int(ca.get('colAddr')),
                                colSpan=int(sp.get('colSpan')), rowSpan=int(sp.get('rowSpan')),
                                para_idx=[pidx[id(p)] for p in cps],
                                text='\n'.join(S.own(p) for p in cps)))
            rows.append(row)
        tables.append(dict(section=sec, table_idx=ti, anchor_idx=pidx[id(anchor)], rows=rows))
(Q/'base_paras.json').write_text(json.dumps(paras, ensure_ascii=False, indent=1), encoding='utf-8')
(Q/'base_tables.json').write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding='utf-8')
with open(Q/'base_paras.txt', 'w', encoding='utf-8') as f:
    for d in paras:
        if d['text'].strip():
            f.write('%s|%d|%s|%s\n' % (d['section'][-5], d['idx'], 'T%s' % d['table_idx'] if d['table_idx'] is not None else '-', d['text']))

# current MD blocks, same shape as old_blocks.json ({md filename: blocks})
spec = importlib.util.spec_from_file_location('m2b', Q.parents[1]/'md_to_blocks.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cur = {}
for src, _ in m.FILES:
    cur[src] = m.parse_file(src)[1]
(Q/'new_blocks.json').write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding='utf-8')
print('paras', len(paras), 'tables', len(tables), {k: len(v) for k, v in cur.items()})
