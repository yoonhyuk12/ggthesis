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
    def __init__(self, name, height, title, stroke=NAVY):
        self.stroke = stroke
        self.name, self.height = name, height
        self.im = Image.new('RGB', (round(1500*SCALE), round(height*SCALE)), 'white')
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="150mm" height="{height/10}mm" viewBox="0 0 1500 {height}">',
                    f'<title>{escape(title)}</title>', '<rect width="1500" height="100%" fill="white"/>']
    def box(self, x, y, w, h, fill='white', dash=False):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{self.stroke}" stroke-width="3"'+(' stroke-dasharray="14 10"' if dash else '')+'/>')
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
            self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{self.stroke}" stroke-width="3"'+(' stroke-dasharray="14 10"' if dash else '')+'/>')
        for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
            length=math.hypot(x2-x1,y2-y1)
            for start in range(0,math.ceil(length),24 if dash else max(1,math.ceil(length))):
                end=min(length,start+(14 if dash else length))
                self.draw.line([(round((x1+(x2-x1)*t/length)*SCALE),round((y1+(y2-y1)*t/length)*SCALE)) for t in (start,end)],fill=self.stroke,width=round(3*SCALE))
        if arrow:
            x,y=pts[-1]; px,py=pts[-2]; a=math.atan2(y-py,x-px)
            tri=[(x,y),(x-18*math.cos(a)+9*math.sin(a),y-18*math.sin(a)-9*math.cos(a)),(x-18*math.cos(a)-9*math.sin(a),y-18*math.sin(a)+9*math.cos(a))]
            self.svg.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in tri)+f'" fill="{self.stroke}"/>')
            self.draw.polygon([(round(a*SCALE),round(b*SCALE)) for a,b in tri],fill=self.stroke)
    def circle(self, x, y, r, fill):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{self.stroke}" stroke-width="3"/>')
        self.draw.ellipse(tuple(round(v*SCALE) for v in (x-r,y-r,x+r,y+r)), fill=fill, outline=self.stroke, width=round(3*SCALE))
    def fill_rect(self, x, y, w, h, fill):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
        self.draw.rectangle(tuple(round(v*SCALE) for v in (x,y,x+w,y+h)), fill=fill)
    def save(self):
        (OUT/(self.name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        self.im.save(OUT/(self.name+'.png'),dpi=(300,300))

def flow():
    f=Figure('figure_1-1_research_flow',1890,'연구의 흐름도')
    steps=[
      (50,270,'제1장  문제 제기와 연구 목적','Why',[
       '중소규모 건설현장의 안전관리 문제와 선행연구의 한계',
       'YOLO-LLM 안전관제 시스템 도입 현장과 미도입 현장의',
       '안전관리 실효성 비교']),
      (380,220,'제2장  이론적 배경과 가설 도출 근거','Why',[
       '이론적 배경과 선행연구 고찰',
       'H1 가설 도출 근거']),
      (660,220,'제3장  YOLO-LLM 안전관제 시스템 개발','How',[
       'YOLO 1차 탐지와 LLM 2차 문맥 검증의 결합',
       '시스템 구현 및 현장 운영 로그 기반 기술 성능 검증']),
      (940,500,'제4장  연구설계 및 실증분석','How·What',[
       '문항 구성 → 전문가 내용타당도 검증 → 예비조사',
       '도입 34개소·미도입 39개소, 응답 73명(모집 목표 60명):',
       '현장당 1명·사후 설문 1회 / 공변량·분석 절차 설정',
       '제6절  자료 정제·기술통계·신뢰도·사전 특성 분포·균형 진단',
       '제7절  가정 점검 → H1 두 집단 공분산분석',
       '(ANCOVA, 연속 공변량 2·범주형 통제요인 4) → 하위요인 Holm 보정',
       '→ 지지·기각 판정']),
      (1500,220,'제5장  결론','의미',[
       '결과의 의미 논의: 선행연구·과정 지표(A-7∼A-9)와 대조',
       '연구 요약, 학술적·실무적 시사점, 한계와 향후 연구 방향'])]
    for i,(y,h,title,tag,lines) in enumerate(steps):
        f.box(45,y,1410,h)
        f.box(45,y,1410,78,PALE)
        f.text(78,y+53,title,40,True,color=NAVY)
        f.text(1360 if len(tag)<=4 else 1310,y+53,tag,36,True,color=GRAY,center=True)
        for j,t in enumerate(lines): f.text(80,y+130+j*51,t)
        if i<len(steps)-1: f.line([(750,y+h),(750,steps[i+1][0])],arrow=True)
    f.text(750,1790,'사후 1회 조사로 도입·미도입 현장 비교 · 관리자 개인 응답 단위 분석 · jamovi 사용',36,center=True)
    f.save()

def model():
    f=Figure('figure_4-1_research_model',780,'연구 모형',stroke='#000000')
    def headed_box(x,y,w,h,title):
        f.box(x,y,w,h)
        f.line([(x,y+80),(x+w,y+80)])
        f.text(x+w/2,y+55,title,40,True,color='#000000',center=True)
    headed_box(40,250,520,270,'독립변수(X)')
    for y,t in [(382,'YOLO-LLM 안전관제 시스템'),(437,'도입 여부'),(492,'(도입 / 미도입)')]:
        f.text(300,y,t,34,color='#000000',center=True)
    headed_box(1040,250,420,270,'종속변수(Y)')
    f.text(1250,400,'안전관리 실효성',34,color='#000000',center=True)
    headed_box(500,560,510,200,'통제변수(C)')
    f.text(518,678,'연속형(공변량): 나이, 경력',32,color='#000000')
    f.text(518,714,'범주형(고정요인): 역할, 성별,',32,color='#000000')
    f.text(590,750,'소속 구분, 총공사비 구간',32,color='#000000')
    f.line([(560,385),(1040,385)],arrow=True)
    f.line([(780,560),(780,390)],arrow=True)
    f.save()

# <그림 4-2> 표 4-12의 jamovi ANCOVA 추정 주변 평균과 95% CI
PLOT_L, PLOT_R, PLOT_T, PLOT_B, Y_MIN, Y_MAX = 200, 1440, 130, 690, 2.5, 4.5
def y_of(v):
    return PLOT_B-(v-Y_MIN)*(PLOT_B-PLOT_T)/(Y_MAX-Y_MIN)

def means_ci():
    K='#000000'
    f=Figure('figure_4-2_adjusted_means_ci',900,'안전관리 실효성의 조정 평균과 95% 신뢰구간',stroke=K)
    groups=[(500,'미도입 현장(n=39)',3.29,2.90,3.69),(1000,'도입 현장(n=34)',3.83,3.38,4.28)]
    lo,hi=3.38,3.69  # 두 CI가 겹치는 범위: 띠를 먼저 그려 뒤에 깐다
    f.fill_rect(PLOT_L,y_of(hi),PLOT_R-PLOT_L,y_of(lo)-y_of(hi),PALE)
    note='두 CI가 겹치는 범위(3.38∼3.69)'
    w=f.draw.textlength(note,font=ImageFont.truetype(str(FONT),round(26*SCALE)))/SCALE
    f.text(PLOT_R-12-w,(y_of(lo)+y_of(hi))/2+9,note,26,color=GRAY)
    f.text(60,72,'안전관리 실효성 조정 평균(점)',32,True,color=K)
    f.line([(PLOT_L,PLOT_T),(PLOT_L,PLOT_B),(PLOT_R,PLOT_B)])
    for i in range(5):
        v=Y_MIN+0.5*i; y=y_of(v)
        f.line([(PLOT_L-12,y),(PLOT_L,y)])
        f.text(145,y+11,f'{v:.1f}',32,color=K,center=True)
    for x,label,m,l,u in groups:
        f.line([(x,PLOT_B),(x,PLOT_B+12)])
        f.line([(x,y_of(u)),(x,y_of(l))])
        for v in (l,u): f.line([(x-15,y_of(v)),(x+15,y_of(v))])
        f.circle(x,y_of(m),12,K)
        f.text(x+30,y_of(m)+11,f'{m:.2f}',32,color=K)
        f.text(x,PLOT_B+58,label,34,color=K,center=True)
        f.text(x,PLOT_B+102,f'[{l:.2f}, {u:.2f}]',30,color=K,center=True)
    f.text(750,868,'점: 조정 평균, 선: 95% 신뢰구간(CI) · 도입–미도입 차이 0.54점 [0.17, 0.91]',28,color=K,center=True)
    f.save()

if __name__ == '__main__':
    flow(); model(); means_ci()
    for p in sorted(OUT.glob('*.png')):
        im=Image.open(p)
        print(p.name, im.size, im.info.get('dpi'))
