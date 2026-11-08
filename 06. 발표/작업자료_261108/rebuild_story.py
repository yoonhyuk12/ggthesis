from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from zoneinfo import ZoneInfo
import json,datetime,hashlib
B=Path(__file__).resolve().parent;R=B.parent
src=R/'261108_1409_윤혁_석사학위논문_심의발표.pptx';original=R/'261106_1209_윤혁_석사학위논문_심의발표.pptx';thesis=R.parent/'00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx'
p=Presentation(src);old=list(p.slides)
order=[1,2,3,4,6,5,8,9,18,12,13,14,15,16,20,19,11,22,23,24,10,25,26,27]
ids=list(p.slides._sldIdLst)
for el in ids:p.slides._sldIdLst.remove(el)
for no in order:p.slides._sldIdLst.append(ids[no-1])
for no in set(range(1,28))-set(order):p.part.drop_rel(ids[no-1].rId)
BLUE='123B78';TEAL='218C9E';DARK='172537';GRAY='68788B';PALE='EEF3F8';RED='BE593C'
changes=[]
def sh(no,id):return next(x for x in p.slides[no-1].shapes if x.shape_id==id)
def settext(obj,value):
 tf=obj.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=value
  for r in list(q.runs)[1:]:r.text=''
 else:q.text=value
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def change(no,id,value,refs,why='스토리 흐름에 맞춰 재구성'):
 obj=sh(no,id);before=obj.text;settext(obj,value);changes.append(dict(slide=no,old=before,new=value,source_idxs=refs,reason=why))
def font(obj,size,color=None,bold=None):
 for q in obj.text_frame.paragraphs:
  for r in q.runs:
   r.font.name='맑은 고딕';r.font.size=Pt(size)
   if color:r.font.color.rgb=RGBColor.from_string(color)
   if bold is not None:r.font.bold=bold

def box(sl,x,y,w,h,color):
 s=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(color);s.line.fill.background();return s

def txt(sl,x,y,w,h,t,size=19,color=DARK,bold=False,align=None):
 s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=s.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=Inches(.025);tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if not i else tf.add_paragraph();q.text=line;q.space_after=Pt(5)
  if align is not None:q.alignment=align
 font(s,size,color,bold);return s

def clear(no):
 sl=p.slides[no-1]
 for s in list(sl.shapes):
  if s.shape_id not in [2,10,11,12,13]:s._element.getparent().remove(s._element)
 return sl

def takeaway(sl,t):box(sl,.56,6.18,8.88,.58,'FBF3E7');txt(sl,.73,6.27,8.5,.40,t,16,'A9651B',True)

def card(sl,x,y,w,h,heading,body):
 box(sl,x,y,w,h,PALE);txt(sl,x+.18,y+.18,w-.36,.6,heading,22,BLUE,True);txt(sl,x+.18,y+1.0,w-.36,h-1.15,body,19)

