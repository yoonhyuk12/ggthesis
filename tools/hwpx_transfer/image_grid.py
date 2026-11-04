"""Manifest-sized PNG grids in body/appendix cells; raster content is unchanged."""
import json
import math
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

MM = 283.465
CELL_IMAGE = re.compile(r"^(.*?)<br\s*/?>\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", re.S)


BODY_HEADING = re.compile(r"^jamovi 원출력\((<표\s+\d+-\d+>)\)")


def parse_cells(block, source, heading=None):
    if any(block["header"]):
        raise ValueError("Image grids require an empty Markdown header")
    source = Path(source)
    rows = []
    manifests = {}
    for row in block["rows"]:
        if len(row) != len(block["header"]):
            raise ValueError("Ragged image grid")
        cells = []
        for raw in row:
            if not raw.strip():
                cells.append(None)
                continue
            match = CELL_IMAGE.fullmatch(raw.strip())
            if not match:
                raise ValueError("Expected label + image in grid cell: " + raw)
            label, alt, path = match.groups()
            img = source.parent / path
            mf = img.parent / "manifest.json"
            if mf not in manifests:
                manifests[mf] = {c["file"]: dict(c, target=group.get("for") if group.get("bupyo") is None else None) for group in json.loads(mf.read_text(encoding="utf-8"))
                                 for c in group["cells"]}
            meta = manifests[mf][img.name]
            if meta.get("target"):
                match_heading = BODY_HEADING.match(heading or "")
                if not match_heading or match_heading.group(1) != meta["target"]:
                    raise ValueError("Body image-grid heading does not match manifest target: " + img.name)
            # Paths stay portable and relative to the repository.
            cells.append(dict(label=label.strip(), alt=alt, path=img.relative_to(
                Path(__file__).resolve().parents[2]).as_posix(),
                width_mm=meta["width_mm"], height_mm=meta["height_mm"],
                fits_width=meta["fits_width"]))
        rows.append(cells)
    result = {"rows": rows, "cols": len(block["header"])}
    match_heading = BODY_HEADING.match(heading or "")
    if match_heading:
        result.update(target=match_heading.group(1), heading=heading, unnumbered=True)
    return result


def plan(grid, total_width):
    """Blank trailing cells extend the preceding cell, preserving image scale.

    First satisfy single-column image widths, then merged spans. This permits
    the 134.2 mm loading table and the three-column reliability layout without
    arbitrarily shrinking every PNG or changing their row order.
    """
    ncols = grid["cols"]
    rows = []
    widths = [1] * ncols
    for row in grid["rows"]:
        active = [i for i, c in enumerate(row) if c is not None]
        if not active or active[0] != 0:
            raise ValueError("Image rows must start in the first cell")
        cells = []
        for j, col in enumerate(active):
            c = dict(row[col])
            span = (active[j + 1] if j + 1 < len(active) else ncols) - col
            w = round(c["width_mm"] * MM)
            h = round(c["height_mm"] * MM)
            pad = round(.5 * MM)
            if not c["fits_width"]:
                w = min(round(140 * MM), total_width)
                h = round(c["height_mm"] * w / c["width_mm"])
                pad = 0  # 140 mm image itself fills the 140 mm body width.
            c.update(col=col, span=span, width=w, height=h, pad=pad)
            cells.append(c)
            if span == 1:
                widths[col] = max(widths[col], w + 2 * pad)
        rows.append(cells)
    for row in rows:
        for c in row:
            a, b = c["col"], c["col"] + c["span"]
            shortage = c["width"] + 2 * c["pad"] - sum(widths[a:b])
            if shortage > 0:
                widths[b - 1] += shortage
    if sum(widths) > total_width:
        raise ValueError("Image grid cannot preserve requested scale: %s > %s" % (widths, total_width))
    remainder = total_width - sum(widths)
    weight = sum(widths)
    extra = [int(remainder * w / weight) for w in widths]
    extra[-1] += remainder - sum(extra)
    widths = [a + b for a, b in zip(widths, extra)]
    return rows, widths


