# HWPX 반입 워커 보고

워커 범위의 패치·코드·정적 검증은 완료했다. `patched.hwpx`는 한글 재조판 전 스크래치이며 최종 한글 산출물이 아니다. 한글 COM·PDF 출력·인쇄 쪽수 갱신은 실행하지 않았다.

## 산출물과 변경 코드

- 패치본: `tools/hwpx_transfer/staging/hwpx_261031/patched.hwpx`
- 조립 비교본: 같은 디렉터리 `assembled.hwpx`; 보고: `report.md`, `patch_report.md`
- 증거: `tests.txt`, `verification.txt`, `integrity.json`, `image_grid_plan.json`, `base_paragraphs.json`, `survey_targets.json`, `worker_changes.diff`
- 코드 변경: `tools/hwpx_transfer/md_to_blocks.py`, `kjn_profile.py`, `patch_from_fresh.py`; 신설 `image_grid.py`, `tests/test_image_grid.py`
- 작업 시작 전 도구 수정분은 `.before`로 보존했다. `blocks_to_hwpx.py`는 워커가 수정하지 않았으며 시작 시 바이트와 동일하다. 기존 table_merges 관련 수정은 유지했다.
- git 쓰기, `00. hwpx/` 쓰기, `01.docs/`·`03.plan/`·`.claude/` 수정, 한글 COM, HWPX MCP를 실행하지 않았다. 산출물·임시 파일은 지정 staging 안에만 썼다.

## MD 반입과 사용자 편집 보존

기본 patch_from_fresh는 부록 뒤를 통째로 보존하고 BinData를 복사하지 않으며, 제4장 재구성 22구간을 수동 처리로 남겼다. 기본 동작을 유지한 채 새 부록·이미지 반입과 과거 MD 검증 기반 구조 반입 옵션을 추가했다.
기준본 본문과 표의 텍스트가 `93aa8fb` 시점 MD를 조립한 `previous/body.xml`에 모두 존재함을 공백 정규화 후 확인했다. 이 검증에서 사용자 고유 추가 텍스트는 0건이었다. 불일치가 있으면 새 구조 반입 경로는 ValueError로 중단한다. `base_vs_previous_unknown.json`과 `base_vs_previous_tables.json`은 모두 빈 배열이다.
- 본문·참고문헌의 기존 최상위 항목 229개는 정확한 XML을 재사용했다. 이 가운데 내용 동일 표 14개는 병합·열폭·정렬·캐시를 포함한 기준본 XML이 그대로다.
- 현행 MD의 변경·새 항목 274개를 반입했다(표·그림 앵커 포함 최상위 항목 기준). 부록 2·3 최상위 문단은 추가 99개다.
- 본문·참고문헌의 비어 있지 않은 항목 497개는 현행 조립본과 순서까지 일치한다. 새 부록 2·3의 텍스트도 현행 MD 조립본과 일치한다.
- 설문 두 벌은 20회 타깃 치환만 했다. 전체 설문 XML을 기준본에 같은 치환만 적용한 기대값과 대조해 일치했다. 표지 제목 2곳도 타깃 치환했다.
- 변경 문단과 표 앵커 캐시만 제거했다. 변경된 표 셀의 형제 셀 캐시는 보존하는 타깃 치환 회귀 테스트를 추가했다. 새 그림 표에는 linesegarray가 없다.
- 참고문헌 v3 JSON은 10월 8일 스냅샷이라 jamovi 서지가 빠져 있었다. 최신 기준본의 7개 분류를 재사용하고 현행 MD에 추가된 산업안전보건법 시행령 항목만 더해 과거 서지로 되돌아가지 않게 했다.
- `images.json`의 오래된 연구 모형 경로를 그대로 쓰지 않았다. 현행 MD가 명시한 `figure_4-1_research_model_261029.png`를 사용했고 바이트 일치를 검사했다. 연구 흐름도도 현행 연결 이미지로 갱신했다. 기존 이미지 4개는 바이트 그대로이며 2개는 갱신된 내용으로 같은 6개 위치에 반입했다.
- 그림과 같은 바이트인 부록 PNG가 두 칸 존재한다. 칸별 그림 47개 규칙을 지키기 위해 서로 다른 입력 item은 중복 제거하지 않았다.
- `00_목차.md`의 표·부표 캡션 51개가 본문과 표 목차에 모두 존재한다. 부록 2·3 목차 항목도 포함된다. 인쇄 쪽수는 임시 0이며 실제 쪽수로 갱신해야 한다.

