import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import openpyxl
import os
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import pixels_to_EMU
from io import BytesIO

SRC = r'C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\원본_정오탐내역_260527_133030 (1).xlsx'
OUT_DIR = r'C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터'

df = pd.read_excel(SRC, sheet_name=0)
df['알림일시'] = pd.to_datetime(df['알림일시'], errors='coerce')
df['엑셀행'] = df.index + 2

wb_src = openpyxl.load_workbook(SRC)
ws_src = wb_src.worksheets[0]
img_row_map = {}
for img in ws_src._images:
    r = img.anchor._from.row + 1
    img_row_map.setdefault(r, []).append(img)
img_rows = set(img_row_map.keys())
df['이미지유무'] = df['엑셀행'].isin(img_rows)

def 구간(t):
    if pd.isna(t):
        return '?'
    if t < pd.Timestamp('2026-03-04'):
        return '1'
    if t < pd.Timestamp('2026-04-02'):
        return '2'
    if t < pd.Timestamp('2026-05-19'):
        return '3'
    return '4'
df['구간'] = df['알림일시'].apply(구간)

# === 실험 1: 전체 알림 분포 ===
exp1_cols = ['번호','판정','알림일시','대상 카메라','분류','내용','2차 사유',
             'LLM 모델','프롬프트','AI 응답(초)','YOLO conf','구간']
df1 = df[exp1_cols].copy()
dst1 = os.path.join(OUT_DIR, '실험1_운영알림분포_13787건.xlsx')
with pd.ExcelWriter(dst1, engine='openpyxl') as w:
    df1.to_excel(w, sheet_name='전체알림_13787건', index=False)
    guide = pd.DataFrame({
        '항목': ['용도','기간','건수','라벨 필요','산출 지표','구간 정의'],
        '설명': [
            '논문 4.2.1 운영 알림 분포 분석',
            '2026-02-11 ~ 2026-05-27 (80일)',
            '전체 13,787건 (LLM 자체 판정 기준)',
            '없음 (LLM 메타데이터만으로 분석)',
            'LLM SEND/BLOCK 비율, 시간당 알림 빈도, 모델/프롬프트 변천에 따른 추이',
            '구간1=결손기(~3/3), 구간2=메타도입기(3/4~4/1), 구간3=이미지산발기(4/2~5/18), 구간4=완전기(5/19~)'
        ]
    })
    guide.to_excel(w, sheet_name='안내', index=False)
print(f"실험1 저장: {dst1} ({os.path.getsize(dst1)/1024/1024:.2f} MB)")

# === 실험 2: 신뢰도 분석 ===
df2 = df[df['구간']=='4'][exp1_cols].copy()
dst2 = os.path.join(OUT_DIR, '실험2_신뢰도분석_구간4_1074건.xlsx')
with pd.ExcelWriter(dst2, engine='openpyxl') as w:
    df2.to_excel(w, sheet_name='구간4_1074건', index=False)
    guide = pd.DataFrame({
        '항목': ['용도','기간','건수','라벨 필요','산출 지표','시스템 구성'],
        '설명': [
            '논문 4.2.2 YOLO conf × LLM 판정 관계 분석',
            '2026-05-19 ~ 2026-05-27 (9일)',
            '구간 4 전체 1,074건 (YOLO conf 100% 기록)',
            '없음 (LLM 메타데이터만으로 분석)',
            'YOLO conf 구간별 SEND율, 임계값 시뮬레이션, 단조 관계 검증',
            'gemini-3.1-flash-lite + 공통prompt 계열 (현 운영)'
        ]
    })
    guide.to_excel(w, sheet_name='안내', index=False)
print(f"실험2 저장: {dst2} ({os.path.getsize(dst2)/1024/1024:.2f} MB)")

