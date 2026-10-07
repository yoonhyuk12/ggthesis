# 참고문헌 김정년 양식 7분류 초안

입력 references.json의 항목을 보존한 분류·연도 위치 변환본이며 최신 확정 서지 목록을 대신하지 않는다. 현행 07 목록은 입력 노후화 확인 용도로만 읽었고 저자·제목·게재지·권호·쪽·URL·flagged 사유를 고치지 않았다.

| 분류 | 개수 |
|---|---:|
| 가. 학위논문 | 8 |
| 나. 학술지 | 0 |
| 다. 보고서 | 2 |
| 라. 관련법 | 0 |
| 마. 기타 | 3 |
| 바. 국외 단행본 | 2 |
| 사. 국외 학술지 | 5 |
| flagged (7분류 외 보존) | 31 |

항목 총수: 51개. ambiguous는 기존 항목에 대한 판단 메모이며 별도 항목으로 중복 합산하지 않는다.

## 연도 변환과 불변 검사

원문의 쉼표+공백+YYYY를 제거한 문자열과 변환본의 저자 뒤 괄호 연도를 제거한 문자열을 문자 단위로 비교한다. 따라서 연도 이동에 수반되는 쉼표/괄호 외의 글자와 문장부호도 보존한다. flagged는 text와 reason을 포함한 객체 전체를 그대로 보존한다.

## 분류 판단이 필요한 항목

| 원문 | 후보 분류 | 이유 |
|---|---|---|
| 한국산업안전보건공단, 『스마트 안전장비 활용 가이드라인』, 한국산업안전보건공단, 2024. | 다. 보고서 / 마. 기타 | 기관 가이드라인: 독립 보고서/기술자료 구분은 양식 적용 판단 필요; 원래 보고서 분류를 잠정 유지 |
| The jamovi project, jamovi (Version 2.7) [Computer Software], 2026. https://www.jamovi.org | 마. 기타 | 소프트웨어/웹자료 전용 분류가 없어 기타 잠정 배치 |
| Wu, J., Wu, S., Ma, Y., Yu, G., Xu, H., Zheng, L., & Duan, J., "MonitorVLM: A Vision–Language Framework for Safety Violation Detection in Mining Operations", arXiv:2510.03666, 2025. | 마. 기타 / 사. 국외 학술지 | 프리프린트이며 정식 학술지 게재 여부를 입력만으로 확정할 수 없어 기타 유지 |
| Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., & Tabkhi, H., "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078, 2023. | 마. 기타 / 사. 국외 학술지 | 프리프린트이며 정식 학술지 게재 여부를 입력만으로 확정할 수 없어 기타 유지 |
| 기사·웹자료 — 김포신문(2021)·연합뉴스(2024) 등 (ref 37) | 마. 기타 / 다. 보고서 | 개별 자료의 매체·일자·제목·URL이 미확정; flagged 유지 |

## 입력 서지의 현행 목록과의 불일치

- {"source_ref": "#04", "input": "김윤헌", "current_07": "김태헌", "evidence": "01.docs/07_참조번호목록.md:109,221,261", "action": "서지 불변 지시에 따라 입력 문자열 보존; 최신 서지로 채택하기 전 별도 승인 필요"}
- {"source_ref": "#36", "input": "한국산업안전보건공단", "current_07": "국토교통부·국토안전관리원", "evidence": "01.docs/07_참조번호목록.md:59,119,257", "action": "서지 불변 지시에 따라 입력 문자열 보존"}
- {"source_ref": "meta", "input": "01.docs/07_참조번호목록.md (단일 기준, 2026-07-25 판독)", "action": "입력은 2026-07-25 판독 기준이며 최신 확정 서지 전체를 반영하지 않는다; flagged 해소·중복 통합·항목 보강 금지"}

## 분류별 변환 목록

### 가. 학위논문

1. 김윤헌(2026), 「건설현장 위험상황 이해 및 대응을 위한 인공지능 안전인지 프레임워크 연구」, 성균관대학교 일반대학원 글로벌스마트시티융합전공 박사학위논문.
2. 김현수(2026), 「통합관제센터 운영을 위한 Vision AI–VLM 비교 및 하이브리드 연구」, 중앙대학교 대학원 ICT안전학과 석사학위논문.
3. 박종학(2025), 「YOLO(You Only Look Once) 모델별 건설 현장 위험 상태 및 객체 인식 성능 비교」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문.
4. 왕인국(2025), 「건설현장 위험요인 식별을 위한 RAG와 Fine-tuning 기반 LLM 성능향상에 관한 연구」, 광운대학교 대학원 석사학위논문.
5. 윤영석(2025), 「중·소규모 건설현장 안전관리자 인건비 직접공사비 계상과 안전관리 작동성에 관한 연구」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문.
6. 이동건(2024), 「통합기술수용모델(UTAUT)을 활용한 건설근로자들의 스마트안전장비 수용에 영향을 미치는 요인에 관한 연구」, 인하대학교 공학대학원 건축토목공간정보공학과 석사학위논문.
7. 이준호(2024), 「건설현장 중대재해 감소를 위한 스마트 안전장비의 지원방법 개선에 관한 연구」, 한양대학교 융합산업대학원 석사학위논문.
8. 황병복(2026), 「철도 건설사업에서 스마트 건설기술의 도입 및 활용이 안전 성과에 미치는 영향」, 우송대학교 일반대학원 철도공학과 박사학위논문.
### 나. 학술지

