"""Main-only entry: create comparison assembly, never final deliverable."""
from pathlib import Path
import shutil, sys, json, runpy
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
OLD=OUT.with_name('hwpx_261031b')
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import md_to_blocks as m
for name in ['template.hwpx','references.json','transplant.json','ch01.blocks.json','ch02.blocks.json','ch04.blocks.json','ch05.blocks.json','apx1.blocks.json','apx2r.blocks.json','apx3.blocks.json']:
    shutil.copy2(OLD/name,OUT/name)
blocks=m.parse_file('04_연구설계및실증분석.md')[1]
(OUT/'ch04.blocks.json').write_text(json.dumps({'source':'04_연구설계및실증분석.md','blocks':blocks},ensure_ascii=False,indent=2),encoding='utf-8')
source=(OLD/'assemble.py').read_text(encoding='utf-8')
source=source.replace("['ch01','ch02','ch03','ch04','ch05']", "['ch04']")
source=source.replace("['ch01','ch02','ch03','ch04','ch05','apx1','apx2r','apx3']", "['ch04']")
source=source.replace("transplant=rel(OUT/'transplant.json')", "transplant=None")
source=source.replace("(OUT/'images.json').write_text", "images['mapping'].append({'caption_prefix':'<그림 4-2>','source':'01.docs/figures/research/figure_4-2_jamovi_emm_plot.png'})\n(OUT/'images.json').write_text")
# Use original assembly implementation with output paths rebound to this folder.
exec(compile(source,str(OUT/'assemble.py'),'exec'),{'__file__':str(OUT/'assemble.py'),'__name__':'__main__'})
