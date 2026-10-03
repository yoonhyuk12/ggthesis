"""Main-context-only surgical transfer; no whole-document reconstruction."""
from pathlib import Path
import copy, collections, difflib, hashlib, html, json, re, sys, zipfile
from lxml import etree as E
from PIL import ImageFont
Q=Path(__file__).resolve().parent
ROOT=Q.parents[3]
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H='{http://www.hancom.co.kr/hwpml/2011/head}'
C='{http://www.hancom.co.kr/hwpml/2011/core}'
MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')

def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def xml(e):
    value=E.tostring(e,encoding='utf-8',with_tail=False)
    value=re.sub(rb'\sxmlns(?::[\w-]+)?="[^"]*"',b'',value)
    assert b'ns0:' not in value
    return value
def dump(v,path):path.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

class Transfer:
    def __init__(self):
        self.original=(Q/'base.hwpx').read_bytes()
        with zipfile.ZipFile(Q/'base.hwpx') as z:self.entries={n:z.read(n) for n in z.namelist()}
        self.head=E.fromstring(self.entries['Contents/header.xml'])
        self.chars={c.get('id'):c for c in self.head.iter(H+'charPr')}
        self.used_ids=set(int(x) for data in self.entries.values() if data.startswith(b'<?xml') for x in re.findall(rb'\bid="(\d+)"',data))
        self.fresh=900000000;self.added_chars=[];self.report={'replacements':[],'tables':[],'inserts':[],'deletions':[],'font_measurement':[]}
    def uid(self):
        while self.fresh in self.used_ids:self.fresh+=1
        v=str(self.fresh);self.used_ids.add(self.fresh);self.fresh+=1;return v
    def black(self,cid):
        if self.chars[cid].get('textColor','').upper()!='#FF0000':return cid
        return self.colored(cid,'#000000')
    def colored(self,cid,color):
        src=self.chars[cid]
        for k,other in self.chars.items():
            if other.get('textColor','').upper()!=color:continue
            a=copy.deepcopy(src);b=copy.deepcopy(other)
            for el in (a,b):el.attrib.pop('id',None);el.attrib.pop('textColor',None)
            if E.tostring(a,method='c14n')==E.tostring(b,method='c14n'):return k
        out=copy.deepcopy(src);nid=str(max(map(int,self.chars))+1);out.set('id',nid);out.set('textColor',color)
        src.getparent().append(out);src.getparent().set('itemCnt',str(len(src.getparent())))
        self.chars[nid]=out;self.added_chars.append(nid);return nid
    def paragraph(self,template,text,new=False):
        p=copy.deepcopy(template);old=own(p)
        assert p.find('.//'+P+'tbl') is None and p.find('.//'+P+'pic') is None and p.find('.//'+P+'equation') is None,'object paragraph needs explicit handling'
        old_styles=[]
        for r in p.findall(P+'run'):
            old_styles.extend([r.get('charPrIDRef')]*sum(len(''.join(t.itertext())) for t in r.findall(P+'t')))
        ids=[x for x in old_styles if self.chars[x].get('textColor','').upper()!='#FF0000']
        default=self.black(collections.Counter(ids or old_styles or [p.find(P+'run').get('charPrIDRef','9') if p.find(P+'run') is not None else '9']).most_common(1)[0][0])
        new_styles=[default]*len(text)
        for tag,a,b,c,d in difflib.SequenceMatcher(None,old,text,autojunk=False).get_opcodes():
            if tag=='equal':new_styles[c:d]=old_styles[a:b]
        new_styles=[self.black(cid) for cid in new_styles]
        for m in MARK.finditer(text):
            for i in range(m.start(),m.end()):new_styles[i]=self.colored(self.black(new_styles[i]),'#FF0000')
        # Preserve actual TOC tab controls; their leader geometry is in paraPr.
        tabs=list(p.iter(P+'tab'))
        saved_tab=copy.deepcopy(tabs[0]) if tabs else None
        preserved=[]
        for r in p.findall(P+'run'):
            for child in r:
                if child.tag!=P+'t':
                    rr=E.Element(P+'run',charPrIDRef=r.get('charPrIDRef',default));rr.append(copy.deepcopy(child));preserved.append(rr)
            p.remove(r)
        for cache in p.findall(P+'linesegarray'):p.remove(cache)
        for r in preserved:p.append(r)
        if saved_tab is not None and not new:
            match=re.search(r'(\d+)\s*$',text);assert match,'TOC folio absent'
            r=E.SubElement(p,P+'run',charPrIDRef=default);t=E.SubElement(r,P+'t');t.text=text[:match.start()];t.append(saved_tab);saved_tab.tail=match.group(1)
        else:
            if not text:new_styles=[]
            start=0
            while start<len(text):
                stop=start+1
                while stop<len(text) and new_styles[stop]==new_styles[start]:stop+=1
                r=E.SubElement(p,P+'run',charPrIDRef=new_styles[start]);E.SubElement(r,P+'t').text=text[start:stop];start=stop
            if not text:E.SubElement(E.SubElement(p,P+'run',charPrIDRef=default),P+'t')
        if new:
            for r in preserved:p.remove(r)
            p.set('id',self.uid());p.set('pageBreak','0');p.set('columnBreak','0')
        assert own(p)==text,(own(p),text)
        return p
    def widths(self,rows,total,template):
        n=max(map(len,rows))
        if n==8 and any(re.match(r'[DE]-\d',row[0]) for row in rows if row):
            # Preserve a wide question column; equal widths apply only to the response grid.
            weights=[7,55,5,5,5,5,5,13]
        else:
            cells=[c for tr in template.findall(P+'tr') for c in tr.findall(P+'tc')]
            cp=next((p for c in cells for p in c.iter(P+'p') if own(p)),None)
            cid=cp.find(P+'run').get('charPrIDRef') if cp is not None else '9'
            char=self.chars[cid];height=int(char.get('height','1000'))
            fid=char.find(H+'fontRef').get('hangul','0')
            face=next(f for f in self.head.iter(H+'fontface') if f.get('lang')=='HANGUL').findall(H+'font')[int(fid)].get('face')
            fontfiles=list(Path('C:/Windows/Fonts').glob('*Batang*'))+list(Path('C:/Windows/Fonts').glob('*batang*'))
            actual=next((f for f in fontfiles if 'han' in f.name.lower()),None) if face in ('한컴바탕','함초롬바탕') else None
            fontpath=actual or Path('C:/Windows/Fonts/malgun.ttf')
            font=ImageFont.truetype(str(fontpath),100)
            measure=lambda s:font.getlength(s)*height/100
            weights=[]
            for j in range(n):
                values=[row[j].replace('\n',' ') for row in rows if len(row)==n]
                ideal=max((measure(s) for s in values),default=height*3)+height
                if all(len(s)<18 for s in values):ideal=min(ideal,height*9)
                weights.append(max(height*3,min(ideal,height*36)**.74*height**.26))
            # Limit long explanatory columns to a readable share; the PDF supplies the final check.
            lo=max(weights)*.12
            weights=[max(w,lo) for w in weights]
            self.report['font_measurement'].append({'family':face,'file':str(fontpath),'fallback_estimate':actual is None,'char_height':height,'columns':n})
        widths=[round(total*w/sum(weights)) for w in weights];widths[-1]+=total-sum(widths)
        return widths
    def table(self,template,rows,table_label):
        if len(rows[0])==7 and len(rows[1])==8 and re.match(r'[DE]-\d',rows[1][0]):
            return self.survey_table(template,rows,table_label)
        t=copy.deepcopy(template);oldrows=t.findall(P+'tr');assert oldrows
        width=int(t.find(P+'sz').get('width'));n=max(map(len,rows));ws=self.widths(rows,width,t)
        title=bool(rows and len(rows[0])==1 and n>1)
        for tr in oldrows:t.remove(tr)
        oldhead=list(oldrows[0].findall(P+'tc'));oldbody=list(oldrows[min(1,len(oldrows)-1)].findall(P+'tc'))
        if len(oldbody)==1 and len(oldrows)>2:oldbody=list(oldrows[2].findall(P+'tc'))
        header_index=1 if title else 0
        row_heights=[]
        for ri,row in enumerate(rows):
            assert len(row) in (1,n),(table_label,ri,len(row),n)
            tr=E.SubElement(t,P+'tr');head=ri<=header_index
            for ci,value in enumerate(row):
                candidates=oldhead if head and len(oldhead)>1 else oldbody
                if len(row)==1:candidates=oldhead
                tc=copy.deepcopy(candidates[min(ci,len(candidates)-1)])
                tc.set('header','1' if head else '0');tc.set('name','');tc.set('hasMargin','1')
                span=n if len(row)==1 else 1
                tc.find(P+'cellAddr').set('rowAddr',str(ri));tc.find(P+'cellAddr').set('colAddr',str(ci))
                tc.find(P+'cellSpan').set('rowSpan','1');tc.find(P+'cellSpan').set('colSpan',str(span))
                sz=tc.find(P+'cellSz');sz.set('width',str(sum(ws[ci:ci+span])));sz.set('height','1600')
                sub=tc.find(P+'subList');existing=list(sub.findall(P+'p'));proto=next((p for p in existing if own(p)),existing[0])
                for p in existing:sub.remove(p)
                lines=value.split('\n')
                if head and len(lines)==1:
                    mm=re.fullmatch(r'(.+?)(\([^()]{1,7}\))',value)
                    if mm:lines=[mm.group(1),mm.group(2)]
                for line in lines:sub.append(self.paragraph(proto,line,new=True))
                tr.append(tc)
            row_heights.append(1600)
        t.set('rowCnt',str(len(rows)));t.set('colCnt',str(n));t.set('pageBreak','TABLE');t.set('repeatHeader','1');t.set('noAdjust','0');t.set('id',self.uid())
        t.find(P+'sz').set('height',str(sum(row_heights)))
        # Splitting is provisionally enabled; actual page/row continuity is checked after reflow.
        pos=t.find(P+'pos')
        if pos is not None:pos.set('treatAsChar','0')
        self.report['tables'].append({'label':table_label,'rows':len(rows),'cols':n,'width':width,'column_widths':ws})
        return t
    def survey_table(self,template,rows,table_label):
        t=copy.deepcopy(template);trs=t.findall(P+'tr');assert len(trs)==len(rows)
        width=int(t.find(P+'sz').get('width'))
        body=trs[1].findall(P+'tc');lead=[int(c.find(P+'cellSz').get('width')) for c in body[:2]]
        na=3500;available=width-sum(lead)-na
        responses=[available//5]*5;responses[-1]+=available-sum(responses)
        logical=lead[:]
        for w in responses+[na]:logical.extend([w//2,w-w//2])
        for ri,(tr,values) in enumerate(zip(trs,rows)):
            cells=tr.findall(P+'tc');cells.append(copy.deepcopy(cells[-1]));tr.append(cells[-1])
            assert len(cells)==len(values)
            for ci,(tc,value) in enumerate(zip(cells,values)):
                ca=0 if ci==0 else 2*ci if ri==0 else ci if ci<2 else 2*(ci-1)
                span=2 if ri==0 or ci>=2 else 1
                tc.find(P+'cellAddr').set('colAddr',str(ca));tc.find(P+'cellAddr').set('rowAddr',str(ri))
                tc.find(P+'cellSpan').set('colSpan',str(span));tc.find(P+'cellSpan').set('rowSpan','1')
                tc.find(P+'cellSz').set('width',str(sum(logical[ca:ca+span])))
                tc.set('header','1' if ri==0 else '0')
                sub=tc.find(P+'subList');paras=sub.findall(P+'p');proto=next((p for p in paras if own(p)),paras[0])
                for p in paras:sub.remove(p)
                for line in value.split('\n'):sub.append(self.paragraph(proto,line,new=True))
        t.set('colCnt','14');t.set('repeatHeader','1')
        self.report['tables'].append({'label':table_label,'rows':len(rows),'cols':14,'width':width,'column_widths':logical,'preserved_survey_merges':True})
        return t
    def main(self,outname):
        plans=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(Q.glob('plan_*.json'))]
        assert len(plans)==3,'Wait for all three scoped plans'
        changes={}
        for sec in ['Contents/section0.xml','Contents/section1.xml','Contents/section2.xml']:
            raw=self.entries[sec];root=E.fromstring(raw);ps=list(root.iter(P+'p'));ts=list(root.iter(P+'tbl'))
            nodes=elements(raw);pns=[n for n in nodes if n['name']=='hp:p'];tns=[n for n in nodes if n['name']=='hp:tbl']
            edits=[];changed_paras=set();whole_tables=set();inserts=collections.defaultdict(list)
            for plan in plans:
                for c in plan.get('replace_tables',[]):
                    if c['section']!=sec:continue
                    ti=c['table_idx'];assert ti not in whole_tables;whole_tables.add(ti)
                    oldrows=[['\n'.join(own(p) for p in tc.find(P+'subList').findall(P+'p')).strip() for tc in tr.findall(P+'tc')] for tr in ts[ti].findall(P+'tr')]
                    assert [[x.strip() for x in row] for row in oldrows]==[[x.strip() for x in row] for row in c['old_rows']],(sec,ti,'table old rows mismatch')
                    nt=self.table(ts[ti],c['new_rows'],f'{sec}:table{ti}');node=tns[ti];edits.append((node['start'],node['end'],xml(nt)))
                    for anc in ts[ti].iterancestors(P+'p'):changed_paras.add(ps.index(anc))
            for plan in plans:
                for c in plan.get('replace',[]):
                    if c['section']!=sec:continue
                    i=c['idx'];assert own(ps[i])==c['old_hwpx'],(sec,i,'old mismatch')
                    assert not any(a is ts[ti] for a in ps[i].iterancestors() for ti in whole_tables),'overlapping paragraph/table edits'
                    np=self.paragraph(ps[i],c['new']);node=pns[i];edits.append((node['start'],node['end'],xml(np)));changed_paras.add(i)
                    for a in ps[i].iterancestors(P+'p'):changed_paras.add(ps.index(a))
                    self.report['replacements'].append({'section':sec,'idx':i,'old':c['old_hwpx'],'new':c['new']})
                for c in plan.get('remove_paragraphs',[]):
                    if c['section']!=sec:continue
                    i=c['idx'];assert own(ps[i])==c['old_hwpx']
                    assert not any(ps[i].iter(P+'pic')) and not any(ps[i].iter(P+'tbl'))
                    node=pns[i];edits.append((node['start'],node['end'],b''));self.report['deletions'].append(c)
                for c in plan.get('insert_after',[]):
                    if c['section']!=sec:continue
                    i=c['idx']
                    for a in ps[i].iterancestors(P+'p'):changed_paras.add(ps.index(a))
                    for block in c['blocks']:
                        assert block['kind']=='paragraph'
                        hint=block.get('style_hint','body')
                        # A clean text template prevents copying hyperlink/control objects into new text.
                        candidates=[p for p in ps[max(0,i-12):i+1] if p.getparent() is root and own(p).strip() and p.find('.//'+P+'tbl') is None and p.find('.//'+P+'pic') is None and p.find('.//'+P+'ctrl') is None]
                        default_body=next(p for p in ps if p.getparent() is root and len(own(p))>150 and p.find('.//'+P+'tbl') is None and p.find('.//'+P+'pic') is None and p.find('.//'+P+'ctrl') is None)
                        template=next((p for p in reversed(candidates) if len(own(p))>65),default_body)
                        if ps[i].getparent() is not root:template=ps[i]
                        if hint=='heading':template=next((p for p in reversed(candidates) if 3<len(own(p))<60),template)
                        np=self.paragraph(template,block['text'],new=True)
                        if sec=='Contents/section2.xml' and i in (2266,2536) and block is c['blocks'][0]:np.set('pageBreak','1')
                        if hint=='heading':
                            blank=self.paragraph(template,'',new=True);inserts[pns[i]['end']].append(xml(blank))
                        inserts[pns[i]['end']].append(xml(np));self.report['inserts'].append({'section':sec,'after_idx':i,'text':block['text']})
                for c in plan.get('insert_tables',[]):
                    if c['section']!=sec:continue
                    i=c['after_idx'];assert ps[i].getparent() is root
                    template=ts[c['template_table_idx']];nt=self.table(template,c['rows'],f'insert after {sec}:{i}')
                    # Clone only the existing table's anchor paragraph styling, without its content.
                    oldanchor=next(a for a in template.iterancestors(P+'p') if a.getparent() is root)
                    np=E.Element(P+'p',nsmap=oldanchor.nsmap,attrib=dict(oldanchor.attrib));np.set('id',self.uid());np.set('pageBreak','0')
                    nr=E.SubElement(np,P+'run',charPrIDRef=oldanchor.find(P+'run').get('charPrIDRef','9'));nr.append(nt)
                    inserts[pns[i]['end']].append(xml(np))
            # Remove each affected enclosing paragraph's own line cache unless already replaced.
            for i in changed_paras:
                node=pns[i]
                for n in nodes:
                    if n['name']=='hp:linesegarray' and n['parent'] is node:
                        if not any(a<=n['start'] and b>=n['end'] for a,b,_ in edits):edits.append((n['start'],n['end'],b''))
            edits.extend((pos,pos,b''.join(values)) for pos,values in inserts.items())
            edits.sort(key=lambda x:(x[0],x[1]));cursor=0;parts=[]
            for a,b,val in edits:
                assert a>=cursor,(sec,'overlapping edits',a,cursor)
                parts.extend((raw[cursor:a],val));cursor=b
            parts.append(raw[cursor:]);patched=b''.join(parts);E.fromstring(patched)
            if patched!=raw:changes[sec]=patched
        if self.added_chars:changes['Contents/header.xml']=E.tostring(self.head,encoding='utf-8',xml_declaration=True,standalone=True)
        # Preserve picture geometry and embedding IDs; replace only the two design assets.
        for bid,asset in [('image1','flow_current.png'),('image6','model_current.png')]:
            matches=[n for n in self.entries if re.fullmatch(r'BinData/'+bid+r'\.[^.]+',n)]
            assert len(matches)==1 and matches[0].lower().endswith('.png'),matches
            changes[matches[0]]=(Q/asset).read_bytes()
        out=Q/outname;assert not out.exists();out.write_bytes(raw_zip_patch(self.original,changes))
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None
            for n in z.namelist():
                if n.endswith('.xml'):E.fromstring(z.read(n))
            assert set(z.namelist())==set(self.entries)
            assert all(z.read(n)==self.entries[n] for n in self.entries if n not in changes)
        self.report['changed_entries']=list(changes);self.report['added_char_styles']=self.added_chars
        self.report['candidate_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
        dump(self.report,Q/'transfer_evidence.json')
        print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in self.report.items()},ensure_ascii=False,indent=2))

if __name__=='__main__':Transfer().main(sys.argv[1])
