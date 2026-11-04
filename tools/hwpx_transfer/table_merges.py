"""Explicit Markdown table layout directives; no HWPX I/O.

Coordinates are zero-based and include the header row. Only empty cells may
be covered by a merge. Legacy labels may be changed only by explicit aliases.
"""
import json
import re
import xml.etree.ElementTree as ET

PREFIX = "<!-- hwpx-table-layout:"
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
CELL_RE = re.compile(r"<hp:tc\b.*?</hp:tc>", re.S)
SEG_RE = re.compile(r"<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>", re.S)


def directive(line):
    if not line.strip().startswith(PREFIX):
        return None
    if not line.strip().endswith("-->"):
        raise ValueError("Unclosed hwpx-table-layout directive")
    spec = json.loads(line.strip()[len(PREFIX):-3])
    if set(spec) - {"caption", "merges", "aliases"} or not spec.get("caption"):
        raise ValueError("Invalid hwpx-table-layout keys/caption")
    if not isinstance(spec.get("merges"), list) or not spec["merges"]:
        raise ValueError("Missing table merges")
    return spec


def validate_block(block):
    spec = block["layout"]
    grid = [block["header"]] + block["rows"]
    nr, nc = len(grid), len(grid[0])
    if any(len(row) != nc for row in grid):
        raise ValueError("Layout table must be rectangular")
    occupied = set()
    for merge in spec["merges"]:
        if len(merge) != 4 or any(type(v) is not int for v in merge):
            raise ValueError("Merge must be [row, col, rowSpan, colSpan]")
        r, c, rs, cs = merge
        if min(r, c) < 0 or min(rs, cs) < 1 or r + rs > nr or c + cs > nc or rs * cs < 2:
            raise ValueError("Merge outside table")
        for y in range(r, r + rs):
            for x in range(c, c + cs):
                if (y, x) in occupied:
                    raise ValueError("Overlapping merge directives")
                occupied.add((y, x))
                if (y, x) != (r, c) and grid[y][x].strip():
                    raise ValueError("Merge would discard nonempty Markdown cell")
    for alias in spec.get("aliases", []):
        if len(alias) != 3:
            raise ValueError("Alias must be [row, col, previous text]")
        r, c, old = alias
        if type(r) is not int or type(c) is not int or not (0 <= r < nr and 0 <= c < nc) or not isinstance(old, str):
            raise ValueError("Invalid table label alias")


def _root(xml):
    # Lazy import avoids a cycle when KjnDocument calls this module.
    import kjn_profile
    return ET.fromstring(kjn_profile._wrap(xml))


def _text(cell):
    return "".join((t.text or "") + "".join(c.tail or "" for c in t) for t in cell.iter(HP + "t"))


def _grid(xml):
    root = _root(xml)
    tables = list(root.iter(HP + "tbl"))
    if len(tables) != 1:
        raise ValueError("Declared layout needs exactly one non-nested table")
    tbl = tables[0]
    nr, nc = int(tbl.get("rowCnt")), int(tbl.get("colCnt"))
    cells, coverage = {}, {}
    raws = CELL_RE.findall(xml)
    elems = tbl.findall(HP + "tr/" + HP + "tc")
    if len(raws) != len(elems):
        raise ValueError("Cannot identify table cells safely")
    for cell, raw in zip(elems, raws):
        a, s = cell.find(HP + "cellAddr"), cell.find(HP + "cellSpan")
        r, c = int(a.get("rowAddr")), int(a.get("colAddr"))
        rs, cs = int(s.get("rowSpan")), int(s.get("colSpan"))
        if min(r, c) < 0 or min(rs, cs) < 1 or r + rs > nr or c + cs > nc:
            raise ValueError("Cell outside table")
        cells[r, c] = (cell, raw, rs, cs)
        for y in range(r, r + rs):
            for x in range(c, c + cs):
                if (y, x) in coverage:
                    raise ValueError("Overlapping table cells")
                coverage[y, x] = (r, c)
    if len(coverage) != nr * nc:
        raise ValueError("Table grid has holes")
    for row, tr in enumerate(tbl.findall(HP + "tr")):
        for cell in tr.findall(HP + "tc"):
            if int(cell.find(HP + "cellAddr").get("rowAddr")) != row:
                raise ValueError("Cell address disagrees with containing row")
    # A complete unmerged row establishes the original column widths.
    for r in range(nr):
        if all((r, c) in cells and cells[r, c][2:] == (1, 1) for c in range(nc)):
            widths = [int(cells[r, c][0].find(HP + "cellSz").get("width")) for c in range(nc)]
            if sum(widths) != int(tbl.find(HP + "sz").get("width")):
                raise ValueError("Column widths do not sum to table width")
            for (_, c), (cell, _, _, cs) in cells.items():
                if int(cell.find(HP + "cellSz").get("width")) != sum(widths[c:c + cs]):
                    raise ValueError("Cell width disagrees with column grid")
            break
    return tbl, cells, coverage


def _attr(raw, tag, name, value):
    pattern = r'(<hp:' + tag + r'\b[^>]*\b' + name + r'=")[^"]*(")'
    result, count = re.subn(pattern, lambda m: m[1] + str(value) + m[2], raw, count=1)
    if count != 1:
        raise ValueError("Missing %s@%s" % (tag, name))
    return result


