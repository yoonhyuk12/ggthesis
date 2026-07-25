# -*- coding: utf-8 -*-
"""Phase 1b+2 스모크: 5W1H 분류기 + 3단계 검색기."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
APP = "D:/onvifcctv"; ACCOUNT = "D:/onvifcctv/data/17e8d71a462e"
sys.path.insert(0, APP); os.chdir(APP)
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = ACCOUNT
from src.utils.few_shot_learning import (get_few_shot_store, reset_few_shot_store,
    FewShotClassifier, FewShotEmbedder, FewShotRetriever)
reset_few_shot_store()
store = get_few_shot_store()

# 1) 분류기: 사용자 예시 두 갈래 (신호수 인정 vs 부정)
clf = FewShotClassifier.get_instance()
print("=== 1) 5W1H 분류 테스트 ===")
cases = [
    ("작업지휘자로 위험사항 없음", "굴착기 작업 반경 내에 작업자가 근접", "warning_close_to_machinery", "false_alarm"),
    ("빨간색 안전모, 빨간색 조끼를 입지 않아, 신호수 부재 상태로 보아야 함", "신호수가 배치되어 안전", "warning_close_to_machinery", "miss"),
    ("충분히 거리가 있음", "굴착기 작업 반경 내 근접", "warning_close_to_machinery", "false_alarm"),
]
for note, reason, wk, ct in cases:
    tags = clf.classify(note, reason, wk, ct, jpeg_bytes=None)
    print(f"  [{ct}] {note[:24]:24} -> {tags}")

# 2) 백필 태그 (백학) + 검색
cam = "백학지구 - 연포천(4급 방성경)"
print("\n=== 2) 백학 태그 백필 ===")
n = store.backfill_tags(cam)
print("태그 백필:", n, "건")
for s in store.list_samples(cam):
    print(f"  {s.sample_id[:8]} {s.correction_type:12} tags={s.tags}")

print("\n=== 3) 검색기 (query_tags=오경보/통제된작업, 이미지 무) ===")
store2 = get_few_shot_store()
retr = FewShotRetriever(store2)
qtags = {"who":"작업자","what":"굴착기","how":"작업반경내근접","why":"통제된작업","direction":"false_alarm"}
sel = retr.select(cam, "warning_close_to_machinery", query_vec=None, query_tags=qtags, k_max=3)
print("선택:", [(s.sample_id[:8], s.tags.get("why") if s.tags else None) for s in sel])
