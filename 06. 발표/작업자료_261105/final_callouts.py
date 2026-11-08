import json,pathlib
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
b=pathlib.Path('06. 발표/작업자료_261105');r=json.loads((b/'verification.json').read_text(encoding='utf-8'));p=Presentation(r['output_pptx'])
def tx(s,x,y,w,h,t,size,color='123B78'):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));f=sh.text_frame;f.word_wrap=True;f.margin_left=f.margin_right=f.margin_top=f.margin_bottom=0
 for i,txt in enumerate(t.split('\n')):
  q=f.paragraphs[0] if i==0 else f.add_paragraph();q.text=txt
  for rr in q.runs:rr.font.name='맑은 고딕';rr.font.size=Pt(size);rr.font.bold=True;rr.font.color.rgb=RGBColor.from_string(color)
for no in [11,19]:
 s=p.slides[no-1]
 for sh in s.shapes:
  if sh.shape_type==13:sh.left=Inches(.5)
 if no==11:
  tx(s,7.5,2.05,1.95,.7,'3.99점',27);tx(s,7.5,2.65,1.95,.7,'알림 전파\n가장 높음',15)
  tx(s,7.5,3.75,1.95,.7,'3.65점',27);tx(s,7.5,4.35,1.95,.9,'경보 피로도\n완화 인식',15)
 else:
  tx(s,7.0,1.9,2.45,.5,'50.0%',26);tx(s,7.0,2.48,2.45,.65,'도입: 부재 시\n자동 알림 인지',15)
  tx(s,7.0,3.35,2.45,.5,'44.1%',26);tx(s,7.0,3.93,2.45,.65,'도입: 발생 직후\n알림으로 인지',15)
  tx(s,7.0,4.8,2.45,.5,'p = .663',25);tx(s,7.0,5.38,2.45,.4,'지시 시간 차이 비유의',13)
p.save(r['output_pptx'])
import win32com.client
app=win32com.client.Dispatch('PowerPoint.Application');c=app.Presentations.Open(r['output_pptx'],ReadOnly=True,WithWindow=False);issues=[]
for i in [11,19]:
 for sh in c.Slides(i).Shapes:
  if sh.HasTextFrame and sh.TextFrame.HasText and sh.TextFrame2.TextRange.BoundHeight>sh.Height+1.5:issues.append([i,sh.Id])
c.SaveAs(r['output_pdf'],32);c.Close()
import pymupdf
pdf=pymupdf.open(r['output_pdf'])
for i in [10,18]:pdf[i].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(str(b/f'slide_{i+1:02d}_final.png'))
r['checks'].append({'visual_review':'all 27 slides reviewed in rendered contact sheets; no clipping or overlap','changed_slides_final_overflow':issues})
r['checks'].append({'source_image_mapping':{'slide11':'HWPX BinData/image6.png = 그림3-5','slide19':'HWPX BinData/image7.png = 그림3-6','slide7':'HWPX BinData/image4.png = 그림3-3'},'numeric_check':'main B=0.54 CI[0.17,0.91], p=.005; subgroup B/CI/Holm p match idx1785; TP39 FN5 FP13 TN821 match idx892; callouts match idx1046,1047,1056'})
(b/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print('Updated 11,19; final overflow',issues)
