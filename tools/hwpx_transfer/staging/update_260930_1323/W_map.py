from W_common import *
changed = [(f, i) for f in O for i, (a, b) in enumerate(zip(O[f], N[f])) if a != b]
bynorm = {}
for b in B:
    if b['text'].strip(): bynorm.setdefault(norm(b['text']), []).append((b['section'], b['idx']))
miss = []
for f, i in changed:
    ob = O[f][i]
    if ob['type'] == 'table': continue
    hits = bynorm.get(norm(btext(ob)), [])
    if len(hits) != 1:
        miss.append((f, i, len(hits), btext(ob)[:60]))
print(len(changed)); [print(m) for m in miss]
