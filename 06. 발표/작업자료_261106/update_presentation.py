from pathlib import Path
from copy import deepcopy
import json,re,datetime,zipfile,hashlib
from zoneinfo import ZoneInfo
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from PIL import Image
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent
src=ROOT/'261105_1550_윤혁_석사학위논문_심의발표.pptx'
p=Presentation(src)
BLUE='123B78'; TEAL='218C9E'; GRAY='8794A4'; RED='BE593C'; DARK='172537'; PALE='EEF3F8'
changes=[]
def txt(sl,x,y,w,h,text,size=18,color=DARK,bold=False,align=None):
 sh=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True
 tf.margin_left=tf.margin_right=Inches(.025);tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(text.split('\n')):
  q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=line
  if align is not None:q.alignment=align
  for r in q.runs:r.font.name='맑은 고딕';r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=RGBColor.from_string(color)
 return sh
def box(sl,x,y,w,h,color):
 sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background();return sh
def line(sl,x1,y1,x2,y2,color=GRAY,width=1):
 sh=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2));sh.line.color.rgb=RGBColor.from_string(color);sh.line.width=Pt(width);return sh
def dot(sl,x,y,color):
 sh=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x-.055),Inches(y-.055),Inches(.11),Inches(.11));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background()
def settext(sh,value):
 ps=sh.text_frame.paragraphs
 if ps and ps[0].runs:
  ps[0].runs[0].text=value
  for rr in list(ps[0].runs)[1:]:rr.text=''
  for pp in list(ps)[1:]:sh.text_frame._txBody.remove(pp._p)
 else:sh.text=value

def header(sl,title,source,section=None):
 for sh in sl.shapes:
  if sh.shape_id==11:settext(sh,title)
  if sh.shape_id==12:settext(sh,source)
  if section and sh.shape_id==2:settext(sh,section[0])
  if section and sh.shape_id==10:settext(sh,section[1])
def clear(sl):
 for sh in list(sl.shapes):
  if sh.shape_id not in [2,10,11,12,13]:sh._element.getparent().remove(sh._element)
def takeaway(sl,t):
 box(sl,.56,6.18,8.88,.58,'FBF3E7');txt(sl,.73,6.27,8.5,.40,t,16,'A9651B',True)
def pic(sl,path,x,y,w,h):
 iw,ih=Image.open(path).size;scale=min(w/iw,h/ih);ww,hh=iw*scale,ih*scale
 sl.shapes.add_picture(str(path),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),Inches(ww),Inches(hh))
def clone_at(template,after):
 sl=p.slides.add_slide(template.slide_layout)
 for sh in list(sl.shapes):sh._element.getparent().remove(sh._element)
 for sh in template.shapes:sl.shapes._spTree.insert_element_before(deepcopy(sh._element),'p:extLst')
 ids=p.slides._sldIdLst;el=ids[-1];ids.remove(el);ids.insert(after+1,el)
 clear(sl);return sl

def change(no, sid, value):
 sl=p.slides[no-1]
 for sh in sl.shapes:
  if sh.shape_id==sid:
   before=sh.text;settext(sh,value);changes.append({'slide':no,'shape':sid,'before':before,'after':value});return
 raise ValueError((no,sid))

def table(sl, rows, widths, y=2.0, height=3.6, size=17):
 sh=sl.shapes.add_table(len(rows),len(rows[0]),Inches(.65),Inches(y),Inches(8.7),Inches(height))
 for j,w in enumerate(widths):sh.table.columns[j].width=Inches(w)
 for i,row in enumerate(rows):
  for j,value in enumerate(row):
   c=sh.table.cell(i,j);c.text=value;c.margin_left=c.margin_right=Inches(.10)
   c.fill.solid();c.fill.fore_color.rgb=RGBColor.from_string(BLUE if i==0 else ('EEF3F8' if i%2 else 'FFFFFF'))
   for q in c.text_frame.paragraphs:
    for r in q.runs:r.font.name='맑은 고딕';r.font.size=Pt(size);r.font.bold=i==0;r.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else DARK)
 return sh

