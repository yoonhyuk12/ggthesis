"""Reproducible scratch assembly; run from repository root, no Hancom COM."""
import argparse
import contextlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TOOL = ROOT / 'tools/hwpx_transfer'
sys.path.insert(0, str(TOOL))
import blocks_to_hwpx as b
import kjn_profile as k

def rel(p):
    return p.relative_to(ROOT).as_posix()

refs = json.loads((TOOL/'staging/migrate_kjn/references_kjn_v3.json').read_text(encoding='utf-8'))
raw = k.read_package(OUT/'base.hwpx')[1]
# v3 is an October 8 snapshot: retain the latest base bibliography (including
# jamovi additions) rather than reverting it to that obsolete snapshot.
base_s2 = raw['Contents/section2.xml'].decode()
ref_categories = {}
category = None
in_refs = False
for a,z in k.split_paragraphs(base_s2):
    text = re.sub(r'\s+', ' ', k.plain_texts(base_s2[a:z])).strip()
    if text == '참고문헌':
        in_refs=True
        continue
    if not in_refs:continue
    if re.sub(r'\s','',text).startswith('부록('):break
    if re.match(r'^[가-사]\. ',text):
        category=text
        ref_categories[category]=[]
    elif text and category:
        content=re.sub(r'^\[\d+\]\s*','',text)
        ref_categories[category].append({'text':content})
assert len(ref_categories)==7
refs={'categories':ref_categories,'flagged':[]}
source = (ROOT/'01.docs/07_참조번호목록.md').read_text(encoding='utf-8')
law = next(x.split(' — ')[0] for x in source.splitlines() if x.startswith('「산업안전보건법 시행령」 제16조'))
refs['categories']['라. 관련법'].append({'no':len(refs['categories']['라. 관련법'])+1, 'text':law})
(OUT/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
s2 = raw['Contents/section2.xml'].decode()
ps = k.split_paragraphs(s2)
start = next(i for i,(a,z) in enumerate(ps) if re.sub(r'\s','',k.plain_texts(s2[a:z])).startswith('부록(도입현장)'))
transplant = {
    '감사의글': {'source_hwpx':rel(OUT/'base.hwpx'),'section':1,'range':[138,162], 'append_red_note':''},
    '부록1_설문지': {'source_hwpx':rel(OUT/'base.hwpx'),'section':2,'range':[start,len(ps)-1],
                   'replace_appendix':'부 록 — 설문지','keep_until':'부 록 — 설문지','drop_heading':True}
}
# Existing survey stays the authoritative layout; actual target strings were
# read from base_paragraphs.json before applying these MD-confirmed changes.
for name,item in transplant.items():
    if name.startswith('부록'):
        survey = ''.join(s2[a:z] for a,z in ps[start:])
        replacements=[]
        for old,new in [('중소규모 건설현장을 위한 YOLO-LLM','건설현장 YOLO-LLM'),
                        ('현장소장','현장소장(관리감독자)'),
                        ('도입·미도입 두 집단 모두','도입·미도입 현장 모두'),
                        ('CCTV YOLO-LLM 안전알림 시스템','YOLO-LLM 안전관제 시스템'),
                        ('CCTV YOLO-LLM 안전알림','YOLO-LLM 안전관제 시스템'),
                        ('분석용 집단은','분석용 현장 도입 여부는'),
                        ('해당 집단의 적용 문항','해당 현장의 적용 문항')]:
            count=survey.count(old)
            if count:
                replacements.append({'old':old,'new':new,'count':count})
                survey=survey.replace(old,new)
        item['text_replacements']=replacements
(OUT/'transplant.json').write_text(json.dumps(transplant,ensure_ascii=False,indent=2),encoding='utf-8')
front=(ROOT/'01.docs/00_목차.md').read_text(encoding='utf-8')
cover=front.split('```',2)[1]
main=[]
for line in cover.splitlines():
    line=line.strip()
    if line.startswith(':'):break
    if main or 'YOLO-LLM' in line:
        if line:main.append(line)
k.COVER_TEXT['title']=' '.join(main)
images=json.loads((TOOL/'staging/migrate_kjn/images.json').read_text(encoding='utf-8'))
for name in ['ch01','ch02','ch03','ch04','ch05']:
    blocks=json.loads((OUT/(name+'.blocks.json')).read_text(encoding='utf-8'))['blocks']
    for figure in k.group_figures(blocks):
        if figure.get('type')=='_figure' and figure.get('image_md') and figure.get('caption'):
            for entry in images['mapping']:
                if figure['caption'].startswith(entry['caption_prefix']):
                    entry['source']='01.docs/'+figure['image_md'][1]
(OUT/'images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2),encoding='utf-8')
args=argparse.Namespace(template=rel(OUT/'template.hwpx'),profile=rel(TOOL/'staging/migrate_kjn/style_map_kjn.json'),
    blocks=[rel(OUT/(n+'.blocks.json')) for n in ['ch01','ch02','ch03','ch04','ch05','apx1','apx2r','apx3']],
    references=rel(OUT/'references.json'),images=rel(OUT/'images.json'),
    transplant=rel(OUT/'transplant.json'),toc_pages=None,front_md=rel(ROOT/'01.docs/00_목차.md'),
    output=rel(OUT/'assembled.hwpx'),report=rel(OUT/'report.md'),no_tail=True,smoke=False)
profile=k.load_profile(json.loads((ROOT/args.profile).read_text(encoding='utf-8')),args.profile)
doc,tpl,sections,_=b.assemble_kjn(args,profile,str(TOOL))
entries=k.plan_package(tpl,sections,tpl.header.xml,doc.bin_items)
b.write_package(args.output,entries,(2026,10,31,0,0,0))
(OUT/'image_grid_plan.json').write_text(json.dumps(doc.image_grid_evidence,ensure_ascii=False,indent=2),encoding='utf-8')
report=['# 조립 보고','',f'- 본문 최상위 문단: {len(doc.body)}',f'- 그림: {len(doc.bin_items)}',
        f'- 목차: {len(doc.toc)}, 표 목차: {len(doc.lot)}, 그림 목차: {len(doc.lof)}',
        '- 목차 인쇄 쪽수: 임시값 0, 메인 재조판 후 갱신 필요','', '## 메모','']
report += ['- '+x for x in doc.notes]
report += ['', '## 표별 열폭',''] + [f'- {cap}: {w}' for cap,w in doc.table_widths]
(OUT/'report.md').write_text('\n'.join(report),encoding='utf-8')
print('\n'.join(report[:8]));print('assembly written')
