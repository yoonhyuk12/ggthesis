"""Read-only HWPX dump/MD comparison; writes only the scoped JSON plan on --build."""
import difflib
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PARS = json.loads((HERE / 'base_paras.json').read_text(encoding='utf-8'))
TABLES = json.loads((HERE / 'base_tables.json').read_text(encoding='utf-8'))
SECT = 'Contents/section2.xml'
PMAP = {(p['section'], p['idx']): p for p in PARS}
TMAP = {(t['section'], t['idx']): t for t in TABLES}
parserfile = REPO / 'tools/hwpx_transfer/md_to_blocks.py'
parser = {'__file__': str(parserfile), '__name__': 'scoped_md_parser'}
exec(compile(parserfile.read_text(encoding='utf-8'), str(parserfile), 'exec'), parser)

SCOPES = {
    '01': ('01_서론.md', 0, 37),
    '02': ('02_이론적배경.md', 37, 419),
    '03': ('03_시스템개발.md', 419, 793),
    '05': ('05_실증분석결과.md', 1201, 2178),
    '06': ('06_결론.md', 2178, 2191),
}

def clean(s):
    return html.unescape(s).replace('<br>', '\n').replace('<br/>', '\n')

def norm(s):
    return re.sub(r'\s+', '', clean(s)).replace('∼', '~')

def mdblocks(fname):
    result = parser['parse_file'](fname)
    assert not result[5], result[5]
    out = []
    for b in result[1]:
        c = dict(b)
        if c['type'] == 'table':
            c['rows'] = [[clean(v) for v in row] for row in [c['header']] + c['rows']]
        else:
            c['text'] = clean(c.get('text', ''.join(r['text'] for r in c.get('runs', []))))
        out.append(c)
    return out

def texts_for(code):
    fname, lo, hi = SCOPES[code]
    old = [p for p in PARS if p['section'] == SECT and lo <= p['idx'] < hi and p['top_level'] and p['text'].strip()]
    new = [b for b in mdblocks(fname) if b['type'] not in ('table', 'table_caption')]
    return old, new

def rows(t):
    return [[c['text'] for c in row] for row in t['rows']]

def inspect(code, limit=220):
    old, new = texts_for(code)
    sm = difflib.SequenceMatcher(a=[norm(p['text']) for p in old], b=[norm(b['text']) for b in new], autojunk=False)
    print('CHAPTER', code, 'OLD', len(old), 'NEW', len(new))
    for op, a, z, b, y in sm.get_opcodes():
        if op == 'equal':
            continue
        print('OP', op, (a, z), (b, y))
        for p in old[a:z]:
            print('OLD', p['idx'], repr(p['text'][:limit]))
        for j in range(b,y):
            print('NEW', j, repr(new[j]['text'][:limit]))
    fname, lo, hi = SCOPES[code]
    oldtables = [t for t in TABLES if t['section'] == SECT and lo <= min(i for r in t['rows'] for c in r for i in c['p_indices']) < hi]
    newtables = [b for b in mdblocks(fname) if b['type'] == 'table']
    print('TABLE_COUNTS', len(oldtables), len(newtables))
    for i,t in enumerate(oldtables):
        oldrows=rows(t)
        print('TABLE OLD',i,t['idx'],len(oldrows),t['attrs']['colCnt'],repr(oldrows[0]))
    for i,t in enumerate(newtables):
        print('TABLE NEW',i,len(t['rows']),len(t['rows'][0]),repr(t['rows'][0]))

def source_for(fname, text):
    lines=(REPO/'01.docs'/fname).read_text(encoding='utf-8-sig').splitlines()
    target=norm(text)
    for i,line in enumerate(lines,1):
        trial=clean(re.sub(r'^#{1,6}\s+', '', line)).replace('**','').replace('`','')
        if norm(trial)==target:
            return f'01.docs/{fname}:{i}'
    return f'01.docs/{fname}'

