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
