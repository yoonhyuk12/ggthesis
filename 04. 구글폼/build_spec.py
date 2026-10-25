"""Export the authoritative appendix into a Google Forms implementation spec."""
from pathlib import Path
import copy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / '01.docs/부록1_설문지_양식.md'
OUT = Path(__file__).resolve().parent
raw = SOURCE.read_text(encoding='utf-8-sig')

def plain(text):
    return re.sub(r'<[^>]+>', '', text.replace('**', '').replace('&emsp;', ' ')).strip()

title = '중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로'
intro = raw.split('안녕하십니까?', 1)[1].split('> 도입 현장용', 1)[0]
intro = '안녕하십니까?\n\n' + plain(intro)
intro = re.sub(r'\n{3,}', '\n\n', intro)
common_help = plain(raw.split('# 공통부 — 두 양식에 공통으로 싣는다', 1)[1].split('## 조사 관리용', 1)[0])
metadata_help = '현장명과 성명은 현장 명부 연결과 중복 제출 확인에 사용하며, A∼E의 측정 문항 수(21문항 또는 33문항)에 포함하지 않습니다.'
likert = ['① 전혀 그렇지 않다', '② 그렇지 않다', '③ 보통이다', '④ 그렇다', '⑤ 매우 그렇다']
blocks = {}
for letter in 'ABCDE':
    heading, body = raw.split('## Part '+letter+'. ', 1)[1].split('\n', 1)
    body = body.split('\n## ', 1)[0].split('\n---', 1)[0]
    help_text = plain(body.split('**A-1)', 1)[0] if letter == 'A' else body.split('| 번호', 1)[0])
    questions = []
    if letter == 'A':
        for m in re.finditer(r'\*\*(A-\d)\)\*\* ([^\n]+)\n(.*?)(?=\n\*\*A-|\Z)', body, re.S):
            qid, prompt, tail = m.groups()
            notes = [plain(line) for line in tail.splitlines() if line.startswith('※')]
            if qid == 'A-9':
                notes = []
            q = dict(id=qid, title=qid+') '+prompt, prompt=prompt, required=True, help='\n'.join(notes))
            if qid in ('A-3','A-4'):
                q.update(type='SHORT_ANSWER', validation={'kind':'REGEX','pattern':'^[0-9]+$','error':'0 이상의 정수만 입력해 주십시오.'}, unit='세' if qid=='A-3' else '년')
                q['help'] = ('만 나이(세)를 숫자로 입력해 주십시오.' if qid=='A-3' else '경력(년)을 숫자로 입력해 주십시오.\n'+q['help'])
            else:
                option_text = ' '.join(line for line in tail.splitlines() if line.startswith('&emsp;'))
                options = [plain(x) for x in re.split(r'[①②③④⑤]',option_text)[1:]]
                other = qid in ('A-5','A-7')
                q.update(type='MULTIPLE_CHOICE', options=options[:-1] if other else options, native_other=other)
            if qid in ('A-7','A-8','A-9'):
                q['help'] += ('\n' if q['help'] else '')+'※ A-7∼A-9는 설문 응답일 직전 1개월 동안 귀하가 담당하시는 현장의 실제 상황을 기준으로 응답해 주십시오.'
            if qid=='A-7':
                q['help'] += '\n※ A-7의 ‘안전관리 담당자’는 선임된 안전관리자뿐 아니라, 전담 안전관리자가 없는 현장에서 안전관리 업무를 맡는 분을 포함합니다.'
            questions.append(q)
    else:
        for qid,prompt in re.findall(r'\| ([B-E]-\d) \| ([^|]+?) \|', body):
            questions.append(dict(id=qid,title=qid+') '+prompt,prompt=prompt,type='MULTIPLE_CHOICE',required=True,help='',options=likert.copy(),native_other=False))
    blocks[letter] = dict(title='Part '+letter+'. '+heading,description=help_text,questions=questions)

