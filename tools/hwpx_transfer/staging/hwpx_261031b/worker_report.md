# jamovi 본문·부록 분리 — 워커 보고

요청된 코드 확장·패치·정적 검증을 완료했다. `patched.hwpx`는 한글 재조판 전 검토용이며 최종 인쇄 산출물이 아니다. 한글 COM·PDF 출력·실제 인쇄 쪽수 갱신은 메인이 수행해야 한다.

## 산출물과 변경 파일

- 결과: `tools/hwpx_transfer/staging/hwpx_261031b/patched.hwpx`
- 비교 조립본: 같은 폴더 `assembled.hwpx`; 보고: `patch_report.md`, `worker_report.md`
- 증거: `integrity.json`, `image_grid_plan.json`, `changes.json`, `patch_stats.json`, `tests.txt`, `verification.txt`, `section1_base_paragraphs.json`, `section2_base_paragraphs.json`
- 확장 코드: `tools/hwpx_transfer/md_to_blocks.py`, `image_grid.py`, `kjn_profile.py`, `tests/test_image_grid.py`
- 모든 생성물·임시 파일은 지정 staging에 저장했다. git 쓰기, 00. hwpx 쓰기, 한글 COM, hwpx/rhwp MCP, 01.docs·03.plan·.claude·MEMORY·CLAUDE 수정은 하지 않았다.
- 선행 assemble·Patcher의 스타일/이미지 반입·verify 로직을 재사용했다. 단순히 선행 assemble.py를 1206에 적용하면 참고문헌 법령 중복, 역할 용어 중복 치환, 설문 이식 범위에 부록 2·3 혼입이 생기므로 이전에 검증된 references.json·transplant.json을 읽어 비교용 조립본을 만들고 실제 패치는 1206 복사본에만 적용했다.

## 구현과 기준본 보존

본문 격자 앞 `jamovi 원출력(<표 n>)` 문단을 인식하고 manifest의 `for` 대상과 일치하는지 검사한다. 번호 없는 격자는 독립 표/그림 목차 항목을 추가하지 않으며 근거 대상과 그림 크기는 조립 증거에 기록한다. 부록 격자 기능과 원본 PNG 바이트는 유지했다.

1206의 실제 문단을 덤프한 뒤 선행 조립본↔현행 조립본의 변경 구간을 대조했다. 주 문장은 마지막 jamovi 안내 문장만 타깃 치환하고, 본문에는 머리 문단 4개·격자 4개를 삽입했다. 부록 3의 같은 문단과 5개 격자는 정확한 기준본 XML을 재사용하고, 머리말과 부표 번호·표 목차 항목만 변경했다. 동일 PNG 두 칸을 합치지 않도록 fresh 이미지와 기존 BinData 사이에 바이트 기반 일대일 매핑을 만들었다.

- section2 최상위 문단 XML 그대로 보존: 802개(빈 문단 포함).
- 기존 본문 표 36개 전부 XML 그대로 보존. 부록 3의 남은 격자 5개도 XML 그대로. 설문·부록 2까지 포함한 기존 최상위 표 보존 57개.
- 본문·참고문헌에서는 변경 주 문장 7개를 제외한 기존 문단 650개가 순서·XML 그대로이며 새 항목은 8개이다.
- 부록 3: 같은 문단 18개 보존, 캡션 4개 번호만 치환, 새 머리말 1개 반입, 이전 항목 17개 퇴역(이동 격자·기존 캡션·안내 주·머리말·빈 문단 포함).
- section1: 부표 목차 번호 4개만 치환, 본문으로 이동한 항목 4개 제거. 나머지 문단 191개 XML 보존. 남는 부표의 기존 인쇄 쪽수 문자열은 모두 그대로이다.
- 표지, 설문 두 벌, 부록 2의 XML은 기준본과 정확히 같다. 전체 section2의 비어 있지 않은 텍스트는 현행 MD 조립본과 순서까지 일치한다.
- 변경 문단·새 격자/셀의 linesegarray는 없으며 무관한 문단과 보존 표의 캐시는 그대로이다.

