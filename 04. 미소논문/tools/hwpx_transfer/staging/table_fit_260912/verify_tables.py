"""Read-only HWPX/PDF table checks. No HWPX writes or office automation.

python verify_tables.py --base base.hwpx --candidate candidate.hwpx --pdf candidate.pdf
Use --resaved only after Hancom re-pagination: layout caches/IDs may change;
outside-table semantic XML, character formatting and paragraph formatting still compare.
--audit writes the JSON audit to stdout (redirect only to table_audit.json).
Exit 1 means a preservation/grid/PDF check failed, not an execution failure.
"""
import argparse
import collections
import copy
import hashlib
import json
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pymupdf

NS = {'p': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'h': 'http://www.hancom.co.kr/hwpml/2011/head'}
P = '{' + NS['p'] + '}'
MARKER = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]')

def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))

def text(e):
    return ''.join(t.text or '' for t in e.iter(P+'t'))

def canonical(e):
    return (e.tag, tuple(sorted(e.attrib.items())), (e.text or '').strip(), tuple(canonical(c) for c in e))

def read_hwpx(path):
    with zipfile.ZipFile(path) as z:
        entries = {n: z.read(n) for n in z.namelist()}
    roots = {n: ET.fromstring(b) for n,b in entries.items() if re.match(r'Contents/section\d+\.xml$',n)}
    header = ET.fromstring(entries['Contents/header.xml'])
    chars = {e.get('id'): e for e in header.findall('.//h:charPr', NS)}
    paras = {e.get('id'): e for e in header.findall('.//h:paraPr', NS)}
    tables = list(roots['Contents/section2.xml'].iter(P+'tbl'))
    return {'entries':entries,'roots':roots,'header':header,'chars':chars,'paras':paras,'tables':tables}

def cells(t):
    return [c for r in t.findall('p:tr',NS) for c in r.findall('p:tc',NS)]

def info(c):
    a=c.find('p:cellAddr',NS); s=c.find('p:cellSpan',NS); z=c.find('p:cellSz',NS)
    return tuple(int(a.get(k)) for k in ('rowAddr','colAddr'))+tuple(int(s.get(k)) for k in ('rowSpan','colSpan'))+(int(z.get('width')),int(z.get('height')))

def grid(t):
    n=int(t.get('colCnt')); width=int(t.find('p:sz',NS).get('width'))
    edges={0:0,n:width}; equations=[(info(c)[1],info(c)[3],info(c)[4]) for c in cells(t)]
    for _ in range(n+1):
        for col,span,w in equations:
            if col in edges and col+span not in edges: edges[col+span]=edges[col]+w
            elif col+span in edges and col not in edges: edges[col]=edges[col+span]-w
    errors=[]
    for col,span,w in equations:
        if col in edges and col+span in edges and abs(edges[col+span]-edges[col]-w)>2:
            errors.append({'col':col,'span':span,'width':w,'grid_width':edges[col+span]-edges[col]})
    if len(edges)!=n+1: errors.append({'underdetermined_edges':sorted(set(range(n+1))-set(edges))})
    widths=[edges.get(i+1,0)-edges.get(i,0) for i in range(n)]
    if any(w<=0 for w in widths): errors.append({'nonpositive_widths':widths})
    occupied=set()
    for c in cells(t):
        r,col,rs,cs,_,_=info(c)
        for rr in range(r,r+rs):
            for cc in range(col,col+cs):
                if (rr,cc) in occupied or rr>=int(t.get('rowCnt')) or cc>=n: errors.append({'invalid_coverage':[rr,cc]})
                occupied.add((rr,cc))
    if len(occupied)!=n*int(t.get('rowCnt')): errors.append({'incomplete_coverage':len(occupied)})
    return widths,errors

def marker_colors(doc, root):
    out=[]
    for p in root.iter(P+'p'):
        # Only direct runs: avoid counting text in a nested table twice.
        s=''; colors=[]
        for run in p.findall('p:run',NS):
            val=''.join(x.text or '' for x in run.findall('p:t',NS))
            color=doc['chars'].get(run.get('charPrIDRef'))
            color=color.get('textColor') if color is not None else None
            s+=val; colors.extend([color]*len(val))
        for m in MARKER.finditer(s): out.append((m.group(),tuple(colors[m.start():m.end()])))
    return out