def apply_layout(xml, block, aliases=False, row_offset=0):
    """Return minimally changed XML, preserving widths, styles and other cells."""
    validate_block(block)
    grid = [block["header"]] + block["rows"]
    tbl, cells, coverage = _grid(xml)
    nr, nc = len(grid), len(grid[0])
    if int(tbl.get("rowCnt")) != nr + row_offset or int(tbl.get("colCnt")) != nc:
        raise ValueError("Declared table dimensions no longer match")
    # Header identifies the table even if a caption number was accidentally reused.
    for c, expected in enumerate(grid[0]):
        if (row_offset, c) not in cells or _text(cells[row_offset, c][0]) != expected:
            raise ValueError("Declared table header mismatch")
    replacements = {}
    if aliases:
        for r, c, old in block["layout"].get("aliases", []):
            pos = (r + row_offset, c)
            if pos not in cells:
                if not grid[r][c] and coverage.get(pos) != pos:
                    continue  # already merged
                raise ValueError("Alias cell is missing")
            cell, raw, _, _ = cells[pos]
            current, expected = _text(cell), grid[r][c]
            if current == expected:
                continue
            if current != old:
                raise ValueError("Unexpected previous label at %s: %r" % (pos, current))
            # Reuse the first text run's style; do not flatten any other cell.
            texts = list(re.finditer(r"<hp:t>([^<]*)</hp:t>", raw))
            if not texts or cell.find('.//' + HP + 'tbl') is not None:
                raise ValueError("Cannot safely replace label runs")
            from html import escape
            new = raw
            for i, match in reversed(list(enumerate(texts))):
                new = new[:match.start(1)] + (escape(expected, quote=False) if i == 0 else "") + new[match.end(1):]
            if _text(next(_root(new).iter(HP + "tc"))) != expected:
                raise ValueError("Label contains unsupported inline content")
            replacements[raw] = SEG_RE.sub("", new)
    for raw, new in replacements.items():
        xml = xml.replace(raw, new, 1)
    changed = bool(replacements)
    for r, c, rs, cs in block["layout"]["merges"]:
        r += row_offset
        tbl, cells, coverage = _grid(xml)
        if (r, c) not in cells:
            raise ValueError("Merge anchor is missing")
        anchor, raw, ars, acs = cells[r, c]
        if _text(anchor) != grid[r - row_offset][c]:
            raise ValueError("Merge anchor text mismatch")
        if (ars, acs) == (rs, cs):
            continue
        region = {(y, x) for y in range(r, r + rs) for x in range(c, c + cs)}
        owners = {coverage[p] for p in region}
        for pos in owners:
            cell, _, crs, ccs = cells[pos]
            own = {(y, x) for y in range(pos[0], pos[0] + crs) for x in range(pos[1], pos[1] + ccs)}
            if not own <= region:
                raise ValueError("Merge crosses existing merged cell")
            has_control = any(child.tag != HP + "t" for run in cell.iter(HP + "run") for child in run)
            if pos != (r, c) and (_text(cell).strip() or has_control):
                raise ValueError("Merge would discard nonempty HWPX cell")
        # Width/height from existing grid, not a new template's metrics.
        widths = [int(cells[coverage[r, x]][0].find(HP + "cellSz").get("width"))
                  / cells[coverage[r, x]][3] for x in range(c, c + cs)]
        heights = [int(cells[coverage[y, c]][0].find(HP + "cellSz").get("height"))
                   / cells[coverage[y, c]][2] for y in range(r, r + rs)]
        new = _attr(_attr(raw, "cellSpan", "rowSpan", rs), "cellSpan", "colSpan", cs)
        new = _attr(_attr(new, "cellSz", "width", round(sum(widths))), "cellSz", "height", round(sum(heights)))
        new = SEG_RE.sub("", new)
        xml = xml.replace(raw, new, 1)
        for pos in owners - {(r, c)}:
            xml = xml.replace(cells[pos][1], "", 1)
        changed = True
    _grid(xml)  # full occupancy validation
    if changed:
        # The containing paragraph's cache follows </hp:tbl>; other cells stay intact.
        end = xml.rfind("</hp:tbl>") + len("</hp:tbl>")
        xml = xml[:end] + SEG_RE.sub("", xml[end:])
    return xml


def assert_fresh_matches(xml, block):
    """Reject stale fresh output before using current Markdown declarations."""
    _, cells, _ = _grid(xml)
    expected = [block["header"]] + block["rows"]
    shape = {(r, c): (1, 1) for r in range(len(expected)) for c in range(len(expected[0]))}
    for r, c, rs, cs in block["layout"]["merges"]:
        for y in range(r, r + rs):
            for x in range(c, c + cs):
                shape.pop((y, x), None)
        shape[r, c] = (rs, cs)
    if {pos: cell[2:] for pos, cell in cells.items()} != shape:
        raise ValueError("Fresh table lacks the declared merge structure; rebuild fresh")
    for (r, c), (cell, _, _, _) in cells.items():
        if r >= len(expected) or c >= len(expected[0]) or _text(cell) != expected[r][c]:
            raise ValueError("Fresh table differs from current declared Markdown table")
    # Enforces dimensions, header, merge anchors and empty covered cells.
    apply_layout(xml, block)
