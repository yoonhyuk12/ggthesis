"""Read-only QA evidence; exit 0 means machine checks pass, NEVER final visual approval."""
import argparse
import collections
import difflib
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
import fitz
from PIL import Image, ImageDraw
from lxml import etree as E
import qa_toc as T

Q, P, H = T.Q, T.P, T.H
MARK = re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def nearest(element, tag):
    return next((p for p in element.iterancestors() if p.tag == P+tag), None)


def inspect(path):
    roots = T.roots(path)
    with zipfile.ZipFile(path, 'r') as z:
        header = E.fromstring(z.read('Contents/header.xml'))
        colors = {c.get('id'): c.get('textColor', '').upper() for c in header.iter(H+'charPr')}
        media = sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('BinData/'))
    paragraphs, tables, markers, ordinary_red, invalid_markers = [], [], [], [], []
    for sec, root in roots.items():
        ps = list(root.iter(P+'p'))
        indices = {p: i for i, p in enumerate(ps)}
        ts = list(root.iter(P+'tbl'))
        table_ids = {t: f'{sec}:table:{i}' for i, t in enumerate(ts)}
        for idx, p in enumerate(ps):
            text = T.own(p)
            is_toc = any(t.find(P+'tab') is not None for r in p.findall(P+'run') for t in r.findall(P+'t')) and bool(re.search(r'\d+\s*$',text))
            row = dict(section=sec, idx=idx, text=text, in_table=nearest(p, 'tc') is not None, is_toc=is_toc)
            paragraphs.append(row)
            chars = []
            for r in p.findall(P+'run'):
                value = ''.join(''.join(t.itertext()) for t in r.findall(P+'t'))
                chars.extend([colors.get(r.get('charPrIDRef'), 'UNRESOLVED')]*len(value))
            spans = list(MARK.finditer(text))
            for m in spans:
                markers.append(dict(section=sec, idx=idx, text=m.group(), start=m.start(),
                                    colors=sorted(set(chars[m.start():m.end()])),
                                    red=all(c == '#FF0000' for c in chars[m.start():m.end()])))
            for m in re.finditer(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)', text):
                if not any(a.start() == m.start() for a in spans):
                    invalid_markers.append(dict(section=sec, idx=idx, text=text, reason='unclosed marker'))
            for m in re.finditer(r'\[[^\]]*\]', text):
                if not any(a.start() <= m.start() < a.end() for a in spans) and any(c == '#FF0000' for c in chars[m.start():m.end()]):
                    ordinary_red.append(dict(section=sec, idx=idx, text=m.group(), colors=sorted(set(chars[m.start():m.end()]))))
        for ti, table in enumerate(ts):
            cells = []
            occupancy, errors, edges = {}, [], {}
            rows, cols = int(table.get('rowCnt')), int(table.get('colCnt'))
            width = int(table.find(P+'sz').get('width'))
            for tr in table.findall(P+'tr'):
                for tc in tr.findall(P+'tc'):
                    addr, span, size = (tc.find(P+tag) for tag in ('cellAddr', 'cellSpan', 'cellSz'))
                    rr, cc = int(addr.get('rowAddr')), int(addr.get('colAddr'))
                    rs, cs = int(span.get('rowSpan')), int(span.get('colSpan'))
                    w = int(size.get('width'))
                    texts = [T.own(p) for p in tc.iter(P+'p') if nearest(p, 'tc') is tc and T.own(p)]
                    cells.append(dict(row=rr, col=cc, rowSpan=rs, colSpan=cs, width=w,
                                      text=texts, header=tc.get('header'),
                                      paragraph_indices=[indices[p] for p in tc.iter(P+'p') if nearest(p, 'tc') is tc]))
                    for y in range(rr, rr+rs):
                        for x in range(cc, cc+cs):
                            if (y,x) in occupancy:
                                errors.append(f'overlap {y},{x}')
                            if not (0 <= y < rows and 0 <= x < cols):
                                errors.append(f'out of range {y},{x}')
                            occupancy[y,x] = (rr,cc)
                    # Boundaries solve merged-width constraints without dividing a merged cell uniformly.
                    edges.setdefault(cc, []).append((cc+cs, w))
                    edges.setdefault(cc+cs, []).append((cc, -w))
            for y in range(rows):
                for x in range(cols):
                    if (y,x) not in occupancy:
                        errors.append(f'hole {y},{x}')
            positions = {0: 0, cols: width}
            stack = [0, cols]
            while stack:
                start = stack.pop()
                for end, distance in edges.get(start, []):
                    value = positions[start]+distance
                    if end in positions and positions[end] != value:
                        errors.append(f'width constraint conflict {start}:{end}')
                    elif end not in positions:
                        positions[end] = value
                        stack.append(end)
            known = sorted(positions)
            if any(positions[b] <= positions[a] for a,b in zip(known, known[1:])):
                errors.append('nonpositive column width')
            if table.get('pageBreak') == 'CELL':
                errors.append('forbidden pageBreak=CELL')
            tables.append(dict(key=table_ids[table], section=sec, table=ti, rows=rows, cols=cols,
                               width=width, cells=cells, grid_errors=sorted(set(errors)),
                               column_boundaries=positions, unresolved_boundaries=sorted(set(range(cols+1))-set(positions)),
                               parent=table_ids.get(nearest(table, 'tbl')),
                               context_before=[T.own(p) for p in ps[:indices[next(table.iter(P+'p'))]]
                                               if T.own(p) and nearest(p,'tc') is None][-3:],
                               context_after=[T.own(p) for p in ps[indices[list(table.iter(P+'p'))[-1]]+1:]
                                              if T.own(p) and nearest(p,'tc') is None][:3]))
    return dict(paragraphs=paragraphs, tables=tables, markers=markers, ordinary_brackets_red=ordinary_red,
                malformed_markers=invalid_markers, media_hashes=media,
                pictures=sum(len(list(r.iter(P+'pic'))) for r in roots.values()))


