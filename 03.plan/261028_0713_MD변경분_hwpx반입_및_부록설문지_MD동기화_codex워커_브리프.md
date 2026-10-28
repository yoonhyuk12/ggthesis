# 2026-10-28 MD 변경분 hwpx 반입 + 부록 설문지 MD 동기화 — Codex 워커 브리프

사용자 지시: "이제 hwpx에 반영해줘, 그리고 설문 문항이 md 파일과 hwpx가 맞지 않는데.. 그것도 확인해서 다시 써줘 codex 워커 시켜" (2026-10-28 07:1x). hwpx 쓰기·한글 COM 조작을 메인이 단독 수행한다는 규칙은 이 지시로 **이번 작업에 한해** Codex 워커 1명(단독·순차)에게 위임한다. 같은 파일에 쓰는 다른 워커는 없다.

작업은 두 덩어리다. **A. 오늘 MD 변경분 반입**(표준 파이프라인) → **B. 부록 설문지 두 벌을 `01.docs/부록1_설문지_양식.md` 기준으로 다시 쓰기**(hwpx XML 직접 수술). 순서는 A → B → 재조판·검증이며, 한 파일 위에서 순차로 한다.

## 0. 기준본·양식 원본·작업 폴더

- **기준본(최신본):** `00. hwpx/261028_0644_경기공학_건축안전_윤혁_논문_자연화반영본.hwpx` — SHA256 `eddab53be59038e36822640f7bfc6c3a1f1f5674b45ddbf614c3d66bb3130f18`. 사용자가 한글에서 직접 고친 표 열폭(표 4-7·4-10·4-11·4-12·4-13·4-14)이 들어 있다. **제자리 수정 금지, 작업 전후 SHA 불변 확인.**
- **양식 원본(김정년):** 워킹트리의 `00. hwpx/`에 없다(git status `D`). **복원하지 말고** git HEAD에서 작업 폴더로만 꺼낸다:
  ```bash
  git show "HEAD:00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx" > tools/hwpx_transfer/staging/survey_261028/template_kjn.hwpx
  sha256sum tools/hwpx_transfer/staging/survey_261028/template_kjn.hwpx   # 9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3
  ```
- **작업 폴더:** `tools/hwpx_transfer/staging/survey_261028/` (이미 있다). 기준본 전 섹션 문단 덤프 `base_paras_261028_0644.json`(`{section, idx, text}`, 표 셀 문단 포함 문서 순서)이 들어 있다. **hwpx 본문을 읽을 때는 이 덤프나 Python `zipfile`+`ElementTree`만 쓴다.** hwpx MCP·rhwp MCP는 읽기 도구까지 전부 금지(2.5MB 본문에 40분 멈춤 사고).
- 직전 성공 실행 기록: `03.plan/261028_0637_자연화분_hwpx반입_codex워커_브리프.md` 진행 기록. 같은 절차·같은 환경 우회(이 PC에 `pwsh` 없음 → Windows PowerShell에서 `resave-hwpx.ps1`을 UTF-8로 읽어 scriptblock 실행, `$OutputEncoding` UTF-8)를 쓴다. Python 앞에는 반드시 `PYTHONIOENCODING=utf-8`.

## A. 반입할 MD 변경분 (오늘 06:47~07:05, 전부 `01.docs/`)

기준본은 06:41 조립본을 반입한 것이므로 그 뒤 MD 변경분만 들어간다. 장 구성·표 번호·목차 항목은 바뀌지 않았다(`--toc-from-fresh` 불필요).