**브리프 예상과 다른 점:** 변경된 본문 주는 9개가 아니라 7개다. 선행·현행 조립본 비교에서 바뀐 주는 표 4-7·4-8·4-9·4-10·4-12·4-15·4-16이다. 표 4-6의 부표 3-1 참조는 그대로이고 표 4-11에는 기존 주가 없다. MD를 임의로 고치지 않았다.

## 보존·치환·삽입 통계

```json
{
  "equal": 802,
  "insert": 8,
  "replace_fresh": 1,
  "replace_kept": 0,
  "delete_kept": 0,
  "manual": 0,
  "table_same_kept": 57,
  "caption_split": 0,
  "body_notes_targeted": 7,
  "appendix_exact_kept": 18,
  "appendix_captions_targeted": 4,
  "appendix_retired": 17,
  "toc_titles_targeted": 4,
  "toc_removed": 4,
  "section1_exact_kept": 191
}
```

## 바뀐 문단 목록

- 본문 주 치환: 부록 3 <부표 3-2>에 제시하였다. → 표 아래에 함께 제시하였다.
  - 해당 문단: 주: 경력은 연 단위 정수로 수집하며(1년 미만은 0, 6개월 이상은 올림) 그대로 연속값으로 사용하였다. 만 나이와 경력은 분석에서도 연속값으로 사용하며, 구간 코드나 구간 중간값으로 대체하지 않았다. 두 변수 모두 결측은 0건이다. jamovi 원출력은 표 아래에 함께 제시하였다.
- body_insert: jamovi 원출력(<표 4-7>). 현장 도입 여부 0=미도입·1=도입.
- body_insert: (가) 현장 도입 여부별 (나) 전체
- 본문 주 치환: 부록 3 <부표 3-3>에 제시하였다. → 부록 3 <부표 3-2>에 제시하였다.
  - 해당 문단: 주: 탐색적 요인분석은 표본 적절성(KMO), 구형성 검정(Bartlett), 추출 요인 수, 적재 양상, 설명분산과 문항 제거 여부를 보고하였다. 안전관리 예산 제약성은 분석 척도로 검토하고, 도입 현장 전용부 D·E는 제3장 제4절 제5항에 기술통계로만 보고하였으므로 요인분석 대상에서 제외하였다. 유효 73명 전체를 대상으로 jamovi의 주축요인추출을 적용하고 고유값 1 이상 기준과 스크리 도표로 요인 수를 정하였으며(Costello & Osborne, 2005), Y·W 모두 첫 요인의 고유값만 1을 넘어(Y 5.33, W 3.06) 1요인이 추출되었고 회전은 적용되지 않았다. 첫 요인의 설명분산은 Y 66.6%, W 76.5%이다. 문항별 적재값은 B-1 0.793, B-2 0.773, B-3 0.807, B-4 0.842, B-5 0.727, B-6 0.810, B-7 0.888, B-8 0.875, C-1 0.922, C-2 0.955, C-3 0.826, C-4 0.784이며, 적재값 범위는 그 최솟값과 최댓값이다. jamovi 원출력은 부록 3 <부표 3-2>에 제시하였다.
- 본문 주 치환: 부록 3 <부표 3-4>에 제시하였다. → 부록 3 <부표 3-3>에 제시하였다.
  - 해당 문단: 주: 단일 문항 두 영역에는 α를 산출하지 않았다. 2문항 세 영역은 α 대신 전체 표본의 문항 간 상관(Pearson r)을 보고하고 8문항 전체의 내적 일관성과 구분하였다. D·E의 기술통계는 제3장 제4절 제5항에 보고하였다. jamovi 원출력은 부록 3 <부표 3-3>에 제시하였다.
- 본문 주 치환: 부록 3 <부표 3-5>에 제시하였다. → 표 아래에 함께 제시하였다.
  - 해당 문단: 주: B·C의 n은 해당 척도 전 문항 응답자 수이며, 결측이 없어 제7절의 가설 검정 표본과 같다. 왜도와 첨도는 모든 척도와 도입·미도입 현장별 분석에서 절댓값 1.25 이하였다. 하위요인은 해당 영역 전 문항 응답 기준이다. jamovi 원출력은 표 아래에 함께 제시하였다.