# A single question-to-answer arc instead of a chapter list.
change(2,11,'기존 CCTV를 활용한 관제, 두 수준에서 검증',[247,249,250])
change(2,12,'논문 제1장 제2절 연구의 목적',[247,248,249,250])
s=clear(2)
for x,head,body in [(0.65,'01  왜 필요한가','CCTV를 계속 지켜보기\n어려운 현장'),(3.65,'02  무엇을 만들었나','영상 확인·위험 판단·알림을\n연결한 관제 시스템'),(6.65,'03  무엇을 확인했나','경보 후보 선별성능과\n관리자가 지각한 실효성')]:card(s,x,2.05,2.7,3.6,head,body)
takeaway(s,'개발 → 기술평가 → 도입·미도입 현장 비교')
change(3,11,'CCTV가 있어도 위험을 계속 살피기는 어렵다',[240,243])
change(3,14,'기존 영상의 활용을 높이되, 불필요한 경보와 위험 누락을 함께 살펴야 한다',[240,241])
change(3,17,'영상 확인 부담',[240]);change(3,18,'육안 확인에 의존\n모니터링 인력 부족\n공정 확인 위주 활용',[240])
change(3,21,'오경보 문제',[241]);change(3,22,'정상 작업도 오탐\n작업 문맥 추가 검증\n실제 위험 손실 점검',[241])
change(3,25,'업무 효과의 질문',[244]);font(sh(3,25),21)
change(3,26,'탐지가 정확해도\n안전관리 업무가\n더 나은지는 별도 검증',[244])
change(3,28,'그래서 영상관제와 위험 판단·알림을 연결하고, 현장 업무 수준까지 비교했다',[247,248,250])
font(sh(3,28),15)
change(3,12,'논문 제1장 제1절 · Kim et al.(2022) · 류정·박인선(2025)',[240,241])
change(4,11,'만드는 것에서 끝내지 않고, 두 가지를 확인했다',[247,249,250])
change(4,14,'시스템 구현 → 경보는 잘 걸러지는가? → 도입 현장의 업무 수준은 다른가?',[247,249,250])
font(sh(4,14),20)
change(4,18,'다중·단일 영상관제\nYOLO와 LLM 연계\n지정 담당자 알림',[248,256])
change(4,22,'오경보와 위험 손실\n검출 판정 시간\n교정 사례 비교',[249,846,1026]);font(sh(4,22),19)
change(4,26,'도입·미도입 현장\n동일한 8문항\n여섯 특성 조정',[250,256])
change(5,11,'기존 카메라와 PC에서 영상·알림·교정을 한곳에',[535,808,809])
change(5,14,'여러 영상을 확인하고, 경보의 장면과 판단 사유를 보고 교정',[808,809])
change(6,11,'YOLO는 후보를 찾고, LLM은 문맥을 검증한다',[703,751])
change(6,14,'관리자가 계속 화면을 보지 않아도, 선별한 경보를 지정 담당자에게 전달',[243,751,769])
font(sh(6,14),20)
change(7,11,'먼저, 운영 중 쌓인 경보 후보 878건을 평가했다',[829])
change(7,19,'라벨링 가능한 경보 후보',[829]);font(sh(7,19),16)
change(7,25,'YOLO가 잡아낸 후보의 2차 선별성능 평가 · 1차 미탐은 평가 범위 밖',[825,829,848])
font(sh(7,25),15)
change(8,11,'오경보는 834→13건, 실제 위험 5건도 차단되었다',[893,897])
font(sh(8,11),25)
change(8,14,'특이도 98.4% · 평가 목표 90% 상회',[847,897])
change(8,27,'조건부 정밀도 .750 · 재현율 .886',[893])
change(8,29,'오경보 감소와 함께, 2차 검증에서 놓친 실제 위험도 관리해야 한다',[893,897])
# Dedicated timing slide; no instruction transmission/process metric.
change(9,11,'검출 판정은 평균 약 7.3초, 모든 사건이 같지는 않다',[897,1026])
font(sh(9,11),25)
change(9,12,'논문 <표 3-7>·<표 3-9> · 제3장 제4절 제4항',[897,1026])
s=clear(9)
card(s,.65,2.1,4.2,3.55,'평균 약 7.3초','YOLO 확정 최소 약 0.7초\n+ LLM 평균 6.55초\n\n평균 10초 이내 설계 목표 충족')
card(s,5.15,2.1,4.2,3.55,'지연의 편차도 존재','LLM 중앙값 3.7초\nLLM 최댓값 62.8초\n\n메신저 전송·열람 시간은 제외')
takeaway(s,'설정상 최소시간을 합산한 평균값 · 순간형 위험 회피를 보장하는 시간은 아님')
change(10,11,'기술성능만으로 현장 업무 실효성을 알 수는 없다',[244,250])
change(10,12,'논문 제1장 제2절 · <그림 4-1>·연구가설 (1-1)',[250,1120])
change(10,23,'연구 질문\n여섯 특성의 차이를 조정해도\n도입 현장의 지각 실효성이 미도입 현장보다 높은가?',[250,1120])
change(11,11,'같은 기관의 73개 현장, 관리자 1명씩 비교했다',[254])
change(11,25,'조사는 한 번, 도입 전 측정은 없음 · 도입의 인과효과로 단정할 수 없음',[255,1699]);font(sh(11,25),15)
change(12,11,'두 집단에 같은 업무를 묻고, 하나의 점수로 비교했다',[256,1141,1169])
font(sh(12,11),25)
change(12,17,'시스템 기능의 만족도가 아니라, 현장 일반의 안전관리 업무 수준',[1141,1169])
change(13,11,'응답자·현장 차이는 조정하고, 척도도 점검했다',[1103,1568])
change(13,21,'jamovi 2.7.41 · 통계적 조정만으로 두 집단의 모든 차이가 사라지는 것은 아님',[257,1102,1103])
font(sh(13,21),15)
change(14,11,'조정 후에도 도입 현장의 지각 실효성이 0.54점 높았다',[1568,1569]);font(sh(14,11),25)
change(14,14,'연구가설 (1-1) 지지 · 같은 시점의 관리자 지각 점수 차이',[1569,1662])
change(15,11,'비교 대상을 달리해도 차이의 방향은 유지되었다',[1610,1611]);font(sh(15,11),25)
change(15,18,'보완분석은 주분석을 지지하는 참고자료 · 전체 73명 결과를 대체하지 않음',[1610,1611]);font(sh(15,18),15)
# Operational uptake: A-7/A-8 only, no old three-panel image containing A-9.
change(16,11,'설치한 모든 현장에서 알림이 인지 수단이 된 것은 아니다',[1086,1687]);font(sh(16,11),24)
change(16,12,'논문 제3장 제4절 제6항 · 제4장 제8절 · A-7·A-8 운용실태',[1086,1687])
s=clear(16)
txt(s,.7,1.75,8.6,.6,'도입 현장 관리자 34명 중',21,GRAY)
box(s,.8,2.55,3.55,2.55,PALE);txt(s,1.0,2.75,3.1,.85,'15명 / 34명',32,BLUE,True)
txt(s,1.0,3.75,3.1,1.0,'시스템 알림이 실제\n위험 인지 수단으로 작동',20)
txt(s,4.9,2.65,4.1,.65,'나머지 19명',25,BLUE,True)
txt(s,4.9,3.45,4.1,1.1,'전화·보고나 순찰 등\n기존 인지 경로에 의존',21)
txt(s,.8,5.35,8.5,.5,'판정 기준: 담당자 부재 시 시스템 경로 + 발생 직후 알림으로 인지',16,GRAY)
takeaway(s,'도입 여부뿐 아니라, 알림이 실제로 쓰이는 운영 과정도 살펴야 한다')
change(17,11,'사용 경험은 알림 전파를 가장 높게 평가했다',[1076,1077])
change(17,16,'도입 34명의 보조적 경험 조사 · 현장 간 가설 검정에는 넣지 않음',[1047,1078])
font(sh(17,16),15)
change(18,11,'현장 적용에서는 알림 뒤의 확인·조치까지 연결해야 한다',[1697]);font(sh(18,11),24)
change(18,12,'논문 제5장 시사점 · 연구 결과를 바탕으로 한 운영 제안',[1697,1698])
change(18,15,'기술 관리',[1693]);change(18,19,'운영 제안',[1697]);change(18,23,'후속 검증',[1698])
change(18,27,'연구가 확인한 지각 차이를 실제 관리 성과로 연결하려는 운영·연구 제안',[1697,1698]);font(sh(18,27),15)
change(19,11,'도입 전후의 변화는 아직 확인하지 못했다',[1699])
change(19,16,'한 시점의 차이는 확인 · 다음 연구는 같은 현장의 전후 변화와 실제 조치 기록',[1699,1700]);font(sh(19,16),15)
change(20,11,'개발과 현장 비교를 연결한 것이 이 연구의 성과다',[1691,1696]);font(sh(20,11),25)
change(20,14,'기존 장비로 안전관제를 구현했고,\n도입 현장의 지각 실효성은 더 높았다.',[1693,1695]);font(sh(20,14),27)
change(20,16,'기술평가  오경보 감소와 실제 위험 차단을 함께 확인\n현장비교  조정 차이 +0.54점, p=.005\n다음 과제  도입 전후 변화·실제 조치·재해 기록 검증',[1693,1695,1700]);font(sh(20,16),20)
change(21,11,'보충 1. RAG는 오경보를 줄였지만 재현율도 낮았다',[970]);font(sh(21,11),24)
change(22,11,'보충 2. ANCOVA 가정과 표본 불균형',[1565])
change(23,11,'보충 3. 측정과 분석의 범위',[1141,1169])
table=sh(23,14).table
for col,text in enumerate(['운용실태 확인','A-7·A-8: 위험 인지 경로·시점\n종속변수·통제변수에는 미포함']):settext(table.cell(4,col),text)
change(24,11,'보충 4. 기술평가가 확인한 것과 남은 것',[825,848,969])
# Consistent story sections and page numbers.
for i,s in enumerate(p.slides,1):
 if i==1:continue
 section=('01','문제와 연구 질문') if i<=4 else ('02','개발과 기술평가') if i<=9 else ('03','현장 비교와 해석') if i<=17 else ('04','결론과 다음 과제') if i<=20 else ('부록','질의응답 참고')
 settext(sh(i,2),section[0]);settext(sh(i,10),section[1]);settext(sh(i,13),str(i))
