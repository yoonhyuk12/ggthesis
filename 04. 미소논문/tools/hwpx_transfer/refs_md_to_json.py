# -*- coding: utf-8 -*-
"""01.docs/08.참고문헌.md → tools/hwpx_transfer/staging/references.json 변환기.

원고의 가·나·다·라 절은 '확보 시점'별 묶음이므로 무시하고, 각 항목의 하위 소제목으로
학교 양식 5종 분류(가. 학위논문 / 나. 학술지 / 다. 보고서 / 라. 관련법 / 마. 기타)에
재배치한다. 서지 문자열은 원고 그대로 쓰며(창작·보완 없음) 마크다운 기울임 마커만 뗀다.

스키마는 staging/references_yoonhyuk_reference.json 과 동일하다
(meta / categories / flagged / sort_rule). 항목 필드도 no·text·source_ref(+note)로 같고,
브리프 규칙 3에 따라 원고 태그 보존용 `id` 만 추가한다.

표준 라이브러리만 사용. 실행:
    PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/refs_md_to_json.py
"""

import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # 04. 미소논문/
SRC_MD = os.path.join(ROOT, "01.docs", "08.참고문헌.md")
STAGING = os.path.join(HERE, "staging")
OUT_JSON = os.path.join(STAGING, "references.json")
OUT_REPORT = os.path.join(STAGING, "references_report.md")
REF_JSON = os.path.join(STAGING, "references_yoonhyuk_reference.json")

CATEGORIES = ["가. 학위논문", "나. 학술지", "다. 보고서", "라. 관련법", "마. 기타"]

# 마크다운 기울임 마커만 제거한다. 여는 별표 앞이 단어문자면(예: "G*Power") 강조가 아니다.
EMPH = re.compile(r"(?<![\w*])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![\w*])")
STRIKE = re.compile(r"~~(.+?)~~")

ENTRY = re.compile(r"^\[(\d{2})\]\s+(.*)$")
H2 = re.compile(r"^##\s+(.*)$")
H3 = re.compile(r"^###\s+(.*)$")
BULLET = re.compile(r"^-\s+(.*)$")

# 분류가 애매해 flagged 에 남길 항목 (id → 사유). 서지는 그대로 채택하되 판단 근거를 남긴다.
UNCERTAIN = {
    "09": "학술대회 논문집(NeurIPS Proceedings)이나 원고가 '학술지·학회지' 소제목에 두었다. 양식의 '나. 학술지'로 배치.",
    "10": "학술대회 논문집(EMNLP Proceedings)이나 원고가 '학술지·학회지' 소제목에 두었다. 양식의 '나. 학술지'로 배치.",
    "11": "학술대회 논문집(NeurIPS Proceedings)이나 원고가 '학술지·학회지' 소제목에 두었다. 양식의 '나. 학술지'로 배치.",
    "12": "학술대회 논문집(NeurIPS Proceedings)이나 원고가 '학술지·학회지' 소제목에 두었다. 양식의 '나. 학술지'로 배치.",
    "14": "웹 기반 지원시스템(KRAS) 안내이며 간행물이 아니다. 원고의 '보고서' 소제목을 따라 '다. 보고서'로 배치했으나 '마. 기타'(웹자료)도 가능.",
    "17": "정기 동향 브리핑(건설동향브리핑 제1019호) — 학술지로도 볼 수 있으나 원고의 '보고서' 소제목을 따라 '다. 보고서'로 배치.",
    "40": "White Paper(기관 발간물) — 원고의 '국외 단행본·단행본 장' 소제목을 따라 '마. 기타'로 배치했으나 '다. 보고서'도 가능.",
    "49": "협회 발행 교육 지면(안전기술 통권 60호) — 학술지 위계가 아니나 원고의 '학술지·학회지' 소제목을 따라 '나. 학술지'로 배치.",
    "53": "기술지침(KOSHA GUIDE P-140-2020) — 고시가 아니므로 '라. 관련법'이 아닌 '다. 보고서'로 배치.",
}