| 파일 | 위치 | 변경 |
| --- | --- | --- |
| `01_서론.md` | 제3절 연구 방법 문단 | "Google Forms 온라인 자기응답 설문" → "자기응답 설문" |
| `01_서론.md` | 제3절 시간적 범위 문단 | "조사는 2026년 10월에 사후 설문으로" → "조사는 2026년 10월 12일부터 10월 23일까지 사후 설문으로" |
| `04_…md` | 제3절 자료 수집 문단("자료는 2026년 …") | Google Forms·단일 링크·계정 로그인 구절 제거, "2026년 10월 12일부터 10월 23일까지" 삽입, "설문 계정 권한·" 삭제 |
| `04_…md` | **<표 4-5> 자료 수집 개요** '조사 방식' 행 | "Google Forms 온라인 자기응답, … 단일 링크 안내 후" → "자기응답 설문, … 안내 후" |
| `04_…md` | **<표 4-5>** '조사 시기·기준기간' 행 | "2026년 10월 실시" → "2026년 10월 12일∼10월 23일 실시" |
| `04_…md` | 제6절 제1항 표본 선정 문단("도입 표본의 선정은…") | "설문 링크를 안내하였다" → "설문을 안내하였다" |
| `04_…md` | 제6절 제1항 설문 기간 문단 | **두 문단이 한 문단으로 합쳐졌다.** 옛 "조사는 2026년 10월 Google Forms 단일 링크로 … 뺀 응답은 없다."(긴 문단)와 그 다음 "자료 정제와 채점은 제3절 제1항과 … 현장 수는 같다." 두 문단이 → "설문은 2026년 10월 12일부터 10월 23일까지 받았다. 연구자가 설치·운용 상태를 아는 현장에 설문을 안내하였다. 자료 정제와 채점은 제3절 제1항과 제5절 제2항의 규칙을 따른다. 부분 무응답은 대체하지 않고 분석별 완전사례를 사용하며, 현장당 1명이므로 개인 수와 현장 수는 같다." 한 문단. **기준본 문단 하나가 사라져야 한다.** 패치 결과에 옛 긴 문단이나 "자료 정제와 채점은"으로 시작하는 별도 문단이 남으면 안 된다 |
| `04_…md` | <표 4-7> 아래 "주: 도입 분류는…" 문단 | 긴 주석을 두 문장으로 줄임("…기록하지 않았다. 역할은 ‘기타’ 응답을 응답자에게 재확인하여 세 범주로 재분류한 값이다.") |
| `04_…md` | **<표 4-11> 공분산분석 가정 점검 결과** '관측의 독립성' 행 | 점검 내용 "현장당 1명 여부·현장 간 업무 공유 확인", 결과 "현장당 1명에게만 설문을 안내하여 모집 단계에서 현장 중복을 막았다", 판단 "독립 관측으로 분석하였다" (개별 대조·제출시각 서술 삭제) |
| `04_…md` | 제7절 가정 점검 문단("H1 모형은 회귀기울기 동질성…") | 끝 문장 "관측의 독립성은 … 모집 방식에 근거한다."로 축약, "링크를 안내" → "설문을 안내" |

**표 2개가 바뀐다(표 4-5, 표 4-11).** `patch_from_fresh`는 내용이 바뀐 표를 조립본 표로 교체하므로 사용자가 한글에서 고친 **표 4-11의 열폭이 사라진다.** 처리: 교체 뒤 기준본 표 4-11과 조립본 표 4-11의 격자(rowCnt·colCnt·병합)가 같음을 확인하고, **기준본의 `hp:tblcol`/`cellSz` 폭을 교체된 표에 다시 적용**한다(전체 폭 `hp:sz@width` 보존, 열폭 합 = 전체 폭). 표 4-5는 사용자 조정 표 목록에 없으므로 조립본 그대로 둔다. 드라이런에서 '사용자 병합 표'로 막히면 `--force-fresh "<표 4-11>"`를 쓰고 위 열폭 재적용을 한다. 그 밖의 표가 교체 목록에 나오면 **멈추고 `ask`**.

## B. 부록 설문지 두 벌을 MD 기준으로 다시 쓴다

### 왜 안 맞는가
조립 파이프라인은 `tools/hwpx_transfer/staging/migrate_kjn/transplant.json`의 `부록1_설문지` 항목대로 **옛 hwpx(261004_0607)의 부록 설문지(section2 문단 630~694 구간)를 통째 이식**한다(공사비 구간 치환 1건만 적용). 그 뒤 MD `부록1_설문지_양식.md`가 여러 번 바뀌었는데(`설문항목_작업이력.md` 10-09·10-10·10-12 항목) 이식본은 10-04판 그대로다. **단일 원본은 MD다.** hwpx를 MD에 맞춘다. MD를 고치지 않는다.

