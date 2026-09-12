"""Conservative section2 table widths; coordinator alone runs CLI to write HWPX.
Read-only planning: build_plan(path). Byte patches preserve all non-target XML.
Requires PyMuPDF only for optional baseline glyph metrics, otherwise stdlib.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

NS = {'p': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'h': 'http://www.hancom.co.kr/hwpml/2011/head'}
P = '{' + NS['p'] + '}'
H = '{' + NS['h'] + '}'
PRESERVE = {22, 24, 25, 26, 27, 29, 30, 31, 32, 37}
SECTION = 'Contents/section2.xml'

def num(el, key, default=0):
    return float(el.get(key, default)) if el is not None else float(default)

def table_spans(data):
    stack, spans = [], []
    for m in re.finditer(rb'<(/?)hp:tbl(?=[\s>])[^>]*>', data):
        if m[1]:
            if not stack:
                raise ValueError('Unbalanced table XML')
            spans.append((stack.pop(), m.end()))
        else:
            stack.append(m.start())
    if stack:
        raise ValueError('Unbalanced table XML')
    return sorted(spans)

class Metrics:
    def __init__(self, header, pdf_path=None):
        self.chars = {x.get('id'): x for x in header.findall('.//h:charPr', NS)}
        self.paras = {x.get('id'): x for x in header.findall('.//h:paraPr', NS)}
        self.faces = {x.get('lang').lower(): {f.get('id'): f.get('face') for f in x} for x in header.findall('.//h:fontface', NS)}
        self.glyphs = {}
        self.pdf_pages = 0
        self.pdf_note = 'Fallback Unicode em widths; PDF absent'
        if pdf_path and Path(pdf_path).exists():
            try:
                import pymupdf
                samples = {}
                with pymupdf.open(pdf_path) as pdf:
                    self.pdf_pages = len(pdf)
                    for page in pdf:
                        for block in page.get_text('rawdict')['blocks']:
                            for line in block.get('lines', []):
                                for span in line['spans']:
                                    size = span['size']
                                    for c in span['chars']:
                                        width = (c['bbox'][2]-c['bbox'][0])/max(size, .01)
                                        if .1 <= width <= 1.5:
                                            samples.setdefault(c['c'], []).append(width)
                self.glyphs = {c: statistics.median(v) for c, v in samples.items()}
                self.pdf_note = 'Baseline PDF glyph bbox/em median; mixed font samples, not exact HWP shaping; 4% horizontal safety'
            except ImportError:
                self.pdf_note = 'PyMuPDF unavailable: fallback Unicode em widths; actual HWP verification required'
        self.used = set()

    def char(self, c, ref):
        cp = self.chars[ref]
        self.used.add(ref)
        lang = 'hangul' if unicodedata.east_asian_width(c) in 'WF' else 'latin'
        size = num(cp, 'height', 1000)
        rel = num(cp.find('h:relSz', NS), lang, 100)/100
        ratio = num(cp.find('h:ratio', NS), lang, 100)/100
        spacing = num(cp.find('h:spacing', NS), lang, 0)/100
        fallback = 1 if lang == 'hangul' else (.33 if c.isspace() else .56)
        em = self.glyphs.get(c, fallback)
        if unicodedata.combining(c):
            em = 0
        return max(0, size*rel*(em*ratio+spacing))*1.04, size*rel

    def paragraph(self, p):
        pr = self.paras[p.get('paraPrIDRef')]
        margin = pr.find('.//h:margin', NS)
        margins = {x.tag.rsplit('}',1)[-1]: num(x, 'value') for x in margin} if margin is not None else {}
        ls = pr.find('.//h:lineSpacing', NS)
        bs = pr.find('h:breakSetting', NS)
        chars = []
        for run in p.findall('p:run', NS):
            ref = run.get('charPrIDRef')
            for el in run.iter():
                if el.tag == P+'t':
                    for c in el.text or '':
                        w,h = self.char(c, ref)
                        chars.append((c,w,h))
                elif el.tag in {P+'lineBreak',P+'br'}:
                    chars.append(('\n',0,1000))
                elif el.tag == P+'tab':
                    chars.append(('\t',4000,1000))
        if not chars:
            run = p.find('p:run',NS)
            height = num(self.chars.get(run.get('charPrIDRef') if run is not None else ''), 'height',1000)
            chars=[('',0,height)]
        return {'chars':chars,'margin':margins,'line_type':ls.get('type','PERCENT') if ls is not None else 'PERCENT',
                'line_value':num(ls,'value',160),'keep_latin':bs is None or bs.get('breakLatinWord')=='KEEP_WORD',
                'keep_korean':bs is not None and bs.get('breakNonLatinWord')=='KEEP_WORD'}

def wrap(p, width):
    chars=p['chars']; m=p['margin']
    available=max(500,width-m.get('left',0)-m.get('right',0))
    # Word-aware greedy wrapping; HWP permits emergency breaks in overlong tokens.
    tokens=[]; current=[]; kind=None
    for c,w,h in chars:
        ck = 'word' if (c.isascii() and (c.isalnum() or c in '_-') and p['keep_latin']) or (p['keep_korean'] and not c.isspace()) else None
        if ck and ck==kind:
            current.append((c,w,h))
        else:
            if current: tokens.append(current)
            current=[(c,w,h)];kind=ck
            if ck is None: tokens.append(current);current=[]
    if current:tokens.append(current)
    used=max(0,m.get('intent',0)); maxh=0; heights=[]
    for token in tokens:
        tw=sum(c[1] for c in token)
        if used and used+tw>available and tw<=available:
            heights.append(maxh or 1000); used=0;maxh=0
        for c,w,h in token:
            if c=='\n':
                heights.append(maxh or h);used=0;maxh=0;continue
            if used and used+w>available:
                heights.append(maxh or h);used=0;maxh=0
            used+=w;maxh=max(maxh,h)
    heights.append(maxh or 1000)
    def advance(h):
        v=p['line_value'];t=p['line_type']
        if t=='PERCENT':return h*v/100
        if t=='FIXED':return max(h,v)
        if t=='BETWEEN_LINES':return h+v
        return max(h,v)
    # Full leading on last line is conservative relative to normal HWP layout.
    return sum(advance(h) for h in heights)+m.get('prev',0)+m.get('next',0),len(heights)

class Table:
    def __init__(self,t,metrics):
        self.xml=t; self.n=int(t.get('colCnt')); self.rows=int(t.get('rowCnt'));self.cells=[]
        self.total=int(t.find('p:sz',NS).get('width'))
        self.old=[None]*self.n; constraints=[]
        default=t.find('p:inMargin',NS)
        for tc in t.findall('./p:tr/p:tc',NS):
            addr=tc.find('p:cellAddr',NS);span=tc.find('p:cellSpan',NS);sz=tc.find('p:cellSz',NS)
            c=int(addr.get('colAddr'));r=int(addr.get('rowAddr'));cs=int(span.get('colSpan'));rs=int(span.get('rowSpan'))
            width=int(sz.get('width'))
            if cs==1:
                if self.old[c] is not None and abs(self.old[c]-width)>2:raise ValueError('Inconsistent column widths')
                self.old[c]=width
            constraints.append((c,cs,width))
            margin=tc.find('p:cellMargin',NS) if tc.get('hasMargin')=='1' else default
            if margin is None:margin=tc.find('p:cellMargin',NS)
            self.cells.append({'c':c,'r':r,'cs':cs,'rs':rs,'old_width':width,'min_height':num(sz,'height'),
                'pad':[num(margin,k) for k in ('left','right','top','bottom')],
                'paras':[metrics.paragraph(p) for p in tc.findall('./p:subList/p:p',NS)],
                'text': ''.join(tc.itertext()),'cache':{}})
        # Merged survey grids may not expose every atomic column; solve boundaries.
        boundaries={0:0,self.n:self.total}
        for _ in range(self.n+1):
            for c,cs,w in constraints:
                if c in boundaries:boundaries.setdefault(c+cs,boundaries[c]+w)
                if c+cs in boundaries:boundaries.setdefault(c,boundaries[c+cs]-w)
        self.ambiguous=[]
        for c in range(self.n):
            if self.old[c] is None:
                if c in boundaries and c+1 in boundaries:self.old[c]=boundaries[c+1]-boundaries[c]
                else:self.ambiguous.append(c);self.old[c]=self.total//self.n
        if not self.ambiguous and abs(sum(self.old)-self.total)<=self.n:self.old[-1]+=self.total-sum(self.old)
        elif not self.ambiguous and sum(self.old)!=self.total:raise ValueError('Width sum mismatch')
        self.header_row=1 if any(c['r']==0 and c['cs']==self.n for c in self.cells) and self.rows>1 else 0
        self.headers=['']*self.n
        for c in self.cells:
            if c['r']==self.header_row and c['cs']==1:self.headers[c['c']]=c['text']

    def estimate(self,widths, detail=False):
        rows=[0.]*self.rows;cellheights=[];lines=[]
        for c in self.cells:
            w=sum(widths[c['c']:c['c']+c['cs']]); key=w
            if key not in c['cache']:
                results=[wrap(p,max(500,w-c['pad'][0]-c['pad'][1])) for p in c['paras']]
                c['cache'][key]=(sum(h for h,n in results)+sum(c['pad'][2:]),sum(n for h,n in results))
            content,n=c['cache'][key];height=max(c['min_height'],content)
            cellheights.append(height);lines.append(n)
            if c['rs']==1:rows[c['r']]=max(rows[c['r']],height)
        for c,h in sorted(zip(self.cells,cellheights),key=lambda x:x[0]['rs']):
            if c['rs']>1:
                r=c['r'];rs=c['rs'];deficit=max(0,h-sum(rows[r:r+rs]))
                for j in range(r,min(r+rs,len(rows))):rows[j]+=deficit/rs
        height=sum(rows)+num(self.xml,'cellSpacing')*max(0,self.rows-1)
        if detail:return {'height':round(height),'row_heights':[round(x) for x in rows], 'cell_lines':lines,'cell_heights':[round(x) for x in cellheights], 'max_row_height':round(max(rows))}
        return height,sum(cellheights)

    def minima(self):
        result=[]
        for i,old in enumerate(self.old):
            title=self.headers[i];text=re.sub(r'\s+','',title)
            numeric=bool(re.search(r'평균|표준편차|최솟값|최댓값|중앙값|신뢰구간|빈도|비율|Cronbach|ICC|M±SD|t\(df\)|F\(df\)|η|효과크기|검정통계량',text)) or text in {'p','W','t','N','n'}
            code=text in {'번호','문항','문항번호','순서','요구','가설'}
            floor=2000 if code else (max(3500,old*.8) if numeric else max(4000,old*.48))
            # Leave short identifiers one line and titles up to two lines.
            header=next((c for c in self.cells if c['r']==self.header_row and c['c']==i and c['cs']==1),None)
            if header:
                glyph=sum(w for p in header['paras'] for _,w,_ in p['chars'])
                floor=max(floor,sum(header['pad'][:2])+glyph/(1 if code and len(text)<=2 else 2)+250)
            result.append(min(old,math.ceil(floor)))
        return result

    def optimize(self,index):
        old=self.old;minimum=self.minima();total=sum(old)
        def objective(w):
            h,ch=self.estimate(w)
            return h+.012*ch+.008*sum(abs(a-b) for a,b in zip(w,old))
        best=old[:];score=objective(best)
        rng=random.Random(260912+index)
        seeds=[old[:]]
        # Demand-guided starts escape staircase plateaus in line count.
        demand=[0.]*self.n
        for c in self.cells:
            if c['cs']==1:demand[c['c']]+=sum(w for p in c['paras'] for _,w,_ in p['chars'])
        for power in [.4,.65,1.]:
            weights=[max(1,d)**power for d in demand];spare=total-sum(minimum)
            seed=[m+int(spare*w/sum(weights)) for m,w in zip(minimum,weights)];seed[-1]+=total-sum(seed);seeds.append(seed)
        for _ in range(100):
            weights=[rng.random()+.03 for _ in old];spare=total-sum(minimum)
            seed=[m+int(spare*w/sum(weights)) for m,w in zip(minimum,weights)];seed[-1]+=total-sum(seed);seeds.append(seed)
        starts=sorted(seeds,key=objective)[:3]
        for start in starts:
            w=start[:];s=objective(w)
            for step in [1200,600,300,150]:
                for _ in range(40):
                    candidate=None;value=s
                    for a in range(self.n):
                        if w[a]-step<minimum[a]:continue
                        for b in range(self.n):
                            if a==b:continue
                            trial=w[:];trial[a]-=step;trial[b]+=step;v=objective(trial)
                            if v<value-.01:candidate=trial;value=v
                    if candidate is None:break
                    w=candidate;s=value
            if s<score:best=w;score=s
        before=self.estimate(old)[0];after=self.estimate(best)[0]
        if before-after<max(800,before*.025):return old[:],minimum,'보존: 최소 800 HWPUNIT 및 2.5% 높이 감소 기준 미달'
        return best,minimum,'변경: 셀 글자폭·줄간격·패딩에 따른 행별 최대높이 합 감소'

def build_plan(input_path):
    path=Path(input_path)
    with zipfile.ZipFile(path) as z:
        data=z.read(SECTION);section=ET.fromstring(data);header=ET.fromstring(z.read('Contents/header.xml'))
    tables=section.findall('.//p:tbl',NS)
    if len(tables)!=45:raise ValueError('Expected exactly 45 section2 tables')
    metrics=Metrics(header,path.with_suffix('.pdf'))
    page=section.find('.//p:pagePr',NS);margin=page.find('p:margin',NS)
    page_height=num(page,'height')-sum(num(margin,k) for k in ('top','bottom','header','footer'))
    plan={'schema_version':1,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'section_sha256':hashlib.sha256(data).hexdigest(),
          'section':SECTION,'units':'HWPUNIT (100 per pt)','page_body_height':page_height,
          'estimation':{'pdf_note':metrics.pdf_note,'pdf_pages':metrics.pdf_pages,'glyph_count':len(metrics.glyphs),
          'limitations':['Height is an estimate, never a fits verdict; HWP reflow/PDF verification required','Stored cellSz heights are lower bounds and are not decreased','Table sz height is preserved as a layout cache; coordinator must reflow in HWP','PDF glyph statistics mix font families; charPr size/ratio/spacing/relSz and paragraph spacing are applied','No current-page remaining-height prediction; full-page body threshold only']},'tables':[]}
    for i,xml in enumerate(tables):
        t=Table(xml,metrics);old=t.old;before=t.estimate(old,True)
        if i in PRESERVE or t.ambiguous:
            new=old[:];minimum=old[:];reason='보존: 설문 고유 양식/병합 격자, 폭 최적화 제외'
        else:new,minimum,reason=t.optimize(i)
        after=t.estimate(new,True)
        out=xml.find('p:outMargin',NS);available=page_height-num(out,'top')-num(out,'bottom')
        split=after['height']>available and i not in PRESERVE
        pagebreak='TABLE' if split else xml.get('pageBreak','NONE')
        headers=list(range(t.header_row+1)) if split else []
        entry={'idx':i,'id':xml.get('id'),'rows':t.rows,'cols':t.n,'headers':t.headers,'reason':reason,
               'before_widths':old,'after_widths':new,'minimum_widths':minimum,'total_width':t.total,
               'ambiguous_atomic_columns':t.ambiguous,'changed_cells':[],'before':before,'after':after,
               'estimated_height_reduction':before['height']-after['height'],'stored_table_height':num(xml.find('p:sz',NS),'height'),
               'pageBreak_before':xml.get('pageBreak'),'pageBreak_after':pagebreak,'repeat_header_rows':headers,
               'changed':new!=old or pagebreak!=xml.get('pageBreak') or bool(headers),
               'warnings':(['Single estimated row exceeds page body; row-boundary split alone cannot solve'] if after['max_row_height']>available else [])}
        if split:entry['reason']+='; 추정 실제높이가 한 쪽을 초과하여 TABLE 행경계 나눔'
        plan['tables'].append(entry)
    plan['changed_indices']=[t['idx'] for t in plan['tables'] if t['changed']]
    plan['estimation']['char_styles']={ref:ET.tostring(metrics.chars[ref],encoding='unicode') for ref in sorted(metrics.used)}
    plan['estimation']['font_faces']=metrics.faces
    # Read dispatch dumps for source traceability, without using stale/corrupt text for layout.
    for name in ['tables.json','base_paras.json']:
        f=path.parent/name
        if f.exists():
            obj=json.loads(f.read_text(encoding='utf-8-sig'))
            plan.setdefault('supporting_inputs',{})[name]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'count':len(obj.get('tables',[])) if isinstance(obj,dict) else len(obj)}
    return plan

def set_attr(tag,key,value):
    pattern=rb'(\s'+key.encode()+rb'=)([\x22\x27])[^\x22\x27]*\2'
    if re.search(pattern,tag):return re.sub(pattern,lambda m:m[1]+m[2]+str(value).encode()+m[2],tag,count=1)
    pos=tag.rfind(b'/>') if tag.endswith(b'/>') else len(tag)-1
    return tag[:pos]+b' '+key.encode()+b'="'+str(value).encode()+b'"'+tag[pos:]

def patch_table(raw,entry):
    if not entry['changed']:return raw,[]
    if len(table_spans(raw))!=1:raise ValueError('Refuse to patch nested table container')
    changes=[];new=entry['after_widths'];default=re.search(rb'<hp:inMargin\b[^>]*/>',raw)
    def attr(tag,key,default=0):
        m=re.search(rb'\b'+key.encode()+rb'="([^\"]*)"',tag)
        return int(m[1]) if m else default
    def cell_patch(m):
        cell=m[0];addr=re.search(rb'<hp:cellAddr\b[^>]*/>',cell)[0];span=re.search(rb'<hp:cellSpan\b[^>]*/>',cell)[0]
        c=attr(addr,'colAddr');r=attr(addr,'rowAddr');cs=attr(span,'colSpan',1)
        sz=re.search(rb'<hp:cellSz\b[^>]*/>',cell)[0];w=sum(new[c:c+cs]);old=attr(sz,'width')
        head=r in entry['repeat_header_rows'];changed=w!=old
        if changed:
            cell=cell.replace(sz,set_attr(sz,'width',w),1)
            opening=cell[:cell.index(b'>')+1]
            margin=re.search(rb'<hp:cellMargin\b[^>]*/>',cell)
            effective=margin if attr(opening,'hasMargin')==1 else default
            if effective is None:effective=margin
            pad=attr(effective[0],'left')+attr(effective[0],'right') if effective else 0
            # Explicit related text extent; zero originally denoted automatic extent.
            cell=re.sub(rb'<hp:subList\b[^>]*>',lambda sm:set_attr(sm[0],'textWidth',max(1,w-pad)),cell,count=1)
        if head:
            end=cell.index(b'>')+1;cell=set_attr(cell[:end],'header',1)+cell[end:]
        if changed or head:
            cell=re.sub(rb'<hp:linesegarray\b[^>]*>.*?</hp:linesegarray\s*>',b'',cell,flags=re.S)
            cell=re.sub(rb'<hp:linesegarray\b[^>]*/>',b'',cell)
            changes.append({'row':r,'column':c,'colSpan':cs,'before_width':old,'after_width':w,'header':head})
        return cell
    raw=re.sub(rb'<hp:tc\b[^>]*>.*?</hp:tc\s*>',cell_patch,raw,flags=re.S)
    end=raw.index(b'>')+1;opening=set_attr(raw[:end],'pageBreak',entry['pageBreak_after'])
    if entry['repeat_header_rows']:opening=set_attr(opening,'repeatHeader',1)
    return opening+raw[end:],changes

def apply_in_memory(data,plan):
    if hashlib.sha256(data).hexdigest()!=plan['section_sha256']:raise ValueError('Plan/source mismatch')
    spans=table_spans(data)
    if len(spans)!=len(plan['tables']):raise ValueError('Table span count mismatch')
    patches=[]
    for entry,(a,b) in zip(plan['tables'],spans):
        if entry['changed']:
            patch,changes=patch_table(data[a:b],entry);entry['changed_cells']=changes;patches.append((a,b,patch))
    for left,right in zip(patches,patches[1:]):
        if left[1]>right[0]:raise ValueError('Overlapping target tables')
    parts=[];cursor=0
    for a,b,patch in patches:parts.extend([data[cursor:a],patch]);cursor=b
    parts.append(data[cursor:]);result=b''.join(parts)
    original=ET.fromstring(data);edited=ET.fromstring(result)
    # Remove only authorized geometry/cache changes, then compare semantic trees.
    def signature(el):
        attrs=dict(el.attrib)
        if el.tag==P+'tbl':
            for key in ['pageBreak','repeatHeader']:attrs.pop(key,None)
        if el.tag==P+'tc':attrs.pop('header',None)
        if el.tag==P+'cellSz':attrs.pop('width',None)
        if el.tag==P+'subList':attrs.pop('textWidth',None)
        return el.tag,sorted(attrs.items()),el.text,el.tail,tuple(signature(c) for c in el if c.tag!=P+'linesegarray')
    if signature(original)!=signature(edited):raise ValueError('Non-geometric XML mutation')
    plan['verification']={'xml_parses':True,'text_styles_and_cell_heights_preserved':True,
                           'outside_target_tables_byte_identical':True,'only_zip_entry_to_replace':SECTION,
                           'actual_hwp_reflow_verified':False}
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if len({p.resolve() for p in [args.input,args.output,args.report]})!=3:raise ValueError('Input, output and report must differ')
    if args.output.exists():raise FileExistsError('Refuse to overwrite existing output')
    plan=build_plan(args.input)
    with zipfile.ZipFile(args.input) as src:
        result=apply_in_memory(src.read(SECTION),plan)
        with zipfile.ZipFile(args.output,'x') as dst:
            dst.comment=src.comment
            for info in src.infolist():dst.writestr(info,result if info.filename==SECTION else src.read(info.filename))
    with zipfile.ZipFile(args.input) as src,zipfile.ZipFile(args.output) as dst:
        changed=[n for n in src.namelist() if src.read(n)!=dst.read(n)]
        if changed!=[SECTION]:raise ValueError('Unexpected ZIP changes: '+str(changed))
    plan['verification']['changed_zip_entries']=changed
    args.report.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'changed_indices':plan['changed_indices'],'report':str(args.report)},ensure_ascii=False))

if __name__=='__main__':
    main()
