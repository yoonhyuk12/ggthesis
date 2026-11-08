from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
from zoneinfo import ZoneInfo
import json,datetime
B=Path(__file__).resolve().parent;R=B.parent
r=json.loads((B/'verification.json').read_text(encoding='utf-8'));p=Presentation(r['output_pptx']);changes=json.loads((B/'story_changes.json').read_text(encoding='utf-8'))
def obj(no,id):return next(s for s in p.slides[no-1].shapes if s.shape_id==id)
def put(s,t):
 tf=s.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=t
  for rr in list(q.runs)[1:]:rr.text=''
 else:q.text=t
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def tx(sl,x,y,w,h,t,size=20,color='172537',bold=False):
 s=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=s.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=0;tf.margin_top=tf.margin_bottom=0
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if not i else tf.add_paragraph();q.text=line;q.space_after=Pt(5)
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor.from_string(color)
 return s

def clear(n):
 s=p.slides[n-1]
 for sh in list(s.shapes):
  if sh.shape_id not in [2,10,11,12,13]:sh._element.getparent().remove(sh._element)
 return s

def pic(sl,n,x,y,w,h):
 path=B/f'thesis_image{n}.png';iw,ih=Image.open(path).size;k=min(w/iw,h/ih);ww=iw*k;hh=ih*k;return sl.shapes.add_picture(str(path),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),Inches(ww),Inches(hh))
# The original thesis diagrams are preserved as source images.
s=clear(6);pic(s,2,.55,1.65,5.3,4.95)
tx(s,6.1,2.05,3.25,.65,'1차: 위험 후보 탐지',21,'123B78',True)
tx(s,6.1,2.8,3.25,1.05,'기존 CCTV 영상에서\nYOLO가 후보를 찾음',20)
tx(s,6.1,4.05,3.25,.65,'2차: 장면 문맥 검증',21,'123B78',True)
tx(s,6.1,4.8,3.25,1.2,'LLM이 다시 판단해\n알림 전송 또는 제외\n확인·조치는 관리자 수행',19)
put(obj(6,12),'논문 <그림 3-1> 원그림 · 정상 검증 경로')
changes.append(dict(slide=6,old='발표용 단순 네 단계 도형',new='논문 그림3-1 원본+평이한 단계 설명',source_idxs=[703,751,757],reason='사용자 요청: 본문 그림 활용'))
s=clear(10);pic(s,9,.65,1.55,8.7,4.75)
tx(s,.7,6.3,8.6,.45,'가설: 여섯 특성 조정 후에도 도입 현장의 지각 실효성이 더 높은가?',17,'123B78',True)
changes.append(dict(slide=10,old='발표용 간략 연구모형',new='논문 그림4-1 원본',source_idxs=[1120,1122],reason='사용자 요청: 본문 그림 활용'))
put(obj(4,11),'정확한 경보와 현장 업무, 서로 다른 증거로 확인했다')
put(obj(4,14),'기술평가에는 경보 후보를, 현장 비교에는 관리자 설문을 사용')
put(obj(4,18),'기존 CCTV·범용 PC\n영상관제·위험 판단\n지정 담당자 알림')
put(obj(4,22),'경보 후보 878건\n오경보와 위험 누락\n검출 판정 시간')
put(obj(4,26),'73개 현장·73명\n공통 8문항\n여섯 특성 조정')
put(obj(16,17),'시스템 알림으로\n위험을 인지')
# Resolve ambiguous timing limitation without implying unmeasured model latency.
c=obj(19,14).table.cell(5,0);put(c,'담당자 열람·조치까지의 시간\n및 경제성 미평가')
for q in c.text_frame.paragraphs:
 for rr in q.runs:rr.font.size=Pt(15)
obj(19,14).table.rows[5].height=Inches(.66)
# Keep the figures legible and simplify the roadmap.
for s in p.slides[1].shapes:
 if s.has_text_frame:
  if s.text.startswith('01  '):put(s,'WHY  왜 필요한가')
  elif s.text.startswith('02  '):put(s,'HOW  어떻게 했나')
  elif s.text.startswith('03  '):put(s,'WHAT  무엇을 얻었나')
  if s.text.startswith(('WHY ','HOW ','WHAT ')):
   for q in s.text_frame.paragraphs:
    for rr in q.runs:rr.font.size=Pt(17)
put(obj(2,11),'왜 필요한가 → 어떻게 했나 → 무엇을 얻었나')
# Sequence: all design before findings; define the 15 cases before sensitivity analysis.
order=[1,2,3,4,5,6,7,10,11,12,13,8,9,14,16,15,17,18,19,20,21,22,23,24]
ids=list(p.slides._sldIdLst)
for el in ids:p.slides._sldIdLst.remove(el)
for no in order:p.slides._sldIdLst.append(ids[no-1])
for i,s in enumerate(p.slides,1):
 if i==1:continue
 section=('WHY','문제와 연구 질문') if i<=3 else ('HOW','개발과 검증 설계') if i<=11 else ('WHAT','결과와 의미') if i<=20 else ('부록','질의응답 참고')
 put(obj(i,2),section[0]);put(obj(i,10),section[1]);put(obj(i,13),str(i))
for no,extra in [(2,'발표는 WHY, HOW, WHAT 순서입니다. 필요성과 문제를 제시하고, 시스템 개발과 두 평가의 설계를 먼저 설명한 뒤, 기술결과와 현장결과를 이어서 제시합니다.'),(7,'경보 후보의 정확성 외에, 관리자 업무 실효성은 별도 현장조사로 비교했습니다. 다음 슬라이드부터 그 비교 설계를 설명합니다.'),(16,'앞서 정의한 실제 알림 활용 15개 현장으로 좁혀도 차이의 방향은 같았습니다.')]:
 tf=p.slides[no-1].notes_slide.notes_text_frame;tf.text=tf.text+'\n'+extra
# Update change numbering to final sequence and record figure provenance.
inv={old:new for new,old in enumerate(order,1)}
for ch in changes:ch['slide']=inv.get(ch['slide'],ch['slide'])
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=R/f'{stamp}_윤혁_석사학위논문_심의발표_스토리재구성.pptx';assert not out.exists();p.save(out)
r.update(output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),checks=[],structure={'WHY':'1–3','HOW':'4–11','WHAT':'12–20','appendix':'21–24'},figure_usage=[{'slide':5,'thesis':'그림 3-4','type':'original'},{'slide':6,'thesis':'그림 3-1','type':'original'},{'slide':8,'thesis':'그림 4-1','type':'original'},{'slide':17,'thesis':'그림 3-6','type':'original'},{'slide':12,'thesis':'표 3-7','type':'reconstructed chart'},{'slide':14,'thesis':'표 4-12','type':'reconstructed chart'},{'slide':15,'thesis':'그림 3-7 A-7/A-8 및 제4장 제8절','type':'extracted statistics'},{'slide':16,'thesis':'표 4-13','type':'presentation table'}])
(B/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
(B/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
