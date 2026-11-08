from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from copy import deepcopy
from zoneinfo import ZoneInfo
import json,hashlib,datetime,win32com.client
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1517_윤혁_석사학위논문_심의발표_이론설명수정.pptx';img=R.parent/'02.reference/KakaoTalk_20261108_152245822.jpg'
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
hashes={str(f):h(f) for f in (src,img)};p=Presentation(src);assert len(p.slides)==34
snap=lambda s:[str(x._element.xml) for x in s.shapes if x.shape_id!=13]
before=[snap(s) for s in p.slides];notes=[str(s.notes_slide._element.xml) for s in p.slides]
t=p.slides[12];s=p.slides.add_slide(t.slide_layout)
for x in list(s.shapes):x._element.getparent().remove(x._element)
for x in t.shapes:
 if x.shape_id in (2,10,11,12,13):s.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
def replace(sh,text):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
replace(next(x for x in s.shapes if x.shape_id==11),'실제 위험 알림 수신 사례')
replace(next(x for x in s.shapes if x.shape_id==12),'실제 알림 수신 화면 (사용자 제공)')
# Coordinates below refer to the proportional 945 x 2048 display of the source.
x0,x1,y0,y1=133,763,375,1670
ix,iy,ih=.95,1.62,5.08;iw=(x1-x0)/(y1-y0)*ih
pic=s.shapes.add_picture(str(img),Inches(ix),Inches(iy),width=Inches(iw),height=Inches(ih))
pic.crop_left=x0/945;pic.crop_right=(945-x1)/945;pic.crop_top=y0/2048;pic.crop_bottom=(2048-y1)/2048
# Opaque visual redaction in the presentation; embedded original image is retained.
for a,b,c,d in [(148,925,710,982),(148,1035,721,1089),(148,1506,721,1612)]:
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(ix+(a-x0)/(x1-x0)*iw),Inches(iy+(b-y0)/(y1-y0)*ih),Inches((c-a)/(x1-x0)*iw),Inches((d-b)/(y1-y0)*ih));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor(255,255,255);sh.line.fill.background()
def tx(x,y,w,hh,text,size,color='123B78',bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(hh));tf=sh.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.text=text
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return sh
for yy,num,title,body in [(2.05,'01','위험 장면과 탐지 내용','위험 스냅샷과 탐지 항목을\n한 화면에서 확인'),(3.55,'02','2차 판정과 판단 사유','시스템의 판정 결과와\n그 이유를 함께 전달'),(5.05,'03','담당자 확인·연락 지원','담당자가 상황을 확인하고\n연락할 수 있도록 정보 제공')]:
 tx(4.05,yy,.5,.4,num,19,'218C9E',True);tx(4.65,yy,4.5,.48,title,22,bold=True);tx(4.65,yy+.56,4.5,.8,body,18,'34465A')
s.notes_slide.notes_text_frame.text='사용자가 제공한 실제 알림 수신 화면입니다. 위험 장면과 탐지 내용, 시스템의 2차 판정 및 사유, 담당자 연락 정보를 함께 전달하는 예입니다. 화면의 정탐 표시는 시스템이 출력한 판정이며 독립 평가자의 정답 검증 결과를 뜻하지 않습니다. 이 한 건은 실제 운영 예시이며 논문의 기술성능 평가 표본에 추가하지 않습니다. 표시된 모델과 논문 평가 시점의 시스템 버전이 같다고 전제하지 않습니다. 담당자 이름과 전화번호는 발표 화면에서 도형으로 가렸습니다.'
ids=p.slides._sldIdLst;el=ids[-1];ids.remove(el);ids.insert(13,el)
for i,sl in enumerate(p.slides,1):
 if i>=14:replace(next(x for x in sl.shapes if x.shape_id==13),str(i))
for old in range(34):
 new=old if old<13 else old+1
 assert snap(p.slides[new])==before[old],old
 assert str(p.slides[new].notes_slide._element.xml)==notes[old],old
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_실제알림추가.pptx';assert not out.exists();p.save(out)
app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(str(out.resolve()),ReadOnly=True,Untitled=False,WithWindow=False);assert d.Slides.Count==35
issues=[]
for sh in d.Slides(14).Shapes:
 if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append(sh.Id)
png=B/'actual_alert_slide14.png';d.Slides(14).Export(str(png.resolve()),'PNG',1600,1200);d.Close();assert not issues,issues
q=Presentation(out)
for old in range(34):
 new=old if old<13 else old+1
 assert snap(q.slides[new])==before[old],old
 assert str(q.slides[new].notes_slide._element.xml)==notes[old],old
assert [next(x.text for x in sl.shapes if x.shape_id==13) for sl in list(q.slides)[1:]]==list(map(str,range(2,36)))
assert all(h(Path(f))==v for f,v in hashes.items())
r=dict(source_pptx=str(src.resolve()),source_hashes=hashes,output_pptx=str(out.resolve()),slide_count=35,inserted_slide=14,checks={'powerpoint_open':True,'original_slides_design_text_notes_preserved_except_numbers':True,'continuous_numbers':'2–35','source_pptx_and_image_unchanged':True,'overflow':issues,'png_direct_export':str(png.resolve()),'pdf_created':False},limitations=['가림은 PPT 불투명 도형을 통한 발표 화면상 표시이며 원본 이미지의 개인정보 픽셀은 PPT 내부 미디어에 남아 있음.','실제 운영 예시 1건으로 기술평가 표본이나 독립 정답 검증 자료가 아님.'])
(B/'actual_alert_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