## 단위 테스트와 무결성 검사

명령: `python -m unittest discover -s tools/hwpx_transfer/tests -p "test_*.py" -v` (PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1, TEMP/TMP는 지정 staging). 기존 김정년 조립 회귀 21건을 포함하여 전체 46건 통과했다.

```text
test_a_caption_outside_before_table (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_a_caption_outside_before_table) ... ok
test_abstract_skeleton_parse (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_abstract_skeleton_parse) ... ok
test_b_header_row_border_fill (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_b_header_row_border_fill) ... ok
test_c_column_widths_content_based (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_c_column_widths_content_based) ... ok
test_d_blank_before_section_and_item (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_d_blank_before_section_and_item) ... ok
test_e_marker_runs_and_black_brackets (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_e_marker_runs_and_black_brackets) ... ok
test_f_no_cell_page_break (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_f_no_cell_page_break) ... ok
test_figure_caption_above_and_bindata (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_figure_caption_above_and_bindata) ... ok
test_full_assembly_with_task_g_profile (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_full_assembly_with_task_g_profile) ... ok
test_h_missing_profile_key_raises (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_h_missing_profile_key_raises) ... ok
test_i_cover_has_no_kjn_strings (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_i_cover_has_no_kjn_strings) ... ok
test_j_references_seven_categories (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_j_references_seven_categories) ... ok
test_single_column_table_open_sides (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_single_column_table_open_sides) ... ok
test_toc_tab_and_pages (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_toc_tab_and_pages) ... ok
test_transplant_remap_and_rescale (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_transplant_remap_and_rescale) ... ok
test_transplant_replace_appendix_and_thanks (test_blocks_to_hwpx_kjn.KjnAssemblyTests.test_transplant_replace_appendix_and_thanks) ... ok
test_g_baseline_is_from_pre_change_code (test_blocks_to_hwpx_kjn.LegacyRegressionTests.test_g_baseline_is_from_pre_change_code) ... ok
test_g_legacy_section2_identical (test_blocks_to_hwpx_kjn.LegacyRegressionTests.test_g_legacy_section2_identical) ... ok
test_legacy_profile_extras_explicit (test_blocks_to_hwpx_kjn.LegacyRegressionTests.test_legacy_profile_extras_explicit) ... ok
test_short_table_whole (test_blocks_to_hwpx_kjn.TableSplitTests.test_short_table_whole) ... ok
test_tall_table_row_split (test_blocks_to_hwpx_kjn.TableSplitTests.test_tall_table_row_split) ... ok
test_all_grids_preserve_sizes_and_complete_occupancy (test_image_grid.ImageGridTests.test_all_grids_preserve_sizes_and_complete_occupancy) ... ok
test_parser_47_cells_nine_captions (test_image_grid.ImageGridTests.test_parser_47_cells_nine_captions) ... ok
test_patch_imports_assets_manifest_and_new_appendix (test_image_grid.ImageGridTests.test_patch_imports_assets_manifest_and_new_appendix) ... ok
test_target_change_clears_ancestor_cache_only (test_image_grid.StructuralPatchTests.test_target_change_clears_ancestor_cache_only) ... ok
test_unknown_user_text_blocks_structural_replacement (test_image_grid.StructuralPatchTests.test_unknown_user_text_blocks_structural_replacement) ... ok
test_verified_structure_reorders_and_keeps_merged_table_xml (test_image_grid.StructuralPatchTests.test_verified_structure_reorders_and_keeps_merged_table_xml) ... ok
test_changed_paragraph_taken_from_fresh_with_id_remap (test_patch_from_fresh.PatchFromFreshTest.test_changed_paragraph_taken_from_fresh_with_id_remap) ... ok
test_merged_body_and_caption_split (test_patch_from_fresh.PatchFromFreshTest.test_merged_body_and_caption_split) ... ok
test_merged_cell_covering_text_in_fresh_differs (test_patch_from_fresh.PatchFromFreshTest.test_merged_cell_covering_text_in_fresh_differs) ... ok
test_merged_table_changed_content_keeps_base_and_reports (test_patch_from_fresh.PatchFromFreshTest.test_merged_table_changed_content_keeps_base_and_reports) ... ok
test_merged_table_same_content_keeps_base (test_patch_from_fresh.PatchFromFreshTest.test_merged_table_same_content_keeps_base) ... ok
test_invalid_or_orphan_directive_refused (test_table_merges.DeclaredMergesTest.test_invalid_or_orphan_directive_refused) ... ok
test_legacy_caption_row_offset (test_table_merges.DeclaredMergesTest.test_legacy_caption_row_offset) ... ok
test_minimal_preservation_and_idempotence (test_table_merges.DeclaredMergesTest.test_minimal_preservation_and_idempotence) ... ok
test_nonempty_covered_cell_refused (test_table_merges.DeclaredMergesTest.test_nonempty_covered_cell_refused) ... ok
test_real_markdown_assembly_and_grid (test_table_merges.DeclaredMergesTest.test_real_markdown_assembly_and_grid) ... ok
test_width_mismatch_refused (test_table_merges.DeclaredMergesTest.test_width_mismatch_refused) ... ok
test_allow_tables_exclusion_wins (test_table_merges.PatchDeclaredMergesTest.test_allow_tables_exclusion_wins) ... ok
test_allow_tables_still_preserves_layout_result (test_table_merges.PatchDeclaredMergesTest.test_allow_tables_still_preserves_layout_result) ... ok
test_explicit_protection_wins (test_table_merges.PatchDeclaredMergesTest.test_explicit_protection_wins) ... ok
test_fresh_without_merges_refused (test_table_merges.PatchDeclaredMergesTest.test_fresh_without_merges_refused) ... ok
test_legacy_labels_merge_and_preserve_user_format (test_table_merges.PatchDeclaredMergesTest.test_legacy_labels_merge_and_preserve_user_format) ... ok
test_same_content_still_merges (test_table_merges.PatchDeclaredMergesTest.test_same_content_still_merges) ... ok
test_stale_fresh_refused (test_table_merges.PatchDeclaredMergesTest.test_stale_fresh_refused) ... ok
test_unexpected_legacy_label_refused (test_table_merges.PatchDeclaredMergesTest.test_unexpected_legacy_label_refused) ... ok

----------------------------------------------------------------------
Ran 46 tests in 3.817s

OK
```

