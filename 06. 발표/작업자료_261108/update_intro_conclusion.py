from pathlib import Path
from copy import deepcopy
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from zoneinfo import ZoneInfo
import json,datetime,hashlib,re
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1436_윤혁_석사학위논문_심의발표_장구분추가.pptx';p=Presentation(src);digest=hashlib.sha256(src.read_bytes()).hexdigest()
def snap(s):
 a=[]
 for x in s.shapes:
  if x.shape_id==13:continue
  if x.has_text_frame:a.append(('text',x.shape_id,x.text))
  if x.has_table:a.append(('table',x.shape_id,[[c.text for c in row.cells] for row in x.table.rows]))
  if x.shape_type==13:a.append(('image',x.shape_id,hashlib.sha256(x.image.blob).hexdigest()))
 return a
before=[snap(s) for s in p.slides];oldnotes=[s.notes_slide.notes_text_frame.text for s in p.slides]
def obj(s,id):return next(x for x in s.shapes if x.shape_id==id)
def put(x,t):
 tf=x.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=t
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=t
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def fs(x,n):
 for q in x.text_frame.paragraphs:
  for rr in q.runs:rr.font.size=Pt(n)
def clear(s):
 for x in list(s.shapes):
  if x.shape_id not in [2,10,11,12,13]:x._element.getparent().remove(x._element)
def tx(s,x,y,w,h,t,size=20,color='172537',bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=True
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=line;q.space_after=Pt(5)
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return sh
def rect(s,x,y,w,h,color):
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background()
def takeaway(s,t):rect(s,.56,6.18,8.88,.58,'FBF3E7');tx(s,.73,6.27,8.5,.4,t,15,'A9651B',True)
def clone():
 tem=p.slides[3];s=p.slides.add_slide(tem.slide_layout)
 for x in list(s.shapes):x._element.getparent().remove(x._element)
 for x in tem.shapes:
  if x.shape_id in [2,10,11,12,13]:s.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
 return s
# 2025 national status and 2030 target, separately labelled from construction share.
s=p.slides[3];clear(s);put(obj(s,11),'건설현장의 위험을 제때 파악하고 대응해야 한다');fs(obj(s,11),25)
put(obj(s,12),'논문 제1장 제1절 · 대한민국 정부(2025), 고용노동부(2026)')
rect(s,.65,2.05,4.2,3.7,'EEF3F8');tx(s,.85,2.25,3.8,.55,'전 산업 사고사망만인율',22,'123B78',True)
tx(s,.85,3.15,3.8,.55,'2025년 현황',18,'68788B');tx(s,.85,3.65,3.8,.75,'0.38명',34,'123B78',True)
tx(s,.85,4.65,3.8,.8,'2030년 정부 목표  0.29명\n단위: 근로자 1만 명당',17)
rect(s,5.15,2.05,4.2,3.7,'EEF3F8');tx(s,5.35,2.25,3.8,.55,'사고사망자 중 건설업 비중',21,'123B78',True)
tx(s,5.35,3.15,3.8,.85,'41.4%',38,'123B78',True);tx(s,5.35,4.35,3.8,.7,'건설업 361명 / 전 산업 872명',18)
tx(s,5.35,5.1,3.8,.4,'2025년 유족급여 승인 기준',16,'68788B')
takeaway(s,'현장 영상을 확인하고 위험을 판단하는 안전관제는 적시 대응을 돕는 수단')
s.notes_slide.notes_text_frame.text='논문 제1장 제1절의 통계입니다. 정부는2030년 전 산업 사고사망만인율을 근로자1만명당0.29명으로 낮추는 목표를 제시했습니다.2025년 현황은0.38명입니다. 오른쪽은 비율의 분모가 다른 통계로,2025년 유족급여 승인 기준 전 산업 사고사망자872명 중 건설업361명,41.4%입니다. 두 수치를 같은 지표로 비교하지 않습니다. 건설현장의 위험을 제때 파악하고 대응하는 것이 주요 과제이며 영상관제는 이를 도울 수 있는 수단입니다.'
# Distinct year/denominator for small-site concentration.
a=clone();put(obj(a,11),'중소규모 현장의 인력과 예산 제약을 고려해야 한다');fs(obj(a,11),25);put(obj(a,12),'논문 제1장 제1절 · 고용노동부(2025), 2024년 산재보상 승인 통계')
rect(a,.65,2.0,4.3,3.75,'EEF3F8');tx(a,.85,2.2,3.9,.75,'2024년 건설업\n업무상사고 사망자',21,'123B78',True)
tx(a,.85,3.3,3.9,.8,'71.6%',38,'123B78',True);tx(a,.85,4.3,3.9,.7,'235명 / 328명',24,'123B78',True)
tx(a,.85,5.05,3.9,.5,'공사금액 120억 원 미만 현장',17)
tx(a,5.4,2.25,3.7,.7,'기존 장비를 활용하는 개발',23,'123B78',True)
tx(a,5.4,3.35,3.7,1.9,'인력·예산 제약을 고려\n기존 CCTV와 범용 PC 활용\n추가 장비 도입 부담 완화',20)
takeaway(a,'통계 범위는 120억 원 미만 · 연구의 중소규모 정의와 구분하여 해석')
a.notes_slide.notes_text_frame.text='이 슬라이드는2024년 산재보상 승인 통계입니다. 건설업 업무상사고 사망자328명 중 공사금액120억원 미만 현장에서235명,71.6%를 차지했습니다. 앞 슬라이드의2025년 전 산업 통계와 연도 및 분모가 다릅니다. 논문은 이런 현장의 인력과 예산 제약을 고려해 기존CCTV와 범용PC를 활용하는 개발 필요성을 제시합니다. 연구의 중소규모 현장 정의는120억원 미만이고 토목공사업은150억원 미만이지만,71.6% 통계 자체의 범위는120억원 미만입니다. 이를 혼합하지 않습니다.'
# Existing surveillance and AHP evidence, with observation limits and false alarms.
b=clone();put(obj(b,11),'CCTV가 있어도 위험 인지와 대응으로 연결되지는 않는다');fs(obj(b,11),24)
put(obj(b,12),'논문 <표 1-1> · 맹인영 등(2021), Kim et al.(2022), 류정·박인선(2025)')
tx(b,.65,1.65,8.7,.6,'맹인영 등(2021)이 조사한 공공기관 10개 현장은 모두 CCTV 사용',19,'123B78',True)
rows=[['장비·플랫폼','AHP 가중치'],['통합관제 플랫폼','0.174'],['모바일 기반 관제 플랫폼','0.091'],['고정식/이동식 CCTV','0.069'],['중장비 접근경보기','0.066'],['근로자 위치 확인 센서','0.057']]
t=b.shapes.add_table(6,2,Inches(.65),Inches(2.45),Inches(4.55),Inches(2.85)).table;t.columns[0].width=Inches(3.35);t.columns[1].width=Inches(1.2)
for i,row in enumerate(rows):
 for j,value in enumerate(row):
  c=t.cell(i,j);c.text=value;c.margin_left=c.margin_right=Inches(.08);c.fill.solid();c.fill.fore_color.rgb=RGBColor.from_string('123B78' if i==0 else 'EEF3F8')
  for q in c.text_frame.paragraphs:
   for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(15);rr.font.bold=i==0;rr.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '172537')
