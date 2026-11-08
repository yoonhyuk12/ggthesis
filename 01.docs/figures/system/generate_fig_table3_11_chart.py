"""Table 3-11 compact v6 (five group bars with item means): python 01.docs/figures/system/generate_fig_table3_11_chart.py.

Requires matplotlib, openpyxl, Pillow. Reads the workbook without saving it.
Uses the approved table values even if the raw-data comparison finds differences.
SVG keeps editable text; install Malgun Gothic on the editing computer.
"""
from pathlib import Path
from statistics import mean, stdev
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
from openpyxl import load_workbook
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = ROOT / "01.docs/설문결과/jamovi_2차/261104_0410_jamovi용_설문응답_73건_2차_PartC삭제.xlsx"
C = [f"C{i}" for i in range(1, 9)]
D = [f"D{i}" for i in range(1, 5)]
# label, published mean, published sample SD, raw item columns
ROWS = [
    ("C-1", 3.71, 1.00, C[0:1]),
    ("C-2", 3.71, 0.97, C[1:2]),
    ("C-3", 3.94, 0.69, C[2:3]),
    ("C-4", 3.53, 0.99, C[3:4]),
    ("C-5", 3.56, 0.96, C[4:5]),
    ("C-6", 3.47, 0.96, C[5:6]),
    ("C-7", 4.12, 0.77, C[6:7]),
    ("C-8", 3.85, 0.86, C[7:8]),
    ("A1 범용성", 3.71, 0.88, C[0:2]),
    ("A2 안정성", 3.74, 0.72, C[2:4]),
    ("A3 오탐 필터링", 3.51, 0.91, C[4:6]),
    ("A4 알림 전파", 3.99, 0.74, C[6:8]),
    ("C 전체", 3.74, 0.66, C),
    ("D-1", 3.53, 1.28, D[0:1]),
    ("D-2", 3.59, 1.21, D[1:2]),
    ("D-3", 3.91, 0.97, D[2:3]),
    ("D-4", 3.59, 1.13, D[3:4]),
    ("D 전체", 3.65, 0.97, D),
]


def verify_source():
    book = load_workbook(SOURCE, read_only=True, data_only=True)
    try:
        records = iter(book["data"].values)
        headers = next(records)
        selected = [dict(zip(headers, r)) for r in records
                    if r[headers.index("D_도입여부")] == 1]
        assert len(selected) == 34, f"Unexpected n: {len(selected)}"
        print("Columns: D_도입여부, " + ", ".join(C + D))
        print("Group scores: respondent-level item means; sample SD uses ddof=1")
        mismatches = []
        for label, expected_m, expected_sd, columns in ROWS:
            assert all(isinstance(r[c], (int, float)) and 1 <= r[c] <= 5
                       for r in selected for c in columns), label
            scores = [mean(r[c] for c in columns) for r in selected]
            actual = (f"{mean(scores):.2f}", f"{stdev(scores):.2f}")
            expected = (f"{expected_m:.2f}", f"{expected_sd:.2f}")
            status = "MATCH" if actual == expected else "MISMATCH"
            print(f"{label}: raw={actual}, table={expected} {status}")
            if actual != expected:
                mismatches.append(label)
        print(f"n=34; matched={18-len(mismatches)}/18; mismatches={mismatches}")
    finally:
        book.close()


