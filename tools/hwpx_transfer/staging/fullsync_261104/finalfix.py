"""Main-only removal of ten empty legacy TOC paragraphs; no prose/style changes."""
from pathlib import Path
import sys,re,zipfile,json
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parents[3]/'tools/hwpx_transfer'))
import patch_from_fresh as p
source=OUT/'resaved2.hwpx'; target=OUT/'fixes.hwpx'
with zipfile.ZipFile(source) as z:
 entries={i.filename:(i,z.read(i.filename)) for i in z.infolist()}
s=entries['Contents/section1.xml'][1].decode();u=p.Units(s,set())
end=next(i for i,v in enumerate(u.items) if p.nows(v['text'])=='표목차' and '<hp:tab' not in v['xml'])
start=end
while start>0 and not u.items[start-1]['text'].strip() and '<hp:tab' not in u.items[start-1]['xml']:start-=1
removed=u.items[start:end]
assert len(removed)==10,len(removed)
assert all(not re.search(r'<hp:(?:tbl|pic|ctrl|secPr)\b',v['xml']) for v in removed)
s=s[:u.spans[start][0]]+s[u.spans[end][0]:]
info=entries['Contents/section1.xml'][0];entries['Contents/section1.xml']=(info,s.encode())
if '--dry-run' not in sys.argv:
 with zipfile.ZipFile(target,'w') as z:
  for info,data in entries.values():z.writestr(info,data)
print(json.dumps({'removed_empty_TOC_paragraphs':len(removed),'output':str(target)},ensure_ascii=False))