def build():
    plan={
        'scope': '현행 MD 00·01·02·03·05·06·07과 원본 HWPX의 표적 대조: ANCOVA·현장당 1명·설문 결정 이관',
        'replace': [], 'insert_after': [], 'remove_paragraphs': [],
        'replace_tables': [], 'insert_tables': [], 'user_edits': [], 'notes': []
    }
    md={c:texts_for(c)[1] for c in SCOPES}
    mdt={c:[b for b in mdblocks(SCOPES[c][0]) if b['type']=='table'] for c in SCOPES}
    handled_md={c:set() for c in SCOPES}
    def replacement(idx, new, fname, reason, section=SECT):
        old=PMAP[(section,idx)]['text']
        if norm(old)!=norm(new):
            plan['replace'].append({'section':section,'idx':idx,'old_hwpx':old,'new':new,
                                    'md_source':source_for(fname,new),'reason':reason})
    def rp(code, idx, j, reason='현행 MD의 조사 조건·분석 설계 및 보고 범위 반영'):
        replacement(idx,md[code][j]['text'],SCOPES[code][0],reason)
        handled_md[code].add(j)
    def ip(code, idx, js, reason):
        plan['insert_after'].append({'section':SECT,'idx':idx,
            'blocks':[{'kind':'paragraph','text':md[code][j]['text'],
                       'style_hint':'heading' if md[code][j]['type'].startswith('h') else ('note' if md[code][j]['text'].startswith('주:') else 'body')} for j in js],
            'reason':reason+'; '+', '.join(source_for(SCOPES[code][0],md[code][j]['text']) for j in js)})
        handled_md[code].update(js)
    def t_repl(tidx,newrows,source,reason):
        oldrows=rows(TMAP[(SECT,tidx)])
        assert [[norm(v) for v in r] for r in oldrows] != [[norm(v) for v in r] for r in newrows]
        plan['replace_tables'].append({'section':SECT,'table_idx':tidx,'old_rows':oldrows,
                'new_rows':newrows,'md_source':source,'reason':reason})
    def ti(after_idx,newrows,template,source,reason):
        plan['insert_tables'].append({'section':SECT,'after_idx':after_idx,'rows':newrows,
            'template_table_idx':template,'md_source':source,'reason':reason})
    def cell_changes(tidx,newrows,fname,reason):
        table=TMAP[(SECT,tidx)]
        assert len(table['rows'])==len(newrows)
        for oldrow,newrow in zip(table['rows'],newrows):
            assert len(oldrow)==len(newrow)
            for cell,newtext in zip(oldrow,newrow):
                if norm(cell['text'])==norm(newtext):
                    continue
                nonempty=[i for i in cell['p_indices'] if PMAP[(SECT,i)]['text'].strip()]
                if not nonempty:
                    nonempty=[cell['p_indices'][0]]
                replacement(nonempty[0],newtext,fname,reason)
                for i in nonempty[1:]:
                    replacement(i,'',fname,'같은 셀의 최신 문구를 첫 문단에 반영하여 이전 문구 중복 제거')

    # Chapters 1–3: preserve existing layout-only differences and literal footnote conversion.
    for oldidx,newidx in {6:4,31:13,32:15}.items(): rp('01',oldidx,newidx)
    ip('01',31,[14],'연구 범위 문단에서 분리된 현장 자격·정상 운용·공통 기간·조사 월 문단')
    ip('01',32,[16],'분리된 횡단 비교의 해석 범위 문단')
    for oldidx,newidx in {288:60,295:64,403:75,416:84,417:85}.items():rp('02',oldidx,newidx)
    replacement(309,mdt['02'][4]['rows'][-1][-1],SCOPES['02'][0],'표 2-5의 본 연구 분석방법을 ANCOVA·일반선형모형으로 반영')
    for oldidx,newidx in {518:25,791:89}.items():rp('03',oldidx,newidx)

    # Chapter 5 paragraph targets; untouched captions and all identical paragraphs remain.
    mapping5={1203:1,1204:2,1208:4,1209:5,1210:6,1211:7,1406:9,1407:12,
      1612:26,1701:32,1755:35,1756:36,1759:38,1761:39,1763:40,1806:41,
      1807:42,1809:43,1811:44,1812:45,1850:48,1915:49,1916:50,1930:52,
      1931:53,1933:54,1935:55,1999:57,2000:58,2032:59,2036:61,2040:63,
      2042:64,2079:65,2122:67,2123:68,2137:70,2164:74,2170:78,2172:80,2175:83}
    for idx,j in mapping5.items():rp('05',idx,j)
    ip('05',1812,[46],'ANCOVA 조정 평균과 부분 η²의 해석 문단 추가')
    ip('05',2124,[69],'표 5-8 패널 C 다음에 실제 잔차 자유도와 상호작용 방향 해석 주석 추가')
    captions5=[b['text'] for b in mdblocks(SCOPES['05'][0]) if b['type']=='table_caption']
    for idx,cno in [(1813,5),(1936,6),(2041,7)]:
        replacement(idx,captions5[cno],SCOPES['05'][0],'현행 ANCOVA·탐색적 상호작용 결과표 제목')

    # Tables with changed dimensions are rebuilt from the corresponding existing table only.
    source5='01.docs/05_실증분석결과.md'
    table5=mdt['05']
    t_repl(26,[[captions5[0]+'\n'+md['05'][8]['text']]]+table5[0]['rows'],source5+':29',
           '표 5-1 패널 A: 연령·경력 범주행을 제거하고 총공사비 5구간 반영; 기존 전체폭 캡션행 유지')
    handled_md['05'].add(8)
    ti(1406,[[md['05'][10]['text']]]+table5[1]['rows']+[[md['05'][11]['text']]],26,source5+':49',
       '표 5-1 패널 B 신규: 만 나이·경력 연속값; 첫행은 패널 제목, 마지막 1셀행은 주석이며 전체폭 병합')
    handled_md['05'].update((10,11))
    t_repl(31,[[captions5[3]+'\n'+md['05'][33]['text']]]+table5[6]['rows'],source5+':162',
           '표 5-4 패널 A를 연속 공변량 2개의 분포·공통범위 표로 전환')
    handled_md['05'].add(33)
    ti(1702,[[md['05'][34]['text']]]+table5[7]['rows'],31,source5+':171',
       '표 5-4 패널 B 신규: 범주형 요인 4개를 별도 패널로 보고; 첫행 전체폭 병합')
    handled_md['05'].add(34)
    t_repl(32,[[captions5[4]]]+table5[8]['rows'],source5+':194',
           '현장 임의절편의 군집·수렴 진단을 ANCOVA의 선형성·기울기 동질성·식별 진단으로 교체')
    t_repl(33,table5[9]['rows'],source5+':225',
           '표 5-6 패널 A의 개인 수·현장 수 두 열을 n(명·개소) 한 열로 통합')
    cell_changes(34,table5[10]['rows'],SCOPES['05'][0],
                 '표 5-6 패널 B: 연속 공변량과 범주형 더미의 계수 보고 구조')
    t_repl(35,table5[11]['rows'],source5+':249',
           '표 5-6 패널 C를 집단 F·분자/분모 df·p·부분 η² 표로 교체; 새로운 내용에 맞춘 열폭 필요')
    ti(1917,[[md['05'][51]['text']]]+table5[12]['rows'],35,source5+':255',
       '표 5-6 패널 D 신규: 분석 규모·계수 수·설계행렬 순위·잔차 자유도·가정 점검; 첫행 전체폭 병합')
    handled_md['05'].add(51)
    t_repl(36,table5[13]['rows'],source5+':273',
           '표 5-7 패널 A: ANCOVA F·분자/분모 df와 부분 η² 추가; Holm 보정 5영역 유지')
    cell_changes(37,table5[14]['rows'],SCOPES['05'][0],
                 '표 5-7 패널 B의 분산 성분·ICC·수렴을 계수 수·rank(X)·잔차 df·추정 가능 여부로 교체')
    t_repl(38,table5[15]['rows'],source5+':309',
           '표 5-8 패널 A: W 상호작용 일반선형모형과 연속 공변량 2개·범주형 요인 4개 반영')
    t_repl(40,table5[17]['rows'],source5+':333',
           '표 5-8 패널 C: 상호작용 F·df·p와 분석 규모·식별 상태 보고')
    cell_changes(41,[[captions5[8]]]+table5[18]['rows'],SCOPES['05'][0],
                 '표 5-9 H1은 ANCOVA, H2는 탐색적 상호작용 일반선형모형으로 명시')

    # Chapter 6: original paragraph boundaries retained wherever source permits.
    for oldidx,newidx in {2180:1,2181:3,2183:5,2187:9}.items():rp('06',oldidx,newidx)
    ip('06',2180,[2],'확정된 도입 운용기간·공통 기간·ANCOVA 조정변수 문단 추가')
    ip('06',2187,[10],'예산 인지 응답자·60명 목표·연속 공변량 및 일반화 한계 문단 추가')

    # Printed TOC labels only: retain each old indentation and existing page number.
    toc_updates={64:'제4절 가설 검정: 공분산분석(ANCOVA)',65:'제1항 공분산분석 가정 점검',
      66:'제2항 안전관리 실효성에 대한 공분산분석',67:'제3항 안전관리 실효성 하위영역별 공분산분석',
      115:captions5[4],116:captions5[5],117:captions5[6],118:captions5[7]}
    for idx,label in toc_updates.items():
        old=PMAP[('Contents/section1.xml',idx)]['text']
        indent=re.match(r'^\s*',old).group()
        page=re.search(r'\d+$',old).group()
        replacement(idx,indent+label+page,'00_목차.md','목차의 현행 제목만 대응; 기존 탭/점선/인쇄 쪽수는 메인이 재조판 후 갱신',section='Contents/section1.xml')

    # Directly affected method references, preserving user-authored bibliography grouping.
    refs=(REPO/'01.docs/07_참조번호목록.md').read_text(encoding='utf-8-sig').splitlines()
    jamovi=next(s for s in refs if s.startswith('The jamovi project, jamovi [Computer Software].'))
    ancova=next(s for s in refs if s.startswith('jamovi, ANCOVA (ancova)'))
    linreg=next(s for s in refs if s.startswith('jamovi, Linear Regression (linReg)'))
    replacement(2242,'[03] '+jamovi,'07_참조번호목록.md','미검증 jamovi Version 2.7·2026 인용을 현행 버전 미확정 서지로 대조; 기존 인쇄 번호 유지')
    replacement(2243,ancova,'07_참조번호목록.md','이전 GAMLj Mixed Models 공식 문헌을 현행 ANCOVA 공식 문헌으로 교체')
    plan['insert_after'].append({'section':SECT,'idx':2243,'blocks':[{'kind':'paragraph','text':linreg,'style_hint':'body'}],
                                'reason':'현행 주 분석 계수·진단 보조 출력의 Linear Regression 공식 문서 추가; '+source_for('07_참조번호목록.md',linreg)})

    # HWPX-only content and layout variations are explicit preservation exceptions.
    plan['user_edits']=[
      {'section':'Contents/section0.xml','idx':[11,17,23,26,49],
       'old_hwpx':['윤   혁','2026년 12월  일','윤   혁','윤   혁의 석사학위논문을 인준함','2026년 12월  일'],
       'action':'preserve','reason':'MD 표지 골격은 성명·제출월 미확정이나 한글본에는 성명·제출월·인준서가 기입되어 있음; 설문 월 10월과 제출월 12월은 구별'},
      {'section':'Contents/section1.xml','idx':[131,133,155,156],
       'action':'preserve','reason':'MD에 없는 감사의 글과 작성자 표기를 그대로 둠'},
      {'section':SECT,'idx':4,'old_hwpx':PMAP[(SECT,4)]['text'],
       'md_text':md['01'][2]['text'],'action':'preserve',
       'reason':'건설업 주어 위치의 어순만 다르며 이번 조사·분석 변경과 무관한 한글 직접 문장 수정 가능성; 의미·근거 동일'},
      {'section':SECT,'idx':[2193,2212,2229,2234,2236],
       'action':'preserve','reason':'참고문헌의 학위논문·학술지·보고서·관련법·기타 분류 및 일부 인쇄 번호는 한글본 직접 편집 구성으로 유지; 이번 방법론 서지 3건만 반영'}
    ]
    plan['notes']=[
      {'kind':'figure_update_required','section':SECT,'idx':34,'caption_idx':35,
       'md_source':'01.docs/01_서론.md:53','reason':'기존 연구흐름도 그림 객체의 구 120명·현장 군집·혼합모형 표현을 현행 Mermaid 원문으로 대응해야 함; 객체 삭제·재작성은 본 워커가 수행하지 않음',
       'md_mermaid':re.search(r'```mermaid\n(.*?)\n```',(REPO/'01.docs/01_서론.md').read_text(encoding='utf-8-sig'),re.S).group(1)},
      {'kind':'preserve_layout','section':SECT,'idx':[292,293],
       'reason':'제2장 제5절 제목과 괄호 부제가 두 문단으로 나뉜 기존 조판은 MD의 한 제목과 내용이 같음; 사용자 추가 내용으로 분류하지 않음'},
      {'kind':'preserve_layout','section':SECT,'table_idx':0,'idx':[17,18],
       'reason':'39.66%와 (328/827명)을 줄바꿈한 표현은 MD의 39.66%(328명/827명)과 수치·의미 동일; 조판 유지'},
      {'kind':'preserve_layout','section':SECT,'table_idx':11,
       'reason':'TP/FP/FN/TN과 정의를 두 문단으로 분리한 셀은 MD의 대시 연결 표현과 동일; 조판 유지'},
      {'kind':'preserve_footnote_conversion','section':SECT,'idx':434,
       'reason':'Bosch 각주 문구가 한글 본문 괄호 안에 이미 동일한 내용으로 수록되어 있음; MD 각주 정의를 별도 문단으로 중복 삽입하지 않음'},
      {'kind':'preserve_figures','section':SECT,'md_source':'01.docs/03_시스템개발.md',
       'reason':'제3장 그림 3-1~3-4의 MD 이미지 링크는 한글 그림 객체로 이미 수록되어 있으므로 텍스트로 삽입하지 않음'},
      {'kind':'abstract_status','section':'Contents/section1.xml','idx':[158,159],
       'md_source':'01.docs/00_목차.md:39',
       'reason':'MD 국문초록은 작성 가이드와 결과 미확정 골격이고 한글 논문개요는 비어 있음; 완성 초록을 창작하거나 작성 가이드 자체를 새 본문으로 이관하지 않음'},
      {'kind':'marker_style','reason':'신규·교체 내용의 [DATA PENDING·[확정 필요·[CITE_TODO·[UNVERIFIED 및 실험전은 전체 토큰을 빨간 run으로 유지·복원해야 함; 목차의 실증 표제는 본문 제목이므로 검정'},
      {'kind':'table_structure','reason':'새 표의 첫 1셀행(패널 제목) 및 표5-1 패널B 마지막 1셀행(주석)은 전체폭 병합한다. 기존 table26/31/35의 실제 글꼴·제목/머리행 서식을 참고하되, 표5-1B=9열·표5-4B=7열·표5-6D=5열로 내용에 맞추어 전체폭 안에서 열폭을 새로 배분한다. 검증 전 숫자를 채우지 않는다.'},
      {'kind':'bibliography_scope','reason':'MD 참고문헌 골격의 기타 누락 서지나 국내/국외 재정렬은 기존 한글 직접 편집 구성과 충돌할 수 있어 임의 전체 재구성하지 않음; 본 작업의 ANCOVA 전환에 직접 필요한 3건은 교체·추가 계획에 포함'},
      {'kind':'md_decision_boundary','reason':'중복 제출 허용·최종 응답 선택 설명을 새로 만들지 않았음. 현행 MD의 명부 대조·분석 단위 중복 방지 문구만 그대로 대응함.'}
    ]
    plan['_verification_input']={'handled_md':{k:sorted(v) for k,v in handled_md.items()}}
    return plan