def label_measure(text):
    """GDI width at 9 pt; name reports a font substitute if GDI uses one."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        g = ctypes.WinDLL("gdi32")
        g.CreateCompatibleDC.restype = wintypes.HDC
        g.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
        g.CreateFontW.restype = wintypes.HANDLE
        g.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
        g.SelectObject.restype = wintypes.HANDLE
        g.GetTextExtentPoint32W.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.c_void_p]
        g.GetTextFaceW.argtypes = [wintypes.HDC, ctypes.c_int, wintypes.LPWSTR]
        g.DeleteObject.argtypes = [wintypes.HANDLE]
        g.DeleteDC.argtypes = [wintypes.HDC]
        dc = g.CreateCompatibleDC(None)
        font = g.CreateFontW(-90, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, "한양신명조")
        old = g.SelectObject(dc, font)
        size = wintypes.SIZE()
        name = ctypes.create_unicode_buffer(128)
        try:
            if not g.GetTextExtentPoint32W(dc, text, len(text), ctypes.byref(size)):
                raise ValueError("GDI label measurement failed")
            g.GetTextFaceW(dc, 128, name)
            return size.cx * 10, name.value
        finally:
            g.SelectObject(dc, old)
            g.DeleteObject(font)
            g.DeleteDC(dc)
    import table_layout
    return table_layout.text_width(text, 9), "estimated (GDI unavailable)"


def assemble(doc, grid):
    import kjn_profile as kp
    asm = doc.asm
    rows, widths = plan(grid, asm.total_width)
    hp = "{" + kp.NS["hp"] + "}"
    # Reuse known-valid table attributes, then replace the dummy text cells.
    xml, _ = asm.table_xml([""] * grid["cols"], [])
    wrapper = ET.fromstring(kp._wrap(xml))
    table = next(wrapper.iter(hp + "tbl"))
    for child in list(table):
        if child.tag == hp + "tr":
            table.remove(child)
    cp = str(asm.pf.get("table", "cell_charPr", "small9"))
    pp = str(asm.pf.get("table", "cell_paraPr", "text_left"))
    spec = {"para": pp, "char": cp, "style": "0"}
    # Clear table borders; the jamovi raster already has horizontal rules.
    border = asm.header.item_xml("borderFill", asm.pf.get("table", "borderFills", "inner_012"))
    border = re.sub(r'(<hh:(?:left|right|top|bottom|diagonal)Border\b[^>]*\btype=")[^"]+', r'\g<1>NONE', border)
    border_id = asm.header.find_same("borderFill", border) or asm.header.add("borderFill", border)
    total_height = 0
    evidence = []
    for row_index, row in enumerate(rows):
        tr = ET.SubElement(table, hp + "tr")
        row_height = 0
        row_cells = []
        for c in row:
            width = sum(widths[c["col"]:c["col"] + c["span"]])
            data = (Path(__file__).resolve().parents[2] / c["path"]).read_bytes()
            pw, ph = kp.png_size(data)
            if abs(pw / ph - c["width_mm"] / c["height_mm"]) > .01:
                raise ValueError("Manifest/PNG aspect ratio mismatch: " + c["path"])
            item = doc._next_bin_id()
            doc.bin_items.append((item, "BinData/" + item + ".png", data))
            picture, _ = asm.picture_para(item, pw, ph, c["width"], name=Path(c["path"]).name,
                                          display_size=(c["width"], c["height"]))
            p = ET.fromstring(kp._wrap(picture))[0]
            p.set("paraPrIDRef", pp)
            p.set("styleIDRef", "0")
            for run in p.findall(hp + "run"):
                run.set("charPrIDRef", cp)
            pic = p.find(".//" + hp + "pic")
            pic.find(hp + "pos").set("treatAsChar", "1")
            pic.find(hp + "pos").set("horzAlign", "LEFT")
            tc = ET.fromstring(kp._wrap(asm.cell("", row_index, c["col"], width, grid["cols"], False)))[0]
            tc.set("hasMargin", "1")
            tc.set("borderFillIDRef", border_id)
            tc.find(hp + "cellSpan").set("colSpan", str(c["span"]))
            sub = tc.find(hp + "subList")
            sub.set("vertAlign", "TOP")
            for child in list(sub):
                sub.remove(child)
            sub.append(ET.fromstring(kp._wrap(asm.text_para(spec, c["label"])))[0])
            sub.append(p)
            margins = tc.find(hp + "cellMargin")
            margins.attrib.update(left=str(c["pad"]), right=str(c["pad"]), top="142", bottom="142")
            tw, font = label_measure(c["label"])
            lines = max(1, math.ceil(tw / (width - 2 * c["pad"])))
            height = c["height"] + lines * 1500 + 600
            row_height = max(row_height, height)
            tr.append(tc)
            row_cells.append(tc)
            evidence.append(dict(row=row_index, col=c["col"], span=c["span"], cell_width=width,
                                 picture_width=c["width"], picture_height=c["height"], file=c["path"],
                                 label_font_measured=font, estimated_label_lines=lines))
        if asm.avail_height and row_height > asm.avail_height:
            raise ValueError("Single image-grid row exceeds body height")
        for tc in row_cells:
            tc.find(hp + "cellSz").set("height", str(row_height))
        total_height += row_height
    table.set("rowCnt", str(len(rows)))
    table.set("repeatHeader", "0")  # Markdown's empty header is structural, not printed.
    split = bool(asm.avail_height and total_height > asm.avail_height)
    table.set("pageBreak", "TABLE" if split else "NONE")
    table.find(hp + "sz").attrib.update(width=str(sum(widths)), height=str(total_height))
    table.find(hp + "pos").set("treatAsChar", "0" if split else "1")
    table.find(hp + "pos").set("horzRelTo", "COLUMN")
    table.find(hp + "inMargin").attrib.update(left="0", right="0", top="0", bottom="0")
    if split:
        asm._z_order += 1
        table.set("zOrder", str(asm._z_order))
    return kp._unwrap(wrapper), widths, evidence
