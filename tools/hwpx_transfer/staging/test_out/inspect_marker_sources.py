# -*- coding: utf-8 -*-
"""blocks JSON의 가이드 마커를 블록/필드별로 집계한다."""

import collections
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).with_name("marker_source_counts.txt")
MARKER_RE = re.compile(
    r"\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]"
)

totals = collections.Counter()
lines = []
for path in sorted((ROOT / "tools" / "hwpx_transfer" / "staging").glob("*.blocks.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    per_type = collections.Counter()
    table_cells = 0
    other_fields = 0
    for block in data["blocks"]:
        kind = block["type"]
        if kind == "table":
            strings = list(block.get("header", []))
            strings.extend(cell for row in block.get("rows", []) for cell in row)
            count = sum(len(MARKER_RE.findall(value)) for value in strings)
            table_cells += count
        else:
            strings = []
            if "text" in block:
                strings.append(block["text"])
            strings.extend(run.get("text", "") for run in block.get("runs", []))
            count = sum(len(MARKER_RE.findall(value)) for value in strings)
            other_fields += count
        per_type[kind] += count
    file_total = sum(per_type.values())
    totals.update(per_type)
    lines.append(
        "%s total=%d table_cells=%d other=%d by_type=%s"
        % (path.name, file_total, table_cells, other_fields, dict(sorted(per_type.items())))
    )

lines.append("all_total=%d" % sum(totals.values()))
lines.append("all_by_type=%s" % dict(sorted(totals.items())))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