```text
PASS: ZIP/XML/style refs; 53 image payloads/manifest refs; 47 unchanged jamovi PNGs; 9 grids; current MD text/TOC; red/black markers; original SHA256
markers 25 black brackets 102 tables preserved 14
```

- ZIP 엔트리 66개, 모든 XML/HPF 9개 파싱 성공, ZIP CRC·중복 경로·mimetype 저장 형식 확인.
- BinData 53개 = 기존 그림 위치 6 + 부록 그림 47. manifest 53개와 실제 hc:img 참조 53개가 일치한다. 모든 부록 PNG는 원본 바이트 그대로다.
- section 내 charPr·paraPr·borderFill·style 참조 모두 유효. pageBreak="CELL" 0건. 빨강 마커 25건 및 검정 숫자·양식 대괄호 102건 확인.
- `git diff --check`는 변경된 추적 코드에서 오류 없이 종료했다.

## 부록 3 표별 폭 정합

아래 행 수는 Markdown의 빈 구조용 머리행을 제외한 실제 그림 행 수다. 한 행의 빈 후속 칸은 앞 그림 칸에 가로 병합했다. 예를 들어 3-3의 134.2mm 그림은 2열을 차지하고 3-4의 첫 두 행 둘째 그림은 2·3열을 차지한다. 원본 그림의 행·수치·픽셀은 전혀 자르지 않았다.
전체 폭은 기존 표 관례 39684 HWPUNIT(약 140mm)을 따랐다. 열폭 합·각 행의 셀 폭 합·병합 점유 격자의 중복/누락을 검사했고 모두 일치했다. 일반 좌우 여백은 각 142 HWPUNIT이며 3-5만 0이다. 3-5 그림은 143.2mm에서 실제 본문 폭 약 140mm로 비례 축소했다.

