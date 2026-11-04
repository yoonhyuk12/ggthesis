from pathlib import Path
import json,re,difflib
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
paras=json.loads((D/'base_paras.json').read_text(encoding='utf8'))
text=(ROOT/'01.docs/07_참조번호목록.md').read_text(encoding='utf8')
refmd=text.split('## 참고문헌(현행 인용 목록)',1)[1].split('### 6.',1)[0]
cats={};cat=None
for line in refmd.splitlines():
 line=line.strip()
 if line.startswith('### '):cat=re.sub(r'\([^)]*\)','',line[4:]).strip();cats[cat]=[];continue
 if not cat or not line or line.startswith(('>','- ','#')):continue
 original=line
 if '(서울연 ' in line:line=re.sub(r';\s*ref\s*\d+(?=\))','',line)
 starts=list(re.finditer(r'\((?:ref\b|서지관리번호|존재 검증|제[1-5]장|3장 1차|연도:|열람일)',line))
 for match in reversed(starts):
  start=match.start();depth=0;end=None
  for j in range(start,len(line)):
   if line[j]=='(':depth+=1
   elif line[j]==')':
    depth-=1
    if depth==0:end=j+1;break
  if end:line=line[:start]+line[end:]
 if cat.startswith('3.') and ' — ' in line:
  url=re.search(r'https?://[^\s]+',line);line=line.split(' — ',1)[0]+(' '+url.group() if url else '')
 if line.startswith('EN 50136-1:2012'):line=line.split(' 공식 서지:',1)[0]
 line=line.replace('**','').strip();cats[cat].append({'text':line,'original_text':original})
cats={c:v for c,v in cats.items() if v}
def n(s):return re.sub(r'\s+','',s)
oldcats={};heads={};cat=None;active=False
for p in paras:
 if p['section']!='Contents/section2.xml':continue
 t=p['text'].strip()
 if t=='참고문헌':active=True;continue
 if not active:continue
 if t.startswith('부   록'):break
 if re.match(r'^[1-5]\. ',t):cat=t;oldcats[cat]=[];heads[cat]=p;continue
 if re.match(r'^\[\d+\]',t):oldcats[cat].append(p)
delta={'replace':[],'delete':[],'insert_after':[],'unresolved':[],'category_counts':{}}
for cat,newrefs in cats.items():
 olds=oldcats[cat];used=set();anchor=heads[cat];order=0
 for num,entry in enumerate(newrefs,1):
  new=f'[{num:02d}] '+entry['text'];raw=entry['text']
  matches=[p for p in olds if n(re.sub(r'^\[\d+\]\s*','',p['text']))==n(raw)]
  if len(matches)==1:
   p=matches[0];used.add(p['idx']);anchor=p;order=0
   if p['text']!=new:delta['replace'].append({'section':p['section'],'idx':p['idx'],'old':p['text'],'new':new,'reason':'reference numbering or whitespace synchronization'})
  else:
   # Existing author/title similarity requires review rather than presumed new entry.
   near=sorted(((difflib.SequenceMatcher(None,n(raw),n(re.sub(r'^\[\d+\]\s*','',p['text'])),autojunk=False).ratio(),p) for p in olds),key=lambda x:x[0],reverse=True)
   if near and near[0][0]>.82:
    s,p=near[0];delta['unresolved'].append({'category':cat,'new':new,'candidate':p['text'],'idx':p['idx'],'score':s});continue
   order+=1;delta['insert_after'].append({'section':anchor['section'],'idx':anchor['idx'],'text':new,'order':order,'category':cat,'template_idx':olds[0]['idx'],'reason':'new reference in confirmed current MD list'})
 for p in olds:
  if p['idx'] not in used:
   delta['delete'].append({'section':p['section'],'idx':p['idx'],'old':p['text'],'reason':'absent from current references; moved to noncited history after user-approved citation changes'})
 delta['category_counts'][cat]={'old':len(olds),'new':len(newrefs)}
(D/'references_current.json').write_text(json.dumps(cats,ensure_ascii=False,indent=2),encoding='utf8')
(D/'refs_delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2),encoding='utf8')
print({k:len(v) for k,v in delta.items() if isinstance(v,list)})
print(json.dumps(delta,ensure_ascii=False,indent=2))
