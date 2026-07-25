# -*- coding: utf-8 -*-
"""RAG few-shot Phase1+2 스모크: 임베딩 백필 + 검색기 동작 검증."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
APP = "D:/onvifcctv"; ACCOUNT = "D:/onvifcctv/data/17e8d71a462e"
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
sys.path.insert(0, APP); os.chdir(APP)
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = ACCOUNT
from src.utils.few_shot_learning import (get_few_shot_store, reset_few_shot_store,
    FewShotEmbedder, FewShotRetriever, FEW_SHOT_EMBED_DIM)
reset_few_shot_store()
store = get_few_shot_store()
emb = FewShotEmbedder.get_instance()

cam = "백학지구 - 연포천(4급 방성경)"
print("=== 1) 백필 전 임베딩 상태 ===")
for s in store.list_samples(cam):
    print(" ", s.sample_id, "emb=", None if s.embedding is None else f"{len(s.embedding)}d", s.embedding_model)

print("\n=== 2) 백필 실행 ===")
n = store.backfill_embeddings(cam)
print("백필 갱신:", n, "건")
for s in store.list_samples(cam):
    print(" ", s.sample_id, "emb=", None if s.embedding is None else f"{len(s.embedding)}d", s.embedding_model)

# 3) 평가 프레임(백학 FP #330)으로 검색
import openpyxl
from PIL import Image
wb = openpyxl.load_workbook(XLSX, data_only=True); ws = wb["라벨링_878건"]
rowmeta = {}
for r in ws.iter_rows(min_row=2, values_only=False):
    rowmeta[r[0].row] = (r[0].value, r[2].value, r[4].value)
qbytes = None; qno = None
for im in ws._images:
    er = im.anchor._from.row + 1; m = rowmeta.get(er)
    if m and str(m[1]).startswith("백학지구") and m[0] == 330:
        qbytes = im._data(); qno = m[0]; qcontent = m[2]; break
print(f"\n=== 3) 쿼리 프레임 #{qno} ({qcontent})로 검색 ===")
qv = emb.embed_bytes(qbytes)
print("query vec dim:", None if qv is None else qv.shape, "norm:", None if qv is None else round(float((qv**2).sum()**.5),3))
retr = FewShotRetriever(store)
for tau in (0.0, 0.3, 0.4, 0.5, 0.6):
    sel = retr.select(cam, "warning_close_to_machinery", qv, k_max=5, tau=tau)
    print(f"  tau={tau}: 선택 {len(sel)}건 -> " + ", ".join(f"{s.sample_id[:8]}({s.correction_type})" for s in sel))

# 유사도 점수 상세
import numpy as np
print("\n=== 4) #330 vs 각 백학 샘플 코사인 ===")
for s in store.list_samples(cam):
    v = np.asarray(s.embedding, dtype=np.float32)
    sim = float(np.dot(qv, v/np.linalg.norm(v)))
    print(f"  {s.sample_id[:8]} {s.correction_type:12} sim={sim:.3f}  note={s.user_note[:20]}")
