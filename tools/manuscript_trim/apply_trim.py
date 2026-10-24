# -*- coding: utf-8 -*-
"""분량 감축 1단계 감사 JSON(03.plan/261024_1314_분량감축_감사/*.json)의 문장 단위 old→new를 원고에 적용한다.

사용:
  python tools/manuscript_trim/apply_trim.py --json 03.plan/261024_1314_분량감축_감사/05.json            # 모의 실행(파일 미수정)
  python tools/manuscript_trim/apply_trim.py --json ... --apply                                       # 실제 적용
  옵션: --include-ambiguous (reason에 '애매'가 든 항목도 적용; 기본은 제외), --exclude-ids 05-001,05-002, --log <path>

규칙: 항목마다 적용 직전에 old가 파일에 정확히 1회 있는지 다시 확인하고, 아니면 건너뛰고 conflicts에 기록한다.
줄끝(CRLF/LF)은 원본 그대로 유지한다. 적용 후 새로 생긴 '다.다'·이중 공백 자리를 찾아 보고한다(워커가 손으로 다듬을 지점).
"""
import argparse, json, re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SEAMS = [r"다\.[가-힣A-Za-z<(\[]", r"  +", r"\. \.", r"다\. 다\. "]


def seams(txt):
    out = []
    for pat in SEAMS:
        out += [m.start() for m in re.finditer(pat, txt)]
    return set(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--include-ambiguous", action="store_true")
    ap.add_argument("--exclude-ids", default="")
    ap.add_argument("--log", default="")
    a = ap.parse_args()
    j = json.load(open(a.json, encoding="utf-8"))
    path = ROOT / j["file"]
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    txt = raw.decode("utf-8")
    before = txt
    excl = {x.strip() for x in a.exclude_ids.split(",") if x.strip()}
    items = sorted(j["items"], key=lambda i: (i.get("line", 0), i["id"]))
    applied, skipped_amb, skipped_id, conflicts = [], [], [], []
    for it in items:
        if it["id"] in excl:
            skipped_id.append(it["id"]); continue
        if not a.include_ambiguous and "애매" in it.get("reason", ""):
            skipped_amb.append(it["id"]); continue
        old, new = it["old"], it.get("new", "")
        if "\n" in old or "\n" in new:
            conflicts.append((it["id"], "줄바꿈 포함")); continue
        c = txt.count(old)
        if c != 1:
            conflicts.append((it["id"], f"old {c}회 등장")); continue
        txt = txt.replace(old, new, 1)
        applied.append((it["id"], len(old) - len(new)))
    saved = len(before) - len(txt)
    new_seams = sorted(seams(txt) - seams(before))
    # 새 이음새 위치를 행 번호로
    seam_lines = sorted({txt.count("\n", 0, p) + 1 for p in new_seams})
    print(f"파일: {j['file']}  줄끝: {'CRLF' if crlf else 'LF'}")
    print(f"적용 {len(applied)}건 / 애매 제외 {len(skipped_amb)}건 / id 제외 {len(skipped_id)}건 / 충돌 {len(conflicts)}건 / 실제 절감 {saved}자")
    if conflicts:
        for cid, why in conflicts: print("  충돌:", cid, why)
    if seam_lines:
        print("  손볼 이음새(행):", seam_lines[:40])
    if a.apply:
        out = txt
        if crlf and "\r\n" not in out[:200]:
            pass
        path.write_bytes(out.encode("utf-8"))
        print("  → 파일에 기록함")
    else:
        print("  (모의 실행 — 파일 미수정)")
    if a.log:
        Path(a.log).write_text(json.dumps({"file": j["file"], "applied": applied, "skipped_ambiguous": skipped_amb,
                                           "skipped_ids": sorted(skipped_id), "conflicts": conflicts, "saved": saved,
                                           "seam_lines": seam_lines, "applied_to_disk": a.apply}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
