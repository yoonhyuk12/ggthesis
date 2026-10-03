"""Read-only appendix comparison; emit a targeted HWPX edit plan, never edit HWPX."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SECTION = "Contents/section2.xml"
APX1 = "01.docs/부록1_설문지_양식.md"
APX2 = "01.docs/부록2_설문항목_근거매핑.md"
DESIGN = "01.docs/04_연구설계.md"
HISTORY = "01.docs/설문항목_작업이력.md"


def plain(value: str) -> str:
    value = value.replace("**", "").replace("`", "")
    value = re.sub(r"<br\s*/?>", "\n", value)
    return html.unescape(value).strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", plain(value))


sources = {
    path: (ROOT / path).read_text(encoding="utf-8").splitlines()
    for path in [APX1, APX2, DESIGN, HISTORY]
}
paras_all = json.loads((HERE / "base_paras.json").read_text(encoding="utf-8"))
tables_all = json.loads((HERE / "base_tables.json").read_text(encoding="utf-8"))
paras = {p["idx"]: p for p in paras_all if p["section"] == SECTION}
tables = {t["idx"]: t for t in tables_all if t["section"] == SECTION}


def source_line(prefix: str, path: str = APX1) -> tuple[str, str]:
    hits = [(i + 1, x) for i, x in enumerate(sources[path]) if x.startswith(prefix)]
    assert hits, (path, prefix)
    assert len({plain(x) for _, x in hits}) == 1, (path, prefix, hits)
    return plain(hits[0][1]), f"{path}:{hits[0][0]}"


def item_map(path: str) -> dict[str, str]:
    result = {}
    for line in sources[path]:
        if re.match(r"\| [BCDE]-\d+ \|", line):
            cells = [plain(x) for x in line.strip().strip("|").split("|")]
            if cells[1] != "(동일)" and cells[0] not in result:
                result[cells[0]] = cells[1]
    return result


items = item_map(APX1)
plan = {
    "scope": "부록 설문지 도입·미도입 두 양식. 부록2는 내부 근거자료로서 대조에만 사용하고 수록하지 않음.",
    "replace": [],
    "insert_after": [],
    "remove_paragraphs": [],
    "replace_tables": [],
    "user_edits": [],
    "notes": [],
}


def replace(idx: int, new: str, src: str, reason: str) -> None:
    old = paras[idx]["text"]
    if old == new:
        return
    assert not paras[idx]["has_object"], idx
    plan["replace"].append({
        "section": SECTION, "idx": idx, "old_hwpx": old,
        "new": new, "md_source": src, "reason": reason,
    })


def from_line(indices: list[int], prefix: str, reason: str) -> None:
    new, src = source_line(prefix)
    for idx in indices:
        replace(idx, new, src, reason)


def insert(idx: int, blocks: list[tuple[str, str]], reason: str) -> None:
    plan["insert_after"].append({
        "section": SECTION,
        "idx": idx,
        "blocks": [{"kind": "paragraph", "text": text, "style_hint": hint} for text, hint in blocks],
        "reason": reason,
    })


# Two survey covers carry the same research purpose, disclosures and survey month.
from_line([2258, 2528], "본 설문은 건설현장의", "두 표지를 현행 Google Forms 온라인 자기응답 안내로 맞춤")
from_line([2259, 2529], "응답에는 정답이 없으며", "성명 수집·연구자 단독 열람·분석용 사본의 성명 제거·자발적 중단 안내 반영")
from_line([2262, 2532], "2026년 10월", "조사 예정 월 확정으로 해당 확정 필요 마커 해소")

# Administration is not an extra A question and is placed BEFORE Part A in both forms.
management = [
    (source_line("※ Part A는")[0], "note"),
    (source_line("※ 본 설문조사는")[0], "note"),
    (source_line("## 조사 관리용 입력")[0].removeprefix("## "), "heading"),
    (source_line("배포코드와 성명은")[0], "body"),
    (source_line("- 배포코드:")[0].removeprefix("- "), "body"),
    (source_line("- 성명:")[0].removeprefix("- "), "body"),
    (source_line("Google 계정 로그인과")[0], "note"),
]
for idx in [2266, 2536]:
    insert(idx, management, f"{APX1}:81-97의 공통 안내와 관리용 입력 2개를 Part A 앞에 배치. 측정 문항 수 18·30에서 제외")
from_line([2268, 2538], "※ 다음은 응답자의", "공통 기간 안내를 Part A 앞에 옮기고 A-3·A-4 숫자 입력 안내를 표시")


def question(number: int) -> tuple[str, str]:
    return source_line(f"**A-{number})**")


# Keep the original one-cell outer A table and its nested title table intact.
for offset in [0, 269]:
    for pidx, number in [(2274, 1), (2278, 3), (2280, 4), (2285, 6)]:
        text, src = question(number)
        replace(pidx + offset, " " + text, src, "A 문항을 현행 질문 문구로 맞춤")

    # A-3 numeric age and A-4 years + residual months replace categorical choices.
    text, src = source_line("&emsp;&emsp;만 (")
    replace(2279 + offset, " " + text, src, "연령대 보기를 만 나이 숫자 입력으로 변경")
    text, src = source_line("&emsp;&emsp;(&emsp;")
    replace(2281 + offset, " " + text, src, "경력 구간 보기를 년·개월 입력으로 변경")
    text, src = source_line("※ 여러 현장이나 업무의")
    replace(2282 + offset, text, src, "남은 경력 구간 문단을 겹치는 경력 중복 합산 금지·개월 0∼11 안내로 변경")

    # A-6 retains five choices and their existing three-paragraph placement.
    first, src = source_line("&emsp;&emsp;① 20억 원")
    first_two, third = first.split("③", 1)
    replace(2287 + offset, " " + first_two.rstrip(), src, "확정된 A-6 보기 ①·②; 조판상 기존 두 보기 한 문단 배치 유지")
    replace(2288 + offset, "     ③" + third, src, "A-6 보기 ③의 상한을 120억 원으로 반영")
    text, src = source_line("&emsp;&emsp;④ 120억 원")
    replace(2289 + offset, " " + text, src, "A-6 보기 ④·⑤의 120·150억 원 경계 반영")
    plan["remove_paragraphs"].append({
        "section": SECTION, "idx": 2286 + offset,
        "old_hwpx": paras[2286 + offset]["text"],
        "reason": "A-6 다섯 구간이 확정되어 공사금액 구간 기준 확정 필요 마커 삭제",
    })
    text, src = source_line("※ 총공사비는")
    insert(2289 + offset, [(text, "note")], f"{src}: 현장 전체·응답일 현재 최신 확정 금액·부가가치세·관급자재비 포함 기준 반영")

from_line([2291, 2560], "※ 다음 Part B의", "두 양식에 동일한 직전 1개월 기준·온라인 보기 선택 안내 반영")
from_line([2362, 2631], "※ 다음 Part C의", "두 양식에 동일한 직전 1개월 기준·온라인 보기 선택 안내 반영")
from_line([2405], "※ Part D는", "D의 문항별 직접 경험 안내를 유지하면서 비해당을 별도 선택지로 표시")
from_line([2476], "※ Part E에서는", "E의 같은 현장 도입 전 자동 알림 비교·기간 길이 미고정·경험 부재 비해당 안내 반영")

# Minimal D/E structure change: retain merged title and anchor-only header styling,
# append one unscored N/A cell to each row, and update only D-3/D-6 item text.
for table_idx, block in [(47, "D"), (48, "E")]:
    old_rows = [[c["text"] for c in row] for row in tables[table_idx]["rows"]]
    new_rows = [old_rows[0] + ["비해당\n(점수 아님)"]]
    for row in old_rows[1:]:
        new = list(row)
        new[1] = items[new[0]]
        new_rows.append(new + ["비해당"])
    plan["replace_tables"].append({
        "section": SECTION, "table_idx": table_idx,
        "old_rows": old_rows, "new_rows": new_rows,
        "md_source": f"{APX1}:Part {block} 문항표",
        "reason": "1∼5점 밖의 비해당 열 추가. 기존 머리행의 문항 영역 병합과 1·3·5점 앵커 표시는 보존; D-3·D-6은 현행 간소화 문구 반영" if block == "D" else "1∼5점 밖의 비해당 열 추가. 기존 머리행의 문항 영역 병합과 1·3·5점 앵커 표시 및 E 4문항은 보존",
    })

plan["user_edits"].extend([
    {
        "section": SECTION, "idx": 2272, "also_idx": 2541,
        "old_hwpx": "A. 실태조사 대상자 개요",
        "assessment": "MD에 독립적으로 적혀 있지 않은 기존 HWPX의 중첩 표 제목. 사용자가 직접 쓴 것인지 확인되지 않으나 내용 충돌이 없어 그대로 보존.",
        "action": "preserve",
    },
    {
        "section": SECTION, "table_indices": [45, 46, 47, 48, 52, 53],
        "assessment": "기존 리커트 표는 문항 영역 머리행을 병합하고 1·3·5점 의미만 앵커로 표시한다. 2·4점 의미는 표 위 척도 문장에 있다. 내용 충돌이 아닌 기존 조판 차이이므로 B·C 표를 재생성하지 않고 D·E 표의 같은 구조도 유지한다.",
        "action": "preserve_existing_header_merges_and_anchor_labels",
    },
])

plan["notes"].extend([
    "부록2 첫 위상 메모에 따라 근거 매핑은 논문 본문 수록 대상이 아니다. HWPX에도 부록2가 없으므로 신규 삽입하지 않는다.",
    "부록1의 맨 위 동기화·양식 메모, 두 양식 결합 안내, 내부 관리용 구성 대조표 및 그 아래 모집·분석 메모, 설문항목 작업이력은 삽입하지 않는다. 예산 인지와 1개월 정상 운용 모집 기준의 출판 본문 반영은 제4장 담당 계획에서 처리한다.",
    "두 벌 공통 A·B·C와 도입 벌 전용 D·E 모두 대조한다. 관리 입력은 두 양식에 각각 배포코드·성명 2개이며 A의 6문항·도입 30문항·미도입 18문항에 합산하지 않는다.",
    "insert_after 2266·2536은 표지 연구자 이메일 뒤이자 기존 Part A 앞이다. 첫 삽입 공통 안내 문단을 새 쪽에서 시작하고 기존 Part A의 새 쪽 시작을 보존한다. 새 관리용 heading 앞에는 필요한 경우 빈 문단 1개만 둔다. 조사 관리 쪽을 추가해도 표지와 각 Part의 시작 쪽 규칙은 유지한다.",
    "D/E replace_tables의 new_rows는 머리행 7셀, 문항행 8셀이다. 기존 머리행 첫 셀(시스템 특성 인식/경보 피로도 완화)은 문항번호+문항의 2개 논리 열을 병합한 셀로 계속 유지한다. 현재 colCnt=12 격자에서 기존 colSpan=2 응답 셀을 유지하고 비해당용 2개 논리 열을 끝에 추가하는 colCnt=14 방식이면 기존 병합 관계를 보존할 수 있다. 전체 폭은 보존하며 새 열에 필요한 폭을 재배분하고, 문항 열을 다른 열과 균등하게 만들지 않는다.",
    "A는 바깥 단일 셀 표 43·50 안에 제목 중첩 표 44·51이 들어 있다. A6 주석 삽입은 같은 바깥 셀 안의 마지막 보기 문단 뒤이며, 바깥/안쪽 폭과 중첩 구조를 보존한다. 한 쪽을 넘기면 메인이 실제 한글 출력에서 해결하며 단일 셀 내용을 자르거나 축약하지 않는다.",
    "새 표지의 긴 개인정보 안내와 관리용 입력 신설로 쪽수가 바뀔 수 있다. 표지 표 42·49의 끝문장과 소속·연락처, A 단일 셀 표, D/E 마지막 행을 재조판 후 PDF에서 확인한다.",
    "표지 개인정보 안내의 굵은 강조는 현행 MD의 '자발적' 및 '학술 연구를 위한 통계 분석에만'을 따른다. 옛 굵은 '무기명'의 스타일을 신규 문장 임의 위치에 물리지 않는다. A-1 등 문항 코드의 기존 강조와 나머지 실제 글꼴·크기는 보존한다.",
    "월 확정 마커 2곳은 '2026년 10월' 검정 본문으로 바꾸고 A-6 구간 미확정 마커 2문단만 제거한다. 다른 미완성 마커·연구자 연락 이메일은 건드리지 않는다.",
    "중복 제출을 허용한다는 문구나 응답 선택 우선순위는 추가하지 않는다. 현행 MD에 이미 있는 배포코드·성명의 '중복 제출 확인' 목적 설명만 그대로 따른다.",
    "MD 질문과 보기의 문구는 유지하며 꺾쇠 HTML·Markdown 강조 표식만 제거한다. 줄바꿈·들여쓰기·A-6 보기 문단 분할·표 머리행 앵커 양식은 기존 조판을 유지하는 차이다.",
])


def verify_plan() -> dict:
    """One evidence run for source-target mapping and the four survey source files."""
    checks = []

    def check(name: str, result: bool, detail=None):
        assert result, (name, detail)
        checks.append({"name": name, "passed": True, "detail": detail})

    check("fixed_schema", set(plan) == {
        "scope", "replace", "insert_after", "remove_paragraphs", "replace_tables", "user_edits", "notes"
    })
    keys = [(x["section"], x["idx"]) for x in plan["replace"]]
    check("unique_replacement_targets", len(set(keys)) == len(keys), len(keys))
    check("replacement_old_text_exact", all(paras[x["idx"]]["text"] == x["old_hwpx"] for x in plan["replace"]), len(keys))
    check("removal_old_text_exact", all(paras[x["idx"]]["text"] == x["old_hwpx"] for x in plan["remove_paragraphs"]), len(plan["remove_paragraphs"]))
    check("table_old_cells_exact", all(x["old_rows"] == [[c["text"] for c in row] for row in tables[x["table_idx"]]["rows"]] for x in plan["replace_tables"]), 2)
    covered_table_paras = {pidx for x in plan["replace_tables"] for row in tables[x["table_idx"]]["rows"] for c in row for pidx in c["p_indices"]}
    check("no_paragraph_table_double_edit", not (covered_table_paras & {x["idx"] for x in plan["replace"]}))
    check("all_targets_within_appendices", all(2248 <= x["idx"] <= 2672 for field in ["replace", "insert_after", "remove_paragraphs"] for x in plan[field]))

    design_items = item_map(DESIGN)
    mapping_items = item_map(APX2)
    check("three_current_sources_24_likert_equal", len(items) == 24 and items == design_items == mapping_items, {b: sum(k.startswith(b) for k in items) for b in "BCDE"})
    current_history = "\n".join(sources[HISTORY]).split("## 과거 결정 기록 — 원문 보존", 1)[0]
    check("fourth_source_history_current_decisions", all(x in current_history for x in [items["D-3"], items["D-6"], "년·개월", "부가가치세", "관급자재비", "직전 1개월", "같은 현장", "비교 기간 길이를 따로 정하지", "1개월 이상 정상 운용", "예산을 알고", "Google 계정 로그인 없이", "연구자 본인만", "모두 필수 입력", "관리용 입력 2개"]))

    replacement = {x["idx"]: x["new"] for x in plan["replace"]}
    inserted = {x["idx"]: x["blocks"] for x in plan["insert_after"]}
    deleted = {x["idx"] for x in plan["remove_paragraphs"]}

    def simulated_table_cell(table_idx: int):
        texts = []
        for row in tables[table_idx]["rows"]:
            for cell in row:
                for pidx in cell["p_indices"]:
                    if pidx not in deleted:
                        texts.append(replacement.get(pidx, paras[pidx]["text"]))
                    texts.extend(b["text"] for b in inserted.get(pidx, []))
        return "\n".join(texts)

    atexts = [simulated_table_cell(t) for t in [43, 50]]
    q = [question(i)[0] for i in range(1, 7)]
    check("six_A_questions_in_each_form", all(all(compact(x) in compact(t) for x in q) for t in atexts), 12)
    numeric_lines = [source_line("&emsp;&emsp;만 (")[0], source_line("&emsp;&emsp;(&emsp;")[0], source_line("※ 여러 현장이나 업무의")[0]]
    check("numeric_A3_A4_and_nonoverlap_guidance", all(all(compact(x) in compact(t) for x in numeric_lines) for t in atexts))
    cost_options = ["① 20억 원 미만", "② 20억 원 이상∼50억 원 미만", "③ 50억 원 이상∼120억 원 미만", "④ 120억 원 이상∼150억 원 미만", "⑤ 150억 원 이상"]
    cost_note = source_line("※ 총공사비는")[0]
    check("five_A6_options_and_whole_site_confirmed_cost_note", all(all(compact(x) in compact(t) for x in [*cost_options, cost_note]) for t in atexts))
    check("obsolete_A_categories_and_cost_marker_removed", all(all(x not in t for x in ["귀하의 연령대", "① 3년 미만", "50억 원 이상 ∼ 100억 원", "공사금액 구간 기준"]) for t in atexts))
    check("common_A_forms_identical", compact(atexts[0]) == compact(atexts[1]))

    eventual_likert = []
    for table_idx in [45, 46, 47, 48, 52, 53]:
        changed = next((x for x in plan["replace_tables"] if x["table_idx"] == table_idx), None)
        rows = changed["new_rows"] if changed else [[c["text"] for c in row] for row in tables[table_idx]["rows"]]
        eventual_likert.extend((row[0], row[1], row[2:]) for row in rows[1:])
    check("all_36_printed_likert_occurrences_match_MD", len(eventual_likert) == 36 and all(items[c] == text for c, text, _ in eventual_likert))
    counts = Counter(c[0] for c, _, _ in eventual_likert)
    check("two_common_one_exclusive_forms", counts == {"B": 16, "C": 8, "D": 8, "E": 4}, dict(counts))
    check("five_scores_and_NA_only_in_DE", all(choices == ["①", "②", "③", "④", "⑤"] + (["비해당"] if code[0] in "DE" else []) for code, _, choices in eventual_likert))
    check("DE_12_NA_choices", sum(choices[-1] == "비해당" for _, _, choices in eventual_likert) == 12)
    check("DE_merged_header_retained", all(len(x["new_rows"][0]) == 7 and all(len(r) == 8 for r in x["new_rows"][1:]) and x["new_rows"][0][:-1] == x["old_rows"][0] for x in plan["replace_tables"]))
    check("B_C_tables_unmodified", {x["table_idx"] for x in plan["replace_tables"]} == {47, 48})
    check("common_guidance_and_administration_identical", inserted[2266] == inserted[2536])
    admin_text = "\n".join(x["text"] for x in inserted[2266])
    check("administration_count_and_field_names", all(x in admin_text for x in ["18문항 또는 30문항", "배포코드: [입력]", "성명: [입력]", "모두 필수 입력", "척도 점수가 아닙니다", "제출 전 언제든지"]))
    check("same_site_E_baseline_and_no_fixed_period", all(x in replacement[2476] for x in ["비교 기간의 길이를 따로 정하지", "현재 담당 현장", "도입 전에", "자동 알림", "전반적인 경험", "비해당", "A∼D"]))
    check("same_BC_one_month_guidance_both_forms", replacement[2291] == replacement[2560] and replacement[2362] == replacement[2631] and "직전 1개월" in replacement[2291] and "직전 1개월" in replacement[2362])
    check("identical_two_cover_disclosures", replacement[2258] == replacement[2528] and replacement[2259] == replacement[2529] and replacement[2262] == replacement[2532] == "2026년 10월")
    check("cover_identified_data_handling", all(x in replacement[2259] for x in ["성명을 수집", "로그인은 요구하지", "이메일은 수집하지", "연구자 본인만", "사본에서는 성명을 제거", "분리하여 보관", "제출 전"]))
    check("researcher_contact_email_preserved", all("yoonhyeok1@gmail.com" in paras[i]["text"] and i not in replacement and i not in deleted for i in [2266, 2536]))
    added_text = "\n".join([x["new"] for x in plan["replace"]] + [b["text"] for x in plan["insert_after"] for b in x["blocks"]] + [c for x in plan["replace_tables"] for row in x["new_rows"] for c in row])
    check("no_duplicate_submission_permission_added", not re.search(r"중복 제출.{0,20}허용|중복 제출 허용", added_text))
    check("no_internal_material_added", all(x not in added_text for x in ["구성 대조표", "근거 매핑", "과거 결정 기록", "Google Forms 관리 계정·권한의 구체 설정"]))
    check("no_markup_artifacts", all(x not in added_text for x in ["**", "&emsp;", "<br>", "<div", "## "]))
    return {
        "passed": True,
        "check_count": len(checks),
        "checks": checks,
        "counts": {field: len(plan[field]) for field in ["replace", "insert_after", "remove_paragraphs", "replace_tables", "user_edits"]},
        "inserted_paragraphs": sum(len(x["blocks"]) for x in plan["insert_after"]),
        "printed_question_occurrences": {"A": 12, "B": 16, "C": 8, "D": 8, "E": 4, "total": 48},
        "unique_questions": 30,
        "admin_inputs": {"per_form": 2, "printed_total": 4},
    }


if __name__ == "__main__":
    verification = verify_plan()
    plan["notes"].append("대조 검증 1회: " + json.dumps(verification, ensure_ascii=False))
    (HERE / "plan_appendices.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))
