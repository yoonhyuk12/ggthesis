from pathlib import Path
from copy import deepcopy
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from zoneinfo import ZoneInfo
import datetime,json,hashlib,re
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1425_윤혁_석사학위논문_심의발표_스토리재구성.pptx';p=Presentation(src);h=hashlib.sha256(src.read_bytes()).hexdigest()
def get(sl,id):return next(s for s in sl.shapes if s.shape_id==id)
def put(sh,text):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def clear(sl):
 for s in list(sl.shapes):
  if s.shape_id not in [2,10,11,12,13]:s._element.getparent().remove(s._element)
def tx(sl,x,y,w,h,t,size=20,color='172537',bold=False):
 s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=s.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=line;q.space_after=Pt(5)
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return s
def rect(sl,x,y,w,h,color):
 s=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(color);s.line.fill.background()
def takeaway(sl,t):rect(sl,.56,6.18,8.88,.58,'FBF3E7');tx(sl,.73,6.27,8.5,.4,t,16,'A9651B',True)
def clone():
 tem=p.slides[3];s=p.slides.add_slide(tem.slide_layout)
 for sh in list(s.shapes):sh._element.getparent().remove(sh._element)
 for sh in tem.shapes:
  if sh.shape_id in [2,10,11,12,13]:s.shapes._spTree.insert_element_before(deepcopy(sh._element),'p:extLst')
 return s
# Chapter 2 conceptual foundations.
a=clone();put(get(a,11),'信頼できる警報') if False else None
put(get(a,11),'경보는 많이 보내는 것보다, 믿고 확인할 수 있어야 한다')
for q in get(a,11).text_frame.paragraphs:
 for rr in q.runs:rr.font.size=Pt(24)
put(get(a,12),'논문 제2장 제1·2절 · Cvach(2012), Green & Swets(1966), Davis(1989)')
for x,title,body in [(0.65,'경보 피로도','오경보가 반복되면\n경보를 믿고 확인하는\n행동이 약해질 수 있음'),(3.65,'신호감지이론','오경보를 줄이는 만큼\n실제 위험도 놓치는지\n함께 확인해야 함'),(6.65,'기술수용모델','쓰기 쉬운가\n업무에 도움이 되는가\n도입·사용 조건 검토')]:
 rect(a,x,2.15,2.7,3.45,'EEF3F8');tx(a,x+.18,2.4,2.34,.6,title,22,'123B78',True);tx(a,x+.18,3.4,2.34,1.8,body,18)
takeaway(a,'이론은 시스템 설계와 경험 척도의 근거 · 인과 경로를 검증한 모형은 아님')
a.notes_slide.notes_text_frame.text='반복되는 오경보는 경보의 신뢰와 대응을 약화할 수 있습니다. 경보 피로도는 문맥 검증의 필요성을 설명합니다. 신호감지이론은 오경보와 위험 누락의 상충을 함께 살피게 합니다. 기술수용모델은 사용 용이성과 업무 유용성을 통해 시스템 특성을 정리하는 근거입니다. 이 세 이론을 하나의 인과모형으로 검증한 것은 아닙니다. 그렇다면 기존 연구와 달리 본 연구가 확인할 대상은 무엇인지 이어서 설명하겠습니다.'
b=clone();put(get(b,11),'탐지 정확도와 수용 의도만으로 업무 실효성을 알 수 없다')
for q in get(b,11).text_frame.paragraphs:
 for rr in q.runs:rr.font.size=Pt(24)
put(get(b,12),'논문 <표 2-4> 선행연구와 본 연구의 차별성 · 제2장 제3·4절')
rows=[['비교 관점','선행연구의 주요 관심','본 연구'],['기술·운용','단일 탐지·개별 장비\n일부 하이브리드 관제','기존 장비에 탐지·문맥검증·\n담당자 알림을 연결'],['비교·측정','탐지 정확도·수용 의도\n관제 효율 등','같은 기관의 두 집단에\n공통 8문항 적용'],['분석·해석','기술성능·수용 관계\n일부 현장 비교','여섯 특성을 조정한\n현재 지각 실효성 비교']]
t=b.shapes.add_table(4,3,Inches(.65),Inches(2.05),Inches(8.7),Inches(3.65)).table
for j,w in enumerate([1.4,3.5,3.8]):t.columns[j].width=Inches(w)
for i,row in enumerate(rows):
 for j,value in enumerate(row):
  c=t.cell(i,j);c.text=value;c.margin_left=c.margin_right=Inches(.1);c.fill.solid();c.fill.fore_color.rgb=RGBColor.from_string('123B78' if i==0 else 'EEF3F8')
  for q in c.text_frame.paragraphs:
   for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(17);rr.font.bold=i==0;rr.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '172537')