section0 = dict(id='START',title='현장 구분 및 조사 안내',description=common_help+'\n\n'+metadata_help,questions=[
    dict(id='GROUP',title='귀하가 담당하시는 현장은 도입현장입니까, 미도입현장입니까?',type='MULTIPLE_CHOICE',required=True,help='연구자로부터 안내받은 현장 구분에 따라 선택해 주십시오. 도입현장은 본 시스템을 설치하여 응답일 현재 3개월 이상 정상 운용이 확인된 현장, 미도입현장은 본 시스템을 설치·운용하지 않는 현장입니다. 이 선택은 해당 설문 문항으로 이동하기 위한 것으로, 분석용 집단 구분은 연구자가 확인한 현장 명부를 기준으로 합니다.',options=['CCTV YOLO-LLM 안전알림 도입 현장', 'CCTV YOLO-LLM 안전알림 미도입 현장'],go_to={'CCTV YOLO-LLM 안전알림 도입 현장':'ADOPTED_A','CCTV YOLO-LLM 안전알림 미도입 현장':'NONADOPTED_A'},native_other=False),
    dict(id='SITE_NAME',title='현장명',type='SHORT_ANSWER',required=True,help='현재 담당하시는 현장명을 적어 주십시오.\n예시 : 00지구 수리시설개보수사업'),
    dict(id='NAME',title='성명',type='SHORT_ANSWER',required=True,help='')
],next='BY_GROUP_ANSWER')
sections=[section0]
for prefix,letters,label in [('ADOPTED','ABCDE','도입현장'),('NONADOPTED','ABC','미도입현장')]:
    for i,letter in enumerate(letters):
        s=copy.deepcopy(blocks[letter])
        s.update(id=prefix+'_'+letter,title=label+' · '+s['title'],next=prefix+'_'+letters[i+1] if i+1<len(letters) else 'SUBMIT')
        sections.append(s)

spec=dict(schema_version=1,source='01.docs/부록1_설문지_양식.md',source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),title=title,description=intro,
    settings=dict(collect_email=False,require_sign_in=False,limit_one_response=False,shuffle_questions=False,show_progress_bar=True,publish_response_summary=False,confirmation_message='끝까지 응답해 주셔서 진심으로 감사합니다.',quiz=False),
    counts=dict(unique_measurement_questions=33,adopted_measurement_questions=33,nonadopted_measurement_questions=21,management_questions=3,adopted_total_questions=36,nonadopted_total_questions=24,editor_total_questions=57,sections=9),
    sections=sections,analysis_notes=['GROUP는 분기용 관리 항목이다. 최종 집단 구분은 연구자 확인 현장 명부를 따른다.','첫 질문·현장명·성명은 21/33개 측정 문항 수에서 제외한다.','연구자가 현장명과 성명으로 명부를 대조하고 내부 현장 ID를 부여한다. 분석용 사본에서는 현장명과 성명을 모두 제거하고 코드로 관리한다.','D·E 모두 1∼5점 응답만 받으며 비해당 선택지를 두지 않는다. 미도입 집단의 D·E 미응답은 설계상 비해당으로 구분한다.','단일 폼에서 공통 A/B/C가 두 경로에 복제되므로 자료 정리 시 해당 경로의 답을 같은 문항 ID로 합친다.','선택 집단과 명부가 다르면 연구자가 확인하며, 자기보고만으로 집단을 확정하거나 바꾸지 않는다.'])
assert [len(blocks[x]['questions']) for x in 'ABCDE']==[9,8,4,8,4]
assert sum(len(s['questions']) for s in sections)==57
for section in sections[1:]:
    for q in section['questions']:
        assert q['prompt'] in raw
assert sections[5]['next']==sections[8]['next']=='SUBMIT'
assert all(not q.get('native_other') for s in sections for q in s['questions'] if q['id'] not in ('A-5','A-7'))
(OUT/'survey-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[title,'',intro,'','설정: 로그인 요구 안 함 / 이메일 수집 안 함 / 1회 제한 안 함 / 문항 순서 섞기 안 함 / 응답 요약 공개 안 함','']
for s in sections:
    lines += ['=== '+s['id']+' | '+s['title']+' ===',s['description']]
    for q in s['questions']:
        lines += [q['title']+' [필수 · '+q['type']+']',q.get('help','')]
        lines += ['- '+option for option in q.get('options',[])]
        if q.get('native_other'):lines+=['- Google Forms 기본 기타(직접 입력)']
        if q.get('validation'):lines+=['입력 검증: 정규표현식 일치 ^[0-9]+$ (0 이상의 정수)']
        if q.get('go_to'):lines += ['답변별 이동: '+json.dumps(q['go_to'],ensure_ascii=False)]
    lines += ['섹션 종료 후: '+s['next'],'']
(OUT/'browser-build-instructions.txt').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(spec['counts'],ensure_ascii=False))
print('PASS: all 54 route-specific measurement prompts are literal matches in the authoritative source; 33 unique items; A/B/C/D/E counts 9/8/4/8/4; both paths terminate at SUBMIT.')