def table_signature(table):
    return dict(rows=table['rows'], cols=table['cols'], width=table['width'], parent=table['parent'],
                cells=[{k:c[k] for k in ('row','col','rowSpan','colSpan','width','text')} for c in table['cells']])


def compare_tables(a, b):
    return dict(count_before=len(a), count_after=len(b), exact_preserved=len(a)==len(b) and
                all(table_signature(x)==table_signature(y) for x,y in zip(a,b)),
                changed=[x['key'] for x,y in zip(a,b) if table_signature(x)!=table_signature(y)])


def content_rows(doc):
    return [(p['section'],p['text']) for p in doc['paragraphs'] if p['text'] and not p['is_toc']]


def pdf_stream(page, clip=None):
    lines = [dict(text=''.join(s['text'] for s in line['spans']), bbox=list(line['bbox']))
             for block in page.get_text('dict', clip=clip)['blocks'] if 'lines' in block for line in block['lines']]
    text, chars = '', []
    for line in lines:
        value = T.norm(line['text'])
        text += value
        chars.extend([line['bbox']]*len(value))
    return text, chars


def occurrences(stream, phrase):
    text, boxes = stream
    goal = T.norm(phrase)
    result = []
    if not goal:
        return result
    offset = 0
    while (start := text.find(goal, offset)) >= 0:
        used = boxes[start:start+len(goal)]
        result.append([min(b[0] for b in used),min(b[1] for b in used),max(b[2] for b in used),max(b[3] for b in used)])
        offset = start+len(goal)
    return result


