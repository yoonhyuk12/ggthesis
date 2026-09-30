# 제1~3장 본문 최상위 문단 변경 명세(prose_A.json) 생성 + 1회 검증
# 입력: base_paras.json·base_tables.json(실제 HWPX 덤프), old_blocks.json(f5588d2), new_blocks.json(현행 MD)
# 출력: prose_A.json (검증 증거는 표준출력 → report_A.md에 수록; HWPX·MD는 읽기만 한다)
import json, pathlib, html, re, difflib
P = pathlib.Path(__file__).parent
rd = lambda f: json.loads((P / f).read_text(encoding='utf-8'))
O, N, B, T = rd('old_blocks.json'), rd('new_blocks.json'), rd('base_paras.json'), rd('base_tables.json')
SEC = 'Contents/section2.xml'
base = {b['idx']: b for b in B if b['section'] == SEC}
F1, F2, F3 = list(N)[:3]
RANGE = {F1: (0, 43), F2: (43, 398), F3: (398, 738)}

def btext(b):
    if b['type'] == 'table': return None
    t = b['text'] if 'text' in b else ''.join(r['text'] for r in b['runs'])
    return html.unescape(t).replace('**', '').replace('`', '')
def norm(s): return re.sub(r'\s+', '', s).translate(str.maketrans({'․': '·', 'ㆍ': '·', '∙': '·', '∼': '~', '～': '~'}))
def lead(s): return s[:len(s) - len(s.lstrip())]
def trail(s): return s[len(s.rstrip()):]

# ── 계획 ───────────────────────────────────────────────────────────────
# R: (idx, new_block)      본문/제목 텍스트 치환(같은 수준 제목·본문만)
# D: idx                   삭제(빈 줄 포함)
# X: idx                   그림 객체 제거(remove_object, 코디네이터 승인 1a)
# I: (anchor, pos, order, template, new_block|'' )   삽입. ''는 제목 앞뒤 빈 줄
# K: (idx, new_block)      변경 없음(대조 확인용)
# C 표 규약(코디네이터 확정): 1-1 after19 o7, 2-5 after296 o74, 2-6 after301 o81, 2-7 after303 o88, 옛 T320·T367 삭제
TB_BODY = {F1: 19, F2: 49, F3: 522}          # 단순 본문 템플릿(단일 run, paraPr45, 선행 공백)
H3 = {F2: 227, F3: 559}                       # 항 제목 템플릿(단일 run charPr39)
BLK_AFTER, BLK_BEFORE = 401, 405              # 제목 뒤 빈 줄(77) / 제목 앞 빈 줄(78)
SRC, NOTE, SUB = 285, 155, 159                # 자료: / 주: / 가.나.다.(볼드 소제목)

