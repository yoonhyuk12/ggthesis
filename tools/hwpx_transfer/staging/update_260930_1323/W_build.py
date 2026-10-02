# spec.json 생성기 — 읽기 전용 분석. 입력은 작업 폴더의 덤프·블록 JSON과 01.docs(읽기)뿐이다.
from W_common import *
REPO = P.parents[3]
S1 = 'Contents/section1.xml'
spec = {k: [] for k in ('replace', 'cell_replace', 'insert', 'delete', 'table_struct', 'user_edits', 'not_applied')}
cov = []
FILES = list(O)
RANGE = {'01_서론.md': (0, 36), '02_이론적배경.md': (36, 411), '03_시스템개발.md': (411, 782), '04_연구설계.md': (782, 1190),
         '05_실증분석결과.md': (1190, 2167), '06_결론.md': (2167, 2178), '부록1_설문지_양식.md': (2235, 2665)}
sec2 = [b for b in B if b['section'] == S2]
def find(f, text, cell=None):
    lo, hi = RANGE[f]; t = norm(text)
    return [b['idx'] for b in sec2 if lo <= b['idx'] < hi and norm(b['text']) == t and (cell is None or (b['table_idx'] is not None) == cell)]
used = {}
def add_rep(key, sec, idx, old, new, md, extra=None):
    k = (sec, idx)
    if k in used:
        prev = used[k]
        if prev['new'] != new: raise SystemExit(('conflict', k, md, prev['md']))
        prev['md'] += ' | ' + md; return
    d = {'section': sec, 'idx': idx, 'old': old, 'new': new, 'md': md}
    if extra: d.update(extra)
    spec[key].append(d); used[k] = d
MDMARK = {}   # (sec, idx) -> 기대 마커 수(MD 새 블록 기준)

# ── 1. 본문 문단 ────────────────────────────────────────────────────
for f in FILES:
    for i, (ob, nb) in enumerate(zip(O[f], N[f])):
        if ob == nb or ob['type'] == 'table': continue
        o, n = btext(ob), btext(nb)
        tag = '%s:#%d %s' % (f, i, n[:30])
        if f == '03_시스템개발.md' and o.startswith('[^r5-bosch]:'):
            # 각주를 HWPX가 R5 문단 끝 괄호로 편입(사용자 형식) → 괄호 안 본문만 교체
            ob_ = o.split(': ', 1)[1].replace('*', '').rstrip('.'); nb_ = n.split(': ', 1)[1].replace('*', '').rstrip('.')
            hits = [b['idx'] for b in sec2 if ob_ in b['text']]
            assert len(hits) == 1, hits
            hw = base[(S2, hits[0])]['text']
            add_rep('replace', S2, hits[0], hw, hw.replace(ob_, nb_), tag)
            MDMARK[(S2, hits[0])] = nmark(btext(N[f][i - 1])) + nmark(n)
            spec['user_edits'].append({'section': S2, 'idx': hits[0], 'hwpx': hw, 'old_md': o, 'new_md': n,
                '판단': 'MD 각주 [^r5-bosch]를 HWPX가 R5 문단(블록 10) 끝 괄호로 편입한 사용자 형식. 형식은 유지하고 괄호 안 각주 본문만 새 MD로 교체(replace에 반영).'})
            cov.append((f, i, 'replace(각주→본문 괄호, user_edit 병합)')); continue
        hits = find(f, o)
        if f == '부록1_설문지_양식.md' and len(hits) == 2 and i in (7, 8, 9, 21, 22, 23):
            hits = [hits[0]] if i < 15 else [hits[1]]       # 양식 1(도입) / 양식 2(미도입) 순서
        if not hits:
            if find(f, n): cov.append((f, i, 'already_applied_in_hwpx')); continue
            raise SystemExit(('unmapped', f, i, o[:60]))
        for h in hits:
            hw = base[(S2, h)]['text']
            new = merge3(o, n, hw)
            if new is None: raise SystemExit(('merge fail', f, i, h))
            if hw.strip() != o.strip():
                spec['user_edits'].append({'section': S2, 'idx': h, 'hwpx': hw, 'old_md': o, 'new_md': n,
                    '판단': 'HWPX 문구가 옛 MD와 글자 단위로 다름 → HWPX 쪽 차이는 두고 MD 변경분만 3방향 병합(replace에 반영)'})
            tix = base[(S2, h)]['table_idx']
            if tix is None: add_rep('replace', S2, h, hw, new, tag)
            else: add_rep('cell_replace', S2, h, hw, new, tag + ' [표 틀 안 본문]', {'table_idx': tix})
            MDMARK[(S2, h)] = nmark(n)
        cov.append((f, i, 'replace x%d %s' % (len(hits), hits)))
        if ob['type'] in ('h1', 'h2', 'h3'):      # 목차(section1) 제목 동기화
            for h in [b['idx'] for b in B if b['section'] == S1 and norm(b['text']) == norm(o)]:
                hw = base[(S1, h)]['text']
                add_rep('replace', S1, h, hw, lead(hw) + n + trail(hw), tag + ' [목차 제목]')
                MDMARK[(S1, h)] = nmark(n)

