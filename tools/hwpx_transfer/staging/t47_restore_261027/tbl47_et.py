import sys,zipfile,re
import xml.etree.ElementTree as ET
NS={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hs':'http://www.hancom.co.kr/hwpml/2011/section'}
HP='{%s}'%NS['hp']
def ptext(p): return ''.join(t.text or '' for t in p.iter(HP+'t'))
def load(path):
    root=ET.fromstring(zipfile.ZipFile(path).read('Contents/section2.xml'))
    tops=list(root)  # top-level hp:p
    return root,tops
def tables47(tops):
    idx=[i for i,p in enumerate(tops) if p.tag==HP+'p' and '<표 4-7>' in ptext(p) and p.find('.//'+HP+'tbl') is None]
    first=idx[0]
    end=next(i for i,p in enumerate(tops) if i>first and '<표 4-8>' in ptext(p))
    res=[]
    for i in range(first,end):
        for tbl in tops[i].iter(HP+'tbl'):
            res.append((i,tbl))
    return res
def grid(tbl):
    cells=[]
    for tc in tbl.iter(HP+'tc'):
        a=tc.find(HP+'cellAddr'); s=tc.find(HP+'cellSpan'); z=tc.find(HP+'cellSz')
        txt='|'.join(ptext(p) for p in tc.find(HP+'subList').findall(HP+'p'))
        cells.append(dict(r=int(a.get('rowAddr')),c=int(a.get('colAddr')),rs=int(s.get('rowSpan')),cs=int(s.get('colSpan')),w=int(z.get('width')),h=int(z.get('height')),t=txt,tc=tc))
    return cells
if __name__=='__main__':
    for path in sys.argv[1:]:
        root,tops=load(path); print('==',path[-50:])
        for k,(i,tbl) in enumerate(tables47(tops),1):
            cells=grid(tbl); sz=tbl.find(HP+'sz')
            print(f' table{k} top{i} rows={tbl.get("rowCnt")} cols={tbl.get("colCnt")} width={sz.get("width")} cells={len(cells)}')
            print('  merged:',[(c['r'],c['c'],c['rs'],c['cs'],c['t'][:8]) for c in cells if c['rs']>1 or c['cs']>1])
            print('  row0 w:',[(c['c'],c['cs'],c['w']) for c in cells if c['r']==0])
            rows={}
            for c in cells: rows.setdefault(c['r'],[]).append(f"{c['c']}:{c['t'][:12]}")
            for r in sorted(rows): print('   r%-2d'%r,' | '.join(rows[r]))
