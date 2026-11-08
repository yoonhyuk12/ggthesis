from pathlib import Path
import sys,re
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p,md_to_blocks as m
original=m.parse_file
# Restrict layout declarations to the actual five manuscript chapters, excluding 08 working notes.
def current_only(path):
 result=original(path)
 if not Path(path).name.startswith(('01_','02_','03_','04_','05_')):
  return (result[0],[],*result[2:])
 for b in result[1]:
  if b.get('layout'):
   b['header']=[re.sub(r'<br\s*/?>','',x) for x in b['header']]
   b['rows']=[[re.sub(r'<br\s*/?>','',x) for x in row] for row in b['rows']]
 return result
m.parse_file=current_only
# Baseline already contains declared merges; normal table comparison preserves them.
p.Patcher._declared_table_layouts=lambda self: None
p.main()