PLAN = {
 F1: dict(
  K=[(0, 0), (2, 1), (25, 10), (34, 14), (42, 19)],
  R=[(6, 2), (13, 3), (14, 4), (19, 5), (27, 11), (29, 12), (30, 13), (36, 15), (38, 16), (39, 17), (41, 18)],
  D=[4, 5, 8, 10, 11, 12, 15, 16, 17, 18, 20, 21, 22, 23, 28, 31, 32, 37],
  X=[7, 9],
  I=[(19, 'after', 8, SRC, 8), (19, 'after', 9, NOTE, 9)]),
 F2: dict(
  K=[(43, 0), (45, 1), (47, 2), (49, 3), (50, 4), (51, 5), (56, 9), (59, 11), (60, 12), (61, 13), (157, 18), (160, 20),
     (163, 23), (164, 24), (166, 26), (167, 27), (168, 28), (187, 32), (188, 33), (189, 34), (225, 38), (227, 39),
     (230, 41), (231, 42), (232, 43), (234, 44), (236, 45), (237, 46), (238, 47), (240, 48), (242, 49), (244, 50),
     (245, 51), (246, 52), (247, 53), (249, 54), (251, 55), (252, 56), (253, 57), (255, 58), (257, 59), (259, 60),
     (260, 61), (285, 65), (288, 67), (290, 68), (291, 69), (292, 70), (294, 71), (304, 90), (310, 94), (391, 95)],
  R=[(52, 6), (53, 7), (54, 8), (58, 10), (62, 14), (155, 17), (159, 19), (161, 21), (162, 22), (165, 25), (186, 31),
     (223, 37), (229, 40), (261, 62), (286, 66), (297, 76), (299, 77), (300, 78), (301, 79), (302, 85), (303, 86),
     (306, 91), (308, 92), (309, 93), (393, 96), (394, 97), (395, 98), (396, 99)],
  D=[311, 312, 313, 314, 315, 316, 317, 318, 319, 366],
  X=[],
  I=[(296, 'after', 72, TB_BODY[F2], 72), (296, 'after', 75, TB_BODY[F2], 75), (296, 'after', 75.5, BLK_BEFORE, ''),
     (301, 'after', 82, NOTE, 82), (301, 'after', 83, TB_BODY[F2], 83), (301, 'after', 83.5, BLK_BEFORE, ''),
     (301, 'after', 84, H3[F2], 84), (301, 'after', 84.5, BLK_AFTER, ''),
     (303, 'after', 89, TB_BODY[F2], 89)]),
 F3: dict(
  K=[(398, 0), (402, 3), (403, 4), (408, 7), (409, 8), (410, 9), (412, 13), (448, 19), (450, 21), (451, 22),
     (484, 27), (485, 28), (494, 34), (495, 35), (497, 37), (498, 38), (502, 40), (504, 41), (508, 43), (511, 46),
     (516, 49), (518, 51), (522, 54), (549, 58), (550, 59), (552, 61), (553, 62), (559, 67), (561, 68), (562, 69),
     (563, 71), (564, 73), (580, 76), (607, 80), (608, 81), (653, 84), (655, 85), (657, 86), (705, 89), (706, 90),
     (708, 92), (710, 93), (711, 94)],
  R=[(400, 1), (404, 5), (444, 16), (446, 17), (480, 25), (486, 29), (490, 32), (509, 44), (512, 47), (517, 50),
     (520, 52), (555, 65), (557, 66), (605, 79), (712, 95), (730, 99), (732, 100), (734, 101), (735, 102), (736, 103)],
  D=[406, 482, 488, 491, 492, 493, 499, 500, 501, 503, 505, 506, 507, 514],
  X=[],
  I=[(401, 'after', 2, H3[F3], 2), (401, 'after', 2.5, BLK_AFTER, ''),
     (405, 'after', 6, H3[F3], 6),
     (411, 'after', 12, TB_BODY[F3], 12),
     (447, 'after', 18, H3[F3], 18), (447, 'after', 18.5, BLK_AFTER, ''),
     (481, 'after', 26, H3[F3], 26),
     (486, 'after', 30, 484, 30),
     (487, 'after', 31, H3[F3], 31),
     (490, 'after', 33, SUB, 33),
     (498, 'after', 39, SUB, 39),
     (504, 'after', 42, SUB, 42),
     (513, 'after', 48, H3[F3], 48),
     (521, 'after', 53, H3[F3], 53), (521, 'after', 53.5, BLK_AFTER, ''),
     (549, 'before', 56.5, BLK_BEFORE, ''), (549, 'before', 57, H3[F3], 57), (549, 'before', 57.5, BLK_AFTER, ''),
     (554, 'after', 63, H3[F3], 63), (554, 'after', 63.5, BLK_AFTER, ''), (554, 'after', 64, TB_BODY[F3], 64),
     (554, 'after', 64.5, BLK_BEFORE, ''),
     (562, 'after', 70, TB_BODY[F3], 70),
     (563, 'after', 72, TB_BODY[F3], 72),
     (706, 'after', 91, TB_BODY[F3], 91),
     (730, 'before', 98, NOTE, 98)]),
}
# HWPX에만 있는 사용자 수정(보존): 411은 MD 각주[^r5-bosch]를 본문 괄호로 편입, 294+295는 절 제목을 두 문단으로 분리
USER_EQUIV = {F3: {411: 10}, F2: {295: None}}
C_TABLES = {  # (anchor, pos, order) -> 새 블록 표 캡션 번호 (C 소유)
 F1: [(19, 'after', 7, '<표 1-1>')],
 F2: [(296, 'after', 74, '<표 2-5>'), (301, 'after', 81, '<표 2-6>'), (303, 'after', 88, '<표 2-7>')], F3: []}
C_REMOVED_TABLE_ANCHORS = {320, 367}

# ── 명세 생성 ───────────────────────────────────────────────────────────
S = {'replace': [], 'delete': [], 'remove_object': [], 'insert': [], 'user_edits': [], 'coverage': []}
tbl_anchor = {t['anchor_idx']: t for t in T if t['section'] == SEC}
def is_top_prose(i):
    b = base[i]; return b['top_level'] and b['table_idx'] is None and i not in tbl_anchor
