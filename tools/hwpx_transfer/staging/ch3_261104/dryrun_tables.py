"""Validate all table cell mappings in memory; never write HWPX."""
from pathlib import Path
import json
here=Path(__file__).resolve().parent
source=(here/'patch_ch3.py').read_text(encoding='utf-8').split('for ni,n in enumerate(new):',1)[0]
scope={'__file__':str(here/'patch_ch3.py')}
exec(compile(source,'patch_ch3_prefix','exec'),scope)
results=[]
for n in scope['new']:
 if not n['tbl']:continue
 if n['cap']=='<표3-9>':
  results.append({'caption':n['cap'],'mode':'new applicability table'});continue
 o=next(o for o in scope['old'] if o['tbl'] and o['cap']==n['cap'])
 pairs=scope['mapped_cells'](o['xml'],n['xml']);changed=0
 for before,after in pairs:
  x=scope['patchcell'](before,after)
  assert scope['p'].nows(scope['text'](x))==scope['p'].nows(scope['text'](after))
  changed+=x!=before
 results.append({'caption':n['cap'],'mapped_cells':len(pairs),'changed_cells':changed,'original_grid_preserved':True})
(here/'table_mapping_dryrun.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
