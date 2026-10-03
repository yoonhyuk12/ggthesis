"""One acceptance pass over saved artifacts and read-only source evidence."""
from collections import Counter
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

OUT=Path(__file__).resolve().parent
REPO=OUT.parent.parent
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def flatten(v):
    if v is None: return ''
    if isinstance(v,(list,dict,bool)): return json.dumps(v,ensure_ascii=False,separators=(',',':'))
    return str(v)

checks=[]
def check(name,condition):
    if not condition: raise AssertionError(name)
    checks.append({'check':name,'passed':True})

p=read('personas.json'); package=read('responses.json'); rows=package['responses']; manifest=read('manifest.json')
people=p['personas']; sites=p['sites']; byid={x['persona_id']:x for x in people}
check('Six distinct source UUIDs',len(people)==6 and len({x['uuid'] for x in people})==6)
check('Six sites with exactly one case each',len(sites)==6 and {s['site_id'] for s in sites}=={f'S{i}' for i in range(1,7)} and all(len(s['case_ids'])==1 for s in sites))
check('Each case assigned to a unique site',Counter(x['scenario_assumptions']['site_id'] for x in people)==Counter({f'S{i}':1 for i in range(1,7)}))
check('Four adopted sites and two non-adopted sites',Counter(s['installation_group'] for s in sites)=={'도입':4,'미도입':2})
check('Two sites per test condition',Counter(s['test_condition'] for s in sites)=={'adopted_alerts':2,'adopted_no_alerts':2,'not_adopted_no_cctv':2})
for x in people:
    provenance=x['provenance']; source=read(provenance['raw_response_file'])
    rr=next(r for r in source['data']['rows'] if r['row_idx']==x['source_row_index'])
    check(x['persona_id']+' original fields copied exactly',all(v==rr['row'][k] for k,v in x['source_fields'].items()) and x['uuid']==rr['row']['uuid'])
    check(x['persona_id']+' provenance complete',source['url']==provenance['source_request_url'] and source['completed_at_utc']==provenance['retrieved_at_utc'] and source['sha256']==provenance['response_body_sha256'] and provenance['truncated_cells']==[])
    check(x['persona_id']+' dataset revision verified',provenance['viewer_dataset_revision']==manifest['provenance']['dataset_revision']==source['headers']['x-revision'])
    check(x['persona_id']+' name from original text',rr['row']['professional_persona'].startswith(x['source_name']+' 씨는'))

qpath=REPO/'01.docs/부록1_설문지_양식.md'
qtext=qpath.read_text(encoding='utf-8')
qitems={}
for n,line in enumerate(qtext.splitlines(),1):
    match=re.match(r'^\*\*(A-\d)\)\*\* (.+)$',line) or re.match(r'^\| ([B-E]-\d) \| (.+?) \|',line)
    if match: qitems[match[1]]=(match[2],n)
