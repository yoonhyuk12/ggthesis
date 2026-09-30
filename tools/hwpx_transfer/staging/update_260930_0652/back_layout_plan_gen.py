# back_layout_plan_gen.py — QA_back 후속: 최소 레이아웃 매니페스트(back_layout_plan.json) 생성(읽기 전용)
# 입력: toc2_saved.hwpx (zipfile+lxml, 쓰기 없음). 출력: back_layout_plan.json
# 사용: PYTHONIOENCODING=utf-8 python back_layout_plan_gen.py
import zipfile, sys, json, hashlib, re, copy
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
SRC = 'toc2_saved.hwpx'
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HH = '{http://www.hancom.co.kr/hwpml/2011/head}'
SEC = 'Contents/section2.xml'

z = zipfile.ZipFile(SRC)
src_sha = hashlib.sha256(open(SRC, 'rb').read()).hexdigest()
root = etree.fromstring(z.read(SEC))
head = etree.fromstring(z.read('Contents/header.xml'))
paraPr = {p.get('id'): p for p in head.iter(HH + 'paraPr')}
T = list(root.iter(HP + 'tbl'))
P = list(root.iter(HP + 'p'))                      # 문서 순서, 표 셀 문단 포함
pidx = {id(p): i for i, p in enumerate(P)}
body = [p for p in root if p.tag == HP + 'p']
sha = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()

def own_cells(t):
    return [c for tr in t.findall(HP + 'tr') for c in tr.findall(HP + 'tc')]

def runs_sig(el):
    """(charPrIDRef, text) 순서 서명 — 글꼴·색·텍스트 보존 확인용."""
    out = []
    for r in el.iter(HP + 'run'):
        out.append([r.get('charPrIDRef'), ''.join(t.text or '' for t in r.iter(HP + 't'))])
    return out

def col_widths(t):
    cw = {}
    for c in own_cells(t):
        a, s, z_ = c.find(HP + 'cellAddr'), c.find(HP + 'cellSpan'), c.find(HP + 'cellSz')
        if s.get('colSpan') == '1':
            cw.setdefault(int(a.get('colAddr')), int(z_.get('width')))
    return [cw.get(k) for k in range(int(t.get('colCnt')))]

def grid_check(t, widths):
    R, C = int(t.get('rowCnt')), int(t.get('colCnt'))
    occ = [[0] * C for _ in range(R)]
    cells, errs = [], []
    for c in own_cells(t):
        a, s, z_ = c.find(HP + 'cellAddr'), c.find(HP + 'cellSpan'), c.find(HP + 'cellSz')
        r0, c0, rs, cs = int(a.get('rowAddr')), int(a.get('colAddr')), int(s.get('rowSpan')), int(s.get('colSpan'))
        for rr in range(r0, r0 + rs):
            for cc in range(c0, c0 + cs):
                if rr >= R or cc >= C:
                    errs.append(f'out_of_range {rr},{cc}')
                else:
                    occ[rr][cc] += 1
        old_w = int(z_.get('width'))
        cells.append(dict(row=r0, col=c0, rowSpan=rs, colSpan=cs, old_width=old_w,
                          new_width=sum(widths[c0:c0 + cs])))
        # 현재 셀 폭이 현재 열폭 합과 일치하는지(구조 사전 확인)
    cur = col_widths(t)
    for cell in cells:
        if sum(cur[cell['col']:cell['col'] + cell['colSpan']]) != cell['old_width']:
            errs.append(f"old_cell_width_mismatch {cell['row']},{cell['col']}")
    bad = [(r, c, occ[r][c]) for r in range(R) for c in range(C) if occ[r][c] != 1]
    if bad:
        errs.append(f'occupancy {bad[:5]}')
    return cells, errs

def anchor_idx(t):
    top = [a for a in t.iterancestors(HP + 'p')][-1]
    return pidx[id(top)]

