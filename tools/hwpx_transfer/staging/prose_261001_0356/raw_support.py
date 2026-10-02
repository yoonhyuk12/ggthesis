import hashlib, struct, zlib
import xml.parsers.expat as expat

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