change(2,29,'조정평균 차이 · 가설 검증 · 실제 운용')
change(5,29,'이미지·판단사유\n지정 담당자 알림')
change(7,19,'현재 알림과 같은 맥락의 교정 선택')
# Replace the old RAG artwork with the exact current PDF figure.
sl=p.slides[6]
for sh in list(sl.shapes):
 if sh.shape_type==13:sh._element.getparent().remove(sh._element)
pic(sl,BASE/'pdf50_image0.jpeg',.6,1.65,4,4.4)
changes.append({'slide':7,'change':'최신 PDF p.37 그림3-3 교체, 근거에 없는 최대3건 삭제'})
change(12,15,'시스템 도입 (X)')
change(12,20,'공통 B 8문항의 평균점수')
change(12,21,'공변량: 만 나이·경력 | 고정요인: 소속·성별·역할·총공사비 구간')
change(14,12,'논문 <표 4-3>·<표 4-4> · 제4장 제5절 제2항')
change(14,14,'단일 종속변수 Y = B 8문항의 동일 가중 평균')
change(14,17,'업무 내용의 구분은 문항 설명용이며, 각각 별도 점수를 산출하지 않음')
sl=p.slides[13]
for sh in sl.shapes:
 if sh.has_table:
  vals=[['문항의 업무 내용','문항','측정 초점'],['위험 조기인지','B-1','위험을 일찍 알아차리는 수준'],['초동대응 지시','B-2','인지 후 초기 대응 지시'],['원격 상황 파악','B-3·4','현장 밖 상황 파악과 정보공유'],['순찰·확인 업무 효율','B-5·6','순찰·확인 업무의 부담 경감'],['위험 통제','B-7·8','시정·작업중지 등 위험 통제']]
  for i,row in enumerate(vals):
   for j,v in enumerate(row):
    c=sh.table.cell(i,j);c.text=v
    for para in c.text_frame.paragraphs:
     for r in para.runs:r.font.name='맑은 고딕';r.font.size=Pt(16);r.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else DARK)
changes.append({'slide':14,'change':'5개 하위요인 표현을 문항 업무내용으로 변경; Y 단일평균 명시'})
change(15,12,'논문 <표 4-7>·<표 4-8> · 제4장 제5절')
change(15,16,'연속형 통제변수 (공변량)\n만 나이 · 건설현장 경력\n\n범주형 통제변수 (고정요인)\n소속 · 성별 · 역할 · 총공사비 구간')
change(16,12,'논문 <표 4-12> | B 8문항 평균 · 5점 척도 · 95% CI')
sl=p.slides[16];clear(sl);header(sl,'전체 실효성과 지시 전달 시간은 구분하여 해석','논문 <표 4-14> · 제4장 제7절 제2항')
table(sl,[['구분','분석 결과','판단'],['안전관리 실효성 Y\n공통 B 8문항 평균','조정 차이 +0.54점\n95% CI [0.17, 0.91]\np=.005','연구가설 (1-1)\n지지'],['지시 전달 소요시간\n과정지표 A-9','Fisher 정확검정\np=.663','유의한 집단 차이를\n확인하지 못함']],[3.0,3.2,2.5],height=3.7,size=18)
takeaway(sl,'지각 실효성의 차이가 실제 지시·조치의 개선을 뜻하지는 않음')
changes.append({'slide':17,'change':'삭제된 하위요인/Holm 결과 대신 최신 표4-14와 A-9 해석'})
change(19,11,'위험 인지 경로의 차이와 지시 시간을 함께 확인')
change(20,12,'논문 <표 4-13> · 제4장 제7절 제1항 강건성 점검')
change(20,14,'사전계획 민감도분석과 사후 강건성 점검을 구분')
change(20,18,'사전계획·사후 보완분석 모두 주분석(전체 73명)을 대체하지 않음')
change(21,11,'전체 실효성의 차이를 운용실태와 함께 해석')
sl=p.slides[20]
for sh in list(sl.shapes):
 if sh.has_table:sh._element.getparent().remove(sh._element)
