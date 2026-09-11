# T1 브리프 — 조립기 표 `pageBreak="CELL"` 회귀 차단 + 스테이징 재생성 + 스모크 조립

담당: codex (`gpt-6-astra`, effort low). 상위 계획: `03.plan/260912_0714_hwpx도구개선_오케스트레이션.md`.

## 배경 (재탐색 금지)

- `tools/hwpx_transfer/staging/style_map.json:63`이 `"pageBreak": "CELL"`, `:64`가 `"repeatHeader": "1"`이다. `blocks_to_hwpx.py:251-261`이 이 값을 **모든 표**에 그대로 찍는다.
- 프로젝트 규칙(`.claude/rules/hwpx-output-verification.md` 표 쪽 넘김 절)은 `CELL`을 **금지**한다. 운영본 `00. hwpx/260911_1101_경기공학_건축안전_윤혁_논문작성_작성본.hwpx`의 표 48개는 전부 `NONE`으로 손질돼 있다. 조립기를 지금 돌리면 그 작업이 되돌아간다 — 이걸 막는다.
- 스테이징 `staging/*.blocks.json`은 2026-08-24본이고 원고 `01.docs/`는 2026-09-02까지 바뀌었다. 재생성한다.
- 두 스크립트 모두 한국어·줄표(`—`)를 출력하므로 **`PYTHONIOENCODING=utf-8`을 앞에 붙이지 않으면 cp949 `UnicodeEncodeError`로 죽는다.** 스크립트 버그가 아니다.

## 작업 (순서대로)

1. 운영본이 쓰는 표 속성 관례를 확인한다. Python `zipfile`로 `Contents/section2.xml`을 읽어 `<hp:tbl ` 태그의 `pageBreak`·`repeatHeader` 값 조합별 개수를 센다(정규식으로 충분). **`mcp__hwpx__*` 도구는 절대 쓰지 않는다** — 2.5MB 본문에서 40분 멈춘다.
2. `style_map.json:63`의 `"CELL"`을 `"NONE"`으로 바꾼다. `repeatHeader`는 1번에서 확인한 운영본 관례(`NONE`과 짝지어진 값)에 맞춘다. 파일의 다른 곳은 손대지 않는다.
3. `grep -n CELL tools/hwpx_transfer/*.py tools/hwpx_transfer/staging/*.json`으로 다른 하드코딩이 없는지 확인한다. 있으면 고치지 말고 보고한다.
4. 저장소 루트에서 `PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/md_to_blocks.py` 실행. `staging/parse_report.md`의 커버리지 결과(파일별 행 수·미매핑 행)를 그대로 옮겨 적는다. 미매핑이 있으면 **고치지 말고** 보고한다.
5. 스모크 조립. 블록 파일 순서는 `md_to_blocks.py` 상단 `FILES` 매핑의 순서를 따른다(`ls staging/*.blocks.json`으로 실제 파일명 확인):
   ```
   PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/blocks_to_hwpx.py --smoke \
     --template "공학대학원_건축안전_윤혁_중소규모 건설현장을 위한 YOLO-VLM 안전관제 시스템 실증 연구 알람 피로도 완화와 안전 자원 제약성의 조절효과를 중심으로 - 복사본.hwpx" \
     --style-map tools/hwpx_transfer/staging/style_map.json \
     --blocks <블록 파일들 순서대로> \
     --references tools/hwpx_transfer/staging/references.json
   ```
   출력은 `tools/hwpx_transfer/staging/test_out/smoke.hwpx`다.
6. `smoke.hwpx`를 Python `zipfile`로 열어 `<hp:tbl ` 태그의 `pageBreak` 값별 개수를 센다. **`CELL`이 0개**여야 한다.

## 수용 기준 (증거를 그대로 붙여라)

- `style_map.json` diff (`git diff tools/hwpx_transfer/staging/style_map.json`)
- 운영본 표 속성 조합 개수표 / 스모크 표 속성 조합 개수표
- `parse_report.md` 커버리지 요약
- `smoke.hwpx` 크기와 표 개수

## 편집 허용 범위

`tools/hwpx_transfer/staging/**`만 (style_map.json, *.blocks.json, parse_report.md, test_out/smoke.hwpx). 그 밖의 파일은 읽기만 한다.

## Scope of action — DO NOT do these things

- Do NOT run `git add`, `git commit`, `git push`, or any git write command.
- Do NOT call any `mcp__hwpx__*` tool, read or write. Use Python `zipfile` + regex only.
- Do NOT write to `00. hwpx/**` (원본·운영본). `--output`을 `00. hwpx/`로 주지 마라 — `--smoke`만 쓴다.
- Do NOT edit `blocks_to_hwpx.py`, `md_to_blocks.py`, `01.docs/**`, `.claude/**`, `MEMORY.md`, `CLAUDE.md`, `03.plan/**`.
- If a step fails, stop, report the exact error output, and do not improvise a fix outside the allowed scope.
