"""설문 응답 원본(Google Forms xlsx) → 통합 원자료·코딩 DataFrame.

원본은 읽기만 한다. 코딩 규칙의 단일 원본은
03.plan/261024_0850_설문응답_정리_분석_원고반영_계획.md 0.3·0.4절이며, 이 모듈은 그 규칙을 그대로 옮긴 것이다.

사용 예 (저장소 루트에서):
    from tools.survey_analysis.coding import build
    result = build()
    result.analysis   # 분석자료(ASCII 변수명, 성명·현장명 제외)
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_REL = Path("01.docs/설문결과/중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구(응답).xlsx")
SRC_PATH = REPO_ROOT / SRC_REL
SRC_SHA256 = "e81a9f6fb5e2557024bdade531bd467a6701944a6d458699334ce94d34f68027"
SRC_SHEET = "설문지 응답 시트1"

# ---------------------------------------------------------------- 열 구조 (1-based)
COL_TIMESTAMP, COL_BRANCH, COL_SITE, COL_NAME = 1, 2, 3, 4
A_ITEMS = [f"A{i}" for i in range(1, 10)]
B_ITEMS = [f"B{i}" for i in range(1, 9)]
C_ITEMS = [f"C{i}" for i in range(1, 5)]
D_ITEMS = [f"D{i}" for i in range(1, 9)]
E_ITEMS = [f"E{i}" for i in range(1, 5)]
ITEMS = A_ITEMS + B_ITEMS + C_ITEMS + D_ITEMS + E_ITEMS
LIKERT_ITEMS = B_ITEMS + C_ITEMS + D_ITEMS + E_ITEMS

# 도입 분기: 5~37열 = A1..E4, 미도입 분기: 38~58열 = A1..C4
ADOPT_COLS = {item: 5 + i for i, item in enumerate(ITEMS)}
NONADOPT_COLS = {item: 38 + i for i, item in enumerate(A_ITEMS + B_ITEMS + C_ITEMS)}
ADOPT_RANGE = range(5, 38)
NONADOPT_RANGE = range(38, 59)

BRANCH_ADOPT = "CCTV YOLO-LLM 안전알림 도입 현장"
BRANCH_NONADOPT = "CCTV YOLO-LLM 안전알림 미도입 현장"
GROUP_MAP = {BRANCH_ADOPT: 1, BRANCH_NONADOPT: 0}

# ---------------------------------------------------------------- 값 코딩 사전 (부록1 보기 순서)
LIKERT_MAP = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}
LIKERT_LABELS = {1: "① 전혀 그렇지 않다", 2: "② 그렇지 않다", 3: "③ 보통이다", 4: "④ 그렇다", 5: "⑤ 매우 그렇다"}

CAT_MAPS: dict[str, dict[str, int]] = {
    "A1": {"시공사": 1, "발주청(공사감독·감리원 포함)": 2},
    "A2": {"남성": 1, "여성": 2},
    "A5": {"공사감독": 1, "안전관리자": 2, "현장소장": 3},           # 그 외 텍스트 = 4(기타)
    "A6": {"20억 원 미만": 1, "20억 원 이상∼50억 원 미만": 2,
           "50억 원 이상∼120억 원 미만": 3, "120억 원 이상": 4},
    "A7": {"알게 될 방법이 없다": 1, "작업자나 반장의 전화·보고": 2,
           "사무실 등에서 CCTV 화면을 직접 본다": 3, "자동 알림(문자·메신저·앱)을 받는다": 4},  # 그 외 = 5(기타)
    "A8": {"다음 순찰 때": 1, "누군가 알려줄 때": 2, "발생 직후 알림으로": 3, "모르고 지나가는 경우가 많다": 4},
    "A9": {"즉시∼5분": 1, "5분 초과∼30분": 2, "30분 초과∼1시간": 3, "1시간 초과 또는 다음 순찰 때": 4},
}
OTHER_CODE = {"A5": 4, "A7": 5}            # 기타 코드
NONRESPONSE_TEXTS = {".", "-", "", "없음"}  # 기타 자리의 무응답 표기 (관측된 것은 "." 1건)

CAT_LABELS: dict[str, dict[int, str]] = {k: {v: t for t, v in m.items()} for k, m in CAT_MAPS.items()}
CAT_LABELS["A5"][4] = "기타"
CAT_LABELS["A7"][5] = "기타"

# 시험 응답 제외 (계획 0.4) — 원본 행 번호 + 내용 대조로 판정
EXCLUSIONS = {
    2: ("2026-10-14 10:31:32", "테스트", "시험 응답(현장명 '테스트')"),
    3: ("2026-10-14 10:32:38", "없음", "연구자 본인 시험 응답(현장명 '없음')"),
}

# ---------------------------------------------------------------- 파생 변수 정의 (04장 제3절·제5절)
# 이름: (구성 문항, 도입 집단 전용 여부). 해당 문항 전부 응답 시에만 평균.
DERIVED: dict[str, tuple[list[str], bool]] = {
    "Y_total": (B_ITEMS, False),
    "Y1": (["B1"], False),
    "Y2": (["B2"], False),
    "Y3": (["B3", "B4"], False),
    "Y4": (["B5", "B6"], False),
    "Y5": (["B7", "B8"], False),
    "W": (C_ITEMS, False),
    "D_sub1": (["D1", "D2"], True),
    "D_sub2": (["D3", "D4"], True),
    "D_sub3": (["D5", "D6"], True),
    "D_sub4": (["D7", "D8"], True),
    "D_total": (D_ITEMS, True),
    "E_total": (E_ITEMS, True),
}

# 분석자료(ASCII) 열 순서
ANALYSIS_COLUMNS = (
    ["resp_id", "group", "A1_affil", "A2_sex", "A3_age", "A4_exp", "A5_role", "A5_role_other",
     "A6_cost", "A7_path", "A7_path_other", "A8_when", "A9_lag"]
    + B_ITEMS + C_ITEMS + D_ITEMS + E_ITEMS
    + list(DERIVED) + ["sys_path", "include", "exclude_reason"]
)
A_ASCII = {"A1": "A1_affil", "A2": "A2_sex", "A3": "A3_age", "A4": "A4_exp", "A5": "A5_role",
           "A6": "A6_cost", "A7": "A7_path", "A8": "A8_when", "A9": "A9_lag"}


@dataclass
class Issue:
    category: str
    resp_id: str
    src_row: int | str
    detail: str
    action: str


@dataclass
class BuildResult:
    raw: pd.DataFrame          # 원자료_통합 (원문 텍스트)
    coded: pd.DataFrame        # 코딩값 + 파생값 (ASCII 이름, 성명·현장명 없음, src_row 포함)
    analysis: pd.DataFrame     # 분석자료 (ANALYSIS_COLUMNS)
    issues: list[Issue] = field(default_factory=list)
    headers: dict[int, str] = field(default_factory=dict)   # 원본 머리글 (열 번호 → 텍스트)
    cross_fill_violations: list[tuple[int, int, object]] = field(default_factory=list)
    likert_failures: list[tuple[int, str, object]] = field(default_factory=list)
    category_failures: list[tuple[int, str, object]] = field(default_factory=list)
    sha256: str = ""


def sha256_of(path: Path = SRC_PATH) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_text(v) -> str | None:
    """strip + 물결표 통일(~, ～ → ∼). 빈 값은 None."""
    if v is None:
        return None
    s = str(v).strip()
    s = s.replace("~", "∼").replace("～", "∼")
    s = re.sub(r"\s+", " ", s)
    return s or None


def code_likert(v):
    s = norm_text(v)
    if s is None:
        return None, True
    code = LIKERT_MAP.get(s[0])
    if code is None or s != LIKERT_LABELS[code]:
        return None, False
    return code, True


def to_number(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        x = float(str(v).strip()) if isinstance(v, str) else float(v)
    except ValueError:
        return "BAD"
    return int(x) if x.is_integer() else x


def mean_if_complete(values):
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in values):
        return None
    return sum(values) / len(values)


def build(path: Path = SRC_PATH) -> BuildResult:
    sha = sha256_of(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[SRC_SHEET]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    wb.close()
    headers = {i + 1: h for i, h in enumerate(rows[0])}
    data = rows[1:]

    issues: list[Issue] = []
    cross: list[tuple[int, int, object]] = []
    lik_fail: list[tuple[int, str, object]] = []
    cat_fail: list[tuple[int, str, object]] = []
    raw_recs, coded_recs = [], []

    for k, row in enumerate(data):
        src_row = k + 2
        rid = f"R{k + 1:03d}"
        cell = lambda c: row[c - 1] if c - 1 < len(row) else None  # noqa: E731
        branch = norm_text(cell(COL_BRANCH))
        group = GROUP_MAP.get(branch)
        if group is None:
            issues.append(Issue("집단 판정 실패", rid, src_row, f"분기값 {branch!r}", "group 결측"))
        cols = ADOPT_COLS if group == 1 else NONADOPT_COLS
        other_range = NONADOPT_RANGE if group == 1 else ADOPT_RANGE
        for c in other_range:
            v = cell(c)
            if v is not None and str(v).strip():
                cross.append((src_row, c, v))
                issues.append(Issue("교차 채움 위반", rid, src_row, f"{c}열({headers[c]!r})에 {v!r}", "무시(해당 분기 열만 사용)"))

        ts = cell(COL_TIMESTAMP)
        raw = {"resp_id": rid, "src_row": src_row, "timestamp": ts, "group_text": branch, "group": group,
               "site": norm_text(cell(COL_SITE)), "name": norm_text(cell(COL_NAME))}
        coded = {"resp_id": rid, "src_row": src_row, "group": group}
        for item in ITEMS:
            c = cols.get(item)
            v = cell(c) if c else None
            raw[item] = v.strip() if isinstance(v, str) else v
            if item in LIKERT_ITEMS:
                code, ok = code_likert(v)
                if not ok:
                    lik_fail.append((src_row, item, v))
                    issues.append(Issue("리커트 매핑 실패", rid, src_row, f"{item}={v!r}", "결측 처리"))
                coded[item] = code
            elif item in ("A3", "A4"):
                x = to_number(v)
                if x == "BAD":
                    cat_fail.append((src_row, item, v))
                    issues.append(Issue("숫자 변환 실패", rid, src_row, f"{item}={v!r}", "결측 처리"))
                    x = None
                coded[A_ASCII[item]] = x
            else:
                s = norm_text(v)
                code = None
                if s is not None:
                    code = CAT_MAPS[item].get(s)
                    if code is None and item in OTHER_CODE:
                        if s in NONRESPONSE_TEXTS:
                            issues.append(Issue("기타 자리 무응답 표기", rid, src_row, f"{item}={v!r}",
                                                "결측 처리(무응답으로 판단)"))
                        else:
                            code = OTHER_CODE[item]
                            coded[f"{A_ASCII[item]}_other"] = s
                    elif code is None:
                        cat_fail.append((src_row, item, v))
                        issues.append(Issue("범주 매핑 실패", rid, src_row, f"{item}={v!r}", "결측 처리"))
                coded[A_ASCII[item]] = code
        coded.setdefault("A5_role_other", None)
        coded.setdefault("A7_path_other", None)

        for name, (items, adopt_only) in DERIVED.items():
            coded[name] = None if (adopt_only and group != 1) else mean_if_complete([coded[i] for i in items])

        if group == 1:
            a7, a8 = coded["A7_path"], coded["A8_when"]
            coded["sys_path"] = None if (a7 is None or a8 is None) else int(a7 in (3, 4) and a8 == 3)
        else:
            coded["sys_path"] = None

        include, reason = 1, None
        if src_row in EXCLUSIONS:
            exp_ts, exp_site, exp_reason = EXCLUSIONS[src_row]
            ts_s = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
            if ts_s != exp_ts or raw["site"] != exp_site:
                raise ValueError(f"제외 대상 행 {src_row}의 내용이 계획과 다르다: {ts_s}, {raw['site']}")
            include, reason = 0, exp_reason
        coded["include"], coded["exclude_reason"] = include, reason
        raw["include"], raw["exclude_reason"] = include, reason
        raw_recs.append(raw)
        coded_recs.append(coded)

    raw_df = pd.DataFrame(raw_recs)
    coded_df = pd.DataFrame(coded_recs)
    analysis = coded_df[ANALYSIS_COLUMNS].copy()
    return BuildResult(raw=raw_df, coded=coded_df, analysis=analysis, issues=issues, headers=headers,
                       cross_fill_violations=cross, likert_failures=lik_fail, category_failures=cat_fail,
                       sha256=sha)


def load_coded(path: Path = SRC_PATH) -> pd.DataFrame:
    """Task B용 진입점: 분석자료 DataFrame(73행, include 열 포함)."""
    return build(path).analysis


if __name__ == "__main__":
    r = build()
    a = r.analysis
    print("sha256", r.sha256, r.sha256 == SRC_SHA256)
    print("rows", len(a), "adopt", int((a.group == 1).sum()), "nonadopt", int((a.group == 0).sum()))
    inc = a[a.include == 1]
    print("include=1", len(inc), "adopt", int((inc.group == 1).sum()), "nonadopt", int((inc.group == 0).sum()))
    print("cross-fill", len(r.cross_fill_violations), "likert fail", r.likert_failures, "cat fail", r.category_failures)
    for i in r.issues:
        print(i)