def outside(doc,resaved):
    result={}
    for name,root in doc['roots'].items():
        root=copy.deepcopy(root)
        for parent in root.iter():
            for c in list(parent):
                if c.tag==P+'tbl': parent.remove(c)
                elif resaved and c.tag in (P+'linesegarray',P+'colLine'): parent.remove(c)
        if resaved:
            for e in root.iter():
                for ref,lookup in [('charPrIDRef','chars'),('paraPrIDRef','paras')]:
                    if ref in e.attrib:
                        definition=copy.deepcopy(doc[lookup].get(e.get(ref)))
                        if definition is not None:
                            definition.attrib.pop('id',None)
                            e.set(ref,repr(canonical(definition)))
                # Generated identity and cache values, not pagination/format settings.
                for k in ('id','instid','textWidth','textHeight','dirty'):
                    e.attrib.pop(k,None)
        result[name]=canonical(root)
    return result

def pdf_pages(path):
    doc=pymupdf.open(path); pages=[]
    for pg in doc:
        lines=[]
        for block in pg.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                s=''.join(x['text'] for x in line['spans'])
                lines.append({'text':s,'bbox':list(line['bbox']),'sizes':sorted(set(round(x['size'],3) for x in line['spans']))})
        footer=[l for l in lines if re.fullmatch(r'-\s*\d+\s*-',l['text'])]
        rects=[list(d['rect']) for d in pg.get_drawings() if d['type']=='s']
        pages.append({'text':norm(pg.get_text()),'lines':lines,'rects':rects,'footer_y':min((x['bbox'][1] for x in footer),default=pg.rect.height-60),'printed':footer[0]['text'] if footer else None,'height':pg.rect.height})
    doc.close();return pages

def fragments(s,n=12):
    s=norm(s)
    return [s[i:i+n] for i in range(0,len(s),n) if len(s[i:i+n])>=4]

