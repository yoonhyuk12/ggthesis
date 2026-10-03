"""Read the latest source HWPX and preserve an immutable local working base."""
from pathlib import Path
import hashlib, json, re, shutil, zipfile
from lxml import etree as E

Q = Path(__file__).resolve().parent
ROOT = Q.parents[3]
P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'

def own_text(p):
    return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))

def main():
    candidates = sorted(p for p in (ROOT/'00. hwpx').glob('*.hwpx') if re.match(r'^\d{6}_\d{4}_',p.name))
    base = candidates[-1]
    copy = Q/'base.hwpx'
    if copy.exists():
        raise SystemExit('working base already exists; do not overwrite')
    shutil.copy2(base, copy)
    paras, tables, sections = [], [], []
    with zipfile.ZipFile(copy) as z:
        for name in sorted(n for n in z.namelist() if re.fullmatch(r'Contents/section\d+\.xml',n)):
            root = E.fromstring(z.read(name))
            ps = list(root.iter(P+'p'))
            pis = {p:i for i,p in enumerate(ps)}
            ts = list(root.iter(P+'tbl'))
            tis = {t:i for i,t in enumerate(ts)}
            for i,p in enumerate(ps):
                ancestors = list(p.iterancestors())
                table = next((a for a in ancestors if a.tag==P+'tbl'),None)
                cell = next((a for a in ancestors if a.tag==P+'tc'),None)
                ca = cell.find(P+'cellAddr') if cell is not None else None
                paras.append(dict(section=name,idx=i,text=own_text(p),runs=[[r.get('charPrIDRef'),''.join(''.join(t.itertext()) for t in r.findall(P+'t'))] for r in p.findall(P+'run')],attrs=dict(p.attrib),top_level=p.getparent() is root,table_idx=tis.get(table),cell=dict(ca.attrib) if ca is not None else None,has_object=any(e.tag in [P+'tbl',P+'pic',P+'equation',P+'container'] for e in p.iterdescendants())))
            for i,t in enumerate(ts):
                rows=[]
                for tr in t.findall(P+'tr'):
                    row=[]
                    for tc in tr.findall(P+'tc'):
                        sub=tc.find(P+'subList')
                        cps=list(sub.findall(P+'p')) if sub is not None else []
                        row.append(dict(text='\n'.join(own_text(p) for p in cps),p_indices=[pis[p] for p in cps],address=dict(tc.find(P+'cellAddr').attrib),span=dict(tc.find(P+'cellSpan').attrib),size=dict(tc.find(P+'cellSz').attrib)))
                    rows.append(row)
                tables.append(dict(section=name,idx=i,attrs=dict(t.attrib),rows=rows))
            sections.append(dict(name=name,paragraphs=len(ps),tables=len(ts)))
    for filename,value in [('base_paras.json',paras),('base_tables.json',tables)]:
        (Q/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(source=str(base.relative_to(ROOT)),source_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),sections=sections,md_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'01.docs').glob('*.md')})
    (Q/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
