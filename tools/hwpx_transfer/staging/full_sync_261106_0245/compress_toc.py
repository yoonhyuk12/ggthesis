"""Targeted layout adjustment. Main agent executes after reviewing this helper."""
from pathlib import Path
import copy, json, re, sys, zipfile
from lxml import etree as E
sys.path.insert(0, 'tools/hwpx_transfer')
import kjn_profile as k
O = Path(__file__).parent
HP = '{' + k.NS['hp'] + '}'
HH = '{' + k.NS['hh'] + '}'
TARGETS = {
    '제1항YOLO-LLM안전관제시스템도입현장의안전관리실효성검증',
    '<표2-2>시스템기능–담당자업무–안전관리실효성측정문항연결',
}
def norm(s): return re.sub(r'\s+', '', s)
def clean(el):
    for c in list(el.iter(HP + 'linesegarray')): c.getparent().remove(c)
def inner(el):
    return re.sub(r' xmlns:[^=]+="[^"]*"', '', E.tostring(el, encoding='unicode'))
def parsed(s): return E.fromstring(k._wrap(s).encode())[0]
PAT = re.compile(r'<hp:p\b[^>]*>(?:(?!<hp:p\b).)*?</hp:p>', re.S)
with zipfile.ZipFile(O / 'toc_patched.hwpx') as z:
    infos = z.infolist()
    data = {i.filename: z.read(i.filename) for i in infos}
header = E.fromstring(data['Contents/header.xml'])
chars = header.find('.//' + HH + 'charProperties')
paras = header.find('.//' + HH + 'paraProperties')
assert chars is not None and paras is not None
audit = []; charcache = {}; paracache = {}
def clone(props, old, cache, kind):
    if old in cache: return cache[old]
    el = copy.deepcopy(next(x for x in props if x.get('id') == old))
    new = str(max(int(x.get('id')) for x in props) + 1)
    el.set('id', new)
    if kind == 'char':
        for name, value in [('ratio', '75'), ('spacing', '-4')]:
            child = el.find(HH + name)
            assert child is not None
            for key in child.attrib: child.set(key, value)
    else:
        child = el.find(HH + 'breakSetting')
        child.set('keepWithNext', '1'); child.set('keepLines', '1')
    props.append(el); props.set('itemCnt', str(len(props)))
    cache[old] = new
    return new
hits = set()
def toc(m):
    raw = m.group(); el = parsed(raw)
    before = []
    for n in el.iter():
        if n.tag == HP + 'tab': break
        if n.tag == HP + 't' and n.text: before.append(n.text)
    label = norm(''.join(before))
    if label not in TARGETS: return raw
    assert label not in hits
    hits.add(label)
    for run in el.iter(HP + 'run'):
        run.set('charPrIDRef', clone(chars, run.get('charPrIDRef'), charcache, 'char'))
    clean(el); audit.append({'toc': ''.join(before).strip(), 'ratio': 75, 'spacing': -4})
    return inner(el)
s1 = PAT.sub(toc, data['Contents/section1.xml'].decode('utf8'))
assert hits == TARGETS, (hits, TARGETS)
heading_found = False
join_blanks = False
def body(m):
    global heading_found, join_blanks
    raw = m.group(); el = parsed(raw)
    txt = ''.join(''.join(t.itertext()) for t in el.iter(HP + 't')).strip()
    target = txt == '국내·외 선행연구'
    blank = not txt and not any(el.iter(HP + 'tbl')) and not any(el.iter(HP + 'pic'))
    if target:
        assert not heading_found
        heading_found = True; join_blanks = True
    elif not (join_blanks and blank):
        join_blanks = False
        return raw
    el.set('paraPrIDRef', clone(paras, el.get('paraPrIDRef'), paracache, 'para'))
    clean(el); audit.append({'keep_with_next': txt or '[blank]'})
    return inner(el)
s2 = PAT.sub(body, data['Contents/section2.xml'].decode('utf8'))
assert heading_found
data['Contents/section1.xml'] = s1.encode('utf8')
data['Contents/section2.xml'] = s2.encode('utf8')
data['Contents/header.xml'] = E.tostring(header, encoding='UTF-8', xml_declaration=True)
out = O / 'toc_ready.hwpx'
assert not out.exists(), 'Refusing to overwrite existing output'
with zipfile.ZipFile(out, 'w') as z:
    for i in infos: z.writestr(i, data[i.filename])
(O / 'compress_toc_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(audit, ensure_ascii=False, indent=2))
