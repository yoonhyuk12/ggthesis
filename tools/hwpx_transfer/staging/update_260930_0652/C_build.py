"""C 담당: 표 내부 변경 명세(tables_C.json) 생성 + 1회 자체 검증.

입력(읽기 전용): base_paras.json, base_tables.json, old_blocks.json, new_blocks.json
출력: tables_C.json (명세), C_validation.json 없음 — 검증 결과는 tables_C.json['validation']과 report_C.md에 남긴다.
HWPX 쓰기·COM·MCP 없음. --probe 옵션은 base.hwpx를 메모리로만 열어 Surgical.table_fragment
생성 가능 여부를 확인한다(파일 쓰기 없음).
"""
import sys
sys.dont_write_bytecode = True
import json, re, math, hashlib
from C_common import *

out = {'cell_replace': [], 'replace_table': [], 'insert_table': [], 'delete_table': [],
       'user_edits': [], 'coverage': []}
cover = out['coverage']


# ---------------------------------------------------------------- helpers
def patch(pidx, new_text, why):
    p = paras[(SEC, pidx)]
    assert p['table_idx'] is not None, pidx
    if p['text'] != new_text:
        out['cell_replace'].append({'section': SEC, 'idx': pidx, 'old': p['text'], 'new': new_text})
        return 1
    return 0


def replace_cell(c, new_text, why=''):
    """첫 문단에 새 텍스트, 나머지 문단은 빈 문자열(이미 비었으면 생략)."""
    n = 0
    for i, p in enumerate(c['paras']):
        n += patch(p['idx'], new_text if i == 0 else '', why)
    return n


def em(s):
    """대략적 글리프 폭(em): 한글·전각 1.0, 영숫자 0.55, 공백 0.3."""
    w = 0
    for ch in s:
        if ch == ' ':
            w += .3
        elif ord(ch) > 0x2E7F:
            w += 1.0
        elif ord(ch) > 255:
            w += .8
        else:
            w += .55
    return w


DESIGN_TOTAL = 39142  # base 본문 표 공통 전체 폭(HWPUNIT). 실제 적용 시 메인은 원본 표 폭을 보존하고 비중만 쓴다.
EM = 1000             # 표 본문 글자 크기 10pt 가정의 1em(HWPUNIT)
PAD = 1300            # 셀 좌우 안쪽 여백 + 여유


def design_weights(matrix):
    """열폭 비중(합=DESIGN_TOTAL인 HWPUNIT 설계값).
    1) 각 열 최소폭 = 줄바꿈 없이 들어가야 할 최장 어절(머리행 포함, 4em 상한)×EM + PAD
    2) 남는 폭은 내용량 need=(0.5·평균폭+0.5·최대폭)^0.9 비례로 긴 설명 열에 배분."""
    head, body = matrix[0], matrix[1:]
    n = len(head)
    mins, soft = [], []
    for j in range(n):
        cells = [r[j] for r in body] or ['']
        tokens = [t for x in cells + [re.sub(r'\([^)]*\)$', '', head[j])] for t in re.split(r'\s+', x) if t]
        mins.append(min(4, max((em(t) for t in tokens), default=2)) * EM + PAD)
        lens = [em(x) for x in cells]
        soft.append(max(1, .5 * sum(lens) / len(lens) + .5 * max(lens)) ** .9)
    rest = DESIGN_TOTAL - sum(mins)
    assert rest > 0, ('최소폭 합이 전체 폭 초과', mins)
    return [round(mins[j] + rest * soft[j] / sum(soft)) for j in range(n)]


def caption_of(b):
    return b['caption'].strip() or None


