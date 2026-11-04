# Markdown 표의 자동 병합

표 캡션과 Markdown 표 사이의 한 줄 HTML 주석 `hwpx-table-layout`을 이관기가 읽는다. 주석은 본문에 출력하지 않는다.

```markdown
<표 4-4> 설문지의 최종 구성

<!-- hwpx-table-layout: {"caption":"<표 4-4>","merges":[[4,0,1,3],[5,0,2,1],[7,0,1,3]]} -->

| 구분 | 변수명 | 내용 | 응답 대상 | 문항수 | 문항번호 |
```

`merges` 항목은 `[행, 열, 행수, 열수]`이다. 행·열은 0부터 시작하고 머리행이 0행이다. 위 선언은 두 소계 행의 1~3열과 시스템특성의 두 행 첫 열을 합친다. 합계 행은 합치지 않는다. 병합으로 가려질 Markdown 셀은 비어 있어야 한다.

`aliases`에는 `[행, 열, 허용 이전 명칭]`을 적을 수 있다. 부분 반영기는 그 위치의 글자가 이전 명칭 또는 현행 Markdown 명칭인 경우에만 변경한다. 현재 표 4-4에는 공통부 A/B/C, 소계, 전용부 D/E, 현행안 합계의 이전 명칭을 기록했다. 다른 글자가 있으면 사용자 수정분을 덮지 않고 오류로 중단한다.

## 자동 적용 경로

기존 명령을 그대로 사용한다. 추가 옵션은 없다.

1. `md_to_blocks.py`가 주석을 읽고 표 블록의 `layout`에 저장한다.
2. `blocks_to_hwpx.py`가 조립 시 해당 셀을 병합한다. 김정년 프로파일 및 옛 프로파일의 캡션 행 오프셋을 지원한다.
3. `patch_from_fresh.py`가 저장소 `01.docs/`의 현행 선언과 fresh 표가 일치하는지 확인한다. 기준본에서는 지정 명칭과 병합만 바꾸고 기존 열폭·글꼴·서식·다른 셀 내용을 보존한다. 그 밖의 내용 차이는 보고서의 수동 검토 목록에 남긴다. 이미 반영된 병합은 다시 바꾸지 않는다.

`--protect` 또는 `--allow-tables`로 대상 표를 명시적으로 보호하면 자동 반영을 생략하고 보고서에 남긴다. 오래된 fresh, 격자 불일치, 가려질 셀의 글자·개체, 예상하지 못한 이전 명칭은 오류로 중단한다. 좌표를 유지한 채 표 행을 삽입·삭제했다면 선언도 함께 갱신해야 한다.

`fill_hwpx.py replace` 같은 단순 텍스트 치환 도구는 이 선언을 읽지 않는다. **자동 병합은 위 표준 조립 → `patch_from_fresh.py` 경로를 사용한다.** 기존 HWPX를 직접 덮어쓰지 않고 최신본의 복사본으로 반영한다.

이 기능의 테스트는 메모리 XML·임시 추출 XML로 수행한다. 실제 논문 HWPX 산출 시 한글 COM 재조판 저장, 전 표 PDF 확인, 목차 쪽수 갱신 절차는 계속 필요하다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest tools/hwpx_transfer/tests/test_table_merges.py tools/hwpx_transfer/tests/test_patch_from_fresh.py tools/hwpx_transfer/tests/test_blocks_to_hwpx_kjn.py
```
