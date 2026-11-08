from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from zoneinfo import ZoneInfo
from copy import deepcopy
import json,datetime,hashlib,re
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1430_윤혁_석사학위논문_심의발표_논문목차순.pptx';p=Presentation(src);digest=hashlib.sha256(src.read_bytes()).hexdigest()
def content(s):
 a=[]
 for x in s.shapes:
  if x.shape_id==13:continue
  if x.has_text_frame:a.append(('text',x.shape_id,x.text))
  if x.has_table:a.append(('table',x.shape_id,[[c.text for c in row.cells] for row in x.table.rows]))
  if x.shape_type==13:a.append(('image',x.shape_id,hashlib.sha256(x.image.blob).hexdigest()))
 return a
before=[content(s) for s in p.slides];notes=[s.notes_slide.notes_text_frame.text for s in p.slides];oldids=list(p.slides._sldIdLst)
def put(sh,text):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def tx(s,x,y,w,h,t,size,color='123B78',bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=True;tf.text=t
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return sh
def rect(s,x,y,w,h,color):
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(color);sh.line.fill.background()
chapters=[(3,'제1장','서론'),(5,'제2장','이론적 배경'),(7,'제3장','YOLO-LLM 안전관제 시스템 개발'),(14,'제4장','연구설계 및 실증분석'),(20,'제5장','결론')];newids={}
for oldstart,label,title in chapters:
 template=p.slides[oldstart-1];s=p.slides.add_slide(template.slide_layout)
 for x in list(s.shapes):x._element.getparent().remove(x._element)
 # Reuse thesis deck section strip, source line and page-number shape.
 for x in template.shapes:
  if x.shape_id in [2,10,12,13]:s.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
 put(next(x for x in s.shapes if x.shape_id==12),'')
 rect(s,.72,2.35,.1,2.1,'218C9E')
 tx(s,1.12,2.25,7.8,.7,label,28,'218C9E',True)
 display=title if oldstart!=7 else 'YOLO-LLM 안전관제\n시스템 개발'
 tx(s,1.1,3.18,8.2,1.65,display,38,'123B78',True)
 rect(s,1.12,5.35,7.7,.025,'DCE5EF')
 s.notes_slide.notes_text_frame.text=f'{label} {title}입니다.'
 newids[oldstart]=p.slides._sldIdLst[-1]
ids=p.slides._sldIdLst
for el in list(ids):ids.remove(el)
mapold={};dividers=[]
for oldno,el in enumerate(oldids,1):
 if oldno in newids:
  ids.append(newids[oldno]);dividers.append(len(ids))
 ids.append(el);mapold[oldno]=len(ids)
for i,s in enumerate(p.slides,1):
 if i>1:put(next(x for x in s.shapes if x.shape_id==13),str(i))
for oldno,newno in mapold.items():
 assert content(p.slides[newno-1])==before[oldno-1],(oldno,newno)
 assert p.slides[newno-1].notes_slide.notes_text_frame.text==notes[oldno-1]
assert len(p.slides)==31
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_장구분추가.pptx';assert not out.exists();p.save(out)
r=dict(source_pptx=str(src.resolve()),source_sha256=digest,output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=31,main_slides=27,appendix_slides=4,divider_slides=dividers,old_to_new=mapold,checks=[{'existing_slide_content_notes_images_preserved':True},{'source_hash_unchanged':True}],limitations=[])
(B/'divider_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out);print(dividers)