TARGETS = [
    # (idx, 새 열폭, 셀 좌우여백(없으면 None), 사유)
    (22, [3276, 17500, 7400, 10966], None, '표 D: 근거 열 협소로 전면 1쪽 차지·제목 고아·꼬리말 침범(QA_back §3)'),
    (28, [5741, 4043, 5100, 4043, 4043, 4043, 4043, 4043, 4043], None, '<표 5-2> 패널 B: df·p 실험전 3줄 분절(§6)'),
    (33, [6495, 4818, 4818, 4818, 4516, 4817, 4043, 4817], None, '<표 5-6> 패널 A: SE 3줄 분절(§6)'),
    (34, [10259, 5366, 4043, 5700, 5688, 4043, 4043], None, '<표 5-6> 패널 B: SE·df·p 2줄 분절(§6)'),
    (35, [9985, 6391, 6391, 6390, 4243, 5742], None, '<표 5-6> 패널 C: ICC 2줄 분절(§6)'),
    (36, [6742] + [3600] * 9, 283, '<표 5-7> 패널 A: 9개 수치 열 분절 — 여백 283 필요(§6)'),
    (38, [10259, 5366, 4043, 5700, 5688, 4043, 4043], None, '<표 5-8> 패널 A: SE·df·p 2줄 분절(§6)'),
    (39, [4800, 5542] + [3600] * 8, 283, '<표 5-8> 패널 B: 수치 열 3줄 분절 — 여백 283 필요(§6)'),
    (40, [9985, 6391, 6391, 6390, 4243, 5742], None, '<표 5-8> 패널 C: ICC 2줄 분절(§6)'),
    (44, [37102], None, '부록(도입) 중첩 표: 부모 셀 가용폭 38402-510-510-outMargin 140×2 = 37102 초과(§5)'),
    (51, [37102], None, '부록(미도입) 중첩 표: 동일(§5)'),
]
EXPECT_OLD = {  # QA_back에서 관찰한 현재 값 — 불일치 시 매니페스트 무효
    22: [3276, 19690, 9219, 6957], 28: [7143, 4286, 4286, 2857, 2857, 4286, 4285, 4571, 4571],
    33: [7527, 4818, 4818, 4818, 4516, 4817, 3011, 4817], 34: [10538, 5645, 3764, 6022, 5645, 3764, 3764],
    35: [9985, 6391, 6391, 6390, 3994, 5991], 36: [6154, 3939, 3939, 3939, 3693, 3939, 3693, 2462, 3692, 3692],
    38: [10538, 5645, 3764, 6022, 5645, 3764, 3764], 39: [6273, 7025, 4015, 4015, 3764, 2509, 4014, 2509, 2509, 2509],
    40: [9985, 6391, 6391, 6390, 3994, 5991], 44: [50179], 51: [50179],
}

problems = []
tables = []
for idx, widths, lr, reason in TARGETS:
    t = T[idx]
    sz = t.find(HP + 'sz')
    total_old = int(sz.get('width'))
    cur = col_widths(t)
    parent = next(iter(t.iterancestors(HP + 'tbl')), None)
    if cur != EXPECT_OLD[idx]:
        problems.append(f'table {idx} old widths {cur} != expected {EXPECT_OLD[idx]}')
    total_new = total_old if parent is None else 37102
    if sum(widths) != total_new:
        problems.append(f'table {idx} sum {sum(widths)} != {total_new}')
    cells, errs = grid_check(t, widths)
    problems += [f'table {idx} {e}' for e in errs]
    entry = dict(
        table_idx=idx, section='Contents/section2.xml', reason=reason,
        rowCnt=int(t.get('rowCnt')), colCnt=int(t.get('colCnt')),
        old_total_width=total_old, total_width=total_new,
        old_widths=cur, widths=widths, widths_sum=sum(widths),
        cells=cells,
        precheck=dict(
            head_text=''.join(t.itertext())[:40],
            text_sha256=sha(''.join(t.itertext())),
            runs_sha256=sha(json.dumps(runs_sig(t), ensure_ascii=False)),
            marker_count_실험전=''.join(t.itertext()).count('실험전'),
            pageBreak=t.get('pageBreak'), repeatHeader=t.get('repeatHeader'),
            treatAsChar=t.find(HP + 'pos').get('treatAsChar'),
        ),
        anchor_paragraph_idx=anchor_idx(t),
        linesegarray_clear_paragraph_idx=[pidx[id(p)] for c in own_cells(t) for p in c.iter(HP + 'p')
                                          if next(iter(p.iterancestors(HP + 'tbl'))) is t],
    )
    if parent is not None:
        pi = T.index(parent)
        pw = int(parent.find(HP + 'sz').get('width'))
        pc = own_cells(parent)[0]; pm = pc.find(HP + 'cellMargin'); om = t.find(HP + 'outMargin')
        avail = pw - int(pm.get('left')) - int(pm.get('right')) - int(om.get('left')) - int(om.get('right'))
        entry['nested'] = dict(parent_table_idx=pi, parent_width_preserve=pw,
                               parent_cellMargin_lr=[int(pm.get('left')), int(pm.get('right'))],
                               outMargin_lr=[int(om.get('left')), int(om.get('right'))], available=avail,
                               apply_to=['hp:tbl/hp:sz@width', 'hp:tc/hp:cellSz@width'])
        if pw != 38402 or avail != 37102:
            problems.append(f'table {idx} parent width {pw} avail {avail}')
        entry['anchor_paragraph_idx'] = anchor_idx(parent)
    if lr is not None:
        cm0 = [dict(c.find(HP + 'cellMargin').attrib) for c in own_cells(t)]
        tb = sorted({(m['top'], m['bottom']) for m in cm0})
        entry['cell_margin_lr'] = lr
        entry['cell_margin_apply'] = dict(
            scope='all own cells of this table', set={'hp:tc@hasMargin': '1',
                                                      'hp:cellMargin@left': str(lr), 'hp:cellMargin@right': str(lr)},
            keep_top_bottom=tb, old_hasMargin=sorted({c.get('hasMargin') for c in own_cells(t)}),
            old_lr=sorted({(m['left'], m['right']) for m in cm0}),
            inner_width_numeric_col=3600 - 2 * lr, note='실험전 1줄 필요 안쪽폭 ≥3023(4043-1020 실측), 3034 확보. 표 inMargin은 변경하지 않는다.')
    tables.append(entry)

