# T1 검증 결과 — FAILED

style_map.json의 표 pageBreak만 CELL에서 NONE으로 변경하고 repeatHeader=1은 운영본 관례에 맞춰 유지했다.
PYTHONIOENCODING=utf-8로 md_to_blocks.py 및 지정 FILES 순서의 blocks_to_hwpx.py --smoke 실행은 모두 exit 0이었다.
최종 검증에서 전체 smoke.hwpx의 CELL이 5개여서 수용 기준에 실패했고 브리프 지시에 따라 추가 수정 없이 중단했다.

## 표 속성 조합 개수

| 파일 / 구역 | pageBreak | repeatHeader | 표 개수 |
|---|---|---|---:|
| 운영본 260911_1101 / section2.xml | NONE | 1 | 48 |
| smoke / section0.xml | NONE | 1 | 3 |
| smoke / section1.xml | CELL | 1 | 5 |
| smoke / section2.xml | NONE | 1 | 46 |
| smoke 전체 | NONE | 1 | 49 |
| smoke 전체 | CELL | 1 | 5 |

smoke.hwpx: 180440 bytes, 총 54개 표, CELL=5 (요구값 0).
Python zipfile + 정규식으로 모든 Contents/section*.xml의 hp:tbl 시작 태그를 집계했다.
한글 COM 개방 및 재저장은 수행하지 않았으며, 실제 한글 개방 가능 여부는 검증하지 않았다.

## style_map.json diff

```diff
diff --git a/tools/hwpx_transfer/staging/style_map.json b/tools/hwpx_transfer/staging/style_map.json
index e6d70fc..9b805cf 100644
--- a/tools/hwpx_transfer/staging/style_map.json
+++ b/tools/hwpx_transfer/staging/style_map.json
@@ -60,7 +60,7 @@
       "textFlow": "BOTH_SIDES",
       "lock": "0",
       "dropcapstyle": "None",
-      "pageBreak": "CELL",
+      "pageBreak": "NONE",
       "repeatHeader": "1",
       "cellSpacing": "0",
       "borderFillIDRef": "6",
```

## parse_report.md 커버리지 요약 (원문)


모든 비어있지 않은 원본 행에 대해 (a) 블록 text/runs/cell 포함 또는 (b) excluded 기록을 확인했다. 비교 전 리스트 글머리와 마커 문자(`#`, `|`, `**`, 백틱, `-`, `\`, `>`)·공백을 정규화했다. '마커뿐'은 정규화 후 내용이 남지 않는 행(수평선·표 구분행 등)이다.

| 파일 | 총 행 | 비어있지 않은 행 | 내용 대조 통과 | 마커뿐(자동 통과) | 누락 |
|---|---:|---:|---:|---:|---:|
| 01_서론.md | 134 | 85 | 78 | 7 | 0 |
| 02_이론적배경.md | 275 | 170 | 156 | 14 | 0 |
| 03_시스템개발.md | 228 | 140 | 132 | 8 | 0 |
| 04_연구설계.md | 262 | 180 | 169 | 11 | 0 |
| 05_실증분석결과.md | 281 | 192 | 173 | 19 | 0 |
| 06_결론.md | 128 | 78 | 72 | 6 | 0 |
| 부록1_설문지_양식.md | 202 | 133 | 119 | 14 | 0 |
| 부록2_설문항목_근거매핑.md | 157 | 130 | 119 | 11 | 0 |

**누락 0 — 8개 파일 전체에서 커버리지 목표를 충족했다.**


## 추가 관찰 및 남은 작업

Python 소스의 CELL 검색 결과는 CELL_BOLD_CHAR 및 CELL_LINEBREAK_TOKEN 식별자뿐이며, staging JSON에는 CELL이 남지 않았다.
section1의 CELL 5개를 제거하는 후속 범위 결정 및 수정이 필요하다; 생성 결과를 임의로 후처리하지 않았다.
조립 리포트는 references.json flagged 30건 제외 및 관련법 확정 항목 없음, 구 표지 제목 보존을 기록한다.
00. hwpx 및 두 Python 스크립트는 수정하지 않았고 git 쓰기 명령 및 hwpx MCP 도구를 사용하지 않았다.
