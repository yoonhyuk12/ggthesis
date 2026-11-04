"""Pure XML transformation for main orchestrator; does not write HWPX."""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/hwpx_transfer'))
import patch_from_fresh as p


def patch_surveys(s2):
    units = p.Units(s2, set())
    start = next(i for i,u in enumerate(units.items) if p.nows(u['text']) == '부록(도입현장)')
    stop = next((i for i,u in enumerate(units.items[start+1:],start+1)
                 if u['text'].startswith('부록 2.') or u['text'].strip().lower()=='abstract'),len(units.items))
    changed=[]; deleted=[]; result=[]; skip_budget=False; region='common'
    for i,u in enumerate(units.items[start:stop],start):
        t=u['text']; xml=u['xml']
        if t=='Part C. 안전관리 예산 제약성':
            skip_budget=True
        elif skip_budget and (t=='도입 현장 전용부' or t=='끝까지 응답해 주셔서 진심으로 감사합니다.'):
            skip_budget=False
        if skip_budget:
            deleted.append({'index':i,'text':t});continue
        if t=='Part D. 시스템 특성 인식': region='system'
        elif t=='Part E. 경보 피로도 완화': region='fatigue'
        elif p.nows(t)=='부록(미도입현장)': region='common'
        pairs=[('Part B·C는','Part B는'),('도입현장은 A∼E, 미도입현장은 A∼C','도입현장은 A∼D, 미도입현장은 A∼B'),('A∼E의 측정 문항 수(21문항 또는 33문항)','측정 문항 수(미도입 현장 17문항, 도입 현장 29문항)'),('미도입 현장 경로에는 D·E가','미도입 현장 경로에는 C·D가')]
        if region=='system':
            pairs += [('Part D','Part C')] + [(f'D-{n}',f'C-{n}') for n in range(1,9)]
        elif region=='fatigue':
            pairs += [('Part E','Part D')] + [(f'E-{n}',f'D-{n}') for n in range(1,5)]
        applied=[]
        for old,new in pairs:
            count=xml.count(p.esc(old))
            if count:
                xml=p.replace_literal_text(xml,old,new,count);applied.append([old,new,count])
            elif old in t:
                raise AssertionError('Fragmented replacement requires review: '+old)
        if applied:changed.append({'index':i,'replacements':applied})
        result.append(xml)
    assert len(deleted)==10, len(deleted)
    a=units.spans[start][0];b=units.spans[stop][0] if stop<len(units.items) else units.spans[-1][1]
    updated=s2[:a]+''.join(result)+s2[b:]
    regiontext=p.kjn_profile.plain_texts(''.join(result))
    assert '안전관리 예산 제약성' not in regiontext
    assert 'Part E.' not in regiontext and 'Part D. 시스템 특성 인식' not in regiontext
    assert '21문항 또는 33문항' not in regiontext
    for label in ['Part A.','Part B.']:
        assert regiontext.count(label)==2
    for label in ['Part C. 시스템 특성 인식','Part D. 경보 피로도 완화']:
        assert regiontext.count(label)==1
    report={'deleted_budget_units':deleted,'changed_units':changed,'other_regions_exact':True,'retained_table_geometry':'Unmodified XML except direct text and affected lineseg caches','survey_counts':{'adopting':29,'non_adopting':17}}
    return updated,report


if __name__=='__main__':
    out=Path(__file__).resolve().parent
    source=(out/'section2.xml').read_text(encoding='utf8')
    updated,report=patch_surveys(source)
    md=(ROOT/'01.docs/부록1_설문지_양식.md').read_text(encoding='utf8')
    units=p.Units(updated,set()).items
    a=next(i for i,u in enumerate(units) if p.nows(u['text'])=='부록(도입현장)')
    b=next(i for i,u in enumerate(units) if u['text'].startswith('부록 2.'))
    text=p.nows(' '.join(u['text'] for u in units[a:b]))
    questions=re.findall(r'^\| ([BCD]-\d+) \| (.*?) \|',md,re.M)
    for label,question in questions:
        expected=2 if label.startswith('B-') else 1
        assert text.count(p.nows(label+question))==expected,(label,expected)
    md_guides=[line.replace('**','') for line in md.splitlines() if line.startswith(('※ Part A는','전자 설문 첫 섹션','Google 계정 로그인','※ Part C는','※ Part D에서는'))]
    for guide in md_guides:
        assert p.nows(guide) in text,guide
    report['validation']={'likert_questions':len(questions),'all_question_texts_match_md':True,'updated_guides_match_md':True,'hwpx_write_executed':False}
    (out/'survey_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report['validation'],ensure_ascii=False))