| 부표 | 행 × 열 | 열폭 HWPUNIT | 전체 폭 / 각 행 폭 합 | 쪽 나눔 |
|---|---:|---|---:|---|
| <부표 3-1> | 4 × 1 | [39684] | 39684 | TABLE |
| <부표 3-2> | 1 × 2 | [22790, 16894] | 39684 | NONE |
| <부표 3-3> | 6 × 2 | [22660, 17024] | 39684 | TABLE |
| <부표 3-4> | 5 × 3 | [16545, 11569, 11570] | 39684 | TABLE |
| <부표 3-5> | 1 × 1 | [39684] | 39684 | NONE |
| <부표 3-6> | 1 × 1 | [39684] | 39684 | NONE |
| <부표 3-7> | 4 × 2 | [24554, 15130] | 39684 | NONE |
| <부표 3-8> | 10 × 1 | [39684] | 39684 | TABLE |
| <부표 3-9> | 2 × 1 | [39684] | 39684 | TABLE |

### 칸별 인쇄 그림 크기

| 파일 | 행·열 / colspan | 셀 폭 HWPUNIT | 그림 폭 × 높이 mm |
|---|---|---:|---|
| 부표3-1_01.png | 1행 1열 / 1 | 39684 | 86.2011 × 59.1995 |
| 부표3-1_02.png | 2행 1열 / 1 | 39684 | 86.2011 × 59.1995 |
| 부표3-1_03.png | 3행 1열 / 1 | 39684 | 86.2011 × 72.1994 |
| 부표3-1_04.png | 4행 1열 / 1 | 39684 | 91.7997 × 85.1992 |
| 부표3-2_01.png | 1행 1열 / 1 | 22790 | 73.2013 × 105.0006 |
| 부표3-2_02.png | 1행 2열 / 1 | 16894 | 53.9996 × 57.0017 |
| 부표3-3_01.png | 1행 1열 / 2 | 39684 | 134.2 × 86.2011 |
| 부표3-3_02.png | 2행 1열 / 1 | 22660 | 76.1999 × 21.0008 |
| 부표3-3_03.png | 2행 2열 / 1 | 17024 | 36.9993 × 21.0008 |
| 부표3-3_04.png | 3행 1열 / 2 | 39684 | 51.7983 × 68.9997 |
| 부표3-3_05.png | 4행 1열 / 2 | 39684 | 134.2 × 62.2017 |
| 부표3-3_06.png | 5행 1열 / 1 | 22660 | 76.1999 × 21.0008 |
| 부표3-3_07.png | 5행 2열 / 1 | 17024 | 36.9993 × 21.0008 |
| 부표3-3_08.png | 6행 1열 / 2 | 39684 | 51.7983 × 45.0003 |
| 부표3-4_01.png | 1행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-4_02.png | 1행 2열 / 2 | 23139 | 63.2 × 69.2008 |
| 부표3-4_03.png | 2행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-4_04.png | 2행 2열 / 2 | 23139 | 63.4999 × 45.2013 |
| 부표3-4_05.png | 3행 1열 / 1 | 16545 | 50.2002 × 51.9994 |
| 부표3-4_06.png | 3행 2열 / 2 | 23139 | 50.2002 × 51.9994 |
| 부표3-4_07.png | 4행 1열 / 1 | 16545 | 50.2002 × 51.9994 |
| 부표3-4_08.png | 4행 2열 / 1 | 11569 | 34.8015 × 27.0016 |
| 부표3-4_09.png | 4행 3열 / 1 | 11570 | 34.8015 × 27.0016 |
| 부표3-4_10.png | 5행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-4_11.png | 5행 2열 / 2 | 23139 | 34.8015 × 27.0016 |
| 부표3-5_01.png | 1행 1열 / 1 | 39684 | 139.9961 × 108.7118 |
| 부표3-6_01.png | 1행 1열 / 1 | 39684 | 101.9985 × 40.0014 |
| 부표3-7_01.png | 1행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 부표3-7_02.png | 1행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 부표3-7_03.png | 2행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 부표3-7_04.png | 2행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 부표3-7_05.png | 3행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 부표3-7_06.png | 3행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 부표3-7_07.png | 4행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 부표3-7_08.png | 4행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 부표3-8_01.png | 1행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-8_02.png | 2행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-8_03.png | 3행 1열 / 1 | 39684 | 116.801 × 70.0016 |
| 부표3-8_04.png | 4행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-8_05.png | 5행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-8_06.png | 6행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-8_07.png | 7행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-8_08.png | 8행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-8_09.png | 9행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-8_10.png | 10행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-9_01.png | 1행 1열 / 1 | 39684 | 130.1995 × 141.1991 |
| 부표3-9_02.png | 2행 1열 / 1 | 39684 | 128.0017 × 81.9995 |

