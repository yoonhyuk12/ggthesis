"""Generate field-operation stacked bars; --verify-source checks the workbook once.

Bar widths use table counts / group n to sum exactly to 100 percent.
Labels use the table percentages rounded to one decimal place.
Requires matplotlib, Pillow and openpyxl; workbook is read-only.
"""
from pathlib import Path
from collections import Counter
import argparse
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager, FontProperties
from matplotlib.patches import Patch
from PIL import Image
from openpyxl import load_workbook

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = ROOT / "01.docs/설문결과/jamovi_2차/261104_0410_jamovi용_설문응답_73건_2차_PartC삭제.xlsx"
PANELS = [
    dict(title="A-7 담당자 부재 시 위험 인지 경로", column="A7_인지경로",
         labels=["① 방법 없음", "② 작업자·반장 전화·보고", "③ CCTV 직접 확인", "④ 자동 알림", "⑤ 기타"],
         counts=[[0,10,7,17,0], [2,27,7,0,3]],
         percentages=[[0,29.4,20.6,50.0,0], [5.1,69.2,17.9,0,7.7]],
         colors=[0.96,0.60,0.82,0.22,0.94], hatches=["///",None,None,None,"..."]),
    dict(title="A-8 순찰 간 위험 인지 시점", column="A8_인지시점",
         labels=["① 다음 순찰 때", "② 누군가 알려줄 때", "③ 발생 직후 알림", "④ 모르고 지나감"],
         counts=[[6,10,15,3], [5,29,2,3]],
         percentages=[[17.6,29.4,44.1,8.8], [12.8,74.4,5.1,7.7]],
         colors=[0.92,0.60,0.22,0.78], hatches=[None,None,None,"///"]),
    dict(title="A-9 인지 후 지시 전달 소요시간", column="A9_전달시간",
         labels=["① 즉시∼5분", "② 5∼30분", "③ 30분∼1시간", "④ 1시간 초과·다음 순찰"],
         counts=[[11,18,4,1], [15,15,7,2]],
         percentages=[[32.4,52.9,11.8,2.9], [38.5,38.5,17.9,5.1]],
         colors=[0.94,0.73,0.48,0.22], hatches=[None,None,None,None]),
]


def verify_source():
    book = load_workbook(SOURCE, read_only=True, data_only=True)
    try:
        rows = iter(book["data"].values)
        header = next(rows)
        records = [dict(zip(header,r)) for r in rows]
        matches = 0
        mismatches = []
        print("Columns: D_도입여부, A7_인지경로, A8_인지시점, A9_전달시간")
        for panel in PANELS:
            for index, (group,n) in enumerate(((1,34),(0,39))):
                selected = [r for r in records if r["D_도입여부"] == group]
                assert len(selected) == n
                frequencies = Counter(r[panel["column"]] for r in selected)
                assert set(frequencies) <= set(range(1,len(panel["labels"])+1))
                for code, (expected, percent) in enumerate(zip(panel["counts"][index],panel["percentages"][index]),1):
                    actual = frequencies[code]
                    ok = actual == expected and f"{actual/n*100:.1f}" == f"{percent:.1f}"
                    matches += ok
                    if not ok:
                        mismatches.append((panel["column"],group,code,actual,expected))
                print(panel["column"], "group=",group,"n=",n,"counts=",dict(sorted(frequencies.items())))
        print(f"Verified {matches}/26 cells; mismatches={mismatches}")
    finally:
        book.close()


