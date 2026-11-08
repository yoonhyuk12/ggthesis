from pathlib import Path
import sys,json,re,zipfile,difflib,hashlib
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p
O=Path('tools/hwpx_transfer/staging/full_sync_261104')
def units(file,s):
 with zipfile.ZipFile(file) as z:return p.Units(z.read(f'Contents/section{s}.xml').decode(),set())
for s in [1,2]:
 a=units(O/'patched.hwpx',s);b=units(O/'fresh.hwpx',s)
 av=[v for v in a.items if v['text']];bv=[v for v in b.items if v['text']]
 sm=difflib.SequenceMatcher(None,[p.nows(v['text']) for v in av],[p.nows(v['text']) for v in bv],autojunk=False)
 diffs=[]
 for tag,i,j,k,l in sm.get_opcodes():
  if tag!='equal':diffs.append({'tag':tag,'actual':[v['text'] for v in av[i:j]],'fresh':[v['text'] for v in bv[k:l]]})
 (O/f'text_diff_section{s}.json').write_text(json.dumps(diffs,ensure_ascii=False,indent=2),encoding='utf8')
 print('SECTION',s,json.dumps(diffs,ensure_ascii=False)[:9000])
