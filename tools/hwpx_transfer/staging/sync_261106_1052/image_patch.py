"""MAIN ONLY: replace current MD figure 3-3 pixels, preserving all XML and geometry."""
from pathlib import Path
import json,zipfile,hashlib,io
from PIL import Image
O=Path(__file__).parent
def main():
 plan=json.loads((O/'image_patch_plan.json').read_text(encoding='utf8'))
 src=O/'patched.hwpx';dest=O/'image_ready.hwpx';data=Path(plan['source']).read_bytes()
 assert hashlib.sha256(data).hexdigest()==plan['new_sha256']
 with zipfile.ZipFile(src) as z:
  old=z.read(plan['entry'])
  assert hashlib.sha256(old).hexdigest()==plan['old_sha256']
  assert Image.open(io.BytesIO(old)).size==Image.open(io.BytesIO(data)).size
  with zipfile.ZipFile(dest,'w') as w:
   for zi in z.infolist():w.writestr(zi,data if zi.filename==plan['entry'] else z.read(zi.filename))
 with zipfile.ZipFile(src) as a,zipfile.ZipFile(dest) as b:
  assert a.namelist()==b.namelist()
  changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
  assert changed==[plan['entry']]
  assert [x.compress_type for x in a.infolist()]==[x.compress_type for x in b.infolist()]
 (O/'image_patch_audit.json').write_text(json.dumps({'output':dest.as_posix(),'changed_entries':changed,'all_XML_unchanged':True,'pixel_size_preserved':plan['pixel_dimensions'],'HWPX_size_preserved':plan['HWPX_dimensions']},ensure_ascii=False,indent=2),encoding='utf8')
 print('PASS: only',changed,'changed; geometry and all XML preserved')
if __name__=='__main__':main()
