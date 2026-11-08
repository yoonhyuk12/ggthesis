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
src=ROOT/'261104_2309_윤혁_석사학위논문_심의발표.pptx'
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
# Remove all obsolete printed page references; pin chapter/figure/table references.
for sl in p.slides:
 for sh in sl.shapes:
  if sh.has_text_frame and sh.text.startswith('논문 '):
   settext(sh,re.sub(r',?\s*pp?\.\d+(?:[–−-]\d+)?(?:,\s*\d+)*','',sh.text))
refs={3:'논문 제1장 제1절 연구의 배경 및 필요성',4:'논문 제2장 소결 · 제3장 제4절 · 제4장 제7절',14:'논문 <표 4-7>·<표 4-9> · 제4장 제5절',17:'논문 <그림 3-6> · 제4장 제7절 제2항',18:'논문 제4장 제7절 제1항 민감도·강건성 점검',19:'논문 제4장 제8절 분석결과 및 논의 · 제5장 결론',20:'논문 제5장 결론: 연구의 시사점',21:'논문 제5장 결론: 한계와 향후 연구',22:'논문 제5장 결론',23:'논문 제4장 제6절 상관분석 · 제7절 ANCOVA 가정 점검'}
for no,ref in refs.items():
 for sh in p.slides[no-1].shapes:
  if sh.shape_id==12:settext(sh,ref)
# RAG actual thesis diagram, readable explanatory panel
sl=p.slides[6];clear(sl);header(sl,'현장 교정을 문맥으로 제공하는 RAG 기능','논문 <그림 3-3> · 제3장 제2절 제3항')
pic(sl,BASE/'image4.png',.6,1.65,4.0,4.4)
txt(sl,4.95,1.85,4.2,.65,'유사한 상황의 교정만 검색',22,BLUE,True)
for y,title,body in [(2.8,'① 교정 등록','카메라별 사례·사유·이미지 저장'),(3.65,'② 문맥 검색','같은 맥락의 교정 최대 3건 선택'),(4.5,'③ 재판정','원본 프레임과 함께 LLM에 제공')]:
 txt(sl,4.95,y,4,.4,title,18,BLUE,True);txt(sl,4.95,y+.42,4,.6,body,16)
takeaway(sl,'관련 사례가 없으면 교정 사례를 주입하지 않고 판정')
changes.append({'original_slide':7,'change':'실제 논문 RAG 절차 그림과 설명 배치','source_idxs':[775,776]})
# Editable stacked bars for TP/FN/FP/TN
sl=p.slides[8];clear(sl);header(sl,'오경보는 줄었지만 실제 위험 5건도 차단','논문 <표 3-7> | 1차 후보 878건에 대한 조건부 선별성능')
txt(sl,.6,1.65,8.8,.55,'같은 후보 집합에서 경보 감소와 위험 누락을 함께 확인',20,bold=True)
txt(sl,.7,2.4,2.1,.5,'안전 장면 834건',18,BLUE,True)
box(sl,2.9,2.42,5.3*821/834,.48,TEAL);box(sl,2.9+5.3*821/834,2.42,5.3*13/834,.48,RED)
txt(sl,2.9,3.02,5.5,.5,'821건 차단  |  오경보 13건 발송',18)
txt(sl,.7,3.85,2.1,.5,'실제 위험 44건',18,BLUE,True)
box(sl,2.9,3.87,5.3*39/44,.48,TEAL);box(sl,2.9+5.3*39/44,3.87,5.3*5/44,.48,RED)
txt(sl,2.9,4.48,5.8,.5,'39건 발송  |  위험 5건 차단',18)
box(sl,.7,5.23,.18,.18,TEAL);txt(sl,.95,5.18,3,.4,'올바른 선별',14)
box(sl,3,5.23,.18,.18,RED);txt(sl,3.25,5.18,3,.4,'오경보 / 위험 누락',14)
txt(sl,.7,5.65,8.5,.4,'조건부 정밀도 .750   ·   조건부 재현율 .886',20,BLUE,True)
takeaway(sl,'막대는 실제 분류별 100% 기준 · 오경보 834 → 13건')
changes.append({'original_slide':9,'change':'혼동행렬을 건수·비율 막대도표로 시각화','source_idxs':[886,892]})
# Five-domain effect plot; CI and Holm distinction
sl=p.slides[15];clear(sl);header(sl,'5개 하위요인 중 3개에서 유의한 조정 차이','논문 <표 4-14> | 도입−미도입 차이 · 95% CI는 개별 비보정 구간')
txt(sl,.6,1.63,8.8,.5,'조기인지·원격 파악·위험 통제력에서 차이 확인',20,bold=True)
left=3.05;right=7.45
fx=lambda v:left+(v+.3)/1.6*(right-left)
for v in [0,.5,1]:
 line(sl,fx(v),2.5,fx(v),5.8,'CBD4DF',1.5 if v==0 else .5);txt(sl,fx(v)-.22,5.82,.6,.3,str(v),11,GRAY)
