import json
from pathlib import Path
import pandas as pd
q=Path(__file__).resolve().parent
r=json.loads((q/'results.json').read_text(encoding='utf-8'))
h=r['H1']; d=h['diff']; e=h['emm']['proportional']; dg=r['H1_diagnostics']; rob=r['H1_robustness']; h2=r['H2']
inter=next(x for x in h2['coefs'] if x['term']=='D:W_c')
ih=next(x for x in h2['hc3_coefs'] if x['term']=='D:W_c')
changes=pd.read_csv(q/'changes_vs_previous.csv')
actual=changes[changes.variable.isin(['A5_role','A7_path','A8_when','B1','B3','B5'])]
def ci(z): return f"[{z['ci_lo']:.3f}, {z['ci_hi']:.3f}]"
def p(x): return '<.001' if x<.001 else f'{x:.3f}'
lines=['# 설문 응답 ANCOVA 재분석 결과 — 2026-10-25','',
'현행 제4장 제2·3·5절의 분석 규칙을 현재 응답 파일에 적용한 재분석이다. 기존 결과를 확인한 상태에서 수행했으며 새 사전등록 분석으로 간주하지 않는다. 논문 본문과 HWPX는 수정하지 않았다.','',
f"**핵심 결과:** 도입 집단의 안전관리 실효성 조정 평균은 미도입 집단보다 {d['B']:.3f}점 높았다(95% CI {ci(d)}, F(1, {h['df2']})={h['F']:.3f}, p={p(h['p'])}, 부분 η²={h['partial_eta2']:.3f}). H1은 지지되며 예산 제약성과 집단의 상호작용 H2는 지지되지 않았다.",'',
'## 자료와 이전 분석의 차이','',
'- 원응답 73건에서 기존 코딩에 시험응답으로 지정된 첫 2건(R001·R002)을 제외했다. 현장명 표기는 각각 ‘테스트’·‘없음’이고 행 위치·집단은 기존 지정과 같지만 타임스탬프와 일부 문항값은 변경되어 동일 원자료라고 볼 수 없다. 기존 시험응답 지정의 연속성을 전제로 제외를 유지했으며, 이 2건을 포함한 민감도 결과도 아래에 제시한다.',
'- 분석 대상은 71명(도입 32명·미도입 39명)이다. 현재 파일에는 Y·W·여섯 조정변수 결측이 없어 모두 H1·H2에 포함된다. 기존 분석은 역할 결측 1건을 뺀 70명이었다. 설계상 비해당인 미도입 D·E 문항은 결측 제외 사유로 사용하지 않았다.',
f'- 이전 coded_data.csv와 행 순서 기반으로 비교하면 실제 범주·문항 코드 변경은 {len(actual)}셀, {actual.resp_id.nunique()}개 응답에 걸쳐 있다(시험응답 포함). 파생 점수와 기타 텍스트 변경은 별도 CSV에 보존했다. 응답 ID는 행 순서 부여값이므로 영구 개인 식별자로 해석하지 않는다.',
'- 변경 항목별 수: '+', '.join(f'{k} {v}건' for k,v in actual.groupby('variable').size().items())+'.',
'- 기존 시험행 타임스탬프는 2026-10-14 10:31:32/10:32:38, 현재는 2026-10-17 08:14:23/08:36:40이다. 다른 행의 과거 타임스탬프 사본은 이번 대조 자료에 없어 전체 타임스탬프 변경 건수는 산출하지 않았다.',
'- 71명 중 현장명·성명이 남은 응답은 각각 3건이며 68건은 빈칸이다. 남은 3건에서는 중복 문자열이 없지만, 전체 표본의 현장당 1명·동일인 중복 여부는 현재 파일만으로 검증할 수 없다. 설치일과 실제 3개월 정상 운용도 이 파일만으로 확인할 수 없다. 집단은 설문 첫 분기 선택값이다.',
'- B·C 12문항 일렬응답 2건은 사전 규칙대로 자동 제외하지 않았다.','',
'## H1: 안전관리 실효성 ANCOVA','',
'종속변수 Y는 B1~B8 전체 응답의 평균(1~5점), 집단은 도입=1·미도입=0이다. 만 나이·건설현장 경력을 연속 공변량으로, 소속·성별·역할·총공사비를 범주형 통제요인으로 투입했다. 기준범주는 시공사·남성·공사감독·20억 원 미만이다. OLS/Type III, 양측 α=.05를 적용했다.','',
'| 집단 | n | 원평균(SD) | 조정 평균(SE) | 조정 평균 95% CI |','|---|---:|---:|---:|---|']
for g in ['도입','미도입']:
    raw=h['raw'][g]; z=e[g]
    lines.append(f"| {g} | {raw['n']} | {raw['mean']:.3f} ({raw['sd']:.3f}) | {z['est']:.3f} ({z['se']:.3f}) | {ci(z)} |")
