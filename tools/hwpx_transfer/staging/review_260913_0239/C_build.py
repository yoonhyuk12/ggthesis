import sys
sys.dont_write_bytecode = True
from C_tables import *
from collections import Counter

out={k:[] for k in ['cell_replace','replace_table','unresolved','user_edits','coverage']}
SEC='Contents/section2.xml'
rawnew=read('new_blocks.json')
def btext(b):return plain(b.get('text','') or ''.join(r['text'] for r in b.get('runs',[])))
def patch(p,newtext):
    if p['text']!=newtext: out['cell_replace'].append({'section':SEC,'idx':p['idx'],'old':p['text'],'new':newtext})
def replace_cell(c,newtext):
    # Changed multi-paragraph cells retain their paragraph nodes; replacement text uses first paragraph.
    for i,p in enumerate(c['paras']):patch(p,newtext if i==0 else '')
def blankresult(s):return '' if s.startswith('[DATA PENDING:') and s.endswith(']') else s
def minimal(k,j,ti,nj=None):
    a=old[k][j];b=new[k][j if nj is None else nj]; t=tables[ti];cm=cellmap(t)
    assert len(a['matrix'])==len(b['matrix']) and len(a['matrix'][0])==len(b['matrix'][0])
    start=len(out['cell_replace'])
    for ri,(ra,rb) in enumerate(zip(a['matrix'],b['matrix'])):
        for ci,(v,w) in enumerate(zip(ra,rb)):
            if v==w:continue
            c=cm[(ri,ci)]; actual=ctext(c)
            if k.startswith('05'):w=blankresult(w)
            if norm(actual)==norm(w):continue
            if norm(actual)!=norm(v) and not (not actual.strip() and v.startswith('[DATA PENDING:')):
                out['unresolved'].append({'table_idx':ti,'row':ri,'col':ci,'old_md':v,'actual':actual,'new_md':w});continue
            replace_cell(c,w)
    if a['caption']!=b['caption'] and offset(t):
        cps=t['cells'][0]['paras']
        match=re.fullmatch(r'(.*?)(\(n=.*)',b['caption'])
        if len(cps)==2 and match:
            patch(cps[0],match[1]);patch(cps[1],match[2])
        else:replace_cell(t['cells'][0],b['caption'])
    out['coverage'].append({'file':k,'md_block_idx':b['block_idx'],'caption':b['caption'],'table_indices':[ti],'action':'cell_replace' if len(out['cell_replace'])>start else 'unchanged_or_already_applied','paragraph_replacements':len(out['cell_replace'])-start,'new_shape':[len(b['matrix']),len(b['matrix'][0])]})

# Record every actual old-MD discrepancy before creating replacement plans.
for k,ids in mapping.items():
    for j,ti in enumerate(ids):
        cm=cellmap(tables[ti]); blanks=[]
        for ri,row in enumerate(old[k][j]['matrix']):
            for ci,v in enumerate(row):
                c=cm.get((ri,ci))
                if c and norm(ctext(c))!=norm(v):
                    entry={'section':SEC,'table_idx':ti,'paragraph_indices':[p['idx'] for p in c['paras']],'old_md':v,'actual':ctext(c),'action':'preserve'}
                    if not ctext(c).strip() and v.startswith('[DATA PENDING:'):blanks.append(entry)
                    else:out['user_edits'].append(entry)
        if blanks:out['user_edits'].append({'section':SEC,'table_idx':ti,'kind':'blank_result_cells','count':len(blanks),'cells':blanks,'action':'preserve_blank_in_existing_and_new_result_cells','authority':'coordinator ask reply: 기존 대응 결과칸 및 신설 통계 결과칸도 빈칸 양식 보존'})

def weights(matrix):
    h=matrix[0]; w=[]
    for ci,label in enumerate(h):
        if label in ['TP','FP','TN','FN','p','df','SE','ICC','t','F1','Recall','Accuracy','Precision']:v=1.0
        elif any(x in label for x in ['점검','처리','고정효과','측정변수','실제 W값','진단']):v=2.8
        elif ci==0:v=2.5
        elif any(x in label for x in ['CI','평균','분산','군집','개인','현장','문항']):v=1.6
        else:v=1.5
        w.append(v)
    return w

def structural(k,oldjs,newjs,positions):
    ids=[mapping[k][j] for j in oldjs];t=tables[ids[0]]; gs=[new[k][j] for j in newjs]
    entry={'section':SEC,'table_idx':ids[0],'old_anchor_idx':t['anchor_idx'],'caption':gs[0]['caption'],'panels':[],'remove_table_indices':ids[1:],'all_old_table_indices':ids,'preserve_total_width':int(t['width']),'width_weights_status':'proposal_only_main_must_measure_actual_font','caption_location':'merged_first_cell' if offset(t) else 'outside_table_owned_by_B'}
    for g,pos in zip(gs,positions):
        m=g['matrix']; applied=[[blankresult(s) if k.startswith('05') else s for s in row] for row in m]
        bi=g['block_idx']; prev=rawnew[k][bi-1]
        panel={'header':applied[0],'rows':applied[1:],'width_weights':weights(m),'note':'','md_block_idx':bi,'after_new_md_block_idx':bi-1,'after_new_md_text':btext(prev),'new_row_count_including_header':len(m),'new_col_count':len(m[0]),**pos}
        if pos.get('table_idx') is not None:panel['old_anchor_idx']=tables[pos['table_idx']]['anchor_idx']
        if k.startswith('05'):
            panel['blank_result_policy']='Preserve HWPX blank result form; all new DATA PENDING result cells are blank by coordinator instruction.'
            end=next((i for i in range(bi+1,len(rawnew[k])) if rawnew[k][i]['type']=='table_caption'),len(rawnew[k]))
            evidence=[i for i in range(bi+1,end) if rawnew[k][i]['type']!='table' and '[DATA PENDING:' in btext(rawnew[k][i])]
            panel['result_pending_context_md_block_indices']=evidence
            panel['note']='[DATA PENDING: 통계 결과는 분석 후 기입한다.]' if not evidence else ''
        entry['panels'].append(panel)
        out['coverage'].append({'file':k,'md_block_idx':bi,'caption':g['caption'],'table_indices':ids,'action':'replace_table_panel','new_shape':[len(m),len(m[0])],'new_result_markers_rendered_blank':sum(s.startswith('[DATA PENDING:') for row in m for s in row) if k.startswith('05') else 0})
    out['replace_table'].append(entry)

