from pathlib import Path
import re,json,difflib,html,collections
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BEFORE=ROOT/'tools/hwpx_transfer/staging/prose_261104'
paras=json.loads((OUT/'base_paras.json').read_text(encoding='utf8'))
def clean(s):
    s=re.sub(r'<!--.*?-->','',s)
    s=re.sub(r'\*\*(.*?)\*\*',r'\1',s)
    s=re.sub(r'`([^`]+)`',r'\1',s)
    s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'\1',s)
    s=re.sub(r'<br\s*/?>',' ',s,flags=re.I)
    return html.unescape(s.strip())
def norm(s):return re.sub(r'\s+','',s)
index=collections.defaultdict(list)
for p in paras:
    if p['text'].strip():index[norm(p['text'])].append(p)
changes=[]
for before in sorted(BEFORE.glob('before_*.md')):
    name=before.name[7:]; a=before.read_text(encoding='utf8').splitlines();b=(ROOT/'01.docs'/name).read_text(encoding='utf8').splitlines()
    assert len(a)==len(b)
    for line,(old,new) in enumerate(zip(a,b),1):
        if old==new:continue
        if old.startswith('|'):
            oc=old.strip().strip('|').split('|');nc=new.strip().strip('|').split('|');assert len(oc)==len(nc)
            for ci,(o,n) in enumerate(zip(oc,nc)):
                if clean(o)!=clean(n):changes.append(dict(source_file='01.docs/'+name,source_line=line,cell=ci,old_md=clean(o),new_md=clean(n)))
        else:changes.append(dict(source_file='01.docs/'+name,source_line=line,cell=None,old_md=clean(old),new_md=clean(new)))
mapping={};mapped=[];unresolved=[];user_edits=[]
marker=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def safe_parts(p,new):
    old=p['text']; styles={c for c,t in p['runs'] if t}
    if len(styles)==1 and not marker.search(old):return [(old,new)]
    ops=[op for op in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes() if op[0]!='equal']
    spans=[];pos=0
    for c,t in p['runs']:
        if t:spans.append((pos,pos+len(t),c))
        pos+=len(t)
    result=[]
    for tag,i,j,k,l in ops:
        # Select a nonempty key carrying enough same-style context.
        allowed=[(a,b,c) for a,b,c in spans if a<=i and j<=b and (i<b or i==j==b)]
        if not allowed:return None
        a,b,c=allowed[0]
        selected=None
        for pad in [8,16,32,64,128,512,2048]:
            left=max(a,i-pad);right=min(b,j+pad)
            key=old[left:right];value=old[left:i]+new[k:l]+old[j:right]
            if key and not marker.search(key) and sum(x['text'].count(key) for x in paras)==1:
                selected=(left,right,key,value);break
        if selected is None:return None
        result.append(selected)
    # Overlap would make map order-dependent; merge by same-style full segment.
    if any(x[1]>y[0] for x,y in zip(result,result[1:])):
        ranges=[]
        for x in result:
            if ranges and x[0]<ranges[-1][1]:ranges[-1][1]=max(ranges[-1][1],x[1])
            else:ranges.append([x[0],x[1]])
        result=[]
        for left,right in ranges:
            edits=[op for op in ops if left<=op[1] and op[2]<=right]
            value=old[left:right]
            for tag,i,j,k,l in reversed(edits):value=value[:i-left]+new[k:l]+value[j-left:]
            key=old[left:right]
            if marker.search(key) or len({c for a,b,c in spans if a<right and b>left})>1:return None
            result.append((left,right,key,value))
    return [(x[2],x[3]) for x in result]
