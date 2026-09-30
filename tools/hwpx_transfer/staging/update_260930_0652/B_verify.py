# prose_B.json 1회 검증 — old 일치·소유 범위·유일 위치·삽입 앵커/템플릿·적용 후 MD 대조·순서·마커 수
import json, re, collections
from B_util import S2, BY, NB, OB, btext, norm, sim, dp_align, hw_items2, blocks

SPEC = json.load(open('prose_B.json', encoding='utf-8'))
SEC = 'Contents/section2.xml'
LO, HI = 738, 2654          # 제4장 제목 ~ 부록 끝(Abstract 앞)
MARK = re.compile(r'\[(DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)|실험전')
errors, notes = [], []


def is_anchor(p):
    return 'tbl' in p['controls'] and 'cellAddr' in p['controls']


# 1) old 일치·소유 범위·중복 조작
touched = collections.Counter()
for kind in ('replace', 'delete'):
    for op in SPEC[kind]:
        p = BY.get(op['idx'])
        if op['section'] != SEC or p is None: errors.append((kind, op['idx'], 'section/idx 없음')); continue
        if p['text'] != op['old']: errors.append((kind, op['idx'], 'old 불일치'))
        if not p['top_level'] or is_anchor(p): errors.append((kind, op['idx'], '최상위 아님 또는 표 앵커(C 소유)'))
        if 'pic' in p['controls']: errors.append((kind, op['idx'], '그림 문단'))
        if not (LO <= op['idx'] < HI): errors.append((kind, op['idx'], '소유 범위 밖'))
        touched[op['idx']] += 1
dup = [i for i, c in touched.items() if c > 1]
if dup: errors.append(('dup-op', dup))
# 유일 위치: 같은 old 문자열이 section2에 여러 번 있는 경우 목록(비어있지 않은 것만)
alltext = collections.Counter(p['text'] for p in S2)
multi = [(op['idx'], alltext[op['old']]) for op in SPEC['replace'] if alltext[op['old']] > 1]
# 2) 삽입 앵커·템플릿
deleted = {op['idx'] for op in SPEC['delete']}
for op in SPEC['insert']:
    a, t = BY.get(op['anchor_idx']), BY.get(op['template_idx'])
    if a is None or not a['top_level'] or is_anchor(a): errors.append(('insert', op['anchor_idx'], '앵커 부적합'))
    if op['anchor_idx'] in deleted: errors.append(('insert', op['anchor_idx'], '삭제되는 앵커'))
    if op['position'] not in ('before', 'after'): errors.append(('insert', op, 'position'))
    if t is None or not t['top_level'] or is_anchor(t) or len({r[0] for r in t['runs']}) != 1 or MARK.search(t['text']):
        errors.append(('insert', op['template_idx'], '템플릿이 단순 문단 아님'))
    if not (LO <= op['anchor_idx'] < HI): errors.append(('insert', op['anchor_idx'], '범위 밖'))
keys = collections.Counter((o['anchor_idx'], o['position'], o['order']) for o in SPEC['insert'])
if any(c > 1 for c in keys.values()): errors.append(('insert', 'order 중복'))

# 3) 적용 시뮬레이션 → 최종 최상위 문단열
R = {op['idx']: op['new'] for op in SPEC['replace']}
before, after = collections.defaultdict(list), collections.defaultdict(list)
for op in SPEC['insert']:
    (before if op['position'] == 'before' else after)[op['anchor_idx']].append(op)
seq = []   # (kind, src, text)
for p in S2:
    i = p['idx']
    for op in sorted(before[i], key=lambda o: o['order']): seq.append(('P', f'ins<{i}#{op["order"]}', op['text']))
    if i not in deleted:
        if p['top_level']:
            seq.append(('P', i, R.get(i, p['text'])))
        elif re.match(r'\s*<(표|그림)\s*\d', p['text']):
            seq.append(('CAP_IN_TABLE', i, p['text']))
    for op in sorted(after[i], key=lambda o: o['order']): seq.append(('P', f'ins>{i}#{op["order"]}', op['text']))


def span(lo, hi):
    out, on = [], False
    for k, s, t in seq:
        if s == lo: on = True
        if s == hi: break
        if on and norm(t): out.append((k, s, t))
    return out


CH = {'04_연구설계.md': (738, 1135), '05_실증분석결과.md': (1135, 2108), '06_결론.md': (2108, 2172)}
for key, (lo, hi) in CH.items():
    hw = span(lo, hi)
    bl = blocks(NB, key)
    pr = dp_align(hw, bl)
    # 원본 HWPX vs 구 MD에서 이미 어긋나던 블록(기존 편집·배치 차이)
    pre = dp_align(hw_items2(lo, hi), blocks(OB, key))
    pre_bad = {btext(OB[key][i]) for i in range(len(OB[key])) if OB[key][i]['type'] != 'table' and (i not in pre or pre[i][1] < 1)}
    bad = [(i, bl[i][0], pr.get(i)) for i in range(len(bl)) if bl[i][0] != 'table' and (i not in pr or norm(bl[i][2]) != norm([x for x in hw if x[1] == pr[i][0]][0][2]))]
    real = [b for b in bad if bl[b[0]][2] not in pre_bad]
    # 순서: 매칭 위치 단조 증가
    pos = {x[1]: n for n, x in enumerate(hw)}
    order = [pos[pr[i][0]] for i in sorted(pr)]
    mono = all(a < b for a, b in zip(order, order[1:]))
    used = {v[0] for v in pr.values()}
    extra = [x for x in hw if x[1] not in used]
    # 마커 수: 새 블록(비표) vs 결과 최상위 문단
    mb = sum(len(MARK.findall(b[2])) for b in bl if b[0] != 'table')
    mh = sum(len(MARK.findall(x[2])) for x in hw if x[0] == 'P')
    notes.append(f'{key}: 새 비표 블록 {sum(1 for b in bl if b[0]!="table")}개, 불일치 {len(bad)}(기존 편집 {len(bad)-len(real)}, 신규 {len(real)}), '
                 f'순서 단조={mono}, MD에 없는 결과 문단 {[(x[1], x[2][:20]) for x in extra]}, 마커 MD {mb} / 결과 {mh}')
    for b in real: errors.append(('coverage', key, b))
    if not mono: errors.append(('order', key))

# 부록1 Part B 안내 2곳
for i in (2270, 2541):
    if norm(R.get(i, '')) != norm(btext(NB['부록1_설문지_양식.md'][49])): errors.append(('appendix', i))

# 참고문헌 최종 구간
refs = span(2172, 2225)
notes.append('참고문헌 최종: ' + ' | '.join(re.sub(r'^\[\d\d\]\s*', '', t)[:12] for _, _, t in refs))
for name in ('류수영', 'Chong, H.-Y.', 'Zhou, Z.-C.', '김민기·박성호'):
    c = sum(1 for _, _, t in refs if t.startswith(name))
    if c != 1: errors.append(('ref', name, c))
    if any(re.search(r'\(ref |서지관리|관리번호', t) for _, _, t in refs if t.startswith(name)): errors.append(('ref-internal', name))

# 제6장 결과 구조
ch6 = span(2108, 2172)
notes.append(f'제6장 결과: {[t[:14] for _, _, t in ch6]}')
print('ERRORS', len(errors))
for e in errors: print('  ', e)
print('동일 old 문자열 복수 위치(idx로 구분):', multi)
for n in notes: print('-', n)