### 기준본 부록 위치(덤프 `base_paras_261028_0644.json`, section 2)
- 도입 현장 벌: idx 2357("부   록 (도입 현장)") ~ 2648("끝까지 응답해 주셔서…")
- 미도입 현장 벌: idx 2649("부   록 (미도입 현장)") ~ 2809
- 패치(A) 뒤에는 idx가 밀리므로 **패치본을 다시 덤프해서** 위치를 잡는다. 텍스트 앵커("부   록 (도입 현장)" 등)로 찾는다.

### 메인이 확인한 불일치(워커가 전수 대조해 보고서에 표로 먼저 적는다 — 아래는 출발점이지 전부가 아니다)
1. **조사 관리용 입력:** hwpx는 "배포코드: [입력] / 성명: [입력]"과 "A∼E의 측정 문항 수(18문항 또는 30문항)". MD는 첫 질문 '현장 구분'(① CCTV YOLO-LLM 안전알림 도입 현장 ② … 미도입 현장), '현장명: [입력]'(안내 2줄: "현재 담당하시는 현장명을 적어 주십시오." "예시 : 00지구 수리시설개보수사업"), '성명: [입력]', 문항 수 "21문항 또는 33문항", 안내 문단 두 개의 문장이 다르다. MD의 해당 절 전문을 그대로 쓴다.
2. **Part A 제목·안내:** hwpx "Part A. 인구통계학적 특성" / "…일반적 사항에 관한 질문입니다." → MD "Part A. 인구통계학적 특성 및 현장 운영 특성" / "…일반적 사항과 현장 운영 특성에 관한 질문입니다."
3. **A-4:** hwpx "귀하의 건설현장 근무 경력은? (…)" + "(   )년 (   )개월" + "※ 여러 현장이나 … 개월은 연수를 제외한 …" → MD "귀하의 건설현장 근무 경력은 약 몇 년입니까? (…)" + "만 (   )년" + "※ 1년 미만은 0으로, 6개월 이상은 1년으로 올려 적어 주십시오. 여러 현장이나 업무의 근무 기간이 겹치면 같은 기간을 중복하여 합산하지 마십시오."
4. **A-7·A-8·A-9와 ※ 안내 2줄이 hwpx에 없다.** MD Part A 끝의 세 문항(보기 포함)과 "※ A-7∼A-9는 설문 응답일 직전 1개월 …", "※ A-7의 ‘안전관리 담당자’는 …"를 A-6 ※ 안내 뒤에 넣는다. `patch_from_fresh.py --appendix <spec.json>`이 A-6 문단(라벨/보기/※)을 복제해 두 벌에 넣는 기능을 이미 갖고 있다(`appendix_insert`, `label_template`·`anchor_startswith`·`count:2`·`items[kind=label|option|note]`). 쓸 수 있으면 쓰고, 맞지 않으면 같은 방식으로 직접 복제한다. A-7 보기는 두 줄(①②③ / ④⑤), A-8·A-9는 한 줄이다.
5. **Part B 안내 둘째 문장:** MD는 "설문 응답일 직전 1개월을 기준으로, 순찰과 순찰 사이나 안전관리 담당자가 현장에 없는 시간대에 생긴 위험 상황까지 포함하여 각 문항을 읽고 …"로 바뀌었다.
6. **Part D·E의 '비해당' 열 삭제(2026-10-12):** hwpx 격자는 번호·문항·①∼⑤·비해당(점수 아님)의 8열이고 각 행 끝에 "비해당" 셀이 있다. MD는 ①∼⑤ 5점만 쓴다(7열). **열을 지우고 colCnt를 7로 줄이며, 지운 열의 폭을 문항 열에 더해 전체 폭(`hp:sz@width`)을 보존**한다. 머리행 병합(colSpan)도 맞춘다. Part D·E 안내문에서 "해당 경험이 없어 판단할 수 없는 문항은 1∼5점 대신 별도의 비해당을 선택해 주십시오." 문장과 Part E 안내의 "같은 현장의 도입 전 …" 이하 문장은 MD에 없으므로 MD 문장으로 바꾼다. Part D·E 제목 아래에 MD의 도입 문장 "다음은 CCTV YOLO-LLM 안전알림 시스템을 사용한 경험에 관한 질문입니다."를 한 문단 넣는다.
7. **표지 문단:** 문장 단위로 MD 표지와 대조한다. 최소한 "안내받은 Google Forms 설문에서 직접 응답을 입력하거나 선택한 뒤 제출해 주십시오."와 개인정보 문단("현장 명부 연결과 중복 제출 확인을 위해 현장명과 성명을 수집하며, …")이 MD와 글자 그대로 같아야 한다. 표지의 기준본 레이아웃(제목 3줄·오른쪽 정렬 소속/지도교수/연구자/이메일 블록)은 유지하고 글자만 맞춘다.
8. **공통 안내 2줄(※ Part A는…, ※ 본 설문조사는 2026년 10월에 실시할 계획입니다.)**은 MD에도 그대로 있으므로 유지한다.
9. 위 모두를 **도입 벌·미도입 벌 두 곳에 같이** 적용한다(D·E는 도입 벌에만). 감사 문구 "끝까지 응답해 주셔서 진심으로 감사합니다."는 기준본처럼 각 벌 끝에 한 번씩.