# ── 2. 표 셀 ─────────────────────────────────────────────────────────
for f in FILES:
    for i, (ob, nb) in enumerate(zip(O[f], N[f])):
        if ob == nb or ob['type'] != 'table': continue
        if len(ob['rows']) != len(nb['rows']) or len(ob['header']) != len(nb['header']):
            spec['table_struct'].append({'table_idx': None, '설명': '행/열 수 변경', 'md_table': '%s:#%d' % (f, i)}); continue
        n_cells = 0; tids = set()
        for r, (xo, xn) in enumerate(zip([ob['header']] + ob['rows'], [nb['header']] + nb['rows'])):
            for c, (u, v) in enumerate(zip(xo, xn)):
                if u == v: continue
                u, v = ctext(u), ctext(v)
                assert '\n' not in u and '\n' not in v
                hits = find(f, u, cell=True)
                if not hits:
                    if find(f, v, cell=True): continue
                    raise SystemExit(('cell unmapped', f, i, r, c, u))
                for h in hits:
                    b = base[(S2, h)]; hw = b['text']
                    new = merge3(u, v, hw)
                    if new is None: raise SystemExit(('cell merge fail', h))
                    add_rep('cell_replace', S2, h, hw, new, '%s:#%d r%dc%d' % (f, i, r, c), {'table_idx': b['table_idx']})
                    MDMARK[(S2, h)] = nmark(v); tids.add(b['table_idx'])
                n_cells += 1
        cov.append((f, i, 'cell_replace %d cells, HWPX 표 %s' % (n_cells, sorted(tids))))

# ── 3. 참고문헌 ──────────────────────────────────────────────────────
def md_refs(path):
    t = pathlib.Path(path).read_text(encoding='utf-8')
    t = t[t.index('## 참고문헌 표기 골격'):]
    out = []
    for blk in re.findall(r'```\n(.*?)```', t, re.S):
        for ln in blk.splitlines():
            ln = ln.strip()
            if not ln or ln.startswith('[') or ln.startswith('…'): continue
            out.append(ln)
    tail = t[t.index('### 5.'):]
    out += [ln.strip() for ln in tail.splitlines() if re.match(r'^(김정아|손형주)\(', ln.strip())]
    return out
NOTE = re.compile(r'\s*\((?:ref |대표 ref|존재 검증|서울연|번호가|ref 30 통계|제\d장 내주|\d장 )[^()]*(?:\([^()]*\)[^()]*)*\)\s*$')
def strip_note(s):
    prev = None
    while prev != s:
        prev = s; s = NOTE.sub('', s).strip()
    return re.sub(r'\s+—\s+0\d장 .*$', '', s)
def title_key(s):
    m = re.search(r'[「『"“](.+?)[」』"”]', s)
    return norm(m.group(1)).replace('–', '-').replace('—', '-')[:25] if m else norm(re.split(r'[,(]', s)[0])