def draw():
    regular = Path("C:/Windows/Fonts/malgun.ttf")
    bold = Path("C:/Windows/Fonts/malgunbd.ttf")
    for font in (regular, bold):
        fontManager.addfont(str(font))
    normal = FontProperties(fname=str(regular), size=8)
    strong = FontProperties(fname=str(bold), size=8)
    small = FontProperties(fname=str(regular), size=6.5)
    plt.rcParams.update({"font.family": "Malgun Gothic", "font.size": 8,
                         "svg.fonttype": "none", "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(150/25.4, 98/25.4), dpi=300)
    fig.subplots_adjust(left=0.30, right=0.96, bottom=0.23, top=0.93)
    positions = [0, 1.45, 2.90, 4.35, 6.50]
    groups = [
        ("A1 범용성", 3.71, [("C-1", 3.71), ("C-2", 3.71)]),
        ("A2 안정성", 3.74, [("C-3", 3.94), ("C-4", 3.53)]),
        ("A3 오탐 필터링", 3.51, [("C-5", 3.56), ("C-6", 3.47)]),
        ("A4 알림 전파", 3.99, [("C-7", 4.12), ("C-8", 3.85)]),
        ("D 전체(D-1∼D-4)", 3.65,
         [("D-1", 3.53), ("D-2", 3.59), ("D-3", 3.91), ("D-4", 3.59)]),
    ]
    ax.set(xlim=(1, 5), ylim=(7.6, -1.1), xticks=[1, 2, 3, 4, 5])
    ax.set_yticks(positions, [g[0] for g in groups])
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", length=3, color="0.4")
    ax.set_xlabel("평균 점수(1∼5점)", fontproperties=normal, labelpad=18)
    for spine in ("top", "left", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("0.4")
    for x in (1, 2, 4, 5):
        ax.axvline(x, color="0.92", linewidth=0.5, zorder=0)
    for i, ((label, m, items), y) in enumerate(zip(groups, positions)):
        ax.barh(y, m-1, left=1, height=1.5 if i == 4 else 0.94,
                color="0.65" if i in (2, 3) else "0.85", zorder=1)
        offsets = [-0.31, 0.31] if len(items) == 2 else [-0.65, -0.30, 0.38, 0.65]
        for j, ((item, value), dy) in enumerate(zip(items, offsets)):
            ax.plot(value, y+dy, "o", markersize=3.4, color="0.16",
                    markeredgecolor="white", markeredgewidth=0.4, zorder=4)
            # No opaque label boxes: the rectangular bar silhouette stays intact.
            right = (i in (1, 2, 3) and j == 0) or (i == 4 and j == 2)
            ax.annotate(f"{item} {value:.2f}", (value, y+dy),
                        xytext=(5 if right else -5, 0), textcoords="offset points",
                        ha="left" if right else "right", va="center",
                        fontproperties=small, zorder=5)
        ax.text(m+0.10, y, f"{m:.2f}", fontproperties=strong,
                ha="left", va="center", zorder=5)
    for low, high in [(-0.70, -0.47), (0.47, 0.98), (1.92, 2.43),
                      (3.37, 3.88), (4.82, 5.75), (7.25, 7.6)]:
        ax.plot([3, 3], [low, high], color="0.5", linewidth=0.7,
                linestyle=(0, (1, 3)), zorder=2)
    for low, high in [(-0.72, -0.47), (0.47, 0.98), (1.92, 2.43),
                      (3.37, 3.88), (4.82, 4.97)]:
        ax.plot([3.74, 3.74], [low, high], color="0.28", linewidth=0.8,
                linestyle=(0, (4, 3)), zorder=2)
    ax.text(1, -0.095, "전혀 그렇지 않다", transform=ax.get_xaxis_transform(),
            ha="left", va="top", fontproperties=small, color="0.4")
    ax.text(3, -0.095, "보통이다", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontproperties=small, color="0.4")
    ax.text(5, -0.095, "매우 그렇다", transform=ax.get_xaxis_transform(),
            ha="right", va="top", fontproperties=small, color="0.4")
    ax.text(3.74, -0.86, "C 전체 3.74", ha="left", va="bottom", fontproperties=normal)
    for tick in ax.get_yticklabels():
        tick.set_fontproperties(normal)
    ax.text(-0.43, -0.82, "C 시스템 특성 인식", transform=ax.get_yaxis_transform(),
            fontproperties=strong, va="center", clip_on=False)
    ax.axhline(5.40, xmin=-0.43, color="0.75", linewidth=0.6, clip_on=False)
    ax.text(-0.43, 5.85, "D 경보 피로도 완화 인식", transform=ax.get_yaxis_transform(),
            fontproperties=strong, va="center", clip_on=False)
    legend = fig.text(0.63, 0.035, "막대=묶음 평균, 점=문항 평균",
                      ha="center", fontproperties=normal)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    title_box = ax.xaxis.label.get_window_extent(renderer)
    legend_box = legend.get_window_extent(renderer)
    scale_box = next(t for t in ax.texts if t.get_text() == "보통이다").get_window_extent(renderer)
    print(f"Vertical text-box gap: scale to title={scale_box.y0-title_box.y1:.2f} px; "
          f"title to legend={title_box.y0-legend_box.y1:.2f} px")
    png = OUT / "fig_3_11_chart_v6.png"
    svg = OUT / "fig_3_11_chart_v6.svg"
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(svg, facecolor="white")
    plt.close(fig)
    with Image.open(png) as im:
        print(f"PNG: {im.size}; dpi={im.info.get('dpi')}; 150 x 98 mm; {png.relative_to(ROOT)}")
    text_nodes = ET.parse(svg).findall(".//{http://www.w3.org/2000/svg}text")
    assert len(text_nodes) >= 30, "SVG text was unexpectedly converted to paths"
    print(f"SVG: editable text nodes={len(text_nodes)}; {svg.relative_to(ROOT)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true",
                        help="Repeat the optional raw-data check (already passed for draft 1).")
    args = parser.parse_args()
    if args.verify_source:
        verify_source()
    draw()