### 메인의 결정(워커는 따르고, 의문이 있으면 `ask`)
- 부록은 **실제 배포한 설문지의 재현**이므로 MD 부록1의 Google Forms·Google 계정 언급을 그대로 둔다(본문 4장에서 지운 것과 다른 결정이다. 보고서에 이 점을 적어 메인이 사용자에게 알린다).
- MD의 `>` 인용 블록(동기화 기준 메모, 변경 기록, 양식 구성 메모, 방법론적 주석, "도입 현장용은 이 표지에 이어…" 안내)과 `## [내부 관리용 — 배포본에서 삭제] 구성 대조표` 절은 **싣지 않는다.** `<div>` 정렬 지시는 서식(오른쪽/가운데 정렬)으로만 옮긴다. `&emsp;`는 기준본의 같은 자리 들여쓰기(공백)로 바꾼다.
- `[입력]`은 설문 양식 라벨이므로 **검정**이다. 빨간 마커 접두사(`[DATA PENDING`·`[확정 필요`·`[CITE_TODO`·`[그림 삽입 예정`·`[UNVERIFIED`)만 빨강.
- 문단 텍스트·서식이 바뀐 모든 문단과 영향받는 표 앵커 문단의 `<hp:linesegarray>`를 제거해 한글이 다시 계산하게 한다. 무관한 문단 캐시는 건드리지 않는다. `pageBreak="CELL"`·글자 축소·행 높이 축소 금지. 새 문항 행은 기존 행(A-6, D-8, E-4)의 charPr·paraPr을 그대로 복제해 쓴다.
- 쪽 넘김은 [표 생성·배치 규칙](../.claude/rules/hwpx-table-layout.md) 3단계(새 쪽 → 열폭 → `pageBreak="TABLE"`+`repeatHeader`)만 쓴다.

## C. 절차 (저장소 루트에서 실행)

1. **1단계 블록 생성.** `python tools/hwpx_transfer/md_to_blocks.py` → `staging/ch01~ch05.blocks.json`, `apx1.blocks.json`, `parse_report.md`. 누락 0 확인.
2. **2단계 조립본.** 양식 원본 사본 위에 조립(직전 브리프와 같은 인자, 출력만 `staging/survey_261028/fresh.hwpx`, 보고서 `fresh_report.md`):
   ```
   python tools/hwpx_transfer/blocks_to_hwpx.py --template tools/hwpx_transfer/staging/survey_261028/template_kjn.hwpx --profile tools/hwpx_transfer/staging/migrate_kjn/style_map_kjn.json --blocks tools/hwpx_transfer/staging/ch01.blocks.json tools/hwpx_transfer/staging/ch02.blocks.json tools/hwpx_transfer/staging/ch03.blocks.json tools/hwpx_transfer/staging/ch04.blocks.json tools/hwpx_transfer/staging/ch05.blocks.json tools/hwpx_transfer/staging/apx1.blocks.json --references tools/hwpx_transfer/staging/migrate_kjn/references_kjn_v4.json --images tools/hwpx_transfer/staging/migrate_kjn/images.json --transplant tools/hwpx_transfer/staging/migrate_kjn/transplant.json --no-tail --output tools/hwpx_transfer/staging/survey_261028/fresh.hwpx --report tools/hwpx_transfer/staging/survey_261028/fresh_report.md
   ```
