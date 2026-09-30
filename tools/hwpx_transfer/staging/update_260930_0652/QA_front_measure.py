# QA_front 측정 스크립트(읽기 전용): reflowed.pdf 1~75쪽의 꼬리말 침범·표 이동으로 생긴 앞쪽 여백·표 높이를 좌표로 측정한다.
# 사용: python QA_front_measure.py   (출력만, 파일 쓰기 없음)
import pymupdf
FOOT_TOP = 742.4  # '- n -' 꼬리말 글자 상단(pt)
d = pymupdf.open('reflowed.pdf')

def body_max(pg):
    ws = [w for w in d[pg - 1].get_text('words') if w[3] <= 745]
    return max((w[3] for w in ws), default=0)

def table_box(pg):
    rs = [r['rect'] for r in d[pg - 1].get_drawings() if r['rect'].height < 2 and r['rect'].width > 20]
    return (min(r.y0 for r in rs), max(r.y1 for r in rs)) if rs else None

print('page body_max_y footer_top margin')
over = [(p, body_max(p)) for p in range(4, 76) if body_max(p) > FOOT_TOP - 20]
print('footer-near(<20pt):', over)
# 표가 통째로 다음 쪽으로 이동해 생긴 앞쪽 여백 vs 표(제목 포함) 높이
for prev, tpg, name in [(26, 27, '표2-3'), (47, 48, '표3-1'), (60, 61, '표3-3'), (65, 66, '표3-5'), (70, 71, '표3-8'), (33, 34, '표2-4')]:
    free = FOOT_TOP - body_max(prev)
    y0, y1 = table_box(tpg)
    cap = [w for w in d[tpg - 1].get_text('words') if w[4].startswith('<표') and w[3] < y0 + 1]
    top = min([w[1] for w in cap] + [y0])
    print(f'{name}: 앞쪽 p{prev} 잔여 {free:.0f}pt / 표+제목 높이 {y1 - top:.0f}pt (부족 {y1 - top - free:.0f}pt)')
