from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('fig', ROOT/'01.docs/figures/research/generate_research_figures.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=HERE
f=m.Figure('flow_current',1790,'연구의 흐름도: 현행 혼합모형 설계')
steps=[(40,230,'제1·2장  연구 배경과 이론적 근거',['현장 안전관리 문제와 선행연구 검토','개인의 현재 지각 실효성 비교 필요성']),
(325,230,'제3장  시스템 개발 및 조건부 성능 평가',['YOLO 1차 후보에 대한 LLM 2차 필터 평가','오경보 감소와 실제 위험 추가 차단을 함께 보고']),
(610,280,'제4장  도입·미도입 현장 비교 설계',['설치·정상 운용 기준 집단 구분과 공통 척도 검토','60현장·120명 모집 목표 / 사후 설문 1회','집단별 공통 안내 · 채점 및 결측 처리 계획']),
(945,390,'제5장  실증분석 결과',['측정도구 · 사전 특성 분포 · 모형 가정 점검','H1: 현장 임의절편 선형혼합모형의 Y 비교','다섯 영역 보조 비교: Holm 보정','H2: 집단 × 사후 개인 지각 예산 제약성(W)','추정치 · 신뢰구간 · 군집 분산과 적합 상태 보고']),
(1390,215,'제6장  결론',['결과와 의의 · 해석의 한계 · 후속 연구','전후 변화·인과 효과·정책 우선배치 단정 제한'])]
for i,(y,h,title,lines) in enumerate(steps):
 f.box(45,y,1410,h);f.box(45,y,1410,75,m.PALE);f.text(78,y+51,title,40,True,color=m.NAVY)
 for j,t in enumerate(lines):f.text(80,y+125+j*52,t,36)
 if i+1<len(steps):f.line([(750,y+h),(750,steps[i+1][0])],arrow=True)
f.text(750,1680,'횡단적 두 집단 비교 · 개인 응답의 현장 군집 반영',36,center=True)
f.text(750,1735,'모집 목표의 검정력과 실제 분석 결과는 별도 확인',36,center=True);f.save()
f=m.Figure('model_current',1630,'연구 모형: 현장 임의절편 선형혼합모형')
f.text(50,65,'H1  주 분석 · 현장 임의절편 선형혼합모형',42,True,color=m.NAVY)
f.text(50,122,'범주형 특성 조정 후 개인 지각 Y의 집단 간 평균 비교',36)
for y,title,line in [(180,'도입 현장 (D=1)','설치 및 정상 운용 확인'),(420,'미도입 현장 (D=0)','미설치·미운용 확인')]:
 f.box(50,y,530,190,m.PALE);f.text(315,y+62,title,38,True,center=True);f.text(315,y+122,line,34,center=True)
f.line([(580,275),(650,275),(650,515),(580,515)]);f.line([(650,395),(825,395)],arrow=True);f.text(736,350,'비교',36,True,center=True)
f.box(825,180,625,430);f.text(1137,245,'안전관리 실효성(Y)',40,True,center=True)
for y,t in [(310,'현재 업무 수행 수준의 개인 지각'),(375,'B 8문항 동일 가중 평균'),(440,'도입-미도입 조정 평균 차이'),(505,'추정치와 95% 신뢰구간')]:f.text(1137,y,t,32,center=True)
f.text(1137,568,'다섯 영역 비교는 Holm 보정',32,color=m.GRAY,center=True)
f.text(50,670,'정상 운용 무알림 현장도 도입에 포함 · 알림 경험은 별도 기록',34)
f.box(50,720,1400,200,m.PALE);f.text(85,775,'여섯 범주형 특성 조정 + 현장 ID 임의절편',38,True)
f.text(85,832,'소속 · 성별 · 연령 · 경력 · 직위 · 현장 공사금액 규모',35)
f.text(85,888,'같은 현장 응답자의 상관 반영 / 미측정 교란 제거를 보장하지 않음',32)
f.text(50,990,'H2  탐색적 보조 분석',42,True,color=m.NAVY);f.box(50,1035,1400,365,dash=True)
f.text(90,1097,'조사 시점 개인 지각 예산 제약성(W)을 평균중심화',36,True)
f.text(90,1150,'같은 혼합모형에 집단·W 주효과 및 집단 × W 포함',35)
f.box(90,1195,690,95,m.PALE,dash=True);f.text(435,1256,'집단 × 개인 지각 W',38,True,center=True)
f.line([(780,1242),(1000,1242)],dash=True,arrow=True);f.text(1220,1256,'안전관리 실효성(Y)',34,True,center=True)
f.text(90,1353,'양 집단 공통 관측범위 내 조건부 차이 · 부호 있는 B와 신뢰구간',32)
f.text(50,1465,'분석 관계를 나타낸 도식이며 도입의 인과 효과를 입증하지 않는다.',33)
f.text(50,1530,'사후 W는 객관 예산이나 정책 우선배치 기준으로 해석하지 않는다.',33)
f.save()
print('Rendered two diagrams using editable native drawing primitives.')
