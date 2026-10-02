"""Coordinator-only: apply spec.json to base.hwpx as byte-span fragment edits -> candidate.hwpx.
Adapted from update_260930_0652/apply_update.py (no table rebuilds, no TOC regeneration)."""
from pathlib import Path
import sys, json, re
from lxml import etree as E
Q = Path(__file__).resolve().parent
sys.path.insert(0, str(Q.parent/'intro_260912'))
from apply_intro import elements, raw_zip_patch
sys.path.insert(0, str(Q.parent/'review_260913_0239'))
import surgical_ops as S
S.MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
P = S.P
def serial(n): return E.tostring(n, encoding='UTF-8', with_tail=False)

def main():
    spec = json.loads((Q/'spec.json').read_text(encoding='utf-8'))
    ed = S.Surgical(Q/'base.hwpx'); ops = {}; queues = {}; logs = []
    def replace(sec, idx, data, kind):
        key = (sec, idx); assert key not in ops, (key, kind, 'duplicate')
        ops[key] = data; logs.append(dict(section=sec, idx=idx, kind=kind))
    for kind in ('replace', 'cell_replace'):
        for op in spec.get(kind, []):
            sec, idx = op['section'], op['idx']
            assert S.own(ed.paras[sec][idx]) == op['old'], (kind, sec, idx)
            replace(sec, idx, ed.edit_paragraph(sec, idx, op['new']), kind)
            if kind == 'cell_replace':
                for anc in ed.paras[sec][idx].iterancestors(P+'p'):
                    for c in anc.findall(P+'linesegarray'): c.set('data-invalidate', '1')
    for op in spec.get('delete', []):
        sec, idx = op['section'], op['idx']
        assert S.own(ed.paras[sec][idx]) == op['old'], ('delete', idx)
        S._plain(ed.paras[sec][idx]); replace(sec, idx, b'', 'delete')
    for op in spec.get('insert', []):
        queues.setdefault((op['section'], op['anchor_idx'], op['position']), []).append(
            (op['order'], ed.edit_paragraph(op['section'], op['template_idx'], op['text'], new=True)))
        logs.append(dict(section=op['section'], idx=op['anchor_idx'], kind='insert'))
    changed = {}
    for sec, ps in ed.paras.items():
        raw = ed.data[sec]; nodes = [n for n in elements(raw) if n['name'] == 'hp:p']; spans = []
        assert len(nodes) == len(ps)
        for idx, p in enumerate(ps):
            if (sec, idx) in ops: continue
            if any(n.get('data-invalidate') == '1' for n in p.findall(P+'linesegarray')):
                caches = [n for n in elements(raw[nodes[idx]['start']:nodes[idx]['end']]) if n['name'] == 'hp:linesegarray']
                if caches:
                    n = caches[-1]; spans.append((nodes[idx]['start']+n['start'], nodes[idx]['start']+n['end'], b''))
        for (s, idx), v in ops.items():
            if s == sec: spans.append((nodes[idx]['start'], nodes[idx]['end'], v))
        for (s, idx, pos), items in queues.items():
            if s == sec:
                off = nodes[idx]['start' if pos == 'before' else 'end']
                spans.append((off, off, b''.join(v for _, v in sorted(items, key=lambda x: x[0]))))
        # cell edits nest inside anchor paragraphs; drop anchor-cache spans that overlap a replaced cell
        spans.sort(key=lambda x: (x[0], x[1])); cursor = 0; chunks = []
        for a, b, v in spans:
            assert a >= cursor, ('overlap', sec, a, b, cursor)
            chunks.extend([raw[cursor:a], v]); cursor = b
        if spans:
            chunks.append(raw[cursor:]); changed[sec] = b''.join(chunks); E.fromstring(changed[sec])
    # TOC titles: change only the text before the dot-leader tab; keep tab + folio, drop that paragraph's cache
    for op in spec.get('toc_title', []):
        sec = op['section']; raw = changed.get(sec, ed.data[sec])
        nodes = [n for n in elements(raw) if n['name'] == 'hp:p']; n = nodes[op['idx']]
        part = raw[n['start']:n['end']]; a = ('<hp:t>'+op['old']+'<hp:tab').encode()
        assert part.count(a) == 1, ('toc', op['idx'])
        part = part.replace(a, ('<hp:t>'+op['new']+'<hp:tab').encode())
        part = re.sub(rb'<hp:linesegarray[ >].*?</hp:linesegarray>', b'', part, flags=re.S)
        changed[sec] = raw[:n['start']]+part+raw[n['end']:]; logs.append(dict(section=sec, idx=op['idx'], kind='toc_title'))
    # existing markers anywhere must stay red
    fixes_log = []
    for sec in ed.paras:
        raw = changed.get(sec, ed.data[sec]); root = E.fromstring(raw); ps = list(root.iter(P+'p'))
        nodes = [n for n in elements(raw) if n['name'] == 'hp:p']; fixes = []
        for idx, p in enumerate(ps):
            value = S.own(p); colors = []
            for r in p.findall(P+'run'):
                colors.extend([ed.chars[r.get('charPrIDRef')].get('textColor', '').upper()]*len(S.own_run(r)))
            if any(any(c != '#FF0000' for c in colors[m.start():m.end()]) for m in S.MARK.finditer(value)):
                S._plain(p)
                fixes.append((nodes[idx]['start'], nodes[idx]['end'], serial(ed._edit(p, value)))); fixes_log.append((sec, idx))
        for a, b, v in reversed(fixes): raw = raw[:a]+v+raw[b:]
        if fixes: changed[sec] = raw
    hb = ed.header_bytes(); body = lambda x: x[x.index(b'?>')+2:].lstrip()
    if body(hb) != body(ed.data['Contents/header.xml']): changed['Contents/header.xml'] = hb
    result = raw_zip_patch((Q/'base.hwpx').read_bytes(), changed)
    (Q/'candidate.hwpx').write_bytes(result)
    (Q/'patch_log.json').write_text(json.dumps(dict(operations=logs, marker_fixes=fixes_log, changed_entries=list(changed)), ensure_ascii=False, indent=1), encoding='utf-8')
    print('candidate', len(result), 'ops', len(logs), 'marker_fixes', len(fixes_log))

if __name__ == '__main__': main()