txt(sl,.65,2.2,2.3,.35,'하위요인',14,BLUE,True);txt(sl,7.65,2.2,1.7,.35,'B / Holm p',14,BLUE,True)
rows=[('조기인지',.62,.24,1.01,'.010',True),('대응 신속성',.13,-.25,.51,'.502',False),('원격 파악',.72,.25,1.19,'.012',True),('순찰부담 경감',.52,.05,.99,'.062',False),('위험 통제력',.54,.18,.91,'.012',True)]
for i,(lab,b,lo,hi,pv,sig) in enumerate(rows):
 y=2.8+i*.58;c=TEAL if sig else GRAY
 txt(sl,.65,y-.16,2.3,.4,lab,17,c,sig);line(sl,fx(lo),y,fx(hi),y,c,2.5);line(sl,fx(lo),y-.065,fx(lo),y+.065,c,1.5);line(sl,fx(hi),y-.065,fx(hi),y+.065,c,1.5);dot(sl,fx(b),y,c)
 txt(sl,7.65,y-.16,1.7,.4,f'+{b:.2f} / {pv}',14,c,sig)
takeaway(sl,'유의 판정은 Holm 보정 p 기준 · 순찰부담 경감은 비유의')
changes.append({'original_slide':16,'change':'조정차이·신뢰구간 점도표 및 Holm p 병기','source_idxs':[1782,1783,1785]})
# New final-thesis figures, after technical RAG evaluation and after operational summary.
sl=clone_at(p.slides[9],9)
header(sl,'사용자는 알림 전파를 가장 높게 평가','논문 <그림 3-5> · 제3장 제4절 제5항 | 도입 현장 관리자 34명',('02','시스템 개발 및 기술평가'))
pic(sl,BASE/'image6.png',.6,1.65,8.8,4.4)
takeaway(sl,'도입 현장만의 경험 인식 · 경보 피로도는 회고적 평가')
newC=sl
# original slide17 now index17; insert after it
sl=clone_at(p.slides[17],17)
header(sl,'위험 인지 경로는 달라도 지시 시간은 비슷','논문 <그림 3-6> · 제3장 제4절 제6항 | A-7·A-8은 운용 확인 지표',('04','분석결과와 논의'))
pic(sl,BASE/'image7.png',.5,1.55,9,4.6)
takeaway(sl,'A-9 지시 전달 시간: p=.663 · A-7·A-8은 가설 검증 근거가 아님')
newA=sl
# Per-slide provenance in notes and correct new numbers.
for i,sl in enumerate(p.slides):
 for sh in sl.shapes:
  if sh.shape_id==13 and sh.has_text_frame:settext(sh,str(i+1))
 sl.notes_slide.notes_text_frame.text='기준: 00. hwpx/261105_1444_경기공학_건축안전_윤혁_논문.hwpx\n최종 논문의 표·그림·장절을 기준으로 업데이트. 집단 비교는 횡단 설문의 조정된 지각 차이이며 인과효과로 해석하지 않음.'
 if sl==newC:changes.append({'slide':i+1,'change':'최종 논문 그림3-5 원본 삽입','source_idxs':[1017,1018,1045,1046,1047,1048,1050]})
 if sl==newA:changes.append({'slide':i+1,'change':'최종 논문 그림3-6 원본 삽입 및 해석 구분','source_idxs':[1053,1054,1055,1056,1058]})
for c in changes:
 if 'original_slide' in c:
  no=c['original_slide'];c['slide']=no+(no>10)+(no>17)
# Date prefix determined by current Seoul wall clock
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M')
output=ROOT/f'{stamp}_윤혁_석사학위논문_심의발표.pptx'
p.save(output)
checks=[]
for i,sl in enumerate(p.slides):
 for sh in sl.shapes:
  if sh.left<0 or sh.top<0 or sh.left+sh.width>p.slide_width+9144 or sh.top+sh.height>p.slide_height+9144:checks.append({'slide':i+1,'out_of_bounds':sh.shape_id})
report={'output_pptx':str(output),'output_pdf':str(output.with_suffix('.pdf')),'slide_count':len(p.slides),'changes':changes,'checks':[{'shape_bounds_violations':checks},{'obsolete_page_references':sum(bool(re.search(r'pp?\.\d',sh.text)) for sl in p.slides for sh in sl.shapes if sh.has_text_frame)}],'limitations':[]}
(BASE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
