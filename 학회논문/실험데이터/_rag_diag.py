# -*- coding: utf-8 -*-
"""Phase 1b+2 검증: 5W1H 분류 백필 + 3단계 검색기. 결과를 JSON으로 출력."""
import sys, os, json
sys.path.insert(0, "D:/onvifcctv"); os.chdir("D:/onvifcctv")
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = "D:/onvifcctv/data/17e8d71a462e"
from src.utils.few_shot_learning import (get_few_shot_store, reset_few_shot_store,
    FewShotClassifier, FewShotRetriever)
reset_few_shot_store(); store = get_few_shot_store()

OUT = "C:/Users/Sweet HOME/Documents/경기대 논문 연구/학회논문/실험데이터/_rag_diag_out.json"
out = {"classify_cases": [], "cameras": {}, "queries": {}}

# 1) 분류기 단위 테스트 (사용자 예시: 신호수 인정 vs 부정)
clf = FewShotClassifier.get_instance()
for note, reason, wk, ct in [
    ("작업지휘자로 위험사항 없음", "굴착기 작업 반경 내에 작업자가 근접", "warning_close_to_machinery", "false_alarm"),
    ("빨간색 안전모/조끼 미착용, 신호수 부재 상태로 보아야 함", "신호수가 배치되어 안전", "warning_close_to_machinery", "miss"),
    ("충분히 거리가 있음", "굴착기 작업 반경 내 근접", "warning_close_to_machinery", "false_alarm"),
]:
    out["classify_cases"].append({"note": note[:30], "ct": ct,
        "tags": clf.classify(note, reason, wk, ct, jpeg_bytes=None)})

# 2) 대상 카메라 태그 백필 + 목록
targets = ["백학지구 - 연포천(4급 방성경)", "상방지구 - 강화옹진(4급 김유라)",
           "풍동지구 - 고양(3급 김효섭)", "흥부지구 - 화성수원(7급 서영천)"]
for cam in targets:
    n = store.backfill_tags(cam)
    lst = [{"id": s.sample_id[:8], "ct": s.correction_type,
            "tags": s.tags, "emb": s.embedding is not None} for s in store.list_samples(cam)]
    out["cameras"][cam] = {"backfilled": n, "samples": lst}

# 3) 검색기 랭킹 (백학: why별 질의)
reset_few_shot_store(); store2 = get_few_shot_store()
retr = FewShotRetriever(store2)
cam = "백학지구 - 연포천(4급 방성경)"
for qwhy in ("통제된작업", "신호수인정", "실제위험"):
    qtags = {"who": "작업자", "what": "굴착기", "how": "작업반경내근접", "why": qwhy, "direction": "false_alarm"}
    sel = retr.select(cam, "warning_close_to_machinery", query_vec=None, query_tags=qtags, k_max=3)
    out["queries"][qwhy] = [{"id": s.sample_id[:8], "why": (s.tags or {}).get("why"),
        "score": FewShotRetriever._tag_score(qtags, s.tags)} for s in sel]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("WROTE", OUT)
