# 두 hwpx의 본문 문단 텍스트를 섹션 순서대로 대조해 바뀐 문단만 출력한다.
# 용도: 사용자가 한글에서 직접 고친 hwpx(new)를 Claude가 마지막으로 산출한 스냅샷(base)과 비교해
#       MD 역동기화 대상을 찾는다(.claude/rules/hwpx-user-edit-backsync.md). 읽기 전용이며 hwpx를 쓰지 않는다.
# 사용: python tools/hwpx_transfer/hwpx_text_diff.py <base.hwpx> <new.hwpx> [--json out.json]
# 한계: 텍스트만 비교한다(글자모양·표 서식·쪽 나눔 변경은 나오지 않는다 — 그런 변경은 MD 대상이 아니다).
#       표를 품은 바깥 문단은 건너뛰고 셀 문단을 각각 비교하며, 빈 문단은 비교에서 뺀다. 2026-11-05 작성.
import difflib
import html
import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

# 안쪽에 다른 <hp:p>가 없는 문단만 잡는다(표 셀 문단 포함, 표를 품은 바깥 문단 제외)
P_RE = re.compile(r"<hp:p\b(?:(?!<hp:p\b).)*?</hp:p>", re.S)
T_RE = re.compile(r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>", re.S)


def paras(path):
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    out = []
    for n in names:
        x = z.read(n).decode("utf-8")
        sec = n.split("/")[-1][:-4]
        for p in P_RE.findall(x):
            t = "".join(T_RE.findall(p))
            t = html.unescape(re.sub(r"<[^>]+>", "", t))
            # 빈 문단은 뺀다 — 한글 재저장이 셀 말미에 빈 문단을 붙이고(hwpx-output-verification.md),
            # 절·항 앞 빈 줄도 조판 전용이라 MD 역동기화 대상이 아니다
            if t.strip():
                out.append(f"{sec}|{t}")
    return out


def main():
    args = sys.argv[1:]
    js = None
    if "--json" in args:
        i = args.index("--json")
        js = args[i + 1]
        del args[i : i + 2]
    base, new = args
    a, b = paras(base), paras(new)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    blocks = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        blocks.append({"op": op, "base": a[i1:i2], "new": b[j1:j2], "base_idx": [i1, i2], "new_idx": [j1, j2]})
        print(f"== {op} base[{i1}:{i2}] new[{j1}:{j2}]")
        for t in a[i1:i2]:
            print("  -", t)
        for t in b[j1:j2]:
            print("  +", t)
    print(f"changed blocks: {len(blocks)} (base {len(a)} paras, new {len(b)} paras)")
    if js:
        with open(js, "w", encoding="utf-8") as f:
            json.dump(blocks, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
