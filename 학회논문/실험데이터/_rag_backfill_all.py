# -*- coding: utf-8 -*-
"""전체 카메라 few-shot 샘플의 임베딩 + 5W1H 태그 일괄 백필 (실알림 전 사전계산)."""
import sys, os, json
sys.path.insert(0, "D:/onvifcctv"); os.chdir("D:/onvifcctv")
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = "D:/onvifcctv/data/17e8d71a462e"
from src.utils.few_shot_learning import get_few_shot_store, reset_few_shot_store
reset_few_shot_store(); store = get_few_shot_store()

n_emb = store.backfill_embeddings()   # 전체 카메라
n_tag = store.backfill_tags()         # 전체 카메라

# 결과 요약
summary = {"embeddings_filled": n_emb, "tags_filled": n_tag, "cameras": {}}
for cam in store._all_camera_dirs():
    # 폴더명이 아니라 실제 camera_name으로 list 해야 하므로 샘플에서 역추출
    samples = []
    import glob
    sj = os.path.join(store._base_dir, cam, "samples.json")
    if os.path.isfile(sj):
        data = json.load(open(sj, encoding="utf-8"))
        for d in data:
            samples.append({"emb": d.get("embedding") is not None,
                            "tags": d.get("tags") is not None,
                            "why": (d.get("tags") or {}).get("why")})
    if samples:
        summary["cameras"][cam] = {"n": len(samples),
            "emb_ok": sum(1 for x in samples if x["emb"]),
            "tag_ok": sum(1 for x in samples if x["tags"])}
json.dump(summary, open(r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\_rag_backfill_out.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("DONE emb=%d tag=%d" % (n_emb, n_tag))
