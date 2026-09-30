# QA_front_final: 3-6 머리행 확대, 8개 표의 앞쪽 여백·마지막 행·꼬리말 여유 측정(읽기 전용)
import pymupdf, re
d = pymupdf.open('layout2_saved.pdf')
p = d[65]
p.get_pixmap(dpi=300, clip=pymupdf.Rect(75, 125, 520, 200)).save('QA_front_final_t3-6_header_zoom.png')
hl = sorted({round(r['rect'].y0, 1) for r in p.get_drawings() if r['rect'].height < 2 and r['rect'].width > 20})
print('3-6 hlines', hl[:4])
for w in p.get_text('words'):
    if 140 < w[3] < 180 and 180 < w[0] < 300: print('  hdr word', [round(v, 1) for v in w[:4]], w[4])
for idx, pg in ((1, 22), (3, 27), (8, 47), (9, 50), (10, 60), (12, 65), (13, 66), (15, 69)):
    q = d[pg - 1]; prev = d[pg - 2]
    hl = sorted({round(r['rect'].y0, 1) for r in q.get_drawings() if r['rect'].height < 2 and r['rect'].width > 20})
    ws = q.get_text('words')
    inside = [w for w in ws if hl[0] - 30 < w[1] < hl[-1] + 2]
    last_text = max(w[3] for w in inside if w[1] < hl[-1])
    prev_body = max((w[3] for w in prev.get_text('words') if w[3] <= 740), default=0)
    print(f'idx{idx} p{pg}: table {hl[0]}–{hl[-1]} last_cell_text_bottom {last_text:.1f} (<= bottom line {hl[-1]}) footer_gap {742.4 - hl[-1]:.1f}pt | prev p{pg-1} body_max {prev_body:.1f} free {742.4 - prev_body:.0f}pt')
