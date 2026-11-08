from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
import json,datetime,hashlib,zipfile
from zoneinfo import ZoneInfo
B=Path(__file__).resolve().parent; ROOT=B.parent
src=ROOT/'261106_1209_윤혁_석사학위논문_심의발표.pptx'; thesis=ROOT.parent/'00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx'
p=Presentation(src);changes=[]
hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [src,thesis]}
def shape(n,sid):return next(s for s in p.slides[n-1].shapes if s.shape_id==sid)
def put(sh,value):
 tf=sh.text_frame;q=tf.paragraphs[0]
 if q.runs:
  q.runs[0].text=value
  for r in list(q.runs)[1:]:r.text=''
 else:q.text=value
 for q in list(tf.paragraphs)[1:]:tf._txBody.remove(q._p)
def ch(n,sid,new,ids,reason):
 sh=shape(n,sid);old=sh.text;put(sh,new);changes.append(dict(slide=n,old=old,new=new,source_idxs=ids,reason=reason))
def cell(n,sid,r,c,new,ids,reason):
 x=shape(n,sid).table.cell(r,c);old=x.text;put(x,new);changes.append(dict(slide=n,old=old,new=new,source_idxs=ids,reason=reason))
ch(2,17,'기존 CCTV를 위험 인지와 대응으로 연결',[240,243,244],'개정 서론 반영')
ch(3,11,'기존 CCTV를 위험 인지와 대응으로 연결',[240,243],'개정 서론 반영')
ch(3,14,'영상 확인의 부담과 오경보를 줄이고, 현장 업무 실효성을 함께 검토',[240,241,244],'개정 서론 반영')
ch(3,17,'CCTV 활용의 한계',[240],'개정 서론 반영')
ch(3,18,'육안 확인에 의존\n모니터링 인력 부족\n공정 확인 위주 활용',[240],'Kim et al.(2022) 근거 요약')
ch(3,22,'정상 작업도 위험 탐지\n장면 문맥 추가 검증\n실제 위험 손실 점검',[241],'오경보와 위험 경보 손실 동시 평가')
ch(3,28,'연구 질문: 시스템 도입 현장의 지각 실효성은 미도입 현장보다 높은가?',[247,250],'단일 연구가설과 일치')
ch(4,12,'논문 제1장 제2절 · 제3장 제4절 · 제4장 제7절',[245,247,249,250],'연구 목적 근거 갱신')
ch(4,18,'다중·단일 영상관제\nYOLO와 LLM 연계\n지정 담당자 알림',[248,256],'개발 범위 명시')
ch(4,22,'오경보·위험 경보 손실\n검출 판정 시간\n교정 사례 비교',[249,846,1026],'최신 기술평가 범위 반영')
ch(5,14,'영상관제 → 후보 탐지 → 문맥 검증 → 지정 담당자 알림',[248,256,703],'최신 개발 범위 반영')
ch(7,23,'5월 평가: RAG 비교 · 이후 기본 경로인 플레이북은 미평가',[764,831],'평가 당시와 이후 운용판본 구분')
ch(9,11,'오경보 억제 목표 충족, 실제 위험 5건은 차단',[893,897],'최신 논문의 목표 평가를 위험손실과 함께 보고')
ch(9,14,'특이도 98.4%로 평가 목표 90% 상회 · 외부 인증 판정은 아님',[847,848,897],'평가 목표 및 범위 반영')
ch(9,27,'평균 검출 판정 약 7.3초 · 평균 10초 이내 설계 목표 충족',[897,1026],'검출 판정 시간 반영; A-9와 별개')
ch(9,29,'LLM 평균 6.55초 + YOLO 확정 최소 약 0.7초 · 전송·열람 시간 제외',[544,897,1026],'평균 합산 추정 구간 명시')
ch(10,11,'RAG는 오경보 억제에 유리, 재현율은 낮음',[970],'최신 비교결과 해석 반영')
ch(10,14,'오경보 17 → 7건 · F1은 유사하여 보편적 성능 우위로 보지 않음',[970],'균형 잡힌 해석 유지')
ch(11,12,'논문 <그림 3-6> · 제3장 제4절 제5항 | 도입 현장 관리자 34명',[1080],'그림 번호 변경')
ch(17,11,'연구가설 (1-1): 도입 현장의 지각 실효성이 높음',[1662],'사용자 요청 A-9 제거')
sh=shape(17,14);old=[[c.text for c in r.cells] for r in sh.table.rows];sh.table._tbl.remove(sh.table.rows[2]._tr)
sh.top=Inches(2.35);sh.table.rows[0].height=Inches(.65);sh.table.rows[1].height=Inches(2.05)
changes.append(dict(slide=17,old=old,new=[[c.text for c in r.cells] for r in sh.table.rows],source_idxs=[1568,1569,1662],reason='사용자 요청: 과정지표 A-9 행 삭제'))
ch(17,16,'가설은 지지되었으나, 횡단 비교 결과를 도입의 인과효과로 단정하지 않음',[1569,1699],'A-9 삭제 후 해석 범위 정리')
ch(18,12,'논문 <그림 3-7> · 제4장 제7절 제2항',[1089,1663],'그림 번호 변경')
ch(19,12,'논문 <그림 3-7> · 제3장 제4절 제6항 | A-7·A-8은 운용 확인 지표',[1084,1089],'그림 번호 변경')
cell(23,14,2,0,'한 기관·1회 자기보고 조사',[1699,1700],'최신 한계 및 향후 방향과 정합')
cell(23,14,3,0,'5월 기술평가·10월 설문의 판본 차이',[742,831],'현장간 동일설정 사실과 운용판본 차이 구별')
cell(23,14,3,1,'CCTV 조건·운용판본을 맞춘 비교',[831,1700],'실제 남은 비교조건 명시')
ch(23,12,'논문 제3장 평가 범위 · 제5장 한계와 향후 연구',[829,831,1699,1700],'유지한 기술 한계의 근거 확장')
ch(24,16,'구현  기존 CCTV·PC 기반 영상관제와 이중검사\n평가  특이도 98.4% · 평균 검출 판정 약 7.3초\n실증  조정 차이 +0.54점, p=.005',[1693,1695,1093],'개정 결론과 핵심 기술평가 반영')
# Refresh exact thesis figures, retaining existing bounds and z-order.
with zipfile.ZipFile(thesis) as z:
 for no,imgid,ids in [(6,5,[811]),(7,4,[762]),(11,7,[1080]),(19,8,[1089])]:
  oldsh=next(s for s in p.slides[no-1].shapes if s.shape_type==13)
  path=B/f'thesis_image{imgid}.png';path.write_bytes(z.read(f'BinData/image{imgid}.png'))
  from PIL import Image
  iw,ih=Image.open(path).size;scale=min(oldsh.width/iw,oldsh.height/ih);w=int(iw*scale);h=int(ih*scale)
  newsh=p.slides[no-1].shapes.add_picture(str(path),oldsh.left+(oldsh.width-w)//2,oldsh.top+(oldsh.height-h)//2,w,h)
  parent=oldsh._element.getparent();idx=parent.index(oldsh._element);parent.remove(newsh._element);parent.insert(idx,newsh._element);parent.remove(oldsh._element)
  changes.append(dict(slide=no,old='이전 PDF 추출 그림',new=f'지정 HWPX BinData/image{imgid}.png',source_idxs=ids,reason='지정 논문의 그림 직접 반영'))
# Source notes on all slides; specific explanatory notes retain all valid content.
for no,sl in enumerate(p.slides,1):
 tf=sl.notes_slide.notes_text_frame;old=tf.text
 new=old.replace('00. hwpx/261106_1132_경기공학_건축안전_윤혁_논문.pdf','00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx')
 if no==3:new+='\n서론 근거: Kim et al.(2022)은 중소규모 현장의 육안 확인·공정 확인 위주 활용을 보고하였다. 류정·박인선(2025)은 정상 장면의 오탐 사례를 보고하였다. 본 연구는 기존 CCTV의 영상관제와 위험 판단·알림을 연결하고 동일 척도로 현장 업무 실효성을 비교한다.'
 if no==7:new+='\n5월 평가 이후 기본 교정 방식은 플레이북(교정 사례의 규칙 문장 요약 주입)으로 변경되었고 RAG는 대체 경로로 남았다. 플레이북 성능은 평가하지 않았다.'
 if no==9:new+='\n조건부 정밀도 .750, 재현율 .886. 특이도 98.4%는 평가 목표 90%를 넘었다. 평균 검출 판정 약 7.3초는 LLM 평균 6.55초와 YOLO 확정 설정상 최소 약 0.7초의 합산값이다. 모든 사건의 10초 이내 판정을 뜻하지 않으며, 메신저 전송·담당자 열람·지시 전달 시간은 포함하지 않는다.'
 if no==17:new='기준: 00. hwpx/261108_1359_경기공학_건축안전_윤혁_논문.hwpx\n연구가설 (1-1)은 여섯 통제변수 조정 후 도입−미도입 차이가 양수이고 양측 p<.05이면 지지한다. 조정 차이 +0.54점, 95% CI [0.17,0.91], p=.005로 가설을 지지하였다. 동일 현장의 도입 전후 변화나 인과효과를 검증한 것은 아니다.'
 if no==23:new+='\n34개 도입 현장의 운용 설정은 현장 간 동일하였으나 기간 중 판본이 갱신되었다. 5월 운영로그 평가와 9월 가중치 교체 이후 10월 설문은 같은 판본의 성능 측정이 아니다.'
 tf.text=new
 changes.append(dict(slide=no,old=old,new=new,source_idxs=([1568,1569,1662,1699] if no==17 else []),reason='발표노트 기준 갱신'+(' 및 해당 장 설명 정합' if no in [3,7,9,17,23] else '')))
stamp=datetime.datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y%m%d_%H%M');out=ROOT/f'{stamp}_윤혁_석사학위논문_심의발표.pptx';assert not out.exists();p.save(out)
(B/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
r=dict(source=str(thesis.resolve()),source_pptx=str(src.resolve()),output_pptx=str(out.resolve()),output_pdf=str(out.with_suffix('.pdf').resolve()),slide_count=len(p.slides),checks=[],limitations=[],source_hashes=hashes)
r['checks'].append({'original_hashes_unchanged':all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v for f,v in hashes.items())})
(B/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