tx(b,.65,5.43,4.6,.55,'관계자의 재해 예방 효과 상대평가\n실제 사고감소율을 측정한 값은 아님',13,'68788B')
tx(b,5.65,2.45,3.65,.5,'사람이 계속 보기 어렵다',20,'123B78',True)
tx(b,5.65,3.05,3.65,.8,'육안 확인·전담 인력 부족\n공정 확인 위주의 활용',18)
tx(b,5.65,4.22,3.65,.5,'자동 탐지도 오경보를 만든다',19,'123B78',True)
tx(b,5.65,4.83,3.65,.9,'정상 작업 장면을 위험으로 오탐\n장면 문맥을 추가로 검증할 필요',17)
takeaway(b,'관제 기능의 중요성 → 영상 확인 부담 완화 → 오경보와 실제 위험 손실을 함께 점검')
b.notes_slide.notes_text_frame.text='맹인영 등(2021)의 공공기관10개 현장은 모두 고정식 또는 이동식CCTV를 사용했습니다. 이는 해당 조사현장에 대한 사실이며 전국보급률이 아닙니다. 장비 경험자의 재해예방효과 상대평가에서 통합관제와 모바일관제 플랫폼이1·2위,CCTV가3위였습니다. 표의AHP가중치는 실제 사고감소율이 아닙니다. Kim et al.(2022)은 중소규모3개현장에서 이동형CCTV가 센서와 따로 작동해 육안확인이 필요하고 전담인력배치가 어려워 공정확인에 주로 활용되는 문제를 보고했습니다. 류정·박인선(2025)은 선정13개현장에서 고양이·옷·몸을 굽힌 작업자를 위험으로 오탐한 사례를 보고했습니다. 따라서 영상확인부담을 줄이는 동시에 오경보와 실제위험경보손실을 함께 검토해야 합니다.'
# Make the research gap explicit before retaining the original study objectives.
s=p.slides[4];put(obj(s,11),'시스템 개발과 함께, 현장의 안전관리 실효성을 확인해야 한다');fs(obj(s,11),24)
put(obj(s,14),'탐지 성능만으로 현장 업무를 알 수 없어, 두 집단을 같은 척도로 비교');fs(obj(s,14),19)
put(obj(s,12),'논문 제1장 제1절 마지막 문단 · 제2절 연구의 목적')
s.notes_slide.notes_text_frame.text='논문 서론은 탐지 정확도가 높거나 오경보가 줄었다는 사실만으로 관리자가 위험을 제때 파악하고 대응하는지 알 수 없다고 봅니다. 선행연구는 탐지 정확도·수용 의향·관제 효율 등을 다뤘지만 도입·미도입 현장에 같은 척도를 적용해 관리자 지각 실효성을 비교한 근거는 부족합니다. 그래서 기존CCTV와 범용PC를 활용한 시스템을 개발하고, 경보선별성능과 현장업무실효성을 서로 다른 자료로 확인했습니다. 다음 장에서는 이 개발과 비교의 이론적 근거를 설명하겠습니다.'
# Original slide21: remove measurement checks only and preserve covariate adjustment.
s=p.slides[20];clear(s);put(obj(s,11),'응답자와 현장 조건의 차이를 고려해 두 집단을 비교했다');fs(obj(s,11),24);put(obj(s,12),'논문 제4장 제3절·제5절 · 여섯 통제변수를 투입한 공분산분석')
for x,title,body in [(.65,'숫자로 반영한 2개 특성','만 나이\n건설현장 근무 경력'),(5.15,'범주로 반영한 4개 특성','소속 · 성별 · 역할\n총공사비 구간')]:
 rect(s,x,2.15,4.2,3.5,'EEF3F8');tx(s,x+.2,2.4,3.8,.65,title,22,'123B78',True);tx(s,x+.2,3.55,3.8,1.2,body,24)
