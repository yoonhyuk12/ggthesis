"""Pinned, surgical intro transfer. Only the coordinator should execute this file."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib
from lxml import etree

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[3] / '01.docs'
HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
P = '{' + HP + '}'
S1, S2 = 'Contents/section1.xml', 'Contents/section2.xml'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    return etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))


def owned(p):
    return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))


def spans(data):
    """Lexical hp:p spans without reserializing XML; validate with lxml first."""
    root = parse(data)
    require(root.prefix == 'hs', 'Unexpected section namespace prefix')
    require(b'<!DOCTYPE' not in data and b'<![CDATA[' not in data, 'Unsupported lexical XML')
    stack, result = [], []
    token = rb'<!--.*?-->|<\?.*?\?>|</?(?:[^>"\']|"[^"]*"|\'[^\']*\')+>'
    for m in re.finditer(token, data, re.S):
        tag = m.group()
        if tag.startswith((b'<!--', b'<?')):
            continue
        if tag.startswith(b'</'):
            node = stack.pop()
            node['end'] = m.end()
        else:
            name = re.match(rb'<([^\s/>]+)', tag)[1]
            node = {'name': name, 'start': m.start(), 'end': m.end(),
                    'tag_end': m.end(), 'parent': stack[-1]['name'] if stack else None}
            if name == b'hp:p':
                result.append(node)
            if not tag.rstrip().endswith(b'/>'):
                stack.append(node)
    require(not stack, 'Unbalanced XML spans')
    require(len(result) == len(list(root.iter(P+'p'))), 'Paragraph span mismatch')
    top = [n for n in result if n['parent'] == b'hs:sec']
    require(len(top) == len(root), 'Non-paragraph section child')
    return root, top


def raw(data, span):
    return data[span['start']:span['end']]


def plain_edit(value, text, new_id=None):
    """Keep paragraph/run attributes; reject objects and mixed-character styles."""
    tags = re.findall(rb'</?([\w:]+)', value)
    require(set(tags) <= {b'hp:p', b'hp:run', b'hp:t', b'hp:linesegarray', b'hp:lineseg'},
            'Cannot edit controls, markers, or objects')
    runs = re.findall(rb'<hp:run\b[^>]*>', value)
    require(len(runs) == 1, 'Mixed runs must remain unchanged')
    opening = value[:value.index(b'>')+1]
    if new_id is not None:
        opening = re.sub(rb'\bid="[^"]*"', b'id="'+str(new_id).encode()+b'"', opening, count=1)
        opening = re.sub(rb'\b(pageBreak|columnBreak)="[^"]*"', rb'\1="0"', opening)
    ropen = runs[0]
    if ropen.endswith(b'/>'):
        ropen = ropen[:-2]+b'>'
    return opening+ropen+b'<hp:t>'+html.escape(text, quote=False).encode()+b'</hp:t></hp:run></hp:p>'


def manuscripts():
    intro = (DOCS/'01.서론.md').read_text(encoding='utf-8')
    blocks = [re.sub(r'^#{1,6}\s+', '', b).replace('`', '').strip()
              for b in intro.split('\n\n') if b.strip() and not b.startswith(('>', '!', '|'))]
    toc = (DOCS/'00.목차.md').read_text(encoding='utf-8')
    part = toc.split('- 제1장 서론\n', 1)[1].split('- 제2장 ', 1)[0]
    headings = ['제1장 서론']+[line.strip()[2:] for line in part.splitlines() if line.strip()]
    require(len(blocks) == 39 and len(headings) == 6, 'MD structure changed; re-audit required')
    require([re.sub(r'^#{1,6}\s+', '', line).strip() for line in intro.splitlines()
             if line.startswith('#')] == headings,
            'Intro and TOC headings disagree')
    return blocks, headings


def plan():
    report = json.loads((HERE/'intro_report.json').read_text(encoding='utf-8'))
    require(sha((DOCS/'01.서론.md').read_bytes()) == report['md_sha256'], 'Intro changed; re-audit')
    require(sha((DOCS/'00.목차.md').read_bytes()) == report['toc_sha256'], 'TOC changed; re-audit')
    require(not report['user_unique_edits']['unexplained'], 'Unresolved user-specific edits')
    blocks, headings = manuscripts()
    replacements = {
        S1: {4: '  '+headings[2], 5: '  '+headings[3], 8: ' '+headings[4]},
        S2: {int(t): ('' if b in (2,11,17) else ' ')+blocks[b]
             for t,b in report['replace_top_to_md_block'].items()}}
    deletions = {S1: {6,7,9,10,11,12,14}, S2: set(report['delete_top'])}
    return report, replacements, deletions, blocks


def patched_sections(base):
    report, replacements, deletions, blocks = plan()
    require(sha(base.read_bytes()) == report['base_sha256'], 'Base differs; preserve manual edits and re-audit')
    changed = {}
    with zipfile.ZipFile(base) as z:
        ids = {int(v) for name in z.namelist() if name.endswith('.xml')
               for v in re.findall(rb'\bid="(\d+)"', z.read(name))}
        fresh = max(ids)+1
        require(fresh < 2**32, 'ID space exhausted')
        for section in (S1, S2):
            data = z.read(section)
            root, top = spans(data)
            require(owned(root[15 if section == S1 else 73]) == '제2장 이론적 배경', 'Scope boundary changed')
            edits = []
            for i, text in replacements[section].items():
                require(owned(root[i]).strip() != text.strip(), 'Unnecessary replacement')
                edits.append((top[i]['start'], top[i]['end'], plain_edit(raw(data, top[i]), text)))
            for i in deletions[section]:
                plain_edit(raw(data, top[i]), '')  # refuses hidden objects/mixed runs
                edits.append((top[i]['start'], top[i]['end'], b''))
            if section == S2:
                pos = top[28]['end']
                edits.append((pos, pos, plain_edit(raw(data, top[6]), ' '+blocks[16], fresh)))
            cursor, chunks = 0, []
            for start, end, value in sorted(edits):
                require(start >= cursor, 'Overlapping edits')
                chunks.extend((data[cursor:start], value))
                cursor = end
            chunks.append(data[cursor:])
            changed[section] = b''.join(chunks)
            parse(changed[section])
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(args.input.resolve() != args.output.resolve(), 'Never overwrite source')
    require(not args.output.exists(), 'Output exists; select a fresh path')
    changed = patched_sections(args.input)
    result = raw_zip_patch(args.input.read_bytes(), changed)
    with args.output.open('xb') as f:
        f.write(result)
    print(json.dumps({'candidate': str(args.output), 'changed_entries': list(changed),
                      'next': 'Run verify_intro.py, then coordinator visual pagination check'}, ensure_ascii=False))


# raw_zip_patch is included below; unchanged ZIP records stay byte-identical.

def raw_zip_patch(original, changed):
    """Retain untouched compressed local records and all ZIP metadata bytes.

    Only CRC/sizes/offset fields change. Reject ZIP64, encryption and descriptors.
    """
    eocd=original.rfind(b'PK\x05\x06')
    require(eocd>=0,'No EOCD')
    end=bytearray(original[eocd:])
    disk,cd_disk,n_disk,n,cd_size,cd_start,comment=struct.unpack_from('<4H2IH',end,4)
    require(disk==cd_disk==0 and n_disk==n and n<65535,'Unsupported split/ZIP64 archive')
    require(len(end)==22+comment and cd_start+cd_size==eocd,'Unsupported ZIP trailer')
    central=[]; cursor=cd_start
    for _ in range(n):
        require(original[cursor:cursor+4]==b'PK\x01\x02','Invalid central record')
        nl,xl,cl=struct.unpack_from('<3H',original,cursor+28)
        rec=bytearray(original[cursor:cursor+46+nl+xl+cl]);cursor+=len(rec)
        flags,method=struct.unpack_from('<2H',rec,8)
        require(flags & 9 == 0 and method in (0,8),'Unsupported flags/compression')
        name=bytes(rec[46:46+nl]).decode('utf-8' if flags&2048 else 'cp437')
        offset=struct.unpack_from('<I',rec,42)[0]
        central.append((offset,name,rec,method))
    require(cursor==eocd,'Unexpected central records')
    ordered=sorted(central,key=lambda row:row[0]); output=bytearray(original[:ordered[0][0]])
    for i,(offset,name,rec,method) in enumerate(ordered):
        stop=ordered[i+1][0] if i+1<len(ordered) else cd_start
        local=bytearray(original[offset:stop]); new_offset=len(output)
        require(local[:4]==b'PK\x03\x04','Invalid local record')
        if name in changed:
            nl,xl=struct.unpack_from('<2H',local,26); payload_start=30+nl+xl
            old_size=struct.unpack_from('<I',local,18)[0]
            value=changed[name]
            if method==8:
                compressor=zlib.compressobj(6,zlib.DEFLATED,-15)
                payload=compressor.compress(value)+compressor.flush()
            else:
                payload=value
            crc=zlib.crc32(value)&0xffffffff
            struct.pack_into('<3I',local,14,crc,len(payload),len(value))
            struct.pack_into('<3I',rec,16,crc,len(payload),len(value))
            local=local[:payload_start]+payload+local[payload_start+old_size:]
        struct.pack_into('<I',rec,42,new_offset)
        output.extend(local)
    new_cd=len(output)
    for _,_,rec,_ in central:
        output.extend(rec)
    struct.pack_into('<2I',end,12,len(output)-new_cd,new_cd)
    output.extend(end)
    return bytes(output)


if __name__ == '__main__':
    main()