def audit(doc,pages):
    reports=[];last_page=0
    section=doc['roots']['Contents/section2.xml']
    parents={c:p for p in section.iter() for c in p}
    paragraph_index={p:i for i,p in enumerate(section.iter(P+'p'))}
    for idx,t in enumerate(doc['tables']):
        cc=cells(t); widths,errors=grid(t)
        chunks=[v for c in cc for v in fragments(text(c))]
        scores=[sum(len(v) for v in chunks if v in pg['text']) for pg in pages]
        # Search after prior table; nested tables share their containing page.
        best=max(range(max(0,last_page-1),len(pages)),key=lambda i:scores[i])
        page_ids=[best]
        if t.get('pageBreak')=='TABLE' and t.find('p:pos',NS).get('treatAsChar')=='0':
            header_row=1 if text(cc[0]).startswith('<표') else 0
            labels=[norm(text(c)) for c in cc if info(c)[0]==header_row and norm(text(c))]
            caption=norm(text(cc[0])) if header_row==1 else None
            for adjacent in range(max(0,best-2),min(len(pages),best+3)):
                pp=pages[adjacent]
                if adjacent!=best and len(labels)>=3 and all(s in pp['text'] for s in labels) and (not caption or caption in pp['text']):page_ids.append(adjacent)
            page_ids.sort()
        last_page=max(page_ids);best=min(page_ids);pg=copy.deepcopy(pages[best])
        if len(page_ids)>1:
            pg['text']='';pg['lines']=[];pg['rects']=[]
            for page_id in page_ids:
                pp=pages[page_id]
                anchors=[l['bbox'][1] for l in pp['lines'] if norm(l['text'])==(caption if caption else labels[0])]
                start=min(anchors,default=0)-(3 if caption else 45)
                selected=[l for l in pp['lines'] if l['bbox'][1]>=start]
                pg['lines'].extend(selected);pg['text']+=norm(''.join(l['text'] for l in selected))
                pg['rects'].extend(r for r in pp['rects'] if r[1]>=start)
        allx=[r for r in pg['rects'] if r[2]-r[0]>100 and abs(r[3]-r[1])<.5]
        x0=min((r[0] for r in allx),default=79.75); x1=max((r[2] for r in allx),default=512.36)
        total=sum(widths);cum=[0]
        for w in widths:cum.append(cum[-1]+w)
        rect_bottom=max((r[3] for r in pg['rects']),default=0)
        crossing=rect_bottom>pg['footer_y']
        predicted_rows=collections.defaultdict(float)
        for c in cc:
            rr,_,rs,_,_,minimum=info(c)
            hh=0
            for para in c.findall('p:subList/p:p',NS):
                segs=para.findall('p:linesegarray/p:lineseg',NS)
                hh+=max((int(l.get('vertpos','0'))+int(l.get('vertsize','0')) for l in segs),default=0)
            margin=c.find('p:cellMargin',NS)
            hh+=sum(int(margin.get(k,'0')) for k in ('top','bottom')) if margin is not None else 0
            predicted_rows[rr]=max(predicted_rows[rr],max(minimum,hh)/rs)
        row_y=[min((r[1] for r in pg['rects']),default=111.12)]
        scale=(x1-x0)/total
        if text(cc[0]).startswith('<표'):
            row_y[0]-=predicted_rows[0]*scale
        for rr in range(int(t.get('rowCnt'))):row_y.append(row_y[-1]+predicted_rows[rr]*scale)
        entries=[];row_heights=collections.defaultdict(float);col_lines=collections.defaultdict(list)
        for c in cc:
            r,col,rs,cs,w,h=info(c);s=text(c);ls=c.findall('.//p:lineseg',NS)
            heights=[]
            for p in c.findall('p:subList/p:p',NS):
                segs=p.findall('p:linesegarray/p:lineseg',NS)
                heights.append(max((int(l.get('vertpos','0'))+int(l.get('vertsize','0')) for l in segs),default=0))
            margin=c.find('p:cellMargin',NS);mh=sum(int(margin.get(k,'0')) for k in ('top','bottom')) if margin is not None else 0
            measured=sum(heights)+mh;row_heights[r]=max(row_heights[r],measured/rs)
            left=x0+(x1-x0)*cum[col]/total;right=x0+(x1-x0)*cum[col+cs]/total
            band=[l for l in pg['lines'] if l['bbox'][0]>=left-2 and l['bbox'][2]<=right+2]
            # On overflowing one-table pages, anchor each cell to its measured row.
            # This prevents a repeated placeholder in an earlier row hiding lost text.
            if crossing:
                band=[l for l in band if l['bbox'][1]>=row_y[r]-2 and l['bbox'][3]<=row_y[min(r+rs,len(row_y)-1)]+2 and not re.fullmatch(r'-\s*\d+\s*-',l['text'])]
            bandtext=norm(''.join(l['text'] for l in band));want=norm(s)
            present=not want or want in bandtext
            # A merged/title cell may contain nested controls; document-order extraction is fallback.
            if not present and not crossing: present=want in pg['text']
            tails=fragments(s);missing=[v for v in tails if v not in bandtext and (crossing or v not in pg['text'])]
            if crossing and want and not present and not missing:missing=[want]
            matching=[l for l in band if norm(l['text']) and len(norm(l['text']))>=2 and norm(l['text']) in want]
            col_lines[col].append(len(ls))
            font_refs=sorted(set(run.get('charPrIDRef') for run in c.iter(P+'run')))
            entries.append({'row':r,'col':col,'span':[rs,cs],'text':s,'minimum_height_hwp':h,'lineseg_count':len(ls),'lineseg_content_height_hwp':measured,'font_heights_hwp':sorted(set(int(doc['chars'][ref].get('height')) for ref in font_refs if ref in doc['chars'])),'line_heights_hwp':sorted(set(int(l.get('vertsize','0')) for l in ls)),'line_spacing_hwp':sorted(set(int(l.get('spacing','0')) for l in ls)),'pdf_full_text_present':present,'missing_fragments':missing,'pdf_matching_line_count':len(matching),'pdf_matching_y_range':[min((l['bbox'][1] for l in matching),default=None),max((l['bbox'][3] for l in matching),default=None)],'pdf_font_sizes':sorted(set(sz for l in matching for sz in l['sizes']))})
        missing=[e for e in entries if e['missing_fragments']]
        equal=max(widths)-min(widths)<=3 if widths else False
        maxima=[max(col_lines.get(i,[0])) for i in range(len(widths))]
        unbalanced=equal and len(widths)>1 and max(maxima)>2*max(1,min(maxima))
        priority='P0' if missing and crossing else 'P1' if missing or crossing else 'P2' if unbalanced else 'P3'
        reports.append({'table_idx':idx,'id':t.get('id'),'rows':int(t.get('rowCnt')),'cols':int(t.get('colCnt')),'title':text(cc[0])[:160],'pdf_page':best+1,'printed_page':pg['printed'],'page_match_score':scores[best],'grid_hwp':widths,'grid_errors':errors,'equal_columns':equal,'max_lines_per_column':maxima,'width_imbalance':unbalanced,'declared_height_hwp':int(t.find('p:sz',NS).get('height')),'lineseg_row_max_sum_hwp':sum(row_heights.values()),'pdf_predicted_row_edges':row_y if crossing else None,'pdf_drawing_bottom':rect_bottom,'pdf_footer_top':pg['footer_y'],'drawing_crosses_footer':crossing,'missing_cell_count':len(missing),'priority':priority,'cells':entries,'recommendation':'열폭을 긴 문장 열 중심으로 재배분하고 새 쪽 배치 후 재조판; 남으면 표 나눔 검토. PDF 끝셀과 하단 경계를 다시 검증.' if priority in ('P0','P1') else '짧은 식별자 열을 좁히고 진술문·근거 열을 넓혀 줄수 균형 개선.' if unbalanced else '현 폭 유지 가능; 실제 PDF 재조판 후 보존 검증.'})
        host=parents[t]
        while host not in paragraph_index and host in parents:host=parents[host]
        reports[-1]['host_paragraph_idx_including_cells']=paragraph_index.get(host)
        reports[-1]['pdf_matching_text_top']=min((e['pdf_matching_y_range'][0] for e in entries if e['pdf_matching_y_range'][0] is not None),default=None)
        reports[-1]['top_overflow_detected']=any(e['pdf_matching_y_range'][0] is not None and e['pdf_matching_y_range'][0]<0 for e in entries)
        specific={
          7: 'P0: PDF67/인쇄53, row13 주공종 정의/측정방법 끝과 row14 총근로자수 행 유실. 구분/변수/정의/측정방법/측정시점 폭을 12:20:29:25:14 정도로 시작하여 정의 열 6줄 병목을 완화; 이미 새 쪽이므로 폭 조정 후에도 넘치면 행 단위 표 나눔.',
          13: 'P0: PDF79/인쇄65, row9 본 시스템 및 6개 DATA PENDING 끝 유실(앞 행 동일 문구로 검출 대체 금지). 8열에 긴 마커가 반복되어 모두 5줄 병목; 단순 열 재배분만으로 해결 어려움. 마커 내용/색을 유지한 채 해당 셀 여백·줄간격을 조정하고 필요하면 행 단위 표 나눔. 기존 top 약111pt에서 footer743pt까지 허용높이 대비 약96pt 초과.',
          21: 'P1: PDF87/인쇄73, 텍스트 유실은 미검출이나 표 하단810pt가 footer743pt 침범. 가설/내용/검정방법/통계량/p/효과크기/채택여부를 7:19:23:13:12:13:13 정도로 시작하여 7줄 검정방법 병목 해소. 재조판 후 footer 위로 전부 들어오는지 확인.',
          38: 'P0: PDF119/인쇄105, row4 관리효율성 정의·이론·선행연구·개발방식 말미 유실, 표 하단853pt. 요인/측정대상/정의/이론/선행연구/개발방식을 11:10:17:22:17:23 정도로 시작하여 13~14줄 병목 완화; 여전히 넘치면 행 단위 표 나눔.',
          43: 'P0 최우선: PDF126/인쇄112, row6 근거 끝 넣지 않는다 및 row7/8 전체 유실. 10pt, lineseg 높이1000/간격600, row별 최다줄 1/2/2/5/9/2/20/4/10, 실제 row6 근거19줄만 검출. 문항/내용/역할/근거 열 7:22:17:54 (2740/8611/6654/21137 HWPUNIT, 합39142)를 출발점으로 재조판. 마지막 기술 보고만 한다 포함 3개 하단 근거 셀 전체를 같은 표 PDF 위치에서 검증.',
        }
        if idx in specific:reports[-1]['recommendation']=specific[idx]
        reports[-1]['pdf_pages']=[n+1 for n in page_ids]
        reports[-1]['repeated_headers_detected']=len(page_ids)>1
        if len(page_ids)>1:
            counts=collections.Counter((info(c)[1],info(c)[3],norm(text(c))) for c in cc if norm(text(c)) and MARKER.search(text(c)))
            shortages=[]
            for (col,cs,value),expected in counts.items():
                left=x0+(x1-x0)*cum[col]/total;right=x0+(x1-x0)*cum[col+cs]/total
                content=norm(''.join(l['text'] for l in pg['lines'] if l['bbox'][0]>=left-2 and l['bbox'][2]<=right+2))
                actual=content.count(value)
                if actual<expected:shortages.append({'col':col,'expected':expected,'actual':actual,'text':value})
            reports[-1]['repeated_marker_shortages']=shortages
    return reports

