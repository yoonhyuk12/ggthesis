"""Reviewed MD synchronization; MAIN context executes, worker only compiles."""
from pathlib import Path
import sys,json,re,difflib,zipfile,io,html,copy
from lxml import etree as E
from PIL import Image
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p, kjn_profile as k
O=Path(__file__).parent
HP='{'+k.NS['hp']+'}'; HC='{'+k.NS['hc']+'}'
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
import hashlib
assert hashlib.sha256(Path(info['base']).read_bytes()).hexdigest()==info['sha256']
pt=p.Patcher(info['base'],str(O/'fresh.hwpx'),[],None)
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
same={}; before_base={}; pending=[]
for u in bu.items:
    if not u['text'].strip() and '<hp:pic' not in u['xml']:pending.append(u['xml'])
    elif u['text'].strip():before_base[id(u)]=pending;pending=[]
base_match={}
for tag,a,b,c,d in difflib.SequenceMatcher(None,[p.nows(x['text']) for x in bn],[p.nows(x['text']) for x in fn],autojunk=False).get_opcodes():
    if tag=='equal':
        for i,j in zip(range(a,b),range(c,d)):
            same[id(fn[j])]=bn[i]['xml'];base_match[id(fn[j])]=bn[i]
    else:audit.append({'content_change':tag,'old':[x['text'] for x in bn[a:b]],'new':[x['text'] for x in fn[c:d]]})
out=[]; nonempty_index=0; fresh_blanks=[]
for u in fu.items:
    if '<hp:pic' in u['xml']:continue
    if u['text'].strip():
        old=base_match.get(id(u))
        out.extend(before_base.get(id(old),[]) if old else [pt.take_fresh(x) for x in fresh_blanks])
        fresh_blanks=[]
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
        fresh_blanks.append(u['xml'])
pt.s2=bu.head+''.join(out)+bu.tail
# Preserve original cells/geometry for explicitly reviewed text-only tables.
review=json.loads((O/'change_audit.json').read_text(encoding='utf8'))
mapping={t['caption']:t['caption'] for t in review['tables'] if t['status']=='text_only'}
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
        assert not re.search(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)|실험전',text(f)), (newcap,'mixed marker requires targeted run patch')
        ts[0].text=text(f)
        for ch in list(ts[0]):ts[0].remove(ch)
        for t in ts[1:]:t.text=''
        if b.find(HP+'cellAddr').get('rowAddr')=='0':
            lines=[text(q) for q in f.find(HP+'subList').findall(HP+'p') if text(q)]
            if len(lines)>1:
                ts[0].text=lines[0]
                sub=b.find(HP+'subList');proto=sub.find(HP+'p')
                for offset,line in enumerate(lines[1:],1):
                    q=copy.deepcopy(proto)
                    qts=list(q.iter(HP+'t'));qts[0].text=line
                    for other in qts[1:]:other.text=''
                    q=wrap(pt.renumber(xml(q)))[0]
                    sub.insert(sub.index(proto)+offset,q)
        clear(b)
    # Invalidate anchor cache while keeping unchanged cell caches.
    for seg in br[0].findall(HP+'linesegarray'):br[0].remove(seg)
    replacement=xml(br[0]);assert p.compare_tables(replacement,fresh['xml'])[0],newcap
    current=gettable(p.Units(pt.s2,set()).items,newcap)
    pt.s2=pt.s2.replace(current['xml'],replacement,1)
    audit.append({'preserved_table':newcap,'source_table':oldcap,'changed_cells':changes})
# Restore known old total width on structurally rebuilt tables; derive new cell
# widths from exact grid boundaries, never from summed row spans.
for cap in review['force_fresh']:
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
# Section1 is unchanged except one reviewed table-list caption; preserve its
# actual baseline typography, thanks, abstract and tab/leader geometry.
old_title='<표 1-1> 건설업 공사금액 규모별 업무상사고 사망자 분포(2024년)'
new_title='<표 1-1> 스마트 안전장비 상대효과성 평가의 공통 상위 5개 항목'
pt.s1=original1
hits=[u for u in p.Units(pt.s1,set()).items if '<hp:tab' in u['xml'] and old_title in u['text']]
assert len(hits)==1,'Expected unique old table-list caption'
u=hits[0];r=wrap(u['xml']);ts=list(r.iter(HP+'t'))
# Preserve the tab and page number, which may be children/tails of hp:t.
joined=''.join(t.text or '' for t in ts)
assert old_title in joined
left=len(old_title);started=False
for t in ts:
    val=t.text or ''
    if not started:
        if old_title.startswith(val) and val:
            t.text=new_title;left-=len(val);started=True
    elif left:
        take=min(left,len(val));t.text=val[take:];left-=take
assert started and left==0
clear(r);pt.s1=pt.s1.replace(u['xml'],xml(r[0]),1)
audit.append({'front_caption':[old_title,new_title],'thanks_abstract':'base preserved'})
base_ap=ou.appendix_start()
base_end=next(i for i in range(base_ap,len(ou.items)) if ou.items[i]['text']=='Abstract')
current=p.Units(pt.s2,set());ca=current.appendix_start()
ce=next(i for i in range(ca,len(current.items)) if current.items[i]['text']=='Abstract')
pt.s2=current.head+''.join(u['xml'] for u in current.items[:ca])+''.join(u['xml'] for u in ou.items[base_ap:base_end])+''.join(u['xml'] for u in current.items[ce:])+current.tail
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
