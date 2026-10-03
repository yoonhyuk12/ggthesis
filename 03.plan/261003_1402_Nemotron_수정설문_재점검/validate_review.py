"""One acceptance run, combining provenance, wording, exports, fixtures and hashes.

Does not rerun the previous audit, call a model or open a browser. Refuses to
overwrite existing acceptance evidence. All writes remain beside this script.
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
PREV = ROOT / "03.plan/261003_1227_Nemotron_설문문항점검"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def table_items(text):
    result = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split('|')]
        if len(cells) >= 4 and re.fullmatch(r'[BCDE]-\d+', cells[1]):
            result[cells[1]] = cells[2]
    return result


class Report(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.review_ids = []
        self.resource_attributes = []
        self.links = []
        self.text = []
        self.pre = {}
        self.active_pre = None
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if 'data-review-id' in a:
            self.review_ids.append(a['data-review-id'])
        if tag == 'pre':
            self.active_pre = a.get('data-question') or a.get('data-part-guidance')
            if self.active_pre:
                self.pre[self.active_pre] = ''
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if tag in {'script', 'img', 'iframe', 'link', 'object', 'embed', 'source', 'video', 'audio'}:
            self.resource_attributes.append({'tag': tag, 'attributes': a})
        if any(k.startswith('on') for k in a):
            self.resource_attributes.append({'inline_event': tag})

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.active_pre = None

    def handle_data(self, value):
        self.text.append(value)
        if self.active_pre:
            self.pre[self.active_pre] += value


def main():
    destination = OUT / 'validation.json'
    if destination.exists():
        raise SystemExit('Acceptance evidence already exists; refusing duplicate run.')
    r = read(OUT / 'review.json')
    m = read(OUT / 'manifest.json')
    f = read(OUT / 'input_cases.json')
    baseline = read(OUT / 'input_snapshot.json')
    prior_profiles = read(PREV / 'personas.json')
    prior_reviews = read(PREV / 'responses.json')
    prior_validation = read(PREV / 'validation.json')
    md = (ROOT / '01.docs/부록1_설문지_양식.md').read_text(encoding='utf-8-sig')
    design = (ROOT / '01.docs/04_연구설계.md').read_text(encoding='utf-8-sig')
    md_lines = md.splitlines()
    checks = []

    def check(name, ok, evidence):
        checks.append({'check': name, 'passed': bool(ok), 'evidence': evidence})

    # Verify reuse against the accepted cache, without re-running its 55 checks.
    profiles = r['reused_profiles']
    check('cached_profiles_and_scenarios_preserved',
          profiles == prior_profiles['personas'] and r['sites'] == prior_profiles['sites'],
          {'profiles': len(profiles), 'source': rel(PREV / 'personas.json'),
           'inherited_validation_status': prior_validation['status'],
           'inherited_checks_passed': prior_validation['checks_passed'],
           'previous_validation_rerun': False})
    ids = [p['persona_id'] for p in profiles]
    uuids = [p['uuid'] for p in profiles]
    site_ids = [p['scenario_assumptions']['site_id'] for p in profiles]
    check('six_unique_profiles_one_per_site',
          len(set(ids)) == len(set(uuids)) == len(set(site_ids)) == len(profiles) == 6
          and all(len(s['case_ids']) == 1 for s in r['sites']),
          {'uuids': uuids, 'sites': site_ids})
    source_errors = []
    for p in profiles:
        provenance = p['provenance']
        if not (p['uuid'] == p['source_fields']['uuid']
                and provenance['dataset'] == m['dataset']['url']
                and provenance['viewer_dataset_revision'] == m['dataset']['revision']
                and len(provenance['response_body_sha256']) == 64
                and (PREV / provenance['raw_response_file']).is_file()):
            source_errors.append(p['persona_id'])
    check('source_uuid_revision_license_traceability',
          not source_errors and m['dataset']['creator'] == prior_profiles['dataset_attribution']['creator']
          and m['dataset']['license'] == prior_profiles['dataset_attribution']['license'] == 'CC BY 4.0',
          {'errors': source_errors, 'dataset': m['dataset'],
           'note': '기존 검증의 출처 증거를 상속하고 이번 산출물의 연결을 확인함; 새 API 조회 없음'})

    qs = {q['question_code']: q for q in r['questions']}
    word_errors = []
    for code, q in qs.items():
        start = md_lines.index(q['question_source_markdown'])
        end = next(i for i in range(start + 1, len(md_lines))
                   if md_lines[i].startswith('**A-') or md_lines[i] == '---')
        expected = '\n'.join(md_lines[start:end]).rstrip()
        if q['full_item_source_markdown'] != expected or q['source_line'] != start + 1:
            word_errors.append(code + ':block')
        if q['question_source_markdown'] != f'**{code})** {q["question_text"]}':
            word_errors.append(code + ':question')
        if q['part_guidance_source_markdown'] not in md_lines:
            word_errors.append(code + ':part_guide')
    check('current_a_wording_guidance_and_options_exact',
          set(qs) == {'A-3', 'A-4', 'A-6'} and not word_errors,
          {'errors': word_errors, 'source_lines': {k: q['source_line'] for k, q in qs.items()},
           'comparison': '현재 MD 블록 전체와 비교; 줄바꿈만 LF로 통일'})
    expected_pairs = {(p, c) for p in ids for c in qs}
    actual_pairs = [(x['persona_id'], x['question_code']) for x in r['reviews']]
    check('eighteen_unique_item_checks',
          len(actual_pairs) == 18 and set(actual_pairs) == expected_pairs and len(set(actual_pairs)) == 18,
          {'count': len(actual_pairs), 'by_item': dict(Counter(x[1] for x in actual_pairs))})
    row_errors = []
    for row in r['reviews']:
        p = next(p for p in profiles if p['persona_id'] == row['persona_id'])
        q = qs[row['question_code']]
        same = row['uuid'] == p['uuid'] and row['source_row_index'] == p['source_row_index']
        same &= row['site_id'] == p['scenario_assumptions']['site_id']
        same &= row['source_locator_url'] == p['provenance']['single_row_locator_url']
        same &= row['source_dataset'] == p['provenance']['dataset']
        same &= row['source_revision'] == p['provenance']['viewer_dataset_revision']
        same &= row['source_age'] == p['source_fields']['age']
        same &= row['original_evidence']['professional_persona_excerpt'] in p['source_fields']['professional_persona']
        same &= all(row['scenario_evidence'][k] == p['scenario_assumptions'][k] for k in row['scenario_evidence'])
        same &= all(row[k] == q[k] for k in ['question_text', 'question_source_markdown',
                     'response_format_source_markdown', 'item_guidance_source_markdown', 'part_guidance_source_markdown'])
        same &= row['question_source_line'] == q['source_line']
        same &= all(bool(row[k]) for k in ['interpretation', 'reason', 'information_needed', 'wording_assessment'])
        if not same:
            row_errors.append(row['review_id'])
    check('all_review_rows_have_exact_wording_uuid_source_and_evidence', not row_errors, {'errors': row_errors})
    check('no_fabricated_numeric_answers_or_age_conversion',
          all(x['confirmed_answer'] is None and x['hypothetical_test_age'] is None
              and x['source_age_is_response_day_age'] is None and not x['virtual_utterance_is_actual_quote']
              and x['status'] == 'insufficient_information' for x in r['reviews'])
          and not m['numeric_likert_responses_generated'] and not m['empirical_survey'],
          {'confirmed_answers': 0, 'source_age_separate': True, 'hypothetical_test_ages': 0,
           'numeric_likert_answers': 0})
    check('source_gaps_distinct_from_wording_clarification_candidates',
          all(x['source_information_gap'] and x['wording_issue_candidate'] == (x['question_code'] == 'A-6') for x in r['reviews'])
          and all(x['respondent_total_cost_access'] == 'unknown_not_inferred_from_safety_budget_access'
                  for x in r['reviews'] if x['question_code'] == 'A-6'),
          {'A-3': '문구 결함 미발견; 원본 age 정보 공백', 'A-4': '문구 결함 미발견; 근무 이력 공백',
           'A-6': '금액 미제공과 범위·시점·부가세 확인 후보를 구분'})

    with (OUT / 'review.csv').open(encoding='utf-8-sig', newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    csv_errors = []
    for i, (j, c) in enumerate(zip(r['reviews'], csv_rows)):
        if set(j) != set(c):
            csv_errors.append(f'{i}:columns')
            continue
        for k, v in j.items():
            expected = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))
            if c[k] != expected:
                csv_errors.append(f'{i}:{k}')
    bom = (OUT / 'review.csv').read_bytes().startswith(b'\xef\xbb\xbf')
    check('json_csv_every_cell_and_utf8_bom', len(csv_rows) == len(r['reviews']) == 18 and not csv_errors and bom,
          {'rows': len(csv_rows), 'columns': len(csv_rows[0]), 'cells': len(csv_rows) * len(csv_rows[0]),
           'errors': csv_errors, 'utf8_bom': bom, 'non_string_cell_encoding': 'compact JSON; null is literal null'})

    current = table_items(md)
    design_items = table_items(design)
    old_items = {q['code']: q['question_text'] for q in prior_reviews['questions'] if q['code'][0] in 'BCDE'}
    reuse = r['prior_audit_reuse']
    check('bcde_24_wordings_same_and_existing_120_reviews_reused',
          len(current) == 24 and current == old_items == design_items
          and {x['code']: x['current_text'] for x in reuse['wording_comparison']} == current
          and all(x['unchanged'] and x['previous_text'] == old_items[x['code']] for x in reuse['wording_comparison'])
          and reuse['reused_applicable_review_count'] == sum(x['code'][0] in 'BCDE' for x in prior_reviews['responses']) == 120
          and reuse['new_bcde_reviews'] == 0,
          {'wordings': len(current), 'previous_applicable_checks_reused': reuse['reused_applicable_review_count'],
           'new_bcde_checks': 0, 'finding_ids_reused': reuse['finding_ids_reused']})
    instructions = reuse['instruction_comparison']
    current_guides = [x for x in md_lines if x.startswith('※')]
    guide_ok = [x['previous'] for x in instructions] == prior_reviews['instructions_source_verbatim']
    guide_ok &= all(x['current'] in current_guides and x['unchanged'] == (x['current'] == x['previous']) for x in instructions)
    guide_ok &= {x['scope'] for x in instructions if not x['unchanged']} == {'A'}
    guide_ok &= len(reuse['new_item_guidance']) == 1 and reuse['new_item_guidance'][0] == qs['A-4']['item_guidance_source_markdown']
    guide_ok &= set(current_guides) == {x['current'] for x in instructions} | set(reuse['new_item_guidance'])
    old_scale = {q['options_source_markdown'] for q in prior_reviews['questions'] if q['code'][0] in 'BCDE'}
    current_scales = {line.removeprefix('&emsp;(').removesuffix(')') for line in md_lines if line.startswith('&emsp;(①')}
    check('instructions_and_response_scale_reuse_impact', guide_ok and old_scale == current_scales == {reuse['scale_current']} and reuse['scale_unchanged'],
          {'unchanged_scopes': [x['scope'] for x in instructions if x['unchanged']],
           'changed_scopes': [x['scope'] for x in instructions if not x['unchanged']],
           'added_guidance': reuse['new_item_guidance'], 'bcde_impact': '기존 판단을 바꾸는 안내 변경 없음'})

    # Fixture and HTML checks follow in the same single acceptance process.
    validate_fixtures(f, qs, design, check)
    validate_report(r, qs, check)
    validate_hashes(baseline, m, check)

    check('manifest_scope_model_and_limitations',
          m['scope']['write_root'] == rel(OUT) and m['scope']['new_reviews'] == 18
          and m['generation']['worker_count'] == 1 and m['generation']['model_id'] == 'gpt-6-astra'
          and m['generation']['temperature'] is None and m['generation']['seed'] is None
          and not m['generation']['nvidia_model_executed'] and not m['generation']['new_dataset_download']
          and not m['statistical_estimation'] and not m['representative_sample']
          and not m['manuscript_modified'] and not m['hwpx_modified']
          and not m['validation']['browser_rendering_performed'],
          {'known_model_id_source': m['generation']['model_id_evidence'],
           'temperature': None, 'seed': None, 'limitations': r['limitations']})
    passed = all(c['passed'] for c in checks)
    result = {
        'status': 'passed' if passed else 'failed',
        'executed_at_kst': datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds'),
        'command': f'python -X utf8 "{rel(Path(__file__).resolve())}"',
        'acceptance_run_count': 1, 'acceptance_pass_count': 1 if passed else 0,
        'checks_passed': sum(c['passed'] for c in checks), 'checks_total': len(checks), 'checks': checks,
        'coverage': r['counts'], 'artificial_fixture_count': f['case_count'],
        'previous_audit_rerun': False, 'browser_or_visual_verification_performed': False,
        'artifact_hashes': [{'path': rel(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
                            for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'validation.json'],
        'limits': '문구·출처 연결·구조·입력 계산·파일 불변 확인이다. 사람의 응답, 타당도, 대표성, 통계 효과 또는 화면 배치를 검증하지 않는다.',
    }
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['status', 'acceptance_run_count', 'checks_passed', 'checks_total']}, ensure_ascii=False))
    if not passed:
        print(json.dumps([c for c in checks if not c['passed']], ensure_ascii=False, indent=2))
    return 0 if passed else 1


def validate_fixtures(f, qs, design, check):
    intervals = f['cost_intervals']
    source_options = qs['A-6']['response_format_source_markdown'].replace('&emsp;', '')
    labels = [s.strip() for s in re.split(r'[①②③④⑤]', source_options) if s.strip()]
    expected_bounds = [0, 2_000_000_000, 5_000_000_000, 12_000_000_000, 15_000_000_000]
    partition_ok = [x['label'] for x in intervals] == labels and len(intervals) == 5
    partition_ok &= [x['lower_inclusive_krw'] for x in intervals] == expected_bounds
    partition_ok &= [x['category'] for x in intervals] == [1, 2, 3, 4, 5]
    partition_ok &= intervals[-1]['upper_exclusive_krw'] is None
    partition_ok &= all(intervals[i]['upper_exclusive_krw'] == intervals[i + 1]['lower_inclusive_krw']
                        for i in range(4))
    partition_ok &= all(x['label'] in design for x in intervals)
    fixture_results = []
    for c in f['cost_boundary_cases']:
        matched = [x['category'] for x in intervals if c['input_krw'] >= x['lower_inclusive_krw']
                   and (x['upper_exclusive_krw'] is None or c['input_krw'] < x['upper_exclusive_krw'])]
        fixture_results.append({'case_id': c['case_id'], 'input_krw': c['input_krw'], 'matched_categories': matched,
                                'expected_category': c['expected_category'],
                                'passed': matched == [c['expected_category']]
                                and c['input_krw'] == c['boundary_eok'] * 100_000_000 + c['delta_krw']
                                and c['expected_label'] == labels[c['expected_category'] - 1]})
    boundary_set = {(x['boundary_eok'], x['delta_krw']) for x in f['cost_boundary_cases']}
    check('five_cost_intervals_and_twelve_boundary_cases',
          partition_ok and len(fixture_results) == 12 and all(x['passed'] for x in fixture_results)
          and boundary_set == {(b, d) for b in [20, 50, 120, 150] for d in [-1, 0, 1]},
          {'domain': '0원 이상; 모든 하한 포함·상한 미포함, 마지막 상한 없음',
           'adjacency_no_gap_or_overlap': partition_ok, 'results': fixture_results})

    career_results = []
    for c in f['career_input_cases']:
        y, mo = c['input_years'], c['input_months']
        valid = type(y) is int and type(mo) is int and y >= 0 and 0 <= mo <= 11
        total = y * 12 + mo if valid else None
        fraction = Fraction(total, 12) if valid else None
        agrees = valid == c['expected_valid'] and total == c['expected_total_months']
        agrees &= (fraction == Fraction(c['expected_years_fraction'])) if valid else c['expected_years_fraction'] is None
        if not valid:
            candidate = c['correction_candidate']
            agrees &= candidate == {'years': 11, 'months': 0, 'only_after_response_confirmation': True}
        career_results.append({'case_id': c['case_id'], 'valid': valid, 'total_months': total,
                               'computed_years_fraction': str(fraction) if fraction is not None else None,
                               'passed': agrees})
    check('career_year_month_input_and_conversion',
          len(career_results) == 4 and all(x['passed'] for x in career_results)
          and {(c['input_years'], c['input_months']) for c in f['career_input_cases']} == {(0, 6), (10, 0), (10, 11), (10, 12)},
          {'results': career_results, 'automatic_correction': False})
    overlap = f['career_overlap_case']
    months = []
    for interval in overlap['intervals']:
        start = date.fromisoformat(interval['start_inclusive'])
        end = date.fromisoformat(interval['end_exclusive'])
        if start.day != 1 or end.day != 1:
            raise ValueError('Fixture intervals must use complete months.')
        months.append(set(range(start.year * 12 + start.month, end.year * 12 + end.month)))
    naive = sum(len(s) for s in months)
    union = len(set.union(*months))
    years, remaining_months = divmod(union, 12)
    check('overlapping_periods_counted_once',
          naive == overlap['expected_naive_sum_months'] == 24
          and union == overlap['expected_union_months'] == 18
          and naive - union == overlap['expected_overlap_months'] == 6
          and overlap['expected_answer'] == {'years': years, 'months': remaining_months}
          and Fraction(union, 12) == Fraction(overlap['expected_years_fraction']),
          {'naive_months': naive, 'union_months': union, 'excluded_overlap_months': naive - union,
           'years': years, 'months': remaining_months, 'convention': '시작일 포함·종료일 미포함인 월 단위 인위적 예시'})
    all_cases = f['cost_boundary_cases'] + f['career_input_cases'] + [overlap]
    check('artificial_values_not_attributed_to_any_profile',
          f['case_count'] == len(all_cases) == 17 and len({x['case_id'] for x in all_cases}) == 17
          and all(x['origin'] == 'artificial_input_fixture' and x['persona_id'] is None and x['uuid'] is None for x in all_cases)
          and all(f['question_source'][c] == qs[c]['full_item_source_markdown'] for c in ['A-4', 'A-6']),
          {'case_count': 17, 'profile_attributions': 0, 'disclosure': f['disclosure']})


def validate_report(r, qs, check):
    source = (OUT / 'report.html').read_text(encoding='utf-8')
    parser = Report()
    parser.feed(source)
    text = ''.join(parser.text)
    required = ['18건', '24문항', '120건', '실제 설문·인지면접이 아니며',
                'NVIDIA 모델을 실행하지 않았다', 'CC BY 4.0', '150억 원 이상',
                '정보 부족', '인위적 입력 시험값', 'temperature', 'seed',
                '대표 표본이 아니며', '시각 검증도 수행하지 않았다']
    missing = [s for s in required if s not in text]
    quote_ok = all(parser.pre.get(c) == q['full_item_source_markdown'] for c, q in qs.items())
    quote_ok &= parser.pre.get('A') == qs['A-3']['part_guidance_source_markdown']
    row_text_ok = all(row['interpretation'] in text and row['information_needed'] in text and row['reason'] in text
                      for row in r['reviews'])
    check('html_eighteen_rows_exact_quotes_and_required_content',
          len(parser.review_ids) == 18 and set(parser.review_ids) == {x['review_id'] for x in r['reviews']}
          and quote_ok and row_text_ok and not missing and parser.lang == 'ko',
          {'review_rows': len(parser.review_ids), 'missing_content': missing, 'exact_source_quotes': quote_ok,
           'rendered_in_browser': False})
    invalid_links = [s for s in parser.links if not s.startswith(('https://', '#'))
                     and not (OUT / s).is_file() and s != 'validation.json']
    check('html_self_contained_resources_and_working_artifact_links',
          not parser.resource_attributes and not re.search(r'url\s*\(|@import', source, re.I) and not invalid_links,
          {'resource_tags': parser.resource_attributes, 'broken_local_links': invalid_links,
           'external_links_are_citations_only': [x for x in parser.links if x.startswith('https://')],
           'method': 'HTML 소스 정적 검사; 렌더링 검사 아님'})
    suspicious = [{'offset': i, 'codepoint': f'U+{ord(c):04X}'} for i, c in enumerate(source)
                  if unicodedata.category(c) == 'Cf' or (unicodedata.category(c) == 'Cc' and c not in '\t\n\r')]
    check('reader_text_unicode_and_korean_review', not suspicious,
          {'suspicious_invisible_characters': suspicious,
           'humanizer_kr_application': '간결한 검토 보고체; 실제 인용·원문 안내·불확실성 보존; 가상 발화의 LLM 작성 사실 명시',
           'authorship_or_detector_claim': False})


def validate_hashes(baseline, manifest, check):
    roots = [ROOT / '01.docs', PREV]
    now_files = {rel(p) for root in roots for p in root.rglob('*') if p.is_file()}
    original_files = {x['path'] for x in baseline['files']}
    evidence = []
    for record in baseline['files']:
        path = ROOT / record['path']
        after = sha(path) if path.is_file() else None
        evidence.append({'path': record['path'], 'before_sha256': record['sha256'],
                         'after_sha256': after, 'unchanged': after == record['sha256']})
    check('all_manuscript_and_previous_artifact_hashes_unchanged',
          now_files == original_files and all(x['unchanged'] for x in evidence),
          {'baseline_at': baseline['captured_at'], 'file_count': len(evidence),
           'added_files': sorted(now_files - original_files), 'removed_files': sorted(original_files - now_files),
           'comparisons': evidence})
    before = {x['path']: x for x in baseline['files']}
    check('manifest_input_sha256_matches_baseline_and_current_files',
          all(x == before[x['path']] and x['sha256'] == sha(ROOT / x['path']) for x in manifest['inputs'])
          and manifest['protected_inputs']['file_count'] == len(evidence),
          {'named_inputs': len(manifest['inputs']), 'all_protected_files': len(evidence),
           'snapshot_path': manifest['protected_inputs']['snapshot']})


if __name__ == '__main__':
    sys.exit(main())