### 다. 보고서

1. 고용노동부(2024), 『2024 산업재해 현황분석』, 고용노동부.
2. 한국산업안전보건공단(2024), 『스마트 안전장비 활용 가이드라인』, 한국산업안전보건공단.
### 라. 관련법

### 마. 기타

1. The jamovi project(2026), jamovi (Version 2.7) [Computer Software]. https://www.jamovi.org
2. Wu, J., Wu, S., Ma, Y., Yu, G., Xu, H., Zheng, L., & Duan, J.(2025), "MonitorVLM: A Vision–Language Framework for Safety Violation Detection in Mining Operations", arXiv:2510.03666.
3. Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., & Tabkhi, H.(2023), "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078.
### 바. 국외 단행본

1. Aiken, L. S., & West, S. G.(1991), Multiple Regression: Testing and Interpreting Interactions, Sage.
2. Shadish, W. R., Cook, T. D., & Campbell, D. T.(2002), Experimental and Quasi-Experimental Designs for Generalized Causal Inference, Houghton Mifflin.
### 사. 국외 학술지

1. Cvach, M.(2012), "Monitor alarm fatigue: An integrative review", Biomedical Instrumentation & Technology, Vol. 46, No. 4, pp. 268-277.
2. Davis, F. D.(1989), "Perceived usefulness, perceived ease of use, and user acceptance of information technology", MIS Quarterly, Vol. 13, No. 3, pp. 319-340.
3. Lawshe, C. H.(1975), "A quantitative approach to content validity", Personnel Psychology, Vol. 28, No. 4, pp. 563-575.
4. Pisu, A., Elia, N., Pompianu, L., Barchi, F., Acquaviva, A., & Carta, S.(2024), "Enhancing workplace safety: A flexible approach for personal protective equipment monitoring", Expert Systems with Applications, Vol. 238, 122285.
5. Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., & Podsakoff, N. P.(2003), "Common method biases in behavioral research: A critical review of the literature and recommended remedies", Journal of Applied Psychology, Vol. 88, No. 5, pp. 879-903.

## flagged 보존

