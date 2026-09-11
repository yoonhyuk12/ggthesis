# T3 브리프 — `fill_hwpx.py replace`를 논문 타깃 치환 표준 경로로 검증한다

담당: claude (opus). 상위 계획: `03.plan/260912_0714_hwpx도구개선_오케스트레이션.md`. **저장소 파일은 하나도 편집하지 않는다 — 스크래치에서만 작업하고 보고서를 돌려준다.**

## 배경 (재탐색 금지)

- CLAUDE.md는 "기존 hwpx의 부분(타깃) 치환"을 일상 작업으로 규정하지만, 감사 결과 **저장소에 그 코드가 0줄**이다. 2026-09-11의 치환 102건은 세션 스크래치로 처리돼 남지 않았다.
- 전역 스킬 `C:/Users/User/.claude/skills/hwpx/scripts/fill_hwpx.py`(5,173줄)에 `replace --map` 서브커맨드가 있다. 정규식 토크나이저로 `<hp:t>` 오프셋만 추적해 문자열을 splice하고, **변경된 ZIP 엔트리만 재작성**한다(바이트 보존). `_strip_para_linesegs`(약 `:3212-3215`)가 **바뀐 문단만** `<hp:linesegarray>`를 제거한다 — 2026-09-11 사고(텍스트를 줄인 뒤 lineseg `textpos`가 넘쳐 한글이 못 엶)의 정확한 해법이다. `check --strict`도 있다.
- 빨간 마커 규칙: `[DATA PENDING`·`[확정 필요`·`[CITE_TODO`·`[그림 삽입 예정`·`[UNVERIFIED` 접두 대괄호는 `textColor="#FF0000"`인 charPr(운영본에서 id 70·71·72·73)로 run이 분리돼 있다. 치환이 이 run 경계를 깨면 안 된다.
- 대상 문서: `00. hwpx/260911_1101_경기공학_건축안전_윤혁_논문작성_작성본.hwpx` (본문 `Contents/section2.xml` 약 2.5MB). **원본은 읽기만 한다.**

## 작업

스크래치: `C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Documents-2026------03--------/43c3c7a0-6f3d-4da6-9f68-f7cf1155797a/scratchpad/t3/`

1. `fill_hwpx.py`의 `replace` 서브커맨드 도움말과 `--map` 입력 형식, `check --strict`, `_strip_para_linesegs` 호출 조건을 코드에서 확인한다(추정 금지, 줄번호 인용).
2. 원본을 `base.hwpx`로 복사. Python `zipfile`+정규식으로 `section2.xml`에서 치환 대상 3개를 고른다: (i) `<hp:linesegarray>`가 있는 일반 본문 문단, (ii) 표 셀 안 문단, (iii) 빨간 charPr run이 들어 있는 문단(header.xml에서 `textColor="#FF0000"`인 charPr id를 먼저 찾는다). 각각에서 **문서 내 유일한** 구절을 골라 길이가 달라지는 치환을 설계한다(예: 구절 뒤에 ` (치환 시험)` 덧붙임).
3. `replace --map`으로 `out.hwpx` 생성. 이어서 `check --strict` 실행.
4. 검증(전부 Python `zipfile`+`hashlib`):
   - 엔트리 목록·순서·압축 방식이 base와 동일한가
   - `Contents/section2.xml` 외 **모든 엔트리 SHA256이 동일**한가
   - section2에서 `<hp:p ` 단위로 나눠 base와 out을 대조 — **달라진 문단이 정확히 3개**인가
   - 달라진 3개 문단의 `<hp:linesegarray>`가 제거됐거나 `textpos`가 새 길이 이내인가
   - 빨간 charPr id의 run 개수가 base와 out에서 같은가(대상 (iii) 포함)
   - `python C:/Users/User/.claude/skills/hwpx/scripts/validate.py out.hwpx` 및 저장소의 `python tools/hwpx_transfer/extract_text.py --check-integrity out.hwpx`(옵션명은 스크립트에서 확인) 결과
5. 한컴 COM 개방 시험: `python -c`로 `win32com.client.Dispatch("HWPFrame.HwpObject")` → `RegisterModule("FilePathCheckDLL","FilePathCheckerModule")` → `Open(out_path,"HWPX","forceopen:true")` 반환값을 찍고 `Quit()`. `finalize_hwpx.py:234-266`의 `hancom_open_check`를 그대로 불러도 된다. **다른 Hwp 프로세스를 죽이지 마라.**
6. 경계 사례 1개: 두 `<hp:t>` run에 걸친 구절(예: 빨간 마커 바로 앞 검은 글자 + 마커 앞부분)을 치환하려 하면 어떻게 되는가 — 거부하는가, 깨뜨리는가, 올바르게 처리하는가. 결과만 기록한다.

## 산출물 (보고서 본문에 포함)

- 위 4·5·6의 증거(명령 + 출력)
- **"논문 타깃 치환 표준 절차"** — SKILL.md에 그대로 붙일 수 있는 형태로: 명령줄, `--map` 예시, 검증 순서, 발견한 주의점. 한국어.
- `fill_hwpx.py`가 이 용도로 부적합하다고 판단되면 그 근거와 대안(예: 저장소 자체 스크립트 신설 사양).

## Scope of action — DO NOT do these things

- Do NOT run `git add`, `git commit`, `git push`, or any git write command.
- Do NOT call any `mcp__hwpx__*` tool, read or write. 2.5MB 본문에서 40분 멈춘다.
- Do NOT write to `00. hwpx/**`. 복사본은 스크래치에만.
- Do NOT edit or create ANY file in the repository (`01.docs/**`, `tools/**`, `.claude/**`, `03.plan/**`, `MEMORY.md`, `CLAUDE.md`) or in `C:/Users/User/.claude/skills/**`.
- Do NOT `Stop-Process`/kill any Hwp process you did not start.
- If a step fails, stop, report the exact error output, and do not improvise.
