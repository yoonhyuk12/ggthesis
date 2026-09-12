import json,pathlib,difflib,html,re
P=pathlib.Path(__file__).parent
O=json.loads((P/'old_blocks.json').read_text('utf-8')); N=json.loads((P/'new_blocks.json').read_text('utf-8')); BASE=json.loads((P/'base_paras.json').read_text('utf-8'))
FILES=['04_연구설계.md','05_실증분석결과.md','06_결론.md','부록1_설문지_양식.md']; ranges=[(718,1104),(1104,1981),(1981,2038),(2091,2632)]
def tx(b):return html.unescape(b.get('text',''.join(r['text'] for r in b.get('runs',[])))).replace('**','').replace('`','')
def norm(s):return re.sub(r'\s+','',s)
def key(v):
 i,typ,t=v
 if typ.endswith('caption'):return typ+':'+t.split('>')[0]
 if typ.startswith('h'):return typ+':'+t.split(' ')[0]
 return t
def seq(bs):return [(i,b['type'],tx(b)) for i,b in enumerate(bs) if b['type']!='table']
R={k:[] for k in ['replace','insert_after','delete','user_edits','unresolved','coverage']}
for f,(lo,hi) in zip(FILES,ranges):
 a=seq(O[f]); z=seq(N[f]); pool=[p for p in BASE if lo<=p['idx']<hi and p['table_idx'] is None and p['text'].strip()]
 matches={i:[p for p in pool if norm(p['text'])==norm(t)] for i,typ,t in a}
 for tag,i,j,k,l in difflib.SequenceMatcher(None,[key(x) for x in a],[key(x) for x in z],autojunk=False).get_opcodes():
  if tag=='equal':
   for av,zv in zip(a[i:j],z[k:l]):
    if av[2]!=zv[2]:
     mm=matches[av[0]]
     if len(mm)==1:
      pp=mm[0];R['replace'].append({'section':pp['section'],'idx':pp['idx'],'old':pp['text'],'new':zv[2]});R['coverage'].append({'file':f,'old_blocks':[av[0]],'new_blocks':[zv[0]],'status':'mapped_structural'})
     else:R['coverage'].append({'file':f,'old_blocks':[av[0]],'new_blocks':[zv[0]],'status':'C_table_caption','new_texts':[zv[2]]})
   continue
  aa=a[i:j]; zz=z[k:l]; cov={'file':f,'old_blocks':[v[0] for v in aa],'new_blocks':[v[0] for v in zz],'tag':tag}; R['coverage'].append(cov)
  if any(t.startswith('![') for _,_,t in aa):
   cov['status']='main_figure'; cov['new_texts']=[v[2] for v in zz];continue
  if f.startswith('부록') and aa and all(any(norm(p['text'])==norm(t) and p['table_idx'] is not None for p in BASE if lo<=p['idx']<hi) for _,_,t in aa):
   cov['status']='C_table_cells';cov['new_texts']=[v[2] for v in zz];continue
  mapped=[];fail=False
  for bi,typ,t in aa:
   mm=matches[bi]
   if len(mm)==1:mapped.append(mm[0]);continue
   best=sorted([(difflib.SequenceMatcher(None,norm(t),norm(p['text'])).ratio(),p) for p in pool],key=lambda x:-x[0])[:2]
   R['unresolved'].append({'file':f,'old_block':bi,'old_md':t,'candidates':[{'score':s,'idx':p['idx'],'text':p['text']} for s,p in best],'exact_count':len(mm)})
   fail=True
  if fail:cov['status']='unresolved';continue
  if not aa:
   prev=next((matches[a[ii][0]][0] for ii in range(i-1,-1,-1) if len(matches[a[ii][0]])==1),None)
   if f.startswith('부록'):
    for anchor in [2111,2457]:R['insert_after'].append({'section':'Contents/section2.xml','idx':anchor,'template_idx':2134,'texts':[v[2] for v in zz]})
   elif prev:R['insert_after'].append({'section':prev['section'],'idx':prev['idx'],'template_idx':prev['idx'],'texts':[v[2] for v in zz]})
   else:R['unresolved'].append(cov)
  else:
   for p,v in zip(mapped,zz):R['replace'].append({'section':p['section'],'idx':p['idx'],'old':p['text'],'new':v[2]})
   for p in mapped[len(zz):]:R['delete'].append({'section':p['section'],'idx':p['idx'],'old':p['text']})
   if len(zz)>len(mapped):
    p=mapped[-1];R['insert_after'].append({'section':p['section'],'idx':p['idx'],'template_idx':p['idx'],'texts':[v[2] for v in zz[len(mapped):]]})
  cov['status']='mapped'
(P/'B_draft.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),'utf-8')
print({k:len(v) for k,v in R.items()})
for x in R['unresolved']:print(x['file'],x['old_block'],x['old_md'][:95],[(c['idx'],round(c['score'],3),c['text'][:70]) for c in x['candidates']])