for f in (F1, F2, F3):
    p = PLAN[f]
    for i, nb in p['R']:
        o = base[i]['text']; nt = btext(N[f][nb])
        S['replace'].append({'section': SEC, 'idx': i, 'old': o, 'new': lead(o) + nt + trail(o)})
    for i in p['D']: S['delete'].append({'section': SEC, 'idx': i, 'old': base[i]['text']})
    for i in p['X']: S['remove_object'].append({'section': SEC, 'idx': i, 'reason': '새 MD에서 <그림 1-1>·<그림 1-2> 통계 그림을 <표 1-1>로 대체(승인 변경, 코디네이터 1a). 캡션·빈 줄은 delete로 분리'})
    for a, pos, order, tpl, nb in p['I']:
        t = '' if nb == '' else lead(base[tpl]['text']) + btext(N[f][nb])
        S['insert'].append({'section': SEC, 'anchor_idx': a, 'position': pos, 'order': order, 'template_idx': tpl, 'text': t})

# ── 검증 1: 유일 위치·old 일치·대상 적격 ─────────────────────────────────
ev = {}
keys = [(x['section'], x['idx']) for k in ('replace', 'delete', 'remove_object') for x in S[k]]
assert len(keys) == len(set(keys)), 'duplicate target'
for k in ('replace', 'delete'):
    for x in S[k]:
        assert x['old'] == base[x['idx']]['text'], (k, x['idx'])
        assert is_top_prose(x['idx']), ('not top-level prose', x['idx'])
        assert 'pic' not in base[x['idx']].get('controls', []), ('pic in prose op', x['idx'])
for x in S['remove_object']:
    assert base[x['idx']]['top_level'] and 'pic' in base[x['idx']].get('controls', []), x['idx']
dele = {x['idx'] for x in S['delete']} | {x['idx'] for x in S['remove_object']}
for x in S['insert']:
    assert is_top_prose(x['anchor_idx']) and x['anchor_idx'] not in dele, ('bad anchor', x['anchor_idx'])
    assert is_top_prose(x['template_idx']), ('bad template', x['template_idx'])
    assert len(base[x['template_idx']]['runs']) == 1, ('template not single-run', x['template_idx'])
ok = [(x['anchor_idx'], x['position'], x['order']) for x in S['insert']]
assert len(ok) == len(set(ok)), 'duplicate insert order'
ctab = {(a, p_, o) for f in C_TABLES for a, p_, o, _ in C_TABLES[f]}
assert not (ctab & set(ok)), 'order collides with C table order'
# 치환 전 문단이 옛 MD와 일치하는지(3자 대조): 옛 블록 대응
def old_match(f, i):
    t = norm(base[i]['text'])
    return [bi for bi, b in enumerate(O[f]) if btext(b) is not None and norm(btext(b)) == t]
three = []
for f in (F1, F2, F3):
    for i, nb in PLAN[f]['R']:
        om = old_match(f, i)
        three.append({'file': f, 'idx': i, 'new_block': nb, 'old_blocks': om, 'hwpx_equals_old_md': bool(om),
                      'new_differs': norm(btext(N[f][nb])) != norm(base[i]['text'])})
    for i in PLAN[f]['D']:
        if base[i]['text'].strip():
            om = old_match(f, i)
            three.append({'file': f, 'idx': i, 'delete': True, 'old_blocks': om, 'hwpx_equals_old_md': bool(om)})
bad3 = [x for x in three if not x['hwpx_equals_old_md']]
assert not bad3, bad3          # 치환·삭제 대상은 모두 옛 MD와 동일 → 사용자 직접 수정분 덮어쓰기 없음
assert all(x['new_differs'] for x in three if 'new_block' in x), [x for x in three if not x.get('new_differs', True)]
ev['three_way_targets'] = len(three)

# ── 검증 2: 적용 시뮬레이션 → 새 MD 블록 순서와 전수 대조 ─────────────────
cap_of = {t['anchor_idx']: re.match(r'<표 \d+-\d+>', t['cells'][0]['paras'][0]['text']).group(0) for t in T
          if t['section'] == SEC and t['cells'] and t['cells'][0]['paras'][0]['text'].startswith('<표')}
rep = {x['idx']: x['new'] for x in S['replace']}
ins = {}
for x in S['insert']: ins.setdefault((x['anchor_idx'], x['position']), []).append((x['order'], 'P', x['text'], x['template_idx']))
for f in C_TABLES:
    for a, p_, o, cap in C_TABLES[f]: ins.setdefault((a, p_), []).append((o, 'T', cap, None))
