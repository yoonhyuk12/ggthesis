"""Reviewed MD synchronization; MAIN context executes, worker only compiles."""
from pathlib import Path
import sys,json,re,difflib,zipfile,io,html
from lxml import etree as E
from PIL import Image
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p, kjn_profile as k
O=Path(__file__).parent
HP='{'+k.NS['hp']+'}'; HC='{'+k.NS['hc']+'}'
pt=p.Patcher(str(O/'patched.hwpx'),str(O/'fresh.hwpx'),[],None)
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
with zipfile.ZipFile(info['base']) as z:
    original2=z.read('Contents/section2.xml').decode('utf8')
    original1=z.read('Contents/section1.xml').decode('utf8')
audit=[]
def wrap(x):return E.fromstring(k._wrap(x).encode('utf8'))
def xml(x):return re.sub(r' xmlns:[^=]+="[^"]*"','',E.tostring(x,encoding='unicode'))
def text(x):return ''.join(''.join(t.itertext()) for t in x.iter(HP+'t'))
def clear(x):
    for v in list(x.iter(HP+'linesegarray')):v.getparent().remove(v)
def capnum(t):
    m=re.match(r'<그림\s*(\d+-\d+)>',t)
    return m.group(1) if m else None
def picture_map(units):
    """Nearest picture/caption association; each picture paired only once."""
    result={}; used=set()
    for i,u in enumerate(units):
        if '<hp:pic' not in u['xml']:continue
        candidates=[(abs(j-i),j,capnum(v['text'])) for j,v in enumerate(units) if abs(j-i)<=3 and capnum(v['text'])]
        candidates.sort()
        if not candidates:raise AssertionError(('Unassociated picture',i))
        _,j,num=candidates[0]
        if num in result:raise AssertionError(('Duplicate picture',num))
        result[num]=u;used.add(i)
    return result
bu=p.Units(pt.s2,set()); fu=p.Units(pt.fresh_s2,set()); ou=p.Units(original2,set())
basepics=picture_map(ou.items)
freshpics=picture_map(fu.items)
desired=set(freshpics)
# Nonempty alignment is the content authority; unaffected paragraphs stay byte-identical.
bn=[x for x in bu.items if x['text'].strip()]; fn=[x for x in fu.items if x['text'].strip()]
same={}
for tag,a,b,c,d in difflib.SequenceMatcher(None,[p.nows(x['text']) for x in bn],[p.nows(x['text']) for x in fn],autojunk=False).get_opcodes():
    if tag=='equal':
        for i,j in zip(range(a,b),range(c,d)):same[id(fn[j])]=bn[i]['xml']
    else:audit.append({'content_change':tag,'old':[x['text'] for x in bn[a:b]],'new':[x['text'] for x in fn[c:d]]})
out=[]; nonempty_index=0
for u in fu.items:
    if '<hp:pic' in u['xml']:continue
    if u['text'].strip():
        n=capnum(u['text'])
        if n:
            # Keep original image geometry and position directly above its caption.
            pic=basepics.get(n)
            out.append(pic['xml'] if pic else pt.take_fresh(freshpics[n]['xml']))
        out.append(same.get(id(u)) or pt.take_fresh(u['xml']))
        nonempty_index+=1
    else:
        # Blank positions follow current section structure; keep an adjacent base blank
        # when available, otherwise import the fresh blank's own style.
        out.append(pt.take_fresh(u['xml']))
pt.s2=bu.head+''.join(out)+bu.tail
# Preserve original cells/geometry for explicitly reviewed text-only tables.
mapping={'<표2-2>':'<표2-2>','<표2-3>':'<표2-3>','<표4-7>':'<표4-8>'}
def gettable(units,cap):return next(x for x in units if x['tbl'] and x['cap']==cap)
for newcap,oldcap in mapping.items():
    original=gettable(ou.items,oldcap); fresh=gettable(fu.items,newcap)
    br=wrap(original['xml']);fr=wrap(fresh['xml'])
    bc=list(br.iter(HP+'tc'));fc=list(fr.iter(HP+'tc'))
    assert len(bc)==len(fc),(newcap,'cell count')
    changes=[]
    for b,f in zip(bc,fc):
        for tag in ['cellAddr','cellSpan']:assert b.find(HP+tag).attrib==f.find(HP+tag).attrib,(newcap,tag)
        if p.nows(text(b))==p.nows(text(f)):continue
        ts=list(b.iter(HP+'t'));assert ts
        changes.append([text(b),text(f)])
        ts[0].text=text(f)
        for ch in list(ts[0]):ts[0].remove(ch)
        for t in ts[1:]:t.text=''
        clear(b)
    # Invalidate anchor cache while keeping unchanged cell caches.
    for seg in br[0].findall(HP+'linesegarray'):br[0].remove(seg)
    replacement=xml(br[0]);assert p.compare_tables(replacement,fresh['xml'])[0],newcap
    current=gettable(p.Units(pt.s2,set()).items,newcap)
    pt.s2=pt.s2.replace(current['xml'],replacement,1)
    audit.append({'preserved_table':newcap,'source_table':oldcap,'changed_cells':changes})
