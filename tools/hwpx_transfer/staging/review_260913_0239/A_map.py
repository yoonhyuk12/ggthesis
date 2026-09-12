import json,pathlib,difflib,html,re
P=pathlib.Path(__file__).parent
def read(f):return json.loads((P/f).read_text(encoding='utf-8'))
O,N,B=map(read,['old_blocks.json','new_blocks.json','base_paras.json'])
def tx(b):return html.unescape(b.get('text',''.join(r['text'] for r in b.get('runs',[])))).replace('**','').replace('`','')
def norm(s):return re.sub(r'\s+','',html.unescape(s)).translate(str.maketrans({'․':'·','ㆍ':'·','∙':'·','∼':'~','～':'~'}))
def eligible(b):return b['type'] in ['p','h1','h2','h3','h4','table_caption'] and not tx(b).startswith('![')
R=[]
for k in list(O)[:3]:
 a,b=O[k],N[k]
 for tag,i,j,u,v in difflib.SequenceMatcher(None,[json.dumps(x,ensure_ascii=False) for x in a],[json.dumps(x,ensure_ascii=False) for x in b],autojunk=False).get_opcodes():
  if tag=='equal':continue
  row={'file':k,'tag':tag,'old_range':[i,j],'new_range':[u,v],'old':[],'new':[]}
  for z in range(i,j):
   if not eligible(a[z]):continue
   t=tx(a[z]); hits=[p for p in B if p['table_idx'] is None and norm(p['text'])==norm(t)]
   near=sorted([(difflib.SequenceMatcher(None,norm(t),norm(p['text'])).ratio(),p) for p in B if p['table_idx'] is None and p['text']],key=lambda x:x[0],reverse=True)[:2] if len(hits)!=1 else []
   row['old'].append({'block':z,'type':a[z]['type'],'text':t,'hits':[p['idx'] for p in hits],'near':[(round(s,3),p['idx'],p['text']) for s,p in near]})
  row['new']=[{'block':z,'type':b[z]['type'],'text':tx(b[z])} for z in range(u,v) if eligible(b[z])]
  R.append(row)
(P/'A_diff.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf-8')
for r in R:
 print(r['file'],r['old_range'],r['new_range'],'old',[(x['block'],x['hits'],[(q[0],q[1]) for q in x['near']]) for x in r['old']],'new',[(x['block'],x['type'],x['text'][:28]) for x in r['new']])
