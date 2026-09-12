"""Read-only source loading and in-memory surgical XML fragments; never writes files.

Indices are original preorder indices, including table-cell paragraphs. Reuse ONE
instance for the whole patch (ID allocation and appended header styles are shared).
Caller performs lexical fragment substitution and ZIP writing, then Hancom/PDF QA.
"""
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path
import math
import os
import re
import zipfile
from lxml import etree as E

P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H = '{http://www.hancom.co.kr/hwpml/2011/head}'
MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]')
# Only physical/count/statistical units, not every semantic parenthesis.
UNIT = re.compile(r'^(.*?)\s*(\((?:단위\s*:[^()]+|%|명|개|건|회|점|년|개월|월|일|시간|분|초|원|만원|억원|m|m²|㎡|mm|cm|kg|Hz|fps|ms|s|N|n)\))$')

def own(p):
    return ''.join(t.text or '' for r in p.findall(P+'run') for t in r.findall(P+'t'))

def _bytes(node):
    return E.tostring(node, encoding='UTF-8', with_tail=False)

def _plain(p):
    allowed = {P+n for n in ('p', 'run', 't', 'linesegarray', 'lineseg')}
    bad = [E.QName(n).localname for n in p.iter() if n.tag not in allowed]
    if bad:
        raise ValueError('Complex paragraph controls cannot be discarded: '+repr(bad))

def _cache(p):
    for n in list(p.findall(P+'linesegarray')):
        p.remove(n)