def validate(plan):
    """One final focused validation of the plan and coverage; does not open HWPX."""
    errors=[]
    for item in plan['replace']+plan['remove_paragraphs']:
        p=PMAP.get((item['section'],item['idx']))
        if p is None or p['text']!=item['old_hwpx']:errors.append(('old_mismatch',item['section'],item['idx']))
    keys=[(r['section'],r['idx']) for r in plan['replace']]
    if len(keys)!=len(set(keys)):errors.append('duplicate_replace_target')
    for t in plan['replace_tables']:
        if rows(TMAP[(t['section'],t['table_idx'])])!=t['old_rows']:errors.append(('table_old_mismatch',t['table_idx']))
    for item in plan['insert_after']:
        if not PMAP[(item['section'],item['idx'])]['top_level']:errors.append(('non_top_paragraph_anchor',item['idx']))
    for item in plan['insert_tables']:
        if not PMAP[(item['section'],item['after_idx'])]['top_level']:errors.append(('non_top_table_anchor',item['after_idx']))
    replacedtableids={t['table_idx'] for t in plan['replace_tables']}
    for p in plan['replace']:
        if p['section']==SECT and PMAP[(SECT,p['idx'])]['table_idx'] in replacedtableids:
            errors.append(('table_paragraph_overlap',p['idx']))

    # Coverage: changed/new source paragraphs must be planned or an explicit representation exception.
    exceptions={'01':{2},'02':{63},'03':{10,11,18,33,42,56},'05':set(),'06':set()}
    handled=plan.pop('_verification_input')['handled_md']
    coverage={}
    for code in SCOPES:
        old,new=texts_for(code)
        oldtexts={norm(p['text']) for p in old}
        missing=[j for j,b in enumerate(new) if norm(b['text']) not in oldtexts and j not in handled[code] and j not in exceptions[code]]
        if missing:errors.append(('paragraph_coverage',code,missing))
        coverage[code]={'source_non_table_blocks':len(new),'unchanged_exact_normalized':sum(norm(b['text']) in oldtexts for b in new),
                        'planned_changed_or_new':len(handled[code]),'documented_representation_exceptions':len(exceptions[code]),'uncovered':missing}

    # Every current table cell is accounted for by preserved or planned content in its chapter.
    tablecoverage={}
    for code in ('01','02','03','05'):
        fname,lo,hi=SCOPES[code]
        scoped=[p for p in PARS if p['section']==SECT and lo<=p['idx']<hi]
        repl={r['idx']:r['new'] for r in plan['replace'] if r['section']==SECT}
        transformed='\n'.join(repl.get(p['idx'],p['text']) for p in scoped if p['table_idx'] not in replacedtableids)
        transformed+='\n'+'\n'.join(v for t in plan['replace_tables'] if lo<=min(i for r in TMAP[(SECT,t['table_idx'])]['rows'] for c in r for i in c['p_indices'])<hi for row in t['new_rows'] for v in row)
        transformed+='\n'+'\n'.join(v for t in plan['insert_tables'] if lo<=t['after_idx']<hi for row in t['rows'] for v in row)
        nn=norm(transformed).replace('—','')
        missing=[]
        for ti,t in enumerate(b for b in mdblocks(fname) if b['type']=='table'):
            for ri,row in enumerate(t['rows']):
                for ci,v in enumerate(row):
                    vv=norm(v).replace('—','')
                    if code=='01' and vv=='39.66%(328명/827명)':continue
                    if vv and vv not in nn:missing.append((ti,ri,ci,v))
        if missing:errors.append(('table_cell_coverage',code,missing))
        tablecoverage[code]={'source_tables':sum(b['type']=='table' for b in mdblocks(fname)),'uncovered_cells':missing}
    # The old-design assertions apply only to the scoped body, with table-object replacements resolved.
    scopedtexts=[]
    for code,(fname,lo,hi) in SCOPES.items():
        for p in PARS:
            if p['section']!=SECT or not lo<=p['idx']<hi or p['table_idx'] in replacedtableids:continue
            scopedtexts.append(next((r['new'] for r in plan['replace'] if r['section']==SECT and r['idx']==p['idx']),p['text']))
    for t in plan['replace_tables']:scopedtexts.extend(v for row in t['new_rows'] for v in row)
    for t in plan['insert_tables']:scopedtexts.extend(v for row in t['rows'] for v in row)
    for i in plan['insert_after']:
        if i['section']==SECT and i['idx']<2191:scopedtexts.extend(b['text'] for b in i['blocks'])
    joined='\n'.join(scopedtexts)
    forbidden=['현장 임의절편 선형혼합모형','현장당 2명','120명을 모집','120명은 모집','REML','Satterthwaite']
    stale=[s for s in forbidden if s in joined]
    if stale:errors.append(('stale_design',stale))
    evidence={'old_paragraph_match':len(plan['replace']),'old_table_match':len(plan['replace_tables']),
              'paragraph_anchor_top_level':len(plan['insert_after']),'new_table_anchor_top_level':len(plan['insert_tables']),
              'paragraph_coverage':coverage,'table_coverage':tablecoverage,'stale_design_texts':stale,
              'errors':errors,'passed':not errors,
              'limitation':'본문/표 타깃 계획 검증이며 그림1-1 객체 교체, 마커 서식, 실제 한글 개방·재조판·전 표 PDF·목차 쪽수 검증은 메인 수행'}
    plan['notes'].append({'kind':'verification','evidence':evidence})
    return evidence

if __name__ == '__main__':
    if '--inspect' in sys.argv:
        for c in sys.argv[sys.argv.index('--inspect')+1:]:
            inspect(c)
    if '--build' in sys.argv:
        plan=build()
        evidence=validate(plan)
        (HERE/'plan_front_results.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'counts':{k:len(plan[k]) for k in ('replace','insert_after','remove_paragraphs','replace_tables','insert_tables','user_edits')},'verification':evidence},ensure_ascii=False,indent=2))
        if not evidence['passed']:sys.exit(1)
