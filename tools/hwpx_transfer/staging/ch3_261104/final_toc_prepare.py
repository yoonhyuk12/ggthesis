"""Main-only: correct chapter3 TOC titles and remove unreferenced image payloads."""
from pathlib import Path
import zipfile,re,html,json,xml.etree.ElementTree as E,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
import kjn_profile as k
src=OUT/'resaved.hwpx'
with zipfile.ZipFile(src) as z:
 infos=z.infolist();raw={i.filename:z.read(i.filename) for i in infos}
s2=raw['Contents/section2.xml'].decode();s1=raw['Contents/section1.xml'].decode()
titles={}
for u in p.Units(s2,set()).items:
 m=re.match(r'^<(표|그림)\s*3-\d+>',u['text'])
 if m and not u['tbl']:titles[p.nows(m.group())]=u['text']
changed=[]
def fix(m):
 xml=m.group()
 if '<hp:tab' not in xml:return xml
 before,after=xml.split('<hp:tab',1)
 title=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip()
 cap=re.match(r'^<(표|그림)\s*3-\d+>',title)
 if not cap or p.nows(cap.group()) not in titles:return xml
 new=titles[p.nows(cap.group())]
 if p.nows(title)==p.nows(new):return xml
 if xml.count(p.esc(title))==1:
  changed.append({'old':title,'new':new})
  return p.replace_literal_text(xml,title,new,1)
 matches=list(re.finditer(r'(<hp:t(?:\s[^>]*)?>)(.*?)(</hp:t>)',before,re.S))
 if not matches:raise ValueError('Cannot replace title: '+title)
 for i,x in reversed(list(enumerate(matches))):
  before=before[:x.start()]+x.group(1)+(p.esc(new) if i==0 else '')+x.group(3)+before[x.end():]
 changed.append({'old':title,'new':new})
 return re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',before+'<hp:tab'+after,flags=re.S)
raw['Contents/section1.xml']=re.sub(r'<hp:p\b.*?</hp:p>',fix,s1,flags=re.S).encode()
refs=set()
for name,data in raw.items():
 if re.match(r'Contents/section\d+\.xml',name):refs.update(re.findall(r'binaryItemIDRef="([^"]+)"',data.decode()))
hpf=raw['Contents/content.hpf'].decode();removed=[]
def remove(m):
 xml=m.group();el=E.fromstring('<r xmlns:opf="http://www.idpf.org/2007/opf">'+xml+'</r>')[0]
 ident=el.get('id');href=el.get('href','')
 if href.startswith('BinData/') and ident not in refs:removed.append(href);return ''
 return xml
hpf=re.sub(r'<opf:item\b[^>]*/>',remove,hpf)
raw['Contents/content.hpf']=hpf.encode()
with zipfile.ZipFile(OUT/'toc_ready.hwpx','w') as z:
 for i in infos:
  if i.filename not in removed:z.writestr(i,raw[i.filename],compress_type=i.compress_type)
(OUT/'toc_cleanup_report.json').write_text(json.dumps({'titles':changed,'removed_unused_images':removed},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'title_changes':changed,'removed':removed},ensure_ascii=False))