NOTE = {
    "20": "arXiv 프리프린트 — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "39": "국외 단행본 — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "40": "국외 White Paper — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "41": "국외 단행본 — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "42": "국외 단행본 — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "43": "국외 단행본 장(In: Hoyle Ed.) — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
    "60": "국외 단행본 — 5분류에 자연 슬롯이 없어 '마. 기타' 배치",
}

SORT_RULE = (
    "각 분류 내 정렬: 국내문헌(저자 첫 글자가 한글) 먼저 저자명 가나다순 → 국외문헌 "
    "제1저자 성(姓) 알파벳순. 동일 저자는 발행연도 오름차순. "
    "정렬 키는 서지 문자열의 연도 괄호 앞부분(저자 또는 법령명)이며, 원고 상단 [정리 규칙] "
    "'국내문헌은 저자명 가나다순, 국외문헌은 저자 성(姓) 알파벳순'을 5분류 체계에 적용한 것이다. "
    "번호(no)는 분류별로 1부터 재시작하고, 원고의 [01]~[60] 태그는 각 항목 id 에 보존한다."
)


def classify(sub):
    """항목의 하위 소제목 문자열 → 양식 5분류."""
    if "학위논문" in sub:
        return "가. 학위논문"
    if "단행본" in sub or "기타" in sub or "Preprint" in sub or "웹자료" in sub:
        return "마. 기타"
    if "학술지" in sub or "학회지" in sub:
        return "나. 학술지"
    if "관련법" in sub or "고시" in sub:
        return "라. 관련법"
    if "보고서" in sub or "간행물" in sub:
        return "다. 보고서"
    raise ValueError("분류 불가 소제목: %r" % sub)


def strip_emphasis(text):
    """마크다운 기울임 마커만 제거한다. 제거 여부를 함께 돌려준다."""
    new = EMPH.sub(r"\1", text)
    return new, new != text


def sort_key(text):
    """(국내0/국외1, 저자키, 연도) — 국내 가나다 → 국외 알파벳."""
    m = re.match(r"^(.*?)\((\d{4})\)", text)
    if m:
        name, year = m.group(1).strip(), m.group(2)
    else:
        name = re.split(r"[,(]", text, 1)[0].strip()
        ym = re.search(r"\((\d{4})\.", text)
        year = ym.group(1) if ym else "0000"
    first = name[0] if name else ""
    domestic = 0 if "HANGUL" in unicodedata.name(first, "") else 1
    key = name if domestic == 0 else name.casefold()
    return (domestic, key, year, text)


def parse(md_text):
    """원고를 (채택 항목, 마절 불릿) 으로 가른다."""
    entries, todos = [], []
    section = sub = ""
    for raw in md_text.splitlines():
        line = raw.strip()
        m = H2.match(line)
        if m:
            section, sub = m.group(1).strip(), ""
            continue
        m = H3.match(line)
        if m:
            sub = m.group(1).strip()
            continue
        in_todo_section = section.startswith("마.")
        m = ENTRY.match(line)
        if m and not in_todo_section:
            entries.append({"id": m.group(1), "raw": m.group(2).strip(),
                            "section": section, "sub": sub})
            continue
        m = BULLET.match(line)
        if m and in_todo_section:
            todos.append({"raw": m.group(1).strip(), "section": section, "sub": sub})
    return entries, todos


