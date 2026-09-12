"""Editable text SVG and white 300-dpi PNG; run with Python + matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'Malgun Gothic', 'svg.fonttype':'none',
                     'font.size':9, 'axes.unicode_minus':False})
NAVY='#243B53'; INK='#202830'; GRAY='#56616B'; PALE='#F2F4F6'

def canvas(h):
    fig=plt.figure(figsize=(150/25.4,h/25.4),facecolor='white')
    ax=fig.add_axes([0,0,1,1]); ax.set(xlim=(0,150),ylim=(h,0)); ax.axis('off')
    return fig,ax

def txt(ax,x,y,s,size=9,bold=False,color=INK,ha='center'):
    return ax.text(x,y,s,ha=ha,va='center',fontsize=size,
                   weight='bold' if bold else 'normal',color=color,linespacing=1.5)

def box(ax,x,y,w,h,title,body='',dark=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=1',
                 linewidth=.8,edgecolor=NAVY,facecolor=NAVY if dark else PALE))
    color='white' if dark else INK
    if body:
        txt(ax,x+w/2,y+5,title,9,True,color)
        txt(ax,x+w/2,y+h/2+3,body,8.4,color=color)
    else: txt(ax,x+w/2,y+h/2,title,9,True,color)

def arrow(ax,points,dashed=False):
    for i,(p,q) in enumerate(zip(points,points[1:])):
        ax.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>' if i==len(points)-2 and p[0]==q[0] and p!=q else '-',
            mutation_scale=9,linewidth=.85,color=NAVY,linestyle='--' if dashed else '-',
            shrinkA=0,shrinkB=0,connectionstyle='arc3'))

def save(fig,name):
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    fig.savefig(OUT/(name+'.png'),dpi=300,facecolor='white')
    plt.close(fig)
    im=Image.open(OUT/(name+'.png'))
    assert im.info['dpi'][0]>299 and im.getpixel((0,0))[:3]==(255,255,255)
    print(name,im.size,im.info['dpi'])

def architecture():
    f,a=canvas(142)
    txt(a,75,6,'영상 수신부터 경보 전파까지',11,True,NAVY)
    box(a,8,16,83,20,'① 영상 수신','ONVIF 카메라 · RTSP / PyAV')
    box(a,8,44,83,23,'② YOLO 1차 검출','신뢰도 임계값 0.3 · 경고 확인 필터')
    arrow(a,[(49.5,36),(49.5,44)])
    txt(a,116,25,'실시간 경로\nVideoThread',8.5,True,NAVY)
    txt(a,116,55,'민감도 중시\n위험 후보 검출',8.5)
    arrow(a,[(49.5,67),(49.5,80)])
    txt(a,53,73.5,'비동기 Signal',8,ha='left',color=GRAY)
    box(a,8,80,83,23,'③ LLM 2차 검증','원본 프레임 + 메타데이터 + 교정 예시',True)
    txt(a,116,91,'특이도 중시\n문맥 오탐 검토',8.5)
    arrow(a,[(49.5,103),(49.5,115)])
    txt(a,52,109,'SEND',8,ha='left')
    box(a,8,115,83,19,'④ 경보 전파','사유·이미지 → 다중 수신자')
    arrow(a,[(91,98),(119,98),(119,115)])
    txt(a,121,107,'BLOCK',8,ha='left')
    box(a,99,115,42,19,'이력 저장','사용자 검토·교정')
    txt(a,75,139,'연구에서 기술한 구성 · 2차 검증의 상세 흐름은 그림 3-2 참조',7.8,color=GRAY)
    save(f,'fig_3_1_architecture')

def verification():
    f,a=canvas(170)
    txt(a,75,6,'멀티모달 입력과 판정·전송 분기',11,True,NAVY)
    box(a,6,15,44,23,'알람 메타데이터','카메라명 · 경고 키\n경고 메시지')
    box(a,53,15,41,23,'원본 프레임','영상 이미지')
    box(a,97,15,47,23,'사용자 교정','선택된 예시\n사유 + 이미지')
    for x in [28,73.5,120.5]: arrow(a,[(x,38),(x,44),(75,44)])
    arrow(a,[(75,44),(75,50)])
    box(a,22,50,106,19,'멀티모달 LLM 문맥 추론','시스템 프롬프트 · 우선 규칙 · SEND/BLOCK 조건',True)
    arrow(a,[(75,69),(75,77)])
    box(a,22,77,106,28,'JSON 응답 · 두 필드','result: SEND 또는 BLOCK\nreason: 한국어 사유(80자 이하)')
    arrow(a,[(75,105),(75,113)])
    box(a,22,113,106,19,'판정 결과에 따라 분기','result = SEND / BLOCK')
    arrow(a,[(48,132),(48,143)]); txt(a,45,137.5,'SEND',8,ha='right')
    arrow(a,[(106,132),(106,143)]); txt(a,109,137.5,'BLOCK',8,ha='left')
    box(a,12,143,63,18,'다중 수신자 알림','한국어 사유 + 감지 이미지')
    box(a,83,143,55,18,'차단 이력·이미지 저장','사용자 검토 후 교정 등록')
    txt(a,75,167,'연구에서 기술한 구성 · API 장애 시 검증 실패를 표시하여 1차 결과 발송',7.8,color=GRAY)
    save(f,'fig_3_2_llm_verification')

def correction():
    f,a=canvas(170)
    txt(a,75,6,'검색 기반 교정 예시 선택과 재판정',11,True,NAVY)
    box(a,9,16,62,24,'① 사용자 교정 등록','알림 이력 우클릭\n사유 10~80자 + 교정 이미지')
    box(a,80,16,61,24,'새 알림 발생','카메라 · 경고 키\n메시지 + 원본 프레임')
    arrow(a,[(40,40),(40,48)])
    box(a,9,48,62,22,'② 맥락별 분류·저장','카메라별 사용자 교정\n사유 + 교정 이미지')
    arrow(a,[(110.5,40),(110.5,48)])
    box(a,80,48,61,22,'현재 알림의 맥락','같은 맥락의 교정 검색에 활용')
    arrow(a,[(40,70),(40,78),(75,78),(75,85)])
    arrow(a,[(110.5,70),(110.5,78),(75,78)])
    box(a,16,85,118,26,'③ 같은 맥락의 교정 검색','현재 알림과 같은 맥락의 교정만 선택\n최대 3건')
    arrow(a,[(47,111),(47,122)]); txt(a,44,116.5,'교정 있음',8,ha='right')
    arrow(a,[(108,111),(108,122)]); txt(a,111,116.5,'교정 없음',8,ha='left')
    box(a,9,122,69,18,'④ 교정 예시 주입','현재 입력 + 선택된 교정')
    box(a,87,122,54,18,'교정 미주입','현재 입력만 사용')
    arrow(a,[(43.5,140),(43.5,145),(75,145),(75,150)])
    arrow(a,[(114,140),(114,145),(75,145)])
    box(a,28,150,94,12,'⑤ 검증 LLM 재판정',dark=True)
    txt(a,75,167,'연구에서 기술한 구성 · 같은 맥락의 교정이 없으면 미주입',7.8,color=GRAY)
    save(f,'fig_3_3_rag_correction')

if __name__=='__main__':
    architecture(); verification(); correction()
