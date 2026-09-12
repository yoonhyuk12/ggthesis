from pathlib import Path
import sys,json,zipfile,re,html,difflib,copy
from lxml import etree as E
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|UNVERIFIED|그림 삽입 예정)[^\]]*\]')
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
rows=json.loads((HERE/'base_paras.json').read_text(encoding='utf8'))
changes=json.loads((HERE/'md_changes.json').read_text(encoding='utf8'))
targets={};inserts={}
def add(sec,idx,text):
 key=(sec,idx)
 assert key not in targets or targets[key]==text,(key,targets.get(key),text)
 targets[key]=text
for c in changes:
 if c['file'].startswith('부록'):continue
 assert len(c['old'])==len(c['new']) or len(c['old'])==1
 for i,matches in enumerate(c['matches']):
  if not matches:
   assert c['old'][i].startswith('중소규모 스마트');add('Contents/section2.xml',149,c['new'][i]);continue
  for m in matches:
   lead=re.match(r'^\s*',m['text'])[0]
   add(m['section'],m['idx'],lead+c['new'][i])
 if len(c['new'])>len(c['old']):
  m=c['matches'][0][0];inserts[(m['section'],m['idx'])]=[(m['idx'],t) for t in c['new'][1:]]
lines=(ROOT/'01.docs/07_참조번호목록.md').read_text(encoding='utf8').splitlines()
def bib(prefix):
 text=next(l for l in lines if l.startswith(prefix))
 return re.sub(r'\s*\((?:ref |대표 ref |번호가 중복된 ).*$', '',text)
sec='Contents/section2.xml'
add(sec,2060,'[02] '+bib('국토교통부·'))
for anchor,prefixes in [(2035,['김용선,']),(2043,['이창남,']),(2045,['한소은,','Mi, Y.']),(2049,['류정·']),(2051,['Dixon,','Igbaria,','Kim, J.']),(2056,['Zeschky,']),(2065,['Bhatti,','Green, D.','Radjou,']),(2069,['김정아(2021','손형주(2024'])]:
 inserts[(sec,anchor)]=[(2035,bib(p)) for p in prefixes]
# The contents entry retains its tab control; replace only the changed title later.
oldtitle=next(c['old'][i] for c in changes[:43] for i,n in enumerate(c['new'][:len(c['old'])]) if n.startswith('<표 3-8>')) if any(n.startswith('<표 3-8>') for c in changes[:43] for n in c['new']) else None
with zipfile.ZipFile(HERE/'base.hwpx') as z:
 data={n:z.read(n) for n in z.namelist()}
header=E.fromstring(data['Contents/header.xml'])
chars={n.get('id'):n for n in header.iter() if E.QName(n).localname=='charPr'}
def stykey(n):
 n=copy.deepcopy(n);n.attrib.pop('id',None);n.attrib.pop('textColor',None);return E.tostring(n)
def colorstyle(cid,color):
 key=stykey(chars[cid])
 for i,n in chars.items():
  if n.get('textColor')==color and stykey(n)==key:return i
 n=copy.deepcopy(chars[cid]);nid=str(max(map(int,chars))+1);n.set('id',nid);n.set('textColor',color)
 chars[cid].getparent().append(n);chars[nid]=n;return nid
