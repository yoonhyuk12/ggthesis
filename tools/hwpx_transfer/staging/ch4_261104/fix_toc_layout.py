"""Main-only post-resave repair: real chapter4 headings and table4-4 start."""
from pathlib import Path
import sys,re,zipfile,html,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
with zipfile.ZipFile(OUT/'resaved.hwpx') as z:
 infos=z.infolist();raw={i.filename:z.read(i.filename) for i in infos}
s1=raw['Contents/section1.xml'].decode();s2=raw['Contents/section2.xml'].decode()
u=p.Units(s2,set());a=next(i for i,v in enumerate(u.items) if re.match(r'^제\s+4\s+장\s+',v['text']));b=next(i for i,v in enumerate(u.items[a+1:],a+1) if re.match(r'^제\s+5\s+장\s+',v['text']))
headings=[v['text'] for v in u.items[a:b] if re.match(r'^제\s+\d+\s+(장|절|항)\s+',v['text'])]
def title(v):return html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',v['xml'].split('<hp:tab',1)[0]))).strip()
t=p.Units(s1,set());old=[];inside=False
for v in t.items:
 text=title(v)
 if re.match(r'^제\s*4\s*장',text):inside=True
 elif re.match(r'^제\s*\d+\s*장',text):inside=False
 if inside and '<hp:tab' in v['xml']:old.append(v)
clean=lambda x:re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',x,flags=re.S)
out=[]
for i,text in enumerate(headings):
 v=old[i];out.append(clean(p.replace_literal_text(v['xml'],title(v),text,1)))
s1=s1.replace(old[0]['xml'],''.join(out),1)
for v in old[1:]:s1=s1.replace(v['xml'],'',1)
cap=next(v for v in u.items[a:b] if v['text'].startswith('<표 4-4>') and not v['tbl'])
q=clean(cap['xml']);q=re.sub(r'pageBreak="\d+"','pageBreak="1"',q,count=1)
assert 'pageBreak="1"' in q
s2=s2.replace(cap['xml'],q,1)
raw['Contents/section1.xml']=s1.encode();raw['Contents/section2.xml']=s2.encode()
with zipfile.ZipFile(OUT/'fixes.hwpx','w') as z:
 for i in infos:z.writestr(i,raw[i.filename],compress_type=i.compress_type)
print(json.dumps({'old_toc':len(old),'new_toc':len(headings),'headings':headings,'table4_4_new_page':True},ensure_ascii=False))
