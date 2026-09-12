from pathlib import Path
import json, shutil, hashlib, zipfile, fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
P=Path(__file__).resolve().parent; D=P/'source-data'; A=P/'assets'; A.mkdir(exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':9,'svg.fonttype':'none','axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white'})
navy='#18354f'; gray='#888888'
rows=[('건설업',328),('제조업',187),('기타의 사업',145),('운수·창고·통신업',138),('임업',11),('농업',9),('광업',4),('전기·가스·수도업',2),('어업',2),('금융 및 보험업',1)]
assert sum(v for _,v in rows)==827
trend=[(2020,458),(2021,417),(2022,402),(2023,356),(2024,328)]
(D/'chart_data.json').write_text(json.dumps({'series':'산재보상 승인자료 기준 업무상사고 사망자','distribution_2024':[{'industry':k,'fatalities':v,'percent':round(v/827*100,2)} for k,v in rows],'construction_2020_2024':[{'year':y,'fatalities':v} for y,v in trend]},ensure_ascii=False,indent=2),encoding='utf-8')
def save(fig,name):
 fig.savefig(A/(name+'.svg'),facecolor='white');fig.savefig(A/(name+'.png'),dpi=300,facecolor='white');plt.close(fig)
fig,ax=plt.subplots(figsize=(150/25.4,112/25.4));fig.subplots_adjust(left=.31,right=.98,bottom=.17,top=.89)
ax.barh(range(10),[v for _,v in rows],color=[navy]+[gray]*9,height=.65)
ax.set_yticks(range(10),[k for k,_ in rows]);ax.invert_yaxis();ax.set_xlim(0,445);ax.set_xticks([0,100,200,300,400]);ax.set_xlabel('업무상사고 사망자 수(명)',labelpad=5)
for i,(_,v) in enumerate(rows):ax.text(v+6,i,f'{v:,}명 ({v/827*100:.2f}%)',va='center',fontsize=8.5,color=navy if i==0 else '#222222')
ax.set_title('2024년 산업별 업무상사고 사망자 분포',fontsize=11,pad=12)
ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#dddddd',lw=.5);ax.set_axisbelow(True)
fig.text(.03,.045,'자료: 고용노동부, 『2024 산업재해현황분석』, 22쪽.\n주: 산재보상 승인자료 기준. 전 산업 합계 827명.',fontsize=8)
save(fig,'fig_1_1_industry_fatalities_2024')
fig,ax=plt.subplots(figsize=(150/25.4,105/25.4));fig.subplots_adjust(left=.14,right=.95,bottom=.24,top=.77)
y,v=zip(*trend);ax.plot(y,v,color=navy,marker='o',lw=2,ms=6);ax.set_ylim(0,550);ax.set_xlim(2019.7,2024.3);ax.set_xticks(y);ax.set_ylabel('업무상사고 사망자 수(명)');ax.set_yticks(range(0,501,100))
for xx,vv in trend:ax.annotate(f'{vv}명',(xx,vv),xytext=(0,10),textcoords='offset points',ha='center',fontsize=10,color=navy)
for xx in [2022,2024]:ax.axvline(xx,color='#999999',ls='--',lw=.8,zorder=0)
fig.text(.5,.94,'건설업 업무상사고 사망자 추이(2020~2024년)',ha='center',fontsize=11)
fig.text(.54,.825,'2022.1.27.\n중대재해처벌법 시행',ha='center',fontsize=8)
fig.text(.86,.825,'2024.1.27.\n유예 대상 확대 적용',ha='center',fontsize=8)
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#dddddd',lw=.5);ax.set_axisbelow(True)
fig.text(.03,.055,'자료: 고용노동부, 2021~2023년 산업재해 현황;\n        『2024 산업재해현황분석』, 22쪽.\n주: 산재보상 승인연도 기준. 시행 시점 표시는 인과효과를 뜻하지 않음.',fontsize=8)
save(fig,'fig_1_2_construction_fatalities_2020_2024')
shutil.copyfile(D/'viewer_candidate.png',A/'fig_3_4_viewer_original.png')
root=P.parents[2];pdf=root/'02.reference/30. 2024 산업재해 현황분석(홈페이지).pdf';doc=fitz.open(pdf)
for idx in [26,27,660]:
 (D/f'moel_2024_pdfpage_{idx+1}.txt').write_text(doc[idx].get_text(),encoding='utf-8')
 if idx==27:doc[idx].get_pixmap(dpi=120).save(D/'moel_2024_pdfpage_28.png')
print('Generated charts and original screenshot copy')
