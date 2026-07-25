# -*- coding: utf-8 -*-
"""RAG vs 고정-k 비교 실험 (Phase 6).
같은 6개 카메라 평가셋(누수행 제외)에서 3조건 비교:
  - fixed k=5 (과교정 조건)  - fixed k=3  - RAG 동적선택(2-pass)
RAG는 앱의 실제 _load_few_shot_samples(classify_query→retriever)를 그대로 호출.
출력: _rag_compare_out.json
"""
import sys, os, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
APP = "D:/onvifcctv"; ACCOUNT_DIR = "D:/onvifcctv/data/17e8d71a462e"
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
OUTDIR = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터"
sys.path.insert(0, APP); os.chdir(APP)

from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = ACCOUNT_DIR
from src.utils.settings_service import get_settings_service
from src.utils.ai_second_check import AISecondChecker
from src.utils.few_shot_learning import get_few_shot_store, reset_few_shot_store
reset_few_shot_store()

TARGET_CAMS = [
    "백학지구 - 연포천(4급 방성경)", "흥부지구 - 화성수원(7급 서영천)",
    "풍동지구 - 고양(3급 김효섭)", "선곡지구 - 연포천(4급 방성경)",
    "애룡저수지(고정) - 파주(4급 김종윤)", "상방지구 - 강화옹진(4급 김유라)",
]
s = get_settings_service()
MODEL = s.value("ai_second_check_model", "gemini-3.1-flash-lite", type=str)
THINK = s.get_ai_second_check_thinking_level()
checker = AISecondChecker(); store = get_few_shot_store()

from PIL import Image
def ahash(pil, n=16):
    g = pil.convert("L").resize((n, n)); px = list(g.getdata()); avg = sum(px)/len(px)
    return [1 if p > avg else 0 for p in px]
def ham(a, b): return sum(x != y for x, y in zip(a, b))
def norm(t): return "".join(str(t).split()).replace("warning_close_to_machinery=", "").replace("warning_close_to_vehicle=", "")

import openpyxl
print("878 로딩...")
wb = openpyxl.load_workbook(XLSX, data_only=True); ws = wb["라벨링_878건"]
meta = {}
for r in ws.iter_rows(min_row=2, values_only=False):
    er = r[0].row
    meta[er] = dict(no=r[0].value, cam=r[2].value, content=r[4].value,
                    reason=norm(r[9].value), verdict=r[10].value, label=r[13].value)
imgbytes = {}; imghash = {}
for im in ws._images:
    er = im.anchor._from.row + 1
    if er in meta:
        b = im._data(); imgbytes[er] = b
        try: imghash[er] = ahash(Image.open(io.BytesIO(b)))
        except Exception: pass

def truth_danger(m):
    if m["label"] == "O" and m["verdict"] == "정탐": return True
    if m["label"] == "X" and m["verdict"] == "오탐": return True
    if m["label"] == "X" and m["verdict"] == "정탐": return False
    if m["label"] == "O" and m["verdict"] == "오탐": return False
    return None
def wkey(content): return "warning_close_to_machinery" if "중장비" in str(content) else "warning_close_to_vehicle"

def judge(cam, m, samples):
    prompt = checker._resolve_prompt(cam)
    allow, reason = checker._api_check("Gemini", MODEL, prompt, cam, wkey(m["content"]),
                                       str(m["content"]), frame_jpeg=imgbytes[m["__row"]],
                                       few_shot_samples=samples or None, thinking_level=THINK)
    return allow

def leak_filter(cam, m, samples):
    """RAG가 고른 카드 중 현재 평가행과 동일 이미지(자기 자신)면 제외."""
    out = []
    for smp in samples:
        try:
            p = store.get_image_path(cam, smp); h = ahash(Image.open(p))
            if ham(h, imghash[m["__row"]]) <= 4 and norm(smp.original_reason)[:18] == m["reason"][:18]:
                continue  # 누수 카드
        except Exception:
            pass
        out.append(smp)
    return out

