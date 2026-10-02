"""Read-only current-TOC/printed-folio mapper. Never writes HWPX/PDF."""
import argparse
import collections
import json
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
import fitz
from lxml import etree as E

Q = Path(__file__).resolve().parent
P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H = '{http://www.hancom.co.kr/hwpml/2011/head}'


def norm(text):
    # Whitespace only: do not silently equate different punctuation/content.
    return re.sub(r'\s+', '', text)


def own(p):
    return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))


def roots(path):
    with zipfile.ZipFile(path, 'r') as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        names = sorted((n for n in z.namelist() if re.fullmatch(r'Contents/section\d+\.xml', n)),
                       key=lambda n: int(re.search(r'\d+', n)[0]))
        return {n: E.fromstring(z.read(n)) for n in names}


def output(name, value):
    path = Path(name).resolve()
    if path.parent != Q or not path.name.startswith('qa_') or path.suffix != '.json':
        raise ValueError('Outputs must be qa_*.json in the script directory')
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def current_toc(hwpx):
    rows = []
    for sec, root in roots(hwpx).items():
        for idx, p in enumerate(root.iter(P+'p')):
            # Canonical idx counts ALL descendant paragraphs, including tables.
            if not any(t.find(P+'tab') is not None for r in p.findall(P+'run') for t in r.findall(P+'t')):
                continue
            text = own(p)
            m = re.fullmatch(r'(.*?)(\d+)\s*', text)
            if m:
                rows.append(dict(section=sec, idx=idx, title=m[1], current_folio=int(m[2]), text=text))
    return rows


def pdf_pages(pdf):
    result = []
    with fitz.open(pdf) as doc:
        for n, page in enumerate(doc):
            lines = [dict(text=''.join(s['text'] for s in line['spans']), bbox=list(line['bbox']))
                     for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines']]
            # Geometry locates the candidate zone; the folio itself is read, never derived from an offset.
            footers = []
            for line in lines:
                m = re.fullmatch(r'\s*[-–—]\s*(\d+|[ivxlcdmIVXLCDM]+)\s*[-–—]\s*', line['text'])
                if m and line['bbox'][1] > page.rect.height * .80:
                    footers.append(dict(text=line['text'], folio=m[1], bbox=line['bbox']))
            printed = int(footers[0]['folio']) if len(footers) == 1 and footers[0]['folio'].isdigit() else None
            body_lines = [l for l in lines if not any(l['bbox'] == f['bbox'] for f in footers)]
            result.append(dict(physical=n+1, printed=printed, footer_candidates=footers,
                               width=page.rect.width, height=page.rect.height, lines=body_lines))
    return result


def heading_hits(pages, text):
    goal = norm(text)
    hits = []
    for page in pages:
        # TOC titles may be separate PDF lines from their dotted leaders/numbers.
        # Roman-folio front matter must never win over a later body heading.
        if any(not f['folio'].isdigit() for f in page['footer_candidates']):
            continue
        lines = page['lines']
        for j, line in enumerate(lines):
            value = ''
            for end in lines[j:j+16]:
                value += norm(end['text'])
                if value == goal:
                    hits.append(dict(physical=page['physical'], printed=page['printed'], y=line['bbox'][1]))
                    break
                if len(value) >= len(goal):
                    break
    return hits


def mapping(base, pdf, targets, final=None):
    toc = current_toc(base)
    expected = json.loads(Path(targets).read_text(encoding='utf-8'))
    pages = pdf_pages(pdf)
    hidden_evidence = []
    for section, root in roots(final or base).items():
        first = next(root.iter(P+'p'), None)
        if first is None:
            continue
        reset = next((n for n in first.iter(P+'newNum') if n.get('numType') == 'PAGE'), None)
        hidden = next((n for n in first.iter(P+'pageHiding') if n.get('hidePageNum') == '1'), None)
        if reset is None or hidden is None or not own(first).strip():
            continue
        candidates = heading_hits(pages, own(first))
        start = int(reset.get('num'))
        if len(candidates) == 1:
            hit = candidates[0]
            k = hit['physical']-1
            if pages[k]['printed'] is None and k+1 < len(pages) and pages[k+1]['printed'] == start+1:
                pages[k]['printed'] = start
                hidden_evidence.append(dict(section=section,heading=own(first),physical=k+1,printed=start,
                                            evidence='first paragraph PAGE newNum + hidePageNum + unique heading + next detected footer',
                                            next_physical=k+2,next_printed=pages[k+1]['printed']))
    mismatches = [dict(position=i, source=x['title'], target=y['toc_title'])
                  for i, (x, y) in enumerate(zip(toc, expected)) if norm(x['title']) != norm(y['toc_title'])]
    source_ok = len(toc) == len(expected) and not mismatches
    report = dict(source_toc_count=len(toc), expected_target_count=len(expected), source_titles_match=source_ok,
                  source_title_mismatches=mismatches, entries=[], recommended_changes=[], unresolved=[],hidden_folio_evidence=hidden_evidence,
                  footer_detection=[{k: p[k] for k in ('physical', 'printed', 'footer_candidates')} for p in pages],
                  limitations=['No physical/printed offset is assumed; hidden folios require explicit XML reset/hiding and next-page evidence.',
                               'Repeated captions require first-start confirmation from table/body evidence.',
                               'An undetected footer remains unresolved; this tool never writes HWPX.'])
    if not source_ok:
        report['unresolved'].append({'reason': 'source TOC and targets differ; positional mapping refused'})
        return report
    last = {}
    final_toc = current_toc(final) if final else toc
    report['final_toc_titles_match'] = len(final_toc) == len(toc) and all(norm(a['title']) == norm(b['title']) for a,b in zip(toc,final_toc))
    for i, (row, target) in enumerate(zip(toc, expected)):
        previous = last.get(target['kind'], (0, -1))
        hits = [h for h in heading_hits(pages, target['body_text']) if (h['physical'], h['y']) > previous]
        # A dotted TOC line includes a trailing number and cannot equal the bare heading.
        chosen = min(hits, key=lambda h: (h['physical'], h['y'])) if hits else None
        item = {**row, 'kind': target['kind'], 'body_text': target['body_text'], 'candidates': hits, 'selected': chosen}
        if chosen:
            last[target['kind']] = chosen['physical'], chosen['y']
        if not chosen or chosen['printed'] is None:
            report['unresolved'].append({**item, 'reason': 'heading absent' if not chosen else 'printed footer not detected'})
        else:
            actual = final_toc[i]['current_folio'] if report['final_toc_titles_match'] else None
            item['final_current_folio'] = actual
            item['first_start_requires_review'] = target['kind'] in ('table', 'figure') and len(hits) > 1
            if actual != chosen['printed']:
                report['recommended_changes'].append(dict(section=row['section'], idx=row['idx'], title=row['title'],
                                                         old=actual, recommended=chosen['printed'], physical=chosen['physical']))
        report['entries'].append(item)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--final')
    parser.add_argument('--targets', default=str(Q.parent/'update_260930_1323/toc_targets.json'))
    parser.add_argument('--out', default=str(Q/'qa_toc_report.json'))
    args = parser.parse_args()
    report = mapping(args.base, args.pdf, args.targets, args.final)
    output(args.out, report)
    print(json.dumps({k: report[k] for k in ('source_toc_count','expected_target_count','source_titles_match')}, ensure_ascii=False))
    print('recommended', len(report['recommended_changes']), 'unresolved', len(report['unresolved']))
    return 0 if report['source_titles_match'] and not report['unresolved'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