takeaway(s,'공분산분석(ANCOVA), jamovi 2.7.41 · 측정하지 않은 집단 차이는 남을 수 있음')
s.notes_slide.notes_text_frame.text='두 집단의 특성이 서로 다를 수 있어 여섯 변수를 분석에 넣었습니다. 만 나이와 건설현장 경력은 숫자로 반영하는 공변량이고, 소속·성별·역할·총공사비 구간은 범주형 고정요인입니다. jamovi2.7.41의 공분산분석으로 이 차이를 고려한 평균을 비교했습니다. 통계적으로 조정해도 측정하지 않은 모든 차이가 사라지는 것은 아닙니다.'
# Chapter5 plain-language editing; evidence and limitations unchanged.
s=p.slides[24];updates={11:'알림 뒤에 누가 확인하고 조치할지 정해야 한다',12:'논문 제5장 결론 · 연구 결과를 바탕으로 한 현장 운영 제안',15:'시스템',16:'놓친 위험 확인',17:'잘못 걸러진 위험을\n정기적으로 살펴보기\n\n오경보와 위험 누락을\n함께 확인하기',19:'현장 운영',20:'확인 담당자 정하기',21:'알림을 받을 사람\n부재 시 대신 볼 사람\n\n확인 뒤 어떤 조치를\n했는지 기록하기',23:'다음 연구',24:'실제 조치도 확인',25:'관리자의 평가와 함께\n실제 조치 기록 수집\n사고 기록과도 연결',27:'시스템 설치에 그치지 않고, 알림 확인과 현장 조치가 이어지도록 운영'}
for sid,text in updates.items():put(obj(s,sid),text)
s.notes_slide.notes_text_frame.text='연구 결과를 현장에서 활용하려면 알림이 온 뒤의 일을 정해야 합니다. 누가 알림을 받을지, 그 사람이 없으면 누가 대신 확인할지 정하고 실제로 어떤 조치를 했는지 남기는 것입니다. 시스템에서는 잘못 걸러진 위험을 정기적으로 살펴야 합니다. 다음 연구에서는 관리자의 평가와 함께 조치 기록과 사고 기록을 확인할 필요가 있습니다. 이 내용은 현장 운영을 위한 제안이며 이번 연구로 그 효과까지 확인한 것은 아닙니다.'
s=p.slides[25];put(obj(s,11),'도입 전후에 무엇이 달라졌는지는 아직 모른다')
t=obj(s,14).table
rows=[['이번 연구에서 확인하지 못한 점','다음에 확인할 방법'],['같은 현장의 도입 전후 변화','같은 현장을 도입 전후로 반복 조사'],['다른 기관에서도 같은 결과인지','조사 기관을 넓히고 실제 기록도 확인'],['시스템 버전·촬영 조건 차이','비슷한 조건에서 같은 버전으로 비교'],['YOLO가 처음부터 놓친 위험','전체 영상 평가·여러 평가자의 판정'],['열람·조치까지의 시간과 비용','실제 처리시간·사고 기록·전체 비용 확인']]
for i,row in enumerate(rows):
 for j,v in enumerate(row):put(t.cell(i,j),v);fs(t.cell(i,j),15)