expected_codes={f'{block}-{n}' for block,total in [('A',6),('B',8),('C',4),('D',8),('E',4)] for n in range(1,total+1)}
check('Thirty source items recovered',set(qitems)==expected_codes)
check('Question bank exactly matches source',len(package['questions'])==30 and all((x['question_text'],x['source_line'])==qitems[x['code']] for x in package['questions']))
design=(REPO/'01.docs/04_연구설계.md').read_text(encoding='utf-8')
design_items=dict(re.findall(r'^\| ([B-E]-\d) \| (.+?) \|',design,re.M))
check('All 24 B/C/D/E items match chapter 4',all(design_items[c]==qitems[c][0] for c in expected_codes if c[0] in 'BCDE'))
expected_pairs={(x['persona_id'],c) for x in people for c in expected_codes if x['persona_id'] not in ('P5','P6') or c[0] in 'ABC'}
check('156 unique applicable items',len(rows)==156 and {(x['persona_id'],x['code']) for x in rows}==expected_pairs)
check('108 common and 48 dedicated items',Counter('common' if x['code'][0] in 'ABC' else 'dedicated' for x in rows)=={'common':108,'dedicated':48})
check('30 items each for P1-P4 and 18 each for P5-P6',Counter(x['persona_id'] for x in rows)=={'P1':30,'P2':30,'P3':30,'P4':30,'P5':18,'P6':18})
check('Every response uses exact source text and line',all((x['question_text'],x['question_source_line'])==qitems[x['code']] for x in rows))
check('Every response site and UUID match its persona',all(x['site_id']==byid[x['persona_id']]['scenario_assumptions']['site_id'] and x['uuid']==byid[x['persona_id']]['uuid'] for x in rows))
check('Every status is allowed and has an interpretation/reason',all(x['status'] in {'answerable','needs_information','ambiguous','not_applicable'} and x['interpretation'] and x['reason'] and x['evidence_type'] and x['evidence_refs'] and x['virtual_utterance'] for x in rows))
check('Scenario gaps are not treated as wording defects',all(x['scenario_information_gap'] and not x['wording_issue_candidate'] and not x['respondent_access_risk'] and x['status']=='needs_information' and x['information_needed'] for x in rows if x['evidence_type']=='scenario_information_gap'))
check('Budget knowledge gaps kept separate',all(not x['scenario_information_gap'] and x['respondent_access_risk'] and not x['wording_issue_candidate'] and x['persona_id'] in ('P2','P4','P6') and x['code'] in ('C-2','C-4') for x in rows if x['evidence_type']=='respondent_knowledge_scope'))
check('No B/C/D/E numeric ratings generated',all(x['numeric_selection'] is None for x in rows if x['code'][0] in 'BCDE'))
numeric=[x for x in rows if x['numeric_selection'] is not None]
check('Only 13 directly source-grounded A selections',len(numeric)==13 and all(x['evidence_type']=='source_fact' and x['numeric_selection_basis'].startswith('source_fields.') and (x['code'] in ('A-2','A-3') or (x['persona_id']=='P5' and x['code']=='A-5')) for x in numeric))
check('No invented career or site-amount selections',all(x['numeric_selection'] is None and x['status']=='needs_information' for x in rows if x['code'] in ('A-4','A-6')))
lookup={(x['persona_id'],x['code']):x for x in rows}
required={'D-1':'equipment_configuration','D-2':'different_manufacturer_camera_integration','D-3':'dense_alerts','D-4':'poor_network','D-5':'alert_content_compared_with_site','D-6':'alert_content_compared_with_site','D-7':'actual_alert_received_and_read','D-8':'actual_alert_received_and_read'}
check('Experience absent D/E items follow existing non-applicable rule',all((x['status']=='not_applicable') == (not byid[x['persona_id']]['scenario_assumptions']['experience'][required.get(x['code'],'actual_alert_received_and_read')]) for x in rows if x['code'][0] in 'DE'))
check('No-alert adopted cases retained and item-level exceptions respected',lookup['P3','D-1']['status']!='not_applicable' and lookup['P3','D-2']['status']!='not_applicable' and all(lookup[pid,code]['status']=='not_applicable' for pid in ('P3','P4') for code in expected_codes if code[0]=='E'))
check('No-CCTV B3 not marked non-applicable',all(lookup[pid,'B-3']['status']=='needs_information' and '전화' in lookup[pid,'B-3']['virtual_utterance'] for pid in ('P5','P6')))
check('Eight findings with required review fields',len(package['findings'])==8 and all(all(x[k] for k in ['priority','codes','virtual_utterance','existing_guidance','ask_human','minimum_change']) and set(x['codes'])<=expected_codes for x in package['findings']))
check('All input files unchanged from recorded hashes',all(digest(REPO/x['path'])==x['sha256'] for x in manifest['inputs']))
csvpath=OUT/'responses.csv'
check('CSV is UTF-8 BOM',csvpath.read_bytes().startswith(b'\xef\xbb\xbf'))
with csvpath.open(encoding='utf-8-sig',newline='') as stream: csvrows=list(csv.DictReader(stream))
check('JSON and CSV identical for every cell',csvrows==[{k:flatten(v) for k,v in r.items()} for r in rows])