fresh=3000000000
def edited(raw,p,text,new=False):
 global fresh
 ns=elements(raw)
 assert all(n['name'] in ('hp:p','hp:run','hp:t','hp:linesegarray','hp:lineseg') for n in ns),[n['name'] for n in ns]
 old=own(p);styles=[]
 for r in p.findall(P+'run'):styles.extend([r.get('charPrIDRef')]*len(''.join(''.join(t.itertext()) for t in r.findall(P+'t'))))
 fallback=next((s for s in styles if chars[s].get('textColor')!='#FF0000'),p.find(P+'run').get('charPrIDRef'))
 fallback=colorstyle(fallback,'#000000')
 out=[fallback]*len(text)
 for op,a,b,c,d in difflib.SequenceMatcher(None,old,text,autojunk=False).get_opcodes():
  if op=='equal':out[c:d]=styles[a:b]
  elif op in ('replace','insert'):
   st=styles[min(a,len(styles)-1)] if styles else fallback
   out[c:d]=[colorstyle(st,'#000000')]*(d-c)
 marked=set(i for m in MARK.finditer(text) for i in range(m.start(),m.end()))
 for i in range(len(out)):
  if i in marked:out[i]=colorstyle(out[i],'#FF0000')
  elif chars[out[i]].get('textColor')=='#FF0000':out[i]=colorstyle(out[i],'#000000')
 opening=raw[:ns[0]['tag_end']]
 if new:
  fresh+=1;opening=re.sub(rb'\bid="[^"]*"',f'id="{fresh}"'.encode(),opening,count=1)
  opening=re.sub(rb'\b(pageBreak|columnBreak)="[^"]*"',rb'\1="0"',opening)
 chunks=[opening];a=0
 while a<len(text):
  b=a+1
  while b<len(text) and out[b]==out[a]:b+=1
  chunks.append(f'<hp:run charPrIDRef="{out[a]}"><hp:t>{html.escape(text[a:b],quote=False)}</hp:t></hp:run>'.encode());a=b
 chunks.append(b'</hp:p>');return b''.join(chunks)
modified={};manifest=[]
for section in sorted(set(k[0] for k in targets)|set(k[0] for k in inserts)):
 raw=data[section];ns=elements(raw);ps=[n for n in ns if n['name']=='hp:p'];ep=list(E.fromstring(raw).iter(P+'p'));edits=[];anchors=set()
 for (s,idx),text in targets.items():
  if s!=section:continue
  node=ps[idx];replacement=edited(fragment(raw,node),ep[idx],text)
  edits.append((node['start'],node['end'],replacement));manifest.append({'section':s,'idx':idx,'old':own(ep[idx]),'new':text})
  parent=node['parent']
  while parent:
   if parent['name']=='hp:p':anchors.add(parent['start'])
   parent=parent['parent']
 for (s,idx),items in inserts.items():
  if s!=section:continue
  value=b''.join(edited(fragment(raw,ps[template]),ep[template],text,True) for template,text in items)
  edits.append((ps[idx]['end'],ps[idx]['end'],value))
 for n in ns:
  if n['name']=='hp:linesegarray' and n['parent']['start'] in anchors:edits.append((n['start'],n['end'],b''))
 cursor=0;chunks=[]
 for a,b,v in sorted(edits,key=lambda e:(e[0],e[1])):
  assert a>=cursor,('overlap',a,cursor);chunks.extend([raw[cursor:a],v]);cursor=b
 chunks.append(raw[cursor:]);modified[section]=b''.join(chunks);E.fromstring(modified[section])
# TOC title only; existing tab is deliberately preserved.
raw=data['Contents/section1.xml']
for c in changes[:43]:
 for old,new in zip(c['old'],c['new']):
  if ('표 3-8' in old or '표 3-8' in new) and len(old)<150:
   old=old.replace('<','').replace('>','').split('(단위:')[0];new=new.replace('<','').replace('>','').split('(단위:')[0]
   # Match title text excluding the table number to allow existing bracket format.
   old=re.sub(r'^표 3-8\s*','',old);new=re.sub(r'^표 3-8\s*','',new)
   raw=raw.replace(html.escape(old,quote=False).encode(),html.escape(new,quote=False).encode())
if raw!=data['Contents/section1.xml']:modified['Contents/section1.xml']=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',raw,flags=re.S)
charparent=next(iter(chars.values())).getparent();charparent.set('itemCnt',str(len(chars)))
if len(chars)!=len([n for n in E.fromstring(data['Contents/header.xml']).iter() if E.QName(n).localname=='charPr']):
 modified['Contents/header.xml']=E.tostring(header,encoding='UTF-8',xml_declaration=True,standalone=True)
(HERE/'candidate.hwpx').write_bytes(raw_zip_patch((HERE/'base.hwpx').read_bytes(),modified))
(HERE/'patch_manifest.json').write_text(json.dumps({'replace':manifest,'insert':[{'section':s,'after':i,'texts':[t for _,t in v]} for (s,i),v in inserts.items()],'changed_parts':list(modified)},ensure_ascii=False,indent=2),encoding='utf8')
print('Replaced',len(manifest),'Inserted',sum(map(len,inserts.values())),'Parts',list(modified))
