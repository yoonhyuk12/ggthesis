# -*- coding: utf-8 -*-
"""Few-shot k-sweep 실험 — 스모크 테스트.
앱 코드(settings/ai_second_check/few_shot)를 독립 실행에서 재사용 가능한지 검증.
실행: cwd=D:/onvifcctv, .venv312_cuda 파이썬.
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

APP = "D:/onvifcctv"
ACCOUNT_DIR = "D:/onvifcctv/data/17e8d71a462e"
XLSX = r"C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터\실험3_정밀도평가_878건_라벨링.xlsx"
sys.path.insert(0, APP)
os.chdir(APP)

from PyQt6.QtCore import QCoreApplication
app = QCoreApplication.instance() or QCoreApplication(sys.argv)
QCoreApplication.setOrganizationName("ONVIF")
QCoreApplication.setApplicationName("CCTVViewer")

# 사용자 데이터 디렉토리 전역 세팅 (few_shot 스토어가 이걸 참조)
import src.utils.user_data as ud
ud._current_data_dir = ACCOUNT_DIR

from src.utils.settings_service import get_settings_service
from src.utils.ai_second_check import AISecondChecker
from src.utils.few_shot_learning import get_few_shot_store, reset_few_shot_store

# --- 실제 앱 코드(수정된 cv2.imdecode) 그대로 사용. 주입 카운터만 래핑 ---
import src.utils.few_shot_learning as fsl
_inject_count = {"n": 0}
_orig_encode = fsl._resize_and_encode_jpeg
def _counting_encode(image_path, max_size, quality):
    out = _orig_encode(image_path, max_size, quality)
    if out is not None:
        _inject_count["n"] += 1
    return out
fsl._resize_and_encode_jpeg = _counting_encode

reset_few_shot_store()
s = get_settings_service()
print("=== settings ===")
print("Gemini api key set:", bool(s.get_provider_api_key("Gemini")))
print("model:", s.value("ai_second_check_model", "gemini-3.1-flash-lite", type=str))
print("provider:", s.value("ai_second_check_provider", "", type=str))
print("few_shot_enabled:", s.get_few_shot_enabled())
print("user_data_dir:", ud.get_user_data_dir())

checker = AISecondChecker()
cam = "백학지구 - 연포천(4급 방성경)"
prompt = checker._resolve_prompt(cam)
print("resolved prompt len:", len(prompt), "(0이면 공통prompt 폴백)")

store = get_few_shot_store()
samples = store.list_samples(cam)
print(f"\n=== 백학 few-shot 샘플 {len(samples)}건 ===")
for smp in samples:
    p = store.get_image_path(cam, smp)
    print(" ", smp.sample_id, smp.correction_type, "img_exists=", os.path.exists(p))

# --- 878 xlsx에서 백학 테스트 이미지 1장 추출 ---
import openpyxl
from PIL import Image
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["라벨링_878건"]
rowmeta = {}
for r in ws.iter_rows(min_row=2, values_only=False):
    rowmeta[r[0].row] = (r[0].value, r[2].value, r[4].value, r[10].value, r[13].value)  # no, cam, 내용, 판정, 맞음
# 백학 FP 오답(정탐/X, #301·#307 누수 제외) 이미지 찾기 — k=0이 잘못 SEND할 케이스
test_img = None; test_no = None; test_content = None
for im in ws._images:
    er = im.anchor._from.row + 1
    meta = rowmeta.get(er)
    if meta and str(meta[1]).startswith("백학지구") and meta[3] == "정탐" and meta[4] == "X" and meta[0] not in (301, 307):
        test_img = im._data(); test_no = meta[0]; test_content = meta[2]
        print(f"\n테스트 알림 #{test_no} (FP 오답, 실제=안전): 내용={meta[2]} 판정={meta[3]} 맞음={meta[4]}")
        break

if test_img:
    wk = "warning_close_to_machinery" if "중장비" in str(test_content) else "warning_close_to_vehicle"
    print("\n=== 실제 LLM 1콜 (k=0) ===")
    allow, reason = checker._api_check(
        "Gemini", s.value("ai_second_check_model", "gemini-3.1-flash-lite", type=str),
        prompt, cam, wk, str(test_content), frame_jpeg=test_img, few_shot_samples=None,
        thinking_level=s.get_ai_second_check_thinking_level(),
    )
    print("verdict:", "SEND" if allow else "BLOCK", "| reason:", reason[:80])

    # clean 샘플(878 밖): 0626f424·f08c1afe·12fb96ab — #301/#307 누수분 제외
    clean = [smp for smp in samples if smp.sample_id in ("0626f424465b", "f08c1afe9ef9", "12fb96ab4f6b")]
    _inject_count["n"] = 0
    print(f"\n=== 실제 LLM 1콜 (k={len(clean)}, clean 백학 샘플 주입) ===")
    allow2, reason2 = checker._api_check(
        "Gemini", s.value("ai_second_check_model", "gemini-3.1-flash-lite", type=str),
        prompt, cam, wk, str(test_content), frame_jpeg=test_img, few_shot_samples=clean,
        thinking_level=s.get_ai_second_check_thinking_level(),
    )
    print("주입된 few-shot 이미지 수:", _inject_count["n"], "(0이면 패치 실패)")
    print("verdict:", "SEND" if allow2 else "BLOCK", "| reason:", reason2[:80])
    print("\n>>> k=0:", "SEND" if allow else "BLOCK", "→ k=3:", "SEND" if allow2 else "BLOCK",
          "| FP가 BLOCK으로 교정되면 few-shot 효과 입증")
else:
    print("백학 테스트 이미지 못 찾음")