# ---- 부록 미도입 표지(49) 1행 셀 문단 줄간격 → 도입 표지(42) 대응 문단과 동일 paraPr 재사용
def norm_pp(pid, drop_ls=True):
    e = copy.deepcopy(paraPr[pid]); e.attrib.pop('id', None)
    if drop_ls:
        for ls in e.iter(HH + 'lineSpacing'):
            ls.set('value', 'X')
    return etree.tostring(e)

def ls_val(pid):
    return [ls.get('value') for ls in paraPr[pid].iter(HH + 'lineSpacing')]

r42 = [p for p in T[42].findall(HP + 'tr')[1].iter(HP + 'p')]
r49 = [p for p in T[49].findall(HP + 'tr')[1].iter(HP + 'p')]
para_styles = []
if len(r42) != len(r49):
    problems.append(f'cover row1 paragraph count 42={len(r42)} 49={len(r49)}')
for k, (a, b) in enumerate(zip(r42, r49)):
    ta, tb = ''.join(a.itertext()), ''.join(b.itertext())
    new, old = a.get('paraPrIDRef'), b.get('paraPrIDRef')
    same_except_ls = norm_pp(new) == norm_pp(old)
    if not same_except_ls:
        problems.append(f'cover para {k}: paraPr {old} vs {new} differ beyond lineSpacing — clone needed')
    if ta != tb:
        problems.append(f'cover para {k}: text differs between 42 and 49 (mapping by position is unsafe)')
    if old == new:
        continue
    para_styles.append(dict(
        section='Contents/section2.xml', idx=pidx[id(b)], table_idx=49, row=1, para_in_cell=k,
        old_paraPrIDRef=old, new_paraPrIDRef=new,
        old_lineSpacing=ls_val(old), new_lineSpacing=ls_val(new),
        counterpart_in_table42_idx=pidx[id(a)],
        paraPr_identical_except_lineSpacing=same_except_ls, clone_needed=False,
        precheck=dict(old_text=tb, runs=runs_sig(b), styleIDRef=b.get('styleIDRef')),
        reason='미도입 부록 표지 줄간격(220~240%)을 도입 표지(190/180%)와 일치 — 제목 고아(p143)·꼬리말 침범(p144) 해소(QA_back §4)'))

cover_anchor = anchor_idx(T[49])
plan = dict(
    source=SRC, source_sha256=src_sha, section='Contents/section2.xml',
    paragraph_idx_convention='section2.xml 전체 hp:p 문서 순서(표 셀 문단 포함, 0부터)',
    table_idx_convention='section2.xml 전체 hp:tbl 문서 순서(중첩 표 포함, 0부터) = reflowed_verification.json',
    keep_unchanged=dict(table26=dict(widths=col_widths(T[26]), note='메인 수정·검증 완료, 변경 금지'),
                        table43_width=int(T[43].find(HP + 'sz').get('width')),
                        table50_width=int(T[50].find(HP + 'sz').get('width'))),
    tables=tables,
    paragraph_styles=para_styles,
    paragraph_styles_linesegarray_clear_idx=[pidx[id(p)] for p in r49] + [cover_anchor],
    header_changes=[],
    validation=dict(ok=not problems, problems=problems),
)
json.dump(plan, open('back_layout_plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok' if not problems else 'PROBLEMS', problems)
for t in tables:
    print(t['table_idx'], t['old_widths'], '->', t['widths'], 'sum', t['widths_sum'], 'total', t['total_width'],
          'cells', len(t['cells']), 'anchor', t['anchor_paragraph_idx'], 'lr', t.get('cell_margin_lr'))
for p in para_styles:
    print('para', p['idx'], p['old_paraPrIDRef'], '->', p['new_paraPrIDRef'], p['old_lineSpacing'], '->', p['new_lineSpacing'], repr(p['precheck']['old_text'][:25]))
