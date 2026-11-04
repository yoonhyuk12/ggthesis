"""Apply verified current MD plus precise cover/survey targets to the base COPY."""
from pathlib import Path
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
import kjn_profile as k

pt=p.Patcher(str(OUT/'base.hwpx'),str(OUT/'assembled.hwpx'),[],str(OUT/'patch_report.md'))
pt.patch_verified_body((OUT/'previous/body.xml').read_text(encoding='utf-8'))
units=p.Units(pt.s2,set())
survey_start=units.spans[units.appendix_start()][0]
survey=pt.s2[survey_start:]
targets=json.loads((OUT/'transplant.json').read_text(encoding='utf-8'))['부록1_설문지']['text_replacements']
for target in targets:
    survey=p.replace_literal_text(survey,target['old'],target['new'],target['count'])
    pt.log.append('SURVEY TARGET x%d | %s -> %s' % (target['count'],target['old'],target['new']))
pt.s2=pt.s2[:survey_start]+survey
cover=pt.base_raw['Contents/section0.xml'].decode('utf-8')
old='중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구'
new='건설현장 YOLO-LLM 안전관제 시스템 개발 및 실증 연구'
cover=p.replace_literal_text(cover,old,new,2)
pt.base_raw['Contents/section0.xml']=cover.encode('utf-8')
pt.log.append('COVER TARGET x2 | '+old+' -> '+new)
pt.append_new_appendices()
pt.toc_from_fresh()
# Current MD includes corrected flow/model PNGs. Their old payloads are now
# unreferenced; use the explicit images.json replaces mapping, never zip-order.
manifest=ET.fromstring(pt.base_raw['Contents/content.hpf'])
base_items={e.get('id'):e.get('href') for e in manifest.iter()
            if e.tag.endswith('}item') and e.get('href','').startswith('BinData/')}
used=set(re.findall(r'binaryItemIDRef="([^"]+)"',cover+pt.s1+pt.s2))
unused={i:href for i,href in base_items.items() if i not in used}
jamovi_hashes={hashlib.sha256(f.read_bytes()).hexdigest() for f in
               (ROOT/'01.docs/설문결과/자모비캡쳐/부표').glob('부표3-*.png')}
non_jamovi={i:v for i,v in pt.bin_imports.items() if hashlib.sha256(v[1]).hexdigest() not in jamovi_hashes}
mapping=json.loads((OUT/'images.json').read_text(encoding='utf-8'))['mapping']
replaced=[]
for entry in mapping:
    if not entry.get('replaces'):continue
    old_id=entry['replaces'].removeprefix('old:')
    if old_id not in unused:continue
    data=(ROOT/entry['source']).read_bytes()
    matches=[i for i,(_,payload,_) in non_jamovi.items() if payload==data]
    assert len(matches)==1,(entry,matches)
    new_id=matches[0]
    old_href=unused[old_id]
    pt.base_raw[old_href]=data
    pt.s2=pt.s2.replace('binaryItemIDRef="'+new_id+'"','binaryItemIDRef="'+old_id+'"')
    del pt.bin_imports[new_id]
    replaced.append(old_id)
    pt.log.append('IMAGE UPDATE | %s -> %s (images.json explicit replaces mapping)' % (entry['caption_prefix'],old_href))
assert set(replaced)==set(unused) and len(replaced)==len(non_jamovi)
pt.write(str(OUT/'patched.hwpx'))
(OUT/'patch_report.md').write_text(pt.summary(),encoding='utf-8')
(OUT/'patch_stats.json').write_text(json.dumps(pt.stats,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'survey_targets.json').write_text(json.dumps(targets,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(pt.stats,ensure_ascii=False))
print('Images: 6 existing positions (corrected flow/model) + 47 appendix PNGs = 53')
