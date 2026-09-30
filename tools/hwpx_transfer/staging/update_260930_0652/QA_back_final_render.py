# QA_back_final_render: 지정 물리 쪽을 130dpi PNG로 저장(읽기 전용). 사용: python QA_back_final_render.py PDF 91 104 ...
import sys, pymupdf
doc = pymupdf.open(sys.argv[1])
for a in sys.argv[2:]:
    doc[int(a) - 1].get_pixmap(dpi=130).save(f'QA_back_final_p{int(a):03d}.png')
    print('saved', a)
