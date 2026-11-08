from pathlib import Path
from copy import deepcopy
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from zoneinfo import ZoneInfo
import json,datetime,hashlib
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1416_윤혁_석사학위논문_심의발표_스토리재구성.pptx';p=Presentation(src);source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
def content(sl):
 out=[]
 for x in sl.shapes:
  if x.shape_id==13:continue
  if x.has_text_frame:out.append(('text',x.shape_id,x.text))
  if x.has_table:out.append(('table',x.shape_id,[[c.text for c in row.cells] for row in x.table.rows]))
  if x.shape_type==13:out.append(('image',x.shape_id,hashlib.sha256(x.image.blob).hexdigest()))
 return out
before=[content(s) for s in p.slides];notes=[s.notes_slide.notes_text_frame.text for s in p.slides]
template=p.slides[1];sl=p.slides.add_slide(template.slide_layout)
for x in list(sl.shapes):x._element.getparent().remove(x._element)
for x in template.shapes:
 if x.shape_id in [2,10,11,12,13]:sl.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
ids=p.slides._sldIdLst;new=ids[-1];ids.remove(new);ids.insert(1,new)
def put(sh,text):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def obj(id):return next(x for x in sl.shapes if x.shape_id==id)
put(obj(2),'목차');put(obj(10),'발표 순서');put(obj(11),'목차');put(obj(12),'WHY → HOW → WHAT');put(obj(13),'2')
def tx(x,y,w,h,t,size=20,color='172537',bold=False):
 s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=s.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
 tf.text=t
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return s
def rect(x,y,w,h,col):
 s=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(col);s.line.fill.background()
for y,num,eng,title,sub in [(1.9,'01','WHY','연구 배경과 필요성','현장의 문제와 연구 질문'),(3.22,'02','HOW','시스템 개발과 연구 방법','시스템 구현과 두 평가의 설계'),(4.54,'03','WHAT','연구 결과와 결론','기술·현장 비교 결과, 의미와 한계')]:
 rect(.65,y,8.7,1.08,'EEF3F8');rect(.65,y,1.6,1.08,'123B78');tx(.85,y+.12,1.2,.33,eng,18,'FFFFFF',True);tx(.85,y+.57,1.2,.32,num,16,'FFFFFF');tx(2.55,y+.16,6.3,.42,title,24,'123B78',True);tx(2.55,y+.66,6.3,.30,sub,16,'68788B')
tx(.7,6.2,8.6,.35,'부록  |  질의응답 참고자료',16,'68788B')
sl.notes_slide.notes_text_frame.text='발표는 WHY, HOW, WHAT 순서로 진행합니다. 연구의 배경과 필요성을 먼저 설명하고, 시스템 개발과 연구 방법을 제시한 뒤, 연구 결과와 결론을 말씀드리겠습니다. 세부 검증 자료는 부록에 두었습니다.'
for i,s in enumerate(p.slides,1):
 if i==1:continue
 f=next((x for x in s.shapes if x.shape_id==13),None)
 if f is not None:put(f,str(i))
assert len(p.slides)==25
for oldno in range(24):
 newno=oldno if oldno==0 else oldno+1
 assert content(p.slides[newno])==before[oldno],(oldno,newno)
 assert p.slides[newno].notes_slide.notes_text_frame.text==notes[oldno]
assert hashlib.sha256(src.read_bytes()).hexdigest()==source_hash
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_스토리재구성.pptx';assert not out.exists();p.save(out)
r=dict(source_pptx=str(src.resolve()),source_sha256=source_hash,output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=25,main_slides=21,appendix_slides=4,checks=[{'original_slide_content_and_notes_unchanged_except_page_number':True},{'source_hash_unchanged':True},{'page_number_sequence':list(range(2,26))}],limitations=[])
(B/'toc_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
