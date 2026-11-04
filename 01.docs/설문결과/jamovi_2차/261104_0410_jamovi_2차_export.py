"""2026-11-04 jamovi 2차 입력본 생성.

2026-11-03 사용자 결정(연구가설 (2-1)·조절변수 W·공통부 Part C 4문항 삭제, 전용부 D→C·E→D 재부여,
기록: 01.docs/설문항목_작업이력.md 2026-11-03 항목)을 jamovi 1차 입력본
`01.docs/설문결과/jamovi/261031_1046_jamovi용_설문응답_73건_한글헤더.xlsx`에 적용한다.
응답 값은 한 칸도 바꾸지 않고, 열 삭제(C1~C4, W_예산제약성)와 열 이름 변경(D→C, E→D)만 한다.

사용법 (저장소 루트에서):
  PYTHONIOENCODING=utf-8 python "01.docs/설문결과/jamovi_2차/261104_0410_jamovi_2차_export.py" [--legacy <경로>]
  --legacy : git 6332282에서 꺼낸 261024_1753_설문응답_리커트숫자변환.xlsx(작업 트리에서 삭제됨). 주면 '분석자료' 시트와
             값을 대조해 검증 JSON에 차이를 기록한다. 대조 결과는 참고용이며 기준은 항상 10-31 한글헤더 파일이다.
"""
import sys, json, hashlib, re, argparse
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

sys.stdout.reconfigure(encoding='utf-8')

PREFIX = '261104_0410'
HERE = Path(__file__).resolve().parent                      # 01.docs/설문결과/jamovi_2차
ROOT = HERE.parents[2]                                      # 저장소 루트
BASE_REL = Path('01.docs/설문결과/jamovi/261031_1046_jamovi용_설문응답_73건_한글헤더.xlsx')
SRC_REL = Path('01.docs/설문결과/중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구(응답).xlsx')
OUT_XLSX = HERE / f'{PREFIX}_jamovi용_설문응답_73건_2차_PartC삭제.xlsx'
OUT_JSON = HERE / f'{PREFIX}_jamovi_2차변환_검증.json'

DROP = ['C1', 'C2', 'C3', 'C4', 'W_예산제약성']
RENAME = {
    **{f'D{i}': f'C{i}' for i in range(1, 9)},
    **{f'E{i}': f'D{i}' for i in range(1, 5)},
    'Dsub1_인프라범용성': 'Csub1_인프라범용성',
    'Dsub2_탐지제어안정성': 'Csub2_탐지제어안정성',
    'Dsub3_오탐필터링': 'Csub3_오탐필터링',
    'Dsub4_알림전파즉각성': 'Csub4_알림전파즉각성',
    'D_시스템특성': 'C_시스템특성',
    'E_경보피로완화': 'D_경보피로완화',
}
EXPECTED_HEADER = (
    ['respondent_id', 'D_도입여부', '소속', '성별', '나이', '경력', '역할', '총공사비',
     'A7_인지경로', 'A8_인지시점', 'A9_전달시간']
    + [f'B{i}' for i in range(1, 9)] + [f'C{i}' for i in range(1, 9)] + [f'D{i}' for i in range(1, 5)]
    + ['Y_실효성', 'Y1_조기인지', 'Y2_대응신속성', 'Y3_원격파악', 'Y4_순찰부담경감', 'Y5_위험통제력',
       'Csub1_인프라범용성', 'Csub2_탐지제어안정성', 'Csub3_오탐필터링', 'Csub4_알림전파즉각성',
       'C_시스템특성', 'D_경보피로완화', 'sys_path_시스템경로']
)
ADOPT_ONLY = [f'C{i}' for i in range(1, 9)] + [f'D{i}' for i in range(1, 5)] + [
    'Csub1_인프라범용성', 'Csub2_탐지제어안정성', 'Csub3_오탐필터링', 'Csub4_알림전파즉각성',
    'C_시스템특성', 'D_경보피로완화', 'sys_path_시스템경로']