- body_insert: jamovi 원출력(<표 4-10>). 현장 도입 여부 0=미도입·1=도입. 편집 폭에 맞추어 비례 축소하였다.
- body_insert: (가) 현장 도입 여부별
- body_insert: jamovi 원출력(<표 4-11>). jamovi의 t는 미도입(0)−도입(1) 기준이므로 평균 차이(도입−미도입)와 부호가 반대이다.
- body_insert: (가) 만 나이·건설현장 경력 독립표본 t검정
- 본문 주 치환: 부록 3 <부표 3-6>·<부표 3-7>에 제시하였다. → 표 아래에 함께 제시하였다.
  - 해당 문단: 주: 모든 특성에 결측이 없으며 분모는 도입 34명·미도입 39명이다. 현장당 1명이므로 개인 수와 현장 수는 같지만 각 특성의 측정 단위는 구분하였다. 효과크기는 도입·미도입 현장 간 분포 차이를 기술하는 진단값이며 교란 제거의 증명이 아니다. 연속 특성은 독립표본 t검정의 Cohen's d(합동 표준편차 기준 절댓값)이며 방향은 평균 차이 열로 읽는다. 범주형 특성은 현장 도입 여부×범주 교차표의 Cramér's V이며 부호가 없고, 도입·미도입 현장 간 분포 차이는 Fisher 정확검정으로 확인하였다. 비유의한 검정을 동질성 확보의 증거로 쓰지 않았다. 공통 관측범위는 도입·미도입 현장 관측범위의 교집합이다. jamovi 원출력은 표 아래에 함께 제시하였다.
- body_insert: jamovi 원출력(<표 4-12>). 각 변수와 현장 도입 여부의 교차표는 부록 3 <부표 3-1>에 제시하였다.
- body_insert: (가) 소속 χ² Tests (나) 소속 Nominal (다) 성별 χ² Tests (라) 성별 Nominal (마) 역할 χ² Tests (바) 역할 Nominal (사) 총공사비 χ² Tests (아) 총공사비 Nominal
- 본문 주 치환: 부록 3 <부표 3-8>에 제시하였다. → 부록 3 <부표 3-4>에 제시하였다.
  - 해당 문단: 주: 모든 분석은 도입 34명·미도입 39명이며 F의 자유도는 (1, 62)이다. 조정 평균의 기준은 <표 4-13>과 같다. Holm 보정은 다섯 하위요인의 집단 차이 검정을 하나의 검정군으로 적용하였으며 연구가설 (1-1)·(2-1)은 포함하지 않았다. 95% CI는 개별 비교의 비보정 구간이며 판정은 Holm 보정 p를 기준으로 하였다. jamovi 원출력은 부록 3 <부표 3-4>에 제시하였다.
- 본문 주 치환: 부록 3 <부표 3-9>에 제시하였다. → 부록 3 <부표 3-5>에 제시하였다.
  - 해당 문단: 주: n=73, 잔차 df=60이다. 상호작용 검정은 F(1, 60)=2.35, p=.131, 부분 η²=0.038이다. X 계수는 예산 제약성이 전체 평균일 때의 집단 차이이고, W_c 계수는 미도입 현장에서의 기울기이다. jamovi 원출력은 부록 3 <부표 3-5>에 제시하였다.
