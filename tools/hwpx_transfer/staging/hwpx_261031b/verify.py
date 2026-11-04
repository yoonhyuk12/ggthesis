"""Verify this narrow patch once; XML evidence does not establish page fit."""
from collections import Counter
from pathlib import Path
import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import kjn_profile as k
import patch_from_fresh as p
HP='{'+k.NS['hp']+'}'
HC='{'+k.NS['hc']+'}'
HH='{'+k.NS['hh']+'}'
audit={}

path=OUT/'patched.hwpx'
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    assert z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==zipfile.ZIP_STORED
    raw={n:z.read(n) for n in z.namelist()}
parsed={n:ET.fromstring(v) for n,v in raw.items() if n.endswith(('.xml','.hpf'))}
audit.update(zip_integrity='PASS',xml_parsed=list(parsed),zip_entries=len(raw),
             sha256=hashlib.sha256(path.read_bytes()).hexdigest())
elems=[e for e in parsed['Contents/content.hpf'].iter() if e.tag.endswith('}item')]
items={e.get('id'):e.get('href') for e in elems}
assert len(items)==len(elems)
bins={n:v for n,v in raw.items() if n.startswith('BinData/')}
registered={v for v in items.values() if v.startswith('BinData/')}
assert set(bins)==registered and len(bins)==53
refs=[e.get('binaryItemIDRef') for n,root in parsed.items() if '/section' in n for e in root.iter(HC+'img')]
assert len(refs)==len(set(refs))==53
assert {items[i] for i in refs}==set(bins)
audit['images']=dict(bins=53,registered=53,references=53,unused=0,body_grid_images=12,appendix_grid_images=35,original_figures=6)
base=k.read_package(OUT/'base.hwpx')[1]
fresh=k.read_package(OUT/'assembled.hwpx')[1]
assert all(v==raw[n] for n,v in base.items() if n.startswith('BinData/'))
audit['all_53_base_image_payloads_exact']=True
pngs=[]
for folder in ['본문','부표']:
    d=ROOT/'01.docs/설문결과/자모비캡쳐'/folder
    pngs += [d/c['file'] for group in json.loads((d/'manifest.json').read_text(encoding='utf-8')) for c in group['cells']]
assert len(pngs)==47
expected=Counter(hashlib.sha256(f.read_bytes()).hexdigest() for f in pngs)
actual=Counter(hashlib.sha256(v).hexdigest() for v in bins.values())
assert all(actual[d]==n for d,n in expected.items())
audit['jamovi_png_byte_matches']=47

texts={n:v.decode() for n,v in raw.items() if re.search(r'/section\d+\.xml$',n)}
assert all('pageBreak="CELL"' not in s for s in texts.values())
audit['pageBreak_CELL']=0
current=p.Units(texts['Contents/section2.xml'],set())
baseline=p.Units(base['Contents/section2.xml'].decode(),set())
assembled=p.Units(fresh['Contents/section2.xml'].decode(),set())
assert [p.nows(u['text']) for u in current.items if u['text']]==[p.nows(u['text']) for u in assembled.items if u['text']]
audit['full_section2_text_matches_current_assembly']=True
assert base['Contents/section0.xml']==raw['Contents/section0.xml']

# Survey and appendix 2 remain byte-exact, including all their blank paragraphs.
def part(units,start,end):
    a=next(a for (a,b),u in zip(units.spans,units.items) if u['text'].replace(' ','').startswith(start))
    b=next(a for (a,b),u in zip(units.spans,units.items) if u['text'].replace(' ','').startswith(end))
    return units.xml[a:b]
assert part(current,'부록(도입현장)','부록3.')==part(baseline,'부록(도입현장)','부록3.')
audit['cover_survey_appendix2_exact']=True
main_tables=[u for u in baseline.items[:baseline.appendix_start()] if u['tbl']]
assert all(u['xml'] in current.xml for u in main_tables)
audit['all_main_tables_exact_XML']=len(main_tables)
old_apx_start=next(i for i,u in enumerate(baseline.items) if u['text'].startswith('부록 3.'))
old_grid_xml={u['xml'] for u in baseline.items[old_apx_start:] if u['tbl']}
apx_start=next(i for i,u in enumerate(current.items) if u['text'].startswith('부록 3.'))
assert all(u['xml'] in old_grid_xml for u in current.items[apx_start:] if u['tbl'])
audit['remaining_appendix_grids_exact_XML']=5