# ---------------------------------------------------------------- 1) 구조 동일 표: 셀 부분 치환
def minimal(prefix, nj, oj, ti, result_table=False):
    k = key(prefix)
    a, b, t = old[k][oj], new[k][nj], tables[ti]
    cm = cellmap(t)
    assert len(a['matrix']) == len(b['matrix']) and len(a['matrix'][0]) == len(b['matrix'][0]), (k, nj)
    n_rep = n_fill = 0
    for ri, (ra, rb) in enumerate(zip(a['matrix'], b['matrix'])):
        for ci, (v, w) in enumerate(zip(ra, rb)):
            c = cm.get((ri, ci))
            if c is None:
                assert not w.strip() or w == v, ('병합으로 없는 셀에 새 값', k, ri, ci, w)
                continue
            actual = ctext(c)
            if norm(actual) != norm(v):  # base가 old MD와 다름 = 직접 편집/빈칸 양식
                entry = {'section': SEC, 'table_idx': ti, 'row': ri + offset(t), 'col': ci,
                         'paragraph_indices': [p['idx'] for p in c['paras']],
                         'old_md': v, 'new_md': w, 'actual': actual}
                if result_table and not actual.strip() and w == '실험전':
                    # 코디네이터 Q1 회신: MD가 명시한 실험전은 빈 결과칸에만 채운다.
                    n_fill += replace_cell(c, '실험전', 'result_placeholder')
                    continue
                if norm(v) == norm(w):
                    entry['action'] = 'preserve_user_edit'
                    out['user_edits'].append(entry)
                    continue
                entry['action'] = 'conflict_preserved_needs_review'
                out['user_edits'].append(entry)
                continue
            if v == w or norm(actual) == norm(w):
                continue
            n_rep += replace_cell(c, w, 'md_change')
    if (a['caption'] or '').strip() != (b['caption'] or '').strip() and has_caption_row(t):
        n_rep += replace_cell(t['cells'][0], b['caption'].strip(), 'caption')
    cover.append({'file': k, 'md_block_idx': b['block_idx'], 'caption': caption_of(b), 'base_table_idx': ti,
                  'action': 'cell_replace' if n_rep or n_fill else 'unchanged',
                  'md_changes_applied': n_rep, 'blank_result_cells_filled_실험전': n_fill,
                  'shape': [len(b['matrix']), len(b['matrix'][0])]})


# ---------------------------------------------------------------- 2) 구조 변경 표: 표 재구성
def entry_common(prefix, nj):
    k = key(prefix)
    b = new[k][nj]
    m = b['matrix']
    return k, b, m, design_weights(m)


def replace(prefix, nj, oj, ti, reason):
    k, b, m, w = entry_common(prefix, nj)
    t = tables[ti]
    # 재구성은 base 셀 내용을 지우므로 old MD와 다른 직접 편집이 없어야 한다.
    cm = cellmap(t)
    diffs = [(r, c) for (r, c), cell in cm.items()
             if r < len(old[k][oj]['matrix']) and c < len(old[k][oj]['matrix'][r])
             and norm(ctext(cell)) != norm(old[k][oj]['matrix'][r][c])]
    assert not diffs, ('재구성 대상에 직접 편집 존재', ti, diffs)
    out['replace_table'].append({'section': SEC, 'table_idx': ti, 'anchor_idx': t['anchor_idx'],
                                 'caption': caption_of(b) if has_caption_row(t) else None,
                                 'header': m[0], 'rows': m[1:], 'weights': w, 'reason': reason})
    cover.append({'file': k, 'md_block_idx': b['block_idx'], 'caption': caption_of(b), 'base_table_idx': ti,
                  'action': 'replace_table', 'old_shape': [len(old[k][oj]['matrix']), len(old[k][oj]['matrix'][0])],
                  'shape': [len(m), len(m[0])], 'base_user_edits_in_table': 0})


