"""재조판 PDF 전 표 점검(PyMuPDF): 쪽마다 표 괘선(수평 직선)의 최하단 y와 꼬리말 쪽번호 y를 비교해
꼬리말 침범(overlap)을 찾고, 결과를 <pdf>_tables.json으로 남긴다. 육안 확인(렌더 PNG)과 함께 쓴다.

사용: PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/pdf_table_check.py <재조판 PDF>
한계: 괘선 없는 표·그림 테두리도 잡힐 수 있고, 표 식별은 쪽 단위다(어느 표인지는 캡션 색인과 대조). 2026-10-08 작성.
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
import pymupdf
pdf = sys.argv[1]
doc = pymupdf.open(pdf)
rows = []
for pno, page in enumerate(doc, 1):
    h = page.rect.height
    # 꼬리말 쪽번호 위치
    footer_y = None; footer_txt = None
    for b in page.get_text("blocks"):
        t = b[4].strip()
        if re.fullmatch(r"-\s*([0-9]+|[ivxlcdm]+)\s*-", t) and b[1] > h * 0.85:
            footer_y = b[1]; footer_txt = t
    # 표 괘선: 수평 직선(길이 > 60pt)
    hlines = []
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.5 and abs(p1.x - p2.x) > 60:
                    hlines.append((p1.y, min(p1.x,p2.x), max(p1.x,p2.x)))
            elif it[0] == "re":
                r = it[1]
                if r.width > 60 and r.height < 1.5:
                    hlines.append((r.y0, r.x0, r.x1))
    if not hlines: continue
    ymax = max(y for y,_,_ in hlines); ymin = min(y for y,_,_ in hlines)
    # 본문 텍스트 최하단(꼬리말 제외)
    body_bottom = max([b[3] for b in page.get_text("blocks") if not (footer_y and b[1] >= footer_y - 2)] or [0])
    rows.append({"page": pno, "footer": footer_txt, "footer_y": round(footer_y,1) if footer_y else None,
                 "table_top": round(ymin,1), "table_bottom": round(ymax,1), "body_bottom": round(body_bottom,1),
                 "page_h": round(h,1), "overlap": bool(footer_y and ymax > footer_y - 4)})
json.dump(rows, open(pdf[:-4] + "_tables.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
over = [r for r in rows if r["overlap"]]
nofoot = [r["page"] for r in rows if r["footer"] is None]
print("pages with table lines:", len(rows))
print("overlap with footer:", [(r["page"], r["table_bottom"], r["footer_y"]) for r in over])
print("table pages without footer number:", nofoot)
# 가장 아래까지 내려간 표 상위 8개
for r in sorted(rows, key=lambda r: -r["table_bottom"])[:8]:
    print(" p%d table_bottom=%.1f footer_y=%s" % (r["page"], r["table_bottom"], r["footer_y"]))
