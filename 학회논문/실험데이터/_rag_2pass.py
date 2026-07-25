# -*- coding: utf-8 -*-
"""2-pass RAG 통합 검증: 실프레임 → 1차 분류(저렴모델) → 검색 → 선택."""
import sys, os, json
sys.path.insert(0, "D:/onvifcctv"); os.chdir("D:/onvifcctv")
from PyQt6.QtCore import QCoreApplication
QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF"); QCoreApplication.setApplicationName("CCTVViewer")
import src.utils.user_data as ud; ud._current_data_dir = "D:/onvifcctv/data/17e8d71a462e"
from src.utils.settings_service import get_settings_service
from src.utils.ai_second_check import AISecondChecker
from src.utils.few_shot_learning import reset_few_shot_store
reset_few_shot_store()

OUT = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\_rag_2pass_out.json"
out = {}
s = get_settings_service()
out["search_model"] = s.get_few_shot_search_model()
out["rag_enabled"] = s.get_few_shot_rag_enabled()
out["k_max"] = s.get_few_shot_rag_k_max()

# 백학 #330 (FP) + 빈카메라 비교용으로 프레임 추출
import openpyxl
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
wb = openpyxl.load_workbook(XLSX, data_only=True); ws = wb["라벨링_878건"]
rm = {}
for r in ws.iter_rows(min_row=2, values_only=False):
    rm[r[0].row] = (r[0].value, r[2].value, r[4].value)
frame = None; content = None
for im in ws._images:
    er = im.anchor._from.row + 1; m = rm.get(er)
    if m and str(m[1]).startswith("백학지구") and m[0] == 330:
        frame = im._data(); content = m[2]; break
out["frame_found"] = frame is not None
out["warning_message"] = content

checker = AISecondChecker()
cam = "백학지구 - 연포천(4급 방성경)"
wk = "warning_close_to_machinery"

# 2-pass 실행 (LLM 1차 분류 호출 포함)
sel = checker._load_few_shot_samples(cam, wk, content, frame)
out["selected"] = [{"id": x.sample_id[:8], "why": (x.tags or {}).get("why"),
                    "ct": x.correction_type} for x in sel]
out["selected_count"] = len(sel)

# 카드 없는 카메라는 분류 호출 없이 즉시 [] 인지 (비용 0 확인)
sel_empty = checker._load_few_shot_samples("존재하지않는카메라XYZ", wk, content, frame)
out["empty_camera_selected"] = len(sel_empty)

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("WROTE")