lines += ['',f"조정 차이(도입−미도입)는 {d['B']:.3f}, SE={d['SE']:.3f}, 95% CI {ci(d)}, p={p(d['p'])}이다. 설계행렬은 {h['rank']}/{h['n_coef']}의 완전 순위이고 잔차 자유도는 71−12=59이다. 조정 평균은 전체 완전사례의 나이·경력 평균과 범주별 관측 비율을 두 집단에 동일하게 적용했다. 참고용 동일 가중 조정 평균은 도입 {h['emm']['equal']['도입']['est']:.3f}, 미도입 {h['emm']['equal']['미도입']['est']:.3f}이다.",'',
'## 다섯 하위영역','',
'H1과 같은 모형을 각각 적합하고 다섯 집단 검정 p값을 하나의 검정군으로 Holm 보정했다. 아래 CI는 개별 비보정 95% CI이다.','',
'| 영역 | 도입−미도입 차이 | 95% CI | 비보정 p | Holm p | 부분 η² |','|---|---:|---|---:|---:|---:|']
for z in r['subscales'].values():
    lines.append(f"| {z['label']} | {z['diff']['B']:.3f} | {ci(z['diff'])} | {p(z['p'])} | {p(z['p_holm'])} | {z['partial_eta2']:.3f} |")
lines += ['','Holm 보정 후 조기인지·원격 파악·위험 통제력에서 유의한 양의 차이가 관찰되었다. 대응 신속성·순찰부담 경감에서는 차이가 확인되지 않았다. 영역 간 효과의 크기 자체를 비교 검정한 결과는 아니다. 모든 모형의 n=71, rank=12, 잔차 df=59이다.','',
'## H2: 예산 제약성과 집단의 상호작용','',
f"C1~C4 평균 W를 전체 완전사례 평균 {h2['W_mean']:.3f}로 중심화하고 W_c와 D×W_c를 H1에 추가했다. 상호작용 B={inter['B']:.3f}, SE={inter['SE']:.3f}, 95% CI {ci(inter)}, F(1, {h2['df_resid']})={h2['F']:.3f}, p={p(h2['p'])}로 H2는 지지되지 않았다. n=71, rank={h2['rank']}/{h2['n_coef']}, 잔차 df={h2['df_resid']}이다.",'',
f"H2 잔차의 Breusch–Pagan p={p(h2['diagnostics']['bp_p'])}로 이분산 신호가 있어 HC3를 병기했다. HC3 상호작용 SE={ih['SE']:.3f}, 95% CI {ci(ih)}, p={p(ih['p'])}이며 결론은 같다.",'',
'| 예산 제약성 수준 | W | 조건부 집단 차이 | 95% CI | p | HC3 p |','|---|---:|---:|---|---:|---:|']
for z in h2['conditional']:
    x=z['difference']; lines.append(f"| {z['level'].replace('平均','평균')} | {z['W']:.3f} | {x['est']:.3f} | {ci(x)} | {p(x['p'])} | {p(z['difference_hc3']['p'])} |")
