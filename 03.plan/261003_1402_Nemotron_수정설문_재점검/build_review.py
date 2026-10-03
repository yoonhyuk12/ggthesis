"""Serialize this worker's incremental review; no network or LLM inference.

Run from any directory with Python 3. All writes stay beside this script.
input_snapshot.json is the immutable baseline captured before this review.
"""
import copy
import csv
import hashlib
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
PREV = ROOT / "03.plan/261003_1227_Nemotron_설문문항점검"
QUESTIONNAIRE = ROOT / "01.docs/부록1_설문지_양식.md"
DESIGN = ROOT / "01.docs/04_연구설계.md"
REVISION = "ada0f5b53a38bb5a30cce09358adde883c1ab63a"
SOURCE = "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea"
TARGET_CODES = ["A-3", "A-4", "A-6"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_a(text):
    lines = text.splitlines()
    guidance = next(x for x in lines if x.startswith("※ 다음은 응답자의 일반적 사항"))
    result = {}
    for i, line in enumerate(lines):
        m = re.fullmatch(r"\*\*(A-[1-6])\)\*\* (.+)", line)
        if not m:
            continue
        tail = []
        for following in lines[i + 1:]:
            if not following.strip():
                break
            tail.append(following)
        result[m[1]] = {
            "question_code": m[1], "question_text": m[2],
            "source_path": rel(QUESTIONNAIRE), "source_line": i + 1,
            "question_source_markdown": line,
            "response_format_source_markdown": "\n".join(x for x in tail if not x.startswith("※")),
            "item_guidance_source_markdown": "\n".join(x for x in tail if x.startswith("※")),
            "part_guidance_source_markdown": guidance,
            "full_item_source_markdown": "\n".join([line] + tail),
        }
    return result


def parse_likert(text):
    return {m[1]: m[2].strip() for m in re.finditer(r"^\|\s*([BCDE]-\d+)\s*\|\s*([^|]+)\|", text, re.M)}


# Interpretations written by the dispatched Codex worker after reading all six
# actual cached source profiles. These are not transcribed human responses.
NOTES = {
    "P1": {
        "source_excerpt": "베테랑 토목 관리자",
        "career_interpretation": "공정 관리와 안전 점검 등 현장 업무 기간을 합치고, 동시에 맡은 기간은 한 번만 센다.",
        "career_reason": "원본의 베테랑 표현은 정확한 근무 연월을 제공하지 않는다.",
        "cost_interpretation": "안전관리 예산과 현장 전체 총공사비를 구분한 뒤 해당 구간을 고른다.",
        "cost_reason": "안전관리 예산 문서 접근은 가상 조건이다. 그 조건만으로 현장 총공사비를 알 수 없고 금액도 없다.",
        "cost_needed": "총공사비가 적힌 현장 자료, 안전관리 예산과의 구별, 조사자가 정한 금액 기준",
    },
    "P2": {
        "source_excerpt": "경기 지역 건설 현장에서",
        "career_interpretation": "전기 감리 등 실제 현장 업무 기간을 합산하고 겹치는 기간은 제외한다.",
        "career_reason": "원본 직함에 연구원이 함께 적혀 있어도 실제 현장 근무 기간을 확인해야 한다. 시작·종료일은 없다.",
        "cost_interpretation": "담당 전기 공종의 금액과 현장 전체 금액 중 어느 것을 묻는지 확인한다.",
        "cost_reason": "전기 감리 직무는 원본에 있지만 총공사비는 없다. 예산 편성·집행액을 모른다는 조건도 재사용한다.",
        "cost_needed": "현장 전체와 담당 공종의 구별, 총공사비 확인 담당자·자료, 조사자가 정한 금액 기준",
    },
    "P3": {
        "source_excerpt": "수십 년간 거친 토목 현장을 누비며",
        "career_interpretation": "과거부터 응답일까지의 현장 업무를 년·개월로 적되 겹치는 기간은 한 번만 센다.",
        "career_reason": "수십 년이라는 원문은 정확한 연수가 아니다. 자문역 전환도 목표일 뿐 실제 경력 변동으로 계산하지 않는다.",
        "cost_interpretation": "계약·공사비 협상 경험과 별개로, 어떤 시점의 현장 총공사비인지 확인한다.",
        "cost_reason": "원본에 공사비 협상 업무가 있고 가상 예산 문서 접근 조건이 있지만, 실제 계약금액과 변경 이력은 없다.",
        "cost_needed": "총공사비 자료, 계약 변경 전후 중 적용 시점, 조사자가 정한 금액 기준",
    },
    "P4": {
        "source_excerpt": "화성시 일대의 토목 현장에서",
        "career_interpretation": "공정·협력업체 조정 등 현장 업무 기간을 년·개월로 적고 중복 기간은 제외한다.",
        "career_reason": "원본은 현장 실무를 설명하지만 근무 연월은 없다. 숙련도나 나이로 경력을 채우지 않는다.",
        "cost_interpretation": "담당 공정의 물량·자재비를 현장 총공사비로 바꾸어 답하지 않는다.",
        "cost_reason": "원본의 물량·자재 관리 업무는 총공사비를 안다는 근거가 아니다. 예산 편성·집행액 미상 조건을 유지한다.",
        "cost_needed": "물량·자재비와 총공사비의 구별, 금액 확인 담당자·자료, 조사자가 정한 금액 기준",
    },
    "P5": {
        "source_excerpt": "강릉의 중소 건설 현장에서",
        "career_interpretation": "현재 현장소장 경력뿐 아니라 과거 현장 업무를 포함하고 겹치는 기간은 제외한다.",
        "career_reason": "소장 직무와 현장 경험은 원본에 있으나 전체 경력의 시작·종료일은 없다.",
        "cost_interpretation": "중소 현장이라는 설명으로 구간을 추정하지 않고 총공사비 자료를 확인한다.",
        "cost_reason": "원본의 중소 건설 현장이라는 표현은 다섯 구간 중 하나를 확정하지 않는다. 가상 현장의 금액은 없다.",
        "cost_needed": "현장 총공사비 자료와 조사자가 정한 금액 기준; 중소라는 표현으로 상한을 추정하지 않음",
    },
    "P6": {
        "source_excerpt": "청주 인근 토목 현장에서",
        "career_interpretation": "토목 감리 등 현장 업무 기간을 합치고, 여러 업무를 동시에 맡았다면 같은 기간은 한 번만 센다.",
        "career_reason": "원본의 감리·공정 조율 업무에서 정확한 근무 연월이나 겹친 기간을 알아낼 수 없다.",
        "cost_interpretation": "감리 대상 공종의 계약액과 현재 담당 현장 전체 금액을 구분해 읽는다.",
        "cost_reason": "감리 직무와 예산 편성·집행액 미상 조건만 주어졌다. 총공사비 지식 유무는 별도로 확인해야 한다.",
        "cost_needed": "현장 전체와 감리 대상 공종의 구별, 총공사비 확인 담당자·자료, 조사자가 정한 금액 기준",
    },
}

FINDINGS = [
    {
        "id": "N1", "codes": ["A-3"], "kind": "source_information_gap",
        "finding": "기준일은 응답일 현재, 나이 방식은 만 나이, 단위는 세로 명시되어 있다. 문구의 새 결함은 발견하지 못했다.",
        "limitation": "원본 age의 계산 방식·기준일과 생년월일이 없어 확정 응답을 만들 수 없다. 데이터셋 수집일도 응답일로 대체할 수 없다.",
        "minimum_proposal": "현 문구를 유지하고 실제 응답자에게 응답일 현재 만 나이를 확인한다. 이 시험을 위해 생년월일 수집 문항을 추가하지 않는다.",
    },
    {
        "id": "N2", "codes": ["A-4"], "kind": "source_information_gap",
        "finding": "현장 업무 전체 기간, 응답일까지의 범위, 중복 기간 제외, 개월 0∼11을 명시한다. 새 문구 결함은 발견하지 못했다.",
        "limitation": "여섯 프로필에 정확한 근무 이력이 없다. 나이나 베테랑·수십 년이라는 서술로 년·개월을 추정하지 않는다.",
        "minimum_proposal": "현 문구를 유지한다. 12개월 입력은 원응답을 확인한 뒤 정정하며, 근무 기간이 겹치는 실제 사례의 합산 방법은 사람에게 확인한다.",
    },
    {
        "id": "N3", "codes": ["A-6"], "kind": "clarification_candidate_and_information_gap",
        "finding": "다섯 구간은 경계에서 중복·누락 없이 이어진다. 150억 원 이상도 응답 범위다. 다만 총공사비의 범위와 기준시점은 문구만으로 충분히 정해지지 않는다.",
        "limitation": "전체 현장과 담당 공종, 계약 변경 전후, 부가세 포함 여부를 응답자가 어떻게 구별하는지는 미확인이다. 법적 결함으로 판정한 결과가 아니다.",
        "minimum_proposal": "조사자가 총공사비의 대상 범위·기준시점·부가세 처리와 확인 자료를 정한 뒤 A-6 안내에 한 문장으로 제시한다. 금액을 모르는 경우의 확인·미응답 처리도 조사 전에 정한다.",
    },
]

LIMITATIONS = [
    "LLM 가상 문항 점검이며 실제 인지면접·설문 응답·타당도 검증이 아니다. 가상 발화는 인터뷰 인용이 아니다.",
    "한 Codex 워커가 여섯 합성 프로필의 해석을 작성했다. 독립 응답자나 대표 표본이 아니며 사람의 오해 빈도를 추정하지 않는다.",
    "원본은 이전 점검에서 편의 선택한 여섯 사례다. 가상 현장·소속·보직·정보 접근·경험 조건은 원본 사실과 구분한다.",
    "source_age는 원본 필드일 뿐 응답일 현재 만 나이가 아니다. 경력·공사비·Likert 응답값을 생성하지 않았다.",
    "인위적 시험값은 계산 규칙만 확인한다. 실제 응답 편의나 혼란의 발생 여부는 사람을 대상으로 확인해야 한다.",
    "B/C/D/E는 문구·안내 비교 후 기존 판단을 재사용했다. 이번에 전체 156건을 새로 검토하지 않았다.",
    "대표성 평가·통계 추정·법적 총공사비 정의 검증을 수행하지 않았다. 브라우저 렌더링이나 시각 검증도 수행하지 않았다.",
]


def make_input_cases(questions):
    labels = ["20억 원 미만", "20억 원 이상∼50억 원 미만", "50억 원 이상∼120억 원 미만",
              "120억 원 이상∼150억 원 미만", "150억 원 이상"]
    cutoffs = [0, 2_000_000_000, 5_000_000_000, 12_000_000_000, 15_000_000_000, None]
    intervals = [{"category": i + 1, "label": labels[i], "lower_inclusive_krw": cutoffs[i],
                  "upper_exclusive_krw": cutoffs[i + 1]} for i in range(5)]
    cost = []
    for boundary_index, boundary_eok in enumerate([20, 50, 120, 150]):
        for delta in [-1, 0, 1]:
            expected = boundary_index + 1 if delta < 0 else boundary_index + 2
            cost.append({"case_id": f"COST-{boundary_eok}-{ {-1:'BEFORE', 0:'EXACT', 1:'AFTER'}[delta]}",
                         "question_code": "A-6", "persona_id": None, "uuid": None,
                         "origin": "artificial_input_fixture", "boundary_eok": boundary_eok,
                         "delta_krw": delta, "input_krw": boundary_eok * 100_000_000 + delta,
                         "expected_category": expected, "expected_label": labels[expected - 1]})
    careers = []
    for case_id, years, months, expected in [("CAREER-0Y6M", 0, 6, "1/2"),
                                           ("CAREER-10Y0M", 10, 0, "10"),
                                           ("CAREER-10Y11M", 10, 11, "131/12"),
                                           ("CAREER-10Y12M", 10, 12, None)]:
        careers.append({"case_id": case_id, "question_code": "A-4", "persona_id": None, "uuid": None,
                        "origin": "artificial_input_fixture", "input_years": years, "input_months": months,
                        "expected_valid": expected is not None, "expected_years_fraction": expected,
                        "expected_total_months": years * 12 + months if expected is not None else None,
                        "correction_candidate": {"years": 11, "months": 0, "only_after_response_confirmation": True}
                        if expected is None else None,
                        "note": "12개월은 형식 위반이다. 원응답을 확인하기 전 자동으로 11년 0개월로 고치지 않는다."
                        if expected is None else "년 + 개월/12 계산만 확인하는 인위적 입력이다."})
    overlap = {
        "case_id": "CAREER-OVERLAP", "question_code": "A-4", "persona_id": None, "uuid": None,
        "origin": "artificial_input_fixture",
        "intervals": [{"start_inclusive": "2020-01-01", "end_exclusive": "2021-01-01"},
                      {"start_inclusive": "2020-07-01", "end_exclusive": "2021-07-01"}],
        "expected_naive_sum_months": 24, "expected_overlap_months": 6, "expected_union_months": 18,
        "expected_answer": {"years": 1, "months": 6}, "expected_years_fraction": "3/2",
        "note": "월 단위 계산이 분명한 예시를 위해 각 기간은 시작일 포함·종료일 미포함으로 정했다. 실제 날짜의 일수·부분월 반올림 규칙을 제안한 것이 아니다.",
    }
    return {
        "schema_version": "1.0", "disclosure": "데이터셋 응답이 아닌 인위적 입력 시험값이며 어느 인물에게도 귀속하지 않는다.",
        "question_source": {c: questions[c]["full_item_source_markdown"] for c in ["A-4", "A-6"]},
        "cost_domain": "0원 이상 금액의 구간 분할을 확인한다. 0원은 계산 영역의 하한이며 조사대상 자격이나 법적 금액 정의를 뜻하지 않는다.",
        "cost_intervals": intervals, "cost_boundary_cases": cost,
        "career_input_cases": careers, "career_overlap_case": overlap,
        "case_count": len(cost) + len(careers) + 1,
    }


def cell(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def render_report(review, fixtures, manifest):
    e = lambda x: html.escape(str(x))
    parts = ['<!doctype html><html lang="ko"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>수정 설문 A-3·A-4·A-6 가상 문항 점검</title>',
             '<style>body{max-width:1120px;margin:0 auto;padding:24px;color:#172330;background:#fbfcfe;',
             'font-family:system-ui,"Malgun Gothic",sans-serif;line-height:1.65}h1{font-size:1.8rem}h2{font-size:1.25rem;margin-top:2.1rem}',
             'table{width:100%;border-collapse:collapse;font-size:.92rem;margin:14px 0}th,td{border:1px solid #cbd5df;padding:10px;text-align:left;vertical-align:top}',
             'th{background:#e9eff6}caption{text-align:left;font-weight:600}.notice{border-left:4px solid #245a83;padding:12px 16px;background:#edf4fa}',
             '.muted,small{color:#4b5b6a}code{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f0f3f7;padding:12px}',
             '.table-scroll{overflow-x:auto}.review-table{min-width:880px}a{color:#125184}summary{cursor:pointer}',
             '@media print{body{background:white;font-size:10pt;padding:0}tr{break-inside:avoid}.table-scroll{overflow:visible}.review-table{min-width:0}thead{display:table-header-group}}</style></head><body>',
             '<header><p class="muted">수정 설문 증분 점검 · ' + e(manifest['created_at_kst']) + '</p>',
             '<h1>A-3·A-4·A-6은 어디까지 답할 수 있나</h1></header>',
             '<p class="notice"><strong>새로 점검한 범위는 6프로필 × 3문항, 총 18건이다.</strong> NVIDIA 합성 프로필을 읽은 단일 Codex 워커가 작성한 LLM 가상 문항 점검이다. 실제 설문·인지면접이 아니며, 아래 가상 해석과 발화는 인터뷰 인용이 아니다. NVIDIA 모델을 실행하지 않았다.</p>',
             '<h2>이번 점검에서 확인한 점</h2><ul>',
             '<li><strong>A-3:</strong> 응답일·만 나이·세 단위가 명확하다. 원본 age의 기준시점과 계산 방식이 없어 실제 답으로 옮길 수 없다.</li>',
             '<li><strong>A-4:</strong> 현장 업무 전체 기간·중복 제외·개월 0∼11을 안내한다. 정확한 이력이 없어 년·개월 응답은 비워 두었다.</li>',
             '<li><strong>A-6:</strong> 20·50·120·150억 경계는 중복·누락 없이 이어진다. 금액의 대상 범위와 기준시점, 정보 접근 가능성은 별도 확인 사항이다. 150억 원 이상도 포함한다.</li></ul>',
             '<p>프로필의 정보 부족을 문항 결함으로 세지 않았다. A-3·A-4에는 새 문구 결함을 억지로 추가하지 않았고, 모든 확정 응답값을 null로 남겼다. 공사비 구간 번호는 금액이나 Likert 점수가 아니다.</p>',
             '<h2>기존 점검에서 이어지는 사항</h2>',
             '<p>B/C/D/E <strong>24문항과 해당 안내·척도는 기존 기록과 같다.</strong> 공통부 안내도 같다. Part A의 숫자 기입 안내와 A-4의 중복 제외·개월 안내가 바뀌었으며, B/C/D/E의 기존 판단을 바꾸는 안내 변경은 확인하지 못했다. 기존 적용 점검 120건을 재사용했고 새 발화·점수를 만들지 않았다.</p>',
             '<table><thead><tr><th>기존 발견</th><th>이어 보는 내용</th></tr></thead><tbody>',
             '<tr><td>F1·F2 / C</td><td>예산 정보 접근, 고가 장비·계상 기준의 해석</td></tr>',
             '<tr><td>F3 / E</td><td>완화 인식의 비교대상·기간</td></tr>',
             '<tr><td>F4·F5 / D</td><td>D-3의 여러 관찰을 합친 판단, 직접 관찰과 내부 기능 추정</td></tr>',
             '<tr><td>F6·F7 / D·E, B-3</td><td>무알림 도입의 문항별 비해당, CCTV 없는 현장의 전화·보고 해석</td></tr></tbody></table>',
             '<p><a href="../261003_1227_Nemotron_설문문항점검/report.html">기존 보고서</a>의 F1∼F7을 참고한다. 그 보고서의 A-3·A-4·A-6과 설계 설명은 수정 전 기록이다. 이번에 전체 156건을 다시 수행한 것으로 읽으면 안 된다.</p>',
             '<h2>현재 문항과 안내</h2><p>아래는 현재 MD 원문의 정확한 발췌다. Markdown 표시와 응답칸의 HTML 공백 표기도 그대로 보존했다.</p>',
             '<pre data-part-guidance="A">' + e(review['questions'][0]['part_guidance_source_markdown']) + '</pre>']
    for q in review['questions']:
        parts += [f'<pre data-question="{q["question_code"]}">' + e(q['full_item_source_markdown']) + '</pre>']
    parts += ['<h2>재사용한 프로필·현장 조건</h2>',
              '<p>원본 직무와 source_age를 가상 조건과 구분했다. 나이·성별·성격에서 응답 성향을 추정하지 않았다. source_age의 숫자는 응답일 현재 만 나이로 확인된 값이 아니다.</p>',
              '<div class="table-scroll"><table><thead><tr><th>프로필 / 원본 행</th><th>원본 직무·age</th><th>재사용한 가상 조건</th><th>원본 UUID</th></tr></thead><tbody>']
    for p in review['reused_profiles']:
        s = p['scenario_assumptions']
        site = next(x for x in review['sites'] if x['site_id'] == s['site_id'])
        parts += ['<tr><td>' + e(p['persona_id'] + ' ' + p['source_name']) + '<br>row ' + e(p['source_row_index']) + '</td><td>' +
                  e(p['source_fields']['occupation']) + '<br>source_age=' + e(p['source_fields']['age']) + '</td><td>' +
                  e(s['site_id'] + ' · ' + site['description']) + '<br>' + e(s['role']) + '<br>' + e(s['budget_knowledge_scope']) +
                  '</td><td><code>' + e(p['uuid']) + '</code></td></tr>']
    parts += ['</tbody></table></div><p>6현장에 각 1명인 이전 시험 조건을 유지했다. 도입 4현장·미도입 2현장은 시험 사례 구성일 뿐 실제 모집 비율을 나타내지 않는다. 현장 위치·총공사비·정확한 경력은 추가하지 않았다.</p>',
              '<h2>18건의 가상 해석과 응답 가능 여부</h2>',
              '<p>해석은 LLM이 만든 점검 예시다. “정보 부족”은 이 프로필만으로 확정할 수 없다는 뜻이며, 실제 사람이 답하지 못한다는 예측이 아니다.</p>',
              '<div class="table-scroll"><table class="review-table"><thead><tr><th>사례·문항</th><th>가상 해석 / 발화</th><th>확정 응답</th><th>필요 정보</th><th>근거·판단</th></tr></thead><tbody>']
    for row in review['reviews']:
        parts += [f'<tr data-review-id="{row["review_id"]}"><td>' + e(row['persona_id'] + ' · ' + row['question_code']) + '</td><td>' +
                  e(row['interpretation']) + '</td><td>정보 부족<br>값: null</td><td>' + e(row['information_needed']) + '</td><td>' +
                  e(row['reason']) + '<br><small>' + e(row['wording_assessment']) + '</small></td></tr>']
    parts += ['</tbody></table></div>',
              '<h2>인위적 입력 시험값</h2><p><strong>다음 값은 데이터셋에서 얻은 응답이 아니며 어떤 프로필에도 귀속하지 않는다.</strong> 경계의 직전·직후는 각각 1원 차이다. 원 단위 정수 계산으로 반올림 문제를 피했다.</p>',
              '<table><thead><tr><th>경계</th><th>1원 직전 → 구간</th><th>정확한 경계 → 구간</th><th>1원 직후 → 구간</th></tr></thead><tbody>']
    for boundary in [20, 50, 120, 150]:
        cases = [c for c in fixtures['cost_boundary_cases'] if c['boundary_eok'] == boundary]
        parts += ['<tr><td>' + e(boundary) + '억 원</td>' + ''.join('<td>' + f'{c["input_krw"]:,}' + '원 → ' + e(c['expected_category']) + '</td>' for c in cases) + '</tr>']
    parts += ['</tbody></table><p>구간 1∼5는 위 A-6 보기와 같다. 각 구간의 상한은 다음 구간의 포함 하한이며 마지막 구간에는 상한이 없다. 0원 이상 계산 영역에서 빈틈과 중복이 없음을 확인한다.</p>',
              '<table><thead><tr><th>A-4 시험값</th><th>계산·처리</th></tr></thead><tbody>',
              '<tr><td>0년 6개월</td><td>6개월, 0.5년</td></tr>',
              '<tr><td>10년 0개월</td><td>120개월, 10년</td></tr>',
              '<tr><td>10년 11개월</td><td>131개월, 131/12년(약 10.9167년)</td></tr>',
              '<tr><td>10년 12개월</td><td>개월 0∼11 위반. 원응답 확인 후 11년 0개월로 정정할 수 있으나 자동 보정하지 않는다.</td></tr>',
              '<tr><td>2020-01-01∼2021-01-01 + 2020-07-01∼2021-07-01</td><td>종료일 미포함 시험 규칙. 단순 합 24개월에서 겹친 6개월을 제외하면 18개월, 1년 6개월(1.5년).</td></tr></tbody></table>',
              '<p>년 + 개월/12는 계산 점검에만 썼다. 부분월·일수의 실제 조사 처리 규칙까지 검증한 것은 아니다.</p>',
              '<h2>문구를 손대기 전에 정할 사항</h2>',
              '<p>A-3·A-4는 현재 안내를 유지한다. A-6은 조사자가 <strong>전체 현장 또는 담당 공종 중 대상 범위, 계약 변경에 적용할 기준시점, 부가세 처리</strong>를 정하고 확인 자료와 함께 짧게 안내하는 안을 검토한다. 예산 문서 접근 조건만으로 총공사비를 안다고 보지 않으며, 금액을 모를 때 확인·미응답 처리도 정한다. 새 법적 기준을 제시하거나 원고를 수정한 결과는 아니다.</p>',
              '<h2>출처·검증 증거와 한계</h2>',
              '<p>프로필 출처는 <a href="' + SOURCE + '">NVIDIA Nemotron-Personas-Korea</a>, 라이선스는 <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>다. 원본 revision은 <code>' + REVISION + '</code>이다. 이전 캐시의 원본 필드·UUID·출처·가상 조건을 재사용하고 이번 문항 해석과 인위적 시험값만 새로 작성했다. 데이터셋 다운로드나 API 재조회는 하지 않았다.</p>',
              '<p>실행 주체는 단일 Codex 워커, 모델 ID는 조정자가 런타임에서 확인해 전달한 gpt-6-astra다. temperature와 seed는 공개되지 않아 null이다. 재현 스크립트는 이미 작성한 판단을 파일로 저장하며 새 LLM 추론을 실행하지 않는다.</p>',
              '<p>수용 검증은 1회로 묶었다. 문항·안내 정확성, 18건의 UUID·출처 연결, JSON/CSV 전 셀, 인위적 시험값, 입력 SHA256 불변, HTML 필수 내용·외부 자원 미사용이 검사 대상이다. <a href="validation.json">validation.json</a>에 실행 결과를 남긴다. 이 검사는 사람의 응답 타당성이나 화면 렌더링을 검증하지 않는다.</p>',
              '<ul>' + ''.join('<li>' + e(x) + '</li>' for x in LIMITATIONS) + '</ul>',
              '<p><a href="review.json">18건·문구 대조 JSON</a> · <a href="review.csv">UTF-8 BOM CSV</a> · <a href="input_cases.json">인위적 시험값</a> · <a href="manifest.json">실행·출처 명세</a> · <a href="input_snapshot.json">입력 해시 기준본</a></p>',
              '</body></html>']
    return ''.join(parts)


def main():
    if (OUT / "validation.json").exists():
        raise SystemExit("Acceptance evidence already exists; do not rebuild a completed run.")
    started = read_json(OUT / "input_snapshot.json")["captured_at"]
    now = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    old = read_json(PREV / "responses.json")
    personas = read_json(PREV / "personas.json")
    text = QUESTIONNAIRE.read_text(encoding="utf-8-sig")
    questions = parse_a(text)
    current_bcde = parse_likert(text)
    previous_questions = {q['code']: q for q in old['questions']}
    previous_bcde = {code: q['question_text'] for code, q in previous_questions.items() if code[0] in "BCDE"}
    comparison = [{"code": code, "current_text": current_bcde[code], "previous_text": previous_bcde.get(code),
                   "unchanged": current_bcde[code] == previous_bcde.get(code), "prior_reference": f"{rel(PREV / 'responses.json')}#/questions/{next(i for i,q in enumerate(old['questions']) if q['code']==code)}"}
                  for code in current_bcde]
    current_instructions = [x for x in text.splitlines() if x.startswith("※")]
    instruction_comparison = []
    for i, instruction in enumerate(old['instructions_source_verbatim']):
        key = ["common", "A", "B", "C", "D", "E"][i]
        current = questions['A-3']['part_guidance_source_markdown'] if key == 'A' else next(x for x in current_instructions if x == instruction)
        instruction_comparison.append({"scope": key, "previous": instruction, "current": current,
                                       "unchanged": current == instruction,
                                       "impact": "A-3·A-4 숫자 기입 안내 추가; B/C/D/E 판단에는 영향 없음" if key == 'A' else "변경 없음"})
    additions = [x for x in current_instructions if x not in [r['current'] for r in instruction_comparison]]
    scale = next(x for x in text.splitlines() if x.startswith("&emsp;(①"))
    current_scale = re.fullmatch(r"&emsp;\((.*)\)", scale)[1]
    reuse = {
        "previous_report": rel(PREV / "report.html"), "previous_responses": rel(PREV / "responses.json"),
        "previous_validation": rel(PREV / "validation.json"),
        "wording_comparison": comparison, "instruction_comparison": instruction_comparison,
        "new_item_guidance": additions, "scale_current": current_scale,
        "scale_unchanged": all(previous_questions[c]['options_source_markdown'] == current_scale for c in current_bcde),
        "reuse_scope": "B/C/D/E의 기존 적용 점검 120건만 참고하며 새 발화나 점수를 생성하지 않음",
        "reused_applicable_review_count": sum(r['code'][0] in 'BCDE' for r in old['responses']),
        "new_bcde_reviews": 0, "finding_ids_reused": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
        "finding_references": [f"{rel(PREV / 'responses.json')}#/findings/{i}" for i in range(7)],
        "not_reused_as_current": "이전 A-3·A-4·A-6과 수정 전 연구설계 설명은 현행 판단으로 재사용하지 않는다.",
    }
    rows = []
    for p in personas['personas']:
        pid = p['persona_id']
        n = NOTES[pid]
        for code in TARGET_CODES:
            q = questions[code]
            row = {"review_id": f"{pid}-{code}", "persona_id": pid, "uuid": p['uuid'],
                   "source_row_index": p['source_row_index'], "site_id": p['scenario_assumptions']['site_id'],
                   "source_dataset": SOURCE, "source_revision": REVISION,
                   "source_locator_url": p['provenance']['single_row_locator_url'],
                   "source_profile_pointer": f"{rel(PREV / 'personas.json')}#/personas/{int(pid[1:])-1}",
                   "question_code": code, "question_text": q['question_text'], "question_source_line": q['source_line'],
                   "question_source_markdown": q['question_source_markdown'],
                   "response_format_source_markdown": q['response_format_source_markdown'],
                   "item_guidance_source_markdown": q['item_guidance_source_markdown'],
                   "part_guidance_source_markdown": q['part_guidance_source_markdown'],
                   "status": "insufficient_information", "confirmed_answer": None,
                   "source_age": p['source_fields']['age'], "source_age_is_response_day_age": None,
                   "hypothetical_test_age": None, "virtual_utterance_is_actual_quote": False,
                   "source_information_gap": True,
                   "wording_issue_candidate": code == 'A-6',
                   "respondent_total_cost_access": "unknown_not_inferred_from_safety_budget_access" if code == 'A-6' else "not_applicable",
                   "original_evidence": {"occupation": p['source_fields']['occupation'],
                                         "professional_persona_excerpt": n['source_excerpt']},
                   "scenario_evidence": {"role": p['scenario_assumptions']['role'],
                                         "budget_knowledge_scope": p['scenario_assumptions']['budget_knowledge_scope']},
                   "finding_ref": {"A-3": "N1", "A-4": "N2", "A-6": "N3"}[code]}
            if code == 'A-3':
                row.update(interpretation="응답하는 날을 기준으로 만 나이를 세 단위로 적는 문항이다.",
                           reason=f"원본 age={p['source_fields']['age']}의 계산 방식·기준일이 없다. 직무나 수집일로 이를 보완할 수 없다.",
                           information_needed="응답일 현재 만 나이의 확인; 또는 계산 근거가 있는 생년월일·기준일",
                           wording_assessment="기준일·방식·단위 명시. 문구 결함과 구분되는 원본 정보 부족.")
            elif code == 'A-4':
                row.update(interpretation=n['career_interpretation'], reason=n['career_reason'],
                           information_needed="현장 업무별 시작·종료 연월, 휴지·겹침 기간, 응답일",
                           wording_assessment="전체 기간·중복 제외·개월 0∼11 명시. 정확한 이력 미제공.")
            else:
                row.update(interpretation=n['cost_interpretation'], reason=n['cost_reason'],
                           information_needed=n['cost_needed'],
                           wording_assessment="구간 경계는 명확. 대상 범위·시점·부가세 처리는 확인 후보.")
            row['virtual_utterance'] = row['interpretation']
            rows.append(row)
    review = {
        "schema_version": "1.0", "created_at_kst": now,
        "disclosure": LIMITATIONS[0],
        "method": "단일 Codex 워커가 실제 캐시 프로필을 읽고 18건의 해석·응답 가능 여부를 작성했다. 공통 판단은 같은 기준으로 직렬화하며 별도 인물별 모델 세션을 실행하지 않았다.",
        "questions": [questions[c] for c in TARGET_CODES],
        "previous_to_current_a": [{"code": c, "previous_question_text": previous_questions[c]['question_text'],
                                   "previous_options_source_markdown": previous_questions[c]['options_source_markdown'],
                                   "current_question_text": questions[c]['question_text']} for c in TARGET_CODES],
        "reused_profiles": copy.deepcopy(personas['personas']), "sites": copy.deepcopy(personas['sites']),
        "reviews": rows, "findings": FINDINGS, "prior_audit_reuse": reuse, "limitations": LIMITATIONS,
        "counts": {"profiles": 6, "sites": 6, "profiles_per_site": 1, "new_cognitive_item_checks": 18,
                   "new_bcde_checks": 0, "reused_bcde_items": 24, "reused_bcde_applicable_checks": 120},
    }
    fixtures = make_input_cases(questions)
    snapshot = read_json(OUT / 'input_snapshot.json')
    key_paths = [QUESTIONNAIRE, DESIGN, PREV / 'personas.json', PREV / 'responses.json',
                 PREV / 'manifest.json', PREV / 'validation.json', PREV / 'report.html', PREV / 'dataset_metadata.json']
    baseline = {x['path']: x for x in snapshot['files']}
    manifest = {
        "schema_version": "1.0", "started_at_kst": started, "created_at_kst": now,
        "purpose": "실제 조사 전 수정 문항의 해석 가능성·자료 공백·입력 경계를 점검한다. 실증 분석에 합치지 않는다.",
        "scope": {"write_root": rel(OUT), "new_review_codes": TARGET_CODES, "new_reviews": 18,
                  "reused_bcde_item_count": 24, "artificial_fixture_count": fixtures['case_count']},
        "generation": {"agent": "Codex", "worker_count": 1, "model_family": "GPT-6", "model_id": "gpt-6-astra",
                       "model_id_evidence": "조정자 msg_df752bf3ec5a: worker-show projection.provider.model 관측, 2026-10-03 14:06 KST",
                       "temperature": None, "seed": None, "detailed_model_build": None,
                       "nvidia_model_executed": False, "separate_persona_sessions": False,
                       "new_model_api_calls": False, "new_dataset_download": False,
                       "code_role": "build_review.py는 워커가 작성한 판단을 직렬화한다. LLM 추론이나 API 호출을 실행하지 않는다."},
        "dataset": {"creator": "NVIDIA", "title": "Nemotron-Personas-Korea", "url": SOURCE,
                    "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "revision": REVISION, "source_is_synthetic": True,
                    "changes": "기존 캐시의 원본 필드·출처·가상 조건은 그대로 재사용하고 수정 문항 해석과 인위적 시험값을 새로 작성함",
                    "source_evidence": rel(PREV / 'personas.json'),
                    "official_card_check": "조정자가 공식 카드의 합성 자료·라이선스·revision을 확인했다고 전달함(msg_cbcd13f097a6); 워커는 캐시만 재사용"},
        "inputs": [baseline[rel(p)] for p in key_paths],
        "protected_inputs": {"snapshot": rel(OUT / 'input_snapshot.json'), "file_count": len(snapshot['files']),
                             "roots": ["01.docs/", rel(PREV) + "/"], "sha_algorithm": "SHA256"},
        "prior_audit": {"report": rel(PREV / 'report.html'), "responses": rel(PREV / 'responses.json'),
                        "manifest": rel(PREV / 'manifest.json'), "validation": rel(PREV / 'validation.json'),
                        "reuse_only": "B/C/D/E 24문항·120건의 기존 판단; 이전 검증을 재실행하지 않음"},
        "limitations": LIMITATIONS,
        "empirical_survey": False, "representative_sample": False, "statistical_estimation": False,
        "numeric_likert_responses_generated": False, "manuscript_modified": False, "hwpx_modified": False,
        "validation": {"command": f'python -X utf8 "{rel(OUT / "validate_review.py")}"',
                       "evidence": rel(OUT / 'validation.json'), "policy": "의미 있는 수용 검증 1회; 통과 후 반복하지 않음",
                       "browser_rendering_performed": False},
        "reproduction": {"build_command": f'python -X utf8 "{rel(OUT / "build_review.py")}"',
                         "note": "이미 validation.json이 있으면 재생성을 거부한다. 현재 캐시와 입력 해시를 고정한 구조·계산 재현이며 새 인지판단의 독립 재현이 아니다."},
        "artifact_hashes_evidence": "validation.json의 artifact_hashes에는 검증 파일 자신을 제외한 모든 산출물 해시를 기록한다.",
    }
    write_json('review.json', review)
    with (OUT / 'review.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: cell(v) for k, v in row.items()} for row in rows)
    write_json('input_cases.json', fixtures)
    write_json('manifest.json', manifest)
    (OUT / 'report.html').write_text(render_report(review, fixtures, manifest), encoding='utf-8')
    print(json.dumps({"built": ['review.json', 'review.csv', 'input_cases.json', 'manifest.json', 'report.html'],
                      "new_checks": len(rows), "artificial_cases": fixtures['case_count']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
