"""04장 볼드 단독 소제목의 파싱 분기와 커버리지를 점검한다."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARSER_PATH = HERE.parent / "md_to_blocks.py"
REPORT_PATH = HERE / "bold_subheading_coverage_check.json"
TARGET_LINES = (55, 65, 136, 147, 162, 173, 188)
BASELINE_COUNTS = {
    "ch01": 41,
    "ch02": 96,
    "ch03": 85,
    "ch04": 93,
    "ch05": 83,
    "ch06": 40,
    "apx1": 63,
    "apx2": 25,
}

parser_env = os.environ.copy()
parser_env["PYTHONIOENCODING"] = "utf-8"
parser_run = subprocess.run(
    [sys.executable, str(PARSER_PATH)],
    cwd=PARSER_PATH.parents[2],
    env=parser_env,
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=False,
)


spec = importlib.util.spec_from_file_location("md_to_blocks", PARSER_PATH)
parser = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(parser)

trace_events = []


def tracer(frame, event, arg):
    if event != "line" or frame.f_code.co_name != "parse_file":
        return tracer

    line_no = frame.f_lineno
    local = frame.f_locals
    if line_no in (273, 274, 275) and local.get("ln") in TARGET_LINES:
        trace_events.append(
            {
                "phase": "parse",
                "source_line": local["ln"],
                "parser_line": line_no,
                "source_text": local.get("line"),
            }
        )
    if line_no == 309 and local.get("ln0") in TARGET_LINES:
        assigned = local.get("a")
        trace_events.append(
            {
                "phase": "coverage",
                "source_line": local["ln0"],
                "parser_line": line_no,
                "normalized_source": local.get("nl"),
                "assignment_kind": assigned[0] if assigned else None,
                "assignment_text": local.get("target"),
                "normalized_assignment": parser.norm(local.get("target", "")),
            }
        )
    return tracer


sys.settrace(tracer)
try:
    lines, blocks, excluded, _, _, missing, _ = parser.parse_file("04_연구설계.md")
finally:
    sys.settrace(None)


def block_text(block):
    if "text" in block:
        return block["text"]
    if "runs" in block:
        return "".join(run["text"] for run in block["runs"])
    return ""


targets = []
for source_line in TARGET_LINES:
    source_text = lines[source_line - 1]
    expected_text = source_text.removeprefix("**").removesuffix("**")
    block_hits = [
        {
            "index": index,
            "type": block["type"],
            "text": block_text(block),
            "runs": block.get("runs", []),
        }
        for index, block in enumerate(blocks)
        if block_text(block) == expected_text
    ]
    exclusion_hits = [entry for entry in excluded if expected_text in entry["text"]]
    targets.append(
        {
            "source_line": source_line,
            "source_text": source_text,
            "normalized_source": parser.norm(source_text),
            "expected_text": expected_text,
            "normalized_expected": parser.norm(expected_text),
            "block_hits": block_hits,
            "exclusion_hits": exclusion_hits,
            "reported_missing": any(item[0] == source_line for item in missing),
        }
    )

report = {
    "parser_command": "python tools/hwpx_transfer/md_to_blocks.py",
    "parser_returncode": parser_run.returncode,
    "parser_stdout": parser_run.stdout,
    "parser_stderr": parser_run.stderr,
    "trace_events": trace_events,
    "targets": targets,
    "missing_lines": [item[0] for item in missing],
}

block_counts = {}
for stem, baseline in BASELINE_COUNTS.items():
    doc = json.loads((HERE / f"{stem}.blocks.json").read_text(encoding="utf-8"))
    block_counts[stem] = len(doc["blocks"])

parse_report_text = (HERE / "parse_report.md").read_text(encoding="utf-8")
report.update(
    {
        "block_counts": block_counts,
        "baseline_counts": BASELINE_COUNTS,
        "total_blocks": sum(block_counts.values()),
        "count_regressions": {
            stem: {"baseline": baseline, "actual": block_counts[stem]}
            for stem, baseline in BASELINE_COUNTS.items()
            if block_counts[stem] < baseline
        },
        "parse_report_has_missing_zero": "**누락 0 — 8개 파일 전체에서 커버리지 목표를 충족했다.**"
        in parse_report_text,
    }
)
report["pass"] = (
    parser_run.returncode == 0
    and all(item["block_hits"] for item in targets)
    and all(
        hit["type"] == "p"
        and hit["runs"]
        and all(run.get("bold") for run in hit["runs"])
        for item in targets
        for hit in item["block_hits"]
    )
    and not any(item["exclusion_hits"] for item in targets)
    and not any(item["reported_missing"] for item in targets)
    and not report["count_regressions"]
    and report["parse_report_has_missing_zero"]
)
REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if not report["pass"]:
    raise SystemExit(1)
