# -*- coding: utf-8 -*-
"""guide 문단(집필 안내 인용구)이 hwpx에 하나도 안 들어갔는지 확인하고,
--verify-blocks 누락 목록이 guide 문단(과 설문 양식 재구성분)뿐임을 보인다."""
import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import extract_text as X

hwpx = sys.argv[1]
paths = sorted(glob.glob(os.path.join(os.path.dirname(hwpx), "..", "*.blocks.json")))
paths = [p for p in paths if os.path.basename(p) != "front.blocks.json"]
units = X.iter_text_units(hwpx)
hay = " \u241f ".join(X.normalize(t) for _, _, _, t in units)

# 1) guide 문단 텍스트가 문서에 0건인지
guide_texts, present = [], []
for p in paths + [os.path.join(os.path.dirname(hwpx), "..", "front.blocks.json")]:
    for b in json.load(open(p, encoding="utf-8"))["blocks"]:
        if b.get("type") == "p" and b.get("guide"):
            t = X.normalize("".join(r.get("text", "") for r in b.get("runs", [])))
            guide_texts.append((os.path.basename(p), t))
            if t and t in hay:
                present.append((os.path.basename(p), t))
print("guide 문단 %d개 · hwpx 안에 남은 것 %d개" % (len(guide_texts), len(present)))
for f, t in present[:10]:
    print("   [남음] %s: %s" % (f, t[:90]))

# 2) --verify-blocks 누락이 guide + 설문 재구성분뿐인지
exp = X.expected_units(paths)
missing = X.verify(units, exp)
gset = {t for _, t in guide_texts}
absent = [(os.path.basename(p), k, t) for p, k, t in missing if X.normalize(t) not in hay]
guide_absent = [x for x in absent if X.normalize(x[2]) in gset]
other = [x for x in absent if X.normalize(x[2]) not in gset]
print("대조 %d · 순서 기준 누락 %d · 문서에 실제로 없음 %d "
      "(guide %d · 설문 양식 재구성 %d)"
      % (len(exp), len(missing), len(absent), len(guide_absent), len(other)))
for f, k, t in other:
    print("   [설문 재구성] %s %s: %s" % (f, k, t[:80]))
sys.exit(1 if present else 0)