# Every unrelated main-body paragraph is exactly retained in sequence.
old_main=baseline.items[:baseline.appendix_start()]
new_main=current.items[:current.appendix_start()]
body_changes=json.loads((OUT/'changes.json').read_text(encoding='utf-8'))
notes={c['old']:c['new'] for c in body_changes if c['kind']=='body_note'}
before=[u['xml'] for u in old_main if u['text'] not in notes]
after=[]
for u in new_main:
    if u['text'] in notes.values() or u['text'].startswith('jamovi 원출력('):continue
    if u['tbl'] and '<hp:pic' in u['xml']:continue
    after.append(u['xml'])
assert before==after
audit['main_paragraphs_exact_except_7_notes_8_insertions']=True
audit['main_exact_paragraphs']=len(before)
for u in new_main:
    if u['text'] in notes.values() or u['text'].startswith('jamovi 원출력(') or (u['tbl'] and '<hp:pic' in u['xml']):
        assert '<hp:linesegarray' not in u['xml']

old_toc=p.Units(base['Contents/section1.xml'].decode(),set())
new_toc=p.Units(texts['Contents/section1.xml'],set())
assert [u['xml'] for u in old_toc.items if not u['text'].startswith('<부표 3-')]==[
    u['xml'] for u in new_toc.items if not u['text'].startswith('<부표 3-')]