put(obj(s,16),'한 번 조사한 두 집단의 차이이며, 같은 현장이 좋아졌다는 뜻은 아님')
s.notes_slide.notes_text_frame.text='가장 큰 한계는 도입 전 상태를 조사하지 않았다는 점입니다. 한 번 조사한 두 집단의 점수가 달랐다는 사실은 알지만 같은 현장이 도입 후 얼마나 달라졌는지는 모릅니다. 다른 기관으로도 조사를 넓히고, 비슷한 촬영 조건과 시스템 버전에서 비교해야 합니다. 영상에서 처음부터 놓친 위험과 알림을 읽고 조치하기까지 걸린 시간, 실제 비용도 더 확인해야 합니다.'
s=p.slides[26];put(obj(s,11),'시스템을 만들고, 현장 관리자의 평가를 비교했다');fs(obj(s,11),25)
put(obj(s,14),'도입 현장 관리자의 평가가 더 높았다.\n사고 감소나 도입 전후 변화는 확인하지 못했다.');fs(obj(s,14),26)
put(obj(s,16),'개발  기존 CCTV와 PC로 위험 판단·알림을 연결\n결과  나이·경력 등 차이를 고려해도 0.54점 높음 (p=.005)\n다음  같은 현장의 전후 변화와 실제 조치·사고 기록 확인');fs(obj(s,16),18)
s.notes_slide.notes_text_frame.text='기존CCTV와 범용PC를 활용해 위험을 판단하고 담당자에게 알리는 시스템을 만들었습니다. 운영 기록에서는 오경보가 줄었지만 실제 위험 경보가 일부 빠지는 점도 확인했습니다. 도입 현장 관리자의 평가는 나이·경력 등의 차이를 고려한 뒤에도 미도입 현장보다0.54점 높았습니다. 그러나 실제 사고가 줄었는지, 같은 현장이 도입 전보다 좋아졌는지는 확인하지 못했습니다. 다음에는 같은 현장을 반복 조사하고 실제 조치와 사고 기록을 함께 확인해야 합니다.'
# Add two new background slides before the existing research purpose slide.
ids=list(p.slides._sldIdLst);order=[1,2,3,4,32,33]+list(range(5,32))
for el in list(p.slides._sldIdLst):p.slides._sldIdLst.remove(el)
for no in order:p.slides._sldIdLst.append(ids[no-1])
for i,s in enumerate(p.slides,1):
 if i>1:put(obj(s,13),str(i))
changed={4,5,21,25,26,27};mapping={old:(old if old<=4 else old+2) for old in range(1,32)}
for old,new in mapping.items():
 if old not in changed:
  assert snap(p.slides[new-1])==before[old-1],(old,new)
  assert p.slides[new-1].notes_slide.notes_text_frame.text==oldnotes[old-1]
assert len(p.slides)==33
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_서론결론수정.pptx';assert not out.exists();p.save(out)
r=dict(source_pptx=str(src.resolve()),source_sha256=digest,output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=33,main_slides=29,appendix_slides=4,changed_slides=[4,5,6,7,23,27,28,29],divider_slides=[3,8,11,19,26],old_to_new=mapping,intro_source_idxs=list(range(218,245)),checks=[{'other_original_content_notes_images_preserved':True}],limitations=[])
(B/'intro_conclusion_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
