"""Targeted 1206 patch using Patcher styles/assets; never invoke Hancom."""
from collections import Counter, defaultdict
from pathlib import Path
import difflib
import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
PREV = OUT.with_name('hwpx_261031')
sys.path.insert(0, str(ROOT/'tools/hwpx_transfer'))
import kjn_profile as k
import patch_from_fresh as p

pt = p.Patcher(str(OUT/'base.hwpx'), str(OUT/'assembled.hwpx'), [], None)
base_units = p.Units(pt.s2, set())
fresh_units = p.Units(pt.fresh_s2, set())
previous = p.Units(k.read_package(PREV/'assembled.hwpx')[1]['Contents/section2.xml'].decode(), set())
changes = []

def images(raw):
    root = ET.fromstring(raw['Contents/content.hpf'])
    return {e.get('id'): raw[e.get('href')] for e in root.iter()
            if e.tag.endswith('}item') and e.get('href','').startswith('BinData/')}

# A bijection preserves two different cells even when their PNG bytes coincide.
available = defaultdict(list)
for item, data in images(pt.base_raw).items():
    available[hashlib.sha256(data).digest()].append(item)
for item, data in images(pt.fresh_raw).items():
    pt.bin_id_map[item] = available[hashlib.sha256(data).digest()].pop(0)
assert not any(available.values()) and len(set(pt.bin_id_map.values())) == 53

def meaningful(units):
    return [u for u in units.items[:units.appendix_start()]
            if u['text'] or u['tbl'] or '<hp:pic' in u['xml']]

old, new = meaningful(previous), meaningful(fresh_units)
base_main = base_units.items[:base_units.appendix_start()]
used = set()
def actual(old_unit):
    matches = [(i,u) for i,u in enumerate(base_main)
               if i not in used and p.nows(u['text']) == p.nows(old_unit['text'])
               and u['tbl'] == old_unit['tbl']]
    assert len(matches) == 1, old_unit['text'][:80]
    i,u = matches[0]
    used.add(i)
    return u

sm = difflib.SequenceMatcher(None, [p.nows(u['text']) for u in old],
                            [p.nows(u['text']) for u in new], autojunk=False)
note_count = insert_count = 0
for tag,i,j,x,y in sm.get_opcodes():
    if tag == 'equal':
        continue
    if tag == 'replace':
        assert j-i == 1 and not old[i]['tbl'] and old[i]['text'].startswith('주:')
        assert new[x]['text'].startswith('주:')
        bu = actual(old[i])
        # Only the final jamovi sentence changes. Retain all existing runs/styles.
        old_tail = 'jamovi 원출력은 ' + old[i]['text'].split('jamovi 원출력은 ')[1]
        new_tail = 'jamovi 원출력은 ' + new[x]['text'].split('jamovi 원출력은 ')[1]
        assert old[i]['text'].split('jamovi 원출력은 ')[0] == new[x]['text'].split('jamovi 원출력은 ')[0]
        replacement = p.replace_literal_text(bu['xml'], old_tail, new_tail, 1)
        replacement += ''.join(pt.take_fresh(u['xml']) for u in new[x+1:y])
        assert pt.s2.count(bu['xml']) == 1
        pt.s2 = pt.s2.replace(bu['xml'], replacement, 1)
        changes.append(dict(kind='body_note',old=bu['text'],new=new[x]['text']))
        note_count += 1
        inserts = new[x+1:y]
    else:
        assert tag == 'insert' and y-x == 2 and new[x]['text'].startswith('jamovi 원출력(<표 4-11>)')
        anchor = actual(old[i-1])
        assert anchor['tbl'] and anchor['cap'] == '<표4-11>'
        addition = ''.join(pt.take_fresh(u['xml']) for u in new[x:y])
        pt.s2 = pt.s2.replace(anchor['xml'], anchor['xml'] + addition, 1)
        inserts = new[x:y]
    for u in inserts:
        changes.append(dict(kind='body_insert',table=u['tbl'],text=u['text']))
        insert_count += 1
assert note_count == 7 and insert_count == 8

def apx3(units):
    i = next(i for i,u in enumerate(units.items) if u['text'].startswith('부록 3.'))
    return i, units.items[i:]