def metrics(rows, decide):
    tp=fp=tn=fn=0
    for er in rows:
        m = meta[er]; td = truth_danger(m)
        allow = decide(m)
        if td and allow: tp+=1
        elif td and not allow: fn+=1
        elif (not td) and allow: fp+=1
        else: tn+=1
    n=tp+fp+tn+fn
    P=tp/(tp+fp) if tp+fp else 0.0; R=tp/(tp+fn) if tp+fn else 0.0
    F=2*P*R/(P+R) if P+R else 0.0; A=(tp+tn)/n if n else 0.0
    return dict(TP=tp,FP=fp,TN=tn,FN=fn,P=round(P,3),R=round(R,3),F1=round(F,3),Acc=round(A,3),n=n)

out = {"conditions": {}, "per_camera": {}}
agg = {"fixed5": [], "fixed3": [], "rag": []}  # er별 (truth, allow) 누적용은 생략, 카메라별 집계 후 합산
s.set_few_shot_rag_enabled(True)  # RAG 경로 보장

for cam in TARGET_CAMS:
    samples_all = store.list_samples(cam)
    cam_rows = [er for er in meta if str(meta[er]["cam"]) == cam]
    for er in cam_rows: meta[er]["__row"] = er
    # 누수행 판별 (카드와 동일한 평가행) — 평가셋서 제외
    leak = set()
    for smp in samples_all:
        try: sh = ahash(Image.open(store.get_image_path(cam, smp)))
        except Exception: continue
        sr = norm(smp.original_reason)
        for er in cam_rows:
            if er in imghash and ham(sh, imghash[er]) <= 4 and sr[:18] == meta[er]["reason"][:18]:
                leak.add(er)
    test_rows = [er for er in cam_rows if er not in leak and truth_danger(meta[er]) is not None]
    print(f"[{cam.split(' - ')[0]}] 카드 {len(samples_all)} / 평가 {len(test_rows)} (누수제외 {len(leak)})")

    # 조건별 판정 캐시 (er → allow) — 합산용
    dec = {"fixed5": {}, "fixed3": {}, "rag": {}}
    for er in test_rows:
        m = meta[er]
        # fixed k=5 / k=3 : 등록순 앞에서 k개, 단 자기누수카드 제외
        base = leak_filter(cam, m, samples_all)
        dec["fixed5"][er] = judge(cam, m, base[:5])
        dec["fixed3"][er] = judge(cam, m, base[:3])
        # RAG: 앱 실제 2-pass 경로
        rag_sel = checker._load_few_shot_samples(cam, wkey(m["content"]), str(m["content"]), imgbytes[er])
        rag_sel = leak_filter(cam, m, rag_sel)
        dec["rag"][er] = judge(cam, m, rag_sel)

    out["per_camera"][cam] = {
        c: metrics(test_rows, lambda m, c=c: dec[c][m["__row"]]) for c in ("fixed5","fixed3","rag")
    }
    out["per_camera"][cam]["n_cards"] = len(samples_all)
    for c in ("fixed5","fixed3","rag"):
        for er in test_rows: agg[c].append((er, dec[c][er]))

# 전체 합산 (모든 카메라 평가행)
all_rows = [er for cam in TARGET_CAMS for er in [x[0] for x in agg["rag"]] ]  # rag 기준 동일 평가셋
# dict로 조건별 allow 매핑
def overall(cond):
    dmap = dict(agg[cond])
    rows = list(dmap.keys())
    return metrics(rows, lambda m: dmap[m["__row"]])
for c in ("fixed5","fixed3","rag"):
    out["conditions"][c] = overall(c)

json.dump(out, open(os.path.join(OUTDIR, "_rag_compare_out.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n=== 전체 ===")
for c in ("fixed5","fixed3","rag"):
    v = out["conditions"][c]
    print(f"{c:8} P={v['P']:.3f} R={v['R']:.3f} F1={v['F1']:.3f} Acc={v['Acc']:.3f} FP={v['FP']} (n={v['n']})")
print("WROTE _rag_compare_out.json")
