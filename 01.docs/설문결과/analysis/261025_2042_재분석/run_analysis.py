"""Current workbook reanalysis; snapshots preserve calculation implementation."""
import sys, json, hashlib, importlib.util, re
from numbers import Number
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import scipy, statsmodels
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.anova import anova_lm
import statsmodels.formula.api as smf

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT / 'dependencies'))
ROOT = next(p for p in OUT.parents if (p / 'tools/survey_analysis').exists())
sys.path.insert(0, str(ROOT))
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, OUT / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m
c = module('coding_snapshot', 'coding_snapshot.py')
a = module('analyze_snapshot', 'analyze_snapshot.py')
a.cd = c
a.FIG_DIR = OUT / 'figs'
a.FIG_DIR.mkdir(exist_ok=True)
a.plt.rcParams['font.family'] = 'Malgun Gothic'
a.plt.rcParams['axes.unicode_minus'] = False
src = ROOT / c.SRC_REL
sha_before = hashlib.sha256(src.read_bytes()).hexdigest()
# Same identified test rows, but timestamps in this workbook differ from the old export.
c.EXCLUSIONS = {
    2: ('2026-10-17 08:14:23', '테스트', '기존 시험응답 행: 현장명 테스트'),
    3: ('2026-10-17 08:36:40', '없음', '기존 연구자 시험응답 행: 현장명 없음'),
}
r = c.build(src)
assert not r.cross_fill_violations and not r.likert_failures and not r.category_failures
for item, col in c.ADOPT_COLS.items():
    assert str(r.headers[col]).startswith(item[0] + '-' + item[1:] + ')')
for item, col in c.NONADOPT_COLS.items():
    assert str(r.headers[col]).startswith(item[0] + '-' + item[1:] + ')')
df = r.analysis
df.to_csv(OUT / 'coded_data.csv', index=False, encoding='utf-8-sig')
inc = df.loc[df.include == 1].copy()
inc['D'] = inc.group.astype(int)
old = pd.read_csv(OUT.parent / 'coded_data.csv')
changes = []
for col in c.ANALYSIS_COLUMNS:
    if col in ('include', 'exclude_reason'): continue
    for i in range(min(len(old), len(df))):
        x,y = old.iloc[i][col],df.iloc[i][col]
        if pd.isna(x) and pd.isna(y): continue
        if str(x) != str(y) and not (isinstance(x,Number) and isinstance(y,Number) and x==y):
            changes.append({'resp_id':df.iloc[i].resp_id,'variable':col,'old':None if pd.isna(x) else x,'current':None if pd.isna(y) else y})
pd.DataFrame(changes).to_csv(OUT / 'changes_vs_previous.csv', index=False, encoding='utf-8-sig')
H1,m,d = a.ancova(inc,'Y_total','안전관리 실효성 전체')
assert H1['full_rank']
diag = a.diagnostics(m,d,'Y_total','H1',plots=True)
slopes = smf.ols('Y_total ~ '+a.RHS+' + D:A3_age + D:A4_exp',data=d).fit()
sf = slopes.f_test('D:A3_age=0, D:A4_exp=0')
diag['slope_joint_F'] = float(sf.fvalue)
diag['slope_joint_p'] = float(sf.pvalue)
diag['slope_individual_p'] = {k:float(slopes.pvalues[k]) for k in ['D:A3_age','D:A4_exp']}
quad = smf.ols('Y_total ~ '+a.RHS+' + I(A3_age**2) + I(A4_exp**2)', data=d).fit()
diag['quadratic_joint_p'] = float(quad.f_test('I(A3_age ** 2)=0, I(A4_exp ** 2)=0').pvalue)
diag['vif']={name:float(a.variance_inflation_factor(m.model.exog,i)) for i,name in enumerate(m.model.exog_names) if name!='Intercept'}
rob = a.h1_robustness(d,m,diag)
subs={}
for dv,label in a.SUBSCALES.items():
    z,mm,dd=a.ancova(inc,dv,label)
    assert z['full_rank']
    z['diagnostics']=a.diagnostics(mm,dd,dv,label)
    z['hc3']=a.group_coef(smf.ols(mm.model.formula,data=dd).fit(cov_type='HC3',use_t=True),dd,dd.resp_id)
    subs[dv]=z
for z,p in zip(subs.values(),multipletests([x['p'] for x in subs.values()],method='holm')[1]): z['p_holm']=float(p)
d2=inc.dropna(subset=['Y_total','W']+a.MODEL_VARS).copy()
wmean=float(d2.W.mean()); wsd=float(d2.W.std(ddof=1))
d2['W_c']=d2.W-wmean
m2,form,rank,ncoef=a.fit_model(d2,'Y_total',' + W_c + D:W_c')
assert rank==ncoef
av=anova_lm(m2,typ=3)
hc=smf.ols(form,data=d2).fit(cov_type='HC3',use_t=True)
H2={'formula':form,'n':len(d2),'rank':rank,'n_coef':ncoef,'df_resid':int(m2.df_resid),'W_mean':wmean,'W_sd':wsd,'coefs':a.coef_table(m2),'hc3_coefs':a.coef_table(hc),'F':float(av.loc['D:W_c','F']),'p':float(av.loc['D:W_c','PR(>F)']),'diagnostics':a.diagnostics(m2,d2,'Y_total','H2')}
lo=max(d2.loc[d2.D==g,'W'].min() for g in (0,1)); hi=min(d2.loc[d2.D==g,'W'].max() for g in (0,1))
H2['common_W_range']=[lo,hi]; H2['conditional']=[]
for lab,w in [('平均−1SD',-wsd),('平均',0),('平均+1SD',wsd)]:
    if lo<=wmean+w<=hi:
        l1=a.lvector(m2,d2,1,'proportional',w); l0=a.lvector(m2,d2,0,'proportional',w)
        H2['conditional'].append({'level':lab,'W':wmean+w,'adopt':a.lin_est(m2,l1),'nonadopt':a.lin_est(m2,l0),'difference':a.lin_est(m2,l1-l0),'difference_hc3':a.lin_est(hc,l1-l0)})
