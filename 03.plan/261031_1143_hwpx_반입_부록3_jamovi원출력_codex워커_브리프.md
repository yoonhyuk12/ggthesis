# hwpx 반입: 미반입 MD 변경 전체 + 부록 3 jamovi 원출력 격자 표 — codex 워커 브리프

- 작성: 2026-10-31 11:43 (Asia/Seoul)
- 오케스트레이터: Claude(메인). 워커: Orca codex `gpt-6-astra`, effort high (사용자 지정)
- 사용자 결정: jamovi 원출력은 본문이 아니라 **부록 3 `<부표 3-1>`∼`<부표 3-9>`**에 모은다. 표 안 칸에 하위 표 그림만 작게 넣는다. jamovi 표는 통째로 고르기만 하고 표 안의 행은 지우지 않는다.

## 1. 목표

기준본 `00. hwpx/261028_0757_경기공학_건축안전_윤혁_논문.hwpx`(SHA256 앞 16자리 `72FA90D52FDBE2E0`, **현재 접두사 최신본**)의 **복사본**에 다음을 반영한 패치본 hwpx를 만든다.

1. 2026-10-28 이후 `01.docs/` MD 변경 전체 (`git diff HEAD -- 01.docs`가 9개 파일 약 400줄: 제목 확정, `현장소장(관리감독자)` 통일, 제4장 제7절 재구성·간소화, 논의 4장 제8절 이동, 결론 재구성, `부록2_실증분석_상세결과.md` 신설, 오늘의 `<표 4-n>` 주 끝 "jamovi 원출력은 부록 3 …" 문장 등).
2. 새 **부록 3 `부록3_jamovi_원출력.md`**: 부표 9개. 각 부표는 jamovi 하위 표 PNG를 칸에 넣은 격자 표다.
3. 목차·표 목차의 부록 2·부록 3 항목(`00_목차.md` 기준).

## 2. 입력

| 항목 | 경로 |
|---|---|
| MD 단일 원본 | `01.docs/00_목차.md`, `01_서론.md`∼`05_논의및결론.md`, `07_참조번호목록.md`, `부록1_설문지_양식.md`, `부록2_실증분석_상세결과.md`(신규), `부록3_jamovi_원출력.md`(신규) |
| 부표 그림 | `01.docs/설문결과/자모비캡쳐/부표/부표3-n_kk.png` (3배 해상도) |
| 그림 배치 명세 | `01.docs/설문결과/자모비캡쳐/부표/manifest.json` — 칸별 `width_mm`·`height_mm`(인쇄 크기, CSS px당 0.25mm = jamovi 글자 약 8.5pt). `fits_width:false`인 `<부표 3-5>`(143.2mm)만 140mm로 비례 축소 |
| 격자 배치 | `부록3_jamovi_원출력.md`의 Markdown 표가 행·열 배치다. 각 칸은 `(가) 라벨<br>![라벨](경로)` — 라벨 문단 + 그림 문단 |
| 조립 파이프라인 | CLAUDE.md "MD → hwpx 조립 파이프라인" 절. `md_to_blocks.py` → `blocks_to_hwpx.py`(양식은 `git show ba33381:"00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx"`로 스크래치에 꺼냄) → `patch_from_fresh.py --base <기준본 복사> --fresh <조립본>` |

## 3. 할 일

1. `tools/hwpx_transfer/md_to_blocks.py`의 파일 목록(23∼24행 부근)에 `부록2_실증분석_상세결과.md`(apx2r 등 기존 apx2와 겹치지 않는 이름)와 `부록3_jamovi_원출력.md`(apx3)를 추가한다. 기존 `부록2_설문항목_근거매핑.md`(apx2)는 본문 미수록이므로 조립에서 계속 뺀다.
2. 부록 3의 **그림 칸 격자 표**를 조립할 수 있게 `md_to_blocks.py`·`blocks_to_hwpx.py`/`kjn_profile.py`를 확장한다. 칸 안 그림은 `hp:pic`(글자처럼 취급) + `BinData` 등록 + `Contents/content.hpf` manifest 항목이 필요하다. 그림 크기는 manifest의 `width_mm`(HWPUNIT = mm × 283.465)를 쓰고 비율 유지. 열폭은 행별 그림 폭 + 칸 좌우 여백으로 설계하고 전체 폭은 본문 표 폭(약 140mm, 기존 표의 `hp:sz@width` 관례)을 넘지 않는다. 표 테두리는 없음 또는 얇은 선, 라벨은 표 글꼴 9pt 안팎 왼쪽 정렬.
3. 단위 테스트를 추가한다(그림 칸 표 1개 조립 → BinData·manifest·`hp:pic` 크기 검증). 기존 `tools/hwpx_transfer/tests/test_blocks_to_hwpx_kjn.py` 21건이 계속 통과해야 한다.
4. 1·2단계 조립 → `patch_from_fresh.py`로 기준본 복사에 반입. 부록 3은 기준본에 없으므로 새로 들어가야 한다. 필요하면 `--toc-from-fresh`.
5. 산출물은 **스크래치 `tools/hwpx_transfer/staging/hwpx_261031/`** 아래에만 쓴다: `patched.hwpx`, `patch_report.md`, `assembled.hwpx`, 조립 `report.md`.

