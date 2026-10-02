"""Editable SVG and matching 300 dpi PNG. Run from any working directory.

Requires Pillow; uses Windows Malgun Gothic. Coordinates are 10 units/mm.
SVG preserves text; PNG uses the same primitives and actual font metrics.
"""
from pathlib import Path
from html import escape
import math
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
NAVY, INK, GRAY, PALE = '#243C55', '#20262D', '#58616B', '#F2F4F6'
SCALE = 300 / 25.4 / 10
FONT = Path('C:/Windows/Fonts/malgun.ttf')
BOLD = Path('C:/Windows/Fonts/malgunbd.ttf')

class Figure:
    def __init__(self, name, height, title):
        self.name, self.height = name, height
        self.im = Image.new('RGB', (round(1500*SCALE), round(height*SCALE)), 'white')
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="150mm" height="{height/10}mm" viewBox="0 0 1500 {height}">',
                    f'<title>{escape(title)}</title>', '<rect width="1500" height="100%" fill="white"/>']
    def box(self, x, y, w, h, fill='white', dash=False):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{NAVY}" stroke-width="3"'+(' stroke-dasharray="14 10"' if dash else '')+'/>')
        self.draw.rectangle(tuple(round(v*SCALE) for v in (x,y,x+w,y+h)), fill=fill)
        self.line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)], dash=dash, svg=False)
    def text(self, x, y, value, size=36, bold=False, color=INK, center=False):
        font=ImageFont.truetype(str(BOLD if bold else FONT), round(size*SCALE))
        width=self.draw.textlength(value,font=font)/SCALE
        assert (x-width/2 if center else x)>=0 and (x+width/2 if center else x+width)<=1500, value
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Malgun Gothic" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{"middle" if center else "start"}">{escape(value)}</text>')
        self.draw.text((round(x*SCALE),round(y*SCALE)),value,font=font,fill=color,anchor='ms' if center else 'ls')
    def line(self, pts, dash=False, arrow=False, svg=True):
        if svg:
            self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{NAVY}" stroke-width="3"'+(' stroke-dasharray="14 10"' if dash else '')+'/>')
        for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
            length=math.hypot(x2-x1,y2-y1)
            for start in range(0,math.ceil(length),24 if dash else max(1,math.ceil(length))):
                end=min(length,start+(14 if dash else length))
                self.draw.line([(round((x1+(x2-x1)*t/length)*SCALE),round((y1+(y2-y1)*t/length)*SCALE)) for t in (start,end)],fill=NAVY,width=round(3*SCALE))
        if arrow:
            x,y=pts[-1]; px,py=pts[-2]; a=math.atan2(y-py,x-px)
            tri=[(x,y),(x-18*math.cos(a)+9*math.sin(a),y-18*math.sin(a)-9*math.cos(a)),(x-18*math.cos(a)-9*math.sin(a),y-18*math.sin(a)+9*math.cos(a))]
            self.svg.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in tri)+f'" fill="{NAVY}"/>')
            self.draw.polygon([(round(a*SCALE),round(b*SCALE)) for a,b in tri],fill=NAVY)
    def save(self):
        (OUT/(self.name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        self.im.save(OUT/(self.name+'.png'),dpi=(300,300))

def flow():
    f=Figure('figure_1-3_research_flow',1790,'연구의 흐름도')
    steps=[
      (50,220,'제1·2장  연구 배경과 이론적 근거','Why',[
       '중소규모 건설현장의 안전관리 문제와 선행연구의 한계',
       '시스템 개발 및 도입 여부에 따른 실효성 비교의 필요성']),
      (330,220,'제3장  YOLO-LLM 안전관제 시스템 개발','How',[
       'YOLO 1차 탐지와 LLM 2차 문맥 검증의 결합',
       '시스템 구현 및 현장 운영 로그 기반 기술 성능 검증']),
      (610,300,'제4장  도입·미도입 현장 비교 조사 설계','How',[
       '문항 구성 → 전문가 내용타당도 검증 → 예비조사',
       '도입 30개소·미도입 30개소, 사후 설문 1회',
       '현장당 2명·총 120부 목표 / 공변량·분석 절차 설정']),
      (970,340,'제5장  실증분석 결과','What',[
       '자료 정제·기술통계·신뢰도·사전 특성 분포·균형 진단',
       '현장 군집성 및 혼합모형 가정 점검',
       'H1 주 분석: 선형혼합모형으로 실효성 조정 평균 비교',
       'H2 탐색적 보조 분석: 집단 × 예산 제약성']),
      (1370,230,'제6장  결론','의미',[
       '연구 결과 요약 및 학술적·실무적·정책적 시사점',
       '연구의 한계와 향후 연구 방향'])]
    for i,(y,h,title,tag,lines) in enumerate(steps):
        f.box(45,y,1410,h)
        f.box(45,y,1410,78,PALE)
        f.text(78,y+53,title,40,True,color=NAVY)
        f.text(1360,y+53,tag,36,True,color=GRAY,center=True)
        for j,t in enumerate(lines): f.text(80,y+130+j*51,t)
        if i<len(steps)-1: f.line([(750,y+h),(750,steps[i+1][0])],arrow=True)
    f.text(750,1670,'횡단적 두 집단 비교 · 개인 응답 분석 · jamovi 사용',36,center=True)
    f.text(750,1725,'조정된 집단 차이를 해석하며 인과 효과를 단정하지 않는다.',36,center=True)
    f.save()

def model():
    f=Figure('figure_4-1_research_model',1630,'연구 모형: 주 분석과 탐색적 보조 분석')
    f.text(50,65,'H1  주 분석 · 현장 임의절편 선형혼합모형',44,True,color=NAVY)
    f.text(50,123,'공변량 조정 후 안전관리 실효성의 집단 간 평균 비교',36)
    f.box(50,180,530,190,PALE)
    f.text(315,235,'AI 관제 시스템 도입 집단',38,True,center=True)
    f.text(315,295,'AI 위험 알림 수신 현장',36,center=True)
    f.box(50,420,530,190,PALE)
    f.text(315,475,'AI 관제 시스템 미도입 집단',36,True,center=True)
    f.text(315,535,'AI 위험 알림 미수신 현장',36,center=True)
    f.line([(580,275),(650,275),(650,515),(580,515)])
    f.line([(650,395),(825,395)],arrow=True)
    f.text(736,350,'비교',36,True,center=True)
    f.box(825,180,625,430)
    f.text(1137,243,'안전관리 실효성(Y)',42,True,center=True)
    f.text(1137,304,'전체 점수의 조정 평균',36,True,center=True)
    for y,t in [(376,'조기인지 · 대응 신속성'),(432,'원격 파악 · 순찰부담 경감'),(488,'위험 통제력')]: f.text(1137,y,t,36,center=True)
    f.text(1137,566,'하위영역 분석은 보조 결과',34,color=GRAY,center=True)
    f.box(380,735,1070,175,PALE)
    f.text(415,790,'공변량 조정',38,True,color=NAVY)
    f.text(415,844,'소속 구분 · 성별 · 연령 · 경력 · 역할',36)
    f.text(415,891,'현장 공사금액 규모',36)
    f.line([(1137,735),(1137,610)],arrow=True)
    f.text(50,990,'H2  탐색적 보조 분석 · 주 결론과 구분',42,True,color=NAVY)
    f.box(50,1035,1400,365,dash=True)
    f.text(90,1100,'안전관리 예산 제약성(W)',38,True)
    f.text(90,1150,'집단 및 W의 주효과와 공변량을 포함한 보조 모형',36)
    f.box(90,1195,690,95,PALE,dash=True)
    f.text(435,1256,'집단 × 예산 제약성(W)',38,True,center=True)
    f.line([(780,1242),(1000,1242)],dash=True,arrow=True)
    f.text(1220,1256,'안전관리 실효성(Y)',36,True,center=True)
    f.text(90,1355,'검정력 제약을 고려하여 방향·효과크기·신뢰구간 중심 해석',35)
    f.text(50,1465,'실선: 주 분석 및 공변량 조정 / 점선: 탐색적 상호작용 분석',34)
    f.text(50,1520,'화살표는 분석 관계를 표시하며 인과관계의 입증을 뜻하지 않는다.',34)
    f.text(50,1575,'사후 설문 1회의 횡단 비교 · 개인 응답 분석 / 현장 군집 반영',34)
    f.save()

if __name__ == '__main__':
    flow(); model()
    for p in sorted(OUT.glob('*.png')):
        im=Image.open(p)
        print(p.name, im.size, im.info.get('dpi'))
