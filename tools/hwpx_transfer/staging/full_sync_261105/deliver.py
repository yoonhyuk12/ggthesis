from pathlib import Path
import sys,json,re,html,zipfile,collections,hashlib,shutil
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p
O=Path(__file__).parent;stamp=sys.argv[1]
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
assert hashlib.sha256(Path(info['path']).read_bytes()).hexdigest()==info['sha256']
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in info['md_sha256'].items())
with zipfile.ZipFile(O/'final_current.hwpx') as z:u=p.Units(z.read('Contents/section1.xml').decode(),set())
expected=json.loads((O/'toc_completed.json').read_text(encoding='utf8'));want={k:([str(x) for x in v] if isinstance(v,list) else [str(v)]) for group in expected.values() for k,v in group.items()};used=collections.Counter();count=0
for v in u.items:
 if '<hp:tab' not in v['xml']:continue
 before,after=v['xml'].split('<hp:tab',1);title=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip();actual=re.search(r'/>([^<]*)</hp:t>',after)[1].strip();index=used[title];used[title]+=1
 assert actual==want[title][min(index,len(want[title])-1)],(title,actual)
 count+=1
assert count==119
dest=Path(f'00. hwpx/{stamp}_경기공학_건축안전_윤혁_논문.hwpx');assert not dest.exists();shutil.copy2(O/'final_current.hwpx',dest)
snap=Path('tools/hwpx_transfer/staging/hwpx_snapshots');snap.mkdir(exist_ok=True);shutil.copy2(dest,snap/dest.name)
h=hashlib.sha256(dest.read_bytes()).hexdigest()
report=f'''# MD 전체·그림 3-5·3-6 HWPX 반입 보고 ({stamp})

- 기준본: `{info['path']}`
- 산출물: `{dest.as_posix()}`
- 기준본 SHA256(시작·종료 불변): `{info['sha256']}`
- 산출물 SHA256: `{h}`
- 증거: `tools/hwpx_transfer/staging/full_sync_261105/`
- 역동기화용 동일 스냅샷: `tools/hwpx_transfer/staging/hwpx_snapshots/{dest.name}`
- MD·기준본·도구 본체·규칙·다른 계획은 수정하지 않았다. 브리프의 금지 범위에 따라 계획 색인도 수정하지 않았다. git 쓰기는 하지 않았다.

## 전체 반입과 사용자 서식 보존

md_to_blocks는 7파일 476블록, 커버리지 누락 0이었다. 조립에는 ch01~ch05·apx1을 사용하고 본문 미수록 apx2는 제외했다. 편집 메모·코드펜스 등의 명시적 제외는 parse_report.md에 기록돼 있다. 실제 본문 전체, 참고문헌, 설문 두 양식과 영문초록을 현행 MD 조립본과 텍스트·순서로 대조해 일치했다. 장·절·항·표·그림 113개 구성 항목도 일치했다. 제1~5장 중 바뀌지 않은 부분은 기준본을 유지했다.

최초 patch_from_fresh 통계는 equal 522, insert 2, replace_fresh 24, delete_kept 8, table_same_kept 3, manual 3이다. `--toc-from-fresh`는 표→그림 전환과 목차 항목 변경 때문에 사용했고, `--force-fresh`는 쓰지 않았다. 별도 resolution_audit.json에 후처리 내역을 기록했다.

- 그림 3-5는 기준본에 이미 있어 옛 C·D 표를 다시 삭제하지 않았다. 자동 정렬이 만든 중복 캡션 1개만 제거했다. 기준본의 남은 옛 표 3-11(A-7~A-9) 1개는 이번 지시에 따른 확정 삭제로 그림 3-6과 새 설명으로 교체했다.
- 자동 반입이 남긴 제4장 상호참조와 표 4-7 머리행을 현행 MD로 반영했다.
- 표 3-8·4-7·4-12·4-14는 기준본 셀을 직접 고쳐 열폭·병합·기존 서식을 유지했다. 표 4-15의 갱신은 조립본에서 반입됐으며 폭·격자는 기준본과 같다.
- 목차 전체 교체로 없어질 수 있는 기존 장평·자간은 동일 제목의 기준본 문단에서 복원했다. 새로 길어진 표 4-12·그림 3-6·그림 4-2 항목만 장평 75%, 자간 -4%로 한 줄에 맞췄다. 문구·글자 크기는 유지했다.
- 최초 수동 목록 3건(운영 특성 블록, 표 4-7 블록, 목차 서식)은 위 처리와 PDF 확인으로 해소했다. 별도 사용자 수동 재적용 잔여 목록은 없다.
- 기준본에만 남은 미확인 비어 있지 않은 문단은 없다. 자동 유지 항목의 실내용은 중복 캡션 및 명시적으로 교체하는 옛 표·관련 문단이었다. 빈 문단은 유지했다. 감사의 글 8문단과 설문 41문단은 최신 기준본에서 이식했으며 설문 내용은 MD와 별도로 대조해 누락 0건이었다.

## 입력 현행화와 그림

references_kjn_v3.json은 옛 분류·서지이므로 현행 07의 「참고문헌(현행 인용 목록)」에서 스크래치 references.json을 작성했다. 국내 20·국외 21·법령 4·표준/기술자료 3, 총 48건이며 분야별 번호를 독립 부여했다. Green & Swets, 이형도 및 법령 서지 변경을 반영했다. 편집용 메모 제거 내역은 reference_filter_audit.json에 있다. 원본 참고문헌 JSON은 수정하지 않았다.

김정년 양식은 git show로 스크래치에만 꺼냈으며 SHA256 `9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3`을 확인했다. 그 조립본은 비교 입력으로만 사용했다.

그림 매핑은 현재 MD에서 다시 만들었다. 그림 3-5·3-6은 조립본 그림을 반입/기준본 그림에 현행 PNG를 적용하고 그림 아래에 캡션을 배치했다. 가로 150mm(42,520 HWPUNIT), 높이 각각 27,778·32,316 HWPUNIT, 원본 비율·글자처럼 취급이다. 인쇄 쪽수는 그림 3-5 **50쪽**, 그림 3-6 **52쪽**이며 둘 다 그림·캡션이 같은 쪽에 있고 잘림이 없다. 이미지 전수 대조에서 그림 4-1·4-2도 현행 파일과 달라 MD PNG로 반영했다. 총 9개 이미지의 디코딩 픽셀이 현재 MD 원본과 일치한다. 한글 재저장 시 PNG 인코딩 바이트가 바뀌는 경우가 있어 해시만으로 그림 불일치를 판정하지 않았다.

## 검증

- 한글 COM Open=True → SaveAs(HWPX)=True → Reopen=True → SaveAs(PDF)=True. 최종 산출물은 한글 재조판 저장본이다.
- ZIP/XML 정상, strict check ok=true(오류·경고 0), validate.py VALID, extract_text XML 8개 문제 0.
- 기준본 표 51개 중 확정 삭제한 운영 특성 표 1개를 제외한 최종 50개(중첩 포함)의 전체 폭·셀 폭·주소·병합 격자 보존 확인. pageBreak=CELL 0.
- 빨간 마커 6종은 수록 조립본 기대 0·산출물 실제 0. 본문·표 셀 전체를 검사했으며 색 변경으로 지운 것이 아니다.
- PDF 113쪽. 표 괘선 검출 43쪽, 꼬리말 침범 0. 쪽번호 없는 물리 3쪽은 인준면이다. 본문·설문 전 표 페이지와 연속 페이지를 review_*.png로 렌더해 확인했으며 잘림·겹침·마지막 행 유실이 없다. 표 4-7의 확장된 검정명은 머리행에서 여러 줄로 표시되지만 셀 안에 전부 들어간다.
- 목차 총 119항목: 99개 쪽수 갱신, 20개 유지, 미매칭 0. 자동 추출이 줄 분리 때문에 못 찾는 논문개요·도입 설문·미도입 설문은 PDF에서 각각 ix·89·95쪽을 확인해 보완했다. 동일한 Part A/B 제목은 도입·미도입 순서대로 90/96, 92/98쪽을 각각 대응했다.
- 목차 갱신 후 PDF 113쪽 유지, 자동 재추출 매핑 동일, 실제 목차 숫자 119개 전부 확정 매핑과 일치. PDF 픽셀 변화는 목차인 물리 4~10쪽뿐이고 본문·그림·전 표는 직전 검증 PDF와 동일하다. 최종 목차 7쪽을 직접 확인해 항목별 한 줄·점선·우측 쪽수 배치가 정상이다.

## 실행 중 해결한 문제와 남은 사항

1. 병합 검증기가 MD `<br>`를 실제 셀 텍스트와 그대로 비교해 조립을 중단했다. 스크래치 래퍼에서 비교용 문자열의 `<br>`만 정규화했다. 기준본의 선언 병합은 이미 반영돼 있어 자동 재적용을 생략하고 실제 표 대조 및 셀 단위 갱신으로 보존했다. 도구 본체를 고치지 않았다.
2. 처음 XML 저장에서 인코딩 이름 `utf8`이 한글/ElementTree에서 거부되어 Open=False였다. XML 표준 선언 `utf-8`로 고친 뒤 무결성·COM·PDF 검증을 통과했다. 실패본은 산출물로 내지 않았다.
3. 목차 서식 복원 시 미완결 XML 조각용 텍스트 추출 방식이 맞지 않아 라벨 중복을 발견했다. 탭 앞 텍스트 전용 추출로 수정한 뒤 전체 제목·순서·쪽수 대조를 통과했다.

4. 배포 직전 해시 검사에서 작업 중 외부 제4장 MD 변경 1건을 발견했다: `jamovi 2.7.41(The jamovi project, 2026)` → `jamovi 2.7.41(2026)`. 초기 해시는 initial_base_info.json에 보존하고 해당 문단만 추가 반입했다. final_current.hwpx/PDF로 다시 한글 저장한 뒤 텍스트·구성·목차·PDF 변화를 확인했다. 작업자가 MD를 수정하지 않았다.

내용 미반입·미검증 산출물·수동 재적용 잔여는 없다. 원고 자체의 내용·주 위치·기존 표의 조밀한 폭은 이번 반입에서 임의로 윤문하거나 재설계하지 않았다. 향후 전체 조립에서도 현행 참고문헌·설문·이미지 매핑 및 `<br>` 병합 비교 처리가 필요하다.

주요 증거: patch_report.md, resolution_audit.json, references.json, reference_filter_audit.json, assembly_report.md, survey_audit.json, image_checks.json, verification.json, resaved2_tables.json, toc_completed.json, toc_final.json, final_pdf_check.json, concurrent_pdf_check.json, final_current.pdf, review_*.png, final_changed_*.png.
'''
rpath=Path(f'03.plan/{stamp}_MD전체_그림3-5_3-6_hwpx반입_코덱스보고.md');rpath.write_text(report,encoding='utf8')
result={'output':dest.as_posix(),'report':rpath.as_posix(),'sha256':h,'toc_verified':count};(O/'delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