DERIVED_RULE = {  # 새 이름 기준 채점 규칙(평균). 1차 codebook과 같다.
    'Y_실효성': [f'B{i}' for i in range(1, 9)], 'Y1_조기인지': ['B1'], 'Y2_대응신속성': ['B2'],
    'Y3_원격파악': ['B3', 'B4'], 'Y4_순찰부담경감': ['B5', 'B6'], 'Y5_위험통제력': ['B7', 'B8'],
    'Csub1_인프라범용성': ['C1', 'C2'], 'Csub2_탐지제어안정성': ['C3', 'C4'],
    'Csub3_오탐필터링': ['C5', 'C6'], 'Csub4_알림전파즉각성': ['C7', 'C8'],
    'C_시스템특성': [f'C{i}' for i in range(1, 9)], 'D_경보피로완화': [f'D{i}' for i in range(1, 5)],
}
# 10-24 리커트 변환본 '분석자료' 시트 열 이름 ↔ 새 열 이름 (대조용)
LEGACY_MAP = {
    'respondent_id': 'resp_id', 'D_도입여부': 'group', '소속': 'A1_affil', '성별': 'A2_sex', '나이': 'A3_age',
    '경력': 'A4_exp', '역할': 'A5_role', '총공사비': 'A6_cost', 'A7_인지경로': 'A7_path', 'A8_인지시점': 'A8_when',
    'A9_전달시간': 'A9_lag', **{f'B{i}': f'B{i}' for i in range(1, 9)},
    **{f'C{i}': f'D{i}' for i in range(1, 9)}, **{f'D{i}': f'E{i}' for i in range(1, 5)},
    'Y_실효성': 'Y_total', 'Y1_조기인지': 'Y1', 'Y2_대응신속성': 'Y2', 'Y3_원격파악': 'Y3', 'Y4_순찰부담경감': 'Y4',
    'Y5_위험통제력': 'Y5', 'Csub1_인프라범용성': 'D_sub1', 'Csub2_탐지제어안정성': 'D_sub2',
    'Csub3_오탐필터링': 'D_sub3', 'Csub4_알림전파즉각성': 'D_sub4', 'C_시스템특성': 'D_total',
    'D_경보피로완화': 'E_total', 'sys_path_시스템경로': 'sys_path',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rename_items_in_text(text):
    """'D-3)' → 'C-3)', 'E-2)' → 'D-2)', '평균(D1,D2)' → '평균(C1,C2)' 처럼 문항 기호만 바꾼다."""
    if not isinstance(text, str):
        return text
    text = re.sub(r'^D-(\d)\)', r'C-\1)', text)
    text = re.sub(r'^E-(\d)\)', r'D-\1)', text)

    def repl(m):
        items = [RENAME.get(x.strip(), x.strip()) for x in m.group(1).split(',')]
        return '평균(' + ','.join(items) + ')'
    return re.sub(r'평균\(([^)]*)\)', repl, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--legacy', help='261024_1753_설문응답_리커트숫자변환.xlsx 경로(git 복구본), 선택')
    args = ap.parse_args()

    base = ROOT / BASE_REL
    src = ROOT / SRC_REL
    base_sha_before = sha(base)
    src_sha = sha(src) if src.exists() else None

    wb = openpyxl.load_workbook(base, data_only=True)
    ws = wb['data']
    rows = list(ws.values)
    header = list(rows[0])
    data = rows[1:]
    assert len(data) == 73 and len(header) == 49, (len(data), len(header))
    for col in DROP + list(RENAME):
        assert col in header, col

    keep_idx = [i for i, h in enumerate(header) if h not in DROP]
    new_header = [RENAME.get(header[i], header[i]) for i in keep_idx]
    assert new_header == EXPECTED_HEADER, new_header
    new_rows = [[row[i] for i in keep_idx] for row in data]

    # codebook 변환: 삭제 행 제거, 변수명·문항 기호·채점 규칙 기호만 변경
    cb_rows = list(wb['codebook'].values)
    cb_header = list(cb_rows[0])
    codebook = []
    for r in cb_rows[1:]:
        var = r[0]
        if var in DROP:
            continue
        r = list(r)
        r[0] = RENAME.get(var, var)
        r[1] = rename_items_in_text(r[1])
        r[5] = rename_items_in_text(r[5])
        if var == 'D_도입여부':
            r[5] = '독립변수(도입=1, 미도입=0). 전용부 D1~D4(경보 피로도 완화) 문항과 구분'
        codebook.append(r)
    assert [r[0] for r in codebook] == EXPECTED_HEADER

    # 10-24 리커트 변환본 대조(선택)
    legacy_report = None
    if args.legacy:
        lp = Path(args.legacy)
        lwb = openpyxl.load_workbook(lp, data_only=True)
        lws = lwb['분석자료']
        lrows = list(lws.values)
        lhdr = list(lrows[0])
        lidx = {h: i for i, h in enumerate(lhdr)}
        legacy_by_id = {row[lidx['resp_id']]: row for row in lrows[1:] if row[lidx['resp_id']]}
        diffs = []
        compared = 0
        for row in new_rows:
            rid = row[0]
            lrow = legacy_by_id.get(rid)
            if lrow is None:
                diffs.append({'respondent_id': rid, 'variable': '(행 없음)', 'new': None, 'legacy': None})
                continue
            for j, name in enumerate(new_header):
                lname = LEGACY_MAP[name]
                a, b = row[j], lrow[lidx[lname]]
                compared += 1
                same = (a is None and b is None) or (
                    a is not None and b is not None and isinstance(a, (int, float)) and isinstance(b, (int, float))
                    and abs(float(a) - float(b)) < 1e-9) or (a == b)
                if not same:
                    diffs.append({'respondent_id': rid, 'variable': name, 'legacy_variable': lname, 'new': a, 'legacy': b})
        by_var = {}
        for d in diffs:
            by_var[d['variable']] = by_var.get(d['variable'], 0) + 1
        legacy_report = {
            'legacy_file': lp.name, 'legacy_sha256': sha(lp), 'legacy_sheet': '분석자료',
            'legacy_rows': len(legacy_by_id), 'cells_compared': compared, 'cells_different': len(diffs),
            'different_by_variable': by_var, 'differences': diffs[:200],
            'legacy_include_0_ids': sorted(rid for rid, row in legacy_by_id.items() if row[lidx['include']] == 0),
        }

    # 저장
    out = openpyxl.Workbook()
    d = out.active
    d.title = 'data'
    d.append(new_header)
    for row in new_rows:
        d.append(list(row))
    d.freeze_panes = 'C2'
    d.auto_filter.ref = d.dimensions
    for cell in d[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='245678')
    for col in d.columns:
        d.column_dimensions[col[0].column_letter].width = max(12, len(str(col[0].value)) + 2)

    cb = out.create_sheet('codebook')
    cb.append(cb_header)
    for r in codebook:
        cb.append(r)
    cb.freeze_panes = 'A2'
    cb.auto_filter.ref = cb.dimensions
    for k, width in {'A': 22, 'B': 72, 'C': 18, 'D': 24, 'E': 90, 'F': 95}.items():
        cb.column_dimensions[k].width = width
    for row in cb:
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=True)

    mapping_text = '; '.join(f'{k}→{v}' for k, v in RENAME.items())
    legacy_text = ('대조하지 않음(--legacy 미지정)' if legacy_report is None else
                   f"git 6332282의 {legacy_report['legacy_file']} '분석자료' 시트와 {legacy_report['cells_compared']}칸 대조, "
                   f"차이 {legacy_report['cells_different']}칸(변수별: {legacy_report['different_by_variable']}). "
                   "차이가 있어도 기준은 10-31 한글헤더 파일이다(1차 jamovi 분석에 실제 쓰인 입력본).")
    notes = [
        ['내용', 'jamovi 2차 분석용: 73건 전부 포함. 2026-11-03 결정(연구가설 (2-1)·조절변수 W·공통부 Part C 삭제, 전용부 D→C·E→D 재부여) 반영'],
        ['가져올 시트', 'data (첫 번째 시트)'],
        ['응답 수', len(new_rows)],
        ['변수 수', len(new_header)],
        ['기준 파일', str(BASE_REL).replace('\\', '/')],
        ['기준 파일 SHA256', base_sha_before],
        ['원본 파일(Google Forms)', str(SRC_REL).replace('\\', '/')],
        ['원본 SHA256', src_sha],
        ['생성 시각', datetime.now().isoformat()],
        ['변경 사유', '2026-11-03 사용자 결정: 연구가설 (2-1)·조절변수 W(안전관리 예산 제약성)·공통부 Part C 4문항 삭제, 전용부 D→C·E→D 재부여. 기록: 01.docs/설문항목_작업이력.md 2026-11-03 항목'],
        ['삭제 변수', 'C1, C2, C3, C4(구 공통부 Part C 예산 제약성 문항), W_예산제약성(C1~C4 평균)'],
        ['변경 대응표(구→현행)', mapping_text],
        ['값 불변', '남은 44개 변수의 73행 값은 기준 파일과 셀 단위로 동일(검증 JSON roundtrip_exact). 채점 규칙(평균)도 그대로이며 codebook의 문항 기호만 바꿨다'],
        ['10-24 리커트 변환본 대조', legacy_text],
        ['H1 설정', '종속변수 Y_실효성; Fixed Factors D_도입여부, 소속, 성별, 역할, 총공사비; Covariates 나이, 경력 (04장 제5절 제2항 여섯째)'],
        ['H2 설정', '없음. 연구가설 (2-1)·조절변수 W·상호작용 분석은 2026-11-03에 삭제'],
        ['주의', 'XLSX에는 jamovi 값라벨·측정수준 메타데이터가 내장되지 않는다. codebook을 기준으로 가져온 뒤 변수 설정 확인. 1차 .omv의 분석 설정은 변수명이 같은 Y_실효성·D_도입여부·통제변수에 그대로 적용된다'],
        ['표본', '73건 전부 본 응답으로 분석(2026-10-26 사용자 판단: 시험응답 없음)'],
        ['원고', '본문·HWPX 수정 없음'],
    ]
    info = out.create_sheet('readme')
    for row in notes:
        info.append(row)
    info.column_dimensions['A'].width = 26
    info.column_dimensions['B'].width = 125
    for row in info:
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    out.save(OUT_XLSX)

    # 검증: 다시 열어 기준 파일과 셀 단위 대조
    chk = openpyxl.load_workbook(OUT_XLSX, data_only=True)
    cws = chk.worksheets[0]
    assert cws.title == 'data'
    vals = list(cws.values)
    assert list(vals[0]) == EXPECTED_HEADER
    assert cws.max_row == 74 and cws.max_column == 44
    base_idx = {h: i for i, h in enumerate(header)}
    inv = {v: k for k, v in RENAME.items()}
    for out_row, base_row in zip(vals[1:], data):
        assert out_row[0] == base_row[0]
        for j, name in enumerate(EXPECTED_HEADER):
            b = base_row[base_idx[inv.get(name, name)]]
            a = out_row[j]
            if b is None:
                assert a is None, (out_row[0], name, a, b)
            elif j == 0:
                assert a == b
            else:
                assert isinstance(a, (int, float)) and abs(float(a) - float(b)) < 1e-12, (out_row[0], name, a, b)
    for name in DROP:
        assert name not in vals[0] or name.startswith('C')  # C1~C4는 새 이름으로 재사용되므로 이름만으로는 판정 불가
    assert not any(str(h).startswith('W') or str(h).startswith('E') for h in vals[0])
    oi = {h: i for i, h in enumerate(vals[0])}
    non = [r for r in vals[1:] if r[oi['D_도입여부']] == 0]
    adopt = [r for r in vals[1:] if r[oi['D_도입여부']] == 1]
    for name in ADOPT_ONLY:
        assert all(r[oi[name]] is None for r in non), name
    for name, items in DERIVED_RULE.items():
        for r in adopt if name.startswith(('C', 'D')) else vals[1:]:
            vs = [r[oi[i]] for i in items]
            if any(v is None for v in vs):
                assert r[oi[name]] is None, (r[0], name)
            else:
                assert abs(r[oi[name]] - sum(vs) / len(vs)) < 1e-9, (r[0], name, r[oi[name]], vs)
    chk.close()

    base_sha_after = sha(base)
    assert base_sha_before == base_sha_after
    result = {
        'base_file': str(BASE_REL).replace('\\', '/'),
        'base_sha256_before': base_sha_before, 'base_sha256_after': base_sha_after,
        'source_file': str(SRC_REL).replace('\\', '/'), 'source_sha256': src_sha,
        'output_file': OUT_XLSX.name, 'output_sha256': sha(OUT_XLSX),
        'dropped': DROP, 'renamed': RENAME,
        'validation': {
            'rows': 73, 'columns': 44, 'first_sheet': 'data', 'header_exact': True,
            'kept_cells_identical_to_base': True, 'nonadopter_blank_in_adopt_only': True,
            'derived_means_recomputed_from_renamed_items': True, 'no_W_or_E_prefixed_columns': True,
            'group_counts': {'adopt': len(adopt), 'nonadopt': len(non)},
        },
        'legacy_261024_comparison': legacy_report,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'legacy_261024_comparison'}, ensure_ascii=False, indent=2))
    if legacy_report:
        print('legacy comparison:', json.dumps({k: v for k, v in legacy_report.items() if k != 'differences'}, ensure_ascii=False))
        for dd in legacy_report['differences'][:40]:
            print('  diff', dd)


if __name__ == '__main__':
    main()
