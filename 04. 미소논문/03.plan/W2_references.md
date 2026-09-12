# W2 — 참고문헌 references.json 생성

공통 규칙: `_COMMON_워커공통규칙.md` 를 먼저 읽는다.

## 목표
`01.docs/08.참고문헌.md`를 조립기 입력 `tools/hwpx_transfer/staging/references.json`으로 변환한다. 스키마는 `staging/references_yoonhyuk_reference.json`과 **동일**(`meta`, `categories`, `flagged`, `sort_rule`; categories 안의 항목 필드 이름도 같게). 먼저 기준 파일을 열어 스키마를 정확히 파악하고, 상위 저장소 `../tools/hwpx_transfer/blocks_to_hwpx.py`의 `add_references()`가 어느 필드를 읽는지 확인해 그 필드는 반드시 채운다.

## 규칙
1. 분류는 학교 양식 5종 고정: `가. 학위논문` / `나. 학술지` / `다. 보고서` / `라. 관련법` / `마. 기타`. 원고의 가·나·다·라 절은 **확보 시점별** 묶음이므로 무시하고, 각 항목의 하위 소제목((1) 학위논문, (2) 학술지·학회지, (3) 보고서, (4) 관련법, (5) 기타/Preprint·웹자료, 국외 단행본·단행본 장, 정부·공공기관 간행물 등)으로 5종에 재배치한다. 단행본·단행본 장·Preprint·웹자료는 `마. 기타`, 정부·공공기관 간행물은 `다. 보고서`, 고시는 `라. 관련법`.
2. `## 마. 추가 확보 필요 문헌 (CiteTodo — 잔여)` 절 전체는 **제외**하고 `flagged`에 `cite_todo` 사유로 목록만 남긴다. `(5) 부분 검증(서지 필드 보완 필요)`과 `(6) 설계 전환으로 불요` 항목도 같은 방식으로 flagged.
3. 앞 번호 `[01]` 같은 태그는 제거하고 `id` 필드에 보존. 원고 서지 문자열은 **그대로**(저자·연도·제목·게재지·권호·쪽·DOI 손대지 않음). 마크다운 `*기울임*` 마커만 제거하고, 제거했음을 `flagged`에 `md_marker_removed`로 기록.
4. 정렬: 각 분류 안에서 국내(한글 저자) 먼저 가나다순, 국외 저자 성 알파벳순. 원고 상단 주석의 정리 규칙을 따른다. `sort_rule`에 규칙 문자열 기록.
5. 중복(같은 서지가 두 절에 있음) 은 하나만 남기고 `flagged`에 `duplicate` 기록.
6. 판단이 애매한 분류(예: 학술대회 논문집, 연구보고서 성격의 학위논문)는 넣되 `flagged`에 `category_uncertain` 으로 남긴다. 서지를 만들어 채우지 않는다.

## 완료 기준
- `PYTHONIOENCODING=utf-8 python -c "import json;json.load(open('…/references.json',encoding='utf-8'))"` 통과
- `references_report.md`: 분류별 건수, 제외(CiteTodo) 건수, flagged 목록, 원고 총 항목 수 = 채택 + 제외 + 중복 임을 보이는 산식
- 기준 파일과 최상위 키·항목 필드가 동일함을 보이는 `python` 비교 출력

## 산출물
- `tools/hwpx_transfer/staging/references.json`, `tools/hwpx_transfer/staging/references_report.md`
- 변환 스크립트를 썼다면 `tools/hwpx_transfer/refs_md_to_json.py`(표준 라이브러리, 재실행 가능)
