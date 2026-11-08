"""Main-only execution: keep top-level section2 headings with following text."""
from pathlib import Path
import copy, json, re, sys, zipfile
from lxml import etree as E
sys.path.insert(0, 'tools/hwpx_transfer')
import patch_from_fresh as p
import kjn_profile as k
O = Path(__file__).parent
HP = '{' + k.NS['hp'] + '}'
HH = '{' + k.NS['hh'] + '}'
with zipfile.ZipFile(O / 'final.hwpx') as z:
    infos = z.infolist()
    data = {i.filename: z.read(i.filename) for i in infos}
header = E.fromstring(data['Contents/header.xml'])
props = header.find('.//' + HH + 'paraProperties')
cache = {}; audit = []
def clone(old):
    if old in cache: return cache[old]
    el = copy.deepcopy(next(x for x in props if x.get('id') == old))
    new = str(max(int(x.get('id')) for x in props) + 1)
    el.set('id', new)
    bs = el.find(HH + 'breakSetting')
    assert bs is not None
    bs.set('keepWithNext', '1'); bs.set('keepLines', '1')
    props.append(el); props.set('itemCnt', str(len(props)))
    cache[old] = new
    return new
units = p.Units(data['Contents/section2.xml'].decode('utf8'), set())
out = []; following = False; target_seen = False
for u in units.items:
    raw = u['xml']
    el = E.fromstring(k._wrap(raw).encode())[0]
    txt = u['text'].strip()
    heading = bool(re.match(r'^제\s*\d+\s*[절항](?:\s|$)', txt)) and not u['tbl']
    blank = not txt and not u['tbl'] and not any(el.iter(HP + 'pic'))
    if heading or (following and blank):
        old = el.get('paraPrIDRef')
        assert old is not None
        el.set('paraPrIDRef', clone(old))
        for c in list(el.iter(HP + 'linesegarray')): c.getparent().remove(c)
        raw = re.sub(r' xmlns:[^=]+="[^"]*"', '', E.tostring(el, encoding='unicode'))
        audit.append({'text': txt or '[blank]', 'old_paraPr': old, 'new_paraPr': el.get('paraPrIDRef')})
        following = True
        if re.sub(r'\s+', '', txt) == '제4항순찰부담경감문항의근거': target_seen = True
    else:
        following = False
    out.append(raw)
assert target_seen, 'Requested orphan heading not found'
data['Contents/section2.xml'] = (units.head + ''.join(out) + units.tail).encode('utf8')
data['Contents/header.xml'] = E.tostring(header, encoding='UTF-8', xml_declaration=True)
dest = O / 'heading_ready.hwpx'
assert not dest.exists(), 'Refusing overwrite'
with zipfile.ZipFile(dest, 'w') as z:
    for i in infos: z.writestr(i, data[i.filename])
(O / 'keep_headings_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf8')
print('Updated headings and adjacent blanks:', len(audit))