def build(entries, todos):
    buckets = {c: [] for c in CATEGORIES}
    flagged = []
    marker_ids, dup_ids = [], []
    seen = {}

    for e in entries:
        text, changed = strip_emphasis(e["raw"])
        if changed:
            marker_ids.append(e["id"])
        norm = re.sub(r"\s+", " ", text).strip().rstrip(".")
        src = "08.참고문헌.md %s / %s [%s]" % (e["section"], e["sub"], e["id"])
        if norm in seen:
            dup_ids.append(e["id"])
            flagged.append({
                "text": text,
                "reason": "duplicate — 원고 [%s]는 [%s]와 같은 서지다. 채택본은 [%s] 하나만 남겼다."
                          % (e["id"], seen[norm], seen[norm]),
                "source_ref": src,
            })
            continue
        seen[norm] = e["id"]
        cat = classify(e["sub"])
        item = {"no": 0, "id": e["id"], "text": text, "source_ref": src}
        if e["id"] in NOTE:
            item["note"] = NOTE[e["id"]]
        buckets[cat].append(item)
        if e["id"] in UNCERTAIN:
            flagged.append({
                "text": text,
                "reason": "category_uncertain — %s (본문에는 수록함)" % UNCERTAIN[e["id"]],
                "source_ref": src,
            })

    for cat in CATEGORIES:
        buckets[cat].sort(key=lambda it: sort_key(it["text"]))
        for i, it in enumerate(buckets[cat], 1):
            it["no"] = i

    if marker_ids:
        flagged.append({
            "text": "마크다운 기울임(*…*) 마커 제거 대상: " + ", ".join(
                "[%s]" % i for i in sorted(marker_ids)),
            "reason": "md_marker_removed — 원고 서지의 서명·게재지 강조 표기에서 별표만 제거했다. "
                      "글자는 그대로이며 'G*Power' 처럼 단어 안의 별표는 건드리지 않았다. (본문에는 수록함)",
            "source_ref": "08.참고문헌.md 전체 (가~라 절)",
        })

    for t in todos:
        text = STRIKE.sub(r"\1", strip_emphasis(t["raw"])[0])
        resolved = t["raw"].startswith("~~")
        flagged.append({
            "text": text,
            "reason": "cite_todo — 원고 '마. 추가 확보 필요 문헌(CiteTodo — 잔여)' %s 항목. %s "
                      "임의 서지를 만들지 않으며 참고문헌 본문에서 제외한다."
                      % (t["sub"] or "(소제목 없음)",
                         "원고에 취소선으로 해소 표기됨(이력 보존)." if resolved else "미해소 — 원문 확보 필요."),
            "source_ref": "08.참고문헌.md %s / %s" % (t["section"], t["sub"]),
        })

    meta = {
        "generated_from": "01.docs/08.참고문헌.md (단일 기준, 2026-09-12 변환 · tools/hwpx_transfer/refs_md_to_json.py)",
        "policy": "원고의 번호 항목 [01]~[60]만 categories에 수록하고, 서지 문자열은 원고 그대로 사용한다"
                  "(저자·연도·제목·게재지·권호·쪽·DOI 창작·보완 없음. 마크다운 기울임 마커만 제거). "
                  "'마. 추가 확보 필요 문헌(CiteTodo — 잔여)' 절 전체와 그 하위 '(5) 부분 검증'·"
                  "'(6) 설계 전환으로 불요' 항목은 본문에서 제외하고 flagged에 cite_todo 사유로만 남겼다. "
                  "[45] 서용하(2013)의 [UNVERIFIED] 표기는 원고 표기이므로 서지 문자열에 그대로 둔다.",
        "category_assumptions": "원고의 가·나·다·라 절은 확보 시점별 묶음이므로 분류에 쓰지 않고, 각 항목의 "
                                "하위 소제목((1) 학위논문 / (2) 학술지·학회지 / (3) 보고서·정부공공기관 간행물 / "
                                "(4) 관련법·고시 / (5) 기타·단행본·Preprint)으로 학교 양식 5분류에 재배치했다. "
                                "단행본·단행본 장·Preprint·웹자료는 '마. 기타', 정부·공공기관 간행물은 '다. 보고서', "
                                "고시는 '라. 관련법'에 넣었다. 판단이 애매한 항목은 flagged의 category_uncertain에 남겼다.",
    }
    return {"meta": meta, "categories": buckets, "flagged": flagged,
            "sort_rule": SORT_RULE}, marker_ids, dup_ids


