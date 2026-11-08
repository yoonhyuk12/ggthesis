from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from copy import deepcopy
from zoneinfo import ZoneInfo
from zipfile import ZipFile
from PIL import Image
import json,hashlib,datetime,win32com.client
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1526_윤혁_석사학위논문_심의발표_실제알림추가.pptx';hw=R.parent/'00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx'
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();hashes={str(f):h(f) for f in (src,hw)}
z=ZipFile(hw);assets={}
for key in ['image5','image6']:
 name=next(n for n in z.namelist() if n.startswith('BinData/'+key+'.'));f=B/('split_'+Path(name).name);f.write_bytes(z.read(name));assets[key]=f
p=Presentation(src);assert len(p.slides)==35
snap=lambda s:[str(x._element.xml) for x in s.shapes if x.shape_id!=13]
before=[snap(s) for s in p.slides];notes=[str(s.notes_slide._element.xml) for s in p.slides]
s=p.slides[11];new=p.slides.add_slide(s.slide_layout)
for x in list(new.shapes):x._element.getparent().remove(x._element)
for x in s.shapes:
 if x.shape_id in (2,10,11,12,13):new.shapes._spTree.insert_element_before(deepcopy(x._element),'p:extLst')
for x in list(s.shapes):
 if x.shape_id not in (2,10,11,12,13):x._element.getparent().remove(x._element)
def replace(sh,text):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def label(sl,id,text):replace(next(x for x in sl.shapes if x.shape_id==id),text)
def tx(sl,x,y,w,hh,text,size,color='34465A',bold=False):
 sh=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(hh));tf=sh.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.text=text
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
label(s,11,'여러 현장의 영상을 한 화면에서 확인한다');label(s,12,'논문 <그림 3-5> 시스템 PC 설치 화면 · 담당자 정보 화면 가림')
im=Image.open(assets['image6']);W,H=im.size;ix,iy,iw=1.05,1.8,7.9;ih=iw*H/W
s.shapes.add_picture(str(assets['image6']),Inches(ix),Inches(iy),width=Inches(iw),height=Inches(ih))
# Camera name strips and bottom alert ticker contain names. Mask visually without modifying source pixels.
for yy in [210,450,690,930,1170]:
 sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(ix),Inches(iy+yy/1249*ih),Inches(iw),Inches(30/1249*ih));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string('30383D');sh.line.fill.background()
# Final ticker below the grid.
sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(ix),Inches(iy+1205/1249*ih),Inches(iw),Inches(44/1249*ih));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string('30383D');sh.line.fill.background()
tx(s,.85,1.48,8.4,.3,'카메라 영상을 격자로 배치하고, 필요한 영상을 선택해 확인',15)
s.notes_slide.notes_text_frame.text='논문 그림 3-5에 실린 실제 멀티뷰 화면입니다. 여러 카메라 영상을 격자로 배치하고 필요한 카메라를 선택해 개별 영상을 확인합니다. 화면의 담당자 정보는 발표용 도형으로 가렸습니다. 원본 그림 자체는 수정하지 않았습니다.'
label(new,11,'검출 장면과 판정 사유를 보고 오판을 교정한다');label(new,12,'논문 <그림 3-4> 시스템 운영 화면 · LLM 판정 교정 창 확대')
W,H=Image.open(assets['image5']).size
pic=new.shapes.add_picture(str(assets['image5']),Inches(.8),Inches(1.65),width=Inches(4.85),height=Inches(5.08));pic.crop_left=577/1919;pic.crop_right=(1919-1303)/1919
# Central native crop keeps actual screenshot, enlarging the correction controls.
tx(new,6.02,2.4,3.35,.9,'장면과 사유 확인',23,'123B78',True);tx(new,6.02,3.1,3.3,.9,'검출 영상과\nLLM 판정 사유 확인',19)
tx(new,6.02,4.55,3.35,.7,'사용자 교정 등록',23,'123B78',True);tx(new,6.02,5.2,3.3,1.0,'실제 판정과 사유를\n입력해 교정 사례 저장',19)
new.notes_slide.notes_text_frame.text='논문 그림 3-4의 중앙 LLM 판정 교정 창을 확대한 화면입니다. 사용자는 알림 이력에서 검출 영상과 판정 사유를 확인한 뒤 실제 판정과 사용자 사유를 입력하여 오판 사례를 교정할 수 있습니다. 이는 카메라별 사용자 교정 샘플 등록 절차를 구현한 화면입니다. 사건 판정과 발송 이력은 담당자의 열람이나 시정 완료 기록과 구별합니다. 근거 문단 idx809,814.'
ids=p.slides._sldIdLst;el=ids[-1];ids.remove(el);ids.insert(12,el)
for i,sl in enumerate(p.slides,1):
 if i>=13:label(sl,13,str(i))
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_멀티뷰교정분리.pptx';assert not out.exists();p.save(out)
q=Presentation(out)
for old in range(35):
 if old==11:continue
 newidx=old if old<12 else old+1
 assert snap(q.slides[newidx])==before[old],old
 assert str(q.slides[newidx].notes_slide._element.xml)==notes[old],old
assert [next(x.text for x in sl.shapes if x.shape_id==13) for sl in list(q.slides)[1:]]==list(map(str,range(2,37)))
app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(str(out.resolve()),ReadOnly=True,Untitled=False,WithWindow=False);assert d.Slides.Count==36;issues=[]
for no in (12,13):
 for sh in d.Slides(no).Shapes:
  if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append([no,sh.Id])
 d.Slides(no).Export(str((B/f'split_screen_{no}.png').resolve()),'PNG',1600,1200)
d.Close();assert not issues,issues;assert all(h(Path(f))==v for f,v in hashes.items())
r=dict(source=str(src.resolve()),output_pptx=str(out.resolve()),slide_count=36,source_hashes=hashes,changes=[{'slide':12,'source':'그림 3-5 / BinData image6','source_idxs':[818,822],'description':'실제 멀티뷰 전체 화면'},{'slide':13,'source':'그림 3-4 / BinData image5','source_idxs':[809,811,814],'description':'중앙 LLM 판정 교정 창 확대'}],checks={'powerpoint_open':True,'overflow':issues,'other_slide_content_design_notes_preserved':True,'continuous_numbers':'2–36','source_hashes_unchanged':True,'pdf_created':False},limitations=['담당자 이름 가림은 PPT 도형에 의한 화면상 가림이며 원본 이미지 픽셀은 PPT 내부에 남아 있음.'])
(B/'split_screen_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out)