for k in ['02_이론적배경.md','03_시스템개발.md','04_연구설계.md']:
    for j,ti in enumerate(mapping[k]):
        if ti==12: structural(k,[j],[j],[{'table_idx':12}])
        else:minimal(k,j,ti)

k='05_실증분석결과.md'
minimal(k,0,24)
structural(k,[1,2],[1,2],[{'table_idx':25},{'table_idx':26}])
structural(k,[3],[3,4],[{'table_idx':27},{'table_idx':None,'after_paragraph_idx':1529,'before_paragraph_idx':1530,'after_old_table_idx':27}])
structural(k,[4],[5],[{'table_idx':28}])
structural(k,[5],[6],[{'table_idx':29}])
structural(k,[6,7],[7,8,9],[{'table_idx':30},{'table_idx':31},{'table_idx':None,'after_old_table_idx':31,'before_paragraph_idx':1803}])
structural(k,[8],[10,11],[{'table_idx':32},{'table_idx':None,'after_old_table_idx':32,'before_paragraph_idx':1862}])
structural(k,[9,10],[12,13,14],[{'table_idx':33},{'table_idx':34},{'table_idx':None,'after_old_table_idx':34,'before_paragraph_idx':1941}])
minimal(k,11,35,nj=15)

for idx,bi in [(2101,7),(2102,8),(2105,10),(2448,22),(2451,24)]:
    p=paras[SEC,idx];patch(p,btext(rawnew['부록1_설문지_양식.md'][bi]))
    out['coverage'].append({'file':'부록1_설문지_양식.md','md_block_idx':bi,'table_indices':[p['table_idx']],'paragraph_idx':idx,'action':'delegated_intro_cell_replace'})
for j,ids in enumerate([[39,46],[40,47],[41],[42]]):
    assert old['부록1_설문지_양식.md'][j]['matrix']==new['부록1_설문지_양식.md'][j]['matrix']
    out['coverage'].append({'file':'부록1_설문지_양식.md','md_block_idx':new['부록1_설문지_양식.md'][j]['block_idx'],'table_indices':ids,'action':'unchanged_preserve_native_survey_grid','new_shape':[len(new['부록1_설문지_양식.md'][j]['matrix']),7]})
for k in ['01_서론.md','06_결론.md']:out['coverage'].append({'file':k,'action':'no_markdown_tables'})

# Strict one-pass specification checks (no HWPX read/write).
seen=set()
for p in out['cell_replace']:
    key=(p['section'],p['idx']);assert key not in seen;seen.add(key)
    assert paras[key]['text']==p['old'] and paras[key]['table_idx'] is not None
replaced={ti for t in out['replace_table'] for ti in t['all_old_table_indices']}
assert not any(paras[p['section'],p['idx']]['table_idx'] in replaced for p in out['cell_replace'])
for t in out['replace_table']:
    assert tables[t['table_idx']]['anchor_idx']==t['old_anchor_idx']
    for p in t['panels']:
        assert len(p['header'])==len(p['width_weights'])==p['new_col_count']
        assert all(len(r)==len(p['header']) for r in p['rows'])
        assert len(p['rows'])+1==p['new_row_count_including_header']
        assert all(w>0 for w in p['width_weights'])
        source=next(g for gs in new.values() for g in gs if g['block_idx']==p['md_block_idx'] and g['caption']==t['caption'])
        expected_matrix=[[blankresult(s) if t['caption'].startswith('<표 5-') else s for s in row] for row in source['matrix']]
        assert [p['header']]+p['rows']==expected_matrix
        assert re.match(r'^<표 \d+-\d+>',t['caption'])
expected={(k,g['block_idx']) for k in list(new)[:7] for g in new[k]}
covered={(c['file'],c['md_block_idx']) for c in out['coverage'] if 'md_block_idx' in c}
assert expected<=covered
(ROOT/'tables_C.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
stats={'cell_replace':len(out['cell_replace']),'replace_table_groups':len(out['replace_table']),'replacement_panels':sum(len(t['panels']) for t in out['replace_table']),'unresolved':len(out['unresolved']),'coverage':len(out['coverage']),'all_new_markdown_tables':len(expected),'blank_user_cells':sum(u.get('count',0) for u in out['user_edits'])}
(ROOT/'C_validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False))
print('UNRESOLVED',json.dumps(out['unresolved'],ensure_ascii=False))
