# -*- coding: utf-8 -*-
"""Phase 3 통합 검증: should_send → RAG 동적 선택 경로가 실제 동작하는지."""
import sys, os, json, io
sys.path.insert(0, "D:/onvifcctv"); os.chdir("D:/onvifcctv")
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = "D:/onvifcctv/data/17e8d71a462e"

from src.utils.settings_service import get_settings_service
from src.utils.ai_second_check import AISecondChecker
from src.utils.few_shot_learning import get_few_shot_store, reset_few_shot_store
reset_few_shot_store()

OUT = "C:/Users/Sweet HOME/Documents/경기대 논문 연구/학회논문/실험데이터/_rag_integration_out.json"
out = {}
s = get_settings_service()
out["rag_enabled"] = s.get_few_shot_rag_enabled()
out["k_max"] = s.get_few_shot_rag_k_max()
out["fs_enabled"] = s.get_few_shot_enabled()

# 백학 평가 프레임 #330 (FP) 추출
import openpyxl
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
wb = openpyxl.load_workbook(XLSX, data_only=True); ws = wb["라벨링_878건"]
rm = {}
for r in ws.iter_rows(min_row=2, values_only=False):
    rm[r[0].row] = (r[0].value, r[2].value, r[4].value)
frame = None
for im in ws._images:
    er = im.anchor._from.row + 1; m = rm.get(er)
    if m and str(m[1]).startswith("백학지구") and m[0] == 330:
        frame = im._data(); break
out["frame_found"] = frame is not None

checker = AISecondChecker()
cam = "백학지구 - 연포천(4급 방성경)"
# RAG 경로로 샘플 선택 (LLM 호출 없이 선택만)
sel = checker._load_few_shot_samples(cam, "warning_close_to_machinery", frame)
out["rag_selected"] = [{"id": x.sample_id[:8], "why": (x.tags or {}).get("why"),
                        "ct": x.correction_type} for x in sel]
# 비교: RAG OFF (전량)
s.set_few_shot_rag_enabled(False)
allsel = checker._load_few_shot_samples(cam, "warning_close_to_machinery", frame)
out["all_count"] = len(allsel)
s.set_few_shot_rag_enabled(True)  # 복구

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("WROTE")
