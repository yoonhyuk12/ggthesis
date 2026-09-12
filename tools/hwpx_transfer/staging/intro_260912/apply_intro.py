"""Coordinator-only surgical HWPX writer: python apply_intro.py BASE OUT.

Only stdlib required. Plan and source hash are pinned; no document reserialization.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import xml.parsers.expat as expat
import xml.etree.ElementTree as ET
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
P = '{' + HP + '}'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def elements(data):
    """Expat lexical byte spans, preorder including nested/self-closing elements."""
    parser = expat.ParserCreate()
    nodes, stack = [], []
    def start(name, attrs):
        pos = parser.CurrentByteIndex
        # Expat has already validated the start tag; locate its closing > quote-aware.
        quote = None
        end = pos
        while end < len(data):
            c = data[end]
            if quote:
                if c == quote:
                    quote = None
            elif c in (34, 39):
                quote = c
            elif c == 62:
                break
            end += 1
        node = dict(name=name, attrs=attrs, start=pos, tag_end=end+1,
                    parent=stack[-1] if stack else None,
                    selfclose=data[pos:end].rstrip().endswith(b'/'))
        nodes.append(node)
        stack.append(node)
    def finish(name):
        node = stack.pop()
        node['end'] = node['tag_end'] if node['selfclose'] else data.index(b'>', parser.CurrentByteIndex)+1
    parser.StartElementHandler, parser.EndElementHandler = start, finish
    parser.Parse(data, True)
    return nodes

def paragraphs(data):
    return [n for n in elements(data) if n['name'] == 'hp:p']

def owned(p):
    return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))

def fragment(data, node):
    return data[node['start']:node['end']]

def plain_edit(raw, text, new_id=None):
    """Only verified plain one-run paragraphs; retain attrs and exact run start tag."""
    ns = elements(raw)
    require(all(n['name'] in ('hp:p','hp:run','hp:t','hp:linesegarray','hp:lineseg') for n in ns), 'Cannot edit paragraph containing controls/objects')
    runs = [n for n in ns if n['name']=='hp:run']
    require(len(runs)==1, 'Mixed-style paragraph cannot be replaced')
    opening = raw[:ns[0]['tag_end']]
    if new_id is not None:
        opening = re.sub(rb'\bid="[^"]*"', b'id="'+str(new_id).encode()+b'"', opening, count=1)
        opening = re.sub(rb'\b(pageBreak|columnBreak)="[^"]*"', rb'\1="0"', opening)
    run = runs[0]
    ropen = raw[run['start']:run['tag_end']]
    if ropen.endswith(b'/>'):
        ropen = ropen[:-2]+b'>'
    return opening+ropen+b'<hp:t>'+html.escape(text, quote=False).encode('utf-8')+b'</hp:t></hp:run></hp:p>'

def load_plan():
    return json.loads((HERE/'transfer_plan.json').read_text(encoding='utf-8'))

def patched_sections(base, plan):
    require(sha(base.read_bytes())==plan['base_sha256'], 'Base hash differs from approved source')
    result = {}
    with zipfile.ZipFile(base) as z:
        ids = set()
        for name in z.namelist():
            if name.endswith('.xml'):
                ids.update(int(v) for v in re.findall(rb'\bid="(\d+)"', z.read(name)))
        fresh = max(ids)+1
        require(fresh+len(plan['insert_after']) < 2**32, 'ID space exhausted')
        for section in plan['expected_deltas']:
            data = z.read(section)
            paras = paragraphs(data)
            tree = ET.fromstring(data)
            ep = list(tree.iter(P+'p'))
            edits = []
            for kind in ('replace','delete'):
                for change in plan[kind]:
                    if change['section'] != section:
                        continue
                    idx=change['idx']; node=paras[idx]
                    require(node['parent']['name']=='hs:sec', 'Target is not a root paragraph')
                    require(owned(ep[idx])==change['old_hwpx'], 'Old text mismatch at '+str(idx))
                    raw=fragment(data,node)
                    if kind=='delete':
                        plain_edit(raw,'')  # Reject any hidden object/control or mixed styling.
                        replacement=b''
                    else:
                        replacement=plain_edit(raw,change['new'])
                    edits.append((node['start'],node['end'],replacement))
            inserts = {}
            for change in plan['insert_after']:
                if change['section']!=section:
                    continue
                node=paras[change['idx']]
                require(node['parent']['name']=='hs:sec','Insertion anchor is nested')
                raw=fragment(data,paras[change['template_idx']])
                inserts.setdefault(node['end'],b'')
                inserts[node['end']]+=plain_edit(raw,change['text'],fresh)
                fresh+=1
            edits.extend((pos,pos,value) for pos,value in inserts.items())
            edits.sort(key=lambda x:(x[0],x[1]))
            cursor=0; chunks=[]
            for start,end,value in edits:
                require(start>=cursor,'Overlapping surgical edits')
                chunks.extend((data[cursor:start],value)); cursor=end
            chunks.append(data[cursor:]); result[section]=b''.join(chunks)
            ET.fromstring(result[section])
    return result

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

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base',type=Path); parser.add_argument('out',type=Path)
    args=parser.parse_args()
    require(args.base.resolve()!=args.out.resolve(),'Never overwrite base')
    require(not args.out.exists(),'Output already exists; choose a fresh path')
    plan=load_plan(); changed=patched_sections(args.base,plan)
    result=raw_zip_patch(args.base.read_bytes(),changed)
    with args.out.open('xb') as f:
        f.write(result)
    print('WROTE surgical candidate; coordinator must validate and run COM:',args.out)

if __name__=='__main__':
    main()
