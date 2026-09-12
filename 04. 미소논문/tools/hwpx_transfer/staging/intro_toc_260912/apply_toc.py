"""Populate existing section1 TOC entries from a matching, Hancom-exported PDF.

Requires lxml and PyMuPDF. No COM. Refuses existing output and in-place writes.
Only Contents/header.xml and targeted section1 paragraphs may change. Run again
with the re-exported PDF and a NEW output name if front-matter pagination changes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.parsers.expat
import zipfile

import fitz
from lxml import etree as ET

NS = {k: f'http://www.hancom.co.kr/hwpml/2011/{v}' for k, v in
      [('hp', 'paragraph'), ('hh', 'head'), ('hc', 'core')]}
HP, HH, HC = (f'{{{NS[k]}}}' for k in ('hp', 'hh', 'hc'))
HEADER, TOC, BODY = 'Contents/header.xml', 'Contents/section1.xml', 'Contents/section2.xml'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def norm(text):
    # Whitespace/punctuation are layout differences, never fuzzy word matching.
    text = unicodedata.normalize('NFKC', text).casefold()
    return ''.join(c for c in text if c.isalnum())


def own_text(p):
    out = []
    for t in p.findall('./hp:run/hp:t', NS):
        out.append(t.text or '')
        for child in t:
            out.append('\t' if child.tag == HP + 'tab' else '\n')
            out.append(child.tail or '')
    return ''.join(out)


def title(p):
    return own_text(p).split('\t', 1)[0].strip()


def top_spans(raw):
    """Byte offsets preserve every non-target paragraph, including cell content."""
    parser = xml.parsers.expat.ParserCreate(namespace_separator='|')
    depth, start, spans = 0, None, []

    def begin(name, attrs):
        nonlocal depth, start
        depth += 1
        if depth == 2 and name == NS['hp'] + '|p':
            start = parser.CurrentByteIndex

    def end(name):
        nonlocal depth
        if depth == 2 and name == NS['hp'] + '|p':
            at = parser.CurrentByteIndex
            # Self-closing elements report the byte after their closing bracket.
            stop = raw.index(b'>', at) + 1 if raw[at:at + 2] == b'</' else at
            spans.append((start, stop))
        depth -= 1

    parser.StartElementHandler, parser.EndElementHandler = begin, end
    parser.Parse(raw, True)
    return spans


def pdf_data(path):
    pages = []
    with fitz.open(path) as doc:
        for page in doc:
            lines = []
            footers = []
            for block in page.get_text('dict', sort=True)['blocks']:
                for line in block.get('lines', []):
                    text = ''.join(s['text'] for s in line['spans']).strip()
                    if not text:
                        continue
                    box = list(line['bbox'])
                    token = unicodedata.normalize('NFKC', text)
                    match = re.fullmatch(r'\s*[-–—]?\s*(\d+|[ivxlcdmIVXLCDM]+)\s*[-–—]?\s*', token)
                    cx = (box[0] + box[2]) / 2
                    if (box[1] > page.rect.height * .86 and
                            abs(cx - page.rect.width / 2) < page.rect.width * .12 and match):
                        val = match[1]
                        footers.append({'text': text, 'value': val,
                                        'kind': 'arabic' if val.isdigit() else 'roman', 'bbox': box})
                    else:
                        lines.append({'text': text, 'norm': norm(text), 'bbox': box})
            require(len(footers) <= 1, f'Ambiguous bottom-center footer on PDF page {len(pages)+1}: {footers}')
            pages.append({'lines': lines, 'footer': footers[0] if footers else None})
    return pages


def occurrences(pages, target, start=0, end=None):
    key, found = norm(target), []
    for pi in range(start, len(pages) if end is None else end):
        lines = pages[pi]['lines']
        for li in range(len(lines)):
            joined = ''
            for stop in range(li, min(li + 8, len(lines))):
                joined += lines[stop]['norm']
                if joined == key:
                    found.append((pi, li, stop))
                    break
                if len(joined) >= len(key) or not key.startswith(joined):
                    break
    return found


def body_start(pages, body, report):
    hits = occurrences(pages, '제1장 서론')
    candidates = []
    for pi, li, stop in hits:
        footer = pages[pi]['footer']
        if footer and footer['kind'] == 'arabic' and footer['value'] == '1':
            candidates.append(pi)
        elif not footer and pi + 2 < len(pages):
            # First printed number is intentionally hidden in the supplied HWPX.
            # This exception is verified by XML restart + hiding + next TWO labels.
            controls = body[0]
            restart = controls.xpath('.//hp:newNum[@numType="PAGE"][@num="1"]', namespaces=NS)
            hiding = controls.xpath('.//hp:pageHiding[@hidePageNum="1"]', namespaces=NS)
            following = [pages[j]['footer'] for j in (pi + 1, pi + 2)]
            if restart and hiding and all(f and f['kind'] == 'arabic' and f['value'] == str(n)
                                          for f, n in zip(following, (2, 3))):
                candidates.append(pi)
    require(len(candidates) == 1, f'Cannot prove unique body start: {candidates}')
    first = candidates[0]
    report['body_start_pdf_page'] = first + 1
    report['hidden_first_page_exception'] = not bool(pages[first]['footer'])
    if not pages[first]['footer']:
        report['hidden_first_page_evidence'] = {
            'xml': 'section2 first paragraph newNum PAGE=1 and pageHiding hidePageNum=1',
            'following_printed_footers': [pages[first + n]['footer'] for n in (1, 2)]}
    # Every other number must be physically present; never fill missing numbers.
    previous = 1
    for pi in range(first + 1, len(pages)):
        footer = pages[pi]['footer']
        require(footer and footer['kind'] == 'arabic', f'Missing Arabic footer on PDF page {pi+1}')
        current = int(footer['value'])
        require(current == previous + 1, f'Non-contiguous observed body labels at PDF page {pi+1}')
        previous = current
    return first


def entries(section):
    mode = None
    result = []
    for idx, p in enumerate(section):
        if p.tag != HP + 'p':
            continue
        text = title(p)
        if p.find('.//hp:tbl', NS) is not None:
            label = norm(''.join(p.xpath('.//hp:t/text()', namespaces=NS)))
            if label in ('목차', '표목차', '그림목차'):
                mode = {'목차': 'main', '표목차': 'table', '그림목차': 'figure'}[label]
            elif label in ('감사의글', '논문개요', '국문초록'):
                mode = None
            continue
        if norm(text) in ('목차', '표목차', '그림목차') and mode != 'main':
            mode = {'목차': 'main', '표목차': 'table', '그림목차': 'figure'}[norm(text)]
            continue
        if mode and text:
            result.append({'top_idx': idx, 'kind': mode, 'title': text, 'p': p})
    require(result and {e['kind'] for e in result} == {'main', 'table', 'figure'}, 'Missing TOC/list regions')
    return result


def map_entries(items, body, pages, first, report):
    # Only each paragraph's own runs: container paragraphs must not duplicate captions.
    paragraphs = [(i, p, title(p)) for i, p in enumerate(body.iter(HP + 'p')) if title(p)]
    body_scope, active = {}, None
    chapter_pdf = {}
    chapter_titles = {norm(e['title']): int(m[1]) for e in items
                      if e['kind'] == 'main'
                      and (m := re.match(r'^제\s*(\d+)\s*장', e['title']))}
    for i, p, text in paragraphs:
        if norm(text) in chapter_titles:
            active = chapter_titles[norm(text)]
            hits = occurrences(pages, text, first)
            require(len(hits) == 1, f'Ambiguous chapter boundary: {text}')
            chapter_pdf[active] = hits[0]
        body_scope[i] = active
    cursor, pdf_cursor = -1, (first, -1, -1)
    toc_scope = None
    for item in items:
        text = item['title']
        chapter = re.match(r'^제\s*(\d+)\s*장', text)
        if item['kind'] == 'main' and chapter:
            toc_scope = int(chapter[1])
        scoped = item['kind'] == 'main' and bool(re.match(r'^제\s*\d+\s*[장절항]', text))
        front = {'표목차': '표 목 차', '그림목차': '그 림 목 차', '국문초록': '논 문 개 요'}
        if item['kind'] == 'main' and norm(text) in front:
            hits = occurrences(pages, front[norm(text)], 0, first)
            require(len(hits) == 1, f'Ambiguous/missing front title: {text}')
            hit = hits[0]
            require(pages[hit[0]]['footer'] and pages[hit[0]]['footer']['kind'] == 'roman', f'No Roman label: {text}')
            body_text, bi = front[norm(text)], None
        else:
            matches = [(i, p, t) for i, p, t in paragraphs if norm(t) == norm(text)
                       and (item['kind'] != 'main' or i > cursor)
                       and (not scoped or body_scope[i] == toc_scope)]
            require(matches, f'No exact normalized body heading/caption for {text}; update approved intro first')
            # Repeated numbered headings resolve through document order, not global find.
            bi, bp, body_text = matches[0]
            hits = occurrences(pages, body_text, first)
            if item['kind'] == 'main':
                hits = [h for h in hits if h[:2] > pdf_cursor[:2]]
                if scoped:
                    lower = chapter_pdf[toc_scope]
                    upper = chapter_pdf.get(toc_scope + 1, (len(pages), 0, 0))
                    hits = [h for h in hits if lower[:2] <= h[:2] < upper[:2]]
            require(hits, f'PDF heading/caption not found: {body_text}')
            hit = hits[0]
            if item['kind'] == 'main':
                cursor, pdf_cursor = bi, hit
            else:
                hit_pages = sorted({h[0] for h in hits})
                if len(hit_pages) > 1:
                    cell = next(bp.iterancestors(HP+'tc'), None)
                    table = next(bp.iterancestors(HP+'tbl'), None)
                    repeated = (len(matches) == 1 and cell is not None and table is not None
                                and cell.get('header') == '1' and table.get('repeatHeader') == '1'
                                and table.get('pageBreak') == 'TABLE'
                                and hit_pages == list(range(hit_pages[0], hit_pages[-1]+1)))
                    require(repeated, f'Caption occurs on multiple pages: {text}; manual disambiguation required')
                    report.setdefault('repeated_caption_first_pages', []).append(
                        {'title': text, 'pdf_pages': [p+1 for p in hit_pages], 'selected': hit[0]+1})
        pi, li, end = hit
        footer = pages[pi]['footer']
        number = footer['value'] if footer else ('1' if pi == first else None)
        require(number, f'No proven printed label: {text}')
        item.update(number=number, body_text=body_text, body_idx=bi, pdf_page=pi + 1,
                    chapter_scope=toc_scope if scoped else None)
        report['entries'].append({k: v for k, v in item.items() if k != 'p'} | {
            'matched_pdf_text': ' '.join(l['text'] for l in pages[pi]['lines'][li:end + 1]),
            'heading_bbox': pages[pi]['lines'][li]['bbox'], 'footer': footer,
            'number_source': 'printed_footer' if footer else 'verified_hidden_restart'})


def wrap_title(text, capacity):
    # Conservative width: every visible character receives a full font-size cell.
    # Explicit line breaks prevent title glyphs entering the reserved number area.
    parts = []
    remaining = re.sub(r'\s+', ' ', text).strip()
    while len(remaining) > capacity:
        stop = remaining.rfind(' ', 0, capacity + 1)
        if stop < capacity // 2:
            stop = capacity
        parts.append(remaining[:stop].rstrip())
        remaining = remaining[stop:].lstrip()
    parts.append(remaining)
    return parts


def serialize(el):
    return ET.tostring(el, encoding='utf-8', with_tail=False)


def append_header(raw, tag, additions):
    pattern = rb'(<hh:' + tag.encode() + rb'\b[^>]*)(>)(.*?)(</hh:' + tag.encode() + rb'>)'
    match = re.search(pattern, raw, re.S)
    require(match is not None, f'Header collection absent: {tag}')
    opening = match[1]
    count = re.search(rb'itemCnt="(\d+)"', opening)
    require(count is not None, 'Header count missing')
    opening = re.sub(rb'itemCnt="\d+"', f'itemCnt="{int(count[1])+len(additions)}"'.encode(), opening)
    replacement = opening + b'>' + match[3] + b''.join(map(serialize, additions)) + match[4]
    return raw[:match.start()] + replacement + raw[match.end():]


def apply_layout(raw, header_raw, section, header, items, report):
    tabs = header.find('.//hh:tabProperties', NS)
    paras = header.find('.//hh:paraProperties', NS)
    chars = {c.get('id'): c for c in header.findall('.//hh:charPr', NS)}
    tab_map, para_map = ({c.get('id'): c for c in collection} for collection in (tabs, paras))
    tab_id = max(map(int, tab_map)) + 1
    para_id = max(map(int, para_map)) + 1
    page = section.find('.//hp:pagePr', NS)
    margin = page.find('hp:margin', NS)
    width = int(page.get('width')) - sum(int(margin.get(k, '0')) for k in ('left', 'right', 'gutter'))
    spans = top_spans(raw)
    require(len(spans) == len(section), 'Unexpected non-paragraph top-level element')
    additions_t, additions_p, replacements = [], [], []
    for item in items:
        p = copy.deepcopy(item['p'])
        old = para_map[p.get('paraPrIDRef')]
        newpara = copy.deepcopy(old)
        newpara.set('id', str(para_id)); newpara.set('tabPrIDRef', str(tab_id))
        newpara.find('hh:align', NS).set('horizontal', 'LEFT')
        breaks = newpara.find('hh:breakSetting', NS)
        if breaks is not None:
            breaks.set('keepLines', '1')
        depth = 2 if re.match(r'제\s*\d+\s*항', item['title']) else (1 if re.match(r'제\s*\d+\s*절', item['title']) else 0)
        left = depth * 1200
        for m in newpara.findall('.//hh:margin', NS):
            for tag, value in [('left', left), ('right', 0), ('intent', 0)]:
                child = m.find('hc:' + tag, NS)
                if child is not None:
                    child.set('value', str(value)); child.set('unit', 'HWPUNIT')
        newtab = copy.deepcopy(tab_map[old.get('tabPrIDRef')])
        newtab.set('id', str(tab_id)); newtab.set('autoTabLeft', '0'); newtab.set('autoTabRight', '0')
        stops = newtab.findall('.//hh:tabItem', NS)
        if not stops:
            template = next((t for t in tabs if t.find('.//hh:tabItem', NS) is not None), None)
            require(template is not None, 'No existing tabItem template')
            for child in list(newtab): newtab.remove(child)
            for child in template: newtab.append(copy.deepcopy(child))
            stops = newtab.findall('.//hh:tabItem', NS)
        pos = width - 300
        for stop in stops:
            stop.set('type', 'RIGHT'); stop.set('leader', 'CIRCLE')
            stop.set('pos', str(pos if stop.get('unit') == 'HWPUNIT' else pos * 2))
        run_styles = {r.get('charPrIDRef') for r in p.findall('hp:run', NS) if r.find('hp:t', NS) is not None}
        require(len(run_styles) == 1, f'Mixed character styles need explicit preservation: {item["title"]}')
        style = next(iter(run_styles))
        height = int(chars[style].get('height'))
        require(height > 0, f'Invalid character height: {item["title"]}')
        require(all(c.tag in (HP+'run', HP+'linesegarray') for c in p), 'Unsupported paragraph control')
        require(all(c.tag == HP+'t' for r in p.findall('hp:run', NS) for c in r), 'Refusing to remove non-text run controls')
        for c in list(p): p.remove(c)
        p.set('paraPrIDRef', str(para_id))
        run = ET.SubElement(p, HP+'run', charPrIDRef=style)
        t = ET.SubElement(run, HP+'t')
        capacity = int((pos - left - (len(item['number']) + 2) * height) // height)
        require(capacity >= 12, 'Insufficient title width')
        lines = wrap_title(item['title'], capacity)
        t.text = lines[0]
        for line in lines[1:]: ET.SubElement(t, HP+'lineBreak').tail = line
        ET.SubElement(t, HP+'tab', width='0', leader='7', type='2').tail = item['number']
        start, stop = spans[item['top_idx']]
        replacements.append((start, stop, serialize(p)))
        additions_t.append(newtab); additions_p.append(newpara)
        report['layout'].append({'top_idx': item['top_idx'], 'paraPr': para_id, 'tabPr': tab_id,
                                 'tab_position_hwpunit': pos, 'font_height': height,
                                 'title_lines': lines, 'reserved_number_cells': len(item['number']) + 2})
        tab_id += 1; para_id += 1
    for start, stop, data in sorted(replacements, reverse=True): raw = raw[:start] + data + raw[stop:]
    header_raw = append_header(header_raw, 'tabProperties', additions_t)
    header_raw = append_header(header_raw, 'paraProperties', additions_p)
    ET.fromstring(raw); ET.fromstring(header_raw)
    return raw, header_raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('input', 'pdf', 'output', 'report'):
        parser.add_argument('--' + flag, required=True, type=Path)
    args = parser.parse_args()
    report = {'status': 'started', 'entries': [], 'layout': [], 'input': str(args.input), 'pdf': str(args.pdf)}
    # A report argument must never be allowed to overwrite source files.
    require(args.report.resolve() not in {args.input.resolve(), args.pdf.resolve(), args.output.resolve()}, 'Report path collision')
    try:
        require(args.output.resolve() not in {args.input.resolve(), args.pdf.resolve()}, 'In-place output forbidden')
        require(not args.output.exists(), 'Output exists; choose a new filename')
        with zipfile.ZipFile(args.input) as src:
            infos = src.infolist(); blobs = {i.filename: src.read(i) for i in infos}; comment = src.comment
        section, body, header = (ET.fromstring(blobs[n]) for n in (TOC, BODY, HEADER))
        items = entries(section)
        pages = pdf_data(args.pdf)
        first = body_start(pages, body, report)
        map_entries(items, body, pages, first, report)
        toc_raw, header_raw = apply_layout(blobs[TOC], blobs[HEADER], section, header, items, report)
        # All lookup/layout validation completes before creating any output.
        changed = {TOC: toc_raw, HEADER: header_raw}
        with args.output.open('xb') as stream:
            with zipfile.ZipFile(stream, 'w') as dst:
                dst.comment = comment
                for info in infos: dst.writestr(info, changed.get(info.filename, blobs[info.filename]))
        with zipfile.ZipFile(args.output) as check:
            require(check.testzip() is None, 'ZIP CRC verification failed')
            preserved = [n for n in blobs if n not in changed]
            require(all(check.read(n) == blobs[n] for n in preserved), 'Untargeted member changed')
        report.update(status='succeeded', output=str(args.output), modified_members=list(changed),
                      unchanged_member_count=len(preserved),
                      section2_sha256=hashlib.sha256(blobs[BODY]).hexdigest(),
                      needs_hancom_reopen_and_pdf_visual_check=True)
    except Exception as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}')
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(args.report), 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'succeeded' else 1


if __name__ == '__main__':
    sys.exit(main())