ds=inc.loc[(inc.D==0)|(inc.sys_path==1)].dropna(subset=['Y_total']+a.MODEL_VARS).copy()
ms=a.h1_subset_fit(ds)
assert np.linalg.matrix_rank(ms.model.exog)==ms.model.exog.shape[1]
sens=a.group_coef(ms,ds,d.resp_id)
sens['rank']=int(np.linalg.matrix_rank(ms.model.exog))
allrows=df.copy(); allrows['D']=allrows.group.astype(int)
all_result,all_model,all_data=a.ancova(allrows,'Y_total','시험응답 2건 포함 민감도')
table=pd.crosstab(inc.D,inc.A9_lag).reindex(index=[1,0],columns=[1,2,3,4],fill_value=0)
a9={'table':table.values.tolist(),'p':a.fisher_exact_2xk(table.values)[0]}
rr=r.raw.loc[r.raw.include==1]
audit={'rows':len(df),'included':len(inc),'groups':inc.D.value_counts().to_dict(),'excluded_test_ids':df.loc[df.include==0,'resp_id'].tolist(),'H1_excluded_missing':inc.loc[~inc.resp_id.isin(d.resp_id),'resp_id'].tolist(),'missing_by_model_variable':inc[a.MODEL_VARS+['Y_total','W']].isna().sum().to_dict(),'site_nonmissing':int(rr.site.notna().sum()),'site_unique_nonmissing':int(rr.site.nunique()),'name_nonmissing':int(rr.name.notna().sum()),'name_unique_nonmissing':int(rr.name.nunique()),'nonmissing_duplicate_site_ids':rr.loc[rr.site.notna() & rr.site.duplicated(False),'resp_id'].tolist(),'nonmissing_duplicate_name_ids':rr.loc[rr.name.notna() & rr.name.duplicated(False),'resp_id'].tolist(),'change_cells_including_derived':len(changes),'changed_response_ids':sorted({x['resp_id'] for x in changes}),'sys_path_adopt':inc.loc[inc.D==1,'sys_path'].value_counts().to_dict(),'B_C_straightline_ids':inc.loc[inc[c.B_ITEMS+c.C_ITEMS].nunique(axis=1)==1,'resp_id'].tolist()}
checks={'headers_mapped':True,'no_coding_failures':True,'H1_F_t2':H1['check_F_equals_t2'],'H1_mean_diff':H1['check_emm_diff_equals_B'],'all_subscale_F_t2':all(z['check_F_equals_t2'] for z in subs.values()),'residual_df':len(d)-H1['rank']==H1['df_resid'],'H2_F_t2':np.isclose(H2['F'],m2.tvalues['D:W_c']**2),'source_unchanged':sha_before==hashlib.sha256(src.read_bytes()).hexdigest()}
# Independent NumPy least-squares crosscheck on the fitted design matrix.
b=np.linalg.lstsq(m.model.exog,m.model.endog,rcond=None)[0]
checks['numpy_lstsq_coefficients']=bool(np.allclose(b,m.params.values,atol=1e-10))
assert all(checks.values()), checks
R={'meta':{'run':datetime.now().isoformat(),'source':str(c.SRC_REL),'sha_before':sha_before,'sha_after':hashlib.sha256(src.read_bytes()).hexdigest(),'previous_source_sha':c.SRC_SHA256,'python':sys.version.split()[0],'pandas':pd.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'audit':audit,'H1':H1,'H1_diagnostics':diag,'H1_robustness':rob,'subscales':subs,'H2':H2,'sensitivity_system_path':sens,'sensitivity_include_test_rows':all_result,'A9':a9,'checks':checks}
(OUT/'results.json').write_text(json.dumps(a.jnum(R),ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame(H1['coefs']).to_csv(OUT/'H1_coefficients.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(H2['coefs']).to_csv(OUT/'H2_coefficients.csv',index=False,encoding='utf-8-sig')
print(json.dumps(a.jnum({'audit':audit,'H1':H1['diff'],'H1_emm':H1['emm']['proportional'],'H1_p':H1['p'],'H1_eta2':H1['partial_eta2'],'H1_diag':diag,'H1_hc3':rob['hc3'],'subscales':{k:{'diff':v['diff'],'p_holm':v['p_holm']} for k,v in subs.items()},'H2':H2,'sensitivity':sens,'A9':a9,'checks':checks}),ensure_ascii=False,indent=2))
