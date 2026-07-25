# -*- coding: utf-8 -*-
"""6개 정본 결과에서 제로샷(k=0) 통합 집계. 깨진 구버전 파일은 제거. ASCII JSON 출력."""
import glob, json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

canonical = {
    "_fewshot_result_백학지구.json", "_fewshot_result_애룡저수지_고정_.json",
    "_fewshot_result_상방지구.json", "_fewshot_result_선곡지구.json",
    "_fewshot_result_흥부지구.json", "_fewshot_result_풍동지구.json",
}
all_files = set(os.path.basename(f) for f in glob.glob("_fewshot_result_*.json"))
stale = sorted(all_files - canonical)

agg = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
per = {}
for b in sorted(canonical):
    d = json.load(open(b, encoding="utf-8"))
    v = d["k_sweep"]["0"]
    cam = d["camera"].split(" - ")[0]
    per[cam] = {k: v[k] for k in ("TP", "FP", "TN", "FN")}
    for k in agg:
        agg[k] += v[k]

N = sum(agg.values())
TP, FP, TN, FN = agg["TP"], agg["FP"], agg["TN"], agg["FN"]
P = TP/(TP+FP) if TP+FP else 0.0
R = TP/(TP+FN) if TP+FN else 0.0
F = 2*P*R/(P+R) if P+R else 0.0
A = (TP+TN)/N if N else 0.0
out = {"zero_shot_overall": dict(P=round(P,3), R=round(R,3), F1=round(F,3), Acc=round(A,3),
                                 TP=TP, FP=FP, TN=TN, FN=FN, n=N),
       "per_camera_k0": per, "stale_files": stale}

# 구버전(깨진 파일명) 삭제
removed = []
for b in stale:
    try:
        os.remove(b); removed.append(b)
    except Exception as e:
        out["remove_error"] = str(e)
out["removed"] = removed

json.dump(out, open("_agg_zeroshot_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK n=", N, "stale_removed=", len(removed))