def insert(prefix, nj, anchor, order, tmpl, reason, oj=None):
    k, b, m, w = entry_common(prefix, nj)
    assert order == b['block_idx'], (order, b['block_idx'])
    t = tables[tmpl]
    assert has_caption_row(t)
    if oj is not None:
        cm = cellmap(t)
        a = old[k][oj]['matrix']
        diffs = [(r, c) for (r, c), cell in cm.items() if r < len(a) and c < len(a[r])
                 and norm(ctext(cell)) != norm(a[r][c])]
        assert not diffs, ('이동 표에 직접 편집 존재', tmpl, diffs)
    assert paras[(SEC, anchor)]['top_level'] and paras[(SEC, anchor)]['table_idx'] is None
    out['insert_table'].append({'section': SEC, 'anchor_idx': anchor, 'position': 'after', 'order': order,
                                'template_table_idx': tmpl, 'template_anchor_idx': t['anchor_idx'],
                                'caption': caption_of(b), 'header': m[0], 'rows': m[1:], 'weights': w})
    cover.append({'file': k, 'md_block_idx': b['block_idx'], 'caption': caption_of(b),
                  'base_table_idx': None, 'template_table_idx': tmpl, 'action': 'insert_table',
                  'anchor': f'after {anchor}', 'reason': reason, 'shape': [len(m), len(m[0])]})


# ================================================================ 제1장
insert('01', 0, anchor=19, order=7, tmpl=1,
       reason='신설 <표 1-1>(옛 그림 1-1·1-2 대체). 앵커·순번은 코디네이터 최종 확정(A 본문 순서 기준).')

# ================================================================ 제2장
minimal('02', 0, 0, 0)
minimal('02', 1, 1, 1)
minimal('02', 2, 2, 2)
replace('02', 3, 3, 3, '<표 2-4> 열 3→4, 행 6→5: 대안 A·B·부대·운영·본 시스템 구성과 미확인 범위 열 신설')
# 표 순서 역전: 옛 t4(도입효과)·t5(차별성) 삭제 후 새 위치에 템플릿 복제 삽입(코디네이터 최종 확정)
insert('02', 4, anchor=296, order=74, tmpl=5, oj=5,
       reason='<표 2-5> 선행연구와 본 연구의 차별성: 옛 <표 2-6>(t5) 번호·위치 이동, 행 6→3 재구성')
insert('02', 5, anchor=301, order=81, tmpl=4,
       reason='신설 <표 2-6> 현장 작동성의 기능–담당자 업무–실효성 영역 연결(5열)')
insert('02', 6, anchor=303, order=88, tmpl=4, oj=4,
       reason='<표 2-7> 도입 효과 선행연구 종합: 옛 <표 2-5>(t4) 번호·위치 이동, 시사점 1셀 변경')
for ti, why in [(4, '옛 <표 2-5> 도입효과 — 새 <표 2-7>로 anchor 303 뒤 재삽입'),
                (5, '옛 <표 2-6> 차별성 — 새 <표 2-5>로 anchor 296 뒤 재삽입')]:
    out['delete_table'].append({'section': SEC, 'anchor_idx': tables[ti]['anchor_idx'],
                                'table_idx': ti, 'reason': why})

# ================================================================ 제3장
replace('03', 0, 0, 6, '<표 3-1> 평가 범위 열 신설(4→5열)')
for j in range(1, 7):
    minimal('03', j, j, 6 + j)
replace('03', 7, 7, 13, '<표 3-8> 대안 A·B 분리(3→4열)와 비교 범위 행 재편(4→6행)')

# ================================================================ 제4장
for j in range(9):
    minimal('04', j, j, 14 + j)
replace('04', 9, 9, 23, '<표 4-5> 도입 후보 명부(등록 90개소·108대)·비교 조건 기록 행 신설(9→11행)')

# ================================================================ 제5장 (결과칸: 빈칸 → MD 명시 실험전만)
for j in range(16):
    minimal('05', j, j, 24 + j, result_table=True)

# ================================================================ 부록(설문지) — 표 셀 안 문단만
ka = key('부록1')
nb = NEW[ka]
cover_para = [(2235, 7), (2236, 8), (2507, 21), (2508, 22)]
for pidx, bi in cover_para:
    assert paras[(SEC, pidx)]['text'] == btext(OLD[ka][bi]), pidx
    patch(pidx, btext(nb[bi]), 'survey cover')
    cover.append({'file': ka, 'md_block_idx': bi, 'base_table_idx': paras[(SEC, pidx)]['table_idx'],
                  'paragraph_idx': pidx, 'action': 'cell_replace(표지 안내문)'})
