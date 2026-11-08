# 메인 실행 인계

워커는 JSON 덤프만 읽고 이번 staging 코드/JSON을 준비했다. HWPX·COM 실행은 하지 않았다.

저장소 루트 PowerShell에서 순서대로 실행:

```powershell
$env:PYTHONIOENCODING='utf-8'
python tools/hwpx_transfer/staging/delivery_261107_2315/prepare_inputs.py
python tools/hwpx_transfer/staging/delivery_261107_2315/assemble.py
python tools/hwpx_transfer/staging/delivery_261107_2315/resolve_patch.py
python tools/hwpx_transfer/staging/delivery_261107_2315/verify_current.py tools/hwpx_transfer/staging/delivery_261107_2315/ready.hwpx
```

- `assemble.py`: 다른 워커의 `references.json` 필수. 보존한 양식 스크래치를 SHA256 확인 후 복사하여 비교용 `fresh.hwpx`만 만든다.
- `resolve_patch.py`: baseline SHA256 확인 후 `patch_from_fresh.Patcher`의 스타일/개체 이식 기능을 이용해 변경분을 반입하고 `ready.hwpx`를 만든다. 별도 CLI `patch_from_fresh.py` 선행 실행은 필요 없다. 기존 CLI의 삭제 보존 정렬을 그대로 쓰면 폐기 문구가 남으므로 승인된 현행 MD 문단 순서로 정렬하며 같은 문단은 base XML을 보존한다.
- force-fresh에 해당하는 표: `<표1-1>,<표3-6>,<표3-7>`; 새 표는 base 전체 폭을 보존하고 새 격자에 맞춰 열폭을 환산한다.
- 텍스트만 바뀐 표 `<표1-2>,<표3-1>,<표3-9>,<표4-13>`은 기존 셀·서식을 보존하고 8개 셀 문구만 고친다. 4-13 머리행의 단위는 새 문단으로 나누되 기존 머리행 글자/문단 서식을 복제한다.
- 감사의 글/국문초록/영문초록은 현행 MD와 일치한다. section1은 표1-1 목차 제목만 바꾼다. 부록은 전체 base XML을 보존한다. 현재 MD 설문 문구 누락 0이며 B문항 각각 2회, C/D문항 각각 1회를 덤프로 확인했다.
- 본문 차이: 1장 3묶음, 2장 1묶음(제1장 제1절 교차참조 삭제), 3장 7묶음(R5·KISA 목표/시간 측정·소결), 4장 5묶음(기존 통계 설명 및 두 연결문단/논의·표 주), 5장 0. 전문 before/after는 `change_audit.json`.
- 파서 호환 처리: 병합 없는 4-11/12/13의 layout 주석은 이번 실행에서만 무병합으로 처리. 공용 코드는 수정하지 않았다. 표3-7의 MD 리터럴 대괄호 이스케이프는 JSON에서만 해제한다.
- 그림 8개는 메인 패치 실행 시 픽셀 비교하여 달라진 이미지 데이터만 반입한다. 워커는 HWPX 이미지 바이너리를 열지 않았다.

검증 증거: `preparation_checks.json`(코드 문법·텍스트 변경 4표의 격자/치수 보존·설문 20문항 출현 횟수), `parse_report.md`(476블록, 누락 0). 준비 코드가 HWPX에서 실행된 결과를 검증한 것은 아니다.

메인 잔여: ready 검증 → 한글 COM 재조판 저장/재개방 → 전 표 PDF 검사/육안 확인 → 실제 인쇄 쪽수 목차 갱신 → 재저장·최종 대조 → 최신 시간 산출물과 snapshot. 이전 finalize_checks.py의 고정 페이지 허용목록은 이번 작업에 재사용하지 않는다. `verify_current.py`는 HWPX 내용/격자/마커/이미지 검사이며 COM/PDF 완료를 대신하지 않는다.
