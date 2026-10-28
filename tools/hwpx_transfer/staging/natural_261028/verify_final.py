from pathlib import Path
import zipfile, xml.etree.ElementTree as E, json, re, hashlib
import pymupdf
W=Path(__file__).parent
NS={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
base=next(Path('00. hwpx').glob('261028_0544_*.hwpx'))
final=Path((W/'output_path.txt').read_text(encoding='utf-8-sig').strip())
def read(path):
    with zipfile.ZipFile(path) as z:
        return [E.fromstring(z.read(f'Contents/section{i}.xml')) for i in range(3)],E.fromstring(z.read('Contents/header.xml'))
def txt(e):return ''.join(e.itertext())
def ps(s):return [txt(p) for p in s.findall('.//hp:p',NS) if txt(p)]
def markers(ss,h):
    red={e.get('id') for e in h.iter() if e.tag.endswith('}charPr') and e.get('textColor','').upper()=='#FF0000'}
    prefixes=['[확정 필요','[CITE_TODO','[UNVERIFIED','[DATA PENDING','[그림 삽입 예정','실험전']
    runs=[r for s in ss for r in s.findall('.//hp:run',NS)]
    return {'red_runs':sum(r.get('charPrIDRef') in red for r in runs),'red_prefix_runs':{p:sum(p in txt(r) and r.get('charPrIDRef') in red for r in runs) for p in prefixes},'nonred_markers':[txt(r) for r in runs if any(p in txt(r) for p in prefixes) and r.get('charPrIDRef') not in red]}
def tables(s):
    out=[];cap=''
    for p in s:
        t=txt(p).strip()
        if re.match(r'^<표\s*\d+-\d+>',t):cap=t.split('>')[0]+'>'
        for tbl in p.findall('.//hp:tbl',NS):
            out.append({'caption':cap,'text':re.sub(r'\s+','',txt(tbl)), 'sig':(tbl.get('rowCnt'),tbl.get('colCnt'),[(x.tag.split('}')[-1],dict(x.attrib)) for x in tbl.iter() if x.tag.split('}')[-1] in ('cellAddr','cellSpan','tblcol')],[x.get('width') for x in tbl.findall('.//hp:cellSz',NS)])})
    return out
b,bh=read(base);f,fh=read(final);p,ph=read(W/'patched_toc.hwpx');fresh,_=read(W/'fresh.hwpx')
text='\n'.join(ps(s)[i] for s in f for i in range(len(ps(s))))
blocks=json.loads((W.parent/'ch05.blocks.json').read_text(encoding='utf-8'))['blocks']
paras=[''.join(r['text'] for r in x['runs']) for x in blocks if x['type']=='p']
checks={}
checks['section_paragraph_text_equal']=[ps(f[i])==ps(p[i]) for i in range(3)]
checks['chapter5_paragraphs']={'expected':len(paras),'present':sum(x in text for x in paras)}
required=['두 집단에 같은 비중을 둔 W의 주효과는 유의하지 않았다(p=.519). 미도입 집단에서의 W 기울기는 −0.208','본 장에서는 연구 모형·가설·측정도구·분석 절차를 설계하고','LLM 검증 기능만의 기여는 따로 가리지 않는다']
checks['required_text']={x:x in text for x in required}
checks['old_text_counts']={x:text.count(x) for x in ['미도입 집단의 W 기울기(W_c)는 유의하지 않았다(p=.519)','분리하지 못하며','시사점은 세 가지이다']}
checks['foreign_text_counts']={x:text.count(x) for x in ['김정년','안전시설물','떨어짐 사고위험','건설현장 안전시설물 설치와 떨어짐 사고위험의 관계']}
checks['markers_base']=markers(b,bh);checks['markers_final']=markers(f,fh)
bt,ft=tables(b[2]),tables(f[2]);checks['table_count']=[len(bt),len(ft)]
checks['table_grid_width_equal']=[{'index':i,'caption':x['caption'],'equal':x['sig']==y['sig'],'text_equal':x['text']==y['text']} for i,(x,y) in enumerate(zip(bt,ft))]
checks['table45_base_fresh_equal']=[x['sig'] for x in bt if x['caption']=='<표 4-5>']==[x['sig'] for x in tables(fresh[2]) if x['caption']=='<표 4-5>']
checks['hashes']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [base,W/'template_kjn.hwpx',final]}
checks['cell_pagebreak_count']=sum(e.get('pageBreak')=='CELL' for s in f for e in s.iter())
d=pymupdf.open(W/'final.pdf');checks['pdf_pages']=len(d)
checks['chapter5_pdf_pages']=[]
for i,pg in enumerate(d):
    t=pg.get_text();n=re.sub(r'\s+','',t)
    if any(re.sub(r'\s+','',x[:30]) in n for x in [paras[0],paras[-1]]):
        checks['chapter5_pdf_pages'].append({'pdf':i+1,'footer':re.findall(r'-\s*(\d+)\s*-',t)})
checks['pass']=all(checks['section_paragraph_text_equal']) and checks['chapter5_paragraphs']=={'expected':11,'present':11} and all(checks['required_text'].values()) and not any(checks['old_text_counts'].values()) and not any(checks['foreign_text_counts'].values()) and checks['markers_base']==checks['markers_final'] and all(x['equal'] for x in checks['table_grid_width_equal']) and checks['cell_pagebreak_count']==0
(W/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
