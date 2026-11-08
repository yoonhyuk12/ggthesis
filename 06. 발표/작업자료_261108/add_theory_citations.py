from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from zoneinfo import ZoneInfo
import hashlib,json,datetime,win32com.client
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1508_윤혁_석사학위논문_심의발표_마무리추가.pptx';digest=hashlib.sha256(src.read_bytes()).hexdigest();p=Presentation(src);before=[(str(s._element.xml),str(s.notes_slide._element.xml)) for s in p.slides]
s=p.slides[8];citations=[{'theory':'경보 피로도','citation':'(Cvach, 2012)','idx':297,'x':.83},{'theory':'신호감지이론','citation':'(Green & Swets, 1966)','idx':304,'x':3.83},{'theory':'기술수용모델','citation':'(Davis, 1989)','idx':303,'x':6.83}]
for c in citations:
 sh=s.shapes.add_textbox(Inches(c['x']),Inches(3.01),Inches(2.34),Inches(.3));tf=sh.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=False;tf.text=c['citation']
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(14);rr.font.color.rgb=RGBColor.from_string('68788B')
s.notes_slide.notes_text_frame.text+='\n이론별 출처: 경보 피로도(Cvach, 2012), 신호감지이론(Green & Swets, 1966), 기술수용모델(Davis, 1989). 지정 논문 제2장 제1·2절의 근거를 따랐습니다.'
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_이론출처표기.pptx';assert not out.exists();p.save(out)
q=Presentation(out)
for i,t in enumerate(q.slides):
 if i!=8:assert (str(t._element.xml),str(t.notes_slide._element.xml))==before[i],i+1
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(str(out.resolve()),ReadOnly=True,Untitled=False,WithWindow=False);assert d.Slides.Count==34;issues=[]
for sh in d.Slides(9).Shapes:
 if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append(sh.Id)
d.Slides(9).Export(str((B/'citations_slide_09.png').resolve()),'PNG',1200,900);d.Close();assert not issues
assert not out.with_suffix('.pdf').exists()
r=dict(source_pptx=str(src.resolve()),source_sha256=digest,output_pptx=str(out.resolve()),slide_count=34,citations=citations,checks=[{'source_hash_unchanged':True},{'other_33_slides_notes_xml_identical':True},{'powerpoint_open_slides':34},{'slide9_height_overflow':issues},{'pdf_created':False},{'direct_png_export':True}]);(B/'citations_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