def simulate(f):
    lo, hi = RANGE[f]; seq = []
    for i in range(lo, hi):
        b = base[i]
        if not b['top_level']: continue
        for o, kind, t, tpl in sorted(ins.get((i, 'before'), [])): seq.append(('TABLE:' + t, None) if kind == 'T' else (t, 'ins', tpl))
        if i in dele or i in C_REMOVED_TABLE_ANCHORS: pass
        elif i in tbl_anchor: seq.append(('TABLE:' + cap_of[i], i))
        elif 'pic' in b.get('controls', []): seq.append(('PIC', i))
        else: seq.append((rep.get(i, b['text']), i, base[i]['attrs']['paraPrIDRef']))
        for o, kind, t, tpl in sorted(ins.get((i, 'after'), [])): seq.append(('TABLE:' + t, None) if kind == 'T' else (t, 'ins', tpl))
    return seq
def expected(f):
    out = []; blocks = N[f]
    for k, b in enumerate(blocks):
        if b['type'] == 'table':
            out.append(('TABLE:' + re.match(r'<표 \d+-\d+>', btext(blocks[k - 1])).group(0), k)); continue
        t = btext(b)
        if b['type'] == 'table_caption' or t.startswith('[^'): continue
        if t.startswith('!['): out.append(('PIC', k)); continue
        out.append((t, k))
    return out
sim_report = {}
for f in (F1, F2, F3):
    seq = simulate(f); exp = expected(f)
    got = []
    for s in seq:
        t, src = s[0], s[1]
        if t == 'PIC' or t.startswith('TABLE:'): got.append((t, src)); continue
        if not t.strip(): continue
        if src in USER_EQUIV.get(f, {}):
            nb = USER_EQUIV[f][src]
            if nb is None: got[-1] = (got[-1][0] + t.strip(), got[-1][1]); continue   # 295: 294 제목 연속
            got.append((btext(N[f][nb]), src)); continue
        got.append((t.strip(), src))
    # 흐름도 그림(40)은 MD에 이미지 줄이 없으므로 PIC 비교에서 제외하고 별도 확인
    got_c = [g for g in got if g[0] != 'PIC']; exp_c = [e for e in exp if e[0] != 'PIC']
    A = [norm(g[0]) for g in got_c]; E = [norm(e[0]) for e in exp_c]
    mism = [(k, got_c[k][0][:40] if k < len(got_c) else None, exp_c[k][0][:40] if k < len(exp_c) else None)
            for k in range(max(len(A), len(E))) if (A[k] if k < len(A) else None) != (E[k] if k < len(E) else None)]
    assert not mism, (f, mism[:5])
    pics_got = [g[1] for g in got if g[0] == 'PIC']; pics_exp = [e[1] for e in exp if e[0] == 'PIC']
    # 빈 줄 구조: 절·항 제목 앞뒤가 빈 문단인지
    flat = [s for s in seq]
    heads = [k for k, s in enumerate(flat) if s[0] and re.match(r'^제\d+(절|항) ', s[0].strip())]
    nxt = lambda k: k + 2 if k + 1 < len(flat) and flat[k + 1][1] == 295 else k + 1   # 295는 294 제목의 사용자 분리 줄
    blank_err = [flat[k][0][:20] for k in heads if not (k > 0 and not flat[k - 1][0].strip() and nxt(k) < len(flat) and not flat[nxt(k)][0].strip())]
    assert not blank_err, (f, blank_err)
    dbl = [k for k in range(1, len(flat)) if not flat[k][0].strip() and not flat[k - 1][0].strip() and flat[k][0] != 'PIC']
    sim_report[f] = {'compared_items': len(E), 'mismatch': 0, 'pics_kept_idx': pics_got, 'pic_blocks_in_md': len(pics_exp),
                     'headings_checked': len(heads), 'heading_blank_errors': 0, 'double_blank_positions': len(dbl)}
ev['simulation'] = sim_report

