"""Post-hoc exploration of construction-cost categories, not the H2 budget scale."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import build_design_matrices
from scipy import stats

q=Path(__file__).resolve().parent
df=pd.read_csv(q/'coded_data.csv')
d=df.loc[df.include==1].copy()
d['D']=d.group.astype(int)
labels={1:'20억 원 미만',2:'20억~50억 원 미만',3:'50억~120억 원 미만',4:'120억 원 이상'}
controls='A3_age + A4_exp + C(A1_affil, Treatment(1)) + C(A2_sex, Treatment(1)) + C(A5_role, Treatment(1))'
base=smf.ols('Y_total ~ D + C(A6_cost, Treatment(1)) + '+controls,data=d).fit()
m=smf.ols('Y_total ~ D * C(A6_cost, Treatment(1)) + '+controls,data=d).fit()
rank=int(np.linalg.matrix_rank(m.model.exog))
assert rank==m.model.exog.shape[1], 'Rank-deficient interaction model'
assert int(m.nobs)==71
hc=m.get_robustcov_results(cov_type='HC3',use_t=True)
names=m.model.exog_names
terms=[x for x in names if x.startswith('D:C(A6_cost')]
R=np.zeros((len(terms),len(names)))
for i,t in enumerate(terms):R[i,names.index(t)]=1
ft=m.f_test(R); fth=hc.f_test(R)
joint={'F':float(ft.fvalue),'p':float(ft.pvalue),'df1':int(ft.df_num),'df2':int(ft.df_denom),'HC3_F':float(fth.fvalue),'HC3_p':float(fth.pvalue)}
checks={'joint_matches_nested_F':bool(np.isclose(joint['F'],m.compare_f_test(base)[0])),'full_rank':rank==len(names),'n71':int(m.nobs)==71}
desc=[]
for cost in range(1,5):
    for g in [0,1]:
        z=d.loc[(d.A6_cost==cost)&(d.D==g)]
        desc.append({'cost':cost,'label':labels[cost],'group':g,'n':len(z),'Y_mean':float(z.Y_total.mean()),'Y_sd':float(z.Y_total.std(ddof=1)),'W_mean':float(z.W.mean()),'W_sd':float(z.W.std(ddof=1))})
costW=[{'cost':cost,'label':labels[cost],'n':len(z),'W_mean':float(z.W.mean()),'W_sd':float(z.W.std(ddof=1))} for cost,z in d.groupby('A6_cost')]
def vec(cost,g):
    L=m.model.exog.mean(axis=0).copy()
    for i,name in enumerate(names):
        if name=='D':L[i]=g
        elif 'C(A6_cost' in name:
            level=float(name.split('[T.')[1].rstrip(']'))
            L[i]=float(cost==level)*(g if name.startswith('D:') else 1)
    return L
def est(L,model):
    b=float(L@np.asarray(model.params)); se=float(np.sqrt(L@np.asarray(model.cov_params())@L));crit=stats.t.ppf(.975,model.df_resid)
    return {'B':b,'SE':se,'lo':b-crit*se,'hi':b+crit*se,'p':float(2*stats.t.sf(abs(b/se),model.df_resid))}
contrasts=[]
for cost in range(1,5):
    v1,v0=vec(cost,1),vec(cost,0)
    contrasts.append({'cost':cost,'label':labels[cost],'adopt_adjusted':est(v1,m),'nonadopt_adjusted':est(v0,m),'difference':est(v1-v0,m),'difference_HC3':est(v1-v0,hc)})
assert all(checks.values())
result={'note':'사후 탐색 분석. H2 예산제약성 W를 총공사비로 대체하는 가설검증이 아님.','formula':m.model.formula,'n':int(m.nobs),'rank':rank,'coefficients':len(names),'residual_df':int(m.df_resid),'descriptive_by_cost_group':desc,'W_by_cost':costW,'interaction_joint':joint,'adjusted_contrasts':contrasts,'checks':checks}
(q/'cost_exploration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
def ci(z):return f"[{z['lo']:.3f}, {z['hi']:.3f}]"
lines=['# 총공사비 구간별 추가 탐색 분석','',
'현재 자료에서는 총공사비가 적을수록 시스템 도입 집단의 평가가 더 긍정적이라고 결론내릴 근거가 없다. 도입 집단 Y 평균은 공사비 구간 순서대로 4.063, 3.979, 4.267, 3.972로 단조로운 추세가 아니다. 공사비별 도입−미도입 조정 차이가 다르다는 근거도 확인되지 않았다(상호작용 p=.955, HC3 p=.983). 다만 작은 표본과 넓은 신뢰구간 때문에 차이가 없다고 입증한 결과는 아니다.','',
'이 분석은 기존 결과를 확인한 뒤 수행한 사후 탐색이다. 총공사비는 객관적인 현장 규모 구간이고, H2의 예산 제약성 W는 응답자가 지각한 안전장비 도입 예산의 부족 정도(C1~C4 평균)다. 두 변수는 같은 뜻이 아니다.','',
'| 총공사비 | 집단 | n | 안전관리 실효성 Y 평균(SD) | 예산 제약성 W 평균 |','|---|---|---:|---:|---:|']
for z in desc:lines.append(f"| {z['label']} | {'도입' if z['group'] else '미도입'} | {z['n']} | {z['Y_mean']:.3f} ({z['Y_sd']:.3f}) | {z['W_mean']:.3f} |")
lines+=['','## 공사비별 도입−미도입 차이','',
'기존 H1의 연속 공변량(나이·경력) 및 범주형 통제요인(소속·성별·역할)을 유지하고 집단×총공사비 4범주 상호작용을 추가했다. 공사비를 1~4의 연속 변수로 취급하지 않았다. 조정 평균은 동일한 전체 표본 공변량 분포에 표준화한 값이며, 희소 집단에서는 외삽에 의존할 수 있다.','',
f"상호작용 공동검정 F({joint['df1']}, {joint['df2']})={joint['F']:.3f}, p={joint['p']:.3f}; HC3 강건 검정 F={joint['HC3_F']:.3f}, p={joint['HC3_p']:.3f}. n=71, 설계행렬 rank={rank}/{len(names)}, 잔차 df={int(m.df_resid)}.",'',
'| 총공사비 | 도입 조정평균 | 미도입 조정평균 | 조정 차이 | 95% CI | p | HC3 95% CI | HC3 p |','|---|---:|---:|---:|---|---:|---|---:|']
for z in contrasts:
    e=z['difference'];hh=z['difference_HC3']
    lines.append(f"| {z['label']} | {z['adopt_adjusted']['B']:.3f} | {z['nonadopt_adjusted']['B']:.3f} | {e['B']:.3f} | {ci(e)} | {e['p']:.3f} | {ci(hh)} | {hh['p']:.3f} |")
lines+=['','구간별 CI·p는 다중검정 미보정 탐색값이다. 어느 한 구간에서만 유의하더라도 구간 간 차이가 유의하다는 뜻은 아니다. 판단은 상호작용 공동검정을 우선한다.','',
'## 공사비와 예산 제약성의 기술통계','',
'| 총공사비 | n | W 평균(SD) |','|---|---:|---:|']
for z in costW:lines.append(f"| {z['label']} | {z['n']} | {z['W_mean']:.3f} ({z['W_sd']:.3f}) |")
lines+=['','검증: 완전 순위, n=71, 공동 F와 중첩모형 비교 F 일치 확인. 본문·HWPX·기존 결과는 수정하지 않았다.','']
lines+=['20억 원 미만은 예산 제약성 평균이 가장 높고 도입−미도입 조정 차이도 점추정상 가장 크지만, 도입 2명·미도입 5명뿐이다. 해당 차이의 일반 95% CI는 [-0.497, 2.018], HC3 CI는 [-1.908, 3.430]으로 매우 넓어 작은 현장에서 차이가 더 크다는 증거로 사용할 수 없다. 예산 제약성 전체 평균도 4.036→3.500→3.219→3.430으로 일관된 감소 추세는 아니다.','']
(q/'공사비별_추가탐색_결과.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
