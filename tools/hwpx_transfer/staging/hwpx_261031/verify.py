"""Structural/contents verification only; deliberately never invokes Hancom."""
from collections import Counter
from pathlib import Path
import hashlib
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
    raw={n:z.read(n) for n in z.namelist()}
    assert z.infolist()[0].filename=='mimetype'
    assert z.infolist()[0].compress_type==zipfile.ZIP_STORED
    parsed={n:ET.fromstring(v) for n,v in raw.items() if n.endswith(('.xml','.hpf'))}
    audit['zip_integrity']='PASS'
    audit['xml_parsed']=list(parsed)
    audit['zip_entries']=len(raw)
    audit['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
manifest=parsed['Contents/content.hpf']
item_elems=[e for e in manifest.iter() if e.tag.endswith('}item')]
items={e.get('id'):e.get('href') for e in item_elems}
assert len(items)==len(item_elems)
bins={n:v for n,v in raw.items() if n.startswith('BinData/')}
registered={v for v in items.values() if v.startswith('BinData/')}
assert set(bins)==registered
assert len(bins)==53
refs=[]
for n,root in parsed.items():
    if '/section' in n:
        refs.extend(e.get('binaryItemIDRef') for e in root.iter(HC+'img'))
assert all(i in items and items[i] in bins for i in refs)
assert len(refs)==53
audit['images']={'bins':len(bins),'registered':len(registered),'references':len(refs)}
base=k.read_package(OUT/'base.hwpx')[1]
fresh=k.read_package(OUT/'assembled.hwpx')[1]
audit['original_base_images']=sum(n.startswith('BinData/') for n in base)
# Every original jamovi PNG appears once, byte-for-byte, in the package.
expected_pngs=list((ROOT/'01.docs/설문결과/자모비캡쳐/부표').glob('부표3-*.png'))
assert len(expected_pngs)==47
bin_hashes=Counter(hashlib.sha256(v).hexdigest() for v in bins.values())
expected_hashes=Counter(hashlib.sha256(f.read_bytes()).hexdigest() for f in expected_pngs)
assert all(bin_hashes[digest]==count for digest,count in expected_hashes.items())
audit['jamovi_unchanged_pngs']=47
audit['existing_images']={n:('unchanged' if v==raw[n] else 'updated from current MD image source')
                          for n,v in base.items() if n.startswith('BinData/')}
current_model=(ROOT/'01.docs/figures/research/figure_4-1_research_model_261029.png').read_bytes()
assert raw['BinData/image6.png']==current_model

texts={n:v.decode('utf-8') for n,v in raw.items() if '/section' in n and n.endswith('.xml')}
assert all('pageBreak="CELL"' not in s for s in texts.values())
audit['pageBreak_CELL']=0
current_units=p.Units(texts['Contents/section2.xml'],set())
fresh_units=p.Units(fresh['Contents/section2.xml'].decode('utf-8'),set())
base_units=p.Units(base['Contents/section2.xml'].decode('utf-8'),set())
def nonempty(units,stop):
    return [p.nows(u['text']) for u in units.items[:stop] if u['text']]
assert nonempty(current_units,current_units.appendix_start())==nonempty(fresh_units,fresh_units.appendix_start())
audit['main_body_and_references_match_current_assembly']=True
audit['main_body_nonempty_units']=len(nonempty(current_units,current_units.appendix_start()))
def tail_from(units,title):
    start=next(i for i,u in enumerate(units.items) if u['text'].startswith(title))
    return [p.nows(u['text']) for u in units.items[start:] if u['text']]
assert tail_from(current_units,'부록 2.')==tail_from(fresh_units,'부록 2.')
audit['new_appendices_text_matches_current_MD']=True
# Survey original formatting is changed only by the documented literal targets.
start=base_units.spans[base_units.appendix_start()][0]
expected_survey=base_units.xml[start:base_units.xml.rfind('</hs:sec>')]
targets=json.loads((OUT/'survey_targets.json').read_text(encoding='utf-8'))
for t in targets:
    expected_survey=p.replace_literal_text(expected_survey,t['old'],t['new'],t['count'])
cstart=current_units.spans[current_units.appendix_start()][0]
cend=next(a for (a,b),u in zip(current_units.spans,current_units.items) if u['text'].startswith('부록 2.'))
assert texts['Contents/section2.xml'][cstart:cend]==expected_survey
audit['survey_exact_target_only_preservation']=True
audit['survey_replacement_occurrences']=sum(t['count'] for t in targets)
assert '중소규모 건설현장을 위한 YOLO-LLM' not in texts['Contents/section0.xml']
assert not re.search(r'현장소장(?!\(관리감독자\))',k.plain_texts(texts['Contents/section2.xml']))
audit['cover_and_role_targets']='PASS'

front=(ROOT/'01.docs/00_목차.md').read_text(encoding='utf-8')
captions=re.findall(r'^- (<(?:표|부표) \d+-\d+> .+)$',front,re.M)
front_text=p.nows(k.plain_texts(texts['Contents/section1.xml']))
body_text=p.nows(k.plain_texts(texts['Contents/section2.xml']))
assert len(captions)==51
for caption in captions:
    assert p.nows(caption) in front_text,caption
    assert p.nows(caption) in body_text,caption
assert '부록2.실증분석상세결과' in front_text and '부록3.jamovi분석원출력' in front_text
audit['toc_table_captions_match_00_MD']=51

header=parsed['Contents/header.xml']
style_ids={kind:{e.get('id') for e in header.iter(HH+kind)}
           for kind in ['charPr','paraPr','borderFill','style','tabPr']}
for name,root in parsed.items():
    if '/section' not in name:continue
    for e in root.iter():
        for attr,kind in [('charPrIDRef','charPr'),('paraPrIDRef','paraPr'),('borderFillIDRef','borderFill'),('styleIDRef','style')]:
            if attr in e.attrib:assert e.get(attr) in style_ids[kind],(name,attr,e.get(attr))
audit['section_style_references']='PASS'

red_ids={e.get('id') for e in header.iter(HH+'charPr') if e.get('textColor','').upper()=='#FF0000'}
marker_count=0
black_brackets=0
for name,root in parsed.items():
    if '/section' not in name:continue
    for para in root.iter(HP+'p'):
        text='';colors=[]
        for run in para.findall(HP+'run'):
            for t in run.findall(HP+'t'):
                part=''.join(t.itertext())
                text+=part
                colors.extend([run.get('charPrIDRef') in red_ids]*len(part))
        for m in k.GUIDE_MARKER_RE.finditer(text):
            assert all(colors[m.start():m.end()]),(name,m.group())
            marker_count+=1
        for m in re.finditer(r'\[(?:-?\d|양식 )[^\]]*\]',text):
            assert not any(colors[m.start():m.end()]),(name,m.group())
            black_brackets+=1
audit['red_markers_verified']=marker_count
audit['black_numeric_or_form_brackets_verified']=black_brackets

plan=json.loads((OUT/'image_grid_plan.json').read_text(encoding='utf-8'))
grid_audit=[]
for evidence in plan:
    cap=evidence['caption']
    ci=next(i for i,u in enumerate(current_units.items) if u['text']==cap)
    unit=current_units.items[ci+1]
    assert unit['tbl']
    table=next(ET.fromstring(k._wrap(unit['xml'])).iter(HP+'tbl'))
    widths=evidence['widths'];total=int(table.find(HP+'sz').get('width'))
    assert total==sum(widths)==39684
    assert not list(table.iter(HP+'linesegarray'))
    cells=[]
    for ri,tr in enumerate(table.findall(HP+'tr')):
        covered=set();row_sum=0
        for tc in tr.findall(HP+'tc'):
            addr,span=tc.find(HP+'cellAddr'),tc.find(HP+'cellSpan')
            col,cs=int(addr.get('colAddr')),int(span.get('colSpan'))
            assert int(addr.get('rowAddr'))==ri and int(span.get('rowSpan'))==1
            occ=set(range(col,col+cs));assert not covered&occ;covered|=occ
            w=int(tc.find(HP+'cellSz').get('width'))
            assert w==sum(widths[col:col+cs]);row_sum+=w
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
                              image_width_mm=round(pw/283.465,4),image_height_mm=round(ph/283.465,4),
                              file=Path(match['file']).name))
        assert covered==set(range(int(table.get('colCnt'))))
        assert row_sum==total
    grid_audit.append(dict(caption=cap,rows=int(table.get('rowCnt')),cols=int(table.get('colCnt')),
                           column_widths=widths,total_width=total,pageBreak=table.get('pageBreak'),
                           all_row_width_sums=total,cells=cells))
audit['appendix3_grids']=grid_audit
base_table_xmls={u['xml'] for u in base_units.items[:base_units.appendix_start()] if u['tbl']}
audit['unchanged_main_tables_exact_XML']=sum(u['tbl'] and u['xml'] in base_table_xmls for u in current_units.items)
assert audit['unchanged_main_tables_exact_XML']==14
original=ROOT/'00. hwpx/261028_0757_경기공학_건축안전_윤혁_논문.hwpx'
before=(OUT/'base_sha256_before.txt').read_text().strip()
after=hashlib.sha256(original.read_bytes()).hexdigest()
assert before==after==hashlib.sha256((OUT/'base.hwpx').read_bytes()).hexdigest()
audit['base_sha256_before']=before;audit['base_sha256_after']=after
(OUT/'base_sha256_after.txt').write_text(after,encoding='utf-8')
(OUT/'integrity.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: ZIP/XML/style refs; 53 image payloads/manifest refs; 47 unchanged jamovi PNGs; 9 grids; current MD text/TOC; red/black markers; original SHA256')
print('markers',marker_count,'black brackets',black_brackets,'tables preserved',audit['unchanged_main_tables_exact_XML'])