def verify(base,candidate,pages,resaved=False):
    errors=[]
    if len(base['tables'])!=len(candidate['tables']): errors.append('table_count_changed')
    for idx,(a,b) in enumerate(zip(base['tables'],candidate['tables'])):
        if [(info(c)[:4],text(c)) for c in cells(a)] != [(info(c)[:4],text(c)) for c in cells(b)]: errors.append({'table_content_or_merge_changed':idx})
        for k in ('numberingType','rowCnt','colCnt'):
            if a.get(k)!=b.get(k):errors.append({'table_attribute_changed':[idx,k]})
        if marker_colors(base,a)!=marker_colors(candidate,b): errors.append({'marker_colors_changed':idx})
        _,ge=grid(b)
        if ge:errors.append({'grid_invalid':idx,'details':ge})
    if marker_colors(base,base['roots']['Contents/section2.xml'])!=marker_colors(candidate,candidate['roots']['Contents/section2.xml']): errors.append('document_marker_colors_changed')
    if outside(base,resaved)!=outside(candidate,resaved): errors.append('outside_table_XML_changed')
    if not resaved:
        for n in base['entries']:
            if n not in base['roots'] and base['entries'][n]!=candidate['entries'].get(n):errors.append({'nonsection_entry_changed':n})
    report=audit(candidate,pages)
    for t in report:
        if t['grid_errors'] or t['missing_cell_count'] or t['drawing_crosses_footer'] or t.get('repeated_marker_shortages'):
            errors.append({'pdf_table_requires_review':t['table_idx'],'page':t['pdf_page'],'missing_cells':t['missing_cell_count'],'crosses_footer':t['drawing_crosses_footer']})
    # Mandatory clipping probes in their actual table page/column, not elsewhere in the PDF.
    if len(report)>43:
        target=report[43]
        for r in (6,7,8):
            for e in target['cells']:
                if e['row']==r and e['col']==3 and not e['pdf_full_text_present']: errors.append({'tbl43_required_cell_not_fully_visible':[r,3],'tail':e['text'][-45:]})
    return {'ok':not errors,'mode':'after_hancom_resave' if resaved else 'before_hancom_resave','errors':errors,'tables':report}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',required=True,type=Path);ap.add_argument('--candidate',required=True,type=Path);ap.add_argument('--pdf',required=True,type=Path)
    ap.add_argument('--resaved',action='store_true');ap.add_argument('--audit',action='store_true')
    args=ap.parse_args();base=read_hwpx(args.base);candidate=read_hwpx(args.candidate);pages=pdf_pages(args.pdf)
    result=verify(base,candidate,pages,args.resaved)
    result['sources']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.base,args.candidate,args.pdf)}
    result['pdf_page_count']=len(pages)
    result['limitations']=['PDF line counts use matching text within column bands; repeated short labels can overcount. Missing fragments are review findings, not proof of clipping unless supported by footer crossing and absent continuation.', 'Drawing bounds are page-wide and can include another table on the same page. A table crossing the footer is conservatively rejected.', 'After resave ignores generated IDs and line-layout caches, but keeps semantic XML and resolved character/paragraph formatting. Unexpected differences require review; never silently whitelist them.', 'Table indices are section2 tbl preorder 0..44, including nested tables. Heights are measured lineseg content, not cellSz minimum fit claims.']
    if not args.audit:
        result['tables']=[{k:v for k,v in t.items() if k!='cells'} for t in result['tables']]
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['ok'] else 1

if __name__=='__main__':
    raise SystemExit(main())