# Replace all generic notes with concise presentation narrative tied to thesis paragraphs.
notes={
1:('기존 CCTV와 범용 PC를 활용한 안전관제 시스템을 개발하고, 도입·미도입 현장의 관리자가 지각한 실효성을 비교한 연구입니다.',[247]),
2:('발표는 세 질문으로 이어집니다. 기존 CCTV만으로 무엇이 어려운지, 이를 보완하기 위해 무엇을 만들었는지, 만든 시스템의 기술성능과 현장 업무 수준은 어떻게 확인했는지 설명하겠습니다.',[240,247,249,250]),
3:('CCTV가 설치되어 있어도 사람이 계속 확인하기 어렵습니다. Kim et al.(2022)은 중소규모 3개 현장에서 육안 확인과 공정 확인 위주의 활용 문제를 보고했습니다. 자동 탐지를 붙이면 정상 장면의 오경보가 생길 수 있으므로 문맥 검증과 실제 위험 손실을 함께 봐야 합니다. 정확도만으로 업무 실효성이 입증되는 것도 아닙니다.',[240,241,244]),
4:('그래서 시스템 개발, 후보 경보의 기술평가, 도입·미도입 현장의 동일 척도 비교를 한 연구로 연결했습니다. 기술 선별성능과 관리자 지각 실효성은 서로 다른 평가입니다.',[248,249,250,251]),
5:('먼저 실제 구현 화면입니다. 기존 카메라의 여러 영상을 한 화면에서 보고, 알림의 장면과 판단 사유를 확인하며 오판을 교정할 수 있습니다. 화면은 구현 범위를 보여주며 열람이나 조치 완료를 증명하지는 않습니다.',[808,809,814]),
6:('YOLO가 먼저 위험 후보를 찾고, LLM이 원본 장면의 문맥을 검토해 SEND 또는 BLOCK을 판단합니다. 정상 경로에서 허용된 알림은 지정 담당자에게 전달합니다. 검증 장애는 별도 예외 경로로 처리하므로 모든 알림이 검증을 마친다는 뜻은 아닙니다. 현장 조치는 관리자의 업무입니다.',[703,751,757,769]),
7:('2026년 5월19일부터 27일까지 운영 기록 중 스냅샷 라벨링이 가능한 경보 후보878건을 평가했습니다. 38대 카메라의 중장비 접근610건과 차량 접근268건입니다. 사람이 실제 위험44건과 안전 장면834건으로 분류했습니다. 분모는 YOLO가 이미 잡아낸 후보이므로 전체 현장 탐지율이 아닙니다.',[829,833,893]),
8:('안전 장면834건 중821건은 차단되고13건이 발송되었습니다. 실제 위험44건 중39건은 발송되고5건은2차 검증에서 차단되었습니다. 특이도98.4%는 참고 목표90%를 넘었지만 외부 인증 결과는 아닙니다. 조건부 정밀도.750, 재현율.886입니다. 따라서 오경보 감소와 위험 경보 손실을 함께 관리해야 합니다.',[847,848,893,897]),
9:('LLM 평균 응답6.55초에 YOLO 확정 설정상 최소 약0.7초를 합산하면 평균 검출 판정은 약7.3초입니다. 평균10초 설계 목표에 부합하지만 모든 사건의 목표 충족을 뜻하지 않습니다. LLM 중앙값3.7초, 최댓값62.8초로 편차가 있습니다. 메신저 전송이나 담당자 열람 시간은 포함하지 않았으며 순간형 위험 회피 보장을 뜻하지 않습니다.',[544,545,897,1026]),
10:('기술평가에서 경보를 걸러내는 성능을 확인했지만 이것만으로 현장 업무가 더 낫다고 말할 수 없습니다. 그래서 시스템 도입을 독립변수, 공통8문항의 평균을 단일 종속변수로 두고 여섯 특성을 조정한 뒤 비교했습니다.',[244,250,256,1120]),
11:('같은 기관 산하73개 현장에서 관리자1명씩 조사했습니다. 도입34개소, 미도입39개소입니다. 도입 현장은3개월 이상 정상 운용을 확인했고,2026년10월12일부터23일에 한 번 조사했습니다. 공통 문항은 직전1개월 기준입니다. 도입 전 점수를 측정하지 않았으므로 원래의 집단 차이를 배제할 수 없습니다.',[254,255,1699]),
12:('두 집단 모두 특정 시스템 기능이 아닌 일반 안전관리 업무를 평가했습니다.8문항은 위험 인지부터 초동 대응, 원격 파악, 순찰·확인 효율, 위험 통제를 다룹니다. 이를 각각 별도 요인으로 검정하지 않고 같은 가중치의 평균 하나로 비교했습니다.',[256,437,1141,1169]),
13:('나이·경력은 연속형 공변량이고 소속·성별·역할·총공사비 구간은 범주형 고정요인입니다. 척도 내적 일관성은α=.937이고 탐색적1요인 설명분산은66.6%였습니다. 이것만으로 집단 간 측정동등성이 확정되는 것은 아니며 통계적 조정도 모든 선정 차이를 제거하지는 못합니다.',[1103,1142,1568]),
14:('조정평균은 도입3.83점, 미도입3.29점으로0.54점 차이였습니다. 차이의95%신뢰구간은0.17~0.91,p=.005,부분η²=.121입니다. 연구가설은 지지되었지만 같은 시점의 지각 점수 차이이며 동일 현장의 개선이나 인과효과는 아닙니다.',[1568,1569,1662]),
15:('시스템 경로가 작동한15명으로 도입 집단을 제한한 사전계획 민감도분석에서도 차이는0.78점이었습니다. 분석 뒤 영향점과 희소범주를 제외한 보완점검에서는0.44~0.53점으로 방향이 유지되었습니다. 보완분석은 전체73명의 주분석을 대체하지 않습니다.',[1610,1611]),
16:('도입34명 중 담당자 부재 시 시스템 경로를 사용하고 발생 직후 알림으로 인지한 응답자는15명이었습니다. 나머지19명은 전화·보고나 순찰 등에 기대었습니다. 이는 설치와 실제 활용을 구분해서 볼 필요를 보여주는 운용실태 자료이며 가설 검정의 별도 성과가 아닙니다.',[1084,1086,1687]),
17:('도입34명에게만 물은 사용 경험을 보조자료로 봅니다. 알림 전파는3.99점으로 가장 높고 경보 피로도 완화 인식은3.65점입니다. 피로도 평가는 이전의 일반 알림 경험을 기억에 의존하여 비교한 것이며 객관적인 전후 측정이 아닙니다. 이 점수는 현장 간 가설 검정에 넣지 않았습니다.',[1047,1048,1076,1077,1078]),
18:('여기부터는 결과에 근거한 운영 제안입니다. 기술적으로 잘못 차단된 위험을 검토하고, 현장에서는 알림 담당자와 부재 시 확인자를 지정하며 실제 시정·작업중지 여부를 기록할 필요가 있습니다. 후속 연구에서는 관리자 평가와 객관적인 조치·재해기록을 함께 검증해야 합니다.',[1697,1698,1700]),
19:('핵심 한계는 같은 현장을 도입 전후로 비교하지 못한 것입니다. 또한5월기술평가와10월설문은 서로 다른 운용판본을 대상으로 합니다. 후속 연구는 기관과 공종을 넓히고 조건이 비슷한 비교현장을 선정하며 반복조사와 실제 기록을 연결해야 합니다.',[831,1699,1700]),
20:('본 연구는 기존 장비 기반 시스템 구현, 운영 경보 평가, 같은 기관의 도입·미도입 현장 비교를 함께 제시했습니다. 도입 현장의 지각 실효성이 더 높았다는 결과는 확인했지만 실제 변화와 재해 감소는 후속 검증 과제입니다.',[1693,1695,1696,1699,1700]),
21:('별도6개카메라202건 회고적 비교에서 RAG는 FP17→7건,정밀도.320→.462였으나재현율.333→.250이었습니다. 보편적 성능우위는 아닙니다. 평가 이후 기본교정은 플레이북으로 변경되었고 RAG는 대체경로로 남았으며 플레이북성능은 평가하지 않았습니다.',[764,969,970]),
22:('가정 점검의 비유의는 표본균형이나 인과적 비교가능성을 보장하지 않습니다. 여성6명은 모두 미도입,20억원미만 도입은3명이며 주분석에 전체표본을 포함한 후 보완점검을 했습니다.',[1565,1611]),
23:('Y는공통B8문항 평균 하나입니다.업무내용별 별도점수나검정은 하지 않았습니다. A-1~A-6는통제변수이고 위험인지 경로·시점은운용실태확인용입니다. 도입전용C·D는기술통계이며집단간가설검정에포함하지않습니다.',[256,1078,1084,1141]),
24:('운영878건은1차후보에대한2차필터성능,202건은별도회고적교정비교입니다.분모와조건이다르므로직접비교하지않습니다.1차미탐을포함한전체탐지,재해감소,인력대체,경제성을입증한것은아닙니다.',[825,848,969,1700])}
for no,(text,refs) in notes.items():
 before=p.slides[no-1].notes_slide.notes_text_frame.text
 p.slides[no-1].notes_slide.notes_text_frame.text='기준: 00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx\n'+text
 changes.append(dict(slide=no,old=before,new=text,source_idxs=refs,reason='질문에서 결과로 이어지는 발표노트 재작성'))
# Confirm no process-time/A-9 reference remains anywhere, including notes/table cells.
for no,s in enumerate(p.slides,1):
 texts=[s.notes_slide.notes_text_frame.text]
 for x in s.shapes:
  if x.has_text_frame:texts.append(x.text)
  if x.has_table:texts.extend(c.text for r in x.table.rows for c in r.cells)
 assert not any(t in '\n'.join(texts) for t in ['A-9','A–9','지시전달 소요시간','지시 전달 소요시간','과정지표']),no
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_스토리재구성.pptx';assert not out.exists();p.save(out)
(B/'story_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
r=dict(source=str(thesis.resolve()),source_pptx=str(original.resolve()),intermediate_pptx=str(src.resolve()),output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=24,main_slides=20,appendix_slides=4,checks=[],limitations=[],source_hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [original,thesis]})
(B/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
