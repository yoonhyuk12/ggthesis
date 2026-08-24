# MD 항목 스트림과 hwpx 추출 스트림을 순서대로 정렬 대조해 누락·변형·추가를 찾는다 (T5b 전용)
"""t5b_compare.py — MD 기준 항목 스트림 vs hwpx section2 항목 스트림 정렬 대조.

difflib.SequenceMatcher로 정규화 텍스트 시퀀스를 정렬하고, 불일치 구간을
(누락 delete / 추가 insert / 변형 replace)으로 분류해 출력한다.
"""

import difflib
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

NBSP = " "
EMSP = " "
FULLWIDTH_SP = "　"


def norm(s):
    s = s.replace(NBSP, " ").replace(EMSP, " ").replace(FULLWIDTH_SP, " ")
    s = s.replace("&emsp;", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def md_stream(items):
    out = []
    for it in items:
        if it["kind"] == "table":
            for row in it["rows"]:
                for cell in row:
                    for line in cell.split("<br>"):
                        if norm(line):
                            out.append(("cell", norm(line), line, it["line"]))
        else:
            if norm(it["text"]):
                out.append((it["kind"], norm(it["text"]), it["text"], it["line"]))
    return out


def hwpx_stream(items, base=0):
    out = []
    for k, it in enumerate(items):
        if it["kind"] == "table":
            for row in it["rows"]:
                for cell in row:
                    for line in cell.split("\n"):
                        if norm(line):
                            out.append(("cell", norm(line), line, base + k))
        else:
            if norm(it["text"]):
                out.append(("para", norm(it["text"]), it["text"], base + k))
    return out


def report(name, md, hw):
    a = [x[1] for x in md]
    b = [x[1] for x in hw]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        diffs.append((tag, md[i1:i2], hw[j1:j2]))
    print("### %s — MD 텍스트단위 %d, hwpx 텍스트단위 %d, 불일치 구간 %d"
          % (name, len(a), len(b), len(diffs)))
    for tag, m, h in diffs:
        print("  [%s]" % tag)
        for x in m:
            print("     MD (%s, L%s): %s" % (x[0], x[3], x[2][:300]))
        for x in h:
            print("     HWPX(idx %s)   : %s" % (x[3], x[2][:300]))
    print()
    return diffs


if __name__ == "__main__":
    mdj = json.load(open(sys.argv[1], encoding="utf-8"))
    hwj = json.load(open(sys.argv[2], encoding="utf-8"))
    ranges = json.load(open(sys.argv[3], encoding="utf-8"))
    sec = hwj["section2"]
    total = 0
    for name, (mdkey, lo, hi) in ranges.items():
        total += len(report(name, md_stream(mdj[mdkey]), hwpx_stream(sec[lo:hi], lo)))
    print("총 불일치 구간: %d" % total)