## 수동 재적용 필요 — patch_report 전문

- <표1-2> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표2-2> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표2-4> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표2-5> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표3-2> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표3-10> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표3-11> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-1> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-2> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-3> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-4> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-5> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-6> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-7> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-9> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-10> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-12> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-13> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-14> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-15> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-16> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- <표4-17> 내용·구조 변경으로 fresh 표 반입 — 기존 사용자 열폭·병합·정렬과 새 내용의 적합성을 한글에서 확인·필요 시 재적용
- section1(목차·감사의 글·논문 개요)을 조립본으로 교체 — base의 목차 run 압축(장평·자간) 등 사용자 서식은 재적용 필요

이 23건은 내용 미반입 목록이 아니다. 내용이 바뀐 본문 표 22개와 교체한 전면부 1개의 서식 재확인 목록이다. 현행 MD 내용은 이미 반입되어 있다.

## 기준본 SHA256

- 기준본: `00. hwpx/261028_0757_경기공학_건축안전_윤혁_논문.hwpx`
- 작업 전: `72fa90d52fdbe2e0e796e5929e6d62b8e82e571ffd28ffe0bedd6e242cd56bf7`
- 작업 후: `72fa90d52fdbe2e0e796e5929e6d62b8e82e571ffd28ffe0bedd6e242cd56bf7`
- 동일: **예**. staging/base.hwpx도 같은 SHA256이다.
- 패치본 SHA256: `9ae1bca1887d0ed6999c3112cf0d386851c54a9df4f2ed109321a662d86fb861`

## 남은 검증과 알려진 제한

1. 메인이 patched.hwpx를 한글 COM으로 실제 Open하고 재조판 SaveAs해야 한다. 스크래치의 ZIP/XML 통과는 한글 개방 또는 인쇄 배치 성공을 의미하지 않는다.
2. 전 표 PDF 검증과 부록 3 쪽 육안 검사가 필요하다. 행 높이는 최소값·추정치이며, TABLE로 나뉜 부표의 행 연속성·라벨과 그림의 같은 셀 배치·꼬리말 침범·표 뒤 본문을 확인해야 한다. 구조용 빈 머리행은 출력하지 않아 repeatHeader=0이며 모든 그림 행의 header=0이다.
3. 라벨은 기존 한양신명조 9pt 스타일을 적용했다. Windows GDI는 한양신명조 대신 굴림을 반환하여 라벨 줄 수 계산은 굴림 실측 대체값이다. 그림 폭은 manifest로 정확히 정했지만 한글의 실제 라벨 줄바꿈은 재조판으로 확인해야 한다.
4. `부록3_jamovi_원출력.md`의 “모든 출력은 같은 배율로 실었다”는 문장에는 브리프의 3-5 축소 예외가 표현되지 않았다. MD 수정은 금지되어 그대로 두었다. 필요하면 메인이 예외 문구를 판단한다.
5. 목차/표 목차/그림 목차는 PDF의 실제 인쇄 쪽수로 갱신하고, 다시 저장·출력하여 목차 변경에 따른 이동까지 확인해야 한다.
6. section1은 fresh로 교체했으므로 목차 장평·자간 등 사용자가 적용한 서식은 확인·재적용이 필요하다. 감사의 글 텍스트는 최신 기준본에서 이식했다.

## 재현 순서

`PYTHONIOENCODING=utf-8`을 설정하고 저장소 루트에서 실행한다. 아래 작업은 모두 staging 산출물만 생성하며 COM을 호출하지 않는다.

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python tools/hwpx_transfer/md_to_blocks.py --out-dir tools/hwpx_transfer/staging/hwpx_261031
python tools/hwpx_transfer/staging/hwpx_261031/assemble.py
python tools/hwpx_transfer/staging/hwpx_261031/patch.py
python tools/hwpx_transfer/staging/hwpx_261031/verify.py
```

`previous/`는 93aa8fb의 1~5장 MD를 git show로 읽어 만든 비교 자료이며 원고가 아니다. 기준본·양식 추출본·단계별 JSON도 모두 스크래치다.