def pdf_qa(pdf, current, edited, regions, render):
    pages = T.pdf_pages(pdf)
    records, samples, table_pages = [], [], set()
    with fitz.open(pdf) as doc:
        streams = [pdf_stream(p) for p in doc]
        # Long unique cell paragraphs anchor a table; repeated short placeholders cannot anchor it.
        phrases = collections.Counter(T.norm(s) for t in current['tables'] for c in t['cells'] for s in c['text'])
        cache = {}
        def hits(s):
            s = T.norm(s)
            if s not in cache:
                cache[s] = [(i+1, box) for i, stream in enumerate(streams) for box in occurrences(stream, s)]
            return cache[s]
        for table in current['tables']:
            explicit = regions.get(table['key'])
            anchors = []
            for cell in table['cells']:
                for s in cell['text']:
                    if len(T.norm(s)) >= 12 and phrases[T.norm(s)] == 1 and len(hits(s)) == 1:
                        anchors.append(dict(text=s, page=hits(s)[0][0], bbox=hits(s)[0][1]))
            context_anchors = []
            if not anchors:
                for side in ('context_before','context_after'):
                    for s in table[side]:
                        candidates = [(p,b) for p,b in hits(s) if not any(not f['folio'].isdigit() for f in pages[p-1]['footer_candidates'])]
                        if len(candidates) == 1:
                            context_anchors.append(dict(text=s,page=candidates[0][0],bbox=candidates[0][1],side=side))
            if explicit:
                selected = sorted({int(r['page']) for r in explicit})
                local_streams = [(int(r['page']), pdf_stream(doc[int(r['page'])-1], fitz.Rect(r['bbox']))) for r in explicit]
                method = 'explicit_reviewed_regions'
            elif anchors or context_anchors:
                # Guard pages cover possible first/last-row continuations; bounds are deliberately not certified.
                evidence = anchors or context_anchors
                first, last = min(a['page'] for a in evidence), max(a['page'] for a in evidence)
                selected = list(range(max(1, first-1), min(len(doc), last+1)+1))
                local_streams = [(p,streams[p-1]) for p in selected]
                method = 'unique_cell_anchors_plus_guard_pages' if anchors else 'surrounding_body_context_plus_guard_pages'
            else:
                selected = list(range(1,len(doc)+1))
                local_streams = []
                method = 'unlocalized_all_pages_queued_for_review'
            table_pages.update(selected)
            cells = []
            for cell in table['cells']:
                needed = collections.Counter(T.norm(s) for s in cell['text'] if T.norm(s))
                checks = []
                for s, count in needed.items():
                    found = [dict(page=p,bbox=b) for p,stream in local_streams for b in occurrences(stream,s)]
                    end = s[-min(24,len(s)):]
                    tails = [dict(page=p,bbox=b) for p,stream in local_streams for b in occurrences(stream,end)]
                    checks.append(dict(text=s, expected_in_cell=count, actual_in_local_regions=len(found),
                                       full_text_hits=found[:12], full_text_hit_pages=sorted({h['page'] for h in found}),
                                       end_text=end, end_hits=tails[:12], end_hit_count=len(tails),
                                       status='missing_or_extraction_order' if len(found)<count else 'found_requires_cell_visual_confirmation'))
                cells.append(dict(row=cell['row'],col=cell['col'],checks=checks))
            expected_markers = collections.Counter(T.norm(m.group()) for c in table['cells'] for s in c['text'] for m in MARK.finditer(s))
            marker_checks = []
            for s,count in expected_markers.items():
                found = [dict(page=p,bbox=b) for p,stream in local_streams for b in occurrences(stream,s)]
                marker_checks.append(dict(text=s,expected=count,actual=len(found),hits=found[:12],hit_pages=sorted({h['page'] for h in found}),
                                          note='Repeated headers and neighboring content need explicit region review; surplus is not silently accepted.'))
            records.append(dict(key=table['key'],parent=table['parent'],method=method,pages=selected,
                                anchors=anchors,context_anchors=context_anchors,cells=cells,marker_multiplicities=marker_checks,
                                visual_status='pending',localization_certified=bool(explicit)))
        # Edited paragraph samples use full text, then first/last fragments if wrapping crosses pages.
        for item in edited:
            s = item['text']
            found = hits(s) if s else []
            sample = dict(section=item['section'],idx=item['idx'],text=s,full_hits=[dict(page=p,bbox=b) for p,b in found])
            sample['fragment_hits'] = [] if found else [dict(fragment=part,hits=[dict(page=p,bbox=b) for p,b in hits(part)]) for part in (T.norm(s)[:40],T.norm(s)[-40:]) if part]
            samples.append(sample)
        sample_pages = {h['page'] for s in samples for h in s['full_hits']}
        sample_pages.update(h['page'] for s in samples for f in s['fragment_hits'] for h in f['hits'])
        footer_warnings = []
        for page in pages:
            if not page['footer_candidates']:
                footer_warnings.append(dict(page=page['physical'],reason='footer_not_detected'))
                continue
            y = min(f['bbox'][1] for f in page['footer_candidates'])
            offenders = [l for l in page['lines'] if l['bbox'][3] >= y and l['text'].strip()]
            # Drawing checks catch a table border entering the observed footer band.
            lines = [list(d['rect']) for d in doc[page['physical']-1].get_drawings()
                     if d['rect'].y1 >= y and d['rect'].y0 < y]
            if offenders or lines:
                footer_warnings.append(dict(page=page['physical'],reason='possible_footer_overlap',footer_y=y,text=offenders,drawings=lines))
        outputs = []
        selected = sorted(table_pages | sample_pages)
        if render:
            thumbs = []
            for page_no in selected:
                pix = doc[page_no-1].get_pixmap(matrix=fitz.Matrix(1.4,1.4), alpha=False)
                path = Q/f'qa_page_{page_no:03d}.png'
                pix.save(path)
                outputs.append(path.name)
                im = Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                im.thumbnail((290,420))
                tile = Image.new('RGB',(310,450),'white')
                tile.paste(im,((310-im.width)//2,25))
                ImageDraw.Draw(tile).text((10,5),f'PDF {page_no} | printed {pages[page_no-1]["printed"]}',fill='black')
                thumbs.append(tile)
            for start in range(0,len(thumbs),12):
                sheet = Image.new('RGB',(1240,1350),'#dddddd')
                for i,tile in enumerate(thumbs[start:start+12]):
                    sheet.paste(tile,((i%4)*310,(i//4)*450))
                path = Q/f'qa_contact_{start//12+1:02d}.png'
                sheet.save(path)
                outputs.append(path.name)
        return dict(pages=len(doc),tables=records,edited_samples=samples,table_pages=sorted(table_pages),
                    edited_sample_pages=sorted(sample_pages),footer_warnings=footer_warnings,artifacts=outputs,
                    figure_pdf_evidence=[dict(page=i+1,image_count=len(p.get_images()),drawing_count=len(p.get_drawings())) for i,p in enumerate(doc)],
                    all_table_visual_review='pending',rendered=render)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--expected',required=True,help='Candidate HWPX BEFORE COM reflow')
    parser.add_argument('--final',required=True,help='Reflowed/final HWPX')
    parser.add_argument('--pdf',required=True)
    parser.add_argument('--regions',help='Optional manually reviewed table-key -> [{page:1,bbox:[x0,y0,x1,y1]}]')
    parser.add_argument('--source-manifest',default=str(Q/'source.json'))
    parser.add_argument('--targets',default=str(Q.parent/'update_260930_1323/toc_targets.json'))
    parser.add_argument('--out',default=str(Q/'qa_report.json'))
    parser.add_argument('--no-render',action='store_true')
    args = parser.parse_args()
    paths = [Path(p) for p in (args.base,args.expected,args.final,args.pdf)]
    before = {str(p):digest(p) for p in paths}
    base,expected,current = (inspect(p) for p in paths[:3])
    a,b = content_rows(expected), content_rows(current)
    diff = list(difflib.unified_diff([f'{s} {t}' for s,t in a],[f'{s} {t}' for s,t in b],n=1))
    seq_a, seq_b = [p for p in base['paragraphs'] if p['text']], [p for p in expected['paragraphs'] if p['text']]
    matcher = difflib.SequenceMatcher(a=[(p['section'],p['text']) for p in seq_a],b=[(p['section'],p['text']) for p in seq_b],autojunk=False)
    edited = [p for tag,i,j,k,l in matcher.get_opcodes() if tag!='equal' for p in seq_b[k:l] if not p['in_table'] and p['section']!='Contents/section1.xml']
    report = dict(inputs=before, body_exact_nonempty_paragraphs=a==b,
                  body_whitespace_normalized=''.join(T.norm(t) for _,t in a)==''.join(T.norm(t) for _,t in b),
                  body_diff=diff, edited_candidate_paragraph_count=len(edited),
                  table_base_to_candidate=compare_tables(base['tables'],expected['tables']),
                  table_candidate_to_final=compare_tables(expected['tables'],current['tables']),
                  grids=[{k:t[k] for k in ('key','grid_errors','column_boundaries','unresolved_boundaries')} for t in current['tables']],
                  marker_colors_wrong=[m for m in current['markers'] if not m['red']],
                  malformed_markers=current['malformed_markers'],ordinary_brackets_red=current['ordinary_brackets_red'],
                  marker_counts={name:dict(collections.Counter(m['text'] for m in d['markers'])) for name,d in [('base',base),('candidate',expected),('final',current)]},
                  figures=dict(base_count=base['pictures'],candidate_count=expected['pictures'],final_count=current['pictures'],
                               counts_preserved=base['pictures']==expected['pictures']==current['pictures'],
                               media_bytes_preserved=base['media_hashes']==expected['media_hashes']==current['media_hashes']))
    # Per nonempty paragraph marker lists detect movement/multiplicity errors even after COM inserts empty paragraphs.
    def local_markers(d):
        return [[m.group() for m in MARK.finditer(p['text'])] for p in d['paragraphs'] if p['text']]
    report['marker_local_candidate_to_final_preserved'] = local_markers(expected)==local_markers(current)
    report['marker_local_base_to_candidate_preserved'] = local_markers(base)==local_markers(expected)
    manifest = json.loads(Path(args.source_manifest).read_text(encoding='utf-8'))
    report['original_source_sha_matches_manifest'] = digest(manifest['source']) == manifest['sha256']
    regions = json.loads(Path(args.regions).read_text(encoding='utf-8')) if args.regions else {}
    report['pdf'] = pdf_qa(args.pdf,current,edited,regions,not args.no_render)
    report['toc'] = T.mapping(args.base,args.pdf,args.targets,args.final)
    report['input_bytes_unchanged_during_check'] = all(digest(p)==before[str(p)] for p in paths)
    report['limitations'] = [
        'COM Open/SaveAs/reopen/export success must be recorded by coordinator; this script performs no COM operations.',
        'Text extraction cannot prove glyph visibility, clipping, cell ownership, borders, repeated headers or figure appearance.',
        'Table localization is heuristic unless explicit reviewed regions are supplied; unlocalized tables queue ALL pages.',
        'A cell phrase spanning PDF pages/column reading orders can be reported missing although visually present.',
        'Repeated text in neighboring cells/pages can cause false matches; exact per-cell visual review remains mandatory.',
        'Footer candidates are detected from bottom-page numbered lines; missing/ambiguous footers remain unresolved.',
        'Paragraph comparison ignores COM-added empty paragraphs, but reports all nonempty text differences.',
        'Figure count and media hashes prove package preservation only, not rendered figure placement or visibility.'
    ]
    report['machine_checks_pass'] = all([
        report['body_exact_nonempty_paragraphs'],report['table_base_to_candidate']['exact_preserved'],
        report['table_candidate_to_final']['exact_preserved'],not any(t['grid_errors'] for t in current['tables']),
        not report['marker_colors_wrong'],not report['malformed_markers'],not report['ordinary_brackets_red'],
        report['marker_local_candidate_to_final_preserved'],report['marker_local_base_to_candidate_preserved'],
        report['figures']['counts_preserved'],report['figures']['media_bytes_preserved'],
        report['original_source_sha_matches_manifest'],report['input_bytes_unchanged_during_check']])
    report['final_approval'] = False
    report['status'] = 'machine_checks_pass_visual_and_toc_review_pending' if report['machine_checks_pass'] else 'machine_check_failure'
    T.output(Q/'qa_page_list.json',dict(table_pages=report['pdf']['table_pages'],edited_sample_pages=report['pdf']['edited_sample_pages'],
                                     tables=[dict(key=t['key'],pages=t['pages'],method=t['method']) for t in report['pdf']['tables']],
                                     artifacts=report['pdf']['artifacts']))
    compact_report(report)
    T.output(args.out,report)
    print(json.dumps(dict(status=report['status'],tables=len(current['tables']),markers=len(current['markers']),
                          pages=report['pdf']['pages'],toc_unresolved=len(report['toc']['unresolved']),out=args.out),ensure_ascii=False))
    return 0 if report['machine_checks_pass'] else 1


def compact_report(report):
    """Keep full local evidence separate from the coordinator's concise status report."""
    pdf = report['pdf']
    detail_name = 'qa_pdf_details.json'
    T.output(Q/detail_name,pdf)
    report['pdf'] = {k:v for k,v in pdf.items() if k not in ('tables','edited_samples','figure_pdf_evidence')}
    report['pdf']['details_file'] = detail_name
    report['pdf']['edited_sample_count'] = len(pdf['edited_samples'])
    report['pdf']['tables'] = [dict(key=t['key'],method=t['method'],pages=t['pages'],visual_status=t['visual_status'],
                                  cell_count=len(t['cells']),missing_or_extraction_order_cells=sum(
                                      any(c['status'].startswith('missing') for c in cell['checks']) for cell in t['cells']),
                                  marker_multiplicity_mismatches=sum(m['expected'] != m['actual'] for m in t['marker_multiplicities']))
                              for t in pdf['tables']]


if __name__ == '__main__':
    raise SystemExit(main())
