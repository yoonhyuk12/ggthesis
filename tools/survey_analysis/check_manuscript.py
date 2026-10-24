"""원고(05장·06장·00_목차)에 반영한 설문 분석 수치가 results.json과 일치하는지 점검한다.

저장소 루트에서 실행:
    PYTHONIOENCODING=utf-8 python tools/survey_analysis/check_manuscript.py

점검 항목
  (a) results.json 핵심값을 원고 표기 규칙(비율 1자리, M·SD·B·SE·CI 2자리, p 3자리·<.001, η²·α 3자리)으로
      문자열화해 해당 원고에서 찾고 누락 목록을 출력한다. 표 행은 행 전체 문자열로 대조한다.
  (b) 파일별 '실험전'·'[DATA PENDING' 개수와 남은 위치
  (c) 횡단 비교 금지 표현
  (d) 대괄호 마커 접두사·닫힘 형식
  (e) 표 간 교차 일치(<표 5-1> 합계, <표 5-6> 패널 D, <표 5-8> 패널 C)
  (f) 확정 단계 금지 문자열(jamovi·명부 대조 전·시험 응답·73건 등) — 00·04·05·06장·부록1
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT / "01.docs/설문결과/analysis/results.json").read_text(encoding="utf-8"))
FILES = {"05": ROOT / "01.docs/05_실증분석결과.md", "06": ROOT / "01.docs/06_결론.md", "00": ROOT / "01.docs/00_목차.md"}
TXT = {k: p.read_text(encoding="utf-8") for k, p in FILES.items()}
# 금지 문자열 검사만 하는 추가 파일(수치 대조 대상 아님)
EXTRA = {"04": ROOT / "01.docs/04_연구설계.md", "부록1": ROOT / "01.docs/부록1_설문지_양식.md",
         "01": ROOT / "01.docs/01_서론.md", "03": ROOT / "01.docs/03_시스템개발.md", "07": ROOT / "01.docs/07_참조번호목록.md"}
ALL_TXT = {**TXT, **{k: p.read_text(encoding="utf-8") for k, p in EXTRA.items()}}

FORBIDDEN = ["도입 이후 향상", "개선시켰", "감소시켰", "효과가 있었"]
# 2026-10-24 Task I: 응답 71명으로 확정하면서 삭제한 보류·도구 표기. 파일별로 0건이어야 한다
BANNED_COMMON = ["jamovi", "명부 대조 전", "시험 응답", "73건"]
# 2026-10-24 Task J: 범위 밖 파급 정리(01장 도구 표기, 03장 명부 기록 계획, 부록1 경력 환산, 05장 H2 HC3 미산출 문구)
BANNED = {"00": BANNED_COMMON, "04": BANNED_COMMON, "부록1": BANNED_COMMON + ["개월/12", "명부에 기록하며"],
          "01": ["jamovi"], "03": ["조사 명부에 함께 기록"],
          "05": BANNED_COMMON + ["명부 대조", "대조 후 확정", "실험전", "[DATA PENDING", "H2에는 산출하지 않았다"],
          "06": BANNED_COMMON + ["명부 대조", "대조 후 확정", "[DATA PENDING"]}
MARKER_PREFIXES = ["[DATA PENDING", "[확정 필요", "[CITE_TODO", "[UNVERIFIED", "[그림 삽입 예정"]


def f2(x): return f"{x:.2f}"
def f3(x): return f"{x:.3f}"
def fp(p): return "<.001" if p < 0.001 else f"{p:.3f}".replace("0.", ".", 1)
def fpc(x): return f"{100 * x:.1f}"
def ci(lo, hi): return f"[{lo:.2f}, {hi:.2f}]"
def fn(x): return str(int(x)) if float(x).is_integer() else f"{x:.2f}"
def row(*c): return "| " + " | ".join(str(x) for x in c) + " |"


LAB = {
    "A1": {1: "시공사", 2: "발주청(공사감독·감리원 포함)"}, "A2": {1: "남성", 2: "여성"},
    "A5": {1: "공사감독", 2: "안전관리자", 3: "현장소장", 4: "기타"},
    "A6": {1: "20억 원 미만", 2: "20억 원 이상∼50억 원 미만", 3: "50억 원 이상∼120억 원 미만", 4: "120억 원 이상"},
}
FAC = {"A1_affil": ("소속 구분", "A1"), "A2_sex": ("성별", "A2"), "A5_role": ("역할", "A5"), "A6_cost": ("총공사비 구간", "A6")}
G3 = ("도입", "미도입", "전체")
SUB = {"Y1": "조기인지", "Y2": "대응 신속성", "Y3": "원격 파악", "Y4": "순찰부담 경감", "Y5": "위험 통제력"}

checks: list[tuple[str, str, str]] = []   # (파일, 라벨, 기대 문자열)


def need(file, label, s):
    checks.append((file, label, s))


T51, T52, T53, T54 = R["table_5_1"], R["table_5_2"], R["table_5_3"], R["table_5_4"]
H1, SENS, T57, H2 = R["table_5_6"]["H1"], R["table_5_6"]["sensitivity"], R["table_5_7"], R["table_5_8"]
meta = R["meta"]

# ---- <표 5-1>
for var, (lab, key) in FAC.items():
    for code, cl in LAB[key].items():
        c = T51["panel_A"][var][cl]
        need("05", f"5-1A {cl}", row(lab if code == 1 else "", cl, *sum(([c[g]["n"], fpc(c[g]["pct"])] for g in G3), [])))
need("05", "5-1A 합계", row("**합계**", "", f"**{meta['n_include_adopt']}**", "**100.0**", f"**{meta['n_include_non']}**", "**100.0**", f"**{meta['n_include']}**", "**100.0**"))
for var, lab, unit in (("A3_age", "만 나이", "세"), ("A4_exp", "건설현장 경력", "년")):
    for g in G3:
        d = T51["panel_B"][var][g]
        need("05", f"5-1B {var} {g}", row(lab if g == "도입" else "", unit, g, d["n"], f2(d["mean"]), f2(d["sd"]), fn(d["median"]), fn(d["min"]), fn(d["max"])))
for var in ("A7_path", "A8_when", "A9_lag"):
    for cl, c in T51["panel_C"][var].items():
        need("05", f"5-1C {var} {cl}", f"{cl} | " + " | ".join(f"{c[g]['n']} ({fpc(c[g]['pct'])})" for g in G3) + " |")
for var, nm in (("A7_path", "A-7"), ("A8_when", "A-8"), ("A9_lag", "A-9")):
    need("05", f"Fisher {nm}", f"{nm} p={fp(T51['fisher'][var]['p_exact'])}")
need("05", "sys_path=0 건수", f"따로 집계한다({T51['sys_path']['sys_path_0']}건)")
need("05", "sys_path=1 건수", f"작동한 도입 응답은 {T51['sys_path']['sys_path_1']}건")
# ---- <표 5-2>
for sc in ("Y_total", "Y3", "Y4", "Y5", "W"):
    a = T52["panel_A"][sc]
    need("05", f"5-2A α {sc}", "/".join(f3(a[g]["alpha"]) for g in ("전체", "도입", "미도입")))
    need("05", f"5-2A n {sc}", "/".join(str(a[g]["n"]) for g in ("전체", "도입", "미도입")))
    if "r" in a["전체"]:
        need("05", f"5-2A r {sc}", "/".join(f2(a[g]["r"]) for g in ("전체", "도입", "미도입")))
for k in ("Y", "W"):
    e = T52["panel_B"][k]
    need("05", f"5-2B {k}", f"| {f3(e['kmo'])} | {f2(e['bartlett_chi2'])} | {e['bartlett_df']} | {fp(e['bartlett_p'])} | {e['n_factors']} |")
# ---- <표 5-3>
for k in ("Y_total", "Y1", "Y2", "Y3", "Y4", "Y5", "W", "E_total"):
    for g, d in T53["panel_A"][k].items():
        if k != "Y_total" and g == "전체":
            continue
        need("05", f"5-3A {k} {g}", f"| {g} | {d['n']} | {f2(d['mean'])} | {f2(d['sd'])} | {f2(d['skew'])} | {f2(d['kurt'])} |")
for it, d in T53["panel_B"].items():
    need("05", f"5-3B {it}", row(f"{it[0]}-{it[1:]}", d["n"], "—", d["nonresponse"], f2(d["mean"]), f2(d["sd"])))
need("05", "본문 Y 원평균", f"도입 집단 {f2(T53['panel_A']['Y_total']['도입']['mean'])}점, 미도입 집단 {f2(T53['panel_A']['Y_total']['미도입']['mean'])}점")
e = T53["panel_A"]["E_total"]["도입"]
need("05", "본문 E", f"평균 {f2(e['mean'])}점, 표준편차 {f2(e['sd'])}, 왜도 {f2(e['skew'])}, 첨도 {f2(e['kurt'])}")
# ---- <표 5-4>
for var in ("A3_age", "A4_exp"):
    r = T54["panel_A"][var]
    need("05", f"5-4A {var}", f"| {f2(r['mean_diff'])} | {f2(r['smd'])} | {fn(r['common_lo'])}∼{fn(r['common_hi'])}")
for var in FAC:
    r = T54["panel_B"][var]
    need("05", f"5-4B {var}", f"{f2(r['smd_yang_dalton'])}(범주별 최대 절대 d {f2(r['max_abs_cat_smd'])})")
need("05", "나이–경력 r", f"r={f2(T54['age_exp_r'])}")
# ---- <표 5-5>
d5 = R["table_5_5"]
need("05", "5-5 SW", f"Shapiro–Wilk W={f3(d5['H1']['shapiro_W'])}, p={fp(d5['H1']['shapiro_p'])}")
need("05", "5-5 H2 BP", f"Breusch–Pagan p={fp(d5['H2']['bp_p'])}")
need("05", "5-5 기울기 결합", f"F({d5['slope_homogeneity']['joint_df'][0]}, {d5['slope_homogeneity']['joint_df'][1]})={f2(d5['slope_homogeneity']['joint_F'])}, p={fp(d5['slope_homogeneity']['joint_p'])}")
need("05", "5-5 Cook's D", "Cook's D>4/n(0.057) " + f"{len(d5['H1']['cooks_flag'])}건(" + "·".join(i for i, _ in d5["H1"]["cooks_flag"]))
need("05", "5-5 VIF", f"VIF 최대값은 {max(d5['vif'].values()):.2f}")
# ---- <표 5-6>
ep = H1["emm"]["proportional"]
eq = H1["emm"]["equal"]
need("05", "5-6A 도입", row("도입", H1["n_adopt"], f2(H1["raw"]["도입"]["mean"]), f2(H1["raw"]["도입"]["sd"]), f2(ep["도입"]["est"]), f2(ep["도입"]["se"]), ci(ep["도입"]["ci_lo"], ep["도입"]["ci_hi"])))
need("05", "5-6A 미도입", row("미도입", H1["n_non"], f2(H1["raw"]["미도입"]["mean"]), f2(H1["raw"]["미도입"]["sd"]), f2(ep["미도입"]["est"]), f2(ep["미도입"]["se"]), ci(ep["미도입"]["ci_lo"], ep["미도입"]["ci_hi"])))
need("05", "5-6A 차이", f"| {f2(ep['차이']['est'])} | {f2(ep['차이']['se'])} | {ci(ep['차이']['ci_lo'], ep['차이']['ci_hi'])} |")
need("05", "5-6A 동일 가중", f"도입 {f2(eq['도입']['est'])}(SE {f2(eq['도입']['se'])}), 미도입 {f2(eq['미도입']['est'])}(SE {f2(eq['미도입']['se'])})")
for c in H1["coefs"]:
    need("05", f"5-6B {c['term']}", f"| {f2(c['B'])} | {f2(c['SE'])} | {ci(c['ci_lo'], c['ci_hi'])} | {f2(c['t'])} | {c['df']} | {fp(c['p'])} |")
need("05", "5-6C", row("집단(도입=1·미도입=0)", f2(H1["F"]), H1["df1"], H1["df2"], fp(H1["p"]), f3(H1["partial_eta2"])))
need("05", "5-6D", f"| {H1['n_adopt']}/{H1['n_non']}/{H1['n']} | {H1['n_coef']} | {H1['rank']} | {H1['df_resid']} |")
d = H1["diff"]
need("05", "본문 H1", f"{f2(d['B'])}점, SE={f2(d['SE'])}, 95% CI={ci(d['ci_lo'], d['ci_hi'])}, F={f2(H1['F'])}, df=({H1['df1']}, {H1['df2']}), p={fp(H1['p'])}, 부분 η²={f3(H1['partial_eta2'])}")
need("05", "민감도", f"제외 현장 {SENS['excluded_adopt_n']}개소, 부분집단 n={SENS['n']}(도입 {SENS['n_adopt']}명·미도입 {SENS['n_non']}명), 조정 평균 차이 {f2(SENS['diff']['B'])}점, 95% CI={ci(SENS['diff']['ci_lo'], SENS['diff']['ci_hi'])}, p={fp(SENS['p'])}")
# ---- <표 5-6> 패널 E(사후 강건성 점검)·경로 작동/미작동 대비
ROB, PS = R["table_5_6"]["robustness"], SENS["path_split"]
for k, lab in (("base", "기본 모형(원고 보고값)"), ("hc3", "HC3 강건 표준오차"), ("cooks_excluded", "Cook's D 초과 4건 제외"),
               ("straightlining_excluded", "일렬응답 1건 제외"), ("male_only", "여성 제외(남성만)"),
               ("exclude_cost1", "총공사비 20억 원 미만 제외"), ("exclude_role_other", "역할 기타 제외"),
               ("unadjusted", "공변량 없는 단순 비교")):
    r_ = ROB[k]
    need("05", f"5-6E {k}", row(lab, r_["n"], f2(r_["B"]), f2(r_["SE"]), ci(r_["ci_lo"], r_["ci_hi"]), fp(r_["p"])))
need("05", "5-6E MWU", f"Mann–Whitney U 검정 p={fp(ROB['unadjusted']['mann_whitney_p'])}")
need("05", "5-6E mde80", f"(1.96+0.84)×SE={f2(ROB['mde80']['value'])}점")
need("05", "5-6E mde80 해설", f"검출 가능 최소 효과({f2(ROB['mde80']['value'])}점)가 관찰된 조정 차이({f2(ROB['base']['B'])}점)")
need("05", "5-6E 역할 기타 p", f"역할 기타 응답자를 제외하면 p={fp(ROB['exclude_role_other']['p'])}")
need("05", "5-6E 영향점 p", f"오히려 p가 {fp(ROB['cooks_excluded']['p'])}")
need("05", "5-6E 조정 범위", f"{f2(min(ROB[k]['B'] for k in ROB if k not in ('unadjusted', 'mde80', 'note') ))}∼{f2(max(ROB[k]['B'] for k in ROB if k not in ('unadjusted', 'mde80', 'note')))}점의 차이")
need("05", "경로 작동 도입", f"작동한 도입 현장 {PS['adopt_sys_path_1']['n']}곳의 안전관리 실효성 원평균은 {f2(PS['adopt_sys_path_1']['mean'])}점")
need("05", "경로 미작동 도입", f"작동하지 않은 {PS['adopt_sys_path_0']['n']}곳은 {f2(PS['adopt_sys_path_0']['mean'])}점")
need("05", "경로 대비 미도입 원평균", f"| 미도입 | {PS['non_adopt']['n']} | {f2(PS['non_adopt']['mean'])} | {f2(PS['non_adopt']['sd'])} |")
# ---- <표 5-7>
for k, nm in SUB.items():
    s = T57[k]
    p = s["emm"]["proportional"]
    need("05", f"5-7A {k}", row(nm, f"{s['n_adopt']}/{s['n_non']}", f"{f2(p['도입']['est'])}({f2(p['도입']['se'])})", f"{f2(p['미도입']['est'])}({f2(p['미도입']['se'])})",
                               f"{f2(s['diff']['B'])}({f2(s['diff']['SE'])})", ci(s["diff"]["ci_lo"], s["diff"]["ci_hi"]), f2(s["F"]), f"{s['df1']}, {s['df2']}",
                               fp(s["p"]), fp(s["p_holm"]), f3(s["partial_eta2"])))
    need("05", f"5-7B {k}", f"| {nm} | {s['n_coef']} | {s['rank']} | {s['df_resid']} |")
    e_ = s["emm"]["equal"]
    need("05", f"5-7 동일 가중 {k}", f"{nm} {f2(e_['도입']['est'])}/{f2(e_['미도입']['est'])}")
# ---- <표 5-8>
for c in H2["coefs"]:
    need("05", f"5-8A {c['term']}", f"| {f2(c['B'])} | {f2(c['SE'])} | {ci(c['ci_lo'], c['ci_hi'])} | {f2(c['t'])} | {c['df']} | {fp(c['p'])} |")
for lab, c in H2["conditional"].items():
    dd = c["diff"]
    need("05", f"5-8B {lab}", f"| {f2(dd['est'])} | {f2(dd['se'])} | {ci(dd['ci_lo'], dd['ci_hi'])} | {f2(dd['t'])} | {dd['df']} | {fp(dd['p'])} |")
    need("05", f"5-8B 동일 가중 {lab}", f"{lab} {f2(c['adopt']['est'])}/{f2(c['non']['est'])}")
    need("05", f"5-8B 비례 가중 {lab}", f"공통범위 안 | {f2(c['adopt_proportional']['est'])} | {f2(c['non_proportional']['est'])} | {f2(dd['est'])} |")
    if abs((c["adopt_proportional"]["est"] - c["non_proportional"]["est"]) - dd["est"]) > 1e-10:
        print(f"[검산 실패] 5-8B {lab}: 도입−미도입 ≠ 조건부 차이 B")
        sys.exit(1)
need("05", "5-8C", row(f2(H2["interaction_F"]), f"{H2['interaction_df'][0]}, {H2['interaction_df'][1]}", fp(H2["interaction_p"]),
                       f"{H2['n_adopt']}/{H2['n_non']}/{H2['n']}", H2["n_coef"], H2["rank"], H2["df_resid"])[:-2])
need("05", "W 평균", f"W 평균 {H2['W_mean']:.3f}")
# ---- <표 5-8> HC3 사후 점검(Task J)
HC = H2["hc3"]["terms"]
need("05", "5-5 등분산 H2 HC3", f"H2의 D×W_c는 HC3 기준 SE {f2(HC['D:W_c']['SE'])}, p={fp(HC['D:W_c']['p'])}로 판정이 같다")
need("05", "5-8A 주 HC3", f"HC3 강건 표준오차(잔차 df {H2['hc3']['df_resid']}의 t분포)에서는 집단 D가 SE {f2(HC['D']['SE'])}, 95% CI {ci(HC['D']['ci_lo'], HC['D']['ci_hi'])}, p={fp(HC['D']['p'])}, "
                         f"W_c가 SE {f2(HC['W_c']['SE'])}, 95% CI {ci(HC['W_c']['ci_lo'], HC['W_c']['ci_hi'])}, p={fp(HC['W_c']['p'])}, "
                         f"D×W_c가 SE {f2(HC['D:W_c']['SE'])}, 95% CI {ci(HC['D:W_c']['ci_lo'], HC['D:W_c']['ci_hi'])}, p={fp(HC['D:W_c']['p'])}(정규 근사 p={fp(HC['D:W_c']['p_normal'])})")
HCC = H2["hc3"]["conditional_diff"]
need("05", "H2 논의 HC3", f"상호작용은 95% CI {ci(HC['D:W_c']['ci_lo'], HC['D:W_c']['ci_hi'])}, p={fp(HC['D:W_c']['p'])}로 H2가 지지되지 않는다는 결론은 바뀌지 않았다")
need("05", "H2 논의 HC3 조건부", f"({f2(HCC['평균']['est'])}점·{f2(HCC['평균+1SD']['est'])}점)는 HC3 기준 95% CI가 각각 "
                              f"{ci(HCC['평균']['ci_lo'], HCC['평균']['ci_hi'])}·{ci(HCC['평균+1SD']['ci_lo'], HCC['평균+1SD']['ci_hi'])}로 0을 포함")
need("05", "W SD", f"SD는 {f2(H2['W_sd'])}")
need("05", "도입 W 기울기", f"{f2(H2['slope_adopt']['est'])}(SE {f2(H2['slope_adopt']['se'])}, 95% CI {ci(H2['slope_adopt']['ci_lo'], H2['slope_adopt']['ci_hi'])})")
ir = H2["interaction"]
need("05", "본문 H2", f"B={f2(ir['B'])}, 95% CI={ci(ir['ci_lo'], ir['ci_hi'])}(F({H2['interaction_df'][0]}, {H2['interaction_df'][1]})={f2(H2['interaction_F'])}, p={fp(H2['interaction_p'])})")
# ---- <표 5-9>
need("05", "5-9 H1", f"조정 차이 B={f2(d['B'])}, 95% CI {ci(d['ci_lo'], d['ci_hi'])}, 부분 η²={f3(H1['partial_eta2'])}(n={H1['n']}) | F({H1['df1']}, {H1['df2']})={f2(H1['F'])}, p={fp(H1['p'])} | 지지 |")
need("05", "5-9 H2", f"D×W_c B={f2(ir['B'])}, 95% CI {ci(ir['ci_lo'], ir['ci_hi'])}(n={H2['n']}) | F({H2['interaction_df'][0]}, {H2['interaction_df'][1]})={f2(H2['interaction_F'])}, p={fp(H2['interaction_p'])} | 기각 |")
need("05", "A-9 p", f"Fisher 정확검정 p={fp(R['a9_judgement']['p_fisher'])}")
need("05", "A-9 조합", R["a9_judgement"]["provisional_combination"].replace("A-9 없음 × H1 있음", "‘A-9 없음 × H1 있음’"))
# ---- 00_목차 국문초록
need("00", "초록 H1", f"0.42점 높게 나타나 H1이 지지됨(95% CI {ci(d['ci_lo'], d['ci_hi'])}, p={fp(H1['p'])}, 부분 η²={f3(H1['partial_eta2'])}, n={H1['n']})".replace("0.42", f2(d["B"])))
need("00", "초록 H2", f"B={f2(ir['B'])}(95% CI {ci(ir['ci_lo'], ir['ci_hi'])}, p={fp(H2['interaction_p'])})")
need("00", "초록 A-9", f"(p={fp(R['a9_judgement']['p_fisher'])})")
need("00", "초록 표본", f"응답 {meta['n_include']}명(도입 {meta['n_include_adopt']}개소·미도입 {meta['n_include_non']}개소, 현장당 1명)")
need("00", "초록 위험 통제력", f"위험 통제력({f2(T57['Y5']['diff']['B'])}점)")
# ---- 06장
need("06", "결론 H1", f"{f2(d['B'])}점 높게 나타나 H1은 지지되었다(95% CI {ci(d['ci_lo'], d['ci_hi'])}, 부분 η²={f3(H1['partial_eta2'])})")
need("06", "결론 H2", f"B={f2(ir['B'])}(95% CI {ci(ir['ci_lo'], ir['ci_hi'])})")
need("06", "결론 표본", f"응답 {meta['n_include']}명(도입 {meta['n_include_adopt']}명·미도입 {meta['n_include_non']}명)")
need("06", "결론 표본 개소", f"응답 {meta['n_include']}명(도입 {meta['n_include_adopt']}개소·미도입 {meta['n_include_non']}개소, 현장당 1명)")
need("06", "결론 sys_path", f"응답자가 {T51['sys_path']['sys_path_1']}명뿐")
# ---- 검출 가능 최소 효과(MDE)와 H1 경계 근처 서술
MDE1, MDE2 = R["table_5_6"]["robustness"]["mde80"], H2["mde80"]
need("06", "결론 MDE", f"H1의 집단 차이 {f2(MDE1['value'])}점, H2의 상호작용 {f2(MDE2['value'])}이다")
need("06", "결론 H1 경계 차이", f"관찰된 H1 차이 {f2(ROB['base']['B'])}점은 이보다 작아")
need("06", "결론 역할 기타 p", f"p={fp(ROB['exclude_role_other']['p'])}로 나타났다")
need("06", "결론 강건성 p 범위", f"p가 {fp(ROB['cooks_excluded']['p'])}∼{fp(ROB['exclude_role_other']['p'])}로 움직여")
need("00", "초록 H1 경계", "사후 강건성 점검에서 유의수준 경계 근처에 있어 차이의 크기는 불확실함")
need("05", "5장 서두 계수 수", f"실제 계수 수는 H1 모형 {H1['n_coef']}개·H2 모형 {H2['n_coef']}개이다")
need("05", "5장 서두 MDE", f"제4절에 보고한다(H1 집단 차이 {f2(MDE1['value'])}점, H2 상호작용 {f2(MDE2['value'])})")
# ---- 응답 71명 확정(Task I): 표본·집단·통계 도구 표기
need("05", "링크 안내 인원", f"링크를 안내한 인원은 {meta['n_include']}명(도입 {meta['n_include_adopt']}개소·미도입 {meta['n_include_non']}개소, 현장당 1명)이며 전원이 응답하였다")
need("05", "표본 선정 개소", f"도입 현장 {meta['n_include_adopt']}개소와 미설치·미운용 현장 {meta['n_include_non']}개소")
SW = dict(s.split(" ", 1) for s in meta["software"].split(", "))
need("05", "통계 도구", f"Python {SW['Python']}의 statsmodels {SW['statsmodels']}(pandas {SW['pandas']}, numpy {SW['numpy']}, scipy {SW['scipy']})")
need("05", "EFA 문헌", "(Costello & Osborne, 2005)")
need("05", "다범주 SMD 문헌", "(Yang & Dalton, 2012)")
need("05", "H2 논의 MDE", f"최소 상호작용은 {f2(MDE2['value'])}로, 관찰값 {f2(ir['B'])}의 세 배를 넘는다")


def main() -> int:
    ok = True
    print("=" * 70)
    print(f"(a) results.json 핵심값 대조: {len(checks)}건")
    missing = [(f, lab, s) for f, lab, s in checks if s not in TXT[f]]
    by = {}
    for f, _, _ in checks:
        by[f] = by.get(f, 0) + 1
    print("    파일별 점검 수:", by)
    if missing:
        ok = False
        print(f"    누락 {len(missing)}건:")
        for f, lab, s in missing:
            print(f"     - [{f}] {lab}: {s}")
    else:
        print("    누락 0건")

    print("=" * 70)
    print("(b) 남은 '실험전'·'[DATA PENDING' (행 번호: 앞뒤 문맥)")
    for k, t in TXT.items():
        lines = t.splitlines()
        e = sum(l.count("실험전") for l in lines)
        dp = sum(l.count("[DATA PENDING") for l in lines)
        print(f"  [{k}] 실험전 {e}회/{sum(1 for l in lines if '실험전' in l)}행, [DATA PENDING {dp}회/{sum(1 for l in lines if '[DATA PENDING' in l)}행")
        for i, l in enumerate(lines, 1):
            for m in re.finditer(r"실험전|\[DATA PENDING[^\]]*\]", l):
                print(f"     {i}: …{l[max(0, m.start() - 25):m.end() + 5]}…")

    print("=" * 70)
    print("(c) 금지 표현")
    hits = [(k, i, w) for k, t in TXT.items() for i, l in enumerate(t.splitlines(), 1) for w in FORBIDDEN if w in l]
    print("    0건" if not hits else hits)
    ok &= not hits

    print("=" * 70)
    print("(d) 마커 형식")
    bad = []
    for k, t in TXT.items():
        for i, l in enumerate(t.splitlines(), 1):
            for m in re.finditer(r"\[(DATA PENDING|확정 필요|CITE_TODO|UNVERIFIED)", l):
                rest = l[m.end():]
                close = rest.find("]")
                nxt_open = rest.find("[")
                if close < 0 or (0 <= nxt_open < close):
                    bad.append((k, i, "닫는 대괄호 없음", l[m.start():m.start() + 40]))
                elif not (rest.startswith(":") or rest.startswith("]") or m.group(1) == "UNVERIFIED" and rest.startswith(" ")):
                    bad.append((k, i, "접두사 뒤 ':' 아님", l[m.start():m.start() + 40]))
            for m in re.finditer(r"\[(DATA\s*PEND\w*|확정\s*필요|CITE[ _-]?TODO|UNVERIF\w*)", l):
                if m.group(1) not in ("DATA PENDING", "확정 필요", "CITE_TODO", "UNVERIFIED"):
                    bad.append((k, i, "접두사 손상", l[m.start():m.start() + 40]))
    counts = {k: {p: t.count(p) for p in MARKER_PREFIXES} for k, t in TXT.items()}
    print("    접두사별 개수:", counts)
    print("    형식 위반 0건" if not bad else bad)
    ok &= not bad

    print("=" * 70)
    print("(e) 표 간 교차 일치")
    t5 = TXT["05"]
    # <표 5-1> 패널 A: 변수별 빈도 합 ↔ 합계 행 / 유효 응답
    sec = t5[t5.index("| 구분 | 항목 | 도입 빈도(명)"):]
    sec = sec[:sec.index("**합계**")]
    rows = [r for r in sec.splitlines()[2:] if r.startswith("|")]
    sums, cur = {}, None
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if len(cells) < 8:
            continue
        if cells[0]:
            cur = cells[0]
        sums.setdefault(cur, [0, 0, 0])
        for j, col in enumerate((2, 4, 6)):
            sums[cur][j] += int(cells[col])
    tot = [meta["n_include_adopt"], meta["n_include_non"], meta["n_include"]]
    for var, s in sums.items():
        expect = list(tot)
        if var == "역할":
            miss = T51["panel_A"]["A5_role"]["_denominator"]
            expect = [miss[g]["valid"] for g in G3]
        flag = "일치" if s == expect else "불일치"
        ok &= s == expect
        note = " (역할 결측 1건 반영: 미도입 38·전체 70)" if var == "역할" else ""
        print(f"    <표 5-1> {var}: 빈도 합 {s} ↔ 기대 {expect} {flag}{note}")
    # <표 5-6> 패널 D, <표 5-8> 패널 C
    for lab, cond in (("<표 5-6> 패널 D n=70(32/38)·계수 12·rank 12·잔차 df 58",
                       f"| {H1['n_adopt']}/{H1['n_non']}/{H1['n']} | {H1['n_coef']} | {H1['rank']} | {H1['df_resid']} |" in t5
                       and (H1["n_adopt"], H1["n_non"], H1["n"], H1["n_coef"], H1["rank"], H1["df_resid"]) == (32, 38, 70, 12, 12, 58)),
                      ("<표 5-8> 패널 C n=70·계수 14·rank 14·잔차 df 56",
                       f"| {H2['n_adopt']}/{H2['n_non']}/{H2['n']} | {H2['n_coef']} | {H2['rank']} | {H2['df_resid']} |" in t5),
                      ("<표 5-6> 패널 C F·df ↔ <표 5-9> H1", f"F({H1['df1']}, {H1['df2']})={f2(H1['F'])}" in t5),
                      ("<표 5-3> Y 원평균 ↔ 본문", f"도입 집단 {f2(T53['panel_A']['Y_total']['도입']['mean'])}점" in t5),
                      ("<표 5-7> 하위요인 n ↔ <표 5-6> n", all(T57[k]["n"] == H1["n"] for k in SUB)),
                      ("잔차 df = n − rank", H1["df_resid"] == H1["n"] - H1["rank"] and H2["df_resid"] == H2["n"] - H2["rank"])):
        print(f"    {lab}: {'일치' if cond else '불일치'}")
        ok &= bool(cond)

    print("=" * 70)
    print("(f) 확정 단계 금지 문자열")
    bh = [(k, w, ALL_TXT[k].count(w)) for k, ws in BANNED.items() for w in ws if w in ALL_TXT[k]]
    print("    0건 (" + ", ".join(f"{k}:{len(ws)}종" for k, ws in BANNED.items()) + ")" if not bh else bh)
    ok &= not bh
    s4 = ALL_TXT["04"]
    for lab, cond in (("04장 통계 도구 statsmodels", f"statsmodels {SW['statsmodels']}" in s4),
                      ("04장 실제 표본 32·39개소", f"도입 현장 {meta['n_include_adopt']}개소와 미도입 현장 {meta['n_include_non']}개소" in s4),
                      ("04장 statsmodels 내주", "(Seabold & Perktold, 2010)" in s4),
                      ("07 Seabold & Perktold 등재", "Seabold, S., & Perktold, J." in ALL_TXT["07"]),
                      ("01장 도구 표기 statsmodels", "두 집단 ANCOVA 설계(Python statsmodels)" in ALL_TXT["01"]),
                      ("03장 설정 동일 운용", f"도입 현장 {meta['n_include_adopt']}개소는" in ALL_TXT["03"])):
        print(f"    {lab}: {'일치' if cond else '불일치'}")
        ok &= bool(cond)

    print("=" * 70)
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