- appendix_import: 본 부록은 제4장 제6·7절 표의 근거가 된 jamovi 2.7.41 출력 가운데 한 쪽을 넘어 본문에 싣지 않은 표의 원출력을 옮긴 것이다. 한 쪽 이내의 원출력은 본문의 해당 표 아래에 함께 실었다. 각 표의 수치를 담은 하위 표만 원형 그대로 옮겼으며, 출력의 행과 수치는 편집하지 않았고 변수명은 분석 파일의 이름을 그대로 두었다. 모든 출력은 같은 배율로 실었다.
- appendix_caption: <부표 3-3> 측정도구의 탐색적 요인분석 jamovi 출력 → <부표 3-2> 측정도구의 탐색적 요인분석 jamovi 출력
- appendix_caption: <부표 3-4> 측정도구의 내적 일관성 검증 jamovi 출력 → <부표 3-3> 측정도구의 내적 일관성 검증 jamovi 출력
- appendix_caption: <부표 3-8> 하위요인별 공분산분석 jamovi 출력 → <부표 3-4> 하위요인별 공분산분석 jamovi 출력
- appendix_caption: <부표 3-9> 현장 도입 여부와 안전관리 예산 제약성의 상호작용 jamovi 출력 → <부표 3-5> 현장 도입 여부와 안전관리 예산 제약성의 상호작용 jamovi 출력
- toc_delete: <부표 3-2> 조사 대상의 만 나이와 건설현장 경력 기술통계 jamovi 출력136
- toc_rename: <부표 3-3> 측정도구의 탐색적 요인분석 jamovi 출력136 → <부표 3-2> 측정도구의 탐색적 요인분석 jamovi 출력136
- toc_rename: <부표 3-4> 측정도구의 내적 일관성 검증 jamovi 출력139 → <부표 3-3> 측정도구의 내적 일관성 검증 jamovi 출력139
- toc_delete: <부표 3-5> 안전관리 실효성과 안전관리 예산 제약성의 기술통계 jamovi 출력141
- toc_delete: <부표 3-6> 연속형 통제변수의 균형 진단 jamovi 출력142
- toc_delete: <부표 3-7> 범주형 통제변수의 균형 진단 jamovi 출력143
- toc_rename: <부표 3-8> 하위요인별 공분산분석 jamovi 출력144 → <부표 3-4> 하위요인별 공분산분석 jamovi 출력144
- toc_rename: <부표 3-9> 현장 도입 여부와 안전관리 예산 제약성의 상호작용 jamovi 출력148 → <부표 3-5> 현장 도입 여부와 안전관리 예산 제약성의 상호작용 jamovi 출력148

## 수동 재적용 필요 — 전문

- 없음 (0건).

이는 이전 1206 산출물의 서식 재확인 요구를 새로 해소했다는 뜻은 아니다. 이번 변경에서 기존 표/목차 전체 교체로 생긴 추가 서식 손실이 없다는 뜻이다.

## 단위 테스트

실행: `python -m unittest discover -s tools/hwpx_transfer/tests -p "test_*.py" -v`
환경: `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`; TEMP/TMP는 지정 staging. 본문 번호 없음·대상 불일치 거부·12개 그림·한 쪽 격자 설정 검증을 추가했고 기존 회귀를 포함해 47건 모두 통과했다.

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
test_body_grids_unnumbered_and_manifest_targeted (test_image_grid.ImageGridTests.test_body_grids_unnumbered_and_manifest_targeted) ... ok
test_parser_35_cells_five_captions (test_image_grid.ImageGridTests.test_parser_35_cells_five_captions) ... ok
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
Ran 47 tests in 5.317s