takeaway(b,'안전관리 실효성: 관리자가 지각한 현재 업무 수행 수준 · 8문항 평균 하나')
b.notes_slide.notes_text_frame.text='선행연구는 탐지 정확도, 기술 수용 의도, 관제 효율 등을 서로 다른 수준에서 다뤘습니다. 본 연구는 기존 장비 기반 시스템을 직접 구현하고, 같은 기관의 도입·미도입 현장에 공통 척도를 적용했습니다. 안전관리 실효성은 관리자가 지각한 현재 안전관리 업무의 수행 수준이며 8문항의 평균 하나로 측정합니다. 다음 장에서는 이 관점을 실제 시스템으로 어떻게 구현했는지 설명하겠습니다.'
# Remove the explicit abstract roadmap and follow the thesis chapter order.
# Original indices refer to the 1425 deck; new theory slides are 26 and 27.
order=[1,2,4,5,26,27,6,7,8,13,14,18,16,9,10,11,12,15,17,19,20,21,22,23,24,25]
ids=list(p.slides._sldIdLst)
for el in ids:p.slides._sldIdLst.remove(el)
for no in order:p.slides._sldIdLst.append(ids[no-1])
p.part.drop_rel(ids[2].rId)
chapters=[(3,4,'제1장','서론'),(5,6,'제2장','이론적 배경'),(7,13,'제3장','YOLO-LLM 안전관제 시스템 개발'),(14,19,'제4장','연구설계 및 실증분석'),(20,22,'제5장','결론'),(23,26,'부록','질의응답 참고')]
for i,s in enumerate(p.slides,1):
 if i==1:continue
 put(get(s,13),str(i))
 if i>=3:
  _,_,label,title=next(c for c in chapters if c[0]<=i<=c[1]);put(get(s,2),label);put(get(s,10),title)
  get(s,10).width=Inches(7.5)
# Five-chapter thesis contents, using exact titles.
s=p.slides[1];clear(s);put(get(s,2),'목차');put(get(s,10),'논문 구성에 따른 발표 순서');get(s,10).width=Inches(7.5);put(get(s,11),'목차');put(get(s,12),'지정 논문 목차: 제1장부터 제5장까지 순서대로 구성')
for j,(label,title) in enumerate([(c[2],c[3]) for c in chapters[:5]]):
 y=1.8+j*.85;rect(s,.65,y,8.7,.69,'EEF3F8');rect(s,.65,y,1.15,.69,'123B78');tx(s,.84,y+.16,.9,.4,label,19,'FFFFFF',True);tx(s,2.05,y+.14,7.0,.45,title,22,'123B78',True)
