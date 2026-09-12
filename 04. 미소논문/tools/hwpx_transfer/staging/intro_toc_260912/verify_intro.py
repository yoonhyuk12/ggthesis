"""Read-only candidate validation; stdout JSON, nonzero exit on any mismatch."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

sys.dont_write_bytecode = True
from apply_intro import (DOCS, P, S1, S2, owned, parse, plan, raw, require, sha, spans)

MARKER = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]')


def compressed_record(data, info):
    off = info.header_offset
    name_len, extra_len = struct.unpack_from('<HH', data, off+26)
    return data[off:off+30+name_len+extra_len+info.compress_size]


def red_markers(root, colors):
    result = []
    for p in root.iter(P+'p'):
        text, run_colors = '', []
        for r in p.findall(P+'run'):
            rt = ''.join(''.join(t.itertext()) for t in r.findall(P+'t'))
            text += rt
            run_colors.extend([colors.get(r.get('charPrIDRef'), '')]*len(rt))
        for m in MARKER.finditer(text):
            require(all(c.upper() in ('#FF0000', 'FF0000') for c in run_colors[m.start():m.end()]),
                    'Marker is not entirely red: '+m.group())
            result.append(m.group())
    return Counter(result)


def verify(base, candidate):
    report, replacements, deletions, blocks = plan()
    require(sha(base.read_bytes()) == report['base_sha256'], 'Base differs from reviewed source')
    base_bytes, candidate_bytes = base.read_bytes(), candidate.read_bytes()
    stats = {'status': 'passed', 'checks': [], 'pagination': 'requires coordinator visual inspection'}
    with zipfile.ZipFile(base) as bz, zipfile.ZipFile(candidate) as cz:
        require(bz.namelist() == cz.namelist(), 'ZIP entry order/names changed')
        require(len(set(cz.namelist())) == len(cz.namelist()), 'Duplicate ZIP names')
        require(bz.comment == cz.comment, 'Archive comment changed')
        require(cz.testzip() is None, 'ZIP CRC error')
        fields = ('compress_type','date_time','flag_bits','extra','comment','create_system',
                  'create_version','extract_version','reserved','volume','internal_attr','external_attr')
        for bi, ci in zip(bz.infolist(), cz.infolist()):
            require(all(getattr(bi,k) == getattr(ci,k) for k in fields), 'ZIP metadata changed: '+bi.filename)
            if bi.filename not in (S1,S2):
                require(bz.read(bi) == cz.read(ci), 'Out-of-scope entry changed: '+bi.filename)
                require(compressed_record(base_bytes,bi) == compressed_record(candidate_bytes,ci),
                        'Untouched compressed record changed: '+bi.filename)
        stats['checks'].append('ZIP order, metadata, CRC and all other entries including BinData preserved')
        header = parse(bz.read('Contents/header.xml'))
        colors = {n.get('id'): n.get('textColor','') for n in header.iter()
                  if n.tag.endswith('}charPr')}
        original_ids = {int(v) for name in bz.namelist() if name.endswith('.xml')
                        for v in re.findall(rb'\bid="(\d+)"', bz.read(name))}
        preserved, changed_count = 0, 0
        for section in (S1,S2):
            bd, cd = bz.read(section), cz.read(section)
            br, bt = spans(bd)
            cr, ct = spans(cd)
            boundary = 15 if section == S1 else 73
            target_end = next(i for i,p in enumerate(cr) if owned(p) == '제2장 이론적 배경')
            require(bd[bt[boundary]['start']:] == cd[ct[target_end]['start']:],
                    'Subsequent chapters/TOC suffix XML changed')
            require(bd[:bt[0]['start']] == cd[:ct[0]['start']], 'Section root/prolog changed')
            cursor = 0
            for i, bp in enumerate(br):
                if i in deletions[section]:
                    continue
                require(cursor < len(cr), 'Missing candidate paragraph')
                cp = cr[cursor]
                if i in replacements[section]:
                    require(owned(cp) == replacements[section][i], 'Replacement text mismatch')
                    require(dict(bp.attrib) == dict(cp.attrib), 'Paragraph formatting changed')
                    require([dict(r.attrib) for r in bp.findall(P+'run')] ==
                            [dict(r.attrib) for r in cp.findall(P+'run')], 'Run/font formatting changed')
                    require(cp.find(P+'linesegarray') is None, 'Changed paragraph has stale linesegarray')
                    require(all(n.tag in {P+'p',P+'run',P+'t'} for n in cp.iter()), 'Unexpected modified control')
                    changed_count += 1
                else:
                    require(raw(bd,bt[i]) == raw(cd,ct[cursor]),
                            'Unchanged paragraph XML differs: '+section+' top_idx '+str(i))
                    preserved += 1
                cursor += 1
                if section == S2 and i == 28:
                    new = cr[cursor]
                    require(owned(new) == ' '+blocks[16], 'Inserted contribution text mismatch')
                    require(int(new.get('id')) == max(original_ids)+1, 'New paragraph ID is not fresh')
                    expected_attrs = dict(br[6].attrib)
                    expected_attrs.update(id=new.get('id'), pageBreak='0', columnBreak='0')
                    require(dict(new.attrib) == expected_attrs, 'New paragraph not cloned from body style')
                    require([dict(r.attrib) for r in new.findall(P+'run')] ==
                            [dict(r.attrib) for r in br[6].findall(P+'run')], 'New font style differs')
                    require(all(n.tag in {P+'p',P+'run',P+'t'} for n in new.iter()), 'New paragraph contains control/lineseg')
                    cursor += 1
            require(cursor == len(cr), 'Unexpected extra candidate paragraphs')
            require(red_markers(br,colors) == red_markers(cr,colors), 'Red marker count/text changed')
            if section == S2:
                intro = list(cr)[:target_end]
                visible = [owned(p).strip() for p in intro if owned(p).strip()]
                # Table caption belongs to the table object, not to its root paragraph.
                expected = [b for i,b in enumerate(blocks) if i != 15]
                require(visible == expected, 'MD prose/headings/captions order or content differs')
                for tag, count in [('pic',2),('tbl',1)]:
                    objects = [n for p in intro for n in p.iter(P+tag)]
                    originals = [n for p in list(br)[:73] for n in p.iter(P+tag)]
                    require(len(objects) == len(originals) == count, 'Intro picture/table count differs')
                table = next(n for p in intro for n in p.iter(P+'tbl'))
                table_text = [owned(p).strip() for p in table.iter(P+'p') if owned(p).strip()]
                source = (DOCS/'01.서론.md').read_text(encoding='utf-8')
                cells = [v.strip().replace('`','') for line in source.splitlines()
                         if line.startswith('|') and not re.match(r'^\|[\s:|-]+\|$', line)
                         for v in line.strip('|').split('|')]
                require(table_text == [blocks[15]]+cells or table_text == cells,
                        'Table 1-1 differs from MD cells')
                for i,p in enumerate(intro):
                    if re.match(r'^제\s*\d+\s*[절항]\s',owned(p)):
                        require(i > 0 and not owned(intro[i-1]).strip() and
                                not list(intro[i-1].iter(P+'pic')) and not list(intro[i-1].iter(P+'tbl')),
                                'Missing one blank before section/subsection')
                        require(i < 2 or owned(intro[i-2]).strip(), 'Multiple blanks before heading')
                a = next(i for i,p in enumerate(intro) if owned(p) == blocks[17])
                b = next(i for i,p in enumerate(intro) if owned(p) == blocks[23])
                require([owned(p).strip() for p in intro[a+1:b] if owned(p).strip()] == blocks[18:23],
                        'Purpose must contain exactly five approved paragraphs')
            else:
                toc = [owned(p).strip() for p in list(cr)[2:target_end] if owned(p).strip()]
                require(toc == [blocks[i] for i in (0,1,2,11,17,23)], 'Chapter 1 TOC differs from MD')
        stats.update(preserved_top_paragraphs=preserved, replaced_paragraphs=changed_count,
                     inserted_paragraphs=1, purpose_paragraphs=5)
        stats['checks'].extend(['All unchanged paragraph XML exact, subsequent chapters and appendix exact',
                                'MD prose/headings/table content exact after removing guides/Markdown',
                                'Two pictures and table 1-1 preserved, marker spans entirely red',
                                'Heading blanks and body/font style preserved; modified linesegarray removed'])
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--candidate', required=True, type=Path)
    args = ap.parse_args()
    try:
        result = verify(args.base, args.candidate)
    except Exception as exc:
        print(json.dumps({'status':'failed','error':str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
