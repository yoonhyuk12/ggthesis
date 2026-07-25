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
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import PatternFill, Alignment, Font
from io import BytesIO

SRC = r'C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\원본_정오탐내역_260527_133030 (1).xlsx'
OUT_DIR = r'C:\Users\Sweet HOME\Documents\경기대 논문 연구\학회논문\실험데이터'
DST = os.path.join(OUT_DIR, '실험3_정밀도평가_878건_라벨링.xlsx')

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

g4 = df[(df['알림일시'] >= pd.Timestamp('2026-05-19')) & (df['이미지유무'])].sort_values('번호').reset_index(drop=True)
print(f"라벨링 대상: 878건 = 오탐 {(g4['판정']=='오탐').sum()} + 정탐 {(g4['판정']=='정탐').sum()}")

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '라벨링_878건'

headers = ['번호','알림일시','대상 카메라','분류','내용','2차 사유',
           'LLM 모델','프롬프트','AI 응답(초)','YOLO conf',
           '판정(LLM)','스냅샷','맞음여부','비고']
for ci, h in enumerate(headers, start=1):
    cell = ws.cell(row=1, column=ci, value=h)
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')

LLM_VERDICT_COL = 11  # K열 (스냅샷 좌측)
SNAPSHOT_COL = 12     # L열
LABEL_COL = 13        # M열 (스냅샷 우측, 입력칸)

# 컬럼 너비
for ci in range(1, 15):
    if ci == SNAPSHOT_COL:
        ws.column_dimensions[get_column_letter(ci)].width = 38
    elif ci in (3,5,6):  # 카메라/내용/2차사유
        ws.column_dimensions[get_column_letter(ci)].width = 28
    elif ci == LABEL_COL:
        ws.column_dimensions[get_column_letter(ci)].width = 12
    elif ci == LLM_VERDICT_COL:
        ws.column_dimensions[get_column_letter(ci)].width = 14
    else:
        ws.column_dimensions[get_column_letter(ci)].width = 13

# 헤더 행 고정
ws.freeze_panes = 'A2'

# LLM 정탐인 행 강조용
pos_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')

n_imgs = 0
for new_idx, (_, row) in enumerate(g4.iterrows(), start=2):
    ws.row_dimensions[new_idx].height = 220
    is_pos = (row['판정'] == '정탐')
    vals = [row['번호'], row['알림일시'], row['대상 카메라'],
            row['분류'], row['내용'], row['2차 사유'], row['LLM 모델'],
            row['프롬프트'], row['AI 응답(초)'], row['YOLO conf'],
            row['판정'], '', '', '']
    for ci, v in enumerate(vals, start=1):
        cell = ws.cell(row=new_idx, column=ci, value=v)
        if is_pos and ci != SNAPSHOT_COL and ci != LABEL_COL:
            cell.fill = pos_fill
        if ci == LLM_VERDICT_COL:
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.font = Font(bold=True, size=14)
        if ci == LABEL_COL:
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.font = Font(bold=True, size=18)
    src_row = row['엑셀행']
    if src_row in img_row_map:
        for src_img in img_row_map[src_row]:
            try:
                img_data = src_img._data() if callable(src_img._data) else src_img._data
                bio = BytesIO(img_data)
                new_img = XLImage(bio)
                marker_from = AnchorMarker(col=SNAPSHOT_COL-1, colOff=0, row=new_idx-1, rowOff=0)
                size = XDRPositiveSize2D(cx=pixels_to_EMU(280), cy=pixels_to_EMU(280))
                new_img.anchor = OneCellAnchor(_from=marker_from, ext=size)
                ws.add_image(new_img)
                n_imgs += 1
            except Exception as e:
                print(f"이미지 복사 실패: {e}")

# 데이터 유효성 검사: L열 드롭다운
label_col_letter = get_column_letter(LABEL_COL)
dv = DataValidation(type='list', formula1='"O,X,?"', allow_blank=True,
                    showDropDown=False, showErrorMessage=True,
                    errorTitle='입력 오류', error='O, X, ? 중 하나만 입력 가능합니다.')
dv.add(f'{label_col_letter}2:{label_col_letter}{len(g4)+1}')
ws.add_data_validation(dv)

# 안내 시트
ws_g = wb.create_sheet('라벨링안내')
guide = [
    ['항목','설명'],
    ['용도','논문 4.2.3 운영 정밀도 평가 (Precision · Recall · F1 · FAR 산출)'],
    ['표본','구간 4 (2026-05-19~05-27, 9일) 이미지 보유분 전수'],
    ['건수','878건 (LLM 오탐 826 + LLM 정탐 52)'],
    ['라벨러','사용자 1인 단독'],
    ['예상 작업시간','약 7~15시간 (1건당 30~60초)'],
    ['',''],
    ['===== 라벨링 방법 ====','=========================================='],
    ['1단계','L열의 사진을 본다'],
    ['2단계','B열의 LLM 판정 (오탐 또는 정탐)을 본다'],
    ['3단계','M열에 LLM 판정이 맞는지 입력 (드롭다운 또는 직접 입력)'],
    ['',''],
    ['M열 입력값','의미'],
    ['O','LLM 판정이 맞다'],
    ['X','LLM 판정이 틀리다'],
    ['?','이미지로 판단 곤란'],
    ['',''],
    ['예시 1','LLM=오탐, 사진=실제 위험 아님 → O (LLM 정확)'],
    ['예시 2','LLM=오탐, 사진=실제로 위험 → X (LLM이 놓침, FN)'],
    ['예시 3','LLM=정탐, 사진=실제로 위험 → O (LLM 정확, TP)'],
    ['예시 4','LLM=정탐, 사진=실제 위험 아님 → X (LLM 과민, FP)'],
    ['',''],
    ['색 강조','노란색 행 = LLM 정탐 판정 (52건). 시선 끌기용'],
    ['',''],
    ['완료 후','이 파일을 그대로 두면 자동으로 Confusion matrix, P/R/F1/CI, 표 본문이 산출됩니다.'],
]
for r, line in enumerate(guide, start=1):
    for c, v in enumerate(line, start=1):
        cell = ws_g.cell(row=r, column=c, value=v)
        if r == 1 or (isinstance(line[0], str) and '=====' in line[0]):
            cell.font = Font(bold=True)
ws_g.column_dimensions['A'].width = 22
ws_g.column_dimensions['B'].width = 75

wb.save(DST)
print(f"저장: {DST}")
print(f"파일 크기: {os.path.getsize(DST)/1024/1024:.2f} MB")
print(f"이미지 임베드: {n_imgs}장")
