"""C 담당 공통 로더: base 표·old/new MD 표 블록 읽기 전용 파싱 (HWPX 직접 읽기 없음)."""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEC = 'Contents/section2.xml'


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def plain(s):
    return html.unescape(re.sub(r'<br\s*/?>', '\n', s)).replace('**', '')


def norm(s):
    return re.sub(r'\s+', '', plain(s))


def btext(b):
    return plain(b.get('text', '') or ''.join(r['text'] for r in b.get('runs', [])))


def groups(bs):
    """연속된 table 블록(패널)을 개별 표로, 직전 캡션과 함께 반환."""
    out = []
    cap = ''
    for i, b in enumerate(bs):
        s = btext(b)
        if b['type'] == 'table_caption':
            cap = s
        if b['type'] == 'table':
            m = [[plain(v) for v in row] for row in [b['header']] + b['rows']
                 if not all(re.fullmatch(r':?-+:?', v.strip()) for v in row)]
            out.append({'caption': cap, 'matrix': m, 'block_idx': i})
            cap = ''
    return out


OLD = read('old_blocks.json')
NEW = read('new_blocks.json')
old = {k: groups(v) for k, v in OLD.items()}
new = {k: groups(v) for k, v in NEW.items()}
paras = {(p['section'], p['idx']): p for p in read('base_paras.json')}
tables = [t for t in read('base_tables.json') if t['section'] == SEC]


def key(prefix):
    return next(k for k in NEW if k.startswith(prefix))


def has_caption_row(t):
    first = [c for c in t['cells'] if c['row'] == 0]
    return len(first) == 1 and any(p['text'].startswith('<표 ') for p in first[0]['paras'])


def offset(t):
    return 1 if has_caption_row(t) else 0


def cellmap(t):
    o = offset(t)
    return {(c['row'] - o, c['col']): c for c in t['cells'] if c['row'] >= o}


def ctext(c):
    return '\n'.join(p['text'] for p in c['paras'])


def caption_text(t):
    return ctext(t['cells'][0]) if has_caption_row(t) else None