class Surgical:
    def __init__(self, base_path):
        with zipfile.ZipFile(base_path, 'r') as z:
            self.data = {n: z.read(n) for n in z.namelist()}
        parser = E.XMLParser(resolve_entities=False, no_network=True)
        self.roots = {n:E.fromstring(v, parser) for n,v in self.data.items() if n.endswith('.xml')}
        self.paras = {n:list(r.iter(P+'p')) for n,r in self.roots.items() if re.fullmatch(r'Contents/section\d+\.xml',n)}
        self.tables = {n:list(self.roots[n].iter(P+'tbl')) for n in self.paras}
        self.header = self.roots['Contents/header.xml']
        self.chars = {n.get('id'):n for n in self.header.iter(H+'charPr')}
        self._ids = {int(n.get('id')) for r in self.roots.values() for n in r.iter() if (n.get('id') or '').isdigit()}
        self._next = max(self._ids, default=0)+1
        self.estimates = []
        self._font = None
        self.font_measurement = 'uninitialized'

    def _id(self):
        if self._next >= 2**32:
            raise ValueError('32-bit object ID space exhausted')
        n=self._next; self._next+=1; self._ids.add(n)
        return str(n)

    def _color(self, cid, color):
        source=self.chars[cid]
        def key(n):
            c=deepcopy(n); c.attrib.pop('id',None); c.attrib.pop('textColor',None)
            return E.tostring(c,method='c14n')
        k=key(source)
        for i,n in self.chars.items():
            if n.get('textColor','').upper()==color and key(n)==k:
                return i
        c=deepcopy(source); i=str(max(map(int,self.chars))+1)
        c.set('id',i); c.set('textColor',color); source.getparent().append(c)
        self.chars[i]=c
        return i

    def _edit(self, p, text, new=False):
        if not isinstance(text,str): raise TypeError('Text must be str')
        _plain(p)
        old=own(p); styles=[]; runs={}
        for r in p.findall(P+'run'):
            cid=r.get('charPrIDRef'); runs.setdefault(cid,r)
            styles.extend([cid]*sum(len(t.text or '') for t in r.findall(P+'t')))
        fallback=next(iter(runs), next(iter(self.chars)))
        out=[fallback]*len(text)
        for op,a,b,c,d in SequenceMatcher(None,old,text,autojunk=False).get_opcodes():
            if op=='equal': out[c:d]=styles[a:b]
            elif op in ('replace','insert'): out[c:d]=[styles[min(a,len(styles)-1)] if styles else fallback]*(d-c)
        marked={i for m in MARK.finditer(text) for i in range(m.start(),m.end())}
        original=list(out)
        for i,cid in enumerate(out):
            if i in marked: out[i]=self._color(cid,'#FF0000')
            elif self.chars[cid].get('textColor','').upper()=='#FF0000': out[i]=self._color(cid,'#000000')
        q=deepcopy(p)
        for child in list(q): q.remove(child)
        if new: q.set('id',self._id()); q.set('pageBreak','0'); q.set('columnBreak','0')
        a=0
        while a<len(text):
            b=a+1
            while b<len(text) and (out[b],original[b])==(out[a],original[a]): b+=1
            r=deepcopy(runs[original[a]]) if original[a] in runs else E.Element(P+'run')
            for child in list(r): r.remove(child)
            r.set('charPrIDRef',out[a]); E.SubElement(r,P+'t').text=text[a:b]; q.append(r); a=b
        if not text:
            r=E.SubElement(q,P+'run',charPrIDRef=fallback); E.SubElement(r,P+'t')
        return q

    def edit_paragraph(self, section, idx, new_text, new=False):
        return _bytes(self._edit(self.paras[section][idx],new_text,new))

    def _load_font(self):
        if self.font_measurement!='uninitialized': return
        try:
            from PIL import ImageFont
            folders=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts']
            for env in ('ProgramFiles(x86)','ProgramFiles'):
                folders.append(Path(os.environ.get(env,'C:/'+('Program Files (x86)' if 'x86' in env else 'Program Files')))/'Hnc')
            for folder in folders:
                if not folder.exists(): continue
                for path in folder.rglob('*'):
                    if path.suffix.lower() not in ('.ttf','.otf','.ttc'): continue
                    try:
                        f=ImageFont.truetype(str(path),1000)
                        name=' '.join(f.getname())
                        if '신명조' in name or 'sinmyeong' in name.lower() or 'shinmy' in name.lower():
                            self._font=f; self.font_measurement='Pillow actual '+name+' '+str(path); return
                    except (OSError,ValueError): pass
            path=folders[0]/'batang.ttc'
            self._font=ImageFont.truetype(str(path),1000)
            self.font_measurement='Pillow substitute Batang; Hanyang Sinmyeongjo file unavailable: '+str(path)
        except (ImportError,OSError):
            self.font_measurement='Fallback estimated em widths (CJK=1em, ASCII=0.6em); Pillow/font unavailable'

    def _width(self, text, cid):
        self._load_font(); cp=self.chars[cid]; size=int(cp.get('height','1000'))
        ratio=cp.find(H+'ratio'); spacing=cp.find(H+'spacing')
        result=0
        for ch in text:
            lang='hangul' if '\uac00'<=ch<='\ud7a3' else 'latin'
            factor=float(ratio.get(lang,'100'))/100 if ratio is not None else 1
            gap=float(spacing.get(lang,'0'))/100 if spacing is not None else 0
            w=self._font.getlength(ch)/1000 if self._font else (1 if ord(ch)>255 else .6)
            result+=(w*factor+gap)*size
        return max(0,result)

    def _height(self, cell, width):
        margin=cell.find(P+'cellMargin'); pad=lambda k:int(margin.get(k,'0')) if margin is not None else 0
        available=width-pad('left')-pad('right')
        if available<=0: raise ValueError('Cell width is smaller than margins')
        height=pad('top')+pad('bottom')
        for p in cell.find(P+'subList').findall(P+'p'):
            runs=p.findall(P+'run'); cid=runs[0].get('charPrIDRef')
            size=max(int(self.chars[r.get('charPrIDRef')].get('height','1000')) for r in runs)
            lines=1; used=0
            for r in runs:
                for ch in own_run(r):
                    w=self._width(ch,r.get('charPrIDRef'))
                    if ch=='\n': lines+=1; used=0
                    elif used+w>available and used: lines+=1; used=w
                    else: used+=w
            pp=next((n for n in self.header.iter(H+'paraPr') if n.get('id')==p.get('paraPrIDRef')),None)
            ls=next(iter(pp.iter(H+'lineSpacing')),None) if pp is not None else None
            advance=size*1.6
            if ls is not None:
                value=float(ls.get('value','160')); kind=ls.get('type')
                if kind=='PERCENT': advance=size*value/100
                elif kind=='FIXED': advance=value
                elif kind=='AT_LEAST': advance=max(size,value)
            height+=lines*max(size,advance)
            if pp is not None:
                for n in pp.iter():
                    if E.QName(n).localname in ('prev','next'): height+=float(n.get('value','0'))
        return math.ceil(height*1.1)

    def table_fragment(self, section, table_idx, header, rows, weights, caption=None):
        header=list(header); rows=[list(r) for r in rows]; n=len(header)
        if not n or any(len(r)!=n for r in rows): raise ValueError('Nonrectangular table')
        if any(not isinstance(v,str) for r in [header]+rows for v in r): raise TypeError('Cells must be strings')
        if caption is not None and not isinstance(caption,str): raise TypeError('caption must be str or None')
        src=self.tables[section][table_idx]
        if len(list(src.iter(P+'tbl')))!=1: raise ValueError('Nested tables require a dedicated plan')
        for p in src.iter(P+'p'): _plain(p)
        allowed={P+x for x in ('tbl','sz','pos','outMargin','inMargin','tr','tc','subList','p','run','t','linesegarray','lineseg','cellAddr','cellSpan','cellSz','cellMargin')}
        if any(x.tag not in allowed for x in src.iter()): raise ValueError('Unsupported table control/metadata')
        trs=src.findall(P+'tr'); first=trs[0].findall(P+'tc')
        merged=len(first)==1 and int(first[0].find(P+'cellSpan').get('colSpan'))==int(src.get('colCnt'))
        head_cells=trs[1 if merged else 0].findall(P+'tc')
        body_cells=trs[min(2 if merged else 1,len(trs)-1)].findall(P+'tc')
        total=int(src.find(P+'sz').get('width'))
        if weights is None:
            scores=[]
            for j in range(n):
                cid=head_cells[min(j,len(head_cells)-1)].find('.//'+P+'run').get('charPrIDRef')
                scores.append(max(1500, max(self._width(r[j],cid) for r in [header]+rows))**.65)
        else:
            scores=list(map(float,weights))
            if len(scores)!=n or any(not math.isfinite(v) or v<=0 for v in scores): raise ValueError('Invalid weights')
        exact=[total*v/sum(scores) for v in scores]; widths=[int(v) for v in exact]
        for j in sorted(range(n),key=lambda j:exact[j]-widths[j],reverse=True)[:total-sum(widths)]: widths[j]+=1
        if min(widths)<=0: raise ValueError('Zero column width')
        tbl=deepcopy(src); tbl.set('id',self._id())
        for tr in tbl.findall(P+'tr'): tbl.remove(tr)
        records=([(True,[caption])] if caption is not None else [])+[(True,header)]+[(False,r) for r in rows]
        heights=[]
        for row_idx,(ishead,values) in enumerate(records):
            tr=E.SubElement(tbl,P+'tr'); captionrow=caption is not None and row_idx==0
            for j,value in enumerate(values):
                templates=head_cells if ishead else body_cells
                template=first[0] if captionrow and merged else templates[min(j,len(templates)-1)]
                tc=deepcopy(template); sub=tc.find(P+'subList'); ps=sub.findall(P+'p')
                if not ps: raise ValueError('Missing paragraph template')
                for child in list(sub): sub.remove(child)
                sub.set('textWidth','0'); sub.set('textHeight','0')
                parts=value.split('\n')
                if ishead and not captionrow:
                    parts=[part for s in parts for part in (list(UNIT.fullmatch(s).groups()) if UNIT.fullmatch(s) else [s])]
                for part in parts: sub.append(self._edit(ps[0],part,True))
                tc.set('header','1' if ishead else '0')
                span=n if captionrow else 1; width=total if captionrow else widths[j]
                tc.find(P+'cellAddr').attrib.update({'colAddr':str(j),'rowAddr':str(row_idx)})
                tc.find(P+'cellSpan').attrib.update({'colSpan':str(span),'rowSpan':'1'})
                tc.find(P+'cellSz').set('width',str(width)); tr.append(tc)
            height=max(self._height(tc,int(tc.find(P+'cellSz').get('width'))) for tc in tr)
            heights.append(height)
            for tc in tr: tc.find(P+'cellSz').set('height',str(height))
        page=next(self.roots[section].iter(P+'pagePr'),None)
        if page is None: raise ValueError('No pagePr: cannot estimate full-page fit')
        margin=page.find(P+'margin')
        available=int(page.get('height'))-sum(int(margin.get(k,'0')) for k in ('top','bottom','header','footer'))
        if max(heights)>available: raise ValueError('A single row exceeds estimated full-page height; structure needs review')
        estimated=sum(heights)+int(tbl.get('cellSpacing','0'))*max(0,len(heights)-1)
        split=estimated>available-2000
        header_count=2 if caption is not None else 1
        if split and sum(heights[:header_count])+max(heights[header_count:],default=0)>available-2000:
            raise ValueError('Repeated header plus one body row exceeds estimated page; structure needs review')
        tbl.set('rowCnt',str(len(records))); tbl.set('colCnt',str(n))
        tbl.set('pageBreak','TABLE' if split else 'NONE'); tbl.set('repeatHeader','1' if split else '0')
        tbl.find(P+'pos').set('treatAsChar','0' if split else '1')
        tbl.find(P+'sz').set('height',str(estimated))
        self.estimates.append(dict(section=section,table_idx=table_idx,widths=widths,total_width=total,estimated_height=estimated,available_height=available,pageBreak=tbl.get('pageBreak'),font=self.font_measurement,estimated_only=True))
        return _bytes(tbl)

    def wrap_table(self, section, anchor_idx, table_xml, new=False):
        p=deepcopy(self.paras[section][anchor_idx])
        candidates=[t for r in p.findall(P+'run') for t in r.findall(P+'tbl')]
        if len(candidates)!=1: raise ValueError('Anchor must own exactly one table')
        old=candidates[0]; replacement=E.fromstring(table_xml)
        if replacement.tag!=P+'tbl': raise ValueError('Expected table fragment')
        probe=deepcopy(p)
        for r in probe.findall(P+'run'):
            for t in r.findall(P+'tbl'): r.remove(t)
        _plain(probe)
        if new:
            # Cloning another object/control would duplicate its IDs and semantics.
            p.set('id',self._id()); p.set('pageBreak','0'); p.set('columnBreak','0')
            for node in replacement.iter():
                if node.tag in (P+'p',P+'tbl'): node.set('id',self._id())
        old.getparent().replace(old,replacement); _cache(p)
        return _bytes(p)

    def header_bytes(self):
        parent=next(iter(self.chars.values())).getparent()
        parent.set('itemCnt',str(len(parent.findall(H+'charPr'))))
        return E.tostring(self.header,encoding='UTF-8',xml_declaration=True,standalone=True)

def own_run(r):
    return ''.join(t.text or '' for t in r.findall(P+'t'))
