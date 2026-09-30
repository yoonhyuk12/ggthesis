# QA_front 증거 크롭 생성(읽기 전용 PDF → QA_front_*.png)
import pymupdf
d = pymupdf.open('reflowed.pdf')
C = [('toc_p004', 4, 100, 780), ('lot_p008', 8, 100, 700), ('lof_p010', 10, 100, 280),
     ('t2-1_p022', 22, 150, 670), ('t2-3_p026_p027a', 26, 540, 745), ('t2-3_p027', 27, 125, 475),
     ('t2-6_p039_end', 39, 480, 640), ('t2-7_p040_widow', 40, 540, 745), ('t3-2_p051', 51, 125, 390),
     ('t3-6_p067', 67, 125, 380), ('t3-3_p061', 61, 105, 370), ('t3-8_p070_blank', 70, 340, 745)]
for name, pg, y0, y1 in C:
    d[pg - 1].get_pixmap(dpi=110, clip=pymupdf.Rect(70, y0, 525, y1)).save(f'QA_front_{name}.png')
print(len(C))
