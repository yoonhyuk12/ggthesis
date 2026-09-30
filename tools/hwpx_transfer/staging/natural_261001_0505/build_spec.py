"""Read-only: naturalize reports (MD old/new paragraphs) -> spec.json (replace/insert) against base.hwpx dump."""
import json, re, html, difflib, hashlib
from pathlib import Path
Q = Path(__file__).resolve().parent
ROOT = Q.parents[3]
REP = ROOT/'.agents/watermarks-remover/local-reports/naturalize_261001'
TR = str.maketrans({'․': '·', 'ㆍ': '·', '∙': '·', '∼': '~', '～': '~', '‘': "'", '’': "'", '“': '"', '”': '"'})
MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')

def md2txt(s):
    s = html.unescape(s).replace('**', '').replace('`', '')
    s = re.sub(r'\[([^\]]+)\]\((?:https?://|\.)[^)]*\)', r'\1', s)   # [text](url)
    return s.strip()
def norm(s): return re.sub(r'\s+', '', s).translate(TR)
def lead(s): return s[:len(s) - len(s.lstrip())]
def trail(s): return s[len(s.rstrip()):]

def merge3(old, new, hw):
    if norm(hw) == norm(old): return lead(hw) + new + trail(hw)
    sm1 = difflib.SequenceMatcher(None, old, hw, autojunk=False); m = {}
    for a, b, n in sm1.get_matching_blocks():
        for k in range(n): m[a+k] = b+k
    edits = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == 'equal': continue
        if i2 > i1:
            if not all(k in m for k in range(i1, i2)) or m[i2-1]-m[i1] != i2-1-i1: return None
            h1, h2 = m[i1], m[i2-1]+1
        elif i1-1 in m: h1 = h2 = m[i1-1]+1
        elif i1 in m: h1 = h2 = m[i1]
        else: return None
        edits.append((h1, h2, new[j1:j2]))
    out = hw
    for h1, h2, s in sorted(edits, reverse=True): out = out[:h1]+s+out[h2:]
    return out

def locate(text, needle):
    pos = [i for i, c in enumerate(text) if not c.isspace()]
    hay = ''.join(c for c in text if not c.isspace()).translate(TR); key = norm(needle); out = []; at = 0
    while key and (at := hay.find(key, at)) >= 0:
        out.append((pos[at], pos[at+len(key)-1]+1)); at += 1
    return out

def main():
    paras = json.loads((Q/'base_paras.json').read_text(encoding='utf-8'))
    body = [p for p in paras if p['table_idx'] is None and not p['has_table'] and p['text'].strip()]
    spec = dict(base_sha256=hashlib.sha256((Q/'base.hwpx').read_bytes()).hexdigest(),
                replace=[], insert=[], conflicts=[], merged=[], cell_replace=[], delete=[], toc_title=[])
    groups = {}   # (section, idx) -> list of (start, end, parts, ident)
    for w in 'ABCDE':
        rep = json.loads((REP/f'{w}_report.json').read_text(encoding='utf-8'))
        for e in rep['edits']:
            old = md2txt(e['old']); parts = [md2txt(x) for x in re.split(r'\n\s*\n', e['new'].strip())]
            ident = dict(worker=w, path=e['path'], line=e.get('line_before'))
            md = (ROOT/e['path']).read_text(encoding='utf-8-sig')
            if norm(e['new']) not in norm(md):
                spec['conflicts'].append(dict(**ident, reason='MD new text absent (changed after report)')); continue
            hits = [(p, h) for p in body for h in locate(p['text'], old)]
            if len(hits) == 1:
                p, (a, b) = hits[0]
                groups.setdefault((p['section'], p['idx']), []).append((a, b, parts, ident)); continue
            if len(hits) > 1:
                spec['conflicts'].append(dict(**ident, reason=f'old text found {len(hits)} times', old=old)); continue
            cands = sorted(body, key=lambda p: difflib.SequenceMatcher(None, norm(old), norm(p['text']), autojunk=False).ratio(), reverse=True)[:2]
            r0, r1 = (difflib.SequenceMatcher(None, norm(old), norm(c['text']), autojunk=False).ratio() for c in cands)
            p = cands[0]; hw = p['text']
            new_hw = merge3(old, parts[0], hw) if (r0 >= 0.85 and r1 < 0.85 and len(parts) == 1) else None
            if new_hw is None:
                spec['conflicts'].append(dict(**ident, reason=f'not found in hwpx (best={r0:.3f})', old=old, nearest=hw[:400], nearest_idx=p['idx'])); continue
            spec['merged'].append(dict(**ident, idx=p['idx'], ratio=round(r0, 4)))
            groups.setdefault((p['section'], p['idx']), []).append(('merge', new_hw, ident))
    byidx = {(p['section'], p['idx']): p for p in body}
    for key, items in groups.items():
        hw = byidx[key]['text']
        if any(it[0] == 'merge' for it in items):
            assert len(items) == 1, key; new_texts = [items[0][1]]; ids = [items[0][2]]
        else:
            items.sort(key=lambda x: x[0])
            assert all(x[1] <= y[0] for x, y in zip(items, items[1:])), ('overlap', key)
            assert sum(len(x[2]) > 1 for x in items) <= 1, ('multiple splits', key)
            new_texts = []
            cur = hw[:items[0][0]]
            for i, (a, b, parts, ident) in enumerate(items):
                nxt = items[i+1][0] if i+1 < len(items) else len(hw)
                cur += parts[0]
                for extra in parts[1:]:
                    new_texts.append(cur.rstrip()); cur = lead(hw) + extra
                cur += hw[b:nxt]
            new_texts.append(cur); ids = [x[3] for x in items]
        old_marks = MARK.findall(hw); new_marks = MARK.findall(''.join(new_texts))
        assert sorted(old_marks) == sorted(new_marks), ('marker changed', key, old_marks, new_marks)
        spec['replace'].append(dict(section=key[0], idx=key[1], old=hw, new=new_texts[0], sources=ids))
        for k, t in enumerate(new_texts[1:], 1):
            spec['insert'].append(dict(section=key[0], anchor_idx=key[1], position='after', order=k, template_idx=key[1], text=t, sources=ids))
    spec['counts'] = {k: len(v) for k, v in spec.items() if isinstance(v, list)}
    spec['edits_total'] = sum(len(v) for v in groups.values()) + len(spec['conflicts'])
    (Q/'spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(spec['counts'], ensure_ascii=False), 'edits_total', spec['edits_total'])
    for c in spec['conflicts']: print('CONFLICT', c['worker'], c['path'][8:], c['line'], c['reason'], '|', c.get('old','')[:70])
    for m in spec['merged']: print('MERGED', m)

if __name__ == '__main__': main()
