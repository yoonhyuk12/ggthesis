# -*- coding: utf-8 -*-
"""Few-shot k-sweep 실험 엔진.
앱 코드(ai_second_check, few_shot_learning) 재사용. 한글 경로 픽스 적용된 버전 사용.
usage: python _fewshot_run.py [카메라명부분문자열]  (생략 시 전체 대상)
출력: 콘솔 요약 + _fewshot_result_<cam>.json
"""
import sys, os, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

APP = "D:/onvifcctv"
ACCOUNT_DIR = "D:/onvifcctv/data/17e8d71a462e"
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
OUTDIR = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터"
sys.path.insert(0, APP); os.chdir(APP)

from PyQt6.QtCore import QCoreApplication
app = QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud
ud._current_data_dir = ACCOUNT_DIR
from src.utils.settings_service import get_settings_service
from src.utils.ai_second_check import AISecondChecker
from src.utils.few_shot_learning import get_few_shot_store, reset_few_shot_store
reset_few_shot_store()

TARGET_CAMS = [
    "백학지구 - 연포천(4급 방성경)",
    "흥부지구 - 화성수원(7급 서영천)",
    "풍동지구 - 고양(3급 김효섭)",
    "선곡지구 - 연포천(4급 방성경)",
    "애룡저수지(고정) - 파주(4급 김종윤)",
    "상방지구 - 강화옹진(4급 김유라)",
]
filt = sys.argv[1] if len(sys.argv) > 1 else None
cams = [c for c in TARGET_CAMS if (filt is None or filt in c)]

s = get_settings_service()
MODEL = s.value("ai_second_check_model", "gemini-3.1-flash-lite", type=str)
THINK = s.get_ai_second_check_thinking_level()
checker = AISecondChecker()
store = get_few_shot_store()

# ---- 16x16 ahash + 사유 prefix 로 누수(샘플==평가행) 판별 ----
from PIL import Image
def ahash(pil, n=16):
    g = pil.convert("L").resize((n, n)); px = list(g.getdata()); avg = sum(px) / len(px)
    return [1 if p > avg else 0 for p in px]
def ham(a, b): return sum(x != y for x, y in zip(a, b))
def norm(t): return "".join(str(t).split()).replace("warning_close_to_machinery=", "").replace("warning_close_to_vehicle=", "")

# ---- 878 로드 (행→메타+이미지) ----
import openpyxl
print("878 xlsx 로딩...")
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["라벨링_878건"]
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
print(f"  행 {len(meta)} / 이미지 {len(imgbytes)}")

def truth_danger(m):
    if m["label"] == "O" and m["verdict"] == "정탐": return True
    if m["label"] == "X" and m["verdict"] == "오탐": return True
    if m["label"] == "X" and m["verdict"] == "정탐": return False
    if m["label"] == "O" and m["verdict"] == "오탐": return False
    return None  # '?' 등 제외

def wkey(content): return "warning_close_to_machinery" if "중장비" in str(content) else "warning_close_to_vehicle"

def call(cam, m, samples_k):
    prompt = checker._resolve_prompt(cam)
    t0 = time.time()
    allow, reason = checker._api_check("Gemini", MODEL, prompt, cam, wkey(m["content"]),
                                       str(m["content"]), frame_jpeg=imgbytes[m["__row"]],
                                       few_shot_samples=samples_k or None, thinking_level=THINK)
    return allow, reason, time.time() - t0

results = {}
for cam in cams:
    safe = cam.split(" - ")[0].replace("(", "_").replace(")", "_")
    outpath = os.path.join(OUTDIR, f"_fewshot_result_{safe}.json")
    if os.path.exists(outpath) and "--force" not in sys.argv:
        print(f"\n[{cam}] 결과 존재 → 건너뜀 ({outpath})")
        continue
    samples = store.list_samples(cam)
    nsmp = len(samples)
    # 카메라 878 행
    cam_rows = [er for er, m in meta.items() if str(m["cam"]) == cam]
    for er in cam_rows: meta[er]["__row"] = er
    # 누수 행 판별: 샘플과 동일(ahash d<=4 + 사유 prefix 일치)
    leak = set()
    for smp in samples:
        sr = norm(smp.original_reason)
        for er in cam_rows:
            if er in imghash:
                # 샘플 이미지 해시
                p = store.get_image_path(cam, smp)
                try: sh = ahash(Image.open(p))
                except Exception: continue
                if ham(sh, imghash[er]) <= 4 and sr[:18] == meta[er]["reason"][:18]:
                    leak.add(er)
    test_rows = [er for er in cam_rows if er not in leak and truth_danger(meta[er]) is not None]
    err_rows = [er for er in test_rows if (meta[er]["label"] == "X")]
    print(f"\n{'='*70}\n[{cam}]  샘플 {nsmp} | 카메라행 {len(cam_rows)} | 누수제외 {sorted(meta[e]['no'] for e in leak)} | 평가 {len(test_rows)} (오답 {len(err_rows)})")

    cam_res = {"camera": cam, "n_samples": nsmp, "leak_excluded": sorted(meta[e]["no"] for e in leak),
               "n_test": len(test_rows), "k_sweep": {}, "per_error": {}}
    per_error = {}  # no -> {truth, k0, k1, ...}  (버그픽스: k루프 밖에서 누적)
    err_truth = {meta[er]["no"]: ("위험" if truth_danger(meta[er]) else "안전") for er in err_rows}
    for k in range(0, nsmp + 1):
        sk = samples[:k]
        tp = fp = tn = fn = 0; tot_t = 0.0
        for er in test_rows:
            m = meta[er]; td = truth_danger(m)
            allow, reason, dt = call(cam, m, sk); tot_t += dt
            if td and allow: tp += 1
            elif td and not allow: fn += 1
            elif (not td) and allow: fp += 1
            else: tn += 1
            if m["label"] == "X":
                per_error.setdefault(m["no"], {"truth": err_truth[m["no"]]})[f"k{k}"] = "SEND" if allow else "BLOCK"
        n = tp + fp + tn + fn
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        acc = (tp + tn) / n if n else 0.0
        cam_res["k_sweep"][k] = dict(TP=tp, FP=fp, TN=tn, FN=fn, P=round(prec, 3), R=round(rec, 3),
                                     F1=round(f1, 3), Acc=round(acc, 3), avg_sec=round(tot_t / n, 2) if n else 0)
        print(f"  k={k}: P={prec:.3f} R={rec:.3f} F1={f1:.3f} Acc={acc:.3f} | TP{tp} FP{fp} TN{tn} FN{fn} | {tot_t/n:.1f}s/건")
    cam_res["per_error"] = per_error
    if per_error:
        print("  --- 오답(X) 케이스 k별 판정 ---")
        for no, d in per_error.items():
            seq = " ".join(f"k{k}:{d.get(f'k{k}','-')}" for k in range(nsmp + 1))
            print(f"    #{no} [{d['truth']}]: {seq}")
    results[cam] = cam_res
    json.dump(cam_res, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("\n완료. 결과 JSON 저장됨.")
