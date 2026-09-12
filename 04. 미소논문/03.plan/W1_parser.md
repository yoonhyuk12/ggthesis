# W1 — MD 파서 개조 (md_to_blocks.py → 미소 원고)

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다.

## 목표
`04. 미소논문/tools/hwpx_transfer/md_to_blocks.py`(윤혁 원고용 사본)를 미소 원고에 맞게 고쳐, 인자 없이 실행하면 `04. 미소논문/01.docs/*.md`를 읽어 `04. 미소논문/tools/hwpx_transfer/staging/*.blocks.json`과 `parse_report.md`를 만들게 한다. **원고 텍스트를 한 글자도 바꾸지 않는 결정적 파서**라는 성격은 유지한다.

## 수정 사항
1. `SRC_DIR`을 `04. 미소논문/01.docs`(스크립트 기준 `parents[2] / "01.docs"`)로. `FILES` 맵:
   - `01.서론.md`→ch01, `02.이론적배경.md`→ch02, `03.시스템개발.md`→ch03, `04.연구설계.md`→ch04, `05.실증분석결과.md`→ch05, `06.결론.md`→ch06, `07.부록.md`→apx1, `07-2. 설문근거.md`→apx2
   - `00.목차.md`는 **국문초록 절만** 파싱해 `front.blocks.json`으로 낸다(표지·목차·표/그림 목차 절은 제외 — 목차는 조립기가 본문에서 생성). `> [작성 가이드] …` 인용구는 제외하고 `excluded`에 기록.
   - `08.참고문헌.md`는 파싱하지 않는다(W2 담당).
2. **그림 이미지 블록 신설.** `![alt](그림/파일.png)` 한 줄 → `{"type":"figure_image","path":"그림/파일.png","alt":"alt"}`. 경로는 `01.docs/` 기준 상대경로 그대로. 파일이 실제로 존재하는지 확인해 없으면 이벤트 `figure_missing`으로 보고.
3. 그림 캡션 인식 확장: 원고는 `` `<그림 1-1>` 2023년 … ``(백틱), `<그림 3-1> …`, `**<그림 4-1> 실험설계 모형**`(굵게) 세 형태다. 백틱·굵게 마커를 벗긴 뒤 `<그림 `으로 시작하면 `figure_caption`으로 본다(텍스트에서 마커만 제거). 표 캡션도 같은 방식(`<표 `).
4. `####` 소제목은 기존 `h4` 블록 그대로. `#` 5단 이상은 없다고 가정하되 있으면 이벤트로 보고.
5. **편집용 섹션 제외 규칙 확장.** `EDITORIAL_H_RE`에 `구 설계 보존 자료|잔여 과제` 를 추가해 `07-2. 설문근거.md`의 `## 4. 잔여 과제`, `## 5. 구 설계 보존 자료 …`(하위 h3·h4·표 포함)를 통째로 excluded 처리. 제외된 헤딩·행 수를 `parse_report.md`에 명시.
6. HTML 주석: 한 줄 `<!-- … -->` 외에 **여러 줄에 걸친** `<!--` … `-->` 블록(08.참고문헌·00.목차에 있음)도 제외하도록 처리. `<div align="center">`·`<br>`·`---` 처리는 기존 로직 확인 후 필요한 만큼만 보완.
7. 인용구(`> …`) 처리: 기존 파서가 어떻게 하는지 확인하고, **본문 안의 인용구가 있으면 그 내용을 문단(`p`)으로 유지**하되 `[작성 가이드]`로 시작하는 인용구만 excluded. 어느 쪽이든 parse_report에 목록화.
8. 표 셀 안 `<br>`·`**굵게**`·`\|` 처리는 기존 로직 유지. 셀에 `` ` ``이 있으면 마커만 제거.

## 완료 기준 (증거를 worker_done에 첨부)
- `PYTHONIOENCODING=utf-8 python "04. 미소논문/tools/hwpx_transfer/md_to_blocks.py"` 가 exit 0
- `parse_report.md`에 파일별 블록 통계(h1/h2/h3/h4/p/table/table_rows/table_caption/figure_caption/figure_image/excluded)와 **커버리지 검사(원고 비어 있지 않은 행 중 블록에 반영되지 않은 행 = 0, 제외 목록은 별도 표)** 가 나온다. 기존 파서의 커버리지 검사(`norm()` 비교)를 그대로 돌려 미반영 행이 0임을 보인다
- 표 `header`/`rows` 열 수 불일치 0건(불일치가 있으면 원고 행 번호와 함께 보고 — 고치지 말 것)
- figure_image 6건(그림 1-1, 1-2, 3-1, 3-2, 3-3, 4-1)과 짝 캡션 6건이 각각 인식됨
- 블록 JSON 스키마는 기존(`{"source":…, "blocks":[…]}`)과 동일해야 한다(W4 조립기가 소비). 새 타입은 `figure_image`뿐이다

## 산출물
- `tools/hwpx_transfer/md_to_blocks.py`(수정), `tools/hwpx_transfer/staging/{ch01..ch06,apx1,apx2,front}.blocks.json`, `tools/hwpx_transfer/staging/parse_report.md`
