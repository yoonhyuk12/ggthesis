# spec.json 검증 (a)~(d) + 잔존 옛 표기 탐색 → spec_check.txt
from W_common import *
spec = rd('spec.json'); mdm = {(s, i): v for s, i, v in rd('_mdmark.json')}
L = []; ok_all = True
def out(s): L.append(s); print(s)
# (a) old 일치
bad = [(k, x['idx']) for k in ('replace', 'cell_replace', 'delete') for x in spec[k] if base[(x['section'], x['idx'])]['text'] != x['old']]
out('(a) old == base_paras.text : %d건 검사, 불일치 %d %s' % (sum(len(spec[k]) for k in ('replace', 'cell_replace', 'delete')), len(bad), bad)); ok_all &= not bad
# cell_replace는 표 셀, replace는 표 밖이어야 함
kind_bad = [x['idx'] for x in spec['replace'] if base[(x['section'], x['idx'])]['table_idx'] is not None] + \
           [x['idx'] for x in spec['cell_replace'] if base[(x['section'], x['idx'])]['table_idx'] != x['table_idx']]
out('    replace=표 밖 문단, cell_replace=해당 표 셀 문단 : 위반 %d %s' % (len(kind_bad), kind_bad)); ok_all &= not kind_bad
# (b) idx 중복
keys = [(x['section'], x['idx']) for k in ('replace', 'cell_replace', 'delete') for x in spec[k]]
dup = sorted({k for k in keys if keys.count(k) > 1})
out('(b) (section, idx) 중복 : %d %s' % (len(dup), dup)); ok_all &= not dup
noop = [x['idx'] for k in ('replace', 'cell_replace') for x in spec[k] if x['old'] == x['new']]
out('    old == new (무의미 치환) : %d %s' % (len(noop), noop)); ok_all &= not noop
# (c) 마커 개수
mk = []
for k in ('replace', 'cell_replace'):
    for x in spec[k]:
        exp = mdm[(x['section'], x['idx'])]; got = nmark(x['new'])
        if exp != got: mk.append((x['idx'], exp, got))
nm = sum(nmark(x['new']) for k in ('replace', 'cell_replace') for x in spec[k])
out('(c) new 마커 수 == MD 새 블록 마커 수 : %d건 검사(마커 총 %d개), 불일치 %d %s' % (len(mdm), nm, len(mk), mk)); ok_all &= not mk
lost = [(x['idx'], nmark(x['old']), nmark(x['new'])) for k in ('replace', 'cell_replace') for x in spec[k] if nmark(x['new']) < nmark(x['old'])]
out('    참고: 치환으로 마커가 줄어드는 문단 %d %s' % (len(lost), lost))
# (d) 커버리지
cov = spec['coverage']
out('(d) 변경 블록 %d / 대응 %d (replace·cell_replace·already_applied 분류) → %s' % (cov['changed_blocks'], cov['mapped'], 'OK' if cov['changed_blocks'] == cov['mapped'] else 'FAIL'))
ok_all &= cov['changed_blocks'] == cov['mapped']
from collections import Counter
out('    분류: %s' % dict(Counter(d.split(' ')[1].split('(')[0] for d in cov['detail'])))
out('    목차 대조(00_목차 §3 ↔ section1, 치환 후): MD %d / HWPX %d 항목, 차이 %s; 표·그림 캡션 블록 변경 %s' % (
    cov['toc_compare']['md_entries'], cov['toc_compare']['hwpx_entries'], cov['toc_compare']['diff_after_spec'], cov['toc_compare']['caption_blocks_changed']))
out('    참고문헌: %s' % dict(Counter(r[0] for r in cov['references'])))
# 적용 시뮬레이션 후 옛 표기 잔존 검색
after = {k: b['text'] for k, b in base.items()}
for k in ('replace', 'cell_replace'):
    for x in spec[k]: after[(x['section'], x['idx'])] = x['new']
for tok in ('김윤헌', '실제 위험 차단', '위험의 추가 차단', 'arXiv:2312.02078,', '2025. 10. 1.] [법률 제21065호, 2025. 10. 1., 타법개정] (ref', '우리 현장은 위험 상황을', '발주처로부터', '쿨링타임', '가짜 위험을 걸러주어'):
    hits = [(s[-5], i) for (s, i), t in after.items() if tok in t]
    out('    잔존 검색 "%s": %s' % (tok, hits))
out('종합: %s' % ('PASS' if ok_all else 'FAIL'))
(P / 'spec_check.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
