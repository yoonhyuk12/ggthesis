from pathlib import Path
import json,re,zipfile,hashlib,datetime,shutil
from zoneinfo import ZoneInfo
O=Path('tools/hwpx_transfer/staging/full_sync_261104');now=datetime.datetime.now(ZoneInfo('Asia/Seoul'));stamp=now.strftime('%y%m%d_%H%M')
source=O/'final.hwpx';dest=Path(f'00. hwpx/{stamp}_경기공학_건축안전_윤혁_논문.hwpx');assert not dest.exists();shutil.copy2(source,dest)
info=json.loads((O/'base_info.json').read_text(encoding='utf8'));h=hashlib.sha256(dest.read_bytes()).hexdigest()
# Verify every actual TOC number against completed map, consuming repeated labels in order.
import sys,html,collections
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p
with zipfile.ZipFile(dest) as z:s=z.read('Contents/section1.xml').decode()
expected=json.loads((O/'toc_completed.json').read_text(encoding='utf8'));want={k:([str(x) for x in v] if isinstance(v,list) else [str(v)]) for group in expected.values() for k,v in group.items()};used=collections.Counter();count=0
for v in p.Units(s,set()).items:
 if '<hp:tab' not in v['xml']:continue
 before,after=v['xml'].split('<hp:tab',1);title=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip();actual=re.search(r'/>([^<]*)</hp:t>',after)[1].strip();index=used[title];used[title]+=1;assert actual==want[title][min(index,len(want[title])-1)],(title,actual);count+=1
