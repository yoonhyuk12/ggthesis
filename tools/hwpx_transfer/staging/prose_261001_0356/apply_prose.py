"""Coordinator-only writer. Default is read-only preflight; --write creates candidate.hwpx."""
import sys
sys.dont_write_bytecode=True
import json, re, html, zipfile, io
import xml.etree.ElementTree as ET
from pathlib import Path
from raw_support import elements, raw_zip_patch, require, sha
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
MARKER=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
def owned(p): return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def load(): return json.loads((HERE/'spec.json').read_text(encoding='utf-8'))
def check_sources(s):
    require(sha((HERE/'base.hwpx').read_bytes())==s['base_sha256'],'base changed')
    require(sha((ROOT/s['source']['source']).read_bytes())==s['source']['sha256'],'source changed')
    for path,digest in s['md_sha256'].items(): require(sha((ROOT/path).read_bytes())==digest,'MD changed: '+path)
def splice(data,edits):
    cursor=0; out=[]
    for a,b,v in sorted(edits):
        require(a>=cursor,'overlapping XML edits'); out.extend((data[cursor:a],v)); cursor=b
    out.append(data[cursor:]); return b''.join(out)
def paragraph_edits(data,node,record):
    raw=data[node['start']:node['end']]; ns=elements(raw); p=ns[0]
    runs=[n for n in ns if n['name']=='hp:run' and n['parent'] is p]
    ts=[n for n in ns if n['name']=='hp:t' and any(n['parent'] is r for r in runs)]
    text=''; segments=[]
    for t in ts:
        require(not any(n['parent'] is t for n in ns),'nested text control: unsafe')
        end=t['end']-len(b'</hp:t>') if not t['selfclose'] else t['tag_end']
        val=html.unescape(raw[t['tag_end']:end].decode('utf-8')) if not t['selfclose'] else ''
        segments.append(dict(node=t,start=len(text),end=len(text)+len(val),text=val,style=t['parent']['attrs'].get('charPrIDRef')));text+=val
    require(text==record['old_hwpx'],'paragraph old text mismatch')
    values=[x['text'] for x in segments]; edits=[]
    for c in sorted(record['changes'],key=lambda c:c['start'],reverse=True):
        a,b=c['start'],c['end'];require(text[a:b]==c['old'],'sentence mismatch')
        require(not any(a<m.end() and b>m.start() for m in MARKER.finditer(text)),'sentence overlaps protected marker')
        touched=[i for i,x in enumerate(segments) if x['start']<b and x['end']>a]
        require(touched,'empty sentence')
        require(len({segments[i]['style'] for i in touched})==1,'sentence crosses mixed char styles')
        first,last=touched[0],touched[-1]
        # No hidden control may sit between the affected text fragments.
        lo=segments[first]['node']['tag_end'];hi=segments[last]['node']['start']
        require(not any(lo<=n['start']<hi and n['name'] not in ('hp:run','hp:t') for n in ns),'sentence crosses control')
        for i in touched:
            x=segments[i]; left=max(0,a-x['start']);right=min(len(x['text']),b-x['start'])
            values[i]=values[i][:left]+(c['new'] if i==first else '')+values[i][right:]
    require(''.join(values)==record['new_hwpx'],'new paragraph text mismatch')
    for x,v in zip(segments,values):
        if v==x['text']: continue
        t=x['node'];require(not t['selfclose'],'cannot fill selfclosing t')
        edits.append((node['start']+t['tag_end'],node['start']+t['end']-len(b'</hp:t>'),html.escape(v,quote=False).encode('utf-8')))
    for n in ns:
        if n['name']=='hp:linesegarray' and n['parent'] is p: edits.append((node['start']+n['start'],node['start']+n['end'],b''))
    return edits
def prepare(s):
    check_sources(s); changed={}; failures=[]; evidence=[]
    with zipfile.ZipFile(HERE/'base.hwpx') as z:
        for section in sorted({r['section'] for r in s['replacements']}):
            data=z.read(section); ns=elements(data); paras=[n for n in ns if n['name']=='hp:p']; edits=[]
            for r in s['replacements']:
                if r['section']!=section: continue
                try:
                    e=paragraph_edits(data,paras[r['idx']],r);edits.extend(e)
                    evidence.append(dict(section=section,idx=r['idx'],fragments=len(e),sentences=len(r['changes'])))
                except ValueError as ex: failures.append(dict(section=section,idx=r['idx'],reason=str(ex),source_md=r['source_md'],paragraph_index=r['paragraph_index']))
            changed[section]=splice(data,edits);ET.fromstring(changed[section])
    return changed,failures,evidence
def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--allow-conflicts',action='store_true');args=ap.parse_args()
    s=load();changed,failures,evidence=prepare(s)
    result=dict(ok=not failures,counts=s['counts'],unsafe=failures,paragraphs=evidence,source_sha256=s['base_sha256'],mode='preflight')
    if args.write:
        require(not failures,'unsafe cases remain');require(args.allow_conflicts or not s['conflicts'],'unresolved conflicts: review spec; explicit --allow-conflicts needed for safe subset')
        out=HERE/'candidate.hwpx';require(not out.exists(),'candidate already exists')
        candidate=raw_zip_patch((HERE/'base.hwpx').read_bytes(),changed)
        with zipfile.ZipFile(io.BytesIO(candidate)) as z: require(z.testzip() is None,'ZIP CRC failed')
        with out.open('xb') as f:f.write(candidate)
        result.update(mode='written',candidate_sha256=sha(candidate))
    (HERE/('patch_evidence.json' if args.write else 'preflight.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(ok=result['ok'],counts=s['counts'],unsafe=failures),ensure_ascii=False))
    if failures: raise SystemExit(1)
if __name__=='__main__':main()