tx(s,.7,6.35,8.6,.3,'부록  |  질의응답 참고자료',16,'68788B')
s.notes_slide.notes_text_frame.text='발표는 논문 목차 순서대로 진행합니다. 제1장 서론에서 연구의 필요성과 목적을 말씀드리고, 제2장에서 개념과 선행연구의 근거를 정리합니다. 제3장에서 시스템 개발과 기술평가를 설명한 뒤, 제4장에서 현장 비교의 설계와 실증 결과를 제시하겠습니다. 마지막 제5장에서 결론과 후속 과제를 말씀드리겠습니다.'
# Natural within-chapter transitions without a named WHY/HOW/WHAT framework.
extra={3:'이 문제에 대응하기 위해 무엇을 개발하고 어떤 수준에서 확인할 것인지 연구목적을 제시하겠습니다.',4:'시스템 개발과 현장 비교의 근거가 되는 개념과 선행연구를 다음 장에서 살펴보겠습니다.',7:'앞 장의 문맥 검증과 업무 지원 관점을 구현한 실제 시스템입니다. 기존 장비로 무엇을 할 수 있게 했는지부터 보겠습니다.',9:'이 자료를 바탕으로 먼저 오경보와 실제 위험 경보 누락을 함께 확인했습니다.',13:'설치와 실제 활용은 구별됩니다. 여기까지는 시스템의 개발·운용 자료였고, 다음 장에서는 두 집단의 안전관리 실효성을 같은 척도로 비교합니다.',14:'도입 현장과 미도입 현장의 현재 업무 수준에 차이가 있는지 확인하기 위해 연구모형과 가설을 설정했습니다. 조사대상과 측정·분석 방법을 차례로 설명하겠습니다.',18:'전체 실효성의 차이는 스마트기술 활용과 안전성과의 관련을 보고한 황병복(2026), 류정·박인선(2025)과 방향이 같습니다. 다만 측정지표가 달라 효과 크기를 직접 비교할 수 없습니다.',19:'앞 장의 운용실태에서 정의한 실제 알림 활용 15개 현장으로 좁혀도 방향이 유지되었습니다. 그러나 특정 기능이 이 차이를 만들었다고 해석할 수는 없습니다. 이 결과를 바탕으로 마지막 장에서 적용상의 의미와 남은 과제를 말씀드리겠습니다.',20:'지금부터는 연구 결과에서 도출한 결론과 시사점입니다. 확인한 지각 차이를 실제 관리 성과로 이어가기 위한 운영 제안을 구분하여 설명하겠습니다.'}
for i,s in enumerate(p.slides,1):
 tf=s.notes_slide.notes_text_frame;text=tf.text
 # Remove old explicit sequencing comments and obsolete cross-slide language.
 text='\n'.join(line for line in text.splitlines() if not re.search(r'WHY|HOW|WHAT',line))
 text=text.replace('경보 후보의 정확성 외에, 관리자 업무 실효성은 별도 현장조사로 비교했습니다. 다음 슬라이드부터 그 비교 설계를 설명합니다.','')
 text=text.replace('앞서 정의한 실제 알림 활용 15개 현장으로 좁혀도 차이의 방향은 같았습니다.','')
 tf.text=text+('\n'+extra[i] if i in extra else '')
put(get(p.slides[18],11),'보완분석에서도 차이의 방향은 유지되었다')
put(get(p.slides[18],18),'지각 실효성의 차이는 유지 · 인과효과나 개별 기능의 효과는 확인하지 않음')
# Validate text-level scope and section order before saving.
texts=[]
for s in p.slides:
 texts.append(s.notes_slide.notes_text_frame.text)
 for sh in s.shapes:
  if sh.has_text_frame:texts.append(sh.text)
  if sh.has_table:texts.extend(c.text for row in sh.table.rows for c in row.cells)
joined='\n'.join(texts)
assert not re.search(r'\b(?:WHY|HOW|WHAT)\b|A-9|지시 전달 소요시간|과정지표',joined,re.I)
assert len(p.slides)==26
assert hashlib.sha256(src.read_bytes()).hexdigest()==h
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_논문목차순.pptx';assert not out.exists();p.save(out)
r=dict(source_pptx=str(src.resolve()),source_sha256=h,source='00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx',output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=26,main_slides=22,appendix_slides=4,chapter_ranges=[list(c) for c in chapters],checks=[{'chapter_titles_verified_in_thesis_dump':[63,68,86,109,130]},{'explicit_why_how_what_removed':True},{'a9_removed':True}],figure_usage=[{'slide':7,'source':'그림3-4','type':'original'},{'slide':8,'source':'그림3-1','type':'original'},{'slide':12,'source':'그림3-6','type':'original'},{'slide':14,'source':'그림4-1','type':'original'},{'slide':6,'source':'표2-4','type':'presentation table'},{'slide':10,'source':'표3-7','type':'presentation chart'},{'slide':18,'source':'표4-12','type':'presentation chart'},{'slide':19,'source':'표4-13','type':'presentation table'}],theory_source_idxs=[297,298,299,303,304,370,371,468,469,475,476,478,479,481,482,484,485],limitations=[])
(B/'chapter_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
