import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def plain(s): return html.unescape(re.sub(r'<br\s*/?>', '\n', s)).replace('**','')
def norm(s): return re.sub(r'\s+', '', plain(s))
def groups(bs):
    out=[]; active=False; cap=''
    for i,b in enumerate(bs):
        s=b.get('text','') or ''.join(r['text'] for r in b.get('runs',[]))
        if re.match(r'^<표 \d+-\d+>',s): cap=s
        if b['type']=='table':
            if not active: out.append({'caption':cap,'matrix':[],'block_idx':i})
            for row in [b['header']]+b['rows']:
                if not all(re.fullmatch(r':?-+:?',v.strip()) for v in row): out[-1]['matrix'].append([plain(v) for v in row])
            active=True
        else: active=False
    return out

old={k:groups(v) for k,v in read('old_blocks.json').items()}
new={k:groups(v) for k,v in read('new_blocks.json').items()}
tables=[t for t in read('base_tables.json') if t['section']=='Contents/section2.xml']
paras={(p['section'],p['idx']):p for p in read('base_paras.json')}
mapping={'02_이론적배경.md':list(range(6)), '03_시스템개발.md':list(range(6,14)), '04_연구설계.md':list(range(14,24)), '05_실증분석결과.md':list(range(24,36))}
def offset(t):
    return 1 if any(c['addr']['rowAddr']=='0' and any(p['text'].startswith('<표 ') for p in c['paras']) for c in t['cells']) else 0
def cellmap(t): return {(int(c['addr']['rowAddr'])-offset(t),int(c['addr']['colAddr'])):c for c in t['cells'] if int(c['addr']['rowAddr'])>=offset(t)}
def ctext(c):return '\n'.join(p['text'] for p in c['paras'])

if __name__=='__main__':
    for k,ids in mapping.items():
        assert len(ids)==len(old[k])
        for j,ti in enumerate(ids):
            t=tables[ti]; cm=cellmap(t); a=old[k][j]
            for ri,row in enumerate(a['matrix']):
                for ci,v in enumerate(row):
                    c=cm.get((ri,ci))
                    if c is None:
                        if v:print('MISSING',k,ti,ri,ci,repr(v))
                    elif norm(ctext(c))!=norm(v):print('BASE_DIFF',ti,ri,ci,repr(v),'=>',repr(ctext(c)))