def draw():
    for name in ("malgun.ttf","malgunbd.ttf"):
        fontManager.addfont("C:/Windows/Fonts/"+name)
    normal = FontProperties(fname="C:/Windows/Fonts/malgun.ttf",size=6.5)
    strong = FontProperties(fname="C:/Windows/Fonts/malgunbd.ttf",size=7.5)
    plt.rcParams.update({"font.family":"Malgun Gothic","font.size":7,
                         "svg.fonttype":"none"})
    positions = [0,1,2,3,4,6,7,8,9,11,12,13,14]
    rows = [(label,p["percentages"][0][j],p["percentages"][1][j])
            for p in PANELS for j,label in enumerate(p["labels"])]
    bottom, height = 0.12, 0.76
    def fig_y(y):
        return bottom+height*(15-y)/16.7
    for variant in ("butterfly","dumbbell"):
        fig=plt.figure(figsize=(150/25.4,114/25.4),dpi=300)
        def setup(rect,reverse=False):
            ax=fig.add_axes(rect)
            ax.set(xlim=(80,0) if reverse else (0,80),ylim=(15,-1.7))
            ax.set_xticks([0,20,40,60,80])
            ax.set_yticks([])
            for spine in ("top","left","right"): ax.spines[spine].set_visible(False)
            ax.spines["bottom"].set_color("0.5")
            ax.tick_params(axis="x",length=2,pad=3)
            ax.grid(axis="x",color="0.90",linewidth=0.4,zorder=0)
            ax.set_axisbelow(True)
            return ax
        if variant=="butterfly":
            left=setup((0.07,bottom,0.24,height),True)
            right=setup((0.69,bottom,0.24,height))
            fig.text(0.19,0.95,"◀ 도입(n=34)",ha="center",fontproperties=strong)
            fig.text(0.81,0.95,"미도입(n=39) ▶",ha="center",fontproperties=strong)
            for y,(label,a,b) in zip(positions,rows):
                left.barh(y,a,height=0.5,color="0.30",zorder=2)
                right.barh(y,b,height=0.5,color="0.80",edgecolor="0.50",linewidth=0.4,zorder=2)
                left.annotate(f"{a:.1f}%",(a,y),xytext=(-3,0),textcoords="offset points",
                              ha="right",va="center",fontproperties=normal,clip_on=False)
                right.annotate(f"{b:.1f}%",(b,y),xytext=(3,0),textcoords="offset points",
                               ha="left",va="center",fontproperties=normal,clip_on=False)
                fig.text(0.50,fig_y(y),label,ha="center",va="center",fontproperties=normal)
            left.set_xlabel("응답 비율(%)",fontproperties=normal,labelpad=5)
            right.set_xlabel("응답 비율(%)",fontproperties=normal,labelpad=5)
        else:
            ax=setup((0.37,bottom,0.57,height))
            fig.text(0.655,0.95,"● 도입(n=34)   ○ 미도입(n=39)",ha="center",fontproperties=strong)
            for y,(label,a,b) in zip(positions,rows):
                ax.plot([a,b],[y,y],color="0.6",lw=1,zorder=1)
                ax.plot(a,y,"o",ms=4,color="black",zorder=3,clip_on=False)
                ax.plot(b,y,"o",ms=4,mfc="white",mec="black",mew=0.8,zorder=3,clip_on=False)
                close=abs(a-b)<13
                for value,is_adopted in ((a,True),(b,False)):
                    if close:
                        offset=(0,3 if is_adopted else -3)
                        align="center"
                        vertical="bottom" if is_adopted else "top"
                    elif value < 10:
                        offset=(0,3)
                        align="center"
                        vertical="bottom"
                    else:
                        offset=(-5,0) if value==min(a,b) else (5,0)
                        align="right" if value==min(a,b) else "left"
                        vertical="center"
                    ax.annotate(f"{value:.1f}%",(value,y),xytext=offset,textcoords="offset points",
                                ha=align,va=vertical,fontproperties=normal,clip_on=False)
                fig.text(0.345,fig_y(y),label,ha="right",va="center",fontproperties=normal)
            ax.set_xlabel("응답 비율(%)",fontproperties=normal,labelpad=5)
        for p,y in zip(PANELS,(-1.15,5.15,10.15)):
            fig.text(0.025,fig_y(y),p["title"],fontproperties=strong,va="center")
        for y in (4.78,9.78):
            fig.add_artist(plt.Line2D([0.025,0.97],[fig_y(y),fig_y(y)],
                                     transform=fig.transFigure,color="0.75",lw=0.5))
        png=OUT/f"fig_3_6_field_operation_{variant}.png"
        svg=OUT/f"fig_3_6_field_operation_{variant}.svg"
        fig.savefig(png,dpi=300,facecolor="white")
        fig.savefig(svg,facecolor="white")
        plt.close(fig)
        with Image.open(png) as im:
            print(f"{variant}: PNG {im.size}, dpi={im.info.get('dpi')}, 150 x 114 mm")
        nodes=ET.parse(svg).findall(".//{http://www.w3.org/2000/svg}text")
        labels=[t.text for t in nodes if t.text and t.text.endswith("%")]
        assert len(labels)==26, labels
        assert labels.count("0.0%")==3
        print(f"SVG editable text={len(nodes)}; percentage labels={len(labels)}/26; zero labels=3")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source",action="store_true")
    args=parser.parse_args()
    if args.verify_source: verify_source()
    draw()
