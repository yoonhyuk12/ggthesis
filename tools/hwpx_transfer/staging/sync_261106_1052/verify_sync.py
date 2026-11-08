"""Read-only HWPX checks; writes only a per-input verification JSON report.

Usage from repository root: python <this script> resaved.hwpx
No COM or HWPX mutation. PDF layout/TOC validation remains a separate gate.
"""
from pathlib import Path
import collections
import difflib
import hashlib
import html
import io
import json
import re
import sys
import zipfile
from lxml import etree as E
from PIL import Image

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
sys.path.insert(0, str(ROOT / 'tools/hwpx_transfer'))
import patch_from_fresh as p
import kjn_profile as k

HP = '{' + k.NS['hp'] + '}'
HC = '{' + k.NS['hc'] + '}'
MARKERS = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')


def load(path):
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            raise ValueError('ZIP CRC failure: ' + bad)
        raw = {n: z.read(n) for n in z.namelist()}
    parsed = {n: E.fromstring(v) for n, v in raw.items() if n.endswith(('.xml', '.hpf'))}
    return raw, parsed


def units(raw, section=2):
    return p.Units(raw[f'Contents/section{section}.xml'].decode('utf-8'), set())


def nonempty(u):
    return [p.nows(v['text']) for v in u.items if v['text']]


def front(u):
    return [p.nows(html.unescape(''.join(re.findall(
        r'<hp:t(?:\s[^>]*)?>([^<]*)', v['xml'].split('<hp:tab')[0]))))
        if '<hp:tab' in v['xml'] else p.nows(v['text']) for v in u.items if v['text']]


def differences(a, b):
    return [{'operation': op, 'actual': a[i:j], 'expected': b[x:y]}
            for op, i, j, x, y in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
            if op != 'equal']


def text(el):
    return ''.join(''.join(t.itertext()) for t in el.iter(HP + 't'))


def table_geometry(tbl):
    cells = []
    for tr in tbl.findall(HP + 'tr'):
        for tc in tr.findall(HP + 'tc'):
            a, s, size = (tc.find(HP + n) for n in ('cellAddr', 'cellSpan', 'cellSz'))
            cells.append([int(a.get('rowAddr')), int(a.get('colAddr')),
                          int(s.get('rowSpan')), int(s.get('colSpan')), int(size.get('width'))])
    return {'rows': int(tbl.get('rowCnt')), 'cols': int(tbl.get('colCnt')),
            'width': int(tbl.find(HP + 'sz').get('width')), 'cells': cells}


def table_records(raw):
    records = []
    for section in range(3):
        for idx, unit in enumerate(units(raw, section).items):
            if not unit['tbl']:
                continue
            root = E.fromstring(k._wrap(unit['xml']).encode('utf-8'))
            for nested_idx, tbl in enumerate(root.iter(HP + 'tbl')):
                records.append({'section': section, 'unit': idx, 'nested_index': nested_idx,
                                'caption': unit['cap'], 'key': p.nows(text(tbl)),
                                'geometry': table_geometry(tbl), 'element': tbl})
    return records


def grid_errors(record):
    g = record['geometry']
    errors, occupied = [], {}
    nr, nc = g['rows'], g['cols']
    # Every row, including cells continued by rowSpan, covers the declared width.
    row_cells = [[] for _ in range(nr)]
    equations = {}
    for r, c, rs, cs, width in g['cells']:
        if r < 0 or c < 0 or rs < 1 or cs < 1 or r + rs > nr or c + cs > nc:
            errors.append('cell outside declared grid')
            continue
        interval = (c, c + cs)
        if interval in equations and equations[interval] != width:
            errors.append(f'inconsistent interval width {interval}')
        equations[interval] = width
        for rr in range(r, r + rs):
            row_cells[rr].append((c, cs, width))
            for cc in range(c, c + cs):
                if (rr, cc) in occupied:
                    errors.append(f'overlap at {(rr, cc)}')
                occupied[rr, cc] = True
    if len(occupied) != nr * nc:
        errors.append(f'coverage {len(occupied)} != {nr * nc}')
    for rr, cells in enumerate(row_cells):
        if sum(w for _, _, w in cells) != g['width']:
            errors.append(f'row {rr} width sum differs from table width')
    # Widths are differences of column-boundary coordinates. Solve that graph
    # exactly; unlike per-row sums, this also checks conflicting merged spans.
    graph = collections.defaultdict(list)
    for (a, b), width in list(equations.items()) + [((0, nc), g['width'])]:
        graph[a].append((b, width)); graph[b].append((a, -width))
    coords = {}
    for start in range(nc + 1):
        if start in coords:
            continue
        coords[start] = 0
        stack = [start]
        while stack:
            a = stack.pop()
            for b, width in graph[a]:
                wanted = coords[a] + width
                if b in coords and coords[b] != wanted:
                    errors.append('inconsistent merged column widths')
                elif b not in coords:
                    coords[b] = wanted; stack.append(b)
    return sorted(set(errors))