bi, base_apx = apx3(base_units)
fi, fresh_apx = apx3(fresh_units)
base_images, fresh_images = images(pt.base_raw), images(pt.fresh_raw)
def signature(u, assets):
    ids = re.findall(r'binaryItemIDRef="([^"]+)"',u['xml'])
    return p.nows(u['text']), tuple(hashlib.sha256(assets[i]).hexdigest() for i in ids)

apx_used, apx_out = set(), []
kept_apx = renamed_apx = new_apx = 0
for fu in fresh_apx:
    candidates = [(i,bu) for i,bu in enumerate(base_apx) if i not in apx_used
                  and signature(bu,base_images)==signature(fu,fresh_images)]
    if candidates:
        i,bu = candidates[0]
        apx_used.add(i)
        apx_out.append(bu['xml'])
        kept_apx += 1
        continue
    cap = re.match(r'^<부표 3-\d+> (.+)$',fu['text'])
    if cap:
        i,bu = next((i,bu) for i,bu in enumerate(base_apx)
                    if i not in apx_used and re.sub(r'^<부표 3-\d+> ', '', bu['text'])==cap.group(1))
        apx_used.add(i)
        old_prefix = re.match(r'<부표 3-\d+>',bu['text']).group()
        new_prefix = re.match(r'<부표 3-\d+>',fu['text']).group()
        apx_out.append(p.replace_literal_text(bu['xml'],old_prefix,new_prefix,1))
        renamed_apx += 1
        changes.append(dict(kind='appendix_caption',old=bu['text'],new=fu['text']))
    else:
        apx_out.append(pt.take_fresh(fu['xml']))
        new_apx += 1
        changes.append(dict(kind='appendix_import',text=fu['text']))
assert sum('<hp:tbl' in s for s in apx_out)==5
now = p.Units(pt.s2,set())
start = next(a for (a,b),u in zip(now.spans,now.items) if u['text'].startswith('부록 3.'))
pt.s2 = pt.s2[:start] + ''.join(apx_out) + now.tail

# Change only appendix-3 LOT titles. Keep the printed page string belonging to
# each surviving logical table, and all other section1 XML verbatim.
toc_units = p.Units(pt.s1,set())
new_caps = [u['text'] for u in fresh_apx if re.match(r'^<부표 3-\d+>',u['text'])]
toc_replaced = toc_deleted = 0
for bu in toc_units.items:
    cap = re.match(r'^<부표 3-\d+>',bu['text'])
    if not cap:
        continue
    prefix = cap.group()
    title = p.norm(html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',bu['xml'].split('<hp:tab',1)[0]))))
    tail = re.sub(r'^<부표 3-\d+> ', '',title)
    target = next((c for c in new_caps if re.sub(r'^<부표 3-\d+> ','',c)==tail),None)
    if target is None:
        pt.s1 = pt.s1.replace(bu['xml'],'',1)
        toc_deleted += 1
        changes.append(dict(kind='toc_delete',text=bu['text']))
    elif target != title:
        new_prefix = re.match(r'<부표 3-\d+>',target).group()
        pt.s1 = pt.s1.replace(bu['xml'],p.replace_literal_text(bu['xml'],prefix,new_prefix,1),1)
        toc_replaced += 1
        changes.append(dict(kind='toc_rename',old=bu['text'],new=bu['text'].replace(prefix,new_prefix,1)))
assert toc_replaced == toc_deleted == 4
assert not pt.bin_imports
base_xmls=Counter(u['xml'] for u in base_units.items)
out_xmls=Counter(u['xml'] for u in p.Units(pt.s2,set()).items)
pt.stats['equal']=sum((base_xmls & out_xmls).values())
pt.stats['table_same_kept']=sum(u['tbl'] and u['xml'] in pt.s2 for u in base_units.items)
pt.stats['section1_exact_kept']=sum(u['xml'] in pt.s1 for u in toc_units.items)
pt.stats.update(replace_fresh=new_apx,insert=insert_count,body_notes_targeted=note_count,
                appendix_exact_kept=kept_apx,appendix_captions_targeted=renamed_apx,
                appendix_retired=len(base_apx)-len(apx_used),toc_titles_targeted=toc_replaced,
                toc_removed=toc_deleted)
pt.log += [json.dumps(c,ensure_ascii=False) for c in changes]
pt.write(str(OUT/'patched.hwpx'))
(OUT/'patch_report.md').write_text(pt.summary(),encoding='utf-8')
(OUT/'patch_stats.json').write_text(json.dumps(pt.stats,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(pt.stats,ensure_ascii=False))
