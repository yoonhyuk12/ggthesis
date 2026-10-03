"""Serialize this Codex worker's authored cognitive-review judgments; no model API."""
from collections import Counter
import csv
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
REPO = OUT.parent.parent
QUESTIONNAIRE = REPO / '01.docs/부록1_설문지_양식.md'
DESIGN = REPO / '01.docs/04_연구설계.md'
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec='seconds')
DATASET_URL = 'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea'
FIELDS = ['uuid','professional_persona','persona','skills_and_expertise',
          'skills_and_expertise_list','career_goals_and_ambitions','sex','age',
          'occupation','province','district']

def dump(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def extract_questions(text):
    result = {}
    lines = text.splitlines()
    for n,line in enumerate(lines, 1):
        a = re.match(r'^\*\*(A-\d)\)\*\* (.+)$',line)
        bcde = re.match(r'^\| ([B-E]-\d) \| (.+?) \|',line)
        if a or bcde:
            code, question = (a or bcde).groups()
            options = []
            if a:
                for nxt in lines[n:]:
                    if not nxt.startswith('&emsp;'):
                        break
                    options.append(nxt)
            result[code] = {'code':code,'question_text':question,'source_line':n,
                'options_source_markdown':'\n'.join(options) if a else '① 전혀 그렇지 않다 — ② 그렇지 않다 — ③ 보통이다 — ④ 그렇다 — ⑤ 매우 그렇다'}
    return result

source_text = QUESTIONNAIRE.read_text(encoding='utf-8')
questions = extract_questions(source_text)
instructions = [line for line in source_text.splitlines() if line.startswith('※')]
raw = {}
request_log = []
for path in sorted(OUT.glob('*.json')):
    if path.name.startswith(('page_','search_','construction_','civil_','architectural_','preview_','dataset_metadata')):
        obj = json.loads(path.read_text(encoding='utf-8'))
        request_log.append({'artifact':path.name, **{k:obj[k] for k in
            ['url','requested_at_utc','completed_at_utc','status','bytes','sha256','error','error_body'] if k in obj}})
        for rr in obj.get('data',{}).get('rows',[]):
            raw[rr['row_idx']] = (path.name,obj,rr)
metadata = json.loads((OUT/'dataset_metadata.json').read_text(encoding='utf-8'))
revision = metadata['data']['sha']

case_specs = [
    ('P1',1187,'S1','시공사','현장 관리감독자(토목 공정·안전 점검)',True,
     '경기 소재 토목 관리자이며 원본에 현장 안전 점검·협력업체 관리가 명시되어 있다.'),
    ('P2',1213,'S2','발주청 측 감리업무를 맡은 감리기관','전기 감리원',False,
     '경기 건설현장에서 설비 감독과 현장 안전 규정 감독을 수행하는 전기 감리 기술자이다.'),
    ('P3',1281,'S3','시공사','현장 관리감독자(토목 공정·계약 조정)',True,
     '경기 토목 관리자이며 현장 안전보건 체계와 공사비 협상 업무가 원본에 있다. 자문역 전환은 목표이므로 현직 관리자 설정과 충돌하지 않는다.'),
    ('P4',1479,'S4','시공사','현장 관리감독자(공정·협력업체 조정)',False,
     '경기 토목 현장 기술자로 공정 관리와 협력업체 조정 업무가 명시되어 있다. 관리감독자라는 가상 보직은 시험용이며 법정 선임 사실로 보지 않는다.'),
    ('P5',1034,'S5','시공사','현장소장',True,
     '강원 중소 건설현장 소장으로 원본에 안전 관리 감독 업무도 있다. 경기의 확인된 적합 직무가 4개여서 범위를 넓혔다.'),
    ('P6',310,'S6','발주청 측 감리업무를 맡은 감리기관','토목 감리원',False,
     '충북 토목 감리 기술자로 현장 안전 점검과 공정 조율 업무가 명시되어 있다. 경기 외 보완 사례이다.'),
]
sites = []
for number in range(1,7):
    adopted=number<=4
    alerts=number<=2
    condition='adopted_alerts' if alerts else ('adopted_no_alerts' if adopted else 'not_adopted_no_cctv')
    sites.append({'site_id':f'S{number}','test_condition':condition,
        'installation_group':'도입' if adopted else '미도입','installed':adopted,
        'normal_operation_confirmed':True if adopted else None,
        'actual_alert_experience':alerts,'cctv_present':adopted,'case_ids':[f'P{number}'],
        'description':('설치·정상 운용을 확인했고 실제 알림 수신·확인 경험 있음' if alerts else
            '설치·정상 운용을 확인했으나 실제 알림 수신·확인 경험 없음' if adopted else
            '미설치·미운용·CCTV 없음; 전화·현장 보고 이용 가능이라는 시험 조건'),
        'construction_amount_krw':None,'location':None,'operation_duration':None})
people = []
for pid,index,site,affiliation,role,budget,why in case_specs:
    path,obj,rr = raw[index]
    r = rr['row']
    experience = {
      'equipment_configuration':pid in ('P1','P3'),
      'different_manufacturer_camera_integration':pid in ('P1','P3'),
      'dense_alerts':pid=='P1',
      'poor_network':pid=='P1',
      'alert_content_compared_with_site':pid in ('P1','P2'),
      'actual_alert_received_and_read':pid in ('P1','P2'),
    }
    people.append({'persona_id':pid,'source_row_index':index,'uuid':r['uuid'],
      'source_name':r['professional_persona'].split(' 씨는',1)[0],
      'name_basis':'professional_persona 첫 문장의 이름을 그대로 추출',
      'source_fields':{k:r[k] for k in FIELDS},'selection_reason':why,
      'provenance':{'dataset':DATASET_URL,'config':'default','split':'train',
          'source_request_url':obj['url'],'retrieved_at_utc':obj['completed_at_utc'],
          'viewer_dataset_revision':obj['headers'].get('x-revision'),
          'repository_revision_observed':revision,'raw_response_file':path,
          'response_body_sha256':obj['sha256'],'truncated_cells':rr.get('truncated_cells',[]),
          'single_row_locator_url':f'https://datasets-server.huggingface.co/rows?dataset=nvidia%2FNemotron-Personas-Korea&config=default&split=train&offset={index}&length=1',
          'locator_note':'위 단일행 URL은 재조회용 위치이며 이번 추출은 source_request_url의 100행 응답에서 수행했다.'},
      'scenario_assumptions':{'site_id':site,'test_condition':next(x['test_condition'] for x in sites if x['site_id']==site),'affiliation':affiliation,'role':role,
          'budget_knowledge_scope':'현장 안전관리 예산 편성·집행을 직접 관리하고 관련 문서를 볼 수 있음' if budget else '담당 공정·감리 업무는 알지만 현장 예산 편성·집행액과 별도 지원 결정은 모름',
          'budget_direct_manager':budget,'experience':experience,
          'exact_construction_career_years':None,'budget_amounts_and_support_history':None,
          'site_performance_and_satisfaction':None,'prior_alarm_comparator':None,
          'note':'소속·보직·예산 정보 접근 범위·설치 및 경험 조건은 가상 시험 설정이다. 관련 문서에 접근할 수 있다는 조건도 예산액이나 충분성을 제공하지는 않는다. 원본에 없는 경력연수·성과·비용·만족도는 미상이다.'}})

personas = {'schema_version':'1.0','created_at_kst':NOW,
 'disclosure':'NVIDIA 합성 데이터셋의 원본 레코드 6개이며 실제 조사 참여자가 아니다.',
 'dataset_attribution':{'creator':'NVIDIA','title':'Nemotron-Personas-Korea','url':DATASET_URL,
    'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
    'changes':'원본 관련 필드를 발췌하고 가상 현장·소속·지식범위·경험 조건을 추가했다. 원본 필드의 문구는 변경하지 않았다.'},
 'selection':{'method':'0~1999행을 확인한 뒤 현직 건설 관리·감리 업무가 명시된 사례를 편의 선택. 경기 사례 우선, 부족분은 강원·충북으로 보완.',
    'rows_inspected':2000,'selected':6,'province_counts':{'경기':4,'강원':1,'충청북':1},
    'not_claimed':['확률표본','인구 대표성','경기 지역 대표성','독립 응답자','실증 증거'],
    'rejected_examples':[{'row_index':419,'reason':'현재 구직중으로 명시되어 현재 현장 재직 설정과 충돌'},
      {'row_index':871,'reason':'전직 산업 안전원·현재 구직중이므로 재직자로 바꾸지 않음'},
      {'row_index':180,'reason':'건축자재 영업원으로 현장 관리·감독 담당이라는 근거 부족'},
      {'row_index':1829,'reason':'현장소장은 장래 목표이며 현재 소장으로 바꾸지 않음'}]},
 'scenario_policy':'가상 현장 6곳에 각 1명을 배치했다. 현장과 배치는 모두 시험용이다. 원본 거주지와 가상 현장 위치를 동일시하지 않는다. 성별·연령·학력·가족관계·성격으로 능력이나 기술 수용성을 추정하지 않는다.',
 'sites':sites,'personas':people}

interpretations = {
'B-1':'위험이 커지거나 사고로 이어지기 전에 알아채는지를 묻는다.',
'B-2':'위험을 알아챈 다음 초기 대응 지시가 늦지 않는지를 묻는다.',
'B-3':'안전관리 업무를 맡은 사람이 현장 밖에 있을 때도 위험 소식을 빨리 파악하는지를 묻는다.',
'B-4':'서로 떨어져 있는 사람에게 위험 내용과 해야 할 조치를 전달하는지를 묻는다.',
'B-5':'현재 인원으로 순찰과 위험 확인 업무를 얼마나 원활히 수행하는지를 묻는다.',
'B-6':'중복되거나 불필요하다고 느끼는 확인 때문에 실제 위험 대응을 놓치는지를 묻는다.',
'B-7':'시정이나 작업중지가 필요한 상황에서 실제 조치를 빨리 하는지를 묻는다.',
'B-8':'위험요인이 사고로 이어지지 않도록 실제로 통제하는 정도를 묻는다.',
'C-1':'비싸다고 생각하는 스마트 안전장비를 살 만큼 현장 예산이 있는지를 묻는다.',
'C-2':'장비나 관제 시스템에 사용할 안전관리 예산이 충분히 배정되었는지를 묻는다.',
'C-3':'산업안전보건관리비의 계상 기준만으로 장비 도입에 필요한 여건이 갖춰지는지를 묻는다.',
'C-4':'현장 자체 예산 외에 본사나 발주청의 추가 지원을 받기 어려운지를 묻는다.',
'D-1':'사무용 PC로 운영할 수 있다는 점과 별도 장비 투자 부담이 작은지를 함께 묻는다.',
'D-2':'제조사가 다른 기존 카메라를 교체하지 않고 연결해 사용할 수 있는지를 묻는다.',
'D-3':'알림이 몰릴 때 반복 발송이 제한되는지와 느려지거나 멈추지 않는지를 함께 묻는다.',
'D-4':'통신이 나쁠 때에도 위험을 판별하는 기능이 유지되는지를 묻는다.',
'D-5':'나무·그림자 등 배경을 사람이나 위험으로 잘못 알린 경우가 드문지를 묻는다.',
'D-6':'정상 작업을 위험으로 잘못 알리지 않는지와 시스템이 작업 맥락을 이해하는지를 함께 읽게 된다.',
'D-7':'위험 요약과 이미지가 메신저로 빨리 도착했다고 느끼는지를 묻는다.',
'D-8':'메신저 알림의 내용만 보고도 현장 상황을 이해할 수 있는지를 묻는다.',
'E-1':'위험 아닌 상황을 거르는 기능 덕분에 알림 확인 스트레스가 이전보다 줄었는지를 묻는다.',
'E-2':'불필요한 알림 확인 시간이 줄고 업무 집중이 늘었다고 느끼는지를 묻는다.',
'E-3':'잘못 온 알림이라 여겨 무시하는 대신 곧바로 확인하는 일이 이전보다 늘었는지를 묻는다.',
'E-4':'도입 이후 알림 피로감이 도입 전보다 줄었다고 느끼는지를 묻는다.',
}
b_needed = {
'B-1':'담당 현장에서 위험을 발견한 상황과 발견 시점에 대한 기억',
'B-2':'위험 인지 후 초동 대응을 지시했던 경험',
'B-3':'현장 밖 안전관리 담당자에게 전화·보고·영상 등으로 위험을 알린 경험',
'B-4':'거리나 위치가 다른 사람들 사이의 위험 정보·조치 전달 경험',
'B-5':'현재 순찰 인력, 업무량과 순찰·위험 확인의 체감 수행 수준',
'B-6':'중복 확인과 실제 위험 대응에 시간을 썼던 경험',
'B-7':'시정·작업중지가 필요했던 사건과 실제 조치 경험',
'B-8':'위험요인 통제 조치가 현장에서 이행되었다고 느낀 근거',
}

def evaluate(p, code):
    s=p['scenario_assumptions']; site=s['site_id']; pid=p['persona_id']; src=p['source_fields']
    role=s['role']; budget=s['budget_direct_manager']; exp=s['experience']
    q=questions[code]
    o={'persona_id':pid,'uuid':p['uuid'],'source_row_index':p['source_row_index'],'site_id':site,
       'group':'미도입' if pid in ('P5','P6') else '도입','code':code,
       'question_text':q['question_text'],'question_source_line':q['source_line'],
       'options_source_markdown':q['options_source_markdown'],'applicable_item':True,
       'status':'needs_information','interpretation':interpretations.get(code,''),'reason':'',
       'evidence_type':'scenario_information_gap','evidence_refs':['scenario_assumptions'],
       'information_needed':[],'ambiguous_expression':[],'non_applicable_handling':'',
       'numeric_selection':None,'numeric_selection_basis':None,
       'virtual_utterance':'','wording_issue_candidate':False,'respondent_access_risk':False,
       'scenario_information_gap':False}
    def result(status, interpretation, reason, evidence, utterance, need=None, ambiguous=None):
        o.update(status=status,interpretation=interpretation,reason=reason,evidence_type=evidence,
                 virtual_utterance=utterance,information_needed=need or [],ambiguous_expression=ambiguous or [])
        o['wording_issue_candidate']=evidence=='item_wording'
        o['respondent_access_risk']=evidence=='respondent_knowledge_scope'
        o['scenario_information_gap']=evidence=='scenario_information_gap'
        if evidence=='item_wording':
            o['evidence_refs']=['questionnaire.'+code,'scenario_assumptions']
        elif evidence=='respondent_knowledge_scope':
            o['evidence_refs']=['scenario_assumptions.budget_knowledge_scope','questionnaire.'+code]
        return o
    if code=='A-1':
        return result('answerable','소속이 시공사 측인지 발주청·감리 측인지를 고르는 항목이다.',
          f'가상 소속은 {s["affiliation"]}로 명시했다. 원본 소속 사실로 확정한 것은 아니므로 번호 선택은 하지 않는다.',
          'scenario_assumption',f'이 시험에서는 {s["affiliation"]} 소속으로 읽겠습니다.')
    if code=='A-2':
        n=1 if src['sex']=='남자' else 2
        o=result('answerable','성별 보기에서 원본 필드에 해당하는 범주를 고른다.',
           f'원본 sex가 {src["sex"]}로 제공되어 있다. 이 정보는 다른 문항의 능력·태도 추정에 사용하지 않는다.',
           'source_fact',f'원본에 적힌 성별은 {src["sex"]}입니다.')
        o.update(numeric_selection=n,numeric_selection_basis='source_fields.sex',evidence_refs=['source_fields.sex']); return o
    if code=='A-3':
        age=src['age']; n=min(age//10-1,5)
        o=result('answerable','원본 나이가 속하는 연령 구간을 고른다.',
           f'원본 age={age}를 현행 보기 구간에 대입한다. 숙련도나 기술 수용성을 나이로 추정하지 않는다.',
           'source_fact',f'{age}세이므로 해당 연령 구간을 고르겠습니다.')
        o.update(numeric_selection=n,numeric_selection_basis='source_fields.age',evidence_refs=['source_fields.age']); return o
    if code=='A-4':
        return result('needs_information','안전관리·감독·시공관리 등 실제 현장 업무 기간을 합산하는 항목이다.',
           '원본의 베테랑·수십 년 같은 서술만으로 정확한 누적 현장 경력은 정하지 않았다. 나이·졸업 시점에서 경력을 만들어내지 않는다.',
           'scenario_information_gap','현장 경력을 합쳐 적는 뜻은 알지만, 제 이력의 정확한 기간은 이 자료에 없습니다.',
           ['경력증명 또는 본인이 확인한 현장 업무 누적 기간'])
    if code=='A-5':
        if pid=='P5':
            o=result('answerable','현장에서 맡은 대표 역할을 고르는 항목이다.',
              '원본 professional_persona에 중소 건설현장의 소장이라고 명시되어 가상 보직과도 일치한다.',
              'source_fact','현장소장이라고 적혀 있으므로 그 보기를 고르겠습니다.')
            o.update(numeric_selection=3,numeric_selection_basis='source_fields.professional_persona',evidence_refs=['source_fields.professional_persona']); return o
        return result('ambiguous','현장 역할을 네 개 보기 가운데 분류하는 항목이다.',
          f'가상 역할은 {role}이다. 관리감독자·감리원 이름이 보기에는 없어 공사감독에 포함할지 기타에 적을지 확인이 필요하다. 기타란은 있으므로 응답 자체가 불가능하지는 않다.',
          'item_wording',f'저는 {role}인데 공사감독을 고르는지 기타에 적는지 망설여집니다.',
          ['조사자가 의도한 역할 범주 매핑'],['공사감독','기타'])
    if code=='A-6':
        return result('needs_information','현재 맡은 현장의 공사금액을 보기 구간에 맞춰 고르는 항목이다.',
          '가상 현장의 공사금액을 제공하지 않았으므로 선택할 수 없다. 원문의 구간 기준 확정 필요 표시도 그대로 보존했다. 정보 미제공은 새로운 문항 결함이 아니다.',
          'scenario_information_gap','공사금액이 주어지면 구간을 고를 수 있지만, 이 시험에는 금액이 없습니다.',
          ['담당 현장 공사금액','원문에 남은 공사금액 구간 기준 확정'])
    if code.startswith('B-'):
        extra='도입 여부만으로 수행 수준을 높거나 낮다고 정하지 않는다.'
        speech=f'{role}으로 경험한 현장의 일을 떠올리는 질문인데, 실제 수행 수준은 여기 주어지지 않았습니다.'
        if code=='B-3':
            extra='기존 안내가 전담 안전관리자뿐 아니라 안전관리 업무 담당자를 포함한다. 문항에는 CCTV라는 제한이 없다.'
            speech='CCTV가 없어도 전화나 현장 보고로 밖에 있는 담당자에게 상황을 알릴 수 있습니다. 얼마나 빨리 파악했는지는 실제 경험이 필요합니다.' if pid in ('P5','P6') else '담당자가 밖에 있을 때도 알게 되는지를 묻는군요. 전화·보고·알림을 모두 떠올릴 수 있습니다.'
        return result('needs_information',interpretations[code],
          '해당 현장의 수행 경험·수준이 시나리오에 없어서 평정하지 않았다. '+extra,
          'scenario_information_gap',speech,[b_needed[code]])
    if code=='C-1':
        return result('ambiguous',interpretations[code],
          '고가가 어느 장비·가격대인지 기준이 없다. 같은 현장 예산이라도 서로 다른 장비를 떠올릴 가능성을 확인할 필요가 있다. 예산액 미제공은 별개이다.',
          'item_wording','제가 떠올리는 고가 장비와 다른 분이 떠올리는 장비가 같을까요?',
          ['응답자가 떠올리는 장비와 비용 범위','현장의 예산 여건에 대한 인식'],['고가'])
    if code=='C-3':
        return result('ambiguous',interpretations[code],
          '계상 기준만으로는이라는 표현이 확보되는 금액의 부족을 뜻하는지, 지출 가능 범위 같은 제도 제약을 뜻하는지 나뉠 수 있다. 법령 내용이나 현장 적용 결과를 이 시험에서 판단하지 않는다.',
          'item_wording','관리비가 모자란다는 뜻인지, 그 돈으로 해당 장비를 살 수 없다는 뜻인지 먼저 확인하고 싶습니다.',
          ['측정하려는 제약의 범위','실제 응답자가 계상 기준을 이해하는 방식'],['산업안전보건관리비 계상 기준만으로는'])
    if code in ('C-2','C-4'):
        needed='예산 편성 내역과 장비 도입 여건' if code=='C-2' else '본사·발주청 지원 절차와 지원 경험'
        if budget:
            return result('needs_information',interpretations[code],
              f'시험에서는 예산을 직접 관리하고 자료에 접근할 수 있게 설정했다. 다만 {needed} 자체를 제공하지 않아 답을 만들지 않았다. 문항 결함으로 계산하지 않는다.',
              'scenario_information_gap','예산 자료를 확인할 역할은 맡았지만, 이 시험에는 실제 금액이나 지원 이력이 없습니다.',[needed])
        return result('needs_information',interpretations[code],
          '가상 지식범위에서 예산 편성·집행액과 지원 결정을 모른다고 설정했다. 현실의 같은 직무에서도 답하기 어려운지는 실제 면담으로 확인해야 하며, 확인된 결함으로 단정하지 않는다.',
          'respondent_knowledge_scope',f'저는 {role} 업무를 맡지만 예산 편성이나 별도 지원 결정까지는 모릅니다.',[needed,'응답자가 실제로 접근하는 예산 정보 범위'])
    if code.startswith(('D-','E-')):
        requirement={'D-1':'equipment_configuration','D-2':'different_manufacturer_camera_integration',
           'D-3':'dense_alerts','D-4':'poor_network','D-5':'alert_content_compared_with_site',
           'D-6':'alert_content_compared_with_site','D-7':'actual_alert_received_and_read',
           'D-8':'actual_alert_received_and_read'}.get(code,'actual_alert_received_and_read')
        if not exp[requirement]:
            desc={'equipment_configuration':'장비 구성','different_manufacturer_camera_integration':'다른 제조사 카메라 연결',
                'dense_alerts':'알림이 짧은 시간에 몰린 상황','poor_network':'통신 상태가 나쁜 상황',
                'alert_content_compared_with_site':'알림과 실제 현장 상황 대조','actual_alert_received_and_read':'실제 알림 수신·확인'}[requirement]
            o=result('not_applicable',interpretations[code],
                f'시험 조건에서 {desc} 경험이 없다. 현행 D·E 안내가 경험 없는 문항의 비해당을 이미 허용하므로 안내대로 처리한다.',
                'existing_instruction',f'{desc}을 경험하지 않았으므로 안내대로 비해당이라고 적겠습니다.')
            o['non_applicable_handling']='문항 옆에 비해당 표기; 0점·불성실 응답으로 보지 않음; 공통부 응답 유지'
            o['evidence_refs']=['scenario_assumptions.experience.'+requirement,'questionnaire.instructions.'+code[0]]
            return o
    if code=='D-1':
        return result('ambiguous',interpretations[code],
          '장비 구성 경험은 있지만 일반 PC 구동과 투자 부담은 별개의 판단이다. 직접 예산을 관리하는 역할이어도 구성비·구매비가 없으면 투자 부담까지 정할 수 없다.',
          'item_wording','어떤 PC를 썼는지와 돈이 적게 들었는지는 따로 생각해야 할 것 같습니다.',
          ['직접 경험한 장비 구성','별도 장비 구입·이용 부담에 대한 인식'],['일반 사무용 PC','투자 부담이 적다'])
    if code=='D-2':
        return result('needs_information',interpretations[code],
          '다른 제조사 카메라 연결을 경험했다는 조건만 부여했다. 실제 교체 여부와 사용 결과를 제공하지 않았으므로 호환 성공을 가정하지 않는다.',
          'scenario_information_gap','제가 연결해 본 카메라를 기준으로 답해야겠네요. 교체했는지와 연결 결과는 이 시험에 없습니다.',
          ['경험한 카메라의 제조사·연결 방식·교체 여부와 사용 결과'])
    if code=='D-3':
        return result('ambiguous',interpretations[code],
          '알림 밀집 경험은 부여했으나 반복 발송 제한과 지연·정지를 한 평정에 묶는다. 두 관찰이 엇갈릴 때의 응답 기준은 경험 안내만으로 결정되지 않는다. 제어 안정성이라는 측정 취지는 유지해야 한다.',
          'item_wording','반복 알림은 적었지만 화면은 느렸다면 어느 쪽을 기준으로 표시하나요?',
          ['알림 밀집 상황에서 관찰한 반복 발송·지연·정지','두 판단이 다를 때의 응답 기준'],['반복 발송을 제한하여','느려지거나 멈추지 않고'])
    if code=='D-4':
        return result('ambiguous',interpretations[code],
          '통신 불량 경험을 부여했더라도 알림이 안 온 것과 내부 위험 판별이 멈춘 것을 화면만으로 구별할 수 있는지는 별도이다. 특정 설계나 정상 성능은 추정하지 않는다.',
          'item_wording','연결이 나쁠 때 메시지가 늦은 건 알겠는데, 위험을 가려내는 기능까지 돌아갔는지는 어떻게 알죠?',
          ['직접 관찰한 위험 판별 화면·운용 상태','응답자가 내부 기능과 전달 지연을 구별할 수 있는지'],['위험 여부를 가려내는 기능'])
    if code=='D-5':
        return result('needs_information',interpretations[code],
          '알림을 현장과 대조한 경험은 있지만 실제 배경 오탐 사례나 체감 빈도를 제시하지 않았다. 원본의 꼼꼼한 직무 서술을 낮은 오탐 빈도의 근거로 쓰지 않는다.',
          'scenario_information_gap','배경 때문에 잘못 온 알림을 떠올려 판단하는 질문입니다. 그 사례와 빈도는 아직 주어지지 않았습니다.',
          ['확인한 알림 가운데 배경을 잘못 인식했다고 느낀 경험'])
    if code=='D-6':
        return result('ambiguous',interpretations[code],
          '정상 작업을 잘못 알리는지는 경험으로 말할 수 있어도 내부적으로 맥락을 파악했는지는 직접 보기 어렵다. 제4장에는 원본 프레임 범위라는 설명이 있으나 설문 안내에는 그 범위가 없다.',
          'item_wording','정상 작업인데 알림이 왔는지는 말할 수 있지만, 시스템이 맥락을 이해했는지는 제가 알기 어렵습니다.',
          ['직접 대조한 정상 작업 알림 사례','촬영 장면·맥락을 응답자가 해석하는 범위'],['작업 상황의 맥락을 파악하여'])
    if code in ('D-7','D-8'):
        needed='요약·이미지 전달이 빨랐다고 느낀 수신 경험' if code=='D-7' else '알림 내용을 보고 이해한 정도와 추가 확인 필요 경험'
        return result('needs_information',interpretations[code],
          '실제 알림 수신·확인 경험은 부여했지만 속도나 이해 용이성은 알려주지 않았다. 도입 또는 수신 사실이 긍정 평정의 근거가 되지는 않는다.',
          'scenario_information_gap','알림은 확인해 보았다는 조건이지만, 빨랐는지 또는 이해하기 쉬웠는지는 아직 정해지지 않았습니다.',[needed])
    if code.startswith('E-'):
        return result('ambiguous',interpretations[code],
          '알림 수신 경험은 있지만 비교할 이전 기간·이전 알림 체계·확인 습관이 제공되지 않았다. 현행 E 안내는 경험 유무를 다루지만 비교 기준을 고정하지 않는다. 회고적 완화 인식이라는 측정 취지는 삭제하지 않는다.',
          'item_wording','줄었다거나 늘었다고 하려면 언제의 어떤 알림과 비교하는지 먼저 알고 싶습니다.',
          ['비교할 도입 전 기간과 알림 체계','비교 가능한 이전 경험이 없는 경우의 처리'],
          ['줄었다' if code!='E-3' else '늘었다','비교 기준기간·이전 알림'])
    raise AssertionError(code)

responses=[]
for person in people:
    for code in questions:
        if person['persona_id'] in ('P5','P6') and code[0] in 'DE':
            continue
        responses.append(evaluate(person,code))

findings=[
 {'id':'F1','priority':'우선 1','codes':['C-2','C-4'],'title':'예산을 모르는 응답자의 처리 기준',
  'case_ids':['P2','P4','P6'],'virtual_utterance':'감리·현장 업무는 알지만 예산이 어떻게 편성됐는지, 추가 지원을 받을 수 있는지는 모릅니다.',
  'finding':'예산을 직접 관리하지 않는 역할의 지식범위에서 답하기 어렵도록 시험했다. 실제 직무에서도 같은 정보 접근 문제가 있는지 확인할 후보이며, 현장 자료를 주지 않아 생긴 공백과 구분해야 한다.',
  'existing_guidance':'C 안내에는 모름·판단 불가 처리 규칙이 없다. D·E의 경험 부재 비해당 안내를 C에 자동 적용할 수는 없다.',
  'ask_human':'실제 업무에서 편성 예산과 본사·발주청 지원 가능성을 어디까지 알고 있습니까? 모르면 ③ 보통이다를 고르게 됩니까?',
  'minimum_change':'먼저 예산 비담당자를 면담한다. 필요하면 C 안내에 모름·판단 불가를 구별하는 방법을 추가하고, 본 조사 전 결측·채점 규칙과 함께 확정한다. 단순히 비해당을 늘리자는 결론은 아니다.'},
 {'id':'F2','priority':'우선 1','codes':['C-1','C-3'],'title':'고가 장비와 계상 기준이 뜻하는 범위',
  'case_ids':['P1','P3','P4','P5'],'virtual_utterance':'어느 정도 장비가 고가인가요? 계상 기준만으로 어렵다는 것은 금액이 부족하다는 말인가요, 사용 가능한 항목의 문제인가요?',
  'finding':'C-1은 떠올리는 장비의 가격대가 달라질 수 있다. C-3은 예산 규모와 제도상 사용 범위를 다르게 읽을 여지가 있다. 법령의 적법성이나 실제 부족액을 판정한 결과는 아니다.',
  'existing_guidance':'C의 5점 척도 안내만으로는 장비 범위나 계상 기준의 의미가 정해지지 않는다.',
  'ask_human':'C-1에서 어떤 장비를 떠올렸습니까? C-3을 자신의 말로 설명하고 그렇게 생각한 현장 사례를 말해 주십시오.',
  'minimum_change':'연구자가 의도한 예산 제약의 범위를 먼저 확정한 뒤 C 안내에 용어 풀이를 짧게 추가한다. 새 가격 기준이나 법 해석을 이 시험에서 임의로 넣지 않는다.'},
 {'id':'F3','priority':'우선 1','codes':['E-1','E-2','E-3','E-4'],'title':'완화 인식의 비교대상과 기간',
  'case_ids':['P1','P2'],'virtual_utterance':'도입 전에 쓰던 알림과 비교하나요, 도입 직후와 최근을 비교하나요? 전에는 알림이 없었다면 어떻게 답하죠?',
  'finding':'E는 완화 인식을 묻는 참고 척도다. 줄었다·늘었다의 비교 시점과 이전 알림 체계가 다르면 같은 문장을 다르게 해석할 수 있다. 비교 정보가 없는 이 사례에 성과 향상을 부여하지 않았다.',
  'existing_guidance':'알림 경험이 없는 경우의 비해당은 이미 안내한다. 현재 알림 경험은 있으나 이전 비교 경험이 없는 경우까지 명확한지는 실제 면담이 필요하다.',
  'ask_human':'어느 기간과 어느 알림 체계를 비교했습니까? 도입 전 알림이 없었을 때도 감소·증가라고 판단할 수 있습니까?',
  'minimum_change':'완화 인식 문구를 유지한 채 E 앞에 비교대상·기간 안내와 비교 경험 부재 처리 기준을 정한다. 현재 수준 문항으로 바꾸거나 문항을 분리하는 것은 별도 측정구성 변경 검토로 남긴다.'},
 {'id':'F4','priority':'우선 1','codes':['D-3'],'title':'반복 발송 제한과 작동 안정성이 엇갈릴 때',
  'case_ids':['P1'],'virtual_utterance':'같은 알림은 덜 왔는데 화면이 느려졌다면 어디에 표시하나요?',
  'finding':'알림 밀집 경험이 있는 사례에서 반복 제한·지연·정지를 한 번에 판단한다. 시스템의 제어 안정성을 묻는 취지는 유지하되 관찰이 서로 다를 때 응답 기준을 확인해야 한다.',
  'existing_guidance':'알림이 짧은 시간에 몰린 경험을 기준으로 하라는 안내는 있다. 서로 다른 관찰 결과를 하나의 평정으로 정하는 기준은 안내하지 않는다.',
  'ask_human':'반복 발송은 줄고 작동은 느려진 상황이라면 몇 번째 보기를 선택하며, 어떤 부분에 더 무게를 둡니까?',
  'minimum_change':'D-3 앞뒤에 제어 안정성을 종합 판단하는 기준을 보충할지 먼저 검토한다. 반복 제한 문구 삭제나 문항 분할은 기존 측정 취지를 바꾸므로 최소 수정과 구분한다.'},
 {'id':'F5','priority':'우선 2','codes':['D-1','D-2','D-4','D-6'],'title':'직접 본 결과와 내부 기능의 추정 구분',
  'case_ids':['P1','P2','P3'],'virtual_utterance':'카메라 연결이나 잘못 온 알림은 확인할 수 있지만 내부에서 맥락을 이해했는지, 통신 불량 때 판별 기능이 계속 돌았는지는 모릅니다.',
  'finding':'장비 구성·호환·통신 불량 경험이 있어도 비용 부담이나 내부 판별 원리까지 아는 것은 아니다. 전기 감리 직무 역시 해당 AI 시스템의 내부 기능을 안다는 근거로 쓰지 않았다.',
  'existing_guidance':'D-1·2는 구성·호환 경험, D-4는 통신 불량, D-5·6은 현장 대조 경험을 요구하므로 경험 없는 사례는 이미 걸러진다. 경험이 있는 사람도 무엇을 관찰해 답하는지는 별도 확인 대상이다.',
  'ask_human':'각 문항을 답할 때 직접 본 화면·알림·설치 경험과 설명을 듣고 추측한 내용을 나눠 말해 주십시오.',
  'minimum_change':'직접 경험한 구성·카메라와 관찰 결과를 기준으로 답하도록 안내를 보완할지 검토한다. D-6의 촬영 장면 범위도 짧게 설명할 수 있다. 문항을 관찰 결과만 묻도록 바꾸는 것은 측정구성 검토 후 결정한다.'},
 {'id':'F6','priority':'유지 확인','codes':['D-1','D-2','D-3','D-4','D-5','D-6','D-7','D-8','E-1','E-2','E-3','E-4'],
  'title':'정상 운용 무알림은 도입이며, 비해당은 문항별로 처리',
  'case_ids':['P3','P4'],'virtual_utterance':'현장은 정상 운용 중이지만 알림은 받은 적이 없습니다. 알림 경험 문항은 비해당이고, 직접 참여한 장비 연결 문항은 따로 읽겠습니다.',
  'finding':'S3·S4를 미도입으로 바꾸지 않았다. P3은 구성·호환 경험을 따로 부여해 D-1·2를 검토했고, 나머지 경험 없는 D·E는 비해당으로 처리했다. P4는 구성·호환 경험도 없어 전용부 전체를 비해당으로 처리했다.',
  'existing_guidance':'현행 안내와 제4장 규칙이 이미 해결한다. 무알림 자체를 문항 결함, 0점, 불성실 응답으로 보지 않는다.',
  'ask_human':'정상 운용하지만 알림을 받은 적이 없을 때, 각 문항 옆에 비해당을 쓰라는 안내를 쉽게 찾고 따를 수 있습니까?',
  'minimum_change':'문구를 유지한다. 실제 종이·온라인 양식에서 문항별 비해당 표시 위치가 눈에 띄는지만 확인한다. D·E 전체를 일괄 건너뛰게 바꾸지 않는다.'},
 {'id':'F7','priority':'유지 확인','codes':['B-3'],'title':'CCTV 없는 현장도 전화·보고로 해석할 수 있음',
  'case_ids':['P5','P6'],'virtual_utterance':'영상은 없어도 전화로 밖에 있는 담당자에게 위험을 알릴 수 있습니다. 실제로 빨리 파악했는지는 경험을 보고 답하겠습니다.',
  'finding':'B-3은 CCTV나 영상 열람을 요구하지 않는다. S5·S6에서 전화·보고를 이용할 수 있다고 설정했으며, 실제 속도와 수행 수준은 미상으로 남겼다.',
  'existing_guidance':'안전관리 담당자가 선임 안전관리자에 한정되지 않는다는 설명이 이미 있다. CCTV 부재만으로 비해당 처리할 이유가 없다.',
  'ask_human':'CCTV가 없는 현장에서 B-3을 읽을 때 전화·보고도 떠올립니까? 여기서 안전관리 담당자는 누구라고 생각합니까?',
  'minimum_change':'문구를 유지하고 해석을 확인한다. 실제 면담에서 영상으로만 오해하는 경우에 한해 공통 안내에 수단을 한정하지 않는다는 설명을 검토한다.'},
 {'id':'F8','priority':'우선 2','codes':['A-5'],'title':'관리감독자·감리원의 역할 보기 매핑',
  'case_ids':['P1','P2','P3','P4','P6'],'virtual_utterance':'관리감독자나 감리원은 공사감독을 고르면 되나요, 기타에 직무를 적으면 되나요?',
  'finding':'조사대상에는 관리감독자와 감리원이 있지만 A-5 보기는 공사감독·안전관리자·현장소장·기타다. 기타란으로 답할 수 있으나 같은 역할이 다르게 분류될 가능성을 점검할 필요가 있다.',
  'existing_guidance':'A-1은 감리원을 포함한다고 설명한다. A-5의 기타란은 탈출 경로지만 역할별 분류 기준까지 정하지는 않는다.',
  'ask_human':'현재 역할을 어떤 보기에 넣었고 이유는 무엇입니까? 공사감독과 시공사 관리감독자를 같은 뜻으로 읽습니까?',
  'minimum_change':'실제 응답자의 분류를 확인한 뒤 A-5 안내 또는 조사자 코딩 지침에 역할별 매핑을 명시한다. 보기 추가는 범주 코딩을 바꾸므로 별도 승인·정합 검토가 필요하다.'},
]

response_package={'schema_version':'1.0','created_at_kst':NOW,
 'disclosure':'가상 발화와 해석·판정은 이 Codex 워커가 작성했다. 실제 사람의 응답, 독립 모델 반복실행, NVIDIA 모델 실행 결과가 아니다.',
 'method':'원본 프로필과 시험 조건을 읽은 단일 워커가 문항별 판단을 작성했다. 반복되는 문구는 공통 판단 기준을 템플릿으로 직렬화했다. build_results.py는 새 LLM 추론을 실행하지 않는다.',
 'status_definition':{
   'answerable':'제공된 원본·명시된 시험 조건으로 응답 내용을 정할 수 있음; 숫자는 원본으로 직접 확정되는 A만 허용',
   'needs_information':'판단에 필요한 현장 경험·자료가 미제공이거나 설정된 직무 지식범위 밖임',
   'ambiguous':'관찰을 평정으로 옮기는 과정의 용어·범위·비교 기준이 여러 해석을 허용함; 확인된 결함이 아니라 면담 후보',
   'not_applicable':'문항별 경험 부재로 현행 D·E 비해당 안내를 적용함'},
 'evidence_type_definition':{
   'source_fact':'합성 원본 필드로 직접 확인',
   'scenario_assumption':'원본과 분리해 명시한 가상 소속·역할 조건',
   'scenario_information_gap':'시나리오에 현장 수치·경험 내용이 없어 판단 못함; 문항 결함으로 집계하지 않음',
   'respondent_knowledge_scope':'시험용 지식범위에서 모르는 정보; 현실에서도 같은지는 면담으로 확인',
   'item_wording':'단일 워커가 지적한 문구·응답 기준의 점검 후보',
   'existing_instruction':'현행 경험 부재 비해당 안내가 해결하는 항목'},
 'questionnaire_source':{'path':'01.docs/부록1_설문지_양식.md','sha256':sha(QUESTIONNAIRE),
   'design_path':'01.docs/04_연구설계.md','design_sha256':sha(DESIGN)},
 'questions':list(questions.values()),'instructions_source_verbatim':instructions,
 'not_administered':[{'persona_id':pid,'codes':[c for c in questions if c[0] in 'DE'],
       'reason':'미도입용 양식에 전용부가 없음; 156개 적용항목에는 포함하지 않음'} for pid in ('P5','P6')],
 'responses':responses,'findings':findings}

manifest={'schema_version':'1.0','created_at_kst':NOW,'purpose':'실제 조사 전 설문 문항 점검',
 'generation':{'agent':'Codex','model_family_from_session_instruction':'GPT-6',
   'exact_model_id':'gpt-6-astra','exact_model_id_note':'코디네이터가 orca orchestration worker-show의 provider.model에서 런타임 값을 확인해 전달한 정보(msg_e003fadc56f8, 2026-10-03T03:50:15Z). 더 세부적인 모델 빌드는 미공개.',
   'temperature':None,'seed':None,'sampling_parameters_note':'세션에 공개되지 않았음; 임의 설정값을 기록하지 않음',
   'nvidia_model_executed':False,'paid_model_api_called':False,'separate_persona_sessions':False,
   'implementation':'이 워커가 작성한 해석·발화를 Python 표준 라이브러리로 JSON/CSV/HTML에 저장'},
 'provenance':{'dataset_url':DATASET_URL,'dataset_revision':revision,'revision_basis':'HF repository API sha와 selected rows 응답 x-revision을 대조',
   'dataset_card_url':DATASET_URL+'/blob/'+revision+'/README.md','license':'CC BY 4.0','creator':'NVIDIA',
   'changes':'관련 원본 필드 발췌; 가상 현장·소속·지식범위 설정 및 LLM 점검 발화 추가',
   'request_log':request_log,'known_download_bytes':sum(r.get('bytes',0) for r in request_log),
   'download_note':'본문을 받은 성공 응답의 바이트 합계이며 HTTP 헤더·실패 응답 본문은 제외. 전체 parquet/약 2GB 데이터셋은 다운로드하지 않음.',
   'records_inspected':2000,'selected_records':6,
   'api_failure_note':'search 3건(500 2건·timeout 1건), 범위 filter 1건(502), equality filter 3건(500 1건·502 2건). 이후 코디네이터 허용에 따라 rows 20페이지(100행씩)로 전환.',
   'local_error_note':'별도의 실제 occupation equality 조회 시도는 Python 모듈 경로 오류로 실행 전에 중단되어 네트워크 요청을 보내지 않음.'},
 'inputs':[{'path':'01.docs/부록1_설문지_양식.md','sha256':sha(QUESTIONNAIRE)},
   {'path':'01.docs/04_연구설계.md','sha256':sha(DESIGN)},
   {'path':'논문양식참조/박종용교수님_논문작성요령20260707.md','sha256':sha(REPO/'논문양식참조/박종용교수님_논문작성요령20260707.md')}],
 'prompt_and_review_focus':{'task_id':'task_e99f93d02c73','dispatch_id':'ctx_8d739c731459',
   'operative_instructions':['실제 원본 직무 프로필 6개로 공통 18문항×6, 도입 전용 12문항×4를 그대로 읽고 해석·답변가능성·필요정보·모호표현·비해당을 점검',
    '사용자 정정 반영: 6개 가상현장×1명; S1·S2 도입·알림 경험, S3·S4 도입·정상 운용 무알림, S5·S6 미도입·CCTV 없음',
    '성과·효율·만족도·예산을 창작하지 말고 현장 정보 미제공과 문항 결함을 구분',
    '성별·나이로 능력·기술수용성을 판단하지 말 것; 점수분포·검정·효과 추정 금지'],
   'coordinator_focus_message':'비교시점(E의 줄었다/늘었다), 복합판단(D3 등), 기술내부를 알아야 하는 문항, 예산담당여부(C), 기존 비해당 안내가 해결하는 항목을 중심으로 실무적인 결과를 작성.',
   'coordinator_preservation_message':'D3는 반복발송 제한으로 풀면서 제어 안정성이라는 측정기능을 유지한 문항이다. E는 경보 피로도 완화 지각을 기술하는 참고척도이므로 과거 대비 표현 자체를 무조건 삭제하지 말고 비교대상·시점 안내와 경험부재 처리를 먼저 검토.',
   'selection_fallback_authorization':'search 실패 후 최대 1000~2000행 정도의 소량 페이지에서 건설 관리직을 고르는 방식 허용',
   'blinding':'위 검토 초점이 사전에 주어졌으므로 블라인드·독립 인지면접이 아니다.'},
 'limitations':['합성 프로필 6개는 편의 선택한 시험 케이스이며 실제 사람·인구 대표 표본·독립 응답자·실증 증거가 아니다.',
   '하나의 생성 워커가 모든 해석을 작성하여 비슷한 표현과 동일한 판단 기준을 공유한다. 사람의 인지 과정이나 오해 빈도를 추정할 수 없다.',
   '현장 배치·소속·보직·예산 담당 여부·경험의 유무가 추가된 가상 조건이며 원본 사실이 아니다.',
   '원본은 많은 인물을 숙련되고 꼼꼼하다고 서술한다. 그 서술을 수행 수준·안전 성과·응답 신뢰성의 증거로 사용하지 않았다.',
   '프로필 거주지는 가상 현장 위치나 지역 표본성을 뜻하지 않는다. 제한된 첫 2000행의 선택이므로 직무·지역 다양성이 제한된다.',
   '이 점검은 제4장에서 계획한 실제 인지면접·전문가 검토·예비조사를 대신하지 않는다.',
   '문항별 ambiguous는 수정 확정이 아니라 실제 사람에게 확인할 후보이며 기존 안내로 해결되는 항목도 별도 표시했다.'],
 'user_correction':{'source':'코디네이터가 전달한 사용자 확정(msg_768e031498c4, msg_29b923ad6d34)',
    'actual_recruitment_plan':{'adopted_sites':30,'non_adopted_sites':30,'respondents_per_site':1,'total_respondents':60},
    'simulation_assignment':'6개 가상현장에 각 1명; 조건별 2현장',
    'earlier_assignment':'초기 3현장×2명 시험안은 폐기했으며 최종 산출물에는 적용하지 않음',
    'questionnaire_version_note':'읽은 원고는 정정 전 현장당 2명 설계와 A-3·A-4 구간형 문항이다. 이번 점검의 원문 대조 기준은 그 읽기 원본이며 원고를 수정하지 않았다.',
    'numeric_collection_allowed':'사용자가 실제 만 나이와 건설현장 근무연수의 숫자 수집이 가능하다고 확인했다.',
    'proposals_only':{'A-3':'응답일 기준 만 나이를 숫자로 수집하는 문항으로 변경 검토',
       'A-4':'실제 현장 근무기간을 숫자로 수집; 필요하면 년·개월을 받고 정한 규칙에 따라 연수로 환산'},
    'source_age_caution':'데이터셋 age의 만 나이 여부는 따로 확인하지 않았으므로 새 문항의 실제 만 나이 값으로 전용하지 않는다.',
    'analysis_direction_note':'코디네이터는 현장 임의절편 없는 두 집단 ANCOVA 방향을 검토한다고 전달했으나 이번 작업은 분석 설계를 변경하거나 실행하지 않는다.'},
 'review_only':True,'manuscript_modified':False,'score_distribution_or_inferential_statistics_created':False,
 'reproduction':'fetch_sources.py는 공개 API 소량 조회 스크립트이며 rows 페이지 조회 상한은 실행 인자로 관리한다. build_results.py는 저장된 판정 내용을 재직렬화할 뿐 새로운 독립 LLM 응답을 생성하지 않는다.'}

dump('personas.json',personas)
dump('responses.json',response_package)
columns=list(responses[0])
def cell(value):
    if value is None:
        return ''
    if isinstance(value,(list,dict,bool)):
        return json.dumps(value,ensure_ascii=False,separators=(',',':'))
    return str(value)
with (OUT/'responses.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=columns)
    writer.writeheader()
    writer.writerows({k:cell(r[k]) for k in columns} for r in responses)
dump('manifest.json',manifest)

def esc(value):
    return html.escape(str(value))

def para(label,body):
    return '<p><b>'+esc(label)+'</b> '+esc(body)+'</p>'

def render_report():
    chunks=['''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nemotron 프로필 6개를 이용한 설문 문항 점검</title><style>
    :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f4f6f7;color:#172b38;font:16px/1.7 system-ui,"Malgun Gothic",sans-serif}main{max-width:1120px;margin:28px auto;padding:36px;background:white;border:1px solid #dbe3e8;border-radius:10px}h1{font-size:28px;line-height:1.35;margin-top:0}h2{font-size:22px;border-top:2px solid #dbe3e8;padding-top:22px;margin-top:34px}h3{font-size:18px;margin-bottom:8px}p{margin:9px 0 14px}.notice{border-left:6px solid #a84024;background:#fff3eb;padding:18px 22px}.box{background:#eef5f8;padding:16px 20px}.meta{color:#546674;font-size:14px}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;margin:14px 0 22px;font-size:14px}th,td{padding:10px 12px;border:1px solid #dbe3e8;vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:#edf2f5}blockquote{border-left:3px solid #7694a6;margin:12px 0;padding:8px 16px;background:#f7f9fa}a{color:#155d91}code{font-size:13px;overflow-wrap:anywhere}.finding{margin:22px 0;padding:18px 22px;border:1px solid #dbe3e8;border-radius:8px}.tag{font-size:13px;background:#e9eff4;padding:3px 8px;border-radius:4px}details{margin:16px 0;border:1px solid #dbe3e8;padding:12px}summary{cursor:pointer;font-weight:600}.response-table{min-width:900px}.response-table td:first-child{width:48px}.response-table td:nth-child(2){width:30%}.response-table td:nth-child(3){width:20%}.response-table td:nth-child(4){width:28%}.small{font-size:13px}li{margin:7px 0}footer{margin-top:32px;color:#546674;font-size:14px}@media(max-width:700px){main{padding:20px;margin:0;border:0;border-radius:0}h1{font-size:23px}}@media print{body{background:white}main{margin:0;border:0;max-width:none}details{break-inside:avoid}.finding{break-inside:avoid}a{color:inherit}}
    </style></head><body><main><h1>설문 문항을 실제 조사 전에 점검한 기록</h1>
    <div class="notice"><strong>LLM 가상 문항 점검 · 실제 사람의 응답 아님</strong><p>NVIDIA의 Nemotron-Personas-Korea 합성 프로필을 읽고 이 Codex 워커가 해석과 가상 발화를 작성했다. NVIDIA 모델을 실행한 결과가 아니다. 6명은 편의 선택한 시험 케이스이며 인구 대표 표본, 독립 응답자, 실증 증거가 아니다.</p><p>생성 주체는 Codex이며, 코디네이터가 Orca 런타임에서 확인한 모델 ID는 gpt-6-astra다. 세부 빌드, temperature, seed는 공개되지 않아 임의 값을 기록하지 않았다.</p></div>''']
    chunks.append('<p class="meta">작성 '+esc(NOW)+' · 원문 문항 30개 · 적용항목 156개 · 원고 수정 없음</p>')
    chunks.append('<div class="box"><p>실제 면담에서 먼저 확인할 점은 <b>예산 정보에 접근할 수 있는지(C), 완화 인식의 비교 기준이 같은지(E), D-3의 여러 관찰을 하나의 평정으로 정할 수 있는지</b>다. 무알림 도입 현장 S3·S4의 경험 없는 D·E는 이미 있는 비해당 안내로 처리할 수 있다. B-3은 CCTV가 없어도 전화·보고 경험으로 읽을 수 있다.</p></div>')
    chunks.append('<p>이 문서는 점수를 만든 모의 설문조사가 아니다. 아래 발화는 사람이 실제로 말한 인용이 아니라 워커가 만든 점검 예시다. 문항의 검토 초점도 코디네이터에게 미리 받았으므로 블라인드 인지면접으로 볼 수 없다.</p>')
    chunks.append('<h2>사용자 정정과 점검 원문의 구분</h2><p>사용자는 실제 모집을 <b>도입 30현장·미도입 30현장, 현장당 1명, 총 60명</b>으로 확정했다. 이 가상 점검도 <b>6현장에 각 1명</b>을 배치했다. 읽은 원고에는 정정 전 현장당 2명 설계와 A-3·A-4 구간형 문항이 남아 있으나, 이번 작업은 그 원문을 대조 기준으로 삼고 원고를 수정하지 않았다.</p><p>사용자가 숫자 수집이 가능하다고 확인했으므로, 후속 수정에서는 <b>A-3을 응답일 기준 실제 만 나이</b>, <b>A-4를 실제 건설현장 근무연수</b>로 바꾸는 안을 검토한다. 필요하면 A-4는 년·개월을 받은 뒤 정한 규칙으로 연수로 환산할 수 있다. 새 문구는 아직 확정하지 않았으므로 아래 원문과 응답 기록을 대체하지 않았다. 데이터셋 age의 만 나이 여부도 별도 확인하지 않아 새 문항의 응답값으로 전용하지 않는다.</p>')
    chunks.append('<h2>어떤 자료와 조건을 사용했나</h2><p><a href="'+DATASET_URL+'">NVIDIA 공식 데이터셋</a>은 KOSIS 등 분포를 바탕으로 만든 100만 합성 인물 자료다. 검색·필터 API 실패 후 <a href="https://huggingface.co/docs/dataset-viewer/rows">행 조회 API</a>로 첫 2,000행만 확인했다. 현재 건설 관리·감리 업무가 명시된 경기 사례를 우선 선택하고 부족한 두 사례를 다른 지역에서 보완했다. 전체 데이터셋은 내려받지 않았다.</p>')
    chunks.append('<p class="small">조회한 원본 revision: <code>'+esc(revision)+'</code>. 선택한 행의 x-revision과 저장소 API sha가 같다. 약 '+f'{manifest["provenance"]["known_download_bytes"]/1_000_000:.2f}'+' MB의 성공 응답을 받았으며 오류와 URL·시각은 manifest.json에 기록했다.</p>')
    chunks.append('<div class="scroll"><table><thead><tr><th>시험 케이스</th><th>원본 직무·거주지</th><th>원본 행·추가 조건</th></tr></thead><tbody>')
    for p in people:
        src=p['source_fields']; s=p['scenario_assumptions']; pr=p['provenance']
        chunks.append('<tr><td>'+esc(p['persona_id']+' '+p['source_name'])+'<br>'+esc(str(src['age'])+'세 / '+src['sex'])+'</td><td>'+esc(src['occupation'])+'<br>'+esc(src['district'])+'</td><td>row '+str(p['source_row_index'])+' · '+esc(s['site_id'])+'<br>'+esc(s['role'])+'<br>'+esc('예산 직접 관리 조건' if s['budget_direct_manager'] else '예산 편성·집행액 모름 조건')+'</td></tr>')
    chunks.append('</tbody></table></div><p>이름·성별·나이·직무·거주지는 합성 원본에서 왔다. 소속·가상 보직·예산 지식범위와 아래 현장 배치는 추가 설정이다. 성별·나이로 기술 능력이나 수용성을 추정하지 않았으며, 원본의 숙련도 묘사로 현장 성과를 정하지 않았다.</p>')
    chunks.append('<table><tr><th>가상 현장·1명</th><th>조건</th><th>문항을 읽는 방식</th></tr>')
    site_reading={'S1':'구성·호환·알림 밀집·통신 불량·알림 대조 경험을 부여했으며 성능 결과는 미상이다.',
      'S2':'알림 수신·확인·현장 대조 경험만 부여했다. 다른 직접 경험은 비해당으로 처리한다.',
      'S3':'구성·호환 경험이 있어 D-1·2를 검토한다. 알림 등 경험 없는 전용부 문항은 비해당이다.',
      'S4':'구성·호환 경험도 없어 D·E를 현행 안내대로 비해당으로 처리한다.',
      'S5':'A·B·C만 읽는다. 전화·보고 이용 가능 조건이며 실제 속도·실효성은 미상이다.',
      'S6':'A·B·C만 읽는다. 전화·보고 이용 가능 조건이며 실제 속도·실효성은 미상이다.'}
    for st in sites:
        chunks.append('<tr><td>'+esc(st['site_id']+' / '+st['case_ids'][0])+'</td><td>'+esc(st['description'])+'</td><td>'+esc(site_reading[st['site_id']])+'</td></tr>')
    chunks.append('</table>')
    chunks.append('<p><b>정보 없음으로 유지한 항목:</b> 공사금액, 정확한 누적 경력, 예산액·지원 이력, 실제 현장 수행 수준·안전 성과·만족도, 과거 알림 비교 기준, 운용 기간과 실제 성능. 자료 접근 역할과 자료 자체의 제공은 다르다. 예산 담당자에게도 예산액이 주어지지 않았으면 값을 만들지 않았다.</p>')
    chunks.append('<p>원본을 고르면서 구직 중인 안전원·토목 기술자를 재직자로 바꾸지 않았다. 소장직을 장래 목표로 둔 작업자를 이미 소장인 것처럼 쓰지도 않았다. 가상 현장 위치는 미정이며 원본 거주지와 현장 위치를 동일시하지 않는다. 여섯 사례는 서로 다른 현장에 배치했지만 한 워커가 생성했으므로 독립 응답자라고 볼 수 없다.</p>')
    chunks.append('<h2>판정을 읽는 방법</h2><table><tr><th>상태</th><th>의미</th></tr>')
    for status,desc in response_package['status_definition'].items():
        chunks.append('<tr><td><code>'+esc(status)+'</code></td><td>'+esc(desc)+'</td></tr>')
    chunks.append('</table><p><b>needs_information은 결함 개수가 아니다.</b> 시나리오에 현장 경험·자료를 넣지 않은 경우는 scenario_information_gap으로 기록했다. 실제 역할의 정보 접근을 확인할 후보는 respondent_knowledge_scope, 문구 점검 후보는 item_wording으로 구분했다. 모든 평정 점수는 비워 두었으며, 숫자 선택은 원본으로 직접 확정되는 성별·연령과 한 사례의 소장 역할에만 사용했다.</p>')
    chunks.append('<h2>실제 사람에게 확인할 8가지</h2><p>아래는 수정 확정안이 아니라 면담과 전문가 검토에 가져갈 목록이다. 가상 발화를 실제 인지면접 인용으로 사용할 수 없다.</p>')
    for f in findings:
        chunks.append('<article class="finding"><span class="tag">'+esc(f['priority'])+'</span><h3>'+esc(f['id']+' · '+f['title'])+'</h3><p class="meta">'+esc(' · '.join(f['codes']))+' / '+esc(' · '.join(f['case_ids']))+'</p><blockquote>가상 발화: '+esc(f['virtual_utterance'])+'</blockquote>')
        for label,key in [('점검 결과','finding'),('기존 안내가 해결하는가','existing_guidance'),('실제 면담 질문','ask_human'),('최소 수정 제안','minimum_change')]:
            chunks.append(para(label,f[key]))
        chunks.append('</article>')
    chunks.append('<p><b>원문에 이미 남아 있는 확정 과제:</b> A-6 공사금액 구간 기준, 두 집단 공통 기준기간, 도입 현장 최소 운용 기간은 현재 설문에 확정 필요로 표시되어 있다. 이 시험이 새로 발견한 결함처럼 세지 않았다. 배포 전 기존 과제로 처리해야 한다.</p>')
    chunks.append('<h2>원본과 156개 적용항목 기록</h2><p>각 케이스를 펼치면 원본 직무 서술과 모든 적용 문항의 문구·해석·판정 근거·필요정보를 볼 수 있다. 공통 18문항×6=108개와 전용 12문항×4=48개다. 미도입 두 사례의 D·E 24개는 양식에 없으므로 이 수에 포함하지 않았다.</p>')
    for p in people:
        s=p['scenario_assumptions']; src=p['source_fields']; pr=p['provenance']
        chunks.append('<details><summary>'+esc(p['persona_id']+' '+p['source_name']+' · '+s['site_id']+' · '+s['role'])+'</summary>')
        chunks.append('<p class="small">UUID <code>'+esc(p['uuid'])+'</code> / row '+str(p['source_row_index'])+' / 조회 '+esc(pr['retrieved_at_utc'])+'</p>')
        chunks.append(para('원본 직무 서술',src['professional_persona']))
        chunks.append(para('선택 이유',p['selection_reason']))
        chunks.append(para('추가 지식범위',s['budget_knowledge_scope']))
        chunks.append('<p><a href="'+esc(pr['source_request_url'])+'">추출에 사용한 API URL</a> · <a href="'+esc(pr['single_row_locator_url'])+'">단일 행 재조회 위치</a></p>')
        chunks.append('<div class="scroll"><table class="response-table"><tr><th>코드</th><th>현행 원문</th><th>해석·가상 발화</th><th>상태·이유</th><th>필요정보·모호표현·처리</th></tr>')
        for r in responses:
            if r['persona_id']!=p['persona_id']: continue
            extra='필요정보: '+(' / '.join(r['information_needed']) or '없음')+'\n모호표현: '+(' / '.join(r['ambiguous_expression']) or '별도 지적 없음')
            if r['non_applicable_handling']: extra+='\n'+r['non_applicable_handling']
            if r['numeric_selection'] is not None: extra+='\n원본 근거 선택: '+str(r['numeric_selection'])+' ('+r['numeric_selection_basis']+')'
            chunks.append('<tr data-response="'+esc(r['persona_id']+':'+r['code'])+'"><td>'+esc(r['code'])+'</td><td>'+esc(r['question_text'])+'</td><td>'+esc(r['interpretation'])+'<br><br>가상 발화: '+esc(r['virtual_utterance'])+'</td><td><code>'+esc(r['status'])+'</code><br><span class="small">'+esc(r['evidence_type'])+'</span><br>'+esc(r['reason'])+'</td><td>'+esc(extra).replace('\n','<br>')+'</td></tr>')
        chunks.append('</table></div></details>')
    chunks.append('<h2>파일과 확인 범위</h2><ul><li><a href="personas.json">personas.json</a>: 원본 관련 필드·UUID·행 위치·API URL·조회 시각·revision·선택 이유·가상 조건</li><li><a href="responses.json">responses.json</a>: 원문·안내·156개 판정·8개 발견</li><li><a href="responses.csv">responses.csv</a>: JSON과 같은 156개 적용항목, Excel용 UTF-8 BOM</li><li><a href="manifest.json">manifest.json</a>: 생성 주체·지시된 검토 초점·API 오류·한계·검증 결과</li></ul>')
    chunks.append('<p id="validation">검증 기록: manifest.json의 validation을 확인한다. 검증은 원본 필드 대조, 6현장 각 1명·도입4/미도입2 구성, 적용항목 156개, 문항 원문 및 제4장 B·C·D·E 일치, 상태·근거 구분, JSON/CSV 전 필드 일치를 한 번 확인한다.</p>')
    chunks.append('<p>실제 응답자의 이해도, 오해 빈도, 응답 시간, 척도의 신뢰도·검정력·집단 효과는 이 자료로 확인하지 않았다. 제4장에 예정된 실제 인지면접·전문가 검토·예비조사를 진행할 때 위 질문을 확인하고 수정 여부를 결정해야 한다.</p>')
    chunks.append('<footer><p>출처: NVIDIA, <a href="'+DATASET_URL+'">Nemotron-Personas-Korea</a>, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. 관련 원본 필드를 발췌했고 가상 현장 조건과 Codex의 해석·발화를 추가했다. NVIDIA가 이 점검을 수행하거나 결과를 보증했다는 뜻이 아니다.</p></footer></main></body></html>')
    return ''.join(chunks)

(OUT/'report.html').write_text(render_report(),encoding='utf-8')
print(json.dumps({'created':NOW,'personas':len(people),'responses':len(responses),'findings':len(findings),
    'source_revision':revision,'output':'03.plan/261003_1227_Nemotron_설문문항점검'},ensure_ascii=False))
