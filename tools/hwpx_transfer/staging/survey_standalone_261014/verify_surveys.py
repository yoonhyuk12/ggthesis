"""Read-only HWPX/PDF evidence checks; does not call Hancom or modify outputs.

Run after main's Hancom resave, optionally with its exported PDF. This verifies
text, grid geometry, page boundaries and absence of source-template prose.
It does not replace visual inspection of every rendered table page.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import kjn_profile as kp
NS=kp.NS

def norm(t):
    return re.sub(r'\s+','',t)

def texts(node):
    return ''.join((x.text or '') for x in node.iter('{%s}t'%NS['hp']))

def pdf_body_text(page):
    """Exclude only bottom page-number lines before cross-page text matching."""
    lines=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            text=''.join(s['text'] for s in line.get('spans',[]))
            y0=line['bbox'][1]
            if y0>page.rect.height-55 and re.fullmatch(r'\s*[-–—]?\s*\d+\s*[-–—]?\s*',text):
                continue
            lines.append(text)
    return '\n'.join(lines)

def expected_fragments(plan):
    result=[]
    for block in plan['intro'].split('\n\n'):
        for line in block.splitlines():
            if line.strip():result.append(line)
    for part in plan['parts']:
        result.extend(x for x in part['description'].splitlines() if x.strip())
        for q in part['questions']:
            result.append(q['prompt'])
            result.extend(x for x in q['help'].splitlines() if x.strip())
    return Counter(norm(x) for x in result)

def verify(hwpx,plan,pdf=None):
    errors=[];warnings=[];report={'hwpx':str(hwpx),'pdf':str(pdf) if pdf else None}
    def check(condition,msg):
        if not condition:errors.append(msg)
    with zipfile.ZipFile(hwpx) as z:
        check(z.testzip() is None,'ZIP CRC failure')
        names=z.namelist()
        section_names=sorted(n for n in names if re.fullmatch(r'Contents/section\d+\.xml',n))
        check(len(section_names)==1,'Expected one fresh section')
        sections=[ET.fromstring(z.read(n)) for n in section_names]
        full='\n'.join(texts(s) for s in sections)
        header=ET.fromstring(z.read('Contents/header.xml'))
        hpf=ET.fromstring(z.read('Contents/content.hpf'))
        for item in hpf.findall('opf:manifest/opf:item',NS):
            href=item.get('href','')
            check(href in names,'Manifest target missing: '+href)
        check(not any(n.startswith('BinData/') for n in names),'Unexpected retained template binary content')
        check(not any(k in full for k in kp.KJN_FORBIDDEN),'Template-specific prose remains')
        for forbidden in ['배포코드','내부 관리용','[확정 필요','[DATA PENDING','Google Forms','필수 입력','해당 문항으로 이동']:
            check(forbidden not in full,'Respondent output contains admin/UI prose: '+forbidden)
        check('현장명' in full and '예시 : 00지구 수리시설개보수사업' in full,'Site-name/example missing')
        alltext=norm(full)
        for fragment,count in expected_fragments(plan).items():
            actual=alltext.count(fragment)
            # Exact multiplicity for prompts and repeated A7-A9/scale guidance.
            check(actual==count,'Text occurrence mismatch: expected %d actual %d %s'%(count,actual,fragment[:100]))
        prompts=[q for part in plan['parts'] for q in part['questions']]
        check(len(prompts)==(33 if plan['route']=='ADOPTED' else 21),'Expected measurement count mismatch')
        rows_seen={};table_reports=[]
        for section in sections:
            pg=section.find('.//hp:pagePr',NS)
            check(pg is not None,'Page dimensions missing')
            if pg is not None:
                check(pg.get('width')=='53858' and pg.get('height')=='72567','Template paper dimensions changed')
            for table in section.findall('.//hp:tbl',NS):
                check(table.get('pageBreak')!='CELL','Forbidden CELL table breaking')
                trs=table.findall('hp:tr',NS)
                rc=int(table.get('rowCnt'));cc=int(table.get('colCnt'))
                check(rc==len(trs),'Table row count mismatch')
                width=int(table.find('hp:sz',NS).get('width'))
                grid={};colwidth={}
                for tr in trs:
                    for cell in tr.findall('hp:tc',NS):
                        addr=cell.find('hp:cellAddr',NS);span=cell.find('hp:cellSpan',NS)
                        row=int(addr.get('rowAddr'));col=int(addr.get('colAddr'))
                        cs=int(span.get('colSpan'));rs=int(span.get('rowSpan'))
                        w=int(cell.find('hp:cellSz',NS).get('width'))
                        if rs==cs==1:colwidth.setdefault(col,w)
                        for r in range(row,row+rs):
                            for c in range(col,col+cs):
                                check((r,c) not in grid,'Overlapping table grid cell')
                                check(0<=r<rc and 0<=c<cc,'Out-of-range table cell')
                                grid[r,c]=True
                        check(cell.get('header')==('1' if row==0 else '0'),'Header row flag mismatch')
                check(len(grid)==rc*cc,'Incomplete table grid')
                check(len(colwidth)==cc and sum(colwidth.values())==width,'Table total/column widths mismatch')
                for tr in trs[1:]:
                    cells=tr.findall('hp:tc',NS);qid=texts(cells[0]).strip()
                    rows_seen[qid]=[texts(c) for c in cells]
                    check(len(cells)==7,'Response table must contain seven columns')
                    check([texts(c).strip() for c in cells[2:]]==['□']*5,'Five paper response boxes missing')
                table_reports.append({'rows':rc,'columns':cc,'width_hu':width,'column_widths_hu':colwidth,'break':table.get('pageBreak')})
            top=list(section)
            for part in plan['parts']:
                title=part['title'].split(' · ',1)[1]
                matches=[p for p in top if texts(p)==title]
                check(len(matches)==1 and matches[0].get('pageBreak')=='1','Part heading must start a new page: '+title)
        for q in prompts:
            if q['id'].startswith('A'):
                for option in q.get('options',[]):
                    check(norm(option) in alltext,'A option missing: '+q['id']+' '+option)
            else:
                row=rows_seen.get(q['id'])
                check(row is not None and norm(row[1])==norm(q['prompt']),'Cell-scoped question mismatch: '+q['id'])
        expected_tables=4 if plan['route']=='ADOPTED' else 2
        check(len(table_reports)==expected_tables,'Unexpected table count')
        report.update(measurement_count=len(prompts),tables=table_reports,hwpx_text_occurrences_checked=len(expected_fragments(plan)))
        if pdf:
            import fitz
            doc=fitz.open(pdf)
            pdftext=norm(''.join(pdf_body_text(page) for page in doc))
            for fragment,count in expected_fragments(plan).items():
                actual=pdftext.count(fragment)
                check(actual==count,'PDF text occurrence mismatch %d/%d %s'%(actual,count,fragment[:100]))
            page_reports=[]
            for index,page in enumerate(doc):
                out=[]
                for block in page.get_text('dict')['blocks']:
                    for line in block.get('lines',[]):
                        for span in line.get('spans',[]):
                            x0,y0,x1,y1=span['bbox']
                            if x0<-1 or y0<-1 or x1>page.rect.width+1 or y1>page.rect.height+1:
                                out.append({'text':span['text'],'bbox':span['bbox']})
                check(not out,'PDF text outside page '+str(index+1))
                page_reports.append({'page':index+1,'width_pt':page.rect.width,'height_pt':page.rect.height,'out_of_page':out})
            # Four-row C/E tables should remain on one page. D/B split must have
            # row continuity and a repeated scale header, then visual confirmation.
            for letter in ('B','C','D','E'):
                qs=[q for q in prompts if q['id'].startswith(letter+'-')]
                if not qs:continue
                locations={q['id']:[i+1 for i,page in enumerate(doc) if norm(q['prompt']) in norm(pdf_body_text(page))] for q in qs}
                check(all(len(v)==1 for v in locations.values()),'PDF per-question page ambiguity/missing: '+letter)
                if letter in ('C','E'):
                    check(len({x for v in locations.values() for x in v})==1,'Four-question table split across pages: '+letter)
                report.setdefault('pdf_question_pages',{}).update(locations)
            report['pdf_pages']=page_reports
            warnings.append('Main must visually inspect every table page for row/cell clipping and footer overlap; geometry is not visual proof.')
            doc.close()
    report.update(ok=not errors,errors=errors,warnings=warnings,
                  template_sha256_expected=plan['template_sha256'],
                  stage='Read-only static/PDF checks; Hancom open/resave and visual proof are separate')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hwpx',required=True);p.add_argument('--plan',required=True)
    p.add_argument('--pdf');p.add_argument('--report',required=True)
    a=p.parse_args();plan=json.loads(Path(a.plan).read_text(encoding='utf-8'))
    report=verify(Path(a.hwpx),plan,Path(a.pdf) if a.pdf else None)
    Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':report['ok'],'errors':report['errors'],'report':a.report},ensure_ascii=False,indent=2))
    return 0 if report['ok'] else 1

if __name__=='__main__':
    raise SystemExit(main())