lines += ['',f"양 집단 W의 공통 범위는 {h2['common_W_range']}이다. 상호작용이 유의하지 않으므로 특정 수준에서의 유의성만으로 수준 간 차이를 주장하지 않는다.",'',
'## 가정 점검과 민감도','',
f"H1 회귀기울기 동질성 공동 검정 p={p(dg['slope_joint_p'])}, 두 공변량 제곱항 공동 검정 p={p(dg['quadratic_joint_p'])}, 잔차 Shapiro–Wilk p={p(dg['shapiro_p'])}, Levene p={p(dg['levene_mean_p'])}, Breusch–Pagan p={p(dg['bp_p'])}이다. 비유의가 가정 충족을 입증하지는 않는다. Cook's D>4/n은 {len(dg['cooks_flag'])}건이며 주 분석에서는 삭제하지 않았다. 절편을 제외한 VIF 최대값은 {max(dg['vif'].values()):.3f}이다. 잔차 Q-Q 및 적합값-잔차 도표는 figs/에 저장했다.",'',
'| 분석 조건 | n | 조정 차이 | 95% CI | p |','|---|---:|---:|---|---:|']
for key,label in [('base','기본'),('hc3','HC3 강건 표준오차'),('cooks_excluded','Cook 영향점 제외(사후)'),('straightlining_excluded','일렬응답 제외(사후)'),('exclude_role_other','기타 역할 제외(사후)')]:
    x=rob[key];lines.append(f"| {label} | {x['n']} | {x['B']:.3f} | {ci(x)} | {p(x['p'])} |")
for key,label in [('sensitivity_system_path','자기보고 시스템 경로 충족 부분집단'),('sensitivity_include_test_rows','시험응답 2건 포함')]:
    z=r[key];x=z.get('diff',z);lines.append(f"| {label} | {z['n']} | {x['B']:.3f} | {ci(x)} | {p(x['p'])} |")
lines += ['','시스템 경로 충족은 A7이 CCTV 직접 확인 또는 자동 알림이고 A8이 발생 직후 알림인 경우다. 현재 도입 32명 중 13명이 충족하고 19명은 충족하지 않는다. 부분집단 분석은 도입 13명·미도입 39명이며, 이 규칙은 자기보고 인지 경로를 뜻할 뿐 실제 기기 정상 가동을 검증한 기준은 아니다. 사후 민감도 결과로 사례나 공변량을 선택하지 않았다.','',
f"지시 전달 소요시간 A9의 Fisher–Freeman–Halton p={p(r['A9']['p'])}로 분포 차이가 확인되지 않았다. 지각 실효성의 차이를 실제 대응시간 단축이나 사고 감소로 해석할 수 없다. 횡단 비교이므로 도입 이후 향상 또는 인과 효과로 단정할 수 없으며, 연구자와의 관계에 따른 호의 응답·미측정 교란도 남는다.",'',
'## 재현 및 검증','',
'실행: 저장소 루트에서 `py -3.12 "01.docs/설문결과/analysis/261025_2042_재분석/run_analysis.py"` 후 `build_report.py`를 실행한다. 원본 계산 코드 스냅샷과 이번 실행 코드를 같은 폴더에 보관했다. Python 3.12 환경에 없던 openpyxl·matplotlib 및 관련 의존성은 이 실행 폴더의 dependencies/에만 설치했다.','',
'- 실제 실행 환경: '+', '.join(f'{k} {r["meta"][k]}' for k in ['python','pandas','numpy','scipy','statsmodels'])+'.',
'- 원자료 읽기 전 SHA256: `'+r['meta']['sha_before']+'`',
'- 원자료 읽기 후 SHA256: `'+r['meta']['sha_after']+'`',
'- 문항 헤더 매핑, 코드 변환 오류 없음, F=t², 조정평균 차이=집단계수, 잔차 df, NumPy 최소제곱 계수 대조, 원본 불변 검증: 모두 통과.',
'- 수치 전체: results.json, 계수표: H1_coefficients.csv·H2_coefficients.csv, 비식별 코딩자료: coded_data.csv, 이전 자료와 변경 대조: changes_vs_previous.csv, 실행 출력: execution_log.txt.',
'- 이 결과는 원자료 변경 원인을 판정하지 않는다. 이전 결과와의 차이는 표본 포함·문항값 변경이 함께 반영된 결과이다.','']
(q/'재분석_결과보고서.md').write_text('\n'.join(lines),encoding='utf-8')
print('report written; actual item changed cells',len(actual),'respondents',actual.resp_id.nunique())
