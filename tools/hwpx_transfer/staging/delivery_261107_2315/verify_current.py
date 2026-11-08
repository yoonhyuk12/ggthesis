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


def main():
    name = Path(sys.argv[1] if len(sys.argv) > 1 else 'resaved.hwpx')
    src = name if name.exists() else O / name
    report = {'input': str(src), 'ok': False, 'errors': [],
              'scope': 'ZIP/XML/content/geometry only; COM and PDF checks are separate'}
    def check(condition, message):
        if not condition:
            report['errors'].append(message)
    try:
        info = json.loads((O / 'base_info.json').read_text(encoding='utf-8'))
        base, _ = load(ROOT / info['base'])
        fresh, fp = load(O / 'fresh.hwpx')
        out, parsed = load(src)
        report['zip_xml'] = 'PASS'
        nu, fu = units(out), units(fresh)
        report['body_differences'] = differences(nonempty(nu), nonempty(fu))
        check(not report['body_differences'], 'section2 text/order differs from current assembly; inspect merged-cell text if applicable')
        report['front_differences'] = differences(front(units(out, 1)), front(units(fresh, 1)))
        check(not report['front_differences'], 'section1 titles/thanks/abstract mismatch (pagination excluded)')
        structure = lambda u: [p.nows(v['text']) for v in u.items if not v['tbl'] and
                              re.match(r'^제\s*\d+\s*(장|절|항)|^<(표|그림)\s*\d+-\d+>', v['text'])]
        check(structure(nu) == structure(fu), 'heading/caption order mismatch')
        report['structure_items'] = len(structure(nu))
        bt, ft, ot = table_records(base), table_records(fresh), table_records(out)
        grid = []
        for rec in ot:
            errors = grid_errors(rec)
            if errors:
                grid.append({key: rec[key] for key in ('section', 'unit', 'nested_index', 'caption')} | {'errors': errors})
        report['table_grid_errors'] = grid
        check(not grid, 'table grid/width errors')
        preservation = []
        for rec in ot:
            matches = [b for b in bt if b['key'] == rec['key'] and b['nested_index'] == rec['nested_index']]
            if matches:
                same = any(b['geometry'] == rec['geometry'] for b in matches)
                preservation.append({'caption': rec['caption'], 'nested_index': rec['nested_index'], 'preserved': same})
                check(same, 'same-content table geometry changed: ' + rec['caption'])
        report['same_content_table_preservation'] = preservation
        expected_cols = {'<표4-10>': 7, '<표4-12>': 8, '<표4-13>': 7, '<표4-14>': 6}
        for cap, cols in expected_cols.items():
            actual = [r for r in ot if r['section'] == 2 and r['caption'] == cap and r['nested_index'] == 0]
            check(len(actual) == 1 and actual[0]['geometry']['cols'] == cols, f'{cap} expected {cols} columns')
        for rec in ot:
            if rec['section'] == 2 and (rec['caption'] in expected_cols or rec['caption'] == '<표4-11>'):
                fm = [r for r in ft if r['section'] == 2 and r['caption'] == rec['caption'] and r['nested_index'] == rec['nested_index']]
                check(len(fm) == 1 and rec['geometry']['rows'] == fm[0]['geometry']['rows'] and
                      rec['geometry']['cols'] == fm[0]['geometry']['cols'], 'changed table dimensions differ from fresh: ' + rec['caption'])
        report['table_count'] = len(ot)
        check(not any(tbl.get('pageBreak') == 'CELL' for root in parsed.values() for tbl in root.iter(HP + 'tbl')), 'pageBreak CELL present')
        actual, expected = markercheck(out, parsed), markercheck(fresh, fp)
        report['markers_actual'], report['markers_expected'] = actual, expected
        check(all(v['red'] for v in actual), 'non-red pending marker')
        check(collections.Counter(v['text'] for v in actual) == collections.Counter(v['text'] for v in expected), 'marker occurrence mismatch')
        manifest = parsed['Contents/content.hpf']
        items = {v.get('id'): v.get('href') for v in manifest.iter() if v.tag.endswith('}item')}
        pics = [imagehash(out[items[v.get('binaryItemIDRef')]]) for v in parsed['Contents/section2.xml'].iter(HC + 'img')]
        imagechecks = [{'caption': v['caption_prefix'], 'match': imagehash((ROOT / v['source']).read_bytes()) in pics}
                       for v in json.loads((O / 'images.json').read_text(encoding='utf-8'))['mapping']]
        report['images'] = imagechecks
        check(all(v['match'] for v in imagechecks), 'current MD image absent or different pixels')
        check(hashlib.sha256((ROOT / info['base']).read_bytes()).hexdigest() == info['sha256'], 'base hash changed')
        md_changed = [n for n, digest in json.loads((O/'md_hashes.json').read_text(encoding='utf8')).items() if hashlib.sha256((ROOT / n).read_bytes()).hexdigest() != digest]
        report['MD_changed'] = md_changed
        check(not md_changed, 'MD changed since input snapshot')
        report['ok'] = not report['errors']
    except Exception as exc:
        report['errors'].append(type(exc).__name__ + ': ' + str(exc))
    dest = O / (src.stem + '_verification.json')
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'report': str(dest), 'errors': report['errors']}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