class PageAudit(HTMLParser):
    def __init__(self): super().__init__(); self.ids=[]; self.resources=[]; self.text=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'data-response' in attrs:self.ids.append(attrs['data-response'])
        if tag in ('img','script','iframe','link','audio','video','source'):self.resources.append((tag,attrs))
    def handle_data(self,data):self.text.append(data)
report=(OUT/'report.html').read_text(encoding='utf-8'); page=PageAudit(); page.feed(report)
check('HTML includes all 156 response rows',len(page.ids)==156 and set(page.ids)=={a+':'+b for a,b in expected_pairs})
check('HTML uses no external resources',not page.resources and 'url(' not in report)
check('HTML contains required LLM and source disclosures',all(word in report for word in ['실제 사람의 응답 아님','NVIDIA 모델을 실행한 결과가 아니다','gpt-6-astra','독립 응답자','CC BY 4.0','6현장에 각 1명']))
check('Confirmed recruitment and numeric-collection proposals recorded separately',manifest['user_correction']['actual_recruitment_plan']=={'adopted_sites':30,'non_adopted_sites':30,'respondents_per_site':1,'total_respondents':60} and set(manifest['user_correction']['proposals_only'])=={'A-3','A-4'} and manifest['manuscript_modified'] is False)
check('No unintended invisible Unicode in generated report',not any(c in report for c in '\u200b\u200c\u200d\u2060\ufeff'))

evidence={'status':'passed','executed_at_kst':dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec='seconds'),
 'command':'python 03.plan/261003_1227_Nemotron_설문문항점검/validate_results.py',
 'acceptance_pass_count':1,'checks_passed':len(checks),'checks':checks,
 'coverage':{'profiles':6,'sites':6,'cases_per_site':1,'adopted_cases':4,'non_adopted_cases':2,'common_items':108,'dedicated_items':48,'total_applicable_items':156},
 'json_csv_identical':True,'utf8_bom':True,'questionnaire_and_design_match':True,
 'limits':'구조·출처·문항·파일 정합 검증이며 실제 사람의 응답 타당성을 검증한 것은 아니다. 브라우저 화면 렌더링은 별도로 실행하지 않았다.'}
(OUT/'validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=re.sub(r'<p id="validation">.*?</p>',
    '<p id="validation"><b>검증 통과:</b> '+str(len(checks))+'개 확인 항목을 1회 검증했다. 원본 프로필 6개 출처, 6현장 각 1명, 도입4·미도입2, 공통108·전용48의 총156개 적용항목, 원문·제4장 대조, 상태·근거 구분, JSON/CSV 전 필드 일치, UTF-8 BOM을 확인했다. 상세 증거는 <a href="validation.json">validation.json</a>과 manifest.json에 있다.</p>',report,flags=re.S)
(OUT/'report.html').write_text(report,encoding='utf-8')
manifest['validation']=evidence
manifest['prose_audit']={'tool':'clean-user-facing-text/inspect_text.py --audit','density_tier':'low','flagged_count':0,
 'rewrite_performed':False,'note':'탐지 회피나 인간 저작 판정이 아니다. 원문 인용을 보존하고 설명문을 검토했다.'}
manifest['artifacts']=[{'path':x,'sha256':digest(OUT/x),'bytes':(OUT/x).stat().st_size} for x in
 ['report.html','personas.json','responses.json','responses.csv','validation.json','fetch_sources.py','build_results.py','validate_results.py']]
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'validation':evidence['status'],'checks_passed':len(checks),'coverage':evidence['coverage'],'json_csv_identical':True,'utf8_bom':True},ensure_ascii=False,indent=2))
