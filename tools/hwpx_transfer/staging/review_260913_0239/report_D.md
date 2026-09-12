# Surgical helper 구현 보고

작성 파일은 `surgical_ops.py`와 이 보고서뿐이다. HWPX 생성·변경, COM/MCP/rhwp, MD 원고·원자료·Git 쓰기, 추가 워커 및 외부검색은 수행하지 않았다. CLAUDE.md, 교수님 작성요령 전문, 표 배치·산출물 검증 규칙을 읽었다.

## API와 호출 계약

- `Surgical(base_path)`는 ZIP을 읽고 `.data`, `.roots`, `.paras`, `.tables`를 제공한다. section 키는 `Contents/section2.xml` 같은 ZIP 경로이며 p/tbl 인덱스는 원본 preorder(표셀 포함)이다.
- 한 이관 작업에서 **동일 인스턴스 하나**를 사용한다. 원본 트리의 문단/표는 변형하지 않고 bytes fragment를 반환하며, header의 색 스타일과 ID allocator만 메모리에서 누적한다.
- `edit_paragraph(section, idx, new_text, new=False)`는 문단 속성을 복제하고 SequenceMatcher의 동일 문자열 구간에 기존 문자스타일을 보존한다. 지정된 미완성 마커만 빨강, 마커 밖 기존 빨강은 검정으로 정규화하며 변경 문단 캐시를 제거한다. `new=True`는 고유 ID와 pageBreak/columnBreak=0이다.
- `table_fragment(section, table_idx, header, rows, weights, caption=None)`는 문자열 행렬을 받는다. 명시한 양수 weights는 상대 열폭이며 `None`이면 실제 글꼴 폭에 따라 자동 배분한다. 원본 전체 폭, 셀·문단 템플릿, 기본 글꼴/크기를 유지하고 새 격자를 구성한다. caption을 주면 첫 행 전체 병합, None이면 원본 캡션행도 제외한다. 단위 괄호는 머리셀의 별도 문단으로 분리한다(명, %, 점, 시간, 원, 단위: 등; 의미 설명 괄호는 무조건 분리하지 않음).
- `wrap_table(section, anchor_idx, table_xml, new=False)`는 해당 앵커가 직접 소유한 표 1개만 교체하고 앵커 캐시를 제거한다. 새 앵커는 p/tbl ID를 새로 부여한다. 다른 복합 컨트롤이 섞인 앵커는 오류이다.
- `header_bytes()`는 추가 charPr와 itemCnt를 반영한다. 파일 출력 함수 및 main은 없다. 호출자가 lexical 범위 치환 및 ZIP 쓰기를 담당하며, **표셀 단독 문단 변경 시 바깥 표 앵커 캐시 제거도 호출자가 담당**한다.
- 본문/표셀의 footnote·tab·field·그림 등 plain text 이외 컨트롤, 중첩 표 및 지원하지 않는 표 메타데이터는 명시적 ValueError로 중단한다. 사용자 직접 수정 텍스트와 반영 대상 결정은 메인 명세의 책임이다.

## 측정과 한계

실제 `C:/Windows/Fonts/H2MJSM.TTF`를 찾아 Pillow `HYSinMyeongJo-Medium Regular`로 측정했다. 이번 환경에서는 대체 글꼴을 사용하지 않았다. 다른 환경에서 못 찾으면 Batang 대체, 그것도 불가능하면 em 추정으로 전환하며 `.font_measurement`와 `.estimates`에 명시한다. 원문 charPr는 변경하지 않으므로 글꼴 파일 경로는 측정에만 사용된다.

글리프 폭·charPr 크기/장평/자간·셀 여백·문단 줄간격/앞뒤 간격에 10% 여유를 적용한다. 정확한 한글 조판 엔진이 아니므로 혼합 글꼴, 문단 들여쓰기, 줄 단위 단어묶음, 현재 쪽 잔여 높이는 완전 재현하지 않는다. 새 쪽 가용 높이에서 2,000 HWPUNIT 여유를 두고 NONE/treatAsChar=1 또는 TABLE/repeatHeader=1/treatAsChar=0을 **추정 선택**한다. 반복 캡션과 머리셀 모두 header=1, 본문 셀은 0이다. 한 행 또는 반복 머리영역+본문 한 행이 새 쪽에 못 들어갈 추정이면 오류를 낸다.

## 메모리 검증 증거

`python -B -`로 모듈을 불러 실제 base ZIP을 읽고 XML fragments만 메모리에서 생성했다. 최초 lxml attrib.update 키워드 사용 오류를 수정한 뒤 다음을 통과했다.

- 본문/표셀 각 문자별 미완성 마커 빨강, 참조번호·신뢰구간 검정, 10pt 유지, 신규 p/tbl ID 중복 없음.
- 전체 폭 39,142 유지: 3열 `[7829, 7828, 23485]`, 2열 `[7828, 31314]`; 모든 행 폭 합 정확, 병합 포함 점유 격자 빈칸·겹침 없음.
- 빈도(명)와 비율(%)의 별도 단위 문단, caption=None 행 제거, 긴 표의 캡션+머리행 반복 플래그.
- 짧은 표 추정 10,044/54,144 → NONE, 40행 긴 표 157,382/54,144 → TABLE; 자동 열폭 긴 설명 열 36,447 > 번호 열 2,695.
- 변경 셀/앵커 linesegarray 제거, 복합 본문 거부, 메모리에 주입한 셀 footNote 거부, header itemCnt 일치.
- base SHA256 전후 동일: `0f09c55022193a3260b88da65f273163cf6e6be77b44e641fed51e66f56f4b12`.

메인은 실제 변경 명세로 helper를 호출하고 부분 ZIP 치환 후 한글 개방·재조판 저장·전 표 PDF 및 목차 인쇄 쪽수 검증을 수행해야 한다. 이 보고서는 helper 검증이며 최종 HWPX 조판 완료 판정이 아니다.
