"""Read-only HWPX comparison; emits JSON for manual preservation decisions."""
from pathlib import Path
import json,sys,re,difflib,zipfile
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
def chapter(items):
    start=next(i for i,u in enumerate(items) if re.match(r'^제\s*3\s*장\s',u['text']))
    end=next(i for i,u in enumerate(items[start+1:],start+1) if re.match(r'^제\s*4\s*장\s',u['text']))
    return [u for u in items[start:end] if u['text'] or u['tbl'] or '<hp:pic' in u['xml']]
base=chapter(json.loads((OUT/'base_units.json').read_text(encoding='utf-8')))
with zipfile.ZipFile(OUT.with_name('hwpx_261031b')/'assembled.hwpx') as z:
    old=chapter(p.Units(z.read('Contents/section2.xml').decode(),set()).items)
sm=difflib.SequenceMatcher(None,[p.nows(u['text']) for u in old],[p.nows(u['text']) for u in base],autojunk=False)
changes=[]
for tag,a,b,c,d in sm.get_opcodes():
    if tag!='equal':changes.append({'tag':tag,'old':[u['text'] for u in old[a:b]],'base':[u['text'] for u in base[c:d]]})
(OUT/'user_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'old_count':len(old),'base_count':len(base),'user_change_groups':len(changes)},ensure_ascii=False))