# ── coverage: 새 블록 전수 + 옛 문단 처분 전수 ──────────────────────────
for f in (F1, F2, F3):
    p = PLAN[f]; cov = {}
    for i, nb in p['K']: cov[nb] = {'status': 'unchanged', 'idx': i}
    for i, nb in p['R']: cov[nb] = {'status': 'replace', 'idx': i}
    for a, pos, o, tpl, nb in p['I']:
        if nb != '': cov[nb] = {'status': 'insert', 'anchor_idx': a, 'position': pos, 'order': o}
    for a, pos, o, cap in C_TABLES[f]:
        for k, b in enumerate(N[f]):
            if b['type'] == 'table_caption' and btext(b).startswith(cap):
                cov[k] = cov[k + 1] = {'status': 'C_table_new_or_moved', 'anchor_idx': a, 'position': pos, 'order': o}
    for k, b in enumerate(N[f]):
        if k in cov: continue
        t = btext(b) or ''
        if b['type'] in ('table', 'table_caption'):
            nxt = N[f][k + 1] if b['type'] == 'table_caption' else b
            cap = re.match(r'<표 \d+-\d+>', btext(b) if b['type'] == 'table_caption' else btext(N[f][k - 1])).group(0)
            anc = [a for a, c in cap_of.items() if c == cap and RANGE[f][0] <= a < RANGE[f][1]]
            cov[k] = {'status': 'C_table_in_place', 'table_anchor_idx': anc[0] if anc else None}
        elif t.startswith('!['): cov[k] = {'status': 'figure_object_kept', 'idx': [s[1] for s in simulate(f) if s[0] == 'PIC']}
        elif t.startswith('[^'): cov[k] = {'status': 'footnote_def_already_in_hwpx_body', 'idx': 411}
        elif k in USER_EQUIV.get(f, {}).values(): cov[k] = {'status': 'user_edit_preserved', 'idx': [i for i, v in USER_EQUIV[f].items() if v == k][0]}
    for k, b in enumerate(N[f]):
        c = cov.get(k); assert c, ('uncovered new block', f, k, b['type'], (btext(b) or '')[:40])
        S['coverage'].append({'file': f, 'new_block': k, 'type': b['type'], **c})
    lo, hi = RANGE[f]
    handled = {i for i, _ in p['K']} | {i for i, _ in p['R']} | set(p['D']) | set(p['X']) | set(USER_EQUIV.get(f, {}))
    for i in range(lo, hi):
        b = base[i]
        if not b['top_level'] or i in handled: continue
        if i in tbl_anchor:
            S['coverage'].append({'file': f, 'hwpx_idx': i, 'status': 'C_table_anchor' + ('_delete_by_C' if i in C_REMOVED_TABLE_ANCHORS else '')}); continue
        if 'pic' in b.get('controls', []):
            S['coverage'].append({'file': f, 'hwpx_idx': i, 'status': 'figure_object_kept'}); continue
        assert not b['text'].strip(), ('unhandled non-empty paragraph', i, b['text'][:40])
        S['coverage'].append({'file': f, 'hwpx_idx': i, 'status': 'blank_kept'})
    for i in p['D'] + p['X']:
        S['coverage'].append({'file': f, 'hwpx_idx': i, 'status': 'removed', 'old_blocks': old_match(f, i) if base[i]['text'].strip() else []})

# ── user_edits: HWPX 실문구가 MD와 다른 지점(보존) ─────────────────────
S['user_edits'] = [
 {'section': SEC, 'idx': 411, 'actual': base[411]['text'], 'old_md': btext(O[F3][9]), 'new_md': btext(N[F3][10]),
  'judgement': '옛·새 MD 모두 같은 문장이고 각주 [^r5-bosch] 정의(새 블록 11)를 HWPX가 본문 괄호로 편입한 사용자 형식. MD 변경이 없으므로 수정하지 않고 보존.'},
 {'section': SEC, 'idx': 295, 'actual': base[295]['text'], 'old_md': btext(O[F2][71]), 'new_md': btext(N[F2][71]),
  'judgement': '절 제목을 294("제5절 …고찰")와 295("(연구 가설 도출 근거)")로 나눈 사용자 조판. 제목 문구 변경이 없어 둘 다 보존.'},
 {'section': SEC, 'idx': 736, 'actual_runs': base[736]['runs'], 'new_md': btext(N[F3][103]),
  'judgement': '텍스트는 옛 MD와 같으나 run이 charPr 77/37/78로 나뉜 서식 흔적이 있음. 새 MD 요청대로 치환하되, 메인이 치환 시 charPr 77/78의 의미(사용자 서식 여부)를 확인할 것.'},
]
ev['counts'] = {k: len(v) for k, v in S.items()}
ev['inserted_nonblank'] = sum(1 for x in S['insert'] if x['text'])
ev['inserted_blank'] = sum(1 for x in S['insert'] if not x['text'])
(P / 'prose_A.json').write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(ev, ensure_ascii=False, indent=1)); print('VALIDATION PASS')
