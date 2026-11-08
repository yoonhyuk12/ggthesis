"""Read-only final HWPX/PDF checks; writes JSON and contact sheet only."""
from pathlib import Path
import argparse, collections, hashlib, html, json, re, sys
import pymupdf
from PIL import Image, ImageDraw
import verify_current as v

O = Path(__file__).resolve().parent
ROOT = O.parents[3]


def locate(s):
    p = Path(s)
    return p if p.exists() else O / p


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('hwpx', nargs='?', default='final.hwpx')
    ap.add_argument('pdf', nargs='?', default='final.pdf')
    ap.add_argument('--toc-json', default='final_toc.json', help='toc_pages_from_pdf.py output for final PDF')
    ap.add_argument('--expected', default='toc_completed.json')
    ap.add_argument('--allow-changed', default='4,5,6,7,8,9,10,31,32,33,34,35', help='physical pages intentionally changed')
    args = ap.parse_args()
    report = {'ok': False, 'errors': [], 'scope': 'read-only HWPX/PDF verification'}
    def check(ok, message):
        if not ok:
            report['errors'].append(message)
    try:
        expected = json.loads(locate(args.expected).read_text(encoding='utf8'))
        actual = json.loads(locate(args.toc_json).read_text(encoding='utf8'))
        final = pymupdf.open(locate(args.pdf))
        before = pymupdf.open(O / 'resaved.pdf')
        # These split-line headings are omitted by the standard extractor.
        special = {'논문개요', '부록(도입현장)', '부록(미도입현장)'}
        evidence = []
        for title in expected['toc']:
            key = re.sub(r'\s+', '', title)
            if key not in special:
                continue
            hits = []
            for i, page in enumerate(final):
                lines = [x.strip() for x in page.get_text().splitlines() if x.strip()]
                page_numbers = [m.group(1) for x in lines if (m := re.fullmatch(r'-\s*(\d+|[ivxlcdm]+)\s*-', x))]
                heading_lines = [re.sub(r'\s+', '', x) for x in lines[:5] if not re.fullmatch(r'-\s*(\d+|[ivxlcdm]+)\s*-', x)]
                # Require complete heading lines, not a TOC line starting with
                # the same title followed by leader dots and a page number.
                exact_heading = any(''.join(heading_lines[:n]) == key for n in range(1, len(heading_lines) + 1))
                if exact_heading and page_numbers:
                    n = page_numbers[0]
                    hits.append(int(n) if n.isdigit() else n)
                    evidence.append({'title': title, 'physical': i + 1, 'printed': n})
            check(len(hits) == 1, 'split heading not uniquely found: ' + title)
            if len(hits) == 1:
                actual['toc'][title] = hits[0]
        report['split_heading_evidence'] = evidence
        (O / 'final_toc_completed.json').write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding='utf8')
        differences = []
        for kind in ('toc', 'lot', 'lof'):
            for title in expected[kind].keys() | actual[kind].keys():
                if expected[kind].get(title) != actual[kind].get(title):
                    differences.append({'kind': kind, 'title': title, 'expected': expected[kind].get(title), 'actual': actual[kind].get(title)})
        report['pdf_toc_differences'] = differences
        check(not differences, 'final PDF targets changed; update TOC and resave')

        raw, parsed = v.load(locate(args.hwpx))
        want = {t: [str(x) for x in (n if isinstance(n, list) else [n])] for group in expected.values() for t, n in group.items()}
        used = collections.Counter()
        entries = []
        xml = raw['Contents/section1.xml'].decode('utf8')
        for para in re.findall(r'<hp:p\b.*?</hp:p>', xml, re.S):
            if '<hp:tab' not in para:
                continue
            pre, post = para.split('<hp:tab', 1)
            title = html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)', pre))).strip()
            match = re.search(r'/>([^<]*)</hp:t>', post)
            num = html.unescape(match.group(1)).strip() if match else None
            index = used[title]
            used[title] += 1
            target = want.get(title, [])
            ok = index < len(target) and num == target[index]
            entries.append({'title': title, 'occurrence': index + 1, 'actual': num, 'expected': target[index] if index < len(target) else None, 'match': ok})
        report['hwpx_toc_entries'] = entries
        check(len(entries) == 117, 'expected 117 dotted TOC entries')
        check(all(e['match'] for e in entries), 'HWPX dotted TOC page mismatch')
        check(all(used[t] == len(ns) for t, ns in want.items()), 'TOC occurrence counts mismatch')

        fresh, fp = v.load(O / 'fresh.hwpx')
        marks, expected_marks = v.markercheck(raw, parsed), v.markercheck(fresh, fp)
        report['markers'] = marks
        check(all(x['red'] for x in marks), 'non-red pending marker')
        check(collections.Counter(x['text'] for x in marks) == collections.Counter(x['text'] for x in expected_marks), 'pending marker count mismatch')
        info = json.loads((O / 'base_info.json').read_text(encoding='utf8'))
        check(hashlib.sha256((ROOT / info['base']).read_bytes()).hexdigest() == info['sha256'], 'base hash changed')
        report['MD_changed'] = [p for p, h in info['md_sha256'].items() if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
        check(not report['MD_changed'], 'MD hash changed')

        allowed = {int(x) for x in args.allow_changed.split(',') if x}
        check(len(final) == len(before), 'PDF page count changed')
        hashes = []
        changed = []
        for i in range(min(len(final), len(before))):
            pair = []
            for doc in (before, final):
                pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(1, 1), alpha=False)
                pair.append(hashlib.sha256(str((pix.width, pix.height)).encode() + pix.samples).hexdigest())
            hashes.append({'physical': i + 1, 'before': pair[0], 'after': pair[1]})
            if pair[0] != pair[1]:
                changed.append(i + 1)
        report.update(page_counts={'before': len(before), 'final': len(final)}, page_pixel_hashes=hashes, changed_physical_pages=changed, allowed_changed_physical_pages=sorted(allowed))
        check(set(changed) <= allowed, 'unexpected PDF pixel changes: ' + str(sorted(set(changed) - allowed)))
        sheet = Image.new('RGB', (4 * 360, 2 * 535), 'white')
        draw = ImageDraw.Draw(sheet)
        for j, physical in enumerate(range(4, 11)):
            pix = final[physical - 1].get_pixmap(matrix=pymupdf.Matrix(.7, .7), alpha=False)
            im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            im.thumbnail((350, 500))
            x, y = (j % 4) * 360, (j // 4) * 535
            draw.text((x + 5, y + 5), 'Physical page ' + str(physical), fill='black')
            sheet.paste(im, (x + 5, y + 25))
        sheet.save(O / 'final_front_contact.png')
    except Exception as exc:
        report['errors'].append(type(exc).__name__ + ': ' + str(exc))
    report['ok'] = not report['errors']
    dest = O / 'final_checks.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'errors': report['errors'], 'report': str(dest)}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
