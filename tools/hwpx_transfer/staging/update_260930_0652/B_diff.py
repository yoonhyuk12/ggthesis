# 구 MD(f5588d2)와 현행 MD 블록의 장별 차이 출력 — 사용: python B_diff.py 04|05|06|부록1
import sys, difflib
from B_util import NB, OB, btext

key = next(k for k in NB if k.startswith(sys.argv[1]))
ot = [b['type'] + '|' + ('[TABLE]' if b['type'] == 'table' else btext(b)) for b in OB[key]]
nt = [b['type'] + '|' + ('[TABLE]' if b['type'] == 'table' else btext(b)) for b in NB[key]]
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ot, nt, autojunk=False).get_opcodes():
    if tag == 'equal': continue
    print(f'==== {tag} old[{i1}:{i2}] new[{j1}:{j2}]')
    for i in range(i1, i2): print('  OLD', i, ot[i])
    for j in range(j1, j2): print('  NEW', j, nt[j])