table(sl,[['관찰 결과','논의'],['전체 실효성 차이 +0.54점','스마트기술–안전성과 관련 연구와 방향 일치\n황병복(2026), 류정·박인선(2025)'],['시스템 경로 작동 15/34명','A-7 ③·④이면서 A-8 ③인 경우\n전체 도입 현장에서 동일하게 활용된 것은 아님'],['지시 전달 시간 차이 비유의','관리자 알림 이후 작업자 지시는 별도 단계\n특정 기능·개별 업무의 효과로 해석하지 않음']],[3.1,5.6],y=1.9,height=3.9,size=17)
changes.append({'slide':21,'change':'개별 하위요인 해석 삭제, 전체 실효성·운용경로·A-9 논의로 갱신'})
change(25,12,'논문 <표 4-10>·<표 4-11> · 제4장 제7절 제1항')
sl=p.slides[25];clear(sl);header(sl,'보충 2. 단일 점수의 측정과 분석 범위','논문 <표 4-3>·<표 4-4>·<표 4-7>·<표 4-8>')
table(sl,[['구분','산출 및 분석 원칙'],['종속변수 Y','B-1∼B-8 동일 가중 평균 · 전 문항 응답 시 산출\n업무 내용별 별도 점수·검정 없음'],['척도 점검','PAF 1요인 · 설명분산 66.6% · α=.937\n단일차원성·집단 간 측정동등성 확정은 아님'],['통제변수 C','A-1∼A-6: 공변량 2개 + 범주형 고정요인 4개'],['현장 운영특성','A-7∼A-9: Y 및 통제변수에 포함하지 않음\n운용 확인·민감도분석·과정지표 비교에 사용']],[2.3,6.4],y=1.85,height=4.05,size=16)
takeaway(sl,'도입 전용 C·D는 제3장 기술통계 · 집단 비교 가설 검정에는 미포함')
changes.append({'slide':26,'change':'삭제된 하위요인 보충표를 단일 Y 측정·분석범위 참고자료로 교체'})

# Current source and a concise speaking note on each revised topic.
notes={7:'같은 맥락의 교정만 주입한다. 교정이 없으면 미주입한다. 정확도의 지속 향상이나 과교정 방지를 보장하지 않는다.',12:'X는 시스템 도입, Y는 B 8문항 평균 하나이다. 만 나이·경력은 공변량, 나머지 네 변수는 범주형 고정요인이다.',14:'문항이 다루는 업무내용을 설명하는 표이다. 다섯 개의 별도 요인 점수를 산출하거나 검정하지 않는다.',16:'도입 3.83 [3.38,4.28], 미도입 3.29 [2.90,3.69]. 차이 B=.54 [0.17,.91], F(1,62)=8.54, p=.005, 부분 η²=.121. 인과효과가 아니라 조정된 지각 차이이다.',17:'A-9는 별도 과정지표로 Fisher 정확검정 p=.663이다. 비유의는 두 집단의 시간이 동일하다는 입증이 아니다.',20:'시스템 경로 작동 현장 제한은 사전계획 민감도분석이고, 영향점·여성·20억원 미만 제외는 사후 강건성 점검이다.',21:'전체 실효성만 비교하였으므로 특정 시스템 기능이 특정 업무 차이를 만든다고 말할 수 없다. 선행연구는 성과지표가 달라 효과크기를 직접 비교하지 않는다.',26:'공통부는 A 9문항과 B 8문항(17문항), 도입 현장 전용부 C 8문항과 D 4문항(합계29문항)이다.'}
for i,sl in enumerate(p.slides,1):
 sl.notes_slide.notes_text_frame.text='기준: 00. hwpx/261106_1132_경기공학_건축안전_윤혁_논문.pdf\n'+notes.get(i,'최신 논문의 해당 표·그림·장절을 근거로 발표한다. 집단 비교는 횡단 설문의 조정된 지각 차이이며 인과효과로 단정하지 않는다.')
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M')
out=ROOT/f'{stamp}_윤혁_석사학위논문_심의발표.pptx';p.save(out)
report={'output_pptx':str(out),'output_pdf':str(out.with_suffix('.pdf')),'source_pdf':'00. hwpx/261106_1132_경기공학_건축안전_윤혁_논문.pdf','slide_count':len(p.slides),'changes':changes,'checks':[],'limitations':[]}
(BASE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(out)