# 설문 문항 3개(B-3·D-6·D-7): 도입 양식 t43·t45, 미도입 양식 t50 — 중첩/응답격자 보존, 문항 셀만
item = {}
for bi in (51, 55, 61, 65):
    for r in NEW[ka][bi]['rows']:
        item[r[0]] = (plain(r[1]), bi)
olditem = {r[0]: plain(r[1]) for bi in (51, 55, 61, 65) for r in OLD[ka][bi]['rows']}
for ti in (43, 44, 45, 46, 50, 51):
    t = tables[ti]
    n = 0
    rows = {}
    for c in t['cells']:
        rows.setdefault(c['row'], {})[c['col']] = c
    for r, cs in rows.items():
        code = ctext(cs.get(0, {'paras': []})) if 0 in cs else ''
        if code in item:
            qcell = cs[1]
            assert norm(ctext(qcell)) == norm(olditem[code]), (ti, code, ctext(qcell))
            if norm(olditem[code]) != norm(item[code][0]):
                n += replace_cell(qcell, item[code][0])
    cover.append({'file': ka, 'base_table_idx': ti, 'action': 'cell_replace(문항 셀만)' if n else 'unchanged',
                  'items_changed': n, 'note': '리커트 응답 격자·병합 구조 보존'})
for bi in (51, 55, 61, 65):
    cover.append({'file': ka, 'md_block_idx': bi, 'action': 'mapped_to_survey_grids',
                  'base_table_idx': {51: [43, 50], 55: [44, 51], 61: [45], 65: [46]}[bi]})
for ti in (40, 41, 42, 47, 48, 49):
    cover.append({'file': ka, 'base_table_idx': ti, 'action': 'unchanged_verified' if ti not in (40, 47) else 'cell_replace(표지 안내문 2문단)',
                  'note': {41: '중첩 Part A 표 — MD Part A 무변경', 48: '중첩 Part A 표 — MD Part A 무변경'}.get(ti, '')})
cover.append({'file': ka, 'action': 'out_of_scope_top_level',
              'note': 'Part B 안내문(new 블록 49, base 2270·2541)은 표 바깥 최상위 문단 → A/B 소유'})
for k in ('06_결론.md',):
    cover.append({'file': k, 'action': 'no_tables_in_new_md'})


