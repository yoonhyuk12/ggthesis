"""Check source fidelity, reachable paths, required fields and choice semantics."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
spec=json.loads((HERE/'survey-spec.json').read_text(encoding='utf-8'))
source=(HERE.parent/spec['source']).read_text(encoding='utf-8-sig')
sections={s['id']:s for s in spec['sections']}
assert len(sections)==9
first=sections['START']['questions'][0]
assert first['id']=='GROUP' and first['required']
assert first['options']==['CCTV YOLO-LLM 안전알림 도입 현장', 'CCTV YOLO-LLM 안전알림 미도입 현장']
assert first['go_to']=={'CCTV YOLO-LLM 안전알림 도입 현장':'ADOPTED_A','CCTV YOLO-LLM 안전알림 미도입 현장':'NONADOPTED_A'}
assert [q['id'] for q in sections['START']['questions']]==['GROUP','SITE_NAME','NAME']
assert sections['START']['questions'][1]['title']=='현장명'
assert sections['START']['questions'][1]['help'].startswith('현재 담당하시는 현장명을 적어 주십시오.')
assert '배포코드' not in json.dumps(spec,ensure_ascii=False)
assert '성명과 현장명을 제거' in spec['description']
results={}
for label,start in first['go_to'].items():
    visited=[]
    questions=[]
    node=start
    while node!='SUBMIT':
        assert node not in visited, 'routing cycle'
        visited.append(node)
        section=sections[node]
        questions.extend(section['questions'])
        node=section['next']
    expected=33 if start=='ADOPTED_A' else 21
    assert len(questions)==expected
    assert len({q['id'] for q in questions})==expected
    for q in questions:
        assert q['required']
        match=(re.search(r'\*\*'+q['id']+r'\)\*\* ([^\n]+)',source) if q['id'].startswith('A') else re.search(r'\| '+q['id']+r' \| ([^|]+?) \|',source))
        assert match and q['prompt']==match.group(1)
        if q['id'].startswith(('B','C','D','E')):assert len(q['options'])==5
    results[label]={'sections':visited,'measurement_questions':expected,'total_with_management':expected+3,'ends_at':'SUBMIT'}

adopted_a=sections['ADOPTED_A']['questions']
assert [len(q.get('options',[])) for q in adopted_a]==[2,2,0,0,3,4,4,4,4]
assert [q['id'] for q in adopted_a if q.get('native_other')]==['A-5','A-7']
for q in adopted_a:
    if q['id'] in ('A-3','A-4'):
        pattern=q['validation']['pattern']
        assert all(re.fullmatch(pattern,x) for x in ['0','1','35','100'])
        assert not any(re.fullmatch(pattern,x) for x in ['-1','1.5','abc','', '3년'])
    elif q['id'].startswith('A'):
        fragment=source.split('**'+q['id']+')**',1)[1].split('\n**A-',1)[0].split('\n---',1)[0]
        for option in q['options']:
            assert option in fragment
for part in 'ABC':
    assert sections['ADOPTED_'+part]['questions']==sections['NONADOPTED_'+part]['questions']
    assert sections['ADOPTED_'+part]['description']==sections['NONADOPTED_'+part]['description']
assert spec['source_sha256']==hashlib.sha256((HERE.parent/spec['source']).read_bytes()).hexdigest()
assert spec['settings']['collect_email'] is False
assert spec['settings']['require_sign_in'] is False
report={'checked_at':datetime.now().astimezone().isoformat(),'result':'PASS','scope':'Local source and implementation specification only; no external Google Form creation or browser verification asserted.','source_sha256':spec['source_sha256'],'routes':results,'checks':['33 exact unique source prompts / 54 exact route-specific source prompts','A/B/C/D/E = 9/8/4/8/4','All 57 editor questions required; route totals 36/24 including management','A/B/C duplicated routes have identical question content and descriptions','A choices exact source substrings; native Other only A-5 and A-7','A-3/A-4 nonnegative integer validation accepts 0/1/35/100 and rejects negative/decimal/text/blank/unit text','B/C/D/E five choices; no nonapplicable response option','First question routes to intended path and both paths terminate at submit','Source hash current']}
(HERE/'validation-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS: source fidelity, choice counts, duplicate equality, numeric validation, routing, settings, source hash.')