- 노희상·박종용·정상윤, 「건설산업 ESG 안전·보건 정책과 건설안전 성과와의 관계 연구」, 『안전문화연구』(ISSN 2586-2685) — 발간호·연도가 게재 확정 교정본에 미기재 — 07목록에 [발간정보 확정 필요]로 명시(ref 45 등재 예정). 권(호)·연도·쪽 결손.
- 류수영, 「CCTV 기반 산업안전 관제 시스템에 관한 연구」, 2023 — 학위수여기관·대학원·학위구분 미확정 — 골격에 [학위 정보 확정 필요]로 명시.
- 이석희·고대식·송석일, 「건설 안전 모니터링을 위한 장면그래프와 템플릿 기반 실시간 비디오 캡셔닝 시스템 구현」, 『Journal of KIIT』, 제23권 제11호, 2025 — 저자·연도·게재지는 01장 각주 기준 확정이나 게재 쪽수 미기재(골격에 권호까지만 있음). 02장 CITE_TODO ⚠도 미해소.
- An et al. (2025), An Integrated YOLO and LLM … — 논문 제목 전문·저널명·권호·쪽 미확정 — 골격에 [저널·권호 확정 필요]로 명시.
- Zhou et al. (2023), Analysis of factors of willingness … — 논문 제목 전문·저널명·권호·쪽 미확정 — 골격에 [저널·권호 확정 필요]로 명시.
- Chong et al. (2023), The Adoption Intentions of Wearable Technology for Construction Safety — 저널명·권호·쪽 미확정 — 골격에 [저널·권호 확정 필요]로 명시.
- 이병길, 스마트장비(Drone·AIoT)를 활용한 … (ref 06) — 연도 미확정(02장 CITE_TODO vs 03장 '이병길(2024)' 상충). ref 18과 동일 연구의 이본 여부도 미확인. 제목 전문·게재처·학위정보 결손.
- 스마트장비(Drone·AIoT)를 활용한 건설현장 안전 관리 활성화 방안에 관한 연구 (ref 18) — 저자·연도 미확인. ref 06과 저자·내용 중복 가능성(별개 문헌 여부 미확인).
- Deep Learning-Based Safety Analysis for High-Altitude Construction Workers PPE Detection and Posture Recognition Model Development (ref 19) — 저자·연도 미확인(02장 CITE_TODO 상태). 게재처·권호·쪽 일체 결손.
- 중소규모 건설현장 재해예방을 위한 스마트 건설안전기술 활용 방안 (ref 22) — 저자·연도 미확인(02장 CITE_TODO 4회). 게재처 결손.
- 국내 소규모 민간 건설프로젝트의 산업안전보건관리비 준수 실태 분석 및 개선방안 제시연구 (ref 28) — 저자·연도 미확인 — '오세욱 외(2022)' 후보만 있고 원문 대조 미완. 게재처 결손.
- 건설현장의 스마트 안전장비 성능과 도입 효과 분석 (ref 32) — 저자·연도 미확인(02장 CITE_TODO 상태). 게재처 결손.
- 기사·웹자료 — 김포신문(2021)·연합뉴스(2024) 등 (ref 37) — 개별 기사의 매체·일자·기사 제목·URL 서지 미확정. ref 37 수록 자료와 02장 인용의 대응 여부도 미확인. '기타 자료' 소절 분리 수록 여부 지도교수 협의 대기.
- 객체 감지 기술을 활용한 반도체 건설 현장의 작업자 사고 예방 기술 연구 (ref 20) — Ⅲ장 인용은 있으나 07목록에 저자·연도·게재처 확정 기록이 전무.
- 서울시 재난안전관리 지원 생성형 AI 구축과 활용 방안 (ref 33) — Ⅲ장 인용은 있으나 07목록에 저자(발행처)·연도 확정 기록이 전무.
- 정보기술수용이론(TAM)의 대안적 모델의 개발에 관한 연구 (ref 43) — Ⅲ장 인용은 있으나 07목록에 저자·연도·게재처 확정 기록이 전무.
- 「산업안전보건법」 — 인용 조항·시행 기준일 미확정 — 골격에 [확정 필요] 명시. 최신 조문 확인(mark-unverified 규칙) 후 '라. 관련법'에 등재해야 함.
- 「건설기술 진흥법」 — 인용 조항·시행 기준일 미확정 — 골격에 [확정 필요] 명시. '라. 관련법' 후보.
- 「건설산업기본법」 — 인용 조항·시행 기준일 미확정 — 골격에 [확정 필요] 명시. '라. 관련법' 후보.
- 「중대재해 처벌 등에 관한 법률」 — 인용 조항 미확정 — 골격에 [확정 필요: 인용 조항] 명시. 시행일·법률번호는 ref 58 원문 대조(2026-08-25) 완료. '라. 관련법' 후보.
- EFA 적용 기준(KMO·Bartlett) 근거 문헌 — 인용할 문헌 자체가 미확정([확정 필요 — 미검증]). 저자·연도·서지 일체 없음.
- Cronbach's α 기준(.70) 근거 문헌 — Nunnally 후보만 있고 미검증([확정 필요 — 미검증]). 연도·판·쪽 일체 미확정.
- 요인적재값 기준(.50/교차적재 .40) 근거 문헌 — 인용할 문헌 자체가 미확정([확정 필요 — 미검증]).
- 다중공선성 진단 기준(상관계수·VIF) 근거 문헌 — 인용할 문헌 자체가 미확정([확정 필요 — 미검증]).
- Green & Swets (1966) — 신호감지이론(SDT) 원전 — 02장 내주로 인용됐으나 원전 서지(제목·출판사) 미확보, 참조번호 미부여 — 존재 검증 후 46~ 부여 예정.
- Dixon, Wickens & McCarley (2007) — 오경보/미탐 비대칭 효과 — 02장 내주로 인용됐으나 원전 서지(저널·권호·쪽) 미확보, 참조번호 미부여.
- Igbaria & Tan (1997) — IT 수용과 개인 수행도 — 02장 내주로 인용됐으나 원전 서지 미확보, 참조번호 미부여.
- Radjou, Prabhu & Ahuja (2012) — Jugaad/절약형 혁신 — 02장 내주로 인용됐으나 원전 서지 미확보, 참조번호 미부여.
- Zeschky, Widenmayer & Gassmann (2011) — 절약형 혁신 정의 — 02장 내주로 인용됐으나 원전 서지 미확보, 참조번호 미부여.
- Bhatti (2012) — 절약형 혁신 개념화 — 02장 내주로 인용됐으나 원전 서지 미확보, 참조번호 미부여.
- Tiwari & Herstatt (2012) — 절약형 엔지니어링 — 02장 내주로 인용됐으나 원전 서지 미확보, 참조번호 미부여.

## 검증 출력

- JSON_LOAD PASS: hwpx_only.json, images.json, references_kjn.json
- ACK PASS: section1 [127,151], 25 paragraphs (including blanks), original text exact
- PART_A PASS: section2 idx647,684; 2 boxes, each 2 nested tables; original text exact
- CANDIDATES: 18 table/body mismatches; 9 assembly differences excluded; 1 high-similarity word-order review; MD-only 527 rows
- IMAGES PASS: old_images=6, mapping=6, extracted_png=6, unmatched=0; hashes/bytes/dimensions verified
- REFERENCES PASS: 20 categorized + 31 flagged = 51 source items; 20/20 exact bibliographic invariance after year-token removal; flagged objects exact
- CATEGORIES: 가8 나0 다2 라0 마3 바2 사5; ambiguous=5
- ACCESS: HWPX ZIP read restricted to BinData/image1..6.png; no XML/MCP/COM/git/web/pip; current MD read only for caption inventory and permitted 07 bibliographic warning check
