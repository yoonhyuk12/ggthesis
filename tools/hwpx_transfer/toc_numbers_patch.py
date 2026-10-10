# 재조판 PDF에서 확정한 인쇄 쪽수(toc_pages_from_pdf.py 산출 JSON)를 기존 hwpx의 목차·표목차·그림목차 문단에 써 넣는 도구
"""toc_numbers_patch.py — section1 목차 문단의 탭 뒤 쪽수만 바꾼다(제목·서식 불변).

사용: PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/toc_numbers_patch.py <in.hwpx> <toc_pages.json> <out.hwpx>
  - toc_pages.json 은 toc_pages_from_pdf.py 산출({"toc":{제목:쪽|[쪽,…]}, "lot":…, "lof":…}). 같은 제목이 두 번(부록 Part A∼C)이면
    문서 순서대로 리스트를 소비한다.
  - 바뀐 문단의 <hp:linesegarray>만 제거한다. 다른 엔트리는 바이트 그대로 복사한다.
  - 이 도구 뒤에는 반드시 한글 재조판 저장과 PDF 재대조가 따른다(쪽수 갱신으로 쪽이 밀릴 수 있다).
2026-10-09 작성(스모크·최종본 갱신에 쓴 인라인 스크립트를 도구화).
"""

import html
import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")


def main(src, pages_json, dst):
    pdf = json.load(open(pages_json, encoding="utf-8"))
    want = {}
    for kind in ("toc", "lot", "lof"):
        for t, v in pdf[kind].items():
            want[t] = [str(x) for x in (v if isinstance(v, list) else [v])]
    zin = zipfile.ZipFile(src)
    s1 = zin.read("Contents/section1.xml").decode("utf-8")
    used = {t: 0 for t in want}
    state = {"changed": 0, "same": 0, "missing": []}

    def fix(m):
        p = m.group(0)
        if "<hp:tab" not in p:
            return p
        before, after = p.split("<hp:tab", 1)
        title = html.unescape("".join(re.findall(r"<hp:t(?:\s[^>]*)?>([^<]*)", before))).strip()
        if title not in want:
            state["missing"].append(title)
            return p
        k = used[title]
        used[title] += 1
        new = want[title][min(k, len(want[title]) - 1)]
        mm = re.search(r"(/>)([^<]*)(</hp:t>)", after)
        if not mm:
            state["missing"].append("no-num:" + title)
            return p
        if mm.group(2).strip() == new:
            state["same"] += 1
            return p
        after2 = after[:mm.start(2)] + new + after[mm.end(2):]
        p2 = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", before + "<hp:tab" + after2, flags=re.S)
        state["changed"] += 1
        return p2

    s1n = re.sub(r"<hp:p\b.*?</hp:p>", fix, s1, flags=re.S)
    with zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "Contents/section1.xml":
                data = s1n.encode("utf-8")
            zout.writestr(info, data, compress_type=info.compress_type)
    print("목차 쪽수 치환:", state["changed"], "| 그대로:", state["same"], "| 미매칭:", state["missing"])
    return state


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