def markercheck(raw, parsed):
    colors = {v.get('id'): v.get('textColor', '').upper()
              for v in parsed['Contents/header.xml'].iter() if v.tag.endswith('}charPr')}
    result = []
    for section in range(3):
        for pi, para in enumerate(parsed[f'Contents/section{section}.xml'].iter(HP + 'p')):
            txt, col = '', []
            for run in para.findall(HP + 'run'):
                t = ''.join(''.join(t.itertext()) for t in run.findall(HP + 't'))
                txt += t; col.extend([colors.get(run.get('charPrIDRef'))] * len(t))
            for match in MARKERS.finditer(txt):
                result.append({'section': section, 'paragraph': pi, 'text': match[0],
                               'red': all(c == '#FF0000' for c in col[match.start():match.end()])})
    return result


def imagehash(data):
    im = Image.open(io.BytesIO(data)).convert('RGBA')
    return im.size, hashlib.sha256(im.tobytes()).hexdigest()


def displayed(unit):
    """Compare text without typesetting whitespace or dotted-TOC page numbers."""
    if '<hp:tab' in unit.get('xml', ''):
        return p.nows(html.unescape(''.join(re.findall(
            r'<hp:t(?:\s[^>]*)?>([^<]*)', unit['xml'].split('<hp:tab')[0]))))
    return p.nows(html.unescape(re.sub(r'<br\s*/?>', '', unit['text'], flags=re.I)))


def expected_records(base, plan, section):
    records = units(base, section).items
    changes = {int(c['unit_index']): c for c in plan['changes'] if int(c['section']) == section}
    deleted = {int(c['unit_index']): c for c in plan.get('deletions', []) if int(c['section']) == section}
    inserted = collections.defaultdict(list)
    for c in plan.get('insertions', []):
        if int(c['section']) == section:
            inserted[int(c['after_unit_index'])].append(c)
    result = []
    for c in inserted[-1]:
        result.append({'text': c['new'], 'xml': ''})
    for i, u in enumerate(records):
        if i in deleted:
            assert p.nows(u['text']) == p.nows(deleted[i]['old']), ('delete old mismatch', section, i)
        else:
            if i in changes:
                c = changes[i]
                assert p.nows(u['text']) == p.nows(c['old']), ('change old mismatch', section, i)
                result.append({'text': c['new'], 'xml': '', 'changed': True, 'source_index': i})
            else:
                result.append(dict(u, source_index=i))
        for c in inserted[i]:
            result.append({'text': c['new'], 'xml': ''})
    tabs_plan = O / 'toc_tabs_plan.json'
    if section == 1 and tabs_plan.exists():
        targets = json.loads(tabs_plan.read_text(encoding='utf8'))['targets']
        for target in targets:
            matches = [r for r in result if r.get('source_index') == target['unit_index']]
            assert len(matches) == 1 and matches[0]['text'] == target['old_text'], 'TOC restoration source mismatch'
            matches[0].update(text=target['title'], xml='', planned_toc_tab_restore=True)
    return result


def image_records(raw, parsed):
    items = {x.get('id'): x.get('href') for x in parsed['Contents/content.hpf'].iter()
             if x.tag.endswith('}item')}
    result = []
    for section in range(3):
        for img in parsed[f'Contents/section{section}.xml'].iter(HC + 'img'):
            name = items[img.get('binaryItemIDRef')]
            result.append({'section': section, 'hash': imagehash(raw[name]), 'entry': name})
    return result


