import json,pathlib,html,re,collections
P=pathlib.Path(__file__).parent;R=json.loads((P/'B_draft.json').read_text('utf-8'));B=json.loads((P/'base_paras.json').read_text('utf-8'));N=json.loads((P/'new_blocks.json').read_text('utf-8')); lookup={(p['section'],p['idx']):p for p in B}
def tx(b):return html.unescape(b.get('text',''.join(r['text'] for r in b.get('runs',[])))).replace('**','').replace('`','')
R['user_edits']=[{'section':'Contents/section2.xml','idx':2284,'old':'도입 현장 전용부','md':'도입 현장 전용부 — 도입 현장용 양식에만 싣는다','action':'preserve','reason':'HWPX의 배포용 제목 축약을 보존하며 MD 양식 관리 지시를 새 삽입하지 않음'}]
# Table builders must interleave newly split tables using exact new-block order, since raw paragraph op order cannot express a future table anchor.
for f in ['04_연구설계.md','05_실증분석결과.md']:
 seq=[]
 for bi,b in enumerate(N[f]):
  t=tx(b)
  if b['type']=='table':seq.append({'new_block':bi,'type':'table','owner':'C'});continue
  refs=[]
  for r in R['replace']:
   if r['new']==t:refs.append({'kind':'replace','section':r['section'],'idx':r['idx']})
  for r in R['insert_after']:
   for offset,s in enumerate(r['texts']):
    if s==t:refs.append({'kind':'insert_after','section':r['section'],'idx':r['idx'],'text_offset':offset})
  if not refs:
   for p in B:
    if p['table_idx'] is None and p['text'].strip()==t:refs.append({'kind':'existing','section':p['section'],'idx':p['idx']})
  seq.append({'new_block':bi,'type':b['type'],'text':t,'locations':refs})
 R['coverage'].append({'file':f,'status':'assembly_order','instruction':'표를 새로 분할·삽입할 때 이 순서로 본문과 표를 교차 배치. replace/insert_after는 본문 객체의 원본 앵커이며 신규 표의 최종 앞뒤 위치는 이 순서가 기준.','sequence':seq})
keys=[]
for op in ['replace','delete']:
 for r in R[op]:
  k=(r['section'],r['idx']);p=lookup[k];assert p['table_idx'] is None;assert p['text']==r['old'];assert r['old'].strip();keys.append(k)
assert len(keys)==len(set(keys))
for r in R['insert_after']:
 assert lookup[(r['section'],r['idx'])]['table_idx'] is None
 assert lookup[(r['section'],r['template_idx'])]['table_idx'] is None
 assert (r['section'],r['idx']) not in [(d['section'],d['idx']) for d in R['delete']]
 assert r['texts'] and all(t.strip() for t in r['texts'])
alltext=[r['new'] for r in R['replace']]+[t for r in R['insert_after'] for t in r['texts']]
assert not any(any(x in t for x in ['[작성 가이드','[내부 관리용','[집필 메모','**','`']) for t in alltext)
# Every changed block marked mapped has a represented new string (two shared survey additions intentionally duplicated).
for c in R['coverage']:
 if c['status'] in ['mapped','mapped_structural']:
  for bi in c['new_blocks']:assert tx(N[c['file']][bi]) in alltext,(c['file'],bi)
R['coverage'].append({'status':'verification','old_exact':len(keys),'unique_mutation_targets':len(set(keys)),'insert_groups':len(R['insert_after']),'insert_texts':sum(len(x['texts']) for x in R['insert_after']),'table_cell_mutations':0,'blank_deletions':0,'unresolved':len(R['unresolved']),'overlap_note':'insert_after may share replace anchor by design; no delete anchor overlap','excluded':'MD blockquotes, internal administration, history, appendix2 excluded by provided block dumps and final marker check'})
(P/'prose_B.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),'utf-8')
report='''# B 본문 이관 명세 검토 결과

- 범위: 04 연구설계, 05 실증분석결과, 06 결론, 부록1 설문양식의 표 밖 본문·제목·캡션. HWPX·원고·원자료·Git은 수정하지 않았다.
- CLAUDE.md 및 교수님 작성요령 전문을 읽고 승인된 최신 MD와 제공 old/new 블록, 실제 문단 덤프를 대조했다. 분석설계 재검토·외부검색은 수행하지 않았다.
- 106 치환, 14 삽입군(문단 수는 JSON verification 참조), 1 삭제. 삭제는 구 ANCOVA 회귀기울기 가정 문단 idx1610이며 빈 문단 삭제는 없다.
- 모든 변경 대상 old 문자열은 section+표셀 포함 idx에서 실제 덤프와 정확히 일치한다. 치환/삭제 107개 대상은 유일하며 표 셀 쓰기 0, 삭제 앵커와 삽입 오버랩 0, unresolved 0이다.
- 04 분석절은 구 13문단→신 17문단으로 매핑하며 H1/H2 공식과 마지막 장 연결문장을 포함한다. 연구모형 이미지와 교환되는 new block11 주 설명은 메인 그림 담당이다.
- 부록 공통 안내 2문단은 도입 idx2111 및 미도입 idx2457 뒤에 각각 삽입한다. D/E 안내 idx2286/2376을 바꾸며 24개 설문 문항 원문 셀은 건드리지 않는다.
- 실제 HWPX의 축약 제목 idx2284 ‘도입 현장 전용부’를 보존하여 user_edits에 기록했다. 04~06 표 밖 본문에는 공백 외 구 MD 내용 불일치가 없었다.
- C 인계: 안내문 셀 idx2101/2102/2105/2448/2451, 표 안 캡션 idx1537/1612/1811. 인계는 코디네이터에게 전달했고 확인을 받았다.

## 최종 조립 시 필수 배치

prose_B.json coverage의 assembly_order는 최신 new_blocks 인덱스별 본문 위치와 표(C 소유)를 함께 기록한다. 표5-2/5-3/5-6/5-7/5-8은 패널 분할로 표의 수·위치가 바뀌므로 단순히 기존 표 자리에 표를 모두 넣고 B 치환만 실행하면 설명이 잘못된 표 뒤에 남을 수 있다. C 표 삽입과 B 본문을 assembly_order 순서로 교차 배치해야 한다. 새 본문 객체는 locations의 replace idx 또는 insert_after idx+text_offset으로 식별할 수 있다. B는 모든 패널 A/B/C 설명과 주석을 제공하며 C는 표만 생성한다.

MD 인용블록 작성가이드, 내부관리부, 작업이력, 부록2는 신규 삽입에 포함하지 않았다. HWPX 실제 수정·조판·한글 개방 검증은 메인 담당 후속 작업이다.
'''
(P/'report_B.md').write_text(report,'utf-8')
print(R['coverage'][-1])