# === 실험 3: 정밀도 평가 (877건 전수 라벨링) ===
def make_label_file(subset, dst, sheet_title, guide_rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    headers = ['번호','판정(LLM)','알림일시','대상 카메라','분류','내용','2차 사유',
               'LLM 모델','프롬프트','AI 응답(초)','YOLO conf','스냅샷',
               '정답라벨','라벨러비고']
    for ci, h in enumerate(headers, start=1):
        ws.cell(row=1, column=ci, value=h)
    SNAPSHOT_COL = 12
    for ci in range(1, 15):
        if ci == SNAPSHOT_COL:
            ws.column_dimensions[get_column_letter(ci)].width = 25
        elif ci in (4,6,7):
            ws.column_dimensions[get_column_letter(ci)].width = 28
        else:
            ws.column_dimensions[get_column_letter(ci)].width = 13
    n_imgs = 0
    for new_idx, (_, row) in enumerate(subset.iterrows(), start=2):
        ws.row_dimensions[new_idx].height = 120
        vals = [row['번호'], row['판정'], row['알림일시'], row['대상 카메라'],
                row['분류'], row['내용'], row['2차 사유'], row['LLM 모델'],
                row['프롬프트'], row['AI 응답(초)'], row['YOLO conf'], '', '', '']
        for ci, v in enumerate(vals, start=1):
            ws.cell(row=new_idx, column=ci, value=v)
        src_row = row['엑셀행']
        if src_row in img_row_map:
            for src_img in img_row_map[src_row]:
                try:
                    img_data = src_img._data() if callable(src_img._data) else src_img._data
                    bio = BytesIO(img_data)
                    new_img = XLImage(bio)
                    marker_from = AnchorMarker(col=SNAPSHOT_COL-1, colOff=0, row=new_idx-1, rowOff=0)
                    size = XDRPositiveSize2D(cx=pixels_to_EMU(140), cy=pixels_to_EMU(140))
                    new_img.anchor = OneCellAnchor(_from=marker_from, ext=size)
                    ws.add_image(new_img)
                    n_imgs += 1
                except Exception as e:
                    print(f"이미지 복사 실패: {e}")
    ws_g = wb.create_sheet('안내')
    for r, line in enumerate(guide_rows, start=1):
        for c, v in enumerate(line, start=1):
            ws_g.cell(row=r, column=c, value=v)
    ws_g.column_dimensions['A'].width = 20
    ws_g.column_dimensions['B'].width = 75
    wb.save(dst)
    return n_imgs

g4 = df[(df['구간']=='4') & (df['이미지유무'])].sort_values('번호').reset_index(drop=True)
g4_oh = g4[g4['판정']=='오탐'].copy()
g4_jt = g4[g4['판정']=='정탐'].copy()
print(f"실험3 라벨링: 오탐 {len(g4_oh)} + 정탐 {len(g4_jt)} = {len(g4)}건")

# 3a 정탐
dst3a = os.path.join(OUT_DIR, '실험3_정밀도평가_정탐52_라벨링.xlsx')
guide3a = [
    ['항목','설명'],
    ['용도','논문 4.2.3 운영 정밀도 평가 — 정탐 부분'],
    ['표본','구간 4 (5/19~5/27) 정탐 전수 (이미지 보유)'],
    ['건수','52건'],
    ['라벨러','사용자 1인 단독'],
    ['예상 작업시간','약 30분~1시간'],
    ['시스템 구성','gemini-3.1-flash-lite + 공통prompt 계열'],
    ['',''],
    ['정답라벨 입력','정탐 / 오탐 / 판단불가'],
    ['정탐','실제로 위험 상황 (LLM 판정 정확 → TP)'],
    ['오탐','실제는 위험 아님 (LLM이 잘못 SEND → FP)'],
    ['판단불가','이미지로 판단 곤란'],
]
n3a = make_label_file(g4_jt, dst3a, '실험3_정탐52', guide3a)
print(f"  실험3a 저장: {dst3a} ({os.path.getsize(dst3a)/1024/1024:.2f} MB), 이미지 {n3a}장")

# 3b 오탐
dst3b = os.path.join(OUT_DIR, '실험3_정밀도평가_오탐826_라벨링.xlsx')
guide3b = [
    ['항목','설명'],
    ['용도','논문 4.2.3 운영 정밀도 평가 — 오탐 부분'],
    ['표본','구간 4 (5/19~5/27) 오탐 전수 (이미지 보유)'],
    ['건수','826건'],
    ['라벨러','사용자 1인 단독'],
    ['예상 작업시간','약 7~14시간 (1건당 30~60초)'],
    ['시스템 구성','gemini-3.1-flash-lite + 공통prompt 계열'],
    ['',''],
    ['정답라벨 입력','정탐 / 오탐 / 판단불가'],
    ['정탐','실제 위험인데 LLM이 BLOCK함 (False Negative → 시스템 실패)'],
    ['오탐','실제는 위험 아님, LLM 판정 정확 (True Negative)'],
    ['판단불가','이미지로 판단 곤란'],
]
n3b = make_label_file(g4_oh, dst3b, '실험3_오탐826', guide3b)
print(f"  실험3b 저장: {dst3b} ({os.path.getsize(dst3b)/1024/1024:.2f} MB), 이미지 {n3b}장")

print("\n=== 디렉토리 내용 ===")
for f in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}  ({os.path.getsize(fp)/1024/1024:.2f} MB)")