for ch in changes:
    old,new=ch['old_md'],ch['new_md']
    candidates=index.get(norm(old),[])
    if len(candidates)!=1:
        # A paragraph may be embedded inside a longer HWPX paragraph.
        exact=[p for p in paras if old and old in p['text']]
        if len(exact)==1:candidates=exact
    if len(candidates)!=1:
        near=sorted(((difflib.SequenceMatcher(None,norm(old),norm(p['text']),autojunk=False).ratio(),p) for p in paras if p['text'].strip()),key=lambda v:v[0],reverse=True)[:3]
        item=ch|{'reason':'no_unique_exact_before_MD_match','candidates':[{'score':round(s,4),'section':p['section'],'idx':p['idx'],'text':p['text']} for s,p in near]}
        unresolved.append(item);continue
    p=candidates[0];text=p['text']
    if norm(text)==norm(old):target=text[:len(text)-len(text.lstrip())]+new+text[len(text.rstrip()):]
    else:target=text.replace(old,new,1)
    parts=safe_parts(p,target)
    if parts is None:
        unresolved.append(ch|{'section':p['section'],'idx':p['idx'],'old':text,'new':target,'runs':p['runs'],'reason':'mixed_styles_or_marker_needs_scoped_edit'});continue
    if any(sum(q['text'].count(o) for q in paras)!=1 or o in mapping for o,n in parts):
        unresolved.append(ch|{'section':p['section'],'idx':p['idx'],'old':text,'new':target,'reason':'global_key_nonunique_or_duplicate'});continue
    for o,n in parts:
        mapping[o]=n;mapped.append(ch|{'section':p['section'],'idx':p['idx'],'old':o,'new':n})
    ch['section']=p['section'];ch['idx']=p['idx'];ch['target']=target;ch['mapped']=True
# Main approved the three known later citation-verification changes.
for item in list(unresolved):
    key=(item['source_file'],item['source_line'])
    if key not in [('01.docs/02_이론적배경.md',23),('01.docs/02_이론적배경.md',35),('01.docs/03_시스템개발.md',23)]:continue
    c=item['candidates'][0];p=next(p for p in paras if p['section']==c['section'] and p['idx']==c['idx'])
    target='  '+item['new_md']
    if p['idx']==345:
        nonempty=[(style,text) for style,text in p['runs'] if text]
        assert len(nonempty)==3 and [c for c,t in nonempty]==['49','60','49']
        parts=[(nonempty[0][1],target),(nonempty[1][1],''),(nonempty[2][1],'')]
    else:parts=[(p['text'],target)]
    for o,n in parts:
        assert sum(q['text'].count(o) for q in paras)==1 and o not in mapping
        mapping[o]=n;mapped.append(item|{'section':p['section'],'idx':p['idx'],'old':o,'new':n,'approval':'main approved later verified-citation update; marker removal intentional for idx345'})
    ch=next(ch for ch in changes if (ch['source_file'],ch['source_line'])==key)
    ch.update(section=p['section'],idx=p['idx'],target=target,mapped=True)
    unresolved.remove(item)
# Simulate exact longest-first replace order and catch collision against other keys/new text.
sim=[]
for p in paras:
    text=p['text']
    for o,n in sorted(mapping.items(),key=lambda x:-len(x[0])):text=text.replace(o,n)
    sim.append((p,text))
errors=[]
for ch in changes:
    if ch.get('mapped'):
        actual=next(t for p,t in sim if p['section']==ch['section'] and p['idx']==ch['idx'])
        if actual!=ch['target']:errors.append({'source_file':ch['source_file'],'source_line':ch['source_line'],'reason':'simulation_mismatch'})
report={'mapped':mapped,'unresolved':unresolved,'user_edits':user_edits,'coverage':{'changed_MD_units':len(changes),'mapped_MD_units':sum(c.get('mapped',False) for c in changes),'keys':len(mapping),'changed_HW_paragraphs':len({(x['section'],x['idx']) for x in mapped}),'unresolved':len(unresolved),'simulation_errors':errors}}
(OUT/'map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'unresolved.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report['coverage'],ensure_ascii=False,indent=2))
for u in unresolved:print(u['source_file'],u['source_line'],u['cell'],u['reason'],[(c['idx'],c['score']) for c in u.get('candidates',[])])