OK
```

## 무결성과 실제 그림 치수

```text
PASS: ZIP/XML/style refs; 53 images, unused 0; body grids 4/12 PNGs, appendix grids 5/35 PNGs; all current MD text; targeted notes and LOT; red/black markers; base SHA256
Main tables retained: 36; appendix grids retained: 5; main exact paragraphs: 650
```

- ZIP CRC·엔트리 중복 없음; XML/HPF 9개 파싱 성공, 총 ZIP 엔트리 66개.
- BinData 53 = 기존 본문 그림 6 + 본문 격자 그림 12 + 부록 격자 그림 35. manifest와 hc:img 참조 각 53개, 서로 일대일이며 미사용 0개.
- 기존 53개 이미지 payload는 모두 바이트 동일. 현행 manifest의 jamovi PNG 47개도 내용·중복 개수까지 일치.
- 스타일 참조 유효, pageBreak="CELL" 0건, 빨간 마커 25건·검정 숫자/양식 대괄호 102건 확인.
- 열폭 합·각 행 셀 폭 합·병합 점유 격자·칸별 이미지 비율 및 크기를 검사했다. 전체 폭은 기존 39684 HWPUNIT(약 140mm). 구조용 빈 Markdown 머리행은 인쇄하지 않는다.
- 아래 NONE/TABLE은 XML 나눔 설정이며 실제 한 쪽 배치 성공 증거가 아니다. 라벨 높이는 한양신명조 요청→GDI 굴림 대체 측정치로 추정하므로 PDF 확인이 필요하다.

| 위치 | 행 × 열 | 열폭 HWPUNIT | 전체 폭/각 행 합 | 나눔 |
|---|---:|---|---:|---|
| <표 4-7> 아래 번호 없는 격자 | 1 × 2 | [22790, 16894] | 39684 | NONE |
| <표 4-10> 아래 번호 없는 격자 | 1 × 1 | [39684] | 39684 | NONE |
| <표 4-11> 아래 번호 없는 격자 | 1 × 1 | [39684] | 39684 | NONE |
| <표 4-12> 아래 번호 없는 격자 | 4 × 2 | [24554, 15130] | 39684 | NONE |
| <부표 3-1> 조사 대상의 범주형 인구통계학적 특성 jamovi 출력 | 4 × 1 | [39684] | 39684 | TABLE |
| <부표 3-2> 측정도구의 탐색적 요인분석 jamovi 출력 | 6 × 2 | [22660, 17024] | 39684 | TABLE |
| <부표 3-3> 측정도구의 내적 일관성 검증 jamovi 출력 | 5 × 3 | [16545, 11569, 11570] | 39684 | TABLE |
| <부표 3-4> 하위요인별 공분산분석 jamovi 출력 | 10 × 1 | [39684] | 39684 | TABLE |
| <부표 3-5> 현장 도입 여부와 안전관리 예산 제약성의 상호작용 jamovi 출력 | 2 × 1 | [39684] | 39684 | TABLE |

| 그림 | 행·열 / colspan | 셀 폭 | 그림 폭 × 높이 mm |
|---|---|---:|---|
| 표4-7_01.png | 1행 1열 / 1 | 22790 | 73.2013 × 105.0006 |
| 표4-7_02.png | 1행 2열 / 1 | 16894 | 53.9996 × 57.0017 |
| 표4-10_01.png | 1행 1열 / 1 | 39684 | 139.9961 × 108.7118 |
| 표4-11_01.png | 1행 1열 / 1 | 39684 | 101.9985 × 40.0014 |
| 표4-12_01.png | 1행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 표4-12_02.png | 1행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 표4-12_03.png | 2행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 표4-12_04.png | 2행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 표4-12_05.png | 3행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 표4-12_06.png | 3행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 표4-12_07.png | 4행 1열 / 1 | 24554 | 60.9987 × 32.9988 |
| 표4-12_08.png | 4행 2열 / 1 | 15130 | 37.2004 × 27.0016 |
| 부표3-1_01.png | 1행 1열 / 1 | 39684 | 86.2011 × 59.1995 |
| 부표3-1_02.png | 2행 1열 / 1 | 39684 | 86.2011 × 59.1995 |
| 부표3-1_03.png | 3행 1열 / 1 | 39684 | 86.2011 × 72.1994 |
| 부표3-1_04.png | 4행 1열 / 1 | 39684 | 91.7997 × 85.1992 |
| 부표3-2_01.png | 1행 1열 / 2 | 39684 | 134.2 × 86.2011 |
| 부표3-2_02.png | 2행 1열 / 1 | 22660 | 76.1999 × 21.0008 |
| 부표3-2_03.png | 2행 2열 / 1 | 17024 | 36.9993 × 21.0008 |
| 부표3-2_04.png | 3행 1열 / 2 | 39684 | 51.7983 × 68.9997 |
| 부표3-2_05.png | 4행 1열 / 2 | 39684 | 134.2 × 62.2017 |
| 부표3-2_06.png | 5행 1열 / 1 | 22660 | 76.1999 × 21.0008 |
| 부표3-2_07.png | 5행 2열 / 1 | 17024 | 36.9993 × 21.0008 |
| 부표3-2_08.png | 6행 1열 / 2 | 39684 | 51.7983 × 45.0003 |
| 부표3-3_01.png | 1행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-3_02.png | 1행 2열 / 2 | 23139 | 63.2 × 69.2008 |
| 부표3-3_03.png | 2행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-3_04.png | 2행 2열 / 2 | 23139 | 63.4999 × 45.2013 |
| 부표3-3_05.png | 3행 1열 / 1 | 16545 | 50.2002 × 51.9994 |
| 부표3-3_06.png | 3행 2열 / 2 | 23139 | 50.2002 × 51.9994 |
| 부표3-3_07.png | 4행 1열 / 1 | 16545 | 50.2002 × 51.9994 |
| 부표3-3_08.png | 4행 2열 / 1 | 11569 | 34.8015 × 27.0016 |
| 부표3-3_09.png | 4행 3열 / 1 | 11570 | 34.8015 × 27.0016 |
| 부표3-3_10.png | 5행 1열 / 1 | 16545 | 34.8015 × 27.0016 |
| 부표3-3_11.png | 5행 2열 / 2 | 23139 | 34.8015 × 27.0016 |
| 부표3-4_01.png | 1행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-4_02.png | 2행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-4_03.png | 3행 1열 / 1 | 39684 | 116.801 × 70.0016 |
| 부표3-4_04.png | 4행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-4_05.png | 5행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-4_06.png | 6행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-4_07.png | 7행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-4_08.png | 8행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-4_09.png | 9행 1열 / 1 | 39684 | 118.2015 × 70.0016 |
| 부표3-4_10.png | 10행 1열 / 1 | 39684 | 82.2006 × 33.1999 |
| 부표3-5_01.png | 1행 1열 / 1 | 39684 | 130.1995 × 141.1991 |
| 부표3-5_02.png | 2행 1열 / 1 | 39684 | 128.0017 × 81.9995 |

## SHA256

- 기준본: `00. hwpx/261031_1206_경기공학_건축안전_윤혁_논문.hwpx`
- 작업 전: `d9ffcc9f26fd6c07d63a62f9df84ac388b72ca2330eeeccb450ed554f0e4e94e`
- 작업 후: `d9ffcc9f26fd6c07d63a62f9df84ac388b72ca2330eeeccb450ed554f0e4e94e`
- 원본·staging 복사본 일치: 예.
- 패치본: `b69ff600fcdafa2103ef5547e21b569f3440f40eab9971c93b60dfa8b0aa4b46`

## 메인이 이어서 할 일

1. 패치본을 한글에서 실제 Open·재조판 저장한다. COM과 HWPX MCP는 이번 작업에서 호출하지 않았다.
2. PDF에서 본문 격자 4개와 원래 표/주의 연결, 라벨/그림 줄바꿈, 표가 다음 쪽으로 밀리는 위치, 모든 표의 꼬리말 침범·행 연속성을 확인한다.
3. 재조판 결과로 점선 목차의 실제 인쇄 쪽수를 갱신하고 다시 저장·PDF 대조한다. 이번 파일의 목차 숫자는 1206 기준값이므로 아직 새 배치와 맞지 않을 수 있다.
4. 기준본에 이미 남아 있던 jamovi [3]·[4] 각주 처리 및 사용자 서식 검토는 메인 판단을 유지한다.

## 재현 명령

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
python tools/hwpx_transfer/md_to_blocks.py --out-dir tools/hwpx_transfer/staging/hwpx_261031b
python tools/hwpx_transfer/staging/hwpx_261031b/assemble.py
python tools/hwpx_transfer/staging/hwpx_261031b/patch.py
python tools/hwpx_transfer/staging/hwpx_261031b/verify.py
python tools/hwpx_transfer/staging/hwpx_261031b/make_report.py
```

기존 staging의 `base.hwpx`, 양식 비교용 `template.hwpx`, 선행 검증 references/transplant JSON을 입력으로 쓴다. 전체 조립본은 비교용이고 패치본만 메인에게 전달한다.
