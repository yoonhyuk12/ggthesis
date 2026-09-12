"""Read-only pre-COM validation: python validate_intro.py BASE OUT."""
import argparse
from collections import Counter
import html
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from apply_intro import HP, P, elements, fragment, load_plan, owned, paragraphs, patched_sections, require, sha

MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]')
OBJECTS = {'hp:tbl','hp:pic','hp:container','hp:rect','hp:ellipse','hp:arc','hp:polygon',
           'hp:curve','hp:line','hp:connectLine','hp:ole','hp:equation','hp:ctrl','hp:secPr'}

def md_blocks(text):
    text=text.split('## 작성 메모')[0]
    text=re.sub(r'```.*?```','',text,flags=re.S)
    return [html.unescape(re.sub(r'^#+\s*','',b.strip()))
            for b in re.split(r'\n\s*\n',text)
            if b.strip() and not b.strip().startswith('>') and b.strip()!='---']

def marker_associations(z):
    header=ET.fromstring(z.read('Contents/header.xml'))
    colors={n.get('id'):n.get('textColor','').upper() for n in header.iter()
            if n.tag.rsplit('}',1)[-1]=='charPr'}
    result=Counter()
    for name in z.namelist():
        if not re.fullmatch(r'Contents/section\d+\.xml',name):
            continue
        for p in ET.fromstring(z.read(name)).iter(P+'p'):
            text=''; char_colors=[]
            for run in p.findall(P+'run'):
                value=''.join(''.join(t.itertext()) for t in run.findall(P+'t'))
                text+=value;char_colors.extend([colors[run.get('charPrIDRef')]]*len(value))
            for match in MARK.finditer(text):
                result[(name,match.group(),tuple(char_colors[match.start():match.end()]))]+=1
    return result

def object_bytes(data):
    return [fragment(data,n) for n in elements(data) if n['name'] in OBJECTS]

