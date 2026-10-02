"""Read-only source analysis; writes JSON specification only."""
import json, hashlib, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
QUOTES=str.maketrans({'‘':"'",'’':"'",'“':'"','”':'"'})
def norm(s): return ''.join(c.translate(QUOTES) for c in s if not c.isspace())
def locate(text, needle):
    positions=[i for i,c in enumerate(text) if not c.isspace()]
    hay=norm(text); key=norm(needle)
    found=[]; at=0
    while key and (at:=hay.find(key,at))>=0:
        found.append((positions[at],positions[at+len(key)-1]+1)); at+=1
    return found
def main():
    paras=load(HERE/'base_paras.json'); records=[]
    for label,group,edits in [('A','changes','edits'),('B','paragraphs','edited_spans'),('C','changes','sentence_changes')]:
        report=load(ROOT/f'.agents/watermarks-remover/local-reports/edit_{label}_report.json')
        for r in report[group]:
            if r.get('action','edit')=='edit': records.append((label,r,edits))
    assert len(records)==164,len(records)
    spec=dict(base_sha256=sha(HERE/'base.hwpx'),source=load(HERE/'source.json'),md_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'01.docs').glob('*.md')},replacements=[],conflicts=[],already_present=[],dispositions=[])
    for label,r,edit_key in records:
        identity=dict(report=label,source_md=r['path'],paragraph_index=r['paragraph_index'])
        edits=r[edit_key]; md=(ROOT/r['path']).read_text(encoding='utf-8-sig')
        if norm(r['new']) not in norm(md):
            spec['conflicts'].append(dict(**identity,reason='current MD new paragraph absent')); continue
        candidates=[p for p in paras if all(locate(p['text'],e['old']) or locate(p['text'],e['new']) for e in edits)]
        # Whole-paragraph context disambiguates repeated sentences, without requiring unchanged manual context.
        if len(candidates)>1:
            exact=[p for p in candidates if norm(p['text']) in (norm(r['old']),norm(r['new']))]
            if len(exact)==1: candidates=exact
        if len(candidates)!=1:
            import difflib
            nearest=sorted(paras,key=lambda p:difflib.SequenceMatcher(None,norm(r['old']),norm(p['text']),autojunk=False).ratio(),reverse=True)[:1]
            spec['conflicts'].append(dict(**identity,reason='unique matching paragraph absent',candidate_count=len(candidates),old_md=r['old'],new_md=r['new'],edits=edits,nearest=[{k:p[k] for k in ('section','idx','text')} for p in nearest])); continue
        p=candidates[0]; changes=[]; errors=[]
        for e in edits:
            hits=locate(p['text'],e['old'])
            if not hits and len(locate(p['text'],e['new']))==1: continue
            if len(hits)!=1: errors.append('nonunique sentence'); continue
            start,end=hits[0]
            changes.append(dict(old=p['text'][start:end],new=e['new'],start=start,end=end))
        changes.sort(key=lambda c:c['start'])
        if any(a['end']>b['start'] for a,b in zip(changes,changes[1:])): errors.append('overlapping sentences')
        if errors: spec['conflicts'].append(dict(**identity,reason=errors));continue
        if not changes: spec['already_present'].append(dict(**identity,section=p['section'],idx=p['idx']));continue
        new=p['text']
        for c in reversed(changes): new=new[:c['start']]+c['new']+new[c['end']:]
        spec['replacements'].append(dict(**identity,section=p['section'],idx=p['idx'],old_hwpx=p['text'],new_hwpx=new,changes=changes,manual_context_preserved=norm(p['text'])!=norm(r['old'])))
    for kind in ('replacements','conflicts','already_present'):
        spec['dispositions'].extend(dict(report=r['report'],source_md=r['source_md'],paragraph_index=r['paragraph_index'],disposition=kind) for r in spec[kind])
    spec['counts']={k:len(spec[k]) for k in ('replacements','conflicts','already_present','dispositions')}
    assert len(spec['dispositions'])==164
    (HERE/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    print(spec['counts'])
if __name__=='__main__': main()