assert count==119
report=f'''# MD 전체 HWPX 반입 보고 ({stamp})

- 기준본: `{info['path']}`
- 산출물: `{dest.as_posix()}`
- 증거 폴더: `{O.as_posix()}/`
- 기준본 SHA256(시작·종료 불변): `{info['sha256']}`
- 산출물 SHA256: `{h}`
- MD·기존 HWPX·도구 본체·규칙·다른 계획 파일은 수정하지 않았다. 브리프의 금지 범위에 따라 계획 색인도 수정하지 않았다.

## 반입 범위와 결과

현행 제1~5장·국문초록·영문초록·감사의 글·참고문헌·설문 두 양식과 구성·순서를 전수 대조하였다. 단순 지정 문구만 반입한 결과가 아니다. MD에서 수록 제외된 근거 대조표·실증 상세 결과·jamovi 원출력 부록은 최종본에 없다. 기존 기준본에 이미 반영된 변경은 유지하였다.

- md_to_blocks: 총 504블록, 7개 파일 커버리지 누락 0. 실제 조립은 ch01~ch05·apx1만 사용하고 apx2는 미수록 규칙에 따라 제외. 편집 메모·내부 관리용 섹션 등은 파서 보고의 명시적 제외 대상이며 누락이 아니다.
- patch_from_fresh: equal 560, replace_fresh 14, insert 0, delete_kept 1(빈 문단), table_same_kept 3, manual 0. 기존 병합을 가진 같은 내용 표 3개도 기준본 유지. MD 선언 병합 7개는 기준본 서식을 보존하여 적용했다.
- 실질 변경: 제4장 가설 띄어쓰기 3문단·소속/역할 통제 근거 1문단·요인분석 해석 1문단·제5장 8문단·산업안전보건법 서지 1문단. 목차 제목 2곳과 쪽수 10곳 추가 갱신.
- `--force-fresh`·`--toc-from-fresh` 불사용. 수동 재적용 필요 목록 없음. 변경된 절 제목의 기존 서식과 앞 빈 줄을 별도 보존했다.

## 입력 현행화와 실행 중 문제

1. 지정된 references_kjn_v3.json은 2026-10-08의 옛 7분류·미확정 서지 입력이었다. 현행 07의 참고문헌 절에서 스크래치 references.json을 만들었다. 국내 20·국외 21·법령 4·표준/기술자료 3 = 48건, 분류별 독립 연속 번호, 빈 번호·중복 0. 류수영 2024·jamovi 2026, Igbaria & Tan·조도빈 제외를 반영했다. 편집 메모 제거 이력은 reference_filter_audit.json에 남겼고 원본 JSON은 수정하지 않았다.
2. 기존 transplant.json은 261004의 옛 설문·감사의 글을 가리킨다. 이를 그대로 쓰면 삭제된 설문이 복원되므로 스크래치 설정에서 최신 기준본의 감사의 글 8문단·설문 64문단을 이식했다. 설문은 별도로 apx1의 본문 문구·문항과 대조해 누락 0건, B 문항 2회·C/D 문항 1회 수록을 확인했다.
3. 그림 매핑도 현행 MD 이미지 경로로 스크래치에서 생성했다. 그림 7개 모두 실제 HWPX BinData와 MD 참조 파일 SHA256이 일치한다. 과거 비교 입력의 없어진 그림 경로로 최초 조립이 중단되었고, 현재 MD를 읽어 해결했다.
4. patch_from_fresh가 01.docs의 작업 메모 08 파일까지 읽어 중복 `<표4-6>` 선언 오류로 중단했다. 도구 본체와 MD는 수정하지 않고 스크래치 실행 래퍼에서 선언 탐색을 실제 제1~5장으로 제한했다. 이후 정상 완료했다.
5. 김정년 양식은 git show의 바이너리 출력을 스크래치로만 추출했다. SHA256 `9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3` 확인. 조립본은 비교 입력으로만 사용했다.

## 검증 증거

- 한글 COM Open=True → SaveAs(HWPX)=True → Reopen=True → SaveAs(PDF)=True, 최초 재조판·목차 갱신 뒤 재조판 모두 성공. 최종 산출물은 한글 재저장본이다.
- ZIP/XML 정상, fill_hwpx strict ok=true(오류·경고 0), validate.py VALID, extract_text XML 8개·문제 0.
- 기준본·MD SHA256 불변. 전체 표 52개(중첩 포함)의 전체 폭·셀 폭·주소·병합 격자 동일. BinData 바이트 전부 보존, pageBreak=CELL 0.
- 본문부터 참고문헌·설문·영문초록까지 section2 비어 있지 않은 전체 문단 텍스트와 순서가 현재 MD 조립본과 일치(공백 정규화, 병합 표 표현 포함). section1의 목차 제목·감사의 글·국문초록도 쪽수 제외하고 일치. 장·절·항 및 표·그림 캡션 순서 대조 113항목 일치.
- 빨간 마커 6종은 수록 대상 조립본 기대 0·최종 실제 0. 삭제나 검은색 전환으로 사라진 것이 아니라 현재 MD 수록 본문에 마커가 없다. 미수록 편집 메모는 대상에서 제외했다.

## 전 표 PDF와 목차

- 123→122쪽. 제5장 윤문으로 결론 분량이 줄어 참고문헌·부록·Abstract가 1쪽 당겨졌다.
- 표 괘선 46쪽 자동 검사: 꼬리말 침범 0, 쪽번호 없는 물리 3쪽은 인준면 서명선이다.
- 기준본 검증 PDF와 본문 영역 픽셀 전수 대조: 113쪽 동일(쪽 이동 포함), 변화 9쪽은 물리 5·7·67·69·85·98·99·100·106쪽. 변화 페이지를 이미지로 직접 확인했으며 잘림·겹침 없음. 변화 표가 있는 물리 67쪽의 표 4-2 셀 끝·하단·후속 배치 정상. 나머지 표 쪽은 선행 작업의 전수 이미지 검증과 픽셀 동일하여 증거 승계.
- 목차 119항목 중 10항목 쪽수 갱신, 109항목 유지, 미매칭 0. 자동 추출이 못 찾는 논문개요·도입/미도입 설문 시작은 PDF 분리 텍스트와 인쇄 쪽수 viii·95·103으로 확인해 보충했다.
- 최종 재조판 뒤 PDF 전체 122쪽 유지, 추출 매핑 동일. 최종 HWPX의 목차 숫자 119개가 확정 매핑과 전부 일치. 목차 수정 후 픽셀 변화는 물리 6쪽뿐이며, 직접 이미지 확인해 한 줄·점선·우측 쪽수 정상. 본문과 전 표의 최종 PDF는 이전 검증 PDF와 동일하다.

## 남은 문제

내용 미반입·수동 재적용·미검증 산출물 없음. 조립 입력의 옛 참고문헌/설문 설정과 작업 메모 중복 선언 문제는 이번 스크래치에서만 우회했으며, 도구 본체를 고치지는 않았다. 향후 전체 조립에서도 같은 현행화가 필요하다.

증거: patch_report.md, assembly_report.md, reference_filter_audit.json, survey_audit.json, image_checks.json, verification.json, pdf_comparison.json, final_pdf_check.json, toc_completed.json, final.pdf 및 페이지 이미지.
'''
rpath=Path(f'03.plan/{stamp}_MD전체_hwpx반입_코덱스보고.md');rpath.write_text(report,encoding='utf8');(O/'delivery.json').write_text(json.dumps({'output':dest.as_posix(),'report':rpath.as_posix(),'sha256':h,'toc_verified':count},ensure_ascii=False,indent=2),encoding='utf8');print((O/'delivery.json').read_text(encoding='utf8'))
