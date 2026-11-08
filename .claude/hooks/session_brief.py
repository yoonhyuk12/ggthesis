# Claude Code SessionStart 훅 — log.md 최근 항목을 세션 시작 컨텍스트에 넣어 준다.
#
# log.md는 최신 항목이 맨 위에 오는 역순 파일이므로, 앞에서 몇 줄만 잘라 읽으면
# 직전 세션에서 실제로 바뀐 파일을 그대로 알 수 있다.
# 또한 00. hwpx/ 접두사 최신본이 Claude가 남긴 스냅샷과 다르면 "사용자 편집 감지"를 맨 앞에 붙인다
# (사용자 한글 직접 편집분의 MD 역동기화, .claude/rules/hwpx-user-edit-backsync.md, 2026-11-05).
# 기록 자체는 PostToolUse 훅인 log_change.py 가 남긴다.
#
# stdout은 반드시 JSON이어야 한다. Windows 콘솔은 cp949라 한글을 그대로 쓰면 깨지므로
# ensure_ascii 로 이스케이프한 뒤 바이트로 내보낸다.

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "log.md"
MAX_LINES = 25


HWPX_DIR = ROOT / "00. hwpx"
SNAP_DIR = ROOT / "tools" / "hwpx_transfer" / "staging" / "hwpx_snapshots"
PREFIX_RE = re.compile(r"^\d{6}_\d{4}_.*\.hwpx$")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def user_edit_notice():
    """접두사 최신 hwpx가 Claude가 남긴 스냅샷과 다르면 역동기화 알림을 만든다
    (.claude/rules/hwpx-user-edit-backsync.md). 실패해도 세션 시작을 막지 않는다."""
    try:
        files = sorted(p.name for p in HWPX_DIR.iterdir() if PREFIX_RE.match(p.name))
        if not files:
            return ""
        latest = files[-1]
        snap = SNAP_DIR / latest
        rule = ".claude/rules/hwpx-user-edit-backsync.md"
        if not snap.exists():
            return (f"[hwpx 스냅샷 없음] 접두사 최신본 {latest} 의 스냅샷이 없다. 사용자 직접 편집 여부는 "
                    f"git HEAD 판이나 직전 접두사 파일과 대조해 판단한다({rule}).")
        if _sha(HWPX_DIR / latest) != _sha(snap):
            return (f"[사용자 편집 감지] 접두사 최신본 {latest} 이 Claude가 남긴 스냅샷과 다르다. 사용자가 한글에서 "
                    f"직접 고친 것이므로, 작업 전에 tools/hwpx_transfer/hwpx_text_diff.py 로 대조해 MD에 역동기화한다({rule}).")
    except Exception as e:  # 파일 잠금 등
        return f"[hwpx 편집 감지 실패] {e!r} — 필요하면 수동으로 스냅샷과 대조한다."
    return ""


def main():
    notice = user_edit_notice()
    entries = []
    if LOG_PATH.exists():
        lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        entries = [ln for ln in lines if ln.strip()][:MAX_LINES]
    if not entries and not notice:
        return

    body = "\n".join(entries)
    context = (
        (notice + "\n\n" if notice else "") +
        f"[직전 작업 이력 — log.md 최근 {len(entries)}건, 최신순]\n"
        f"{body}\n\n"
        "이 저장소는 PostToolUse 훅이 파일 변경을 log.md에 자동 기록한다. "
        "위 목록은 직전 세션에서 실제로 바뀐 파일이며, 세션 밖에서 한글이나 편집기로 "
        "직접 고친 내용도 포함된다. 다만 시각은 실제 수정 시각이 아니라 훅이 발견한 시각이다. "
        f"더 거슬러 올라가려면 {LOG_PATH.name} 를 직접 읽는다."
    )

    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    sys.stdout.buffer.write(json.dumps(out).encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
