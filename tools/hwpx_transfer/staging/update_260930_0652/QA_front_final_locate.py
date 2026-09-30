# QA_front_final: 변경된 8개 표의 캡션으로 PDF 쪽을 찾고, 괘선 범위·꼬리말 여유를 재고, 표 영역 PNG를 만든다(읽기 전용).
import sys, re, pymupdf
PDF = sys.argv[1] if len(sys.argv) > 1 else 'layout2_saved.pdf'
CAPS = {1: '<표 2-1>', 3: '<표 2-3>', 8: '<표 3-1>', 9: '<표 3-2>', 10: '<표 3-3>', 12: '<표 3-5>', 13: '<표 3-6>', 15: '<표 3-8>'}
d = pymupdf.open(PDF)
norm = lambda s: re.sub(r'\s', '', s)
print(PDF, 'pages', len(d))
for idx, cap in CAPS.items():
    key = norm(cap)
    hits = [i for i in range(12, len(d)) if key in norm(d[i].get_text())]
    for i in hits:
        p = d[i]
        if sum(1 for r in p.get_drawings() if r['rect'].height < 2 and r['rect'].width > 20) < 4: continue
        ws = p.get_text('words')
        foot = [w for w in ws if w[1] > 735 and re.fullmatch(r'-|\d+', w[4])]
        folio = ''.join(w[4] for w in foot)
        capw = [w for w in ws if norm(w[4]).startswith('<표') and w[1] < 740]
        hl = sorted({round(r['rect'].y0, 1) for r in p.get_drawings() if r['rect'].height < 2 and r['rect'].width > 20})
        body = max((w[3] for w in ws if w[3] <= 740), default=0)
        print(f'idx{idx} {cap} phys{i+1} folio[{folio}] hlines {hl[:1]}..{hl[-1:]} n={len(hl)} body_max={body:.1f}')
        y0 = max(60, (hl[0] if hl else 100) - 40); y1 = min(841, (hl[-1] if hl else 700) + 45)
        p.get_pixmap(dpi=130, clip=pymupdf.Rect(70, y0, 525, y1)).save(f'QA_front_final_idx{idx}_p{i+1:03d}.png')
