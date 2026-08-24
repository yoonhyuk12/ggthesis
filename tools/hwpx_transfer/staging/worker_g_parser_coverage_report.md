# 워커 G 파서 커버리지 수정 보고

## 결론

누락 7행의 원인은 `editorial_section` 스킵이나 파싱 유실이 아니라 커버리지 검증용 `norm()`의 비대칭 정규화였다. 7행은 수정 전부터 `parse_file()`의 일반 문단 분기 273~275행을 통과하여 `p` 블록의 단일 bold run으로 정상 저장됐지만, 원문 `**1. ...**`에서는 번호 마커가 남고 배정 텍스트 `1. ...`에서는 번호 마커가 제거되어 거짓 누락으로 판정됐다. 따라서 블록 타입이나 조립기를 바꾸지 않고 `norm()`에서 헤딩·인라인 마커를 먼저 제거한 뒤 리스트 마커를 제거하도록 순서만 고쳤다.

## 근본 원인 조사 증거

UTF-8 점검 스크립트 `tools/hwpx_transfer/staging/check_bold_subheading_coverage.py`를 만들고 `sys.settrace`로 `parse_file()`의 실제 분기를 기록했다. 수정 전 실행은 종료 코드 1로 실패했고, 55·65·136·147·162·173·188행 모두 파서 273·274·275행을 통과했다. 즉 `editorial_section` 분기는 이 7행에 관여하지 않았다.

수정 전 55행의 비교값은 다음과 같았다.

```text
원문 정규화 = 1.연구문제1.시스템도입에따른안전관리실효성차이.
배정 정규화 = 연구문제1.시스템도입에따른안전관리실효성차이.
배정 종류 = text
블록 = index 15, type p, runs [{text: "1. 연구문제 1. 시스템 도입에 따른 안전관리 실효성 차이.", bold: true}]
excluded 적중 = 없음
```

나머지 6행도 같은 패턴이었다. `norm()`이 리스트 마커를 인라인 마커보다 먼저 제거하므로 `**1. ...**`의 선두가 별표일 때 `NUMBERED_RE`와 동일한 리스트 마커 정규식이 작동하지 않았고, `parse_inline()`이 별표를 제거한 배정 텍스트에서는 작동했다.

## 수정 내용

`tools/hwpx_transfer/md_to_blocks.py`의 `norm()`에서 처리 순서를 다음과 같이 바꿨다.

```text
수정 전 = 헤딩 마커 제거 → 리스트 마커 제거 → 인라인·기타 마커 제거 → 공백 제거
수정 후 = 헤딩 마커 제거 → 인라인·기타 마커 제거 → 리스트 마커 제거 → 공백 제거
```

이 변경으로 원문과 배정 텍스트에 같은 리스트 마커 제거 규칙이 적용된다. 7행의 블록은 조립기가 이미 `BODY_BOLD_CHAR`로 처리하는 `p`와 bold run을 그대로 사용하므로 `blocks_to_hwpx.py`는 수정하지 않았다.

## TDD와 최종 검증

점검 스크립트의 최초 실행은 `missing_lines=[55,65,136,147,162,173,188]` 때문에 종료 코드 1로 실패했다. `norm()` 수정 후 같은 스크립트는 종료 코드 0으로 통과했고, 최종 실행은 내부에서 요구된 파서 명령을 UTF-8로 다시 실행한 뒤 블록·리포트·회귀 조건을 함께 검사했다.

최종 파서 실제 출력은 다음과 같다.

```text
01_서론.md -> ch01.blocks.json: blocks=41 excluded=56 missing=0
02_이론적배경.md -> ch02.blocks.json: blocks=96 excluded=113 missing=0
03_시스템개발.md -> ch03.blocks.json: blocks=85 excluded=86 missing=0
04_연구설계.md -> ch04.blocks.json: blocks=93 excluded=83 missing=0
05_실증분석결과.md -> ch05.blocks.json: blocks=83 excluded=96 missing=0
06_결론.md -> ch06.blocks.json: blocks=40 excluded=59 missing=0
부록1_설문지_양식.md -> apx1.blocks.json: blocks=63 excluded=86 missing=0
부록2_설문항목_근거매핑.md -> apx2.blocks.json: blocks=25 excluded=33 missing=0
report: C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\staging\parse_report.md
total blocks=526, coverage missing=0
```

UTF-8 점검 스크립트의 최종 요약은 다음과 같다.

```text
parser_returncode=0
missing_lines=
parse_report_has_missing_zero=True
block_counts=ch01=41, ch02=96, ch03=85, ch04=93, ch05=83, ch06=40, apx1=63, apx2=25
total_blocks=526
count_regressions=0
pass=True
line 55: type=p, bold=True, text=1. 연구문제 1. 시스템 도입에 따른 안전관리 실효성 차이.
line 65: type=p, bold=True, text=2. 탐색적 연구문제 2. 안전관리 예산 제약성과 도입 효과의 상호작용.
line 136: type=p, bold=True, text=1. 공통부 A. 인구통계학적 특성 6문항.
line 147: type=p, bold=True, text=2. 공통부 B. 안전관리 실효성 일반형 8문항.
line 162: type=p, bold=True, text=3. 공통부 C. 안전관리 예산 제약성 4문항.
line 173: type=p, bold=True, text=4. 도입 현장 전용부 D. 시스템 특성 인식 8문항. [확정 필요: D블록 유지 여부]
line 188: type=p, bold=True, text=5. 도입 현장 전용부 E. 경보 피로도 완화 인식 4문항(참고용 기술 척도).
```

`parse_report.md`에는 `누락 0 — 8개 파일 전체에서 커버리지 목표를 충족했다.`가 기록됐다. 8개 파일의 블록 수는 수정 전 기준과 모두 같고 총 526개이므로 감소 회귀가 없다.

## 변경 범위

생산 코드 변경은 `tools/hwpx_transfer/md_to_blocks.py` 한 파일뿐이다. `blocks_to_hwpx.py`, `논문구조/`, `MEMORY.md`, `CLAUDE.md`, `docs/`, `plan/`은 수정하지 않았고 git 및 hwpx 쓰기 도구도 사용하지 않았다. `staging/` 아래의 JSON과 `parse_report.md`는 파서 실행으로 정상 갱신됐으며, 진단 스크립트와 상세 JSON 증거를 같은 디렉터리에 남겼다.
