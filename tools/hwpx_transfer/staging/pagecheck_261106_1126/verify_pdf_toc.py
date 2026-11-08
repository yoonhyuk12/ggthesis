"""Read-only PDF/TOC check and page-number map generation; no HWPX writes.

Usage: python verify_pdf_toc.py document.hwpx document.pdf [--final]
Without --final, existing dotted TOC mismatches are reported but do not fail:
the completed JSON is for the main agent's toc_numbers_patch.py call.
"""
from pathlib import Path
import argparse, collections, html, json, re, subprocess, sys, zipfile
import pymupdf

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
FOOTER = re.compile(r'-\s*(\d+|[ivxlcdm]+)\s*-')
norm = lambda s: re.sub(r'\s+', '', s)


def locate(name):
    p = Path(name)
    return p if p.exists() else O / p


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('hwpx')
    ap.add_argument('pdf')
    ap.add_argument('--final', action='store_true')
    args = ap.parse_args()
    hp, pp = locate(args.hwpx), locate(args.pdf)
    report = {'ok': False, 'errors': [], 'input': str(pp), 'final_mode': args.final}
    def check(ok, message):
        if not ok:
            report['errors'].append(message)
    rawmap = O / (pp.stem + '_toc_raw.json')
    complete = O / (pp.stem + '_toc_completed.json')
    try:
        run = subprocess.run([sys.executable, str(ROOT / 'tools/hwpx_transfer/toc_pages_from_pdf.py'),
                              str(hp), str(pp), str(rawmap)], capture_output=True, text=True, encoding='utf8')
        report['extractor_exit'] = run.returncode
        report['extractor_stdout'] = run.stdout
        if run.returncode:
            raise RuntimeError(run.stderr)
        mapping = json.loads(rawmap.read_text(encoding='utf8'))
        xml = zipfile.ZipFile(hp).read('Contents/section1.xml').decode('utf8')
        entries = []
        for para in re.findall(r'<hp:p\b.*?</hp:p>', xml, re.S):
            if '<hp:tab' not in para:
                continue
            pre, post = para.split('<hp:tab', 1)
            title = html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)', pre))).strip()
            m = re.search(r'/>([^<]*)</hp:t>', post)
            entries.append({'title': title, 'actual': html.unescape(m[1]).strip() if m else None})
        doc = pymupdf.open(pp)
        evidence, blank, pages = [], [], []
        special = {norm(x['title']): x['title'] for x in entries
                   if norm(x['title']) in {'논문개요', '부록(도입현장)', '부록(미도입현장)'}}
        found = collections.defaultdict(list)
        for i, page in enumerate(doc):
            lines = [line.strip() for line in page.get_text().splitlines() if line.strip()]
            footer_matches = [FOOTER.fullmatch(x) for x in lines]
            numbers = [x[1] for x in footer_matches if x]
            bodylines = [x for x in lines if not FOOTER.fullmatch(x)]
            if not bodylines and not page.get_images() and not page.get_drawings():
                blank.append({'physical': i + 1, 'printed': numbers})
            headinglines = [norm(x) for x in bodylines[:5]]
            for key, title in special.items():
                if numbers and any(''.join(headinglines[:n]) == key for n in range(1, len(headinglines) + 1)):
                    number = numbers[0]
                    found[title].append(int(number) if number.isdigit() else number)
                    evidence.append({'title': title, 'physical': i + 1, 'printed': number})
            pages.append({'physical': i + 1, 'printed': numbers[0] if numbers else None,
                          'body_characters': sum(map(len, bodylines)), 'images': len(page.get_images())})
        for title in special.values():
            check(len(found[title]) == 1, 'split heading not uniquely found: ' + title)
            if len(found[title]) == 1:
                mapping['toc'][title] = found[title][0]
        complete.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf8')
        report.update(page_count=len(doc), blank_pages=blank, split_heading_evidence=evidence,
                      pages=pages, completed_map=str(complete))
        check(not blank, 'blank PDF pages present')
        want = {title: [str(n) for n in (num if isinstance(num, list) else [num])]
                for group in mapping.values() for title, num in group.items()}
        used = collections.Counter()
        for entry in entries:
            title = entry['title']
            occurrence = used[title]
            used[title] += 1
            targets = want.get(title, [])
            entry['occurrence'] = occurrence + 1
            entry['expected'] = targets[occurrence] if occurrence < len(targets) else None
            entry['match'] = entry['expected'] == entry['actual']
        missing = [e for e in entries if e['expected'] is None]
        count_mismatch = {t: {'in_hwpx': used[t], 'mapped': len(ns)} for t, ns in want.items() if used[t] != len(ns)}
        report['toc_entries'] = entries
        report['toc_mismatches'] = [x for x in entries if not x['match']]
        report['toc_occurrence_errors'] = count_mismatch
        check(not missing, 'unmapped TOC entries remain')
        check(not count_mismatch, 'TOC occurrence counts mismatch')
        if args.final:
            check(not report['toc_mismatches'], 'dotted TOC differs from actual printed page')
        report['ok'] = not report['errors']
    except Exception as exc:
        report['errors'].append(type(exc).__name__ + ': ' + str(exc))
    dest = O / (pp.stem + '_pdf_toc_verification.json')
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'errors': report['errors'], 'report': str(dest),
                      'toc_changes': len(report.get('toc_mismatches', [])), 'completed_map': str(complete)}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
