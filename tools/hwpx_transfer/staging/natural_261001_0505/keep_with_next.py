"""Main only: clone paraPr of one heading paragraph with keepWithNext=1 (reflowed.hwpx -> layout1.hwpx)."""
import sys, re, zipfile
from pathlib import Path
Q = Path(__file__).resolve().parent
sys.path.insert(0, str(Q.parent/'intro_260912'))
from apply_intro import elements, raw_zip_patch
TITLE = '4. 전달: 알림 전파 즉각성'
src = (Q/'reflowed.hwpx').read_bytes(); z = zipfile.ZipFile(Q/'reflowed.hwpx')
hd = z.read('Contents/header.xml'); sec = z.read('Contents/section2.xml')
ids = [int(x) for x in re.findall(rb'<hh:paraPr id="(\d+)"', hd)]; new = max(ids) + 1
m = re.search(rb'<hh:paraPr id="45".*?</hh:paraPr>', hd, re.S); clone = m.group()
assert clone.count(b'keepWithNext="0"') == 1
clone = clone.replace(b'<hh:paraPr id="45"', b'<hh:paraPr id="%d"' % new, 1).replace(b'keepWithNext="0"', b'keepWithNext="1"')
end = hd.index(b'</hh:paraProperties>'); hd2 = hd[:end] + clone + hd[end:]
cnt = re.search(rb'<hh:paraProperties itemCnt="(\d+)"', hd2); assert int(cnt[1]) == len(ids)
hd2 = hd2.replace(cnt.group(), b'<hh:paraProperties itemCnt="%d"' % (len(ids)+1), 1)
nodes = [n for n in elements(sec) if n['name'] == 'hp:p']; hits = []
for n in nodes:
    part = sec[n['start']:n['end']]
    text = b''.join(re.findall(rb'<hp:t>(.*?)</hp:t>', part)).decode('utf-8')
    if text.strip() == TITLE and b'<hp:tbl' not in part: hits.append(n)
assert len(hits) == 1; n = hits[0]; part = sec[n['start']:n['end']]
head = part[:part.index(b'>')+1]; assert head.count(b'paraPrIDRef="45"') == 1
part = head.replace(b'paraPrIDRef="45"', b'paraPrIDRef="%d"' % new) + part[len(head):]
part = re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>', b'', part, flags=re.S)
sec2 = sec[:n['start']] + part + sec[n['end']:]
(Q/'layout1.hwpx').write_bytes(raw_zip_patch(src, {'Contents/header.xml': hd2, 'Contents/section2.xml': sec2}))
print('new paraPr', new)
