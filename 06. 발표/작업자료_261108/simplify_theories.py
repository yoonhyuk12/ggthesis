from pathlib import Path
from pptx import Presentation
from pptx.util import Pt,Inches
from zoneinfo import ZoneInfo
import datetime,hashlib,json,win32com.client
B=Path(__file__).resolve().parent;R=B.parent;src=R/'261108_1512_윤혁_석사학위논문_심의발표_이론출처표기.pptx';digest=hashlib.sha256(src.read_bytes()).hexdigest();p=Presentation(src);before=[(str(s._element.xml),str(s.notes_slide._element.xml)) for s in p.slides]
values={16:'불필요한 경보가 자주 울리면, 중요한 경보에도 주의를 덜 기울일 수 있다.',19:'위험 판단 기준에 따라 미탐과 오탐 사이에 상충관계가 생기므로, 두 오류를 함께 평가해야 한다.',22:'사용자가 도움이 된다고 느끼고 쓰기 편해야, 시스템을 받아들이고 사용하려 한다.'}
s=p.slides[8]
for sid,text in values.items():
 sh=next(x for x in s.shapes if x.shape_id==sid);tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=text
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=text
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
 sh.height=Inches(2.0)
 for q in tf.paragraphs:
  for rr in q.runs:rr.font.size=Pt(17)
s.notes_slide.notes_text_frame.text='경보 피로도는 불필요한 경보가 자주 울리면 중요한 경보에도 주의를 덜 기울일 수 있다는 설명입니다(Cvach, 2012). 신호감지이론은 위험 판단 기준에 따라 미탐과 오탐 사이에 상충관계가 생기므로 두 오류를 함께 평가해야 한다는 설명입니다(Green & Swets, 1966). 이는 같은 탐지성능에서 판단 기준을 조정할 때의 상충관계를 뜻하며, 탐지기술이 개선되어 두 오류가 함께 줄어드는 가능성을 부정하는 뜻은 아닙니다. 기술수용모델은 사용자가 도움이 된다고 느끼고 쓰기 편해야 시스템을 받아들이고 사용하려 한다는 설명입니다(Davis, 1989). 세 이론은 본 논문의 시스템 설계와 경험 척도의 근거이며, 하나의 인과모형으로 검증한 것은 아닙니다.'
assert all(c in '\n'.join(x.text for x in s.shapes if x.has_text_frame) for c in ['(Cvach, 2012)','(Green & Swets, 1966)','(Davis, 1989)'])
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_이론설명수정.pptx';assert not out.exists();p.save(out)
q=Presentation(out)
for i,sl in enumerate(q.slides):
 if i!=8:assert (str(sl._element.xml),str(sl.notes_slide._element.xml))==before[i],i+1
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
app=win32com.client.Dispatch('PowerPoint.Application');d=app.Presentations.Open(str(out.resolve()),ReadOnly=True,Untitled=False,WithWindow=False);issues=[]
for sh in d.Slides(9).Shapes:
 if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append({'shape':sh.Id,'height':sh.Height,'bound':sh.TextFrame2.TextRange.BoundHeight})
d.Slides(9).Export(str((B/'theory_easy_slide09.png').resolve()),'PNG',1200,900);d.Close()
r=dict(source_pptx=str(src.resolve()),source_sha256=digest,output_pptx=str(out.resolve()),slide_count=len(q.slides),changed_slide=9,agreed_signal_detection=values[19],checks=[{'other33_slides_notes_xml_identical':True},{'source_hash_unchanged':True},{'citations_preserved':['(Cvach, 2012)','(Green & Swets, 1966)','(Davis, 1989)']},{'powerpoint_open':True},{'height_overflow':issues},{'direct_png_export':True},{'pdf_created':False}]);(B/'theory_easy_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(out);print(issues)