def schema_diff(data):
    """기준 파일과 최상위 키·항목 필드 동일성 비교 문자열."""
    lines = []
    with open(REF_JSON, encoding="utf-8") as f:
        base = json.load(f)
    lines.append("최상위 키    기준=%s" % list(base.keys()))
    lines.append("             생성=%s  -> %s"
                 % (list(data.keys()),
                    "동일" if list(base.keys()) == list(data.keys()) else "불일치"))
    lines.append("분류 키      기준=%s" % list(base["categories"].keys()))
    lines.append("             생성=%s  -> %s"
                 % (list(data["categories"].keys()),
                    "동일" if list(base["categories"].keys()) == list(data["categories"].keys()) else "불일치"))
    bf = set()
    for v in base["categories"].values():
        for it in v:
            bf |= set(it)
    nf = set()
    for v in data["categories"].values():
        for it in v:
            nf |= set(it)
    lines.append("항목 필드    기준=%s" % sorted(bf))
    lines.append("             생성=%s" % sorted(nf))
    lines.append("             기준 ⊆ 생성 : %s / 생성 추가분 : %s"
                 % (bf <= nf, sorted(nf - bf) or "없음"))
    bfl = set()
    for f_ in base["flagged"]:
        bfl |= set(f_)
    nfl = set()
    for f_ in data["flagged"]:
        nfl |= set(f_)
    lines.append("flagged 필드 기준=%s  생성=%s  -> %s"
                 % (sorted(bfl), sorted(nfl), "동일" if bfl == nfl else "불일치"))
    lines.append("meta 키      기준=%s" % list(base["meta"].keys()))
    lines.append("             생성=%s  -> %s"
                 % (list(data["meta"].keys()),
                    "동일" if list(base["meta"].keys()) == list(data["meta"].keys()) else "불일치"))
    lines.append("sort_rule 형 기준=%s  생성=%s  -> %s"
                 % (type(base["sort_rule"]).__name__, type(data["sort_rule"]).__name__,
                    "동일" if type(base["sort_rule"]) is type(data["sort_rule"]) else "불일치"))
    lines.append("add_references() 소비 필드 no·text 결손 : %d건"
                 % sum(1 for v in data["categories"].values() for it in v
                       if not isinstance(it.get("no"), int) or not it.get("text")))
    return "\n".join(lines)


def fidelity_check(data, entries):
    """원고 서지 문자열이 별표 외에는 한 글자도 바뀌지 않았음을 재현 가능하게 검사한다."""
    lines = []
    orig = {e["id"]: e["raw"] for e in entries}
    got = {}
    for v in data["categories"].values():
        for it in v:
            got[it["id"]] = it["text"]
    lines.append("원고 id 집합 == JSON id 집합 : %s (원고 %d · JSON %d)"
                 % (set(orig) == set(got), len(orig), len(got)))
    diff = [i for i in orig if orig[i].replace("*", "") != got.get(i, "").replace("*", "")]
    lines.append("별표를 제외한 문자열 불일치 : %d건 %s"
                 % (len(diff), sorted(diff) if diff else ""))
    kept = sorted(i for i, t in got.items() if "*" in t)
    lines.append("별표가 남은 항목 : %s (단어 내부 별표이므로 보존이 정상)"
                 % (", ".join("[%s]" % i for i in kept) or "없음"))
    bad_no = [c for c, v in data["categories"].items()
              if [it["no"] for it in v] != list(range(1, len(v) + 1))]
    lines.append("분류별 no 1..n 연속성 : %s" % ("전 분류 통과" if not bad_no else "실패 %s" % bad_no))
    return "\n".join(lines)


