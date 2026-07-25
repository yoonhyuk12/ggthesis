# -*- coding: utf-8 -*-
"""통합 비교표용: 카메라별 제로샷(k0)+고정k3+RAG (Acc/FP) 한 파일로."""
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

zk = json.load(open("_agg_zeroshot_out.json", encoding="utf-8"))["per_camera_k0"]
cmp = json.load(open("_rag_compare_out.json", encoding="utf-8"))["per_camera"]

name_map = {  # compare 키(풀네임) → 약칭
    "백학지구 - 연포천(4급 방성경)": "백학지구",
    "흥부지구 - 화성수원(7급 서영천)": "흥부지구",
    "풍동지구 - 고양(3급 김효섭)": "풍동지구",
    "선곡지구 - 연포천(4급 방성경)": "선곡지구",
    "애룡저수지(고정) - 파주(4급 김종윤)": "애룡저수지",
    "상방지구 - 강화옹진(4급 김유라)": "상방지구",
}
def acc(d):
    n=d["TP"]+d["FP"]+d["TN"]+d["FN"]; return round((d["TP"]+d["TN"])/n,3) if n else 0.0

rows=[]
for full, short in name_map.items():
    c = cmp[full]
    z = zk.get(short, {})
    rows.append({
        "cam": short, "n": c["fixed3"]["n"],
        "zero_acc": acc(z) if z else None, "zero_fp": z.get("FP"),
        "f3_acc": c["fixed3"]["Acc"], "f3_fp": c["fixed3"]["FP"],
        "rag_acc": c["rag"]["Acc"], "rag_fp": c["rag"]["FP"],
    })
json.dump(rows, open("_unified_table_out.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK rows=", len(rows))
