import json,pathlib,difflib,html,re
P=pathlib.Path(__file__).parent
read=lambda f:json.loads((P/f).read_text(encoding='utf-8'))
B=read('base_paras.json');R=read('A_diff.json');O=read('old_blocks.json');N=read('new_blocks.json')
base={b['idx']:b for b in B if b['section']=='Contents/section2.xml'}
S={k:[] for k in ['replace','insert_after','delete','user_edits','unresolved','coverage']}
for r in R:
 cov={'file':r['file'],'old_blocks':r['old_range'],'new_blocks':r['new_range'],'mapped':[]}
 old=r['old'];new=r['new']
 if not old and not new:
  cov['status']='out_of_scope_table_or_diagram';S['coverage'].append(cov);continue
 pairs=list(zip(old,new))
 for x,y in pairs:
  if x['type']=='table_caption':
   idx=606 if x['block']==71 else 655
   cov['mapped'].append({'old_block':x['block'],'new_block':y['block'],'section':'Contents/section2.xml','idx':idx,'status':'table_cell_caption_owned_by_table_worker','old':base[idx]['text'],'new':y['text']})
   continue
  idx=x['hits'][0] if x['hits'] else x['near'][0][1]
  b=base[idx]
  if idx==409:
   S['user_edits'].append({'file':r['file'],'section':b['section'],'idx':idx,'old_md':x['text'],'actual':b['text'],'requested_new':y['text'],'reason':'기존 HWPX는 MD 각주 참조를 Bosch 설명 본문 괄호로 확장하여 수록함; 내용차이 보존 원칙으로 문단 전체 치환 제외. 기존 UNVERIFIED 메모도 현재 문단과 함께 보존.'})
   cov['mapped'].append({'old_block':x['block'],'new_block':y['block'],'idx':idx,'status':'preserved_user_edit'});continue
  assert b['table_idx'] is None
  assert b['text'].strip().replace('`','')==x['text'],(idx,x['text'])
  prefix=b['text'][:len(b['text'])-len(b['text'].lstrip())]
  suffix=b['text'][len(b['text'].rstrip()):]
  newtext=prefix+y['text']+suffix
  if b['text']!=newtext:S['replace'].append({'section':b['section'],'idx':idx,'old':b['text'],'new':newtext})
  cov['mapped'].append({'old_block':x['block'],'new_block':y['block'],'idx':idx,'status':'replace'})
 if len(new)>len(old):
  anchor=old[-1]['hits'][0];b=base[anchor]
  texts=[y['text'] for y in new[len(old):]]
  S['insert_after'].append({'section':b['section'],'idx':anchor,'template_idx':anchor,'texts':texts})
  cov['mapped'].extend({'new_block':y['block'],'idx':anchor,'status':'insert_after'} for y in new[len(old):])
 assert len(old)<=len(new)
 cov['status']='accounted';S['coverage'].append(cov)
# Evidence: source indices are section-local document order, including cells.
keys=[(x['section'],x['idx']) for x in S['replace']+S['delete']]
assert len(keys)==len(set(keys))
for x in S['replace']+S['delete']:
 assert base[x['idx']]['text']==x['old'] and base[x['idx']]['table_idx'] is None
 assert x['old'].strip()
for x in S['insert_after']:
 assert base[x['idx']]['table_idx'] is None and base[x['template_idx']]['table_idx'] is None
 assert all(t.strip() and not t.startswith(('![','>','[작성','[메모')) for t in x['texts'])
 assert (x['section'],x['idx']) not in {(d['section'],d['idx']) for d in S['delete']}
assert len({(x['section'],x['idx']) for x in S['insert_after']})==len(S['insert_after'])
# Insertion anchors may also be replaced: apply insertions against original indices, as standard schema requires.
(P/'prose_A.json').write_text(json.dumps(S,ensure_ascii=False,indent=2),encoding='utf-8')
counts={k:len(v) for k,v in S.items()}
report='''# 본문 A 대조 보고

대상: 01_서론.md, 02_이론적배경.md, 03_시스템개발.md. CLAUDE.md와 교수님 논문작성요령 전문을 읽었으며 승인된 분석설계는 재검토하지 않았다. 원본 HWPX를 열지 않고 제공 덤프와 old/new 블록을 대조했다.

## 결과

'''+json.dumps(counts,ensure_ascii=False)+'''

삽입은 559 뒤 2문단, 688 뒤 1문단, 692 뒤 1문단으로 총 4문단이다. 각 원문단을 스타일 템플릿으로 지정했다. 같은 앵커의 본문 치환과 insert_after는 의도된 순차 동작이며, 인덱스를 원본 덤프 기준으로 고정해서 적용해야 한다. 삭제 문단은 없으므로 레이아웃 빈 문단과 사용자 추가 빈줄은 모두 보존된다.

## 보존·담당 경계

- section2 idx 409: 기존 HWPX에 Bosch 각주 설명이 본문 괄호로 수록되어 있다. MD와 다른 실제 내용을 덮어쓰지 않도록 전체 치환을 제외했고 user_edits에 actual·old_md·requested_new를 기록했다. 기존 UNVERIFIED 메모도 보존된다. 메인 담당이 설명을 보존하는 부분 수정 여부를 결정해야 한다.
- section2 idx 501: HWPX의 코드 백틱 이외 내용이 기존 MD와 같아 현재 MD의 인라인 마커 없는 새 본문으로 치환한다.
- 변경 캡션 2건은 실제로 표 셀이다: section2 idx 606(table_idx 11), 655(table_idx 12). 본 명세는 이 셀을 수정하지 않으며 coverage에 실제 old와 요청 new를 전달했다. 특히 606은 기존 HWPX에서 표본·시간·카메라 부제를 본문 캡션에서 분리한 형식이므로 표 담당이 현재 배치를 보존해야 한다.
- 표·도식 변경은 coverage의 out_of_scope 항목으로 구분했다. TOC를 치환하지 않는다. old/new의 h1~h4 제목 변경은 없으며, 도식·표 셀 제목은 담당 범위에서 제외한다.
- 새 내부관리 메모나 작성가이드 단독 문단은 삽입하지 않았다. 최신 MD의 본문 내부 확정 필요 표시는 그대로 유지한다. 03장 변경 대상 밖 표 전후 주석과 빈 문단은 건드리지 않는다.

## 검증 증거

A_build.py 실행에서 치환 73개와 삽입 앵커 3개의 원본 위치 및 실제 old 일치를 assert 검증했다. 모든 치환은 section2 본문(table_idx=null)이며, 409 이외 본문은 기존 MD와 유일하게 일치한다(선행 공백과 501의 백틱 제외). 선행·후행 공백은 실제 HWPX에서 보존했다. 치환/삭제 키 중복 0, 삽입 앵커 중복 0, 삭제와 삽입 충돌 0이며 빈 문단 삭제 0이다. 모든 old/new 변경 구간을 coverage에 수록했다. 동일 원문단 치환 및 뒤 삽입 3건은 문단 분할을 위한 명시적 결합 작업으로서 서로 다른 텍스트 범위를 다룬다.
'''
report=report.replace('치환 73개',f"치환 {len(S['replace'])}개")
(P/'report_A.md').write_text(report,encoding='utf-8')
print(json.dumps(counts));print('VALIDATION PASS; inserted paragraphs',sum(len(x['texts']) for x in S['insert_after']))
