# -*- coding: utf-8 -*-
"""감축 전후 보존 항목 대조. 기준은 git HEAD 판본(감축 직전 커밋)이다.

  python tools/manuscript_trim/verify_trim.py 01.docs/05_실증분석결과.md [더 많은 파일…]

대조 항목: 마커 5종 건수, 인용 연도 표기 건수, <표>·<그림> 참조 집합, 금지 표현, 줄끝 일관성, 글자 수 변화.
마커·표/그림 집합이 달라지면 FAIL(의도한 변경이면 보고에 사유를 적는다). 인용 건수 감소는 WARN.
"""
import re, subprocess, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
MARKERS = ["[DATA PENDING", "[확정 필요", "[CITE_TODO", "[UNVERIFIED", "[그림 삽입 예정"]
BANNED = ["도입 이후 향상", "개선시켰", "감소시켰", "효과가 있었", "보여진다", "해석되어진다", "jamovi", "명부 대조 전", "시험 응답", "73건"]
CITE = re.compile(r"(?:19|20)\d{2}[a-z]?(?=[);,:])")


def stats(txt):
    return {
        "chars": len(txt),
        "markers": {m: txt.count(m) for m in MARKERS},
        "cites": len(CITE.findall(txt)),
        "tables": set(re.findall(r"<표 \d-\d+>", txt)),
        "figs": set(re.findall(r"<그림 \d-\d+>", txt)),
        "banned": {b: txt.count(b) for b in BANNED if txt.count(b)},
    }


def head_version(rel):
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def main(paths):
    fail = False
    for p in paths:
        rel = str(Path(p)).replace("\\", "/")
        cur_raw = (ROOT / rel).read_bytes()
        cur = cur_raw.decode("utf-8")
        base = head_version(rel)
        print("=" * 70); print(rel)
        n_crlf, n_lf = cur_raw.count(b"\r\n"), cur_raw.count(b"\n")
        mixed = 0 < n_crlf < n_lf
        print(f"줄끝: CRLF {n_crlf} / LF {n_lf} {'← 혼합 FAIL' if mixed else 'OK'}")
        fail |= mixed
        s = stats(cur)
        if base is None:
            print("HEAD 판본 없음 — 현재 상태만 출력"); print(s); continue
        b = stats(base)
        print(f"글자 수: {b['chars']} → {s['chars']} ({s['chars']-b['chars']:+d}, {(s['chars']-b['chars'])/b['chars']*100:+.1f}%)")
        for m in MARKERS:
            if b["markers"][m] != s["markers"][m]:
                print(f"마커 {m}: {b['markers'][m]} → {s['markers'][m]}  ← FAIL(의도한 변경이면 사유 보고)"); fail = True
        print("마커 합계:", sum(b["markers"].values()), "→", sum(s["markers"].values()))
        print(f"인용 연도 표기: {b['cites']} → {s['cites']}" + ("  ← WARN 감소(합치기였는지 확인)" if s["cites"] < b["cites"] else ""))
        for k in ("tables", "figs"):
            lost, added = b[k] - s[k], s[k] - b[k]
            if lost or added:
                print(f"{k}: 사라짐 {sorted(lost)} 추가 {sorted(added)}  ← FAIL(의도한 변경이면 사유 보고)"); fail = True
            else:
                print(f"{k}: {len(s[k])}종 동일")
        if s["banned"]:
            print("금지 표현:", s["banned"], "← FAIL"); fail = True
        else:
            print("금지 표현: 0")
    print("=" * 70); print("RESULT", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