def local_record(blob,info,stop):
    return blob[info.header_offset:stop]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base',type=Path);ap.add_argument('out',type=Path)
    a=ap.parse_args();plan=load_plan()
    base_blob=a.base.read_bytes();out_blob=a.out.read_bytes()
    require(sha(base_blob)==plan['base_sha256'],'Base SHA256 changed')
    # Computing expected XML in memory is read-only; never invokes writer/main.
    expected=patched_sections(a.base,plan)
    md_path=Path(plan['md_path'])
    require(md_path.exists(),'Run validator from repository root so current MD can be verified')
    require(sha(md_path.read_bytes())==plan['md_sha256'],'Current MD changed since plan preparation')
    blocks=md_blocks(md_path.read_text(encoding='utf-8-sig'))
    require(blocks==plan['expected_intro_text'],'MD extraction differs from approved plan')
    with zipfile.ZipFile(a.base) as b,zipfile.ZipFile(a.out) as o:
        require(o.testzip() is None,'ZIP CRC failure')
        require(b.namelist()==o.namelist(),'ZIP entry list/order changed')
        require(b.comment==o.comment,'ZIP comment changed')
        bi=b.infolist();oi=o.infolist()
        metadata=('filename','date_time','compress_type','comment','extra','create_system','create_version',
                  'extract_version','reserved','flag_bits','volume','internal_attr','external_attr')
        for ib,io in zip(bi,oi):
            require(all(getattr(ib,k)==getattr(io,k) for k in metadata),'ZIP metadata changed: '+ib.filename)
            name=ib.filename;before=b.read(name);after=o.read(name)
            if name in expected:
                require(after==expected[name],'Output differs from exact surgical span plan: '+name)
                bp=paragraphs(before);op=paragraphs(after)
                require(len(op)-len(bp)==plan['expected_deltas'][name]['paragraphs'],'Unexpected paragraph delta')
                require(object_bytes(before)==object_bytes(after),'Object/control/table XML changed')
                # All unchanged paragraphs preserve complete bytes, including styles and caches.
                changed_ids={x['idx'] for kind in ('replace','delete') for x in plan[kind] if x['section']==name}
                after_counter=Counter(fragment(after,p) for p in op)
                required_counter=Counter(fragment(before,p) for i,p in enumerate(bp) if i not in changed_ids)
                require(not (required_counter-after_counter),'Untouched paragraph bytes missing')
                old_ids={p['attrs'].get('id') for p in bp}
                new_ids=[p['attrs'].get('id') for p in op if p['attrs'].get('id') not in old_ids]
                require(len(new_ids)==plan['expected_deltas'][name]['insert'] and len(set(new_ids))==len(new_ids),'New IDs not unique')
                new_or_changed={x['new'] for x in plan['replace'] if x['section']==name}|{x['text'] for x in plan['insert_after'] if x['section']==name}
                tree=ET.fromstring(after)
                for tag,counts in plan['expected_deltas'][name]['xml_counts'].items():
                    require(len(list(ET.fromstring(before).iter(P+tag)))==counts['before'], 'Baseline structural count differs')
                    require(len(list(tree.iter(P+tag)))==counts['after'], 'Unexpected structural count: '+tag)
                for p in tree.iter(P+'p'):
                    if p.get('id') in new_ids:
                        require(p.find(P+'linesegarray') is None,'Inserted paragraph has stale linesegarray')
                    if owned(p) in new_or_changed and owned(p):
                        require(p.find(P+'linesegarray') is None,'Changed paragraph has stale linesegarray')
            else:
                require(before==after,'Untouched ZIP entry changed: '+name)
                # Preserve raw compressed records, not merely decompressed content.
                bs=min([x.header_offset for x in bi if x.header_offset>ib.header_offset]+[b.start_dir])
                os=min([x.header_offset for x in oi if x.header_offset>io.header_offset]+[o.start_dir])
                require(local_record(base_blob,ib,bs)==local_record(out_blob,io,os),'Untouched compressed record changed')
        sec='Contents/section2.xml';before=b.read(sec);after=o.read(sec)
        bp=paragraphs(before);op=paragraphs(after)
        shift=plan['expected_deltas'][sec]['paragraphs']
        require(before[bp[61]['start']:]==after[op[61+shift]['start']:],'Chapter2 preceding blank or later XML changed')
        tree=ET.fromstring(after);top=list(tree)
        chapter=next(i for i,p in enumerate(top) if p.tag==P+'p' and owned(p)=='제2장 이론적 배경')
        actual=[owned(p).strip() for p in top[:chapter] if p.tag==P+'p' and owned(p).strip()]
        require(actual==blocks,'Intro nonempty text does not match current MD')
        for i,p in enumerate(top[:chapter]):
            if owned(p) in plan['headings']:
                require(i>=1 and not owned(top[i-1]).strip(),'Heading lacks preceding empty paragraph')
                require(i<2 or bool(owned(top[i-2]).strip()),'Heading has redundant preceding blanks')
                require(all(n.tag in (P+'p',P+'run',P+'t',P+'linesegarray',P+'lineseg') for n in top[i-1].iter()),'Heading blank contains object')
        toc=ET.fromstring(o.read('Contents/section1.xml'))
        texts=[owned(p).strip() for p in toc if p.tag==P+'p']
        first=texts.index('제1장 서론');last=texts.index('제2장 이론적 배경')
        require(texts[first+1:last]==plan['headings'],'TOC intro headings mismatch')
        bm=marker_associations(b);om=marker_associations(o)
        require(bm==om,'Marker text/color association changed')
        intro_markers=[(key,count) for key,count in om.items() if key[0]==sec and key[1] in '\n'.join(blocks)]
        require(all(set(key[2])=={'#FF0000'} for key,count in intro_markers),'Intro marker not fully red')
    print('PASS: pinned base and current MD; exact surgical XML; ZIP metadata/order/compression and untouched raw records;')
    print('intentional paragraph deltas; unchanged chapter2+ bytes and tables/objects/controls; intro/TOC text; heading blanks; marker text/color associations.')
    print('LIMIT: pre-COM candidate only. Coordinator must verify actual Hancom open/reflow/save and rendered layout separately.')

if __name__=='__main__':
    main()
