# QA_back_final_prep: 대상 표 목록(내용 기반 로케이터) 작성 — 읽기 전용
import zipfile, sys, json, re
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
SRC = sys.argv[1] if len(sys.argv) > 1 else 'toc2_saved.hwpx'
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
TARGETS = [22, 26, 28, 33, 34, 35, 36, 38, 39, 40, 42, 43, 44, 49, 50, 51]
root = etree.fromstring(zipfile.ZipFile(SRC).read('Contents/section2.xml'))
tbls = list(root.iter(HP + 'tbl'))
paras = list(root.iter(HP + 'p'))
pidx = {p: i for i, p in enumerate(paras)}
norm = lambda s: re.sub(r'\s+', '', s)
def ptext(p):
    return ''.join(t.text or '' for t in p.iter(HP + 't') if next(t.iterancestors(HP + 'p')) is p)
out = []
for i in TARGETS:
    t = tbls[i]
    rows = t.findall(HP + 'tr')
    rowtxt = [norm(''.join(r.itertext())) for r in rows]
    anchor = next(t.iterancestors(HP + 'p'))
    ai = pidx[anchor]
    # 앵커 앞 캡션 후보(비어 있지 않은 직전 본문 문단)
    cap = ''
    for j in range(ai - 1, max(ai - 6, 0), -1):
        if paras[j].getparent().tag == HP + 'subList':
            continue
        s = ptext(paras[j]).strip()
        if s:
            cap = s; break
    parent = next((tbls.index(a) for a in t.iterancestors(HP + 'tbl')), None)
    lastrow = next((r for r in reversed(rowtxt) if r), '')
    out.append(dict(table_idx=i, parent=parent, anchor_para=ai, caption=cap[:80],
                    head=rowtxt[0][:24], lastrow_tail=lastrow[-16:], lastrow_head=lastrow[:16],
                    rows=len(rows), n_실험전=norm(''.join(t.itertext())).count('실험전'),
                    n_확정필요=''.join(t.itertext()).count('[확정 필요')))
json.dump(out, open('QA_back_final_targets.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for d in out: print(json.dumps(d, ensure_ascii=False))