3. **patch 드라이런.** `python tools/hwpx_transfer/patch_from_fresh.py --base "<기준본>" --fresh …/fresh.hwpx --out …/patched.hwpx --report …/patch_dry_report.md --dry-run`. 기대값: 본문 문단 교체 약 8~10(1장 2 + 4장 6~8), 문단 삭제 1, 표 교체 2(표 4-5·4-11). 그 밖의 표나 1·4장 외 장의 문단이 목록에 있으면 **멈추고 `ask`**.
4. **실제 patch** → `patched.hwpx`, `patch_report.md`. 표 4-11 열폭 재적용(A절). 통계(동일/반입/수동)를 보고에 적는다.
5. **부록 수술(B절).** `patched.hwpx`를 다시 덤프해 부록 구간을 잡고, 전수 대조표를 `report.md`에 먼저 적은 뒤 Python으로 section2 XML을 고쳐 `patched_apx.hwpx`로 저장. ZIP 구조(mimetype 첫 항목·무압축)와 XML 정합을 `zipfile`+`ElementTree`로 확인.
6. **1차 재조판.** `resave-hwpx.ps1 -HwpxIn …/patched_apx.hwpx -HwpxOut …/resaved1.hwpx -PdfOut …/resaved1.pdf`. Open/SaveAs/Reopen/PDF 모두 True. 한글 창이 떠 있으면 먼저 닫는다.
7. **표 검사.** `python tools/hwpx_transfer/pdf_table_check.py …/resaved1.pdf` → 침범 0. 부록 쪽은 **PyMuPDF로 PNG 렌더해 직접 본다**(D·E 격자 7열, A-7∼A-9 위치, 표지 정렬). 침범·깨짐이 있으면 3단계 규칙으로 처리하되 처리 전 `ask`.
8. **목차 쪽수.** `toc_pages_from_pdf.py …/patched_apx.hwpx …/resaved1.pdf …/toc_pages.json`. 미매칭(지난번 논문개요 ix·부록 도입·미도입 3건)은 PDF 꼬리말 쪽수를 직접 읽어 보완. 물리 페이지 인덱스를 인쇄 쪽수로 쓰지 않는다.
9. **목차 주입 → 2차 재조판.** `toc_numbers_patch.py …/patched_apx.hwpx …/toc_pages.json …/patched_toc.hwpx` → `resave-hwpx.ps1 -HwpxIn …/patched_toc.hwpx -HwpxOut "00. hwpx/YYMMDD_HHMM_경기공학_건축안전_윤혁_논문_설문지동기화본.hwpx" -PdfOut …/final.pdf`(YYMMDD_HHMM은 저장 시점 Asia/Seoul). 재추출 = 주입값 차이 0, 표 침범 0. 차이가 있으면 한 번 더.
10. **최종 검증(보고서에 전부 적는다, Python 직접 읽기만).**
   - 최종본 section0~2 문단 텍스트 = `patched_toc.hwpx`(section1 쪽수 run만 차이).
   - A절 표의 새 문장 전부 존재, 옛 문장("Google Forms", "설문 링크", "단일 링크", "Google 계정 로그인은 요구하지 않았고", "개별 대조", "제출시각이 10분 이내", "조사는 2026년 10월 Google", "2026년 10월에 사후 설문") **본문(부록 제외)** 0건. "자료 정제와 채점은 제3절 제1항과"가 문단 시작이 아니라 합쳐진 문단 안에 1회.
   - 부록: MD 부록1의 문항·보기·안내 문장 전부가 최종본에 글자 그대로 존재하며 출현 횟수가 기대와 같다(공통부 A-1∼A-9·B-1∼B-8·C-1∼C-4·※ 안내·조사 관리용 각 2회, D-1∼D-8·E-1∼E-4·D/E 안내 각 1회). 옛 문자열 "배포코드", "18문항 또는 30문항", "비해당", "(   )개월", "개월은 연수를 제외한", "별도의 비해당을 선택" 0건. D·E 격자 colCnt=7, 열폭 합 = 기준본 전체 폭.
   - 빨간 마커: 기준본 `textColor="#FF0000"` run 수를 접두사별로 세고(지난번 28: 확정 필요 13·CITE_TODO 9·UNVERIFIED 4·DATA PENDING 0) 최종본과 같은지 확인(재저장 후 charPr id가 바뀌므로 `header.xml` 재판독). 검정 1건("[확정 필요: 분류 미정 서지]" 참고문헌 분류 제목)은 알려진 예외. `[입력]`은 검정.
   - 표 보존: 표 4-7(패널 A·B·C)·4-10·4-11·4-12·4-13·4-14의 열폭·병합 격자가 기준본과 동일(4-11은 재적용 후 기준).
   - 김정년 고유 문구("안전시설물", "떨어짐 사고위험", 원제목, 성명) 0건. 양식 사본 SHA `9bf1980a…`, 기준본 SHA `eddab53b…` 불변.
   - PDF 총 쪽수(기준본 141), 부록 시작 쪽(도입·미도입), 5장 시작·끝 쪽, 표 침범 0.

