# 자연화분 HWPX 반입 결과

- 결과: 성공. 산출물 `00. hwpx/261028_0644_경기공학_건축안전_윤혁_논문_자연화반영본.hwpx`.
- 검증용 PDF: `tools/hwpx_transfer/staging/natural_261028/final.pdf`, 총 141쪽(브리프의 기준본 140쪽 대비 +1쪽).
- 제5장: PDF 118~121쪽, 실제 인쇄 쪽수 105~108. 다음 참고문헌은 인쇄 109쪽.
- 원고·규칙·도구 본체·기존 HWPX는 수정하지 않았으며 git add/commit/push도 실행하지 않았다.

## 실행과 승인

1. `PYTHONIOENCODING=utf-8` 환경에서 `python tools/hwpx_transfer/md_to_blocks.py` 실행. 7개 블록 JSON, 총 562블록, coverage missing=0. `apx2.blocks.json`도 도구의 기본 출력으로 갱신되지만 조립에는 넣지 않았다.
2. 양식은 `git show HEAD:00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx`의 바이너리를 Python subprocess로 받아 작업 폴더 `template_kjn.hwpx`에만 저장했다. 원래 위치에는 복원하지 않았다.
3. 브리프의 `blocks_to_hwpx.py` 인자를 그대로 사용해 `fresh.hwpx`, `fresh_report.md` 생성. 프로파일 style_map_kjn.json, references_kjn_v4.json, images.json, transplant.json, --no-tail 사용. 본문 문단 762개.
4. `patch_from_fresh.py --dry-run`: equal=619, replace_fresh=66, insert=0, replace_kept=0, delete_kept=0, manual=0, table_same_kept=6. header 추가 없음.
5. 표 교체 0 기대와 달리 표 4-5 하나가 교체되고 3장 문단도 변경되어 `orca orchestration ask`로 문의했다. 코디네이터가 모두 반입 승인: 표 4-5의 모집 목표에 ‘이상’ 추가, 1장 공간적 범위에 ‘이상’ 추가, 3장 도입 현장 32→34개소는 05:57 MD 수정의 미반영분이다. 표 4-5 기준본/조립본의 14행×2열 격자·병합·모든 셀 폭(9820/29864)이 동일한 것을 확인하고 반입했다. 2장 변경 없음. 상세 목록은 `patch_dry_report.md`.
6. 실제 patch도 동일 통계로 성공. `patched.hwpx`, `patch_report.md` 생성. --force-fresh 및 --toc-from-fresh 미사용.
7. 1차 재조판: `resave-hwpx.ps1`의 Open/SaveAs(HWPX)/Reopen/SaveAs(PDF) 모두 True, RESULT OK. 근거 `resave1.log`.
8. `pdf_table_check.py resaved1.pdf`: 괘선 검출 57쪽, 꼬리말 침범 0. `toc_pages_from_pdf.py patched.hwpx resaved1.pdf toc_pages.json` 실행. 자동 미매칭 3개는 PDF 글자와 실제 꼬리말을 직접 읽어 보완: 논문개요 ix(PDF 12), 도입 부록 117(PDF 130), 미도입 부록 124(PDF 137). 물리 순번을 인쇄 쪽수로 사용하지 않았다.
9. `toc_numbers_patch.py patched.hwpx toc_pages.json patched_toc.hwpx`: 11항목 변경, 113항목 유지, 미매칭 0. 2차 재조판으로 산출물 저장. Open/SaveAs(HWPX)/Reopen/SaveAs(PDF) 모두 True, RESULT OK, 파일 잠금 없음. 근거 `resave2.log`.
10. 최종 PDF 재추출 후 같은 3항목을 실제 꼬리말로 보완했다. `toc_final.json`과 주입 `toc_pages.json` 완전 동일. 최종 HWPX 안의 실제 목차 쪽수 124항목도 JSON과 차이 0(`toc_verification.json`). 최종 PDF 표 침범 0(`final_tables.json`).

실행 환경 보정: PowerShell 기본 파이프 인코딩에서 한글 경로가 `?`로 변해 최초 해시 읽기만 실패했다. `$OutputEncoding=[System.Text.UTF8Encoding]::new()`로 해결했다. 이 PC에는 `pwsh`가 없고 Windows PowerShell은 BOM 없는 스크립트를 잘못 읽으므로, 도구 원문을 수정하지 않고 `& ([scriptblock]::Create((Get-Content -LiteralPath '.claude/skills/hwpx-thesis-editing/scripts/resave-hwpx.ps1' -Raw -Encoding UTF8)))`에 동일 인자를 넘겼다. COM 작업은 단독·순차 수행했다.

## 최종 대조

- `verification.json`: section0/1/2의 비어 있지 않은 문단 텍스트가 `patched_toc.hwpx`와 모두 동일. 재저장에 따른 빈 문단 정규화는 텍스트 비교에서 제외.
- 제5장 MD 본문 11문단 모두 글자 그대로 존재(블록 JSON의 본문 문자열과 대조).
- 4장 주효과 p=.519/미도입 기울기 −0.208 문장, 제1절 첫 문단, 1장 ‘LLM 검증 기능만의 기여는 따로 가리지 않는다’ 모두 존재.
- 옛 p=.519 기울기 문장, ‘분리하지 못하며’, ‘시사점은 세 가지이다’ 각각 0건.
- 빨간 charPr를 header.xml에서 각 파일별로 다시 판정: 전체 빨간 run 기준본/최종본 28/28. 접두사 포함 빨간 run은 확정 필요 13/13, CITE_TODO 9/9, UNVERIFIED 4/4, DATA PENDING·그림 삽입 예정·실험전 각 0/0. 비빨강 run에서 온전한 접두사 검출은 양쪽 모두 0건(브리프의 과거 검정 예외를 이번 파일에서 새로 가정하지 않음).
- 본문·부록 표 개체 55/55: 모든 표의 열폭·행열 주소·병합 격자 동일. 표 4-7 패널 A/B/C, 4-10~4-14 전체 보존. 표 내용은 승인된 4-5만 변경, 나머지 54개 동일.
- pageBreak=CELL 0건. 김정년·안전시설물·떨어짐 사고위험·김정년 원제목 각각 0건.
- 최종 PDF에서 괘선 검출 57쪽 전체를 `table_sheet_1.png`~`table_sheet_5.png`로 시각 확인. 전반 배치·표 끝·이어지는 머리행·본문과 꼬리말 간 여백 확인. 꼬리말 없는 PDF 3쪽은 인준지, 14쪽은 본문 첫 쪽 번호 숨김이며 하단 잘림 없음. 접촉 시트는 배치 확인용이며 글자 단위 원문 보존은 XML 대조로 검증했다.

## SHA256

| 파일 | SHA256 |
| --- | --- |
| 기준본 `00. hwpx/261028_0544_경기공학_건축안전_윤혁_논문_표4-11_4-13_4-14_미입력값반영본.hwpx` | `2b00512634526fc6c466e9909376bdb1ff6332e96f574dff9954faecff535965` (전후 불변) |
| 작업 폴더 `template_kjn.hwpx` | `9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3` (전후 불변) |
| 최종 자연화반영본 | `eddab53be59038e36822640f7bfc6c3a1f1f5674b45ddbf614c3d66bb3130f18` |

남은 작업: 없음. 커밋은 코디네이터 소관이다. PDF와 중간 파일은 작업 폴더에만 남겼다.