def build_report(data, entries, todos, marker_ids, dup_ids, diff_text, fid_text):
    counts = {c: len(v) for c, v in data["categories"].items()}
    adopted = sum(counts.values())
    total = len(entries)
    kinds = {}
    for f in data["flagged"]:
        code = f["reason"].split(" — ")[0]
        kinds[code] = kinds.get(code, 0) + 1
    L = []
    L.append("# references.json 생성 리포트 (W2)")
    L.append("")
    L.append("- 입력: `01.docs/08.참고문헌.md`")
    L.append("- 출력: `tools/hwpx_transfer/staging/references.json`")
    L.append("- 변환기: `tools/hwpx_transfer/refs_md_to_json.py` (표준 라이브러리, 재실행 가능)")
    L.append("- 스키마 기준: `tools/hwpx_transfer/staging/references_yoonhyuk_reference.json`, "
             "필드 소비처 `../tools/hwpx_transfer/blocks_to_hwpx.py :: add_references()` "
             "(읽는 필드는 `categories`의 `no`·`text`, 그리고 `flagged` 길이)")
    L.append("")
    L.append("## 1. 분류별 건수")
    L.append("")
    L.append("| 분류 | 건수 | 원고 태그 |")
    L.append("|---|---:|---|")
    for c in CATEGORIES:
        ids = ", ".join("[%s]" % it["id"] for it in data["categories"][c])
        L.append("| %s | %d | %s |" % (c, counts[c], ids or "—"))
    L.append("| **계(채택)** | **%d** | |" % adopted)
    L.append("")
    L.append("## 2. 산식 — 원고 총 항목 = 채택 + 제외 + 중복")
    L.append("")
    L.append("원고의 번호 서지 항목(`[01]`~`[60]`) 총 **%d**건." % total)
    L.append("")
    L.append("```")
    L.append("원고 총 항목 %d = 채택 %d + 제외 %d + 중복 %d"
             % (total, adopted, total - adopted - len(dup_ids), len(dup_ids)))
    L.append("```")
    L.append("")
    L.append("- 채택 %d = %s" % (adopted, " + ".join("%s %d" % (c, counts[c]) for c in CATEGORIES)))
    L.append("- 제외(번호 항목 중) %d건 — 번호 서지 항목은 전량 채택했다. 본문 제외 대상은 번호가 없는 "
             "`## 마. 추가 확보 필요 문헌 (CiteTodo — 잔여)` 절의 불릿 **%d건**이며, 이는 서지 번호 총계와 별개다."
             % (total - adopted - len(dup_ids), len(todos)))
    L.append("- 중복 %d건 — %s"
             % (len(dup_ids),
                ", ".join("[%s]" % i for i in dup_ids) if dup_ids
                else "없음(공백 정규화·말미 마침표 제거 후 문자열 동일 항목 없음)"))
    L.append("")
    L.append("제외 절을 포함한 확장 산식:")
    L.append("")
    L.append("```")
    L.append("원고 서지 항목 %d + CiteTodo 불릿 %d = 원고 총 항목 %d"
             % (total, len(todos), total + len(todos)))
    L.append("  = categories 수록 %d + flagged cite_todo %d + 중복 %d"
             % (adopted, kinds.get("cite_todo", 0), len(dup_ids)))
    L.append("  = %d" % (adopted + kinds.get("cite_todo", 0) + len(dup_ids)))
    L.append("```")
    L.append("")
    L.append("## 3. flagged 목록 (%d건)" % len(data["flagged"]))
    L.append("")
    L.append("사유 코드별 건수: " + ", ".join("`%s` %d건" % (k, v) for k, v in sorted(kinds.items())))
    L.append("")
    L.append("> ⚠️ 주의 — `flagged`에는 **본문 제외 항목(cite_todo)** 과 **본문에 수록했으나 기록만 남긴 "
             "항목(category_uncertain·md_marker_removed)** 이 섞여 있다. 기준 스키마에 둘을 가르는 필드가 "
             "없어 사유 문자열 앞머리 코드로 구분했다. `add_references()`가 자동으로 다는 "
             "\"flagged N건은 본문에 넣지 않았다\" 주석은 이 구분을 못 하므로, 실제 본문 제외 건수는 "
             "cite_todo **%d건**이다." % kinds.get("cite_todo", 0))
    L.append("")
    for i, f in enumerate(data["flagged"], 1):
        L.append("%d. **%s**" % (i, f["reason"].split(" — ")[0]))
        L.append("   - text: %s" % f["text"])
        L.append("   - reason: %s" % f["reason"])
        L.append("   - source_ref: %s" % f["source_ref"])
    L.append("")
    L.append("## 4. 기준 파일과의 스키마 비교 (python 출력)")
    L.append("")
    L.append("```")
    L.append(diff_text)
    L.append("```")
    L.append("")
    L.append("")
    L.append("### 4-1. 서지 문자열 무결성 검사 (python 출력)")
    L.append("")
    L.append("```")
    L.append(fid_text)
    L.append("```")
    L.append("")
    L.append("`id`는 브리프 규칙 3(\"앞 번호 `[01]` 같은 태그는 제거하고 `id` 필드에 보존\")에 따라 추가한 "
             "필드이며, 기준 파일의 필드는 모두 그대로 유지한다. `note`는 기준 파일 '마. 기타' 항목이 쓰던 "
             "필드를 같은 용도로 썼다.")
    L.append("")
    L.append("## 5. 결정 사항")
    L.append("")
    L.append("- 원고의 `## 가.`~`## 라.` 절(확보 시점별 묶음)은 분류에 쓰지 않고, 각 항목의 `###` 소제목으로 "
             "양식 5분류에 재배치했다. 매핑: 학위논문→가 / 학술지·학회지→나 / 보고서·정부공공기관 간행물→다 / "
             "관련법·고시→라 / 기타·단행본·단행본 장·Preprint·웹자료→마.")
    L.append("- 서지 문자열은 손대지 않았다. 유일한 변형은 마크다운 기울임 별표 제거(**%d건**)다. "
             "`G*Power`처럼 단어 내부의 별표는 강조가 아니므로 보존했다(정규식 좌측 lookbehind로 배제)."
             % len(marker_ids))
    L.append("- `[45] 서용하(2013)`의 `[UNVERIFIED — 학과·페이지수 미확인…]`은 원고 본문 표기이므로 서지에 "
             "남겼다. hwpx 조립 시 빨간색 마커 규칙(`[UNVERIFIED` 접두사)이 그대로 적용된다.")
    L.append("- `[14]`는 법적 근거 괄호(`— [54] 참조` 포함)까지 원고 그대로 옮겼다.")
    L.append("- 번호(`no`)는 분류별 1부터 재시작한다. 조립기가 `[%02d]` 형식으로 출력한다.")
    L.append("")
    L.append("## 6. 미해결 사항")
    L.append("")
    L.append("- 분류 애매 %d건(`category_uncertain`)은 지도교수 양식 대조 후 최종 확정이 필요하다."
             % kinds.get("category_uncertain", 0))
    L.append("- 원고 상단 [정리 규칙]의 \"본문 실인용 문헌과 상호 대조\"는 본 작업 범위 밖이다(G3 과제). "
             "특히 원고 주석이 예고한 `[26]~[38]·[41]·[43]`(SEM·요인구조 전용 인용)의 실인용 재판정은 "
             "이 파일에서 수행하지 않았다 — 전량 수록 상태다.")
    L.append("- `라. 관련법` 3건은 저자가 없어 법령명 가나다순으로 정렬했다. 양식이 법률→고시 위계 순을 "
             "요구하면 재정렬이 필요하다.")
    return "\n".join(L) + "\n"


def main():
    with open(SRC_MD, encoding="utf-8") as f:
        md_text = f.read()
    entries, todos = parse(md_text)
    data, marker_ids, dup_ids = build(entries, todos)
    if not os.path.isdir(STAGING):
        os.makedirs(STAGING)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    diff_text = schema_diff(data)
    fid_text = fidelity_check(data, entries)
    with open(OUT_REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_report(data, entries, todos, marker_ids, dup_ids, diff_text, fid_text))
    sys.stdout.write("원고 서지 항목 %d건 · CiteTodo 불릿 %d건 파싱\n" % (len(entries), len(todos)))
    for c in CATEGORIES:
        sys.stdout.write("  %s : %d건\n" % (c, len(data["categories"][c])))
    sys.stdout.write("flagged %d건 · 기울임 마커 제거 %d건 · 중복 %d건\n"
                     % (len(data["flagged"]), len(marker_ids), len(dup_ids)))
    sys.stdout.write(diff_text + "\n")
    sys.stdout.write(fid_text + "\n")
    sys.stdout.write("-> %s\n-> %s\n" % (OUT_JSON, OUT_REPORT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