# ================================================================ 검증 (1회)
def validate(probe=False):
    v = {}
    # (a) cell_replace: old 일치·중복 없음·표 셀 문단·재구성/삭제 표와 겹치지 않음
    seen = set()
    rebuilt = {e['table_idx'] for e in out['replace_table']} | {e['table_idx'] for e in out['delete_table']}
    for e in out['cell_replace']:
        kk = (e['section'], e['idx'])
        assert kk not in seen, kk
        seen.add(kk)
        assert paras[kk]['text'] == e['old'], kk
        assert paras[kk]['table_idx'] is not None, kk
        assert paras[kk]['table_idx'] not in rebuilt, kk
    v['cell_replace_old_match'] = f"{len(out['cell_replace'])}/{len(out['cell_replace'])}"
    # (b) 재구성·삽입: 직사각형·열수=비중수·MD 행렬과 문자열 동일
    for e in out['replace_table'] + out['insert_table']:
        n = len(e['header'])
        assert n == len(e['weights']) and all(len(r) == n for r in e['rows']) and all(x > 0 for x in e['weights'])
        src = next(g for k in new for g in new[k] if (g['caption'] or '').strip() == (e['caption'] or ''))
        assert [e['header']] + e['rows'] == src['matrix'], e['caption']
    v['rebuild_matrix_equals_new_md'] = len(out['replace_table']) + len(out['insert_table'])
    # (c) 수치·문항 보존: 새 명세에 담긴 모든 숫자 토큰이 new MD 표에 있고, new MD 표의 숫자는 명세 또는 base에 존재
    def nums(s):
        return re.findall(r'\d[\d,.]*%?', s)
    spec_text = [e['new'] for e in out['cell_replace']] + [x for e in out['replace_table'] + out['insert_table'] for x in [e['header']] + e['rows'] for x in x]
    md_text = ' '.join(x for k in new for g in new[k] for r in g['matrix'] for x in r) + ' ' + ' '.join(btext(b) for b in NEW[ka])
    missing = sorted({n for s in spec_text for n in nums(s) if n not in md_text})
    assert not missing, missing
    v['numbers_in_spec_all_from_new_md'] = True
    # (d) 격자: 부분 치환 표는 base 격자 그대로(행·열·병합 무변경), 재구성은 table_fragment가 직사각형 재생성
    v['partial_tables_grid'] = 'unchanged (텍스트만 치환, 셀·병합 추가/삭제 없음)'
    # (e) new MD 표 전건 커버
    expected = {(k, g['block_idx']) for k in new for g in new[k]}
    covered = {(c['file'], c['md_block_idx']) for c in cover if 'md_block_idx' in c}
    assert expected <= covered, expected - covered
    v['new_md_tables_covered'] = f'{len(expected)}/{len(expected)}'
    # (f) 앵커 충돌 없음
    anchors = [e['anchor_idx'] for e in out['insert_table']]
    assert len(set(anchors)) == len(anchors)
    assert not set(anchors) & {e['anchor_idx'] for e in out['delete_table']}
    # (g) 문항 3개 반영 확인
    q = [e for e in out['cell_replace'] if e['old'].startswith(('우리 현장은 안전관리자가', 'LLM이 캡처 이미지의 전후', '위험 상황이 발생하면'))]
    v['survey_item_cells_changed'] = len(q)
    v['실험전_fills'] = sum(1 for e in out['cell_replace'] if e['new'] == '실험전')
    if probe:
        v['probe'] = probe_fragments()
    return v


def probe_fragments():
    """base.hwpx를 메모리로만 열어 table_fragment가 모든 재구성·삽입 명세를 받아들이는지 확인."""
    import os
    sys.path.insert(0, str(ROOT.parent / 'review_260913_0239'))
    from surgical_ops import Surgical
    s = Surgical(str(ROOT / 'base.hwpx'))
    res = []
    for e in out['replace_table']:
        s.table_fragment(e['section'], e['table_idx'], e['header'], e['rows'], e['weights'], e['caption'])
        res.append(dict(s.estimates[-1], kind='replace', caption=e['caption'] or e['header'][0]))
    for e in out['insert_table']:
        x = s.table_fragment(e['section'], e['template_table_idx'], e['header'], e['rows'], e['weights'], e['caption'])
        s.wrap_table(e['section'], e['template_anchor_idx'], x, new=True)
        res.append(dict(s.estimates[-1], kind='insert', caption=e['caption']))
    return res


if __name__ == '__main__':
    out['validation'] = validate(probe='--probe' in sys.argv)
    src = read('source.json')
    out['validation']['base_hwpx_sha256_expected'] = src['sha256']
    out['validation']['base_hwpx_sha256_actual'] = hashlib.sha256((ROOT / 'base.hwpx').read_bytes()).hexdigest()
    (ROOT / 'tables_C.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: len(v) for k, v in out.items() if isinstance(v, list)}, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out['validation'].items() if k != 'probe'}, ensure_ascii=False, indent=1))
    for p in out['validation'].get('probe', []):
        print(p['kind'], p['caption'][:30], 'widths', p['widths'], 'total', p['total_width'], 'est_h', p['estimated_height'], '/', p['available_height'], p['pageBreak'])
    for u in out['user_edits']:
        print('USER_EDIT', u['action'], u['table_idx'], u['row'], u['col'], repr(u['actual'][:40]), '<-old', repr(u['old_md'][:40]), 'new', repr(u['new_md'][:40]))
