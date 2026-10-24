import json, sys, io, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:\Users\User\Documents\2026 개발관련\03. 경기대 논문"
CATS = ["M","R","H","P","T","D","L"]
tot = {"items":0,"saved":0,"struct":0}; bycat = {c:0 for c in CATS}
print(f"{'파일':12}{'본문자수':>8}{'건수':>5}{'문장절감':>8}{'문단제안':>8}{'합계':>7}{'비율':>6}  유일성  by_cat")
for f in sorted(glob.glob(os.path.join(D, "*.json"))):
    j = json.load(open(f, encoding="utf-8"))
    txt = open(os.path.join(ROOT, j["file"]), encoding="utf-8").read()
    items = j.get("items", [])
    saved = sum(i.get("saved", 0) for i in items)
    # 실제 재확인: old 유일성·saved 일치
    bad = [i["id"] for i in items if txt.count(i["old"]) != 1]
    badsave = [i["id"] for i in items if i.get("saved") != len(i["old"]) - len(i.get("new", ""))]
    st = sum(s.get("saved_est", 0) for s in j.get("structural", []))
    bc = {c:0 for c in CATS}
    for i in items: bc[i.get("cat","?")] = bc.get(i.get("cat","?"),0) + i.get("saved",0)
    base = j.get("prose_chars_before", 0) or 1
    name = os.path.basename(f)
    print(f"{name:12}{base:8}{len(items):5}{saved:8}{st:8}{saved+st:7}{(saved+st)/base*100:5.1f}%  {'OK' if not bad else 'BAD '+str(bad[:3])}  " + " ".join(f"{c}{v}" for c,v in bc.items() if v))
    if badsave: print("   saved 불일치:", badsave[:5])
    tot["items"] += len(items); tot["saved"] += saved; tot["struct"] += st
    for c in CATS: bycat[c] += bc[c]
print("합계 건수", tot["items"], "문장절감", tot["saved"], "문단제안", tot["struct"], "총", tot["saved"]+tot["struct"], "| by_cat", bycat)