## D. 금지 사항

- `git add/commit/push` 금지(커밋은 메인이 한다). `00. hwpx/`의 기존 파일 삭제·개명·제자리 수정 금지. 양식 원본을 `00. hwpx/`에 복원하지 않는다.
- `01.docs/*.md`·`CLAUDE.md`·`AGENTS.md`·`MEMORY.md`·`.claude/**`·`03.plan/**`·`tools/hwpx_transfer/*.py`(도구 본체)·`staging/migrate_kjn/*.json` 수정 금지. 도구에 버그가 있으면 고치지 말고 `ask`. 필요한 스펙 JSON·스크립트는 `staging/survey_261028/` 안에만 새로 만든다.
- hwpx MCP(`mcp__hwpx__*`)·rhwp MCP(`mcp__rhwp__*`) 호출 금지(읽기 포함).
- `pageBreak="CELL"`, 글자 크기·행 높이 축소, 마커·문구 삭제·축약, MD에 없는 문장 창작 금지.
- 워커를 추가로 띄우지 않는다. 한글 COM은 한 번에 하나의 파일만 연다.

## E. 보고

`tools/hwpx_transfer/staging/survey_261028/report.md`에 (1) A절 패치 통계, (2) B절 전수 대조표(항목 / 기준본 문구 / MD 문구 / 처리), (3) C절 각 단계 명령·핵심 수치, (4) 10의 검증 결과를 적는다. `worker_done`에 산출물 경로·PDF 쪽수·검증 요약(3문장)·`--outcome`·`--files-modified`·`--report-path`를 넣는다. 실패나 불확실은 숨기지 말고 `--outcome failed`로 보고한다.

## 진행 기록

