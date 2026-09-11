# T2 브리프 — `verify-hwpx.ps1`이 규칙대로 검증하게 고친다

담당: claude (opus). 상위 계획: `03.plan/260912_0714_hwpx도구개선_오케스트레이션.md`.

## 배경 (재탐색 금지)

대상: `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1` (69줄).
규칙: `.claude/rules/hwpx-output-verification.md` 1번 항목 — **`RegisterModule('FilePathCheckDLL','FilePathCheckerModule')` 후 `Open(path,'HWPX','forceopen:true')`가 `True`여야 완료다.** 2026-09-11에 ZIP·XML 검증을 전부 통과한 파일이 `Open=False`였다(원인: 문단 텍스트를 줄인 뒤 `<hp:linesegarray>`의 `textpos`가 본문 길이를 넘김).

감사에서 확인된 결함 3개:
1. `:63` `$h.Open($HwpxPath,"HWPX","") | Out-Null` — **반환값을 버려서** 규칙의 True/False 판정을 못 한다. 그리고 COM 경로는 `-PdfPath`를 줄 때만 돈다. 기본 경로(`:38-56`)는 `Get-Process Hwp` 생존만 본다.
2. `:22-25` `Kill-Hwp`가 `Get-Process Hwp | Stop-Process -Force`로 **사용자의 다른 한글 문서까지 전부 죽인다.** 3회 호출(`:29,:35,:56`).
3. 타임아웃 없음.

살릴 것: `:28-35`의 워밍업 후 폴링(콜드스타트 오탐 방지 — MEMORY.md `[LEARN:hwpx]` "고정 12초 대기는 정상 파일을 CRASHED로 오탐"). 참고 구현: `C:/Users/User/.claude/skills/hwpx/scripts/finalize_hwpx.py:234-266` `hancom_open_check` — `Open()` 반환값을 판정하는 유일한 기존 코드지만 `except: pass` 3개에 타임아웃이 없다.

## 요구사항

- **COM 개방 판정이 기본 경로**다. `New-Object -ComObject HWPFrame.HwpObject` → `RegisterModule("FilePathCheckDLL","FilePathCheckerModule")` → `$ok = $h.Open($path,"HWPX","forceopen:true")` → `Open=True|False`를 stdout에 찍고 exit 0/2. `finally`에서 `$h.Quit()` 및 COM 해제. `RegisterModule`이 False를 돌려주면 그 사실을 stdout에 찍고 계속 진행(보안 대화상자 여부를 보고에 적는다).
- **다른 한글 프로세스를 절대 죽이지 않는다.** `Kill-Hwp` 제거. 정리가 필요하면 스크립트 시작 전 `Get-Process Hwp`의 PID 집합을 찍어 두고, 그 뒤 새로 생긴 PID만 정리한다.
- **타임아웃**: COM 구간을 `Start-Job`(또는 동등한 방식)으로 감싸 `-TimeoutSec`(기본 120) 초과 시 `Open=TIMEOUT` exit 3, 그 잡이 띄운 새 Hwp PID만 정리.
- `-PdfPath`는 유지: `Open=True`일 때만 COM으로 PDF 저장.
- pwsh 7에서 동작해야 한다. 5.1에서도 되면 좋지만 필수 아님 — 시험한 버전을 적어라.
- 스크립트는 입력 hwpx에 **아무것도 쓰지 않는다** (Open만, SaveAs 금지).

## 시험 (증거를 그대로 붙여라)

a. 정상본: `00. hwpx/260911_1101_경기공학_건축안전_윤혁_논문작성_작성본.hwpx` → 기대 `Open=True`, exit 0. 실행 전후 파일 SHA256 동일함을 출력.
b. 파손본: 위 파일을 스크래치(`C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Documents-2026------03--------/43c3c7a0-6f3d-4da6-9f68-f7cf1155797a/scratchpad/t2/`)에 복사한 뒤 Python `zipfile`로 `Contents/section2.xml`에서 `<hp:linesegarray>`가 있는 본문 문단 하나를 골라 **텍스트만 30자 이상 줄이고 linesegarray는 그대로 둔다**(2026-09-11 사고 재현). ZIP 엔트리 순서·압축 방식 유지. 기대 `Open=False`, exit 2. 만약 한글이 `forceopen`으로 열어 버리면 그 사실을 보고하고, 대신 `section2.xml` 끝을 잘라낸 파손본으로 exit 2를 확인한다.
c. 타 프로세스 생존: 시험 전에 `Start-Process Hwp.exe`로 빈 한글을 하나 띄워 PID를 적고, a·b를 돌린 뒤 그 PID가 살아 있음을 `Get-Process -Id`로 보인다. 끝나면 그 PID만 종료.
d. 타임아웃 경로는 `-TimeoutSec 1`로 인위 재현이 가능하면 하고, 아니면 코드 경로만 설명한다.

## 편집 허용 범위 (명시적 예외)

`.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1` **한 파일만** 편집한다. `.claude/**`의 다른 파일(SKILL.md 포함)은 읽기만 한다. 스크래치 디렉토리는 자유.

## Scope of action — DO NOT do these things

- Do NOT run `git add`, `git commit`, `git push`, or any git write command.
- Do NOT call any `mcp__hwpx__*` tool, read or write. hwpx는 Python `zipfile`로만 읽는다.
- Do NOT write to `00. hwpx/**`. 파손본은 스크래치에만 만든다.
- Do NOT `Stop-Process` any Hwp process you did not start.
- Do NOT edit `MEMORY.md`, `CLAUDE.md`, `.claude/rules/**`, `.claude/skills/hwpx-thesis-editing/SKILL.md`, `03.plan/**`, `01.docs/**`, `tools/**`.
- If a step fails, stop, report the exact error output, and do not improvise a fix outside the allowed scope.
