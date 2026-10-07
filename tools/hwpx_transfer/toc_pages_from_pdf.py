"""조립본 section1의 목차·표목차·그림목차 항목(탭 앞 제목)을 뽑아 한글 재조판 PDF에서 각 항목의
**첫 시작 쪽의 인쇄 쪽수**(꼬리말 '- n -' 텍스트)를 찾아 `--toc-pages`용 JSON을 만든다.

사용: PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/toc_pages_from_pdf.py <조립 hwpx> <재조판 PDF> <out.json>
규칙(hwpx-table-layout): PDF 물리 인덱스나 고정 오프셋을 쓰지 않고 쪽마다 추출한 인쇄 쪽수를 쓴다. 본문 참조문
("<표 3-7>·<표 3-8>의 결과를 참조")과 캡션을 구분하기 위해 캡션 전문으로 맞추며, 같은 제목이 두 번 나오는
부록 Part A∼C는 문서 순서대로 리스트에 담는다(조립기 `_page_of`가 순서대로 소비). 2026-10-08 작성.
"""
import sys, re, json, zipfile
sys.stdout.reconfigure(encoding="utf-8")
from pypdf import PdfReader
hwpx, pdf, out = sys.argv[1:4]
s1 = zipfile.ZipFile(hwpx).read("Contents/section1.xml").decode("utf-8")
entries = []  # (kind, title)
for p in re.findall(r"<hp:p\b.*?</hp:p>", s1, flags=re.S):
    if "<hp:tab" not in p: continue
    # 목차 문단은 <hp:t>제목<hp:tab …/>쪽수</hp:t> 꼴 — 탭 앞 텍스트가 제목(여러 run이면 이어 붙인다)
    before = p.split("<hp:tab")[0]
    title = "".join(re.findall(r"<hp:t(?:\s[^>]*)?>([^<]*)", before))
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").strip()
    if not title: continue
    kind = "lot" if title.startswith("<표") else "lof" if title.startswith("<그림") else "toc"
    entries.append((kind, title))
norm = lambda t: re.sub(r"\s+", "", t)
r = PdfReader(pdf)
pn_re = re.compile(r"^-\s*([0-9]+|[ivxlcdm]+)\s*-$")
pages = []
for i, pg in enumerate(r.pages):
    lines = [l.strip() for l in (pg.extract_text() or "").splitlines() if l.strip()]
    pns = [pn_re.match(l).group(1) for l in lines if pn_re.match(l)]
    pages.append({"pdf": i + 1, "printed": pns[0] if pns else None, "lines": [norm(l) for l in lines]})
# 본문 쪽(숫자 쪽번호)만 — 인쇄 쪽수는 pdf 인덱스 - 고정 오프셋이 아니라 쪽마다 추출한 값을 쓴다
body = [p for p in pages if p["printed"]]  # 로마 숫자 전면부(감사의 글 등)도 목차 대상
# 본문 첫 쪽(장 제목 쪽은 쪽번호 숨김)은 다음 쪽 번호 - 1로 보정
digits = [p for p in body if p["printed"].isdigit()]
first_body_pdf = min(p["pdf"] for p in digits) - 1
for p in pages:
    if p["pdf"] == first_body_pdf and p["printed"] is None:
        p["printed"] = str(int(digits[0]["printed"]) - 1)
        body.append(p); body.sort(key=lambda q: q["pdf"])
result = {"toc": {}, "lot": {}, "lof": {}}
unmatched = []
start_pdf = 1  # 목차 항목은 문서 순서이므로 직전 항목의 쪽부터 찾는다(중복 제목 Part A~C 구분)
cap_skip = re.compile(r"^<(표|그림)\d+-\d+>[^<]*(과같|에서|의수치|를참조|와같)")
for kind, title in entries:
    key = norm(title)  # 표·그림도 캡션 전문으로 맞춘다 — "<표 3-7>·<표 3-8>의 결과를 참조" 같은 본문 참조와 구분
    hit = None
    cands = body if kind == "toc" else [p for p in body if p["printed"].isdigit()]  # 표·그림은 본문 쪽만
    if kind == "toc":
        cands = [p for p in cands if p["pdf"] >= start_pdf]
    for p in cands:
        for l in p["lines"]:
            if "····" in l:
                continue  # 목차 쪽의 점선 항목은 제외
            if kind == "toc":
                # 제목이 두 줄로 꺾인 경우 PDF 첫 줄은 제목의 접두 문자열이다
                ok = (l.startswith(key) and len(l) <= len(key) + 2) or (len(l) >= 10 and key.startswith(l))
            else:
                ok = (l.startswith(key) and len(l) <= len(key) + 2) or (len(l) >= 12 and key.startswith(l))
            if ok:
                hit = p["printed"]; hit_pdf = p["pdf"]; break
        if hit: break
    if hit is None:
        unmatched.append(title)
    else:
        val = int(hit) if hit.isdigit() else hit
        if kind == "toc":
            start_pdf = hit_pdf
            if title in result["toc"]:
                prev = result["toc"][title]
                result["toc"][title] = (prev if isinstance(prev, list) else [prev]) + [val]
            else:
                result["toc"][title] = val
        else:
            result[kind][title] = val
json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("entries:", len(entries), "matched:", sum(len(v) for v in result.values()), "unmatched:", unmatched)
for k in ("toc", "lot", "lof"):
    print(k, list(result[k].items())[:4], "...", list(result[k].items())[-2:])