# Restore known old total width on structurally rebuilt tables; derive new cell
# widths from exact grid boundaries, never from summed row spans.
for cap in ['<표4-3>','<표4-10>','<표4-11>','<표4-12>','<표4-13>','<표4-14>']:
    old=next((x for x in ou.items if x['tbl'] and x['cap']==cap),None)
    current=gettable(p.Units(pt.s2,set()).items,cap)
    r=wrap(current['xml']);t=next(r.iter(HP+'tbl'));cells=t.findall(HP+'tr/'+HP+'tc')
    width=int(t.find(HP+'sz').get('width'))
    oldwidth=int(next(wrap(old['xml']).iter(HP+'tbl')).find(HP+'sz').get('width')) if old else width
    if width!=oldwidth:
        n=int(t.get('colCnt')); bounds={0:0,n:width}
        while len(bounds)<n+1:
            before=len(bounds)
            for c in cells:
                col=int(c.find(HP+'cellAddr').get('colAddr'));span=int(c.find(HP+'cellSpan').get('colSpan'));cw=int(c.find(HP+'cellSz').get('width'))
                if col in bounds:bounds[col+span]=bounds[col]+cw
                if col+span in bounds:bounds[col]=bounds[col+span]-cw
            assert len(bounds)>before,('Cannot derive grid',cap)
        scaled={i:round(bounds[i]*oldwidth/width) for i in range(n+1)}
        t.find(HP+'sz').set('width',str(oldwidth))
        for c in cells:
            col=int(c.find(HP+'cellAddr').get('colAddr'));span=int(c.find(HP+'cellSpan').get('colSpan'))
            c.find(HP+'cellSz').set('width',str(scaled[col+span]-scaled[col]))
        clear(r);pt.s2=pt.s2.replace(current['xml'],xml(r[0]),1)
    audit.append({'rebuilt_table':cap,'width_preserved':oldwidth,'previous_width':width})
def label(u):return p.nows(html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',u['xml'].split('<hp:tab')[0]))))
available={label(u):u for u in p.Units(original1,set()).items if '<hp:tab' in u['xml']}
for u in p.Units(pt.s1,set()).items:
    if '<hp:tab' in u['xml'] and label(u) in available:
        pt.s1=pt.s1.replace(u['xml'],available[label(u)]['xml'],1)
expected=[p.nows(x['text']) for x in fu.items if x['text'].strip()]
actual=[p.nows(x['text']) for x in p.Units(pt.s2,set()).items if x['text'].strip()]
assert actual==expected,'Resolved nonempty content differs from fresh'
assert '<그림 4-2>' not in pt.s2
pt.write(str(O/'resolved.hwpx'))
# Replace changed figure pixels while retaining every unaffected image byte.
with zipfile.ZipFile(O/'resolved.hwpx') as z:infos=z.infolist();data={i.filename:z.read(i) for i in infos}
manifest=E.fromstring(data['Contents/content.hpf']);items={x.get('id'):x.get('href') for x in manifest.iter() if x.tag.endswith('}item')}
units=p.Units(data['Contents/section2.xml'].decode('utf8'),set());pics=picture_map(units.items)
for m in json.loads((O/'images.json').read_text(encoding='utf8'))['mapping']:
    num=capnum(m['caption_prefix']);pic=pics[num];r=wrap(pic['xml']);img=next(r.iter(HC+'img'));href=items[img.get('binaryItemIDRef')]
    source=Path(m['source']).read_bytes();a=Image.open(io.BytesIO(data[href])).convert('RGBA');b=Image.open(io.BytesIO(source)).convert('RGBA')
    if a.size!=b.size or a.tobytes()!=b.tobytes():
        data[href]=source;clear(r)
        section=data['Contents/section2.xml'].decode('utf8').replace(pic['xml'],xml(r[0]),1)
        data['Contents/section2.xml']=section.encode('utf8')
        audit.append({'updated_image':num,'source':m['source'],'old_size':a.size,'new_size':b.size})
with zipfile.ZipFile(O/'ready.hwpx','w') as z:
    for i in infos:z.writestr(i,data[i.filename])
(O/'resolution_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print('Resolved content sequence matches fresh; ready.hwpx written; audit entries',len(audit))
