from pathlib import Path
import sys
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p,md_to_blocks as m
original=m.parse_file
# Restrict layout declarations to the actual five manuscript chapters, excluding 08 working notes.
def current_only(path):
 result=original(path)
 if not Path(path).name.startswith(('01_','02_','03_','04_','05_')):
  return (result[0],[],*result[2:])
 return result
m.parse_file=current_only
p.main()
