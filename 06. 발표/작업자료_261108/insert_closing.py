from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from copy import deepcopy
from zoneinfo import ZoneInfo
import json,hashlib,datetime,win32com.client
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1457_윤혁_석사학위논문_심의발표_결론성과보강.pptx';h=hashlib.sha256(src.read_bytes()).hexdigest();p=Presentation(src)
def snap(sl):
 e=deepcopy(sl._element)
 for sh in list(e):pass
 # Compare all shape elements except page-number shape.
 return [str(s._element.xml) for s in sl.shapes if s.shape_id!=13]
before=[snap(s) for s in p.slides];notes=[str(s.notes_slide._element.xml) for s in p.slides]
assert len(p.slides)==33
assert next(s.text for s in p.slides[29].shapes if s.shape_id==2)=='부록'
t=p.slides[28];s=p.slides.add_slide(t.slide_layout)
for x in list(s.shapes):x._element.getparent().remove(x._element)
# Keep only footer number; slide layout/master provides school mark and top line.
for x in t.shapes:
 if x.shape_id==13:s.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
def tx(x,y,w,h,text,size,color,bold):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.text=text
 from pptx.enum.text import PP_ALIGN
 for q in tf.paragraphs:
  q.alignment=PP_ALIGN.CENTER
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
tx(1,2.7,8,1,'감사합니다.',44,'123B78',True);tx(1,4.0,8,.6,'질의응답',27,'218C9E',False)
s.notes_slide.notes_text_frame.text='발표를 마치겠습니다. 감사합니다. 질문에 답변드리겠습니다.'
ids=p.slides._sldIdLst;el=ids[-1];ids.remove(el);ids.insert(29,el)
for i,sl in enumerate(p.slides,1):
 if i<30:continue
 sh=next(x for x in sl.shapes if x.shape_id==13);tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=str(i)
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=str(i)
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
for old in range(33):
 new=old if old<29 else old+1
 assert snap(p.slides[new])==before[old],old
 assert str(p.slides[new].notes_slide._element.xml)==notes[old],old
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_마무리추가.pptx';assert not out.exists();p.save(out)
app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(str(out.resolve()),ReadOnly=True,Untitled=False,WithWindow=False);assert d.Slides.Count==34
issues=[]
for sh in d.Slides(30).Shapes:
 if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append(sh.Id)
d.Slides(30).Export(str((B/'closing_slide_30.png').resolve()),'PNG',1200,900);d.Close();assert not issues
assert hashlib.sha256(src.read_bytes()).hexdigest()==h
q=Presentation(out);assert [next(x.text for x in sl.shapes if x.shape_id==13) for sl in list(q.slides)[1:]]==list(map(str,range(2,35)))
assert next(x.text for x in q.slides[30].shapes if x.shape_id==2)=='부록'
assert not out.with_suffix('.pdf').exists()
r=dict(source_pptx=str(src.resolve()),source_sha256=h,output_pptx=str(out.resolve()),slide_count=34,closing_slide=30,appendix_start=31,checks=[{'original_slide_content_design_notes_preserved_except_page_numbers':True},{'powerpoint_open':34},{'closing_slide_overflow':issues},{'continuous_page_numbers':'2–34'},{'source_hash_unchanged':True},{'png_direct_export':True},{'pdf_created':False}]);(B/'closing_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