## 4. 금지 (Scope of action)

- `git add`/`commit`/`push` 등 git 쓰기 금지.
- `00. hwpx/`의 어떤 파일도 쓰거나 덮어쓰지 않는다. 기준본은 복사해서만 쓴다(작업 전후 SHA256 동일 확인).
- **한글 COM(`resave-hwpx.ps1`, HWPFrame) 실행 금지** — 재조판 저장·PDF 출력·목차 쪽수 갱신은 메인이 한다.
- hwpx MCP 도구(`mcp__hwpx__*`)는 읽기 포함 전부 금지(2.5MB 본문에서 40분 멈춤). rhwp MCP 쓰기 도구 금지. 본문은 Python `zipfile`+ElementTree로 읽는다.
- `01.docs/**`, `MEMORY.md`, `CLAUDE.md`, `.claude/**`, `03.plan/**` 수정 금지. MD에 문제가 있으면 고치지 말고 보고한다.
- `pageBreak="CELL"` 금지. 빨간 마커 규칙(`[DATA PENDING` 등, `실험전`)은 `blocks_to_hwpx.py`의 기존 처리 유지. 대괄호 참조번호·신뢰구간은 검정.
- 내용·배치가 바뀐 문단과 새 표 셀 문단의 `<hp:linesegarray>`는 제거하고, 무관한 문단 캐시는 건드리지 않는다.

## 5. 완료 기준과 보고 증거

- 단위 테스트 전체 통과 출력.
- `patched.hwpx`: ZIP 무결성, 모든 XML 파싱 성공, BinData 그림 수 = 부록 3 칸 수(47)와 기존 그림 수의 합, manifest 등록 일치.
- 기준본 대비 텍스트 대조 요약: MD 변경이 반영된 문단 수, `patch_report.md`의 "수동 재적용 필요" 목록 전문.
- 부록 3 격자 표 9개의 행·열·칸 폭 합계(전체 폭 정합)와 칸별 그림 크기(mm).
- 기준본 SHA256 작업 전후 동일.
- 알려진 미해결점과 메인이 한글에서 확인해야 할 지점.

## 6. 이후 메인 단계 (워커 범위 밖)

한글 COM 개방·재조판 `SaveAs` → `00. hwpx/YYMMDD_HHMM_경기공학_건축안전_윤혁_논문.hwpx` → `pdf_table_check.py` 전 표 검사 + 부록 3 쪽 육안 확인 → `toc_pages_from_pdf.py`·`toc_numbers_patch.py`로 목차 쪽수 → 재저장·재대조.

## 진행 기록

- 2026-10-31 11:43 브리프 작성, 워커 디스패치.
- 2026-10-31 12:00 워커 완료(outcome succeeded). 증거 `tools/hwpx_transfer/staging/hwpx_261031/worker_report.md`: 테스트 46건 통과, ZIP/XML·그림 53개 등록·부표 9개 폭 정합 PASS, 기준본 SHA256 불변, 기준본 텍스트가 93aa8fb MD와 전부 일치(사용자 고유 텍스트 0건). 서식 재확인 23건(표 22개 fresh 반입 + section1).
- 2026-10-31 12:03 메인: 부록 3 머리말에 <부표 3-5> 축소 예외 문장 추가(MD) → 워커 재현 명령으로 패치본 재생성·verify PASS.
- 2026-10-31 12:04 한글 COM 재조판 저장 `00. hwpx/261031_1204_…` (중간본, 목차 쪽수 0) → PDF 164쪽, 표 꼬리말 침범 0.
- 2026-10-31 12:06 목차 쪽수 151개 반영(도구 미매칭 9개는 PDF 꼬리말 번호로 지정) → 한글 재저장 `00. hwpx/261031_1206_경기공학_건축안전_윤혁_논문.hwpx`(SHA256 D9FFCC9F…) = **최종본**. 재출력 PDF와 목차 151개 전부 일치, 쪽수 164 불변, 표 꼬리말 침범 0, 빨간 마커 run 25개 전부 빨강, 기준본 SHA256 불변.
- 남은 일: 사용자 한글 서식 재확인(표 22개·목차 쪽 장평/자간), jamovi 출력의 `[3]`·`[4]` 참조 각주 처리 결정, 커밋.
