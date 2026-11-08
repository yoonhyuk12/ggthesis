from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from zoneinfo import ZoneInfo
import hashlib,json,datetime
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1442_윤혁_석사학위논문_심의발표_서론결론수정.pptx';digest=hashlib.sha256(src.read_bytes()).hexdigest();p=Presentation(src)
before={i:{'slide_xml':str(s._element.xml),'notes_xml':str(s.notes_slide._element.xml)} for i,s in enumerate(p.slides,1)}
def obj(s,id):return next(x for x in s.shapes if x.shape_id==id)
def put(sh,t):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=t
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=t
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def clear(s):
 for sh in list(s.shapes):
  if sh.shape_id not in [2,10,11,12,13]:sh._element.getparent().remove(sh._element)
def tx(s,x,y,w,h,t,size=20,color='172537',bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=True
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=line;q.space_after=Pt(5)
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return sh
def rect(s,x,y,w,h,color):
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background()
def foot(s,t):rect(s,.56,6.18,8.88,.58,'FBF3E7');tx(s,.73,6.27,8.5,.4,t,15,'A9651B',True)
# Target-only update from user's current disk copy. No regeneration of other slides.
s=p.slides[26];clear(s);put(obj(s,11),'이번 연구는 시스템 개발과 두 가지 검증을 연결했다');put(obj(s,12),'논문 제5장 결론 · 제3장 <표 3-7> · 제4장 <표 4-12>')
for x,label,title,body in [(.65,'개발 성과','기존 장비로 구현','CCTV와 범용 PC 활용\n영상관제·위험 판단\n담당자 알림을 연결'),(3.65,'기술 평가','오경보 834→13건','특이도 98.4%\n실제 위험 44건 중\n39건의 경보 유지'),(6.65,'현장 비교','업무 평가 +0.54점','여섯 특성 조정 후\n도입 현장 점수가 높음\np=.005')]:
 rect(s,x,2.1,2.7,3.65,'EEF3F8');tx(s,x+.18,2.3,2.34,.4,label,17,'218C9E',True);tx(s,x+.18,3.02,2.34,.8,title,22,'123B78',True);tx(s,x+.18,4.08,2.34,1.4,body,18)
foot(s,'기술 선별성능과 관리자 평가를 함께 제시 · 사고 감소나 인과효과를 뜻하지는 않음')
s.notes_slide.notes_text_frame.text='이번 연구의 성과는 세 가지입니다. 첫째, 기존CCTV와 범용PC를 활용해 영상관제,위험판단,담당자알림을 연결하는 시스템을 구현했습니다. 둘째,운영 경보후보878건에서 오경보가834건에서13건으로 줄어 특이도98.4%를 확인했고,실제위험44건중39건은경보로남았습니다. 실제위험5건의경보가누락된한계도함께확인했습니다. 셋째,같은기관의도입·미도입73개현장에같은척도를적용해여섯특성조정후도입현장의안전관리업무평가가0.54점높다는결과를확인했습니다. 기술성능평가와현장비교를연결한것이이번연구의성과입니다. 사고감소나도입의인과효과를입증한것은아닙니다.'
# A single principal limitation, corresponding exactly to thesis paragraph1699.
s=p.slides[27];clear(s);put(obj(s,11),'한계: 같은 현장의 도입 전후 변화를 비교하지 못했다');put(obj(s,12),'논문 제5장 결론 · 연구의 한계')
rect(s,.8,2.2,8.4,3.25,'EEF3F8');tx(s,1.12,2.55,7.75,.8,'두 집단을 한 시점에 한 번 조사했다.',28,'123B78',True)
tx(s,1.12,3.75,7.75,1.15,'도입 전부터 차이가 있었는지,\n도입 뒤 무엇이 달라졌는지는 확인하지 못했다.',24)
foot(s,'도입 현장의 현재 평가가 더 높았다는 결과와, 도입 후 개선되었다는 주장은 다름')
s.notes_slide.notes_text_frame.text='핵심한계는같은현장을도입전과후로비교하지못했다는점입니다. 도입현장과미도입현장을한시점에한번조사했기때문에도입전부터두집단에차이가있었는지,도입뒤무엇이달라졌는지는알수없습니다. 따라서이번결과는현재의집단차이를뜻하며도입후개선되었다는뜻은아닙니다.'
# All future directions on one slide.
s=p.slides[28];clear(s);put(obj(s,11),'향후 연구는 변화와 실제 조치, 성능·비용을 확인해야 한다');put(obj(s,12),'논문 제5장 결론 · 향후 연구 방향')
for x,label,title,body in [(.65,'연구 설계','같은 현장을 반복 조사','도입 전후 비교\n다른 기관·공종 확대\n표본 수를 미리 산정'),(3.65,'현장 성과','실제 조치와 연결','알림 기록과\n시정·작업중지 기록\n사고 기록을 함께 확인'),(6.65,'기술 검증','전체 성능·비용 비교','처음 놓친 위험도 평가\n같은 조건에서\n상용 관제와 비교')]:
 rect(s,x,2.05,2.7,3.65,'EEF3F8');tx(s,x+.18,2.25,2.34,.4,label,17,'218C9E',True);tx(s,x+.18,2.94,2.34,.8,title,21,'123B78',True);tx(s,x+.18,4.03,2.34,1.4,body,18)
tx(s,.7,6.25,8.6,.45,'감사합니다 · 질의응답',22,'123B78',True)
s.notes_slide.notes_text_frame.text='향후연구는세방향으로진행할필요가있습니다. 먼저필요한표본수를미리산정하고다른기관과공종으로대상을넓히며같은현장을도입전후로반복조사해야합니다. 다음으로알림기록을실제시정·작업중지조치및사고기록과연결해확인해야합니다. 마지막으로YOLO가처음부터놓친위험까지포함한전체탐지성능을평가하고,같은조건에서상용AI관제솔루션과성능및비용을비교할필요가있습니다.'
# Existing user changes and all other slide/notes XML must remain byte-identical in memory.
for i,s in enumerate(p.slides,1):
 if i not in [27,28,29]:
  assert str(s._element.xml)==before[i]['slide_xml'],i
  assert str(s.notes_slide._element.xml)==before[i]['notes_xml'],i
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_결론성과보강.pptx';assert not out.exists();p.save(out)
# Verify persisted slide XML and notes rather than relying only on extracted text.
q=Presentation(out)
for i,s in enumerate(q.slides,1):
 if i not in [27,28,29]:
  assert str(s._element.xml)==before[i]['slide_xml'],i
  assert str(s.notes_slide._element.xml)==before[i]['notes_xml'],i
r=dict(source_pptx=str(src.resolve()),source_sha256=digest,output_pptx=str(out.resolve()),slide_count=len(q.slides),changed_slides=[27,28,29],source_idxs={'achievements':[1693,1695,1696],'limitation':[1699],'future':[1700]},checks=[{'other_slides_and_notes_xml_exactly_preserved':True},{'user_edited_slides_16_23_preserved':True},{'source_hash_unchanged':True},{'pdf_generation':False}],limitations=[])
(B/'conclusion_only_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