def toc_parts(u):
    first,last=u['xml'].split('<hp:tab',1)
    title=p.norm(html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',first))))
    return re.sub(r'^<부표 3-\d+> ','',title),last
old_pages=dict(toc_parts(u) for u in old_toc.items if u['text'].startswith('<부표 3-'))
for u in new_toc.items:
    if u['text'].startswith('<부표 3-'):
        name,page=toc_parts(u)
        assert old_pages[name]==page
audit['section1_unrelated_XML_and_surviving_pages_exact']=True
captions=re.findall(r'^- (<(?:표|부표) \d+-\d+> .+)$',(ROOT/'01.docs/00_목차.md').read_text(encoding='utf-8'),re.M)
assert len(captions)==47
for cap in captions:
    assert p.nows(cap) in p.nows(k.plain_texts(texts['Contents/section1.xml']))
    assert p.nows(cap) in p.nows(k.plain_texts(current.xml))
assert len([u for u in new_toc.items if u['text'].startswith('<부표 3-')])==5
audit['toc_table_captions_match_MD']=47

header=parsed['Contents/header.xml']
ids={kind:{e.get('id') for e in header.iter(HH+kind)} for kind in ['charPr','paraPr','borderFill','style']}
for n,root in parsed.items():
    if '/section' not in n:continue
    for e in root.iter():
        for attr,kind in [('charPrIDRef','charPr'),('paraPrIDRef','paraPr'),('borderFillIDRef','borderFill'),('styleIDRef','style')]:
            if attr in e.attrib:assert e.get(attr) in ids[kind],(n,attr,e.get(attr))
audit['section_style_references']='PASS'
red_ids={e.get('id') for e in header.iter(HH+'charPr') if e.get('textColor','').upper()=='#FF0000'}
marker_count=black_brackets=0
for n,root in parsed.items():
    if '/section' not in n:continue
    for para in root.iter(HP+'p'):
        text='';colors=[]
        for run in para.findall(HP+'run'):
            for t in run.findall(HP+'t'):
                part_text=''.join(t.itertext());text+=part_text
                colors.extend([run.get('charPrIDRef') in red_ids]*len(part_text))
        for m in k.GUIDE_MARKER_RE.finditer(text):
            assert all(colors[m.start():m.end()]),(n,m.group())
            marker_count+=1
        for m in re.finditer(r'\[(?:-?\d|양식 )[^\]]*\]',text):
            assert not any(colors[m.start():m.end()]),(n,m.group())
            black_brackets+=1
audit.update(red_markers_verified=marker_count,black_brackets_verified=black_brackets)

plans=json.loads((OUT/'image_grid_plan.json').read_text(encoding='utf-8'))
grids=[]
for evidence in plans:
    cap=evidence['caption']
    if evidence['unnumbered']:
        heading='jamovi 원출력('+evidence['target']+')'
        ci=next(i for i,u in enumerate(current.items) if u['text'].startswith(heading))
        prev=next(u for u in reversed(current.items[:ci]) if u['text'] or u['tbl'])
        if evidence['target']=='<표 4-11>':assert prev['tbl'] and prev['cap']=='<표4-11>'
        else:assert prev['text'].startswith('주:') and prev['text'].endswith('jamovi 원출력은 표 아래에 함께 제시하였다.')
        label=evidence['target']+' 아래 번호 없는 격자'
    else:
        ci=next(i for i,u in enumerate(current.items) if u['text']==cap)
        label=cap
    unit=current.items[ci+1]
    assert unit['tbl']
    tbl=next(ET.fromstring(k._wrap(unit['xml'])).iter(HP+'tbl'))
    widths=evidence['widths'];total=int(tbl.find(HP+'sz').get('width'))
    assert sum(widths)==total==39684
    if evidence['unnumbered']:
        assert not list(tbl.iter(HP+'linesegarray')) and tbl.get('pageBreak')=='NONE'
    cells=[]
    for ri,tr in enumerate(tbl.findall(HP+'tr')):
        covered=set();row_sum=0
        for tc in tr.findall(HP+'tc'):
            addr,span=tc.find(HP+'cellAddr'),tc.find(HP+'cellSpan')
            col,cs=int(addr.get('colAddr')),int(span.get('colSpan'))
            assert int(addr.get('rowAddr'))==ri and int(span.get('rowSpan'))==1
            occ=set(range(col,col+cs));assert not covered&occ;covered|=occ
            w=int(tc.find(HP+'cellSz').get('width'));row_sum+=w
            assert w==sum(widths[col:col+cs])
            pic=tc.find('.//'+HP+'pic');sz=pic.find(HP+'sz')
            pw,ph=int(sz.get('width')),int(sz.get('height'))
            margin=tc.find(HP+'cellMargin')
            assert pw<=w-int(margin.get('left'))-int(margin.get('right'))
            assert pic.find(HP+'pos').get('treatAsChar')=='1'
            item=pic.find(HC+'img').get('binaryItemIDRef')
            match=next(c for c in evidence['cells'] if c['row']==ri and c['col']==col)
            assert (pw,ph)==(match['picture_width'],match['picture_height'])
            assert bins[items[item]]==(ROOT/match['file']).read_bytes()
            cells.append(dict(row=ri+1,col=col+1,colSpan=cs,width=w,
                image_width_mm=round(pw/283.465,4),image_height_mm=round(ph/283.465,4),file=Path(match['file']).name))
        assert covered==set(range(int(tbl.get('colCnt')))) and row_sum==total
    grids.append(dict(caption=label,body=evidence['unnumbered'],rows=int(tbl.get('rowCnt')),cols=int(tbl.get('colCnt')),
        column_widths=widths,total_width=total,all_row_width_sums=total,pageBreak=tbl.get('pageBreak'),cells=cells))
assert len(grids)==9 and sum(g['body'] for g in grids)==4
audit['grids']=grids
original=ROOT/'00. hwpx/261031_1206_경기공학_건축안전_윤혁_논문.hwpx'
before=(OUT/'base_sha256_before.txt').read_text().strip()
after=hashlib.sha256(original.read_bytes()).hexdigest()
assert before==after==hashlib.sha256((OUT/'base.hwpx').read_bytes()).hexdigest()
audit.update(base_sha256_before=before,base_sha256_after=after)
(OUT/'base_sha256_after.txt').write_text(after,encoding='utf-8')
(OUT/'integrity.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: ZIP/XML/style refs; 53 images, unused 0; body grids 4/12 PNGs, appendix grids 5/35 PNGs; all current MD text; targeted notes and LOT; red/black markers; base SHA256')
print('Main tables retained:',len(main_tables),'appendix grids retained: 5; main exact paragraphs:',len(before) if isinstance(before,list) else audit['main_exact_paragraphs'])
