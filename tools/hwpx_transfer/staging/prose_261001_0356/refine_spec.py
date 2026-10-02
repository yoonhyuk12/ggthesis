"""Refine split-list mapping and mixed-style sentence into safe exact phrase edits."""
import json,re
from build_spec import HERE,load,locate,norm
def main():
 s=load(HERE/'spec.json');paras=load(HERE/'base_paras.json')
 for r in s['replacements']:
  if r['section']=='Contents/section2.xml' and r['idx']==225 and r['changes'][0]['old'].endswith('검정한다.'):
   c=r['changes'][0]; a,b=c['old'],c['new']; suffix=0
   while suffix<min(len(a),len(b)) and a[-suffix-1]==b[-suffix-1]:suffix+=1
   assert suffix>0
   c.update(old=a[:-suffix],new=b[:-suffix],end=c['end']-suffix)
   r['safety_note']='Shared unchanged sentence suffix preserved in original mixed-style runs; only changed initial phrase is targeted.'
 for c in list(s['conflicts']):
  if c['report']=='B' and c['paragraph_index'] in (37,52):
   def render(t):return re.sub(r'`([^`]+)`',r'\1',t)
   edits=[dict(old=render(e['old']),new=render(e['new'])) for e in c['edits']]
   hits=[p for p in paras if all(len(locate(p['text'],e['old']))==1 for e in edits)]
   assert len(hits)==1
   p=hits[0];changes=[];new=p['text']
   for e in edits:
    a,b=locate(p['text'],e['old'])[0];changes.append(dict(old=p['text'][a:b],new=e['new'],start=a,end=b))
   for e in sorted(changes,key=lambda e:e['start'],reverse=True):new=new[:e['start']]+e['new']+new[e['end']:]
   s['replacements'].append(dict(report=c['report'],source_md=c['source_md'],paragraph_index=c['paragraph_index'],section=p['section'],idx=p['idx'],old_hwpx=p['text'],new_hwpx=new,changes=changes,mapping_note='Coordinator authorized rendering inline-code delimiters only; code content preserved.'))
   s['conflicts'].remove(c)
   for d in s['dispositions']:
    if d['report']=='B' and d['paragraph_index']==c['paragraph_index']:d['disposition']='replacements'
  if c['report']=='C' and c['paragraph_index']==53:
   for e in c['edits']:
    hits=[(p,locate(p['text'],e['old'])) for p in paras if locate(p['text'],e['old'])]
    assert len(hits)==1 and len(hits[0][1])==1
    p,h=hits[0];a,b=h[0]
    s['replacements'].append(dict(report=c['report'],source_md=c['source_md'],paragraph_index=c['paragraph_index'],section=p['section'],idx=p['idx'],old_hwpx=p['text'],new_hwpx=p['text'][:a]+e['new']+p['text'][b:],changes=[dict(old=p['text'][a:b],new=e['new'],start=a,end=b)],mapping_note='MD list block maps to separate unique HWPX paragraphs.'))
   s['conflicts'].remove(c)
   for d in s['dispositions']:
    if d['report']=='C' and d['paragraph_index']==53:d['disposition']='replacements';d['hwpx_paragraphs']=2
 s['counts']={k:len(s[k]) for k in ('replacements','conflicts','already_present','dispositions')}
 s['counts']['md_paragraphs_ready']=sum(d['disposition']=='replacements' for d in s['dispositions'])
 (HERE/'spec.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
 print(s['counts'])
if __name__=='__main__':main()