def main():
    src = Path(sys.argv[1])
    if not src.exists():
        src = O / src
    report = {'input': str(src), 'ok': False, 'errors': [],
              'scope': 'read-only ZIP/XML, planned content/order, table geometry, markers, image pixels; COM/PDF gates separate'}
    def check(ok, error):
        if not ok:
            report['errors'].append(error)
    try:
        info = json.loads((O / 'base_info.json').read_text(encoding='utf8'))
        plan = json.loads((O / 'md_diff_plan.json').read_text(encoding='utf8'))
        base, bp = load(ROOT / info['base'])
        out, op = load(src)
        report['zip_xml'] = 'PASS'
        report['content_differences'] = {}
        report['unchanged_unit_xml_differences'] = []
        for section in range(3):
            expected_units = [x for x in expected_records(base, plan, section) if displayed(x)]
            actual_units = [x for x in units(out, section).items if displayed(x)]
            expected = [displayed(x) for x in expected_units]
            actual = [displayed(x) for x in actual_units]
            ds = differences(actual, expected)
            report['content_differences'][str(section)] = ds
            check(not ds, f'section{section} planned content/order mismatch')
            if '--pre-com' in sys.argv and not ds:
                for before, after in zip(expected_units, actual_units):
                    if before.get('xml') and before['xml'] != after['xml']:
                        report['unchanged_unit_xml_differences'].append({'section': section,
                            'base_unit_index': before.get('source_index'), 'text': before['text'][:90]})
        if '--pre-com' in sys.argv:
            check(not report['unchanged_unit_xml_differences'], 'unplanned unit XML changes before COM')
        bt, ot = table_records(base), table_records(out)
        check(len(bt) == len(ot), 'table count changed')
        report['table_count'] = len(ot)
        report['table_grid_errors'] = []
        report['table_geometry_changes'] = []
        changed_tables = {(int(c['section']), int(c['unit_index'])): c
                          for c in plan['changes'] if c['kind'] == 'table'}
        for idx, rec in enumerate(ot):
            errors = grid_errors(rec)
            if errors:
                report['table_grid_errors'].append({'table_index': idx, 'caption': rec['caption'], 'errors': errors})
            if idx < len(bt):
                before = bt[idx]
                same = rec['geometry'] == before['geometry']
                change = changed_tables.get((before['section'], before['unit']))
                block = change.get('block', {}) if change else {}
                expected_rows = len(block.get('rows', [])) + 1
                expected_cols = len(block.get('header', []))
                approved = bool(change and (expected_rows != before['geometry']['rows'] or
                                             expected_cols != before['geometry']['cols']))
                if approved:
                    check(rec['geometry']['rows'] == expected_rows and rec['geometry']['cols'] == expected_cols,
                          'changed table dimensions differ from MD block: ' + str(idx))
                if not same:
                    report['table_geometry_changes'].append({'table_index': idx, 'caption': rec['caption'],
                                                             'planned_table_change': approved,
                                                             'before': before['geometry'], 'after': rec['geometry']})
                check(same or approved, 'unplanned table geometry change: ' + str(idx))
                check(before['geometry']['width'] == rec['geometry']['width'], 'table total width changed: ' + str(idx))
        check(not report['table_grid_errors'], 'table grid/width conflicts')
        check(not any(t.get('pageBreak') == 'CELL' for root in op.values() for t in root.iter(HP + 'tbl')), 'pageBreak CELL present')
        marks = markercheck(out, op)
        expected_markers = collections.Counter()
        for section in range(3):
            for rec in expected_records(base, plan, section):
                expected_markers.update(MARKERS.findall(rec['text']))
        report['markers'] = marks
        report['expected_marker_counts'] = dict(expected_markers)
        check(all(x['red'] for x in marks), 'pending marker not entirely red')
        check(collections.Counter(x['text'] for x in marks) == expected_markers, 'pending marker count mismatch')
        bi, oi = image_records(base, bp), image_records(out, op)
        expected_images = [x['hash'] for x in bi]
        replacements_file = O / 'image_replacements.json'
        image_replacements = json.loads(replacements_file.read_text(encoding='utf8')) if replacements_file.exists() else []
        for replacement in image_replacements:
            matches = [i for i, item in enumerate(bi) if item['entry'] == replacement['entry']]
            check(len(matches) == 1, 'planned image replacement does not uniquely identify a base picture')
            for i in matches:
                expected_images[i] = imagehash((ROOT / replacement['source']).read_bytes())
        report['image_replacements'] = image_replacements
        report['planned_image_pixel_sequence_matches'] = expected_images == [x['hash'] for x in oi]
        check(report['planned_image_pixel_sequence_matches'], 'image pixel sequence differs from baseline plus planned replacements')
        actual_hashes = [x['hash'] for x in oi]
        image_checks = []
        for chapter in range(1, 6):
            blockfile = O / f'ch{chapter:02}.blocks.json'
            if not blockfile.exists():
                continue
            grouped = k.group_figures(json.loads(blockfile.read_text(encoding='utf8'))['blocks'])
            for fig in grouped:
                if fig.get('type') == '_figure' and fig.get('image_md'):
                    f = ROOT / '01.docs' / fig['image_md'][1]
                    image_checks.append({'caption': fig.get('caption'), 'path': str(f.relative_to(ROOT)),
                                         'match': imagehash(f.read_bytes()) in actual_hashes})
        report['MD_image_checks'] = image_checks
        check(all(x['match'] for x in image_checks), 'current MD image absent or different')
        check(hashlib.sha256((ROOT / info['base']).read_bytes()).hexdigest() == info['sha256'], 'baseline hash changed')
        report['MD_hash_changes'] = [name for name, digest in info['md_sha256'].items()
                                     if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
        check(not report['MD_hash_changes'], 'MD changed since input snapshot')
        report['ok'] = not report['errors']
    except Exception as exc:
        report['errors'].append(type(exc).__name__ + ': ' + str(exc))
    dest = O / (src.stem + '_sync_verification.json')
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'errors': report['errors'], 'report': str(dest)}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())