- 2026-10-28 07:13 브리프 작성(Advisor). Orca `worker-start --agent codex --worktree current`로 위임.
- 2026-10-28 07:16 첫 시작(ctx_700b473f45cb)이 Codex 업데이트 안내(0.164→0.165)에 막혀 `agent_readiness` 실패 → 터미널에서 '다음 버전까지 건너뛰기' 선택 후 release, `--retry-of`로 재시작(run_d263b2778c64 / task_8a7a25b8960c / ctx_880483e9f2da).
- 2026-10-28 07:16~07:30 Codex 워커 실행 완료, outcome succeeded. 질문 2건 회신: ① 부록 Part A가 한 칸 표라 A-7∼A-9 추가 후 넘침 → 제목행+문항별 행(10행) 분할, `pageBreak="TABLE"`·`repeatHeader`·필요한 표만 `treatAsChar=0`, 행 사이 괘선 없음 승인. ② 미도입 벌 A 셀 최소높이 44685가 행마다 복제돼 깨짐 → 합계 보존 배분 대신 도입 벌과 동일(행 1600)하게 복제 지시.
  - A: 561블록·누락 0. 패치 동일 675 / 반입 9(본문 7·표 2) / 수동 0 / 표 유지 6. 문단 합침으로 1개 감소. 표 4-11 기준본 열폭 재적용.
  - B: 대조표 62항목 반영(조사 관리용 현장 구분·현장명·성명, Part A 제목·안내, A-4, A-7∼A-9+※ 2줄, Part B 안내, D·E 비해당 열 삭제 colCnt 7·폭 3500 문항 열 배분, 표지 문장, D·E 도입 문장). Google Forms 언급은 배포본 재현으로 유지.
  - 검증: 재조판 5회(Open/SaveAs/Reopen/PDF True), 표 침범 0(59쪽), 목차 124항목 차이 0, XML 검증 65항목 PASS, 빨간 run 28/28, 표 4-7·4-10∼4-14 열폭·병합 보존, CELL 0, 김정년 문구 0, 기준본 eddab53b…·양식 9bf1980a… 불변. 부록 16쪽 PNG 육안 확인(Advisor도 appendix_1∼4.png 확인).
  - **산출물:** `00. hwpx/261028_0727_경기공학_건축안전_윤혁_논문_설문지동기화본.hwpx`(SHA256 a2fadf06…). PDF 143쪽(+2). 부록 도입 115·미도입 124쪽, Part A 117~118·126~127, 5장 103~106, 참고문헌 107부터. 보고서 `tools/hwpx_transfer/staging/survey_261028/report.md`. 커밋 대기.
- 2026-10-28 07:43 사용자가 산출물을 한글에서 직접 고쳐 `00. hwpx/261028_0727_경기공학_건축안전_윤혁_논문.hwpx`(SHA256 59b9c425…)로 저장·개명하고 **기준본으로 지정**(CLAUDE.md 기준본 항목 갱신). `…_설문지동기화본.hwpx`는 더 이상 없다. 조판 전 동일 내용본 `staging/survey_261028/patched_toc.hwpx`와 문단 텍스트 대조 결과 차이 9블록: 참고문헌 [01] URL 앞 공백 1건, 부록 두 벌 A-7 보기 ③·A-8 보기 ④·A-9 보기 ④ 삭제, 도입 벌 A-9 보기 뒤 '1' 문단 1개. 보기 삭제·'1'은 실수로 보여 사용자 확인 요청(MD 부록1·<표 4-7> 패널 B·원자료에는 해당 보기가 있다).
- 2026-10-28 07:57 **정정:** 위 '세 보기 삭제'는 오진이었다. XML에는 보기 전문이 `<hp:lineBreak/>`로 줄만 나뉘어 그대로 있었고, 메인의 텍스트 추출이 lineBreak 뒤 tail을 놓쳤다. 실제 결함은 도입 벌 A-9 보기 뒤 `<hp:t>1</hp:t>` 문단(paraPr 82·charPr 48, id="0") 하나뿐. 메인이 직접 Python zipfile로 그 문단만 삭제(앞뒤 문단 linesegarray 제거), 한글 재조판 → PDF 142쪽(사용자본은 3장 끝에서 1쪽이 줄어 4장 이후 목차가 전부 1쪽씩 어긋나 있었음) → `toc_numbers_patch` 53항목 수정(부록 114·123, 논문개요 ix 수동) → 재조판 → 재추출 차이 0, 표 침범 0, 빨간 run 25/25, 기준본 SHA 59b9c425… 불변. **산출물:** `00. hwpx/261028_0757_경기공학_건축안전_윤혁_논문_부록1문단정리본.hwpx`(SHA256 72fa90d5…). 사용자 줄바꿈·여백 편집은 그대로 보존.
