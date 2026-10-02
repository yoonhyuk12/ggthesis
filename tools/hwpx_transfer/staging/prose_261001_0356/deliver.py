from pathlib import Path
import hashlib
import json
import shutil

q = Path(__file__).parent
manifest = json.loads((q / 'source.json').read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = Path(manifest['source'])
output = Path(manifest['output'])
pdf = output.with_suffix('.pdf')
assert digest(source) == manifest['sha256']
assert digest(output) == manifest['sha256'], 'Reserved output has changed'
assert not pdf.exists(), 'PDF already exists'
qa = json.loads((q / 'qa_report.json').read_text(encoding='utf-8'))
toc = json.loads((q / 'qa_toc_final.json').read_text(encoding='utf-8'))
visual = json.loads((q / 'visual_final_equivalence.json').read_text(encoding='utf-8'))
assert qa['machine_checks_pass']
assert not toc['recommended_changes'] and not toc['unresolved']
assert visual['same_body_image_pages'] == 148
shutil.copy2(q / 'final150.hwpx', output)
shutil.copy2(q / 'final150.pdf', pdf)
assert digest(output) == digest(q / 'final150.hwpx')
assert digest(pdf) == digest(q / 'final150.pdf')
assert digest(source) == manifest['sha256']
result = {
    'status': 'complete', 'final_approval': True,
    'source_unchanged': True, 'source_sha256': manifest['sha256'],
    'outputs': [{'path': p.as_posix(), 'sha256': digest(p)} for p in [output, pdf]],
    'md_paragraphs': 164, 'hwpx_paragraphs': 165, 'pages': 150,
    'tables_including_nested': 62, 'red_markers': 681, 'figures': 6,
    'toc_items': 120, 'toc_mismatches': 0,
    'com': 'Open, SaveAs HWPX, reopen and SaveAs PDF succeeded for final150',
    'layout': 'Section2 paragraph408 spacing 0 to -1; font size unchanged; orphan line resolved',
    'toc_final_change': 'Section1 paragraph5 purpose heading page3 to page2',
    'visual_evidence': ['visual_A_report.json', 'visual_B_report.json', 'visual_final_equivalence.json'],
    'final_visual': '148 body page images identical to reviewed output; final pages4 and45 reviewed separately by main',
    'limitations': 'PDF cell localization heuristics are not exhaustive; combined with all-page visual review. Preexisting printed Markdown link and sparse bibliography heading retained. No CopyKiller retest.'
}
(q / 'completion.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
plan = next(Path('03.plan').glob('261001_0358_*'))
content = plan.read_text(encoding='utf-8')
content = content.replace('- 산출 예정:', '- 산출물:')
content = content.replace('- 현재 상태: 사본 생성 및 현행 HWPX 덤프 완료, 문장 매핑·검증 도구 준비 중.', '- 현재 상태: 완료. MD 수정 164문단을 HWPX 165문단에 반영했으며 누락·충돌은 없다.')
content += '''
## 완료 결과

- 한글 COM 개방·재조판 저장·재개방·PDF 출력을 완료했다. 최종본은 150쪽이며 기준 원본 해시는 변하지 않았다.
- 표 62개(중첩 포함)의 내용·격자·폭, 그림 6개, 빨간 마커 681개를 보존했다. 초기 부분 치환 검증 8항목과 최종 기계 검증을 통과했다.
- 제2장 끝 한 줄이 별도 쪽으로 밀려 해당 문단만 자간을 0에서 -1로 조정했다. 글꼴 크기와 본문 내용은 유지했다.
- 최종 목차 120항목의 불일치는 0건이다. 기준본 대비 최종 목차 수정은 ‘제2절 연구의 목적’의 3→2 한 건이다. 중간 151쪽 출력의 목차 수정 이력은 최종본에 적용되지 않는다.
- 작업자들이 전체 페이지를 육안 검토했다. 최종본의 148쪽은 검토본과 본문 이미지가 같고, 달라진 목차 1쪽과 제2장 끝 1쪽은 메인이 별도 확인했다. PDF 텍스트의 표 셀 위치 매칭 한계는 전체 페이지 육안 검토로 보완했다.
- 기존 Markdown 링크 표기와 빈 관련 법령 제목 등 요청 범위 밖의 기존 상태는 보존했다. 카피킬러 재검사는 수행하지 않았다.
- 결과·해시·검증 근거: `tools/hwpx_transfer/staging/prose_261001_0356/completion.json`. 최종 검증 대상은 `final150.hwpx` 및 `final150.pdf`이며 결과 폴더 복사본과 해시가 같다.
'''
plan.write_text(content, encoding='utf-8')
index = Path('03.plan/README.md')
lines = index.read_text(encoding='utf-8').splitlines()
for i, line in enumerate(lines):
    if '261001_0358_' in line:
        lines[i] = line.replace('진행 중', '완료·150쪽·한글/PDF 검증')
    elif '260930_2333_' in line:
        lines[i] = line.replace('HWPX/재검사 미실시', 'HWPX 후속 반영 완료(261001_0358)·재검사 미실시')
index.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
