# 공통 로더·정규화 (읽기 전용 분석)
import json, pathlib, html, re, difflib
P = pathlib.Path(__file__).parent
rd = lambda f: json.loads((P / f).read_text(encoding='utf-8'))
O, N, B, T = rd('old_blocks.json'), rd('new_blocks.json'), rd('base_paras.json'), rd('base_tables.json')
S2 = 'Contents/section2.xml'
base = {(b['section'], b['idx']): b for b in B}
def btext(b):
    if b['type'] == 'table': return None
    t = b['text'] if 'text' in b else ''.join(r['text'] for r in b['runs'])
    return html.unescape(t).replace('**', '').replace('`', '')
def ctext(c): return html.unescape(c).replace('**', '').replace('`', '').replace('<br>', '\n')
TR = str.maketrans({'․': '·', 'ㆍ': '·', '∙': '·', '∼': '~', '～': '~', '‘': "'", '’': "'", '“': '"', '”': '"'})
def norm(s): return re.sub(r'\s+', '', s).translate(TR)
def lead(s): return s[:len(s) - len(s.lstrip())]
def trail(s): return s[len(s.rstrip()):]
MARK = re.compile(r'\[(DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)|실험전')
def nmark(s): return len(MARK.findall(s or ''))

def merge3(old, new, hw):
    """old→new 변경분을 hw(HWPX 실문구)에 얹는다. 변경 구간이 HWPX 조정과 겹치면 None."""
    if hw.strip() == old.strip():
        return lead(hw) + new.strip() + trail(hw)
    sm1 = difflib.SequenceMatcher(None, old, hw, autojunk=False)
    m = {}
    for a, b, n in sm1.get_matching_blocks():
        for k in range(n): m[a + k] = b + k
    ops = [op for op in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if op[0] != 'equal']
    out = hw; edits = []
    for tag, i1, i2, j1, j2 in ops:
        if i2 > i1:
            if not all(k in m for k in range(i1, i2)): return None
            if m[i2 - 1] - m[i1] != i2 - 1 - i1: return None
            h1, h2 = m[i1], m[i2 - 1] + 1
        else:
            if i1 - 1 in m: h1 = h2 = m[i1 - 1] + 1
            elif i1 in m: h1 = h2 = m[i1]
            else: return None
        edits.append((h1, h2, new[j1:j2]))
    for h1, h2, s in sorted(edits, reverse=True):
        out = out[:h1] + s + out[h2:]
    return out