newR = [strip_note(x) for x in md_refs(REPO / '01.docs/07_참조번호목록.md')]
oldR = [strip_note(x) for x in md_refs(P / 'old_md/07_참조번호목록.md')]
nk = {title_key(x): x for x in newR}; ok = {title_key(x): x for x in oldR}
ref_hw = [b for b in sec2 if 2178 < b['idx'] < 2235 and b['text'].strip() and not re.match(r'^[가-마]\. ', b['text'])]
ref_log = []; matched = set()
for b in ref_hw:
    hw = b['text']; m = re.match(r'^(\[\d\d\] )?(.*)$', hw); pre, core = m.group(1) or '', m.group(2)
    k = title_key(core)
    if k not in nk:
        ref_log.append(('HWPX만 있음', b['idx'], hw[:50])); continue
    matched.add(k)
    nw, od = nk[k], ok.get(k)
    tag = '07_참조번호목록.md:참고문헌 ' + core[:24]
    if norm(core) == norm(nw): ref_log.append(('동일', b['idx'])); continue
    if od is not None and norm(core) == norm(od):
        add_rep('replace', S2, b['idx'], hw, pre + nw + trail(hw), tag); MDMARK[(S2, b['idx'])] = nmark(nw)
        ref_log.append(('치환', b['idx'])); continue
    if od is not None and od != nw:
        mg = merge3(od, nw, core)
        if mg is None: raise SystemExit(('ref merge fail', b['idx']))
        add_rep('replace', S2, b['idx'], hw, pre + mg, tag); MDMARK[(S2, b['idx'])] = nmark(nw)
        spec['user_edits'].append({'section': S2, 'idx': b['idx'], 'hwpx': hw, 'old_md': od, 'new_md': nw,
            '판단': 'HWPX 서지가 옛 MD와 달랐음(HWPX 쪽 조정) → 조정은 유지하고 MD 변경분만 병합(replace에 반영)'})
        ref_log.append(('병합', b['idx'])); continue
    spec['user_edits'].append({'section': S2, 'idx': b['idx'], 'hwpx': hw, 'old_md': od, 'new_md': nw,
        '판단': 'MD 서지는 이번에 바뀌지 않았고 HWPX가 옛 MD와 다른 기존 차이(0808본 이전부터) → 보존, 치환하지 않음'})
    ref_log.append(('기존차이 보존', b['idx']))
oauth = {x.split(',')[0] for x in oldR}
missing = [(k not in ok and x.split(',')[0] not in oauth, x) for k, x in nk.items() if k not in matched]

# ── 4. 목차 전수 대조(00_목차 §3 ↔ section1) ────────────────────────
toc = (REPO / '01.docs/00_목차.md').read_text(encoding='utf-8')
toc = toc[toc.index('## 3. 목차'):toc.index('### 참고문헌')]
toc_md = [re.sub(r'^(###|\s*-)\s*', '', l).strip() for l in toc.splitlines() if re.match(r'^(### 제|\s*- 제)', l)]
toc_hw = [(b['idx'], (used.get((S1, b['idx'])) or {}).get('new', b['text']).strip())
          for b in B if b['section'] == S1 and 3 <= b['idx'] <= 73 and b['text'].strip()]
toc_diff = [(a, h) for a, h in zip(toc_md, toc_hw) if norm(a) != norm(h[1])]
# 표·그림 목차: 캡션 블록 변경 여부
cap_changed = [(f, i) for f in O for i, (a, b) in enumerate(zip(O[f], N[f])) if a != b and a['type'] in ('table_caption', 'figure_caption')]

spec['not_applied'] += [
 {'md': '부록2_설문항목_근거매핑.md (25블록)', '사유': '현 HWPX에 부록2가 수록되지 않음 — 추가는 별도 지시 사항(계획서 반영 제외)'},
 {'md': '00_목차.md §2 국문초록(골격)', '사유': 'HWPX에 국문초록 문단이 없음(section0 표지·인준, section1 목차·표/그림 목차, section2 끝 Abstract 자리표시만). 00_목차의 국문초록은 작성 가이드 골격이라 이관 대상 아님'},
]
for is_new, x in missing:
    spec['not_applied'].append({'md': '07_참조번호목록.md 참고문헌: ' + x[:140],
        '사유': ('옛 MD에 없던 신규 서지(이번 변경분)' if is_new else '옛 MD에도 있었으나 0808본 HWPX 참고문헌에 미수록(기존 선별 상태)') + ' — HWPX 참고문헌에 새 항목 삽입은 수록 범위·구분(가~마) 판단이 필요해 메인 결정으로 넘김'})
spec['coverage'] = {'changed_blocks': sum(1 for f in O for a, b in zip(O[f], N[f]) if a != b),
                    'mapped': len(cov), 'detail': ['%s#%d %s' % c for c in cov],
                    'toc_compare': {'md_entries': len(toc_md), 'hwpx_entries': len(toc_hw), 'diff_after_spec': toc_diff,
                                    'caption_blocks_changed': cap_changed},
                    'references': ref_log}
(P / 'spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
(P / '_mdmark.json').write_text(json.dumps([[s, i, v] for (s, i), v in MDMARK.items()]), encoding='utf-8')
print({k: len(v) for k, v in spec.items() if isinstance(v, list)}, spec['coverage']['changed_blocks'], len(cov))
print('TOC', len(toc_md), len(toc_hw), toc_diff, 'captions changed', cap_changed)
for r in ref_log: print(r)
for x in missing: print('MISSING', x[0], x[1][:80])
