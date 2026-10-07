# 현행 골격 기반 참고문헌 7분류 재생성

단일 입력은 01.docs/07_참조번호목록.md의 참고문헌 표기 골격 절이다. 전체 목록·대응표·이력 절은 사용하지 않았다. 원문의 주석·ref 번호·DOI·URL·미확정 마커를 전부 보존했으므로 조립 전에 이를 임의로 줄이지 않는다.

## 분류 및 순서 규칙

- 박사/석사/Doctoral dissertation → 가; 영문 저자 Mi도 국내 대학 학위논문이라는 골격 설명을 따라 가에 수록.
- 국내 학술지명·권호·쪽 표기 → 나; 기관 보고서·가이드라인·벤더 기술노트 → 다(경계 항목은 ambiguous).
- 법률·고시 → 라; 프로시딩·학술대회·프리프린트·working paper·소프트웨어·공식 웹문서·기사 → 마.
- 국외 단행본·출판사 → 바; 국외 정기 학술지 → 사.
- 개별 항목의 [확정 필요]·[UNVERIFIED]·⚠ → flagged로만 수록; categories와 중복 계수하지 않음.
- 골격의 행 순서를 분류별로 유지. Cvach/Cohen 등 골격의 실제 순서도 재정렬하지 않음.
- 연도가 여러 번 나오거나 날짜/법령 구조가 애매하면 변환하지 않고 ambiguous로 기록. 분류와 연도 변환 판단 메모는 한 항목에 복수 존재할 수 있음.

## 개수

| 분류 | 개수 |
|---|---:|
| 가. 학위논문 | 15 |
| 나. 학술지 | 3 |
| 다. 보고서 | 4 |
| 라. 관련법 | 4 |
| 마. 기타 | 10 |
| 바. 국외 단행본 | 7 |
| 사. 국외 학술지 | 16 |
| flagged | 5 |
| 합계 | 64 |

원본 하위 절 항목 수: {"1. 국내문헌(저자 가나다순)": 23, "2. 국외문헌(제1저자 알파벳순)": 30, "3. 법령(국가법령정보센터)": 4, "4. 표준·기술자료": 5, "5. 기타 자료(ref 37의 검증 기사)": 2}. 연도 이동 35개; ambiguous 34건 / 서로 다른 28항목.

## flagged 원문

| 원문 행 | 서지 원문 | 표시 사유 원문 |
|---:|---|---|
| 267 | 왕인국, 「건설현장 위험요인 식별을 위한 RAG와 Fine-tuning 기반 LLM 성능향상에 관한 연구」, 광운대학교 대학원 건축공학과 석사학위논문, 2025(잠정). [확정 필요: 발행·학위수여 연도; 원문 제출 2024.12 확인] | [확정 필요: 발행·학위수여 연도; 원문 제출 2024.12 확인] |
| 268 | 윤영석, 「중·소규모 건설현장 안전관리자 인건비 직접공사비 계상과 안전관리 작동성에 관한 연구」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문, 2025(제출연도에 따른 잠정 표기). [확정 필요: 발행·학위수여 연도; 원문 제출 2025.12 확인] | [확정 필요: 발행·학위수여 연도; 원문 제출 2025.12 확인] |
| 309 | The jamovi project, jamovi [Computer Software]. https://www.jamovi.org [확정 필요: 실제 사용 버전·해당 공식 인용문과 연도; 과거 Version 2.7 인용 기록은 위 서지관리번호 #6에 보존] | [확정 필요: 실제 사용 버전·해당 공식 인용문과 연도; 과거 Version 2.7 인용 기록은 위 서지관리번호 #6에 보존] |
| 327 | 「중대재해 처벌 등에 관한 법률」 [시행 2022. 1. 27.] [법률 제17907호, 2021. 1. 26., 제정] (ref 58 원문 대조 2026-08-25) [확정 필요: 인용 조항] — 01장(50억 원 미만 현장의 규제 편입 시점) | [확정 필요: 인용 조항] |
| 339 | EN 50136-1, Alarm systems — Alarm transmission systems and equipment — Part 1: General requirements for alarm transmission systems. [UNVERIFIED — 정본 Table 2 대조 필요] 최고등급 전송 지연 평균 10초. 측정 구간이 전송에 한정되며 경보 장치 내부 처리를 제외한다. | [UNVERIFIED — 정본 Table 2 대조 필요] |

## ambiguous 목록

| 원문 행 | 서지 원문 | 후보 | 이유 |
|---:|---|---|---|
| 255 | 고용노동부, 『2024 산업재해 현황분석』, 고용노동부, 2025a. (ref 30 통계; 제1장 내주: 고용노동부, 2025a) | 다. 보고서 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 256 | 고용노동부, 「건설업 산업안전보건관리비 계상 및 사용기준」, 고용노동부고시 제2025-11호, 2025b. 제2조제1항제2호·제4조. https://www.moel.go.kr/info/lawinfo/instruction/view.do?bbs_seq=20250200610 (제2장 내주: 고용노동부, 2025b; 2026-09-30 공식 첨부 원문 대조) | 라. 관련법 | 행 전체에 연도 출현이 4개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 257 | 국토교통부·국토안전관리원, 『스마트 안전장비 활용 가이드라인』, 2024.03, CS-24-E6-002. (ref 36) | 다. 보고서 / 마. 기타 | 기관 가이드라인/벤더 기술노트의 양식상 보고서와 기타 분류 판단 필요; 보고서 잠정 배치 |
| 257 | 국토교통부·국토안전관리원, 『스마트 안전장비 활용 가이드라인』, 2024.03, CS-24-E6-002. (ref 36) | 다. 보고서 | 연월/날짜 또는 식별자 안의 연도일 수 있어 토큰을 나누어 옮기지 않음 |
| 258 | 김민기·박성호, 『서울시 재난안전관리 지원 생성형 AI 구축과 활용 방안』, 서울연구원, 2026. (서울연 2024-BR-14; ref 33) | 다. 보고서 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 263 | 노희상·박종용·정상윤, 「건설산업 ESG 안전·보건 정책과 건설안전 성과와의 관계 연구」, 『안전문화연구』, 제51호, 2026, pp.89–112. DOI 10.52902/kjsc.2026.51.89. (ref 45; 내용별 출판 쪽수는 교정본과 별도 대조 필요) | 나. 학술지 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 264 | 류정·박인선, 「건설현장의 스마트 안전장비 성능과 도입 효과 분석」, 『Crisisonomy』, 제21권 제6호, 2025, pp.125–135. DOI 10.14251/crisisonomy.2025.21.6.125. (ref 32) | 나. 학술지 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 271 | 이석희·고대식·송석일, 「건설 안전 모니터링을 위한 장면그래프와 템플릿 기반 실시간 비디오 캡셔닝 시스템 구현」, 『Journal of KIIT』, 제23권 제11호, 2025, pp.279–282. DOI 10.14801/jkiit.2025.23.11.279. | 나. 학술지 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 286 | Bhatti, Y. A., What is Frugal, What is Innovation? Towards a Theory of Frugal Innovation, SSRN working paper, 2012. DOI 10.2139/ssrn.2005910. | 마. 기타 / 사. 국외 학술지 | 인용 골격의 보유 판본이 프리프린트/working paper이므로 기타 유지; 저널판으로 바꾸지 않음 |
| 287 | Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D., Wu, J., Winter, C., Hesse, C., Chen, M., Sigler, E., Litwin, M., Gray, S., Chess, B., Clark, J., Berner, C., McCandlish, S., Radford, A., Sutskever, I., &amp; Amodei, D., "Language Models are Few-Shot Learners", Advances in Neural Information Processing Systems, Vol. 33, Curran Associates, 2020, pp.1877–1901. https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html (ref 55) | 사. 국외 학술지 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 290 | Cohen, J., Statistical Power Analysis for the Behavioral Sciences (2nd ed.), Lawrence Erlbaum, 1988. (존재 검증: 2026-08-21 웹 대조 완료 — 구 효과크기 관례 참고 이력, 현행 표본 충분성의 근거 아님) | 바. 국외 단행본 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 296 | Green, S. B., "How many subjects does it take to do a regression analysis?", Multivariate Behavioral Research, Vol. 26, No. 3, 1991, pp. 499-510. (존재 검증: 2026-08-21 웹 대조 완료 — 구 표본 크기 판단 이력) | 사. 국외 학술지 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 297 | Huitema, B. E., The Analysis of Covariance and Alternatives (2nd ed.), Wiley, 2011. (존재 검증: 2026-08-21 웹 대조 완료 — 구 ANCOVA 설계 참고 이력) | 바. 국외 단행본 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 299 | Kim, J., Lee, Y., Yoon, D., Jung, C., &amp; Lee, G., "An Integrated YOLO and VLM System for Fire Detection in Enclosed Environments", Proceedings on “I Can't Believe It's Not Better: Challenges in Applied Deep Learning” at ICLR 2025 Workshops, Proceedings of Machine Learning Research, Vol. 296, 2025, pp.151–162. https://proceedings.mlr.press/v296/kim25a.html (ref 08; Kim et al.(2025)) | 마. 기타 / 사. 국외 학술지 | 학술대회/워크숍 프로시딩으로 정기 학술지와 구별해 기타 잠정 배치 |
| 299 | Kim, J., Lee, Y., Yoon, D., Jung, C., &amp; Lee, G., "An Integrated YOLO and VLM System for Fire Detection in Enclosed Environments", Proceedings on “I Can't Believe It's Not Better: Challenges in Applied Deep Learning” at ICLR 2025 Workshops, Proceedings of Machine Learning Research, Vol. 296, 2025, pp.151–162. https://proceedings.mlr.press/v296/kim25a.html (ref 08; Kim et al.(2025)) | 마. 기타 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 300 | Kish, L., Survey Sampling, John Wiley &amp; Sons, 1965. (존재 검증: 2026-08-21 웹 대조 완료 — 구 군집 설계효과·현장 수 산정 참고 이력, 현행 표본 산정의 근거 아님) | 바. 국외 단행본 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 303 | Mi, Y., Deep Learning-Based Safety Analysis for High-Altitude Construction Workers: PPE Detection and Posture Recognition Model Development, Doctoral dissertation, Kyungpook National University, 2025. (ref 19; 국내 대학 박사학위논문이며 영문 저자 표기에 따라 이 골격에 수록) | 가. 학위논문 | 영문 저자지만 골격에 국내 대학 박사학위논문이라고 명시되어 학위논문으로 배치; 국외 단행본으로 간주하지 않음 |
| 307 | Shadish, W. R., Cook, T. D., &amp; Campbell, D. T., Experimental and Quasi-Experimental Designs for Generalized Causal Inference, Houghton Mifflin, 2002. (존재 검증: 2026-07-12 웹 대조 완료 — 04장 인과 3조건 인용) | 바. 국외 단행본 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 308 | Teizer, J., "The Role of Automation in Right-time Construction Safety", Proceedings of the 33rd International Symposium on Automation and Robotics in Construction (ISARC 2016), 2016, pp.191–199. DOI 10.22260/ISARC2016/0024. (ref 63; 직접 대조한 학회본) | 마. 기타 / 사. 국외 학술지 | 학술대회/워크숍 프로시딩으로 정기 학술지와 구별해 기타 잠정 배치 |
| 308 | Teizer, J., "The Role of Automation in Right-time Construction Safety", Proceedings of the 33rd International Symposium on Automation and Robotics in Construction (ISARC 2016), 2016, pp.191–199. DOI 10.22260/ISARC2016/0024. (ref 63; 직접 대조한 학회본) | 마. 기타 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 310 | Wilson, E. B., "Probable Inference, the Law of Succession, and Statistical Inference", Journal of the American Statistical Association, Vol. 22, No. 158, 1927, pp. 209-212. DOI 10.1080/01621459.1927.10502953 | 사. 국외 학술지 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 311 | Wu, J., Wu, S., Ma, Y., Yu, G., Xu, H., Zheng, L., &amp; Duan, J., "MonitorVLM: A Vision–Language Framework for Safety Violation Detection in Mining Operations", arXiv:2510.03666v1, 2025. https://arxiv.org/abs/2510.03666v1 (ref 23; 보유·인용 판본) | 마. 기타 / 사. 국외 학술지 | 인용 골격의 보유 판본이 프리프린트/working paper이므로 기타 유지; 저널판으로 바꾸지 않음 |
| 312 | Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., &amp; Tabkhi, H., "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078v3, 2025. https://arxiv.org/abs/2312.02078v3 (ref 65; 직접 읽은 보유 판본, v3 공개 2025.8.12) | 마. 기타 / 사. 국외 학술지 | 인용 골격의 보유 판본이 프리프린트/working paper이므로 기타 유지; 저널판으로 바꾸지 않음 |
| 312 | Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., &amp; Tabkhi, H., "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078v3, 2025. https://arxiv.org/abs/2312.02078v3 (ref 65; 직접 읽은 보유 판본, v3 공개 2025.8.12) | 마. 기타 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 324 | 「건설기술 진흥법」 제39조(건설사업관리 등의 시행)·제49조(건설공사감독자의 감독 의무), [시행 2025. 10. 1.] [법률 제21065호, 2025. 10. 1., 타법개정]. — 03장 제2절 제4항 경보 수신자의 법적 직무 근거. https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&amp;lsJoLnkSeq=1033555451 ; https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1029371815 | 라. 관련법 | 행 전체에 연도 출현이 2개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 325 | 「건설산업기본법」 제40조(건설기술인의 배치), [시행 2025. 11. 27.] [법률 제21034호]. — 03장 제2절 제4항 현장 배치 건설기술인의 직무 근거. https://www.law.go.kr/법령/건설산업기본법/제40조 | 라. 관련법 | 법령 시행/공포일과 저자 표기가 일반 서지와 달라 연도 위치 유지 |
| 326 | 「산업안전보건법」 제15조(안전보건관리책임자)·제17조(안전관리자), [시행 2026. 6. 1.] [법률 제21374호, 2026. 2. 19., 일부개정]. — 03장 제2절 제4항 경보 수신자의 법적 직무 근거. https://www.law.go.kr/법령/산업안전보건법 (2026-09-30 공식 조문 대조; 보유 ref 57의 2025.10.1 판본과 구별) | 라. 관련법 | 행 전체에 연도 출현이 4개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 340 | Bosch Security Systems, Alarm Verification for Alarm Management, Application note F01U411472, V02, 2024. (ref 69 — 벤더 애플리케이션 노트. 본문 내주가 아니라 제3장 제1절 제2항 각주로만 인용한다) | 다. 보고서 / 마. 기타 | 기관 가이드라인/벤더 기술노트의 양식상 보고서와 기타 분류 판단 필요; 보고서 잠정 배치 |
| 342 | jamovi, ANCOVA (ancova) [공식 문서], 연도 미상. https://docs.jamovi.org/jmv/jmv_ancova.html (열람일 2026.10.3; 제4장 주 분석 기능 확인). | 마. 기타 | 연월/날짜 또는 식별자 안의 연도일 수 있어 토큰을 나누어 옮기지 않음 |
| 343 | jamovi, Linear Regression (linReg) [공식 문서], 연도 미상. https://docs.jamovi.org/jmv/jmv_linReg.html (열람일 2026.10.3; 제4장 동일 모형 계수·진단 보조 출력 확인). | 마. 기타 | 연월/날짜 또는 식별자 안의 연도일 수 있어 토큰을 나누어 옮기지 않음 |
| 350 | 김정아(2021.5.4), 「도시안전정보센터, 지능형 CCTV 선별관제시스템 구축」, 김포신문. https://www.igimpo.com/news/articleView.html?idxno=63694 (검색일 2026.9.12). 내주: 김정아(2021). | 마. 기타 | 골격 절 공통 안내: [확정 필요: 최종본의 기타 자료 분리 수록 형식 — 지도교수 협의]; 개별 기사 서지는 확정이므로 flagged 아닌 기타로 유지 |
| 350 | 김정아(2021.5.4), 「도시안전정보센터, 지능형 CCTV 선별관제시스템 구축」, 김포신문. https://www.igimpo.com/news/articleView.html?idxno=63694 (검색일 2026.9.12). 내주: 김정아(2021). | 마. 기타 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |
| 352 | 손형주(2024.5.24), 「부산 강서구, 271억원 들여 지능형 CCTV 관제 시스템 도입」, 연합뉴스. https://www.yna.co.kr/view/AKR20240524079100051 (검색일 2026.9.12). 내주: 손형주(2024). | 마. 기타 | 골격 절 공통 안내: [확정 필요: 최종본의 기타 자료 분리 수록 형식 — 지도교수 협의]; 개별 기사 서지는 확정이므로 flagged 아닌 기타로 유지 |
| 352 | 손형주(2024.5.24), 「부산 강서구, 271억원 들여 지능형 CCTV 관제 시스템 도입」, 연합뉴스. https://www.yna.co.kr/view/AKR20240524079100051 (검색일 2026.9.12). 내주: 손형주(2024). | 마. 기타 | 행 전체에 연도 출현이 3개라 발행연도 이동을 하지 않음(제목·DOI·URL·검증/열람일·내주 메모도 포함) |

## 이전 두 JSON과 차이

이전 references.json과 Task I references_kjn.json은 원문 항목 다중집합이 동일한 51개(20+flagged31)이다. 아래 표는 두 파일 모두에 대한 원문 비교이며, v1에서 달라진 분류도 함께 표시한다. 대응 없음은 골격에 없는 항목을 v2로 가져오지 않았다는 뜻이며 파일이나 원전을 삭제한 것이 아니다. 부분 제목·구 저자명 대응은 검토용이며, 이 대응 정보를 사용해 새로운 서지 문장을 만들지 않았다.

| 이전 JSON 서지 | 이전/v1 분류 | 변화 | 현행 골격 행·서지·분류 |
|---|---|---|---|
| 김윤헌, 「건설현장 위험상황 이해 및 대응을 위한 인공지능 안전인지 프레임워크 연구」, 성균관대학교 일반대학원 글로벌스마트시티융합전공 박사학위논문, 2026. | 가. 학위논문 / 가. 학위논문 | 표기/정보 갱신 또는 분리·통합 | 261: 김태헌, 「건설현장 위험상황 이해 및 대응을 위한 인공지능 안전인지 프레임워크 연구」, 성균관대학교 일반대학원 글로벌스마트시티융합전공 박사학위논문, 2026. [가. 학위논문] |
| 김현수, 「통합관제센터 운영을 위한 Vision AI–VLM 비교 및 하이브리드 연구」, 중앙대학교 대학원 ICT안전학과 석사학위논문, 2026. | 가. 학위논문 / 가. 학위논문 | 동일 | 262: 김현수, 「통합관제센터 운영을 위한 Vision AI–VLM 비교 및 하이브리드 연구」, 중앙대학교 대학원 ICT안전학과 석사학위논문, 2026. [가. 학위논문] |
| 박종학, 「YOLO(You Only Look Once) 모델별 건설 현장 위험 상태 및 객체 인식 성능 비교」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문, 2025. | 가. 학위논문 / 가. 학위논문 | 동일 | 266: 박종학, 「YOLO(You Only Look Once) 모델별 건설 현장 위험 상태 및 객체 인식 성능 비교」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문, 2025. [가. 학위논문] |
| 왕인국, 「건설현장 위험요인 식별을 위한 RAG와 Fine-tuning 기반 LLM 성능향상에 관한 연구」, 광운대학교 대학원 석사학위논문, 2025. | 가. 학위논문 / 가. 학위논문 | 표기/정보 갱신 또는 분리·통합 | 267: 왕인국, 「건설현장 위험요인 식별을 위한 RAG와 Fine-tuning 기반 LLM 성능향상에 관한 연구」, 광운대학교 대학원 건축공학과 석사학위논문, 2025(잠정). [확정 필요: 발행·학위수여 연도; 원문 제출 2024.12 확인] [flagged] |
| 윤영석, 「중·소규모 건설현장 안전관리자 인건비 직접공사비 계상과 안전관리 작동성에 관한 연구」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문, 2025. | 가. 학위논문 / 가. 학위논문 | 표기/정보 갱신 또는 분리·통합 | 268: 윤영석, 「중·소규모 건설현장 안전관리자 인건비 직접공사비 계상과 안전관리 작동성에 관한 연구」, 경기대학교 공학대학원 건축·안전공학전공 석사학위논문, 2025(제출연도에 따른 잠정 표기). [확정 필요: 발행·학위수여 연도; 원문 제출 2025.12 확인] [flagged] |
| 이동건, 「통합기술수용모델(UTAUT)을 활용한 건설근로자들의 스마트안전장비 수용에 영향을 미치는 요인에 관한 연구」, 인하대학교 공학대학원 건축토목공간정보공학과 석사학위논문, 2024. | 가. 학위논문 / 가. 학위논문 | 동일 | 269: 이동건, 「통합기술수용모델(UTAUT)을 활용한 건설근로자들의 스마트안전장비 수용에 영향을 미치는 요인에 관한 연구」, 인하대학교 공학대학원 건축토목공간정보공학과 석사학위논문, 2024. [가. 학위논문] |
| 이준호, 「건설현장 중대재해 감소를 위한 스마트 안전장비의 지원방법 개선에 관한 연구」, 한양대학교 융합산업대학원 석사학위논문, 2024. | 가. 학위논문 / 가. 학위논문 | 동일 | 272: 이준호, 「건설현장 중대재해 감소를 위한 스마트 안전장비의 지원방법 개선에 관한 연구」, 한양대학교 융합산업대학원 석사학위논문, 2024. [가. 학위논문] |
| 황병복, 「철도 건설사업에서 스마트 건설기술의 도입 및 활용이 안전 성과에 미치는 영향」, 우송대학교 일반대학원 철도공학과 박사학위논문, 2026. | 가. 학위논문 / 가. 학위논문 | 동일 | 277: 황병복, 「철도 건설사업에서 스마트 건설기술의 도입 및 활용이 안전 성과에 미치는 영향」, 우송대학교 일반대학원 철도공학과 박사학위논문, 2026. [가. 학위논문] |
| Cvach, M., "Monitor alarm fatigue: An integrative review", Biomedical Instrumentation &amp; Technology, Vol. 46, No. 4, 2012, pp. 268-277. | 나. 학술지 / 사. 국외 학술지 | 동일 | 289: Cvach, M., "Monitor alarm fatigue: An integrative review", Biomedical Instrumentation &amp; Technology, Vol. 46, No. 4, 2012, pp. 268-277. [사. 국외 학술지] |
| Davis, F. D., "Perceived usefulness, perceived ease of use, and user acceptance of information technology", MIS Quarterly, Vol. 13, No. 3, 1989, pp. 319-340. | 나. 학술지 / 사. 국외 학술지 | 동일 | 291: Davis, F. D., "Perceived usefulness, perceived ease of use, and user acceptance of information technology", MIS Quarterly, Vol. 13, No. 3, 1989, pp. 319-340. [사. 국외 학술지] |
| Lawshe, C. H., "A quantitative approach to content validity", Personnel Psychology, Vol. 28, No. 4, 1975, pp. 563-575. | 나. 학술지 / 사. 국외 학술지 | 동일 | 301: Lawshe, C. H., "A quantitative approach to content validity", Personnel Psychology, Vol. 28, No. 4, 1975, pp. 563-575. [사. 국외 학술지] |
| Pisu, A., Elia, N., Pompianu, L., Barchi, F., Acquaviva, A., &amp; Carta, S., "Enhancing workplace safety: A flexible approach for personal protective equipment monitoring", Expert Systems with Applications, Vol. 238, 2024, 122285. | 나. 학술지 / 사. 국외 학술지 | 표기/정보 갱신 또는 분리·통합 | 304: Pisu, A., Elia, N., Pompianu, L., Barchi, F., Acquaviva, A., &amp; Carta, S., "Enhancing workplace safety: A flexible approach for personal protective equipment monitoring", Expert Systems with Applications, Vol. 238, 2024, 122285. (ref 68) [사. 국외 학술지] |
| Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., &amp; Podsakoff, N. P., "Common method biases in behavioral research: A critical review of the literature and recommended remedies", Journal of Applied Psychology, Vol. 88, No. 5, 2003, pp. 879-903. | 나. 학술지 / 사. 국외 학술지 | 동일 | 305: Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., &amp; Podsakoff, N. P., "Common method biases in behavioral research: A critical review of the literature and recommended remedies", Journal of Applied Psychology, Vol. 88, No. 5, 2003, pp. 879-903. [사. 국외 학술지] |
| 고용노동부, 『2024 산업재해 현황분석』, 고용노동부, 2024. | 다. 보고서 / 다. 보고서 | 표기/정보 갱신 또는 분리·통합 | 255: 고용노동부, 『2024 산업재해 현황분석』, 고용노동부, 2025a. (ref 30 통계; 제1장 내주: 고용노동부, 2025a) [다. 보고서] |
| 한국산업안전보건공단, 『스마트 안전장비 활용 가이드라인』, 한국산업안전보건공단, 2024. | 다. 보고서 / 다. 보고서 | 표기/정보 갱신 또는 분리·통합 | 257: 국토교통부·국토안전관리원, 『스마트 안전장비 활용 가이드라인』, 2024.03, CS-24-E6-002. (ref 36) [다. 보고서] |
| Aiken, L. S., &amp; West, S. G., Multiple Regression: Testing and Interpreting Interactions, Sage, 1991. | 마. 기타 / 바. 국외 단행본 | 동일 | 285: Aiken, L. S., &amp; West, S. G., Multiple Regression: Testing and Interpreting Interactions, Sage, 1991. [바. 국외 단행본] |
| Shadish, W. R., Cook, T. D., &amp; Campbell, D. T., Experimental and Quasi-Experimental Designs for Generalized Causal Inference, Houghton Mifflin, 2002. | 마. 기타 / 바. 국외 단행본 | 표기/정보 갱신 또는 분리·통합 | 307: Shadish, W. R., Cook, T. D., &amp; Campbell, D. T., Experimental and Quasi-Experimental Designs for Generalized Causal Inference, Houghton Mifflin, 2002. (존재 검증: 2026-07-12 웹 대조 완료 — 04장 인과 3조건 인용) [바. 국외 단행본] |
| The jamovi project, jamovi (Version 2.7) [Computer Software], 2026. https://www.jamovi.org | 마. 기타 / 마. 기타 | 표기/정보 갱신 또는 분리·통합 | 309: The jamovi project, jamovi [Computer Software]. https://www.jamovi.org [확정 필요: 실제 사용 버전·해당 공식 인용문과 연도; 과거 Version 2.7 인용 기록은 위 서지관리번호 #6에 보존] [flagged] |
| Wu, J., Wu, S., Ma, Y., Yu, G., Xu, H., Zheng, L., &amp; Duan, J., "MonitorVLM: A Vision–Language Framework for Safety Violation Detection in Mining Operations", arXiv:2510.03666, 2025. | 마. 기타 / 마. 기타 | 표기/정보 갱신 또는 분리·통합 | 311: Wu, J., Wu, S., Ma, Y., Yu, G., Xu, H., Zheng, L., &amp; Duan, J., "MonitorVLM: A Vision–Language Framework for Safety Violation Detection in Mining Operations", arXiv:2510.03666v1, 2025. https://arxiv.org/abs/2510.03666v1 (ref 23; 보유·인용 판본) [마. 기타] |
| Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., &amp; Tabkhi, H., "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078, 2023. | 마. 기타 / 마. 기타 | 표기/정보 갱신 또는 분리·통합 | 312: Yao, S., Rahimi Ardabili, B., Danesh Pazho, A., Alinezhad Noghre, G., Neff, C., Bourque, L., &amp; Tabkhi, H., "From Lab to Field: Real-World Evaluation of an AI-Driven Smart Video Solution to Enhance Community Safety", arXiv:2312.02078v3, 2025. https://arxiv.org/abs/2312.02078v3 (ref 65; 직접 읽은 보유 판본, v3 공개 2025.8.12) [마. 기타] |
| 노희상·박종용·정상윤, 「건설산업 ESG 안전·보건 정책과 건설안전 성과와의 관계 연구」, 『안전문화연구』(ISSN 2586-2685) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 263: 노희상·박종용·정상윤, 「건설산업 ESG 안전·보건 정책과 건설안전 성과와의 관계 연구」, 『안전문화연구』, 제51호, 2026, pp.89–112. DOI 10.52902/kjsc.2026.51.89. (ref 45; 내용별 출판 쪽수는 교정본과 별도 대조 필요) [나. 학술지] |
| 류수영, 「CCTV 기반 산업안전 관제 시스템에 관한 연구」, 2023 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 265: 류수영, 「CCTV 기반 산업안전 관제 시스템에 관한 연구」, 배재대학교 대학원 컴퓨터공학과 박사학위논문, 2023. (ref 17) [가. 학위논문] |
| 이석희·고대식·송석일, 「건설 안전 모니터링을 위한 장면그래프와 템플릿 기반 실시간 비디오 캡셔닝 시스템 구현」, 『Journal of KIIT』, 제23권 제11호, 2025 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 271: 이석희·고대식·송석일, 「건설 안전 모니터링을 위한 장면그래프와 템플릿 기반 실시간 비디오 캡셔닝 시스템 구현」, 『Journal of KIIT』, 제23권 제11호, 2025, pp.279–282. DOI 10.14801/jkiit.2025.23.11.279. [나. 학술지] |
| An et al. (2025), An Integrated YOLO and LLM … | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 299: Kim, J., Lee, Y., Yoon, D., Jung, C., &amp; Lee, G., "An Integrated YOLO and VLM System for Fire Detection in Enclosed Environments", Proceedings on “I Can't Believe It's Not Better: Challenges in Applied Deep Learning” at ICLR 2025 Workshops, Proceedings of Machine Learning Research, Vol. 296, 2025, pp.151–162. https://proceedings.mlr.press/v296/kim25a.html (ref 08; Kim et al.(2025)) [마. 기타] |
| Zhou et al. (2023), Analysis of factors of willingness … | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 314: Zhou, Z.-C., Su, Y.-K., Zheng, Z.-Z., &amp; Wang, Y.-L., "Analysis of factors of willingness to adopt intelligent construction technology in highway construction enterprises", Scientific Reports, Vol. 13, 2023, 19339. DOI 10.1038/s41598-023-46241-6. (ref 40) [사. 국외 학술지] |
| Chong et al. (2023), The Adoption Intentions of Wearable Technology for Construction Safety | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 288: Chong, H.-Y., Xu, Y., Lun, C., &amp; Chi, M., "The Adoption Intentions of Wearable Technology for Construction Safety", Buildings, Vol. 13, No. 11, 2023, 2747. DOI 10.3390/buildings13112747. (ref 41) [사. 국외 학술지] |
| 이병길, 스마트장비(Drone·AIoT)를 활용한 … (ref 06) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 273: 이창남, 「스마트장비(Drone·AIoT)를 활용한 건설현장 안전 관리 활성화 방안에 관한 연구」, 경기대학교 대학원 건설안전학과 박사학위논문, 2025. (대표 ref 06; ref 18 중복) [가. 학위논문] |
| 스마트장비(Drone·AIoT)를 활용한 건설현장 안전 관리 활성화 방안에 관한 연구 (ref 18) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 273: 이창남, 「스마트장비(Drone·AIoT)를 활용한 건설현장 안전 관리 활성화 방안에 관한 연구」, 경기대학교 대학원 건설안전학과 박사학위논문, 2025. (대표 ref 06; ref 18 중복) [가. 학위논문] |
| Deep Learning-Based Safety Analysis for High-Altitude Construction Workers PPE Detection and Posture Recognition Model Development (ref 19) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 303: Mi, Y., Deep Learning-Based Safety Analysis for High-Altitude Construction Workers: PPE Detection and Posture Recognition Model Development, Doctoral dissertation, Kyungpook National University, 2025. (ref 19; 국내 대학 박사학위논문이며 영문 저자 표기에 따라 이 골격에 수록) [가. 학위논문] |
| 중소규모 건설현장 재해예방을 위한 스마트 건설안전기술 활용 방안 (ref 22) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 260: 김용선, 「중·소규모 건설현장 재해예방을 위한 스마트 건설안전기술 활용 방안」, 인천대학교 일반대학원 안전공학과 박사학위논문, 2022. (ref 22) [가. 학위논문] |
| 국내 소규모 민간 건설프로젝트의 산업안전보건관리비 준수 실태 분석 및 개선방안 제시연구 (ref 28) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 275: 조도빈, 「국내 소규모 민간 건설프로젝트의 산업안전보건관리비 준수 실태 분석 및 개선방안 제시연구」, 울산대학교 대학원 건축학과 공학박사학위논문, 2026. (ref 28) [가. 학위논문] |
| 건설현장의 스마트 안전장비 성능과 도입 효과 분석 (ref 32) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 264: 류정·박인선, 「건설현장의 스마트 안전장비 성능과 도입 효과 분석」, 『Crisisonomy』, 제21권 제6호, 2025, pp.125–135. DOI 10.14251/crisisonomy.2025.21.6.125. (ref 32) [나. 학술지] |
| 기사·웹자료 — 김포신문(2021)·연합뉴스(2024) 등 (ref 37) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 350: 김정아(2021.5.4), 「도시안전정보센터, 지능형 CCTV 선별관제시스템 구축」, 김포신문. https://www.igimpo.com/news/articleView.html?idxno=63694 (검색일 2026.9.12). 내주: 김정아(2021). [마. 기타]<br>352: 손형주(2024.5.24), 「부산 강서구, 271억원 들여 지능형 CCTV 관제 시스템 도입」, 연합뉴스. https://www.yna.co.kr/view/AKR20240524079100051 (검색일 2026.9.12). 내주: 손형주(2024). [마. 기타] |
| 객체 감지 기술을 활용한 반도체 건설 현장의 작업자 사고 예방 기술 연구 (ref 20) | flagged / flagged | 골격에서 대응 없음 |  |
| 서울시 재난안전관리 지원 생성형 AI 구축과 활용 방안 (ref 33) | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 258: 김민기·박성호, 『서울시 재난안전관리 지원 생성형 AI 구축과 활용 방안』, 서울연구원, 2026. (서울연 2024-BR-14; ref 33) [다. 보고서] |
| 정보기술수용이론(TAM)의 대안적 모델의 개발에 관한 연구 (ref 43) | flagged / flagged | 골격에서 대응 없음 |  |
| 「산업안전보건법」 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 326: 「산업안전보건법」 제15조(안전보건관리책임자)·제17조(안전관리자), [시행 2026. 6. 1.] [법률 제21374호, 2026. 2. 19., 일부개정]. — 03장 제2절 제4항 경보 수신자의 법적 직무 근거. https://www.law.go.kr/법령/산업안전보건법 (2026-09-30 공식 조문 대조; 보유 ref 57의 2025.10.1 판본과 구별) [라. 관련법] |
| 「건설기술 진흥법」 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 324: 「건설기술 진흥법」 제39조(건설사업관리 등의 시행)·제49조(건설공사감독자의 감독 의무), [시행 2025. 10. 1.] [법률 제21065호, 2025. 10. 1., 타법개정]. — 03장 제2절 제4항 경보 수신자의 법적 직무 근거. https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&amp;lsJoLnkSeq=1033555451 ; https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1029371815 [라. 관련법] |
| 「건설산업기본법」 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 325: 「건설산업기본법」 제40조(건설기술인의 배치), [시행 2025. 11. 27.] [법률 제21034호]. — 03장 제2절 제4항 현장 배치 건설기술인의 직무 근거. https://www.law.go.kr/법령/건설산업기본법/제40조 [라. 관련법] |
| 「중대재해 처벌 등에 관한 법률」 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 327: 「중대재해 처벌 등에 관한 법률」 [시행 2022. 1. 27.] [법률 제17907호, 2021. 1. 26., 제정] (ref 58 원문 대조 2026-08-25) [확정 필요: 인용 조항] — 01장(50억 원 미만 현장의 규제 편입 시점) [flagged] |
| EFA 적용 기준(KMO·Bartlett) 근거 문헌 | flagged / flagged | 골격에서 대응 없음 |  |
| Cronbach's α 기준(.70) 근거 문헌 | flagged / flagged | 골격에서 대응 없음 |  |
| 요인적재값 기준(.50/교차적재 .40) 근거 문헌 | flagged / flagged | 골격에서 대응 없음 |  |
| 다중공선성 진단 기준(상관계수·VIF) 근거 문헌 | flagged / flagged | 골격에서 대응 없음 |  |
| Green &amp; Swets (1966) — 신호감지이론(SDT) 원전 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 295: Green, D. M., &amp; Swets, J. A., Signal Detection Theory and Psychophysics, Wiley, 1966. ISBN 9780471324201. [바. 국외 단행본] |
| Dixon, Wickens &amp; McCarley (2007) — 오경보/미탐 비대칭 효과 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 292: Dixon, S. R., Wickens, C. D., &amp; McCarley, J. S., "On the independence of compliance and reliance: Are automation false alarms worse than misses?", Human Factors, Vol. 49, No. 4, 2007, pp.564–572. DOI 10.1518/001872007X215656. [사. 국외 학술지] |
| Igbaria &amp; Tan (1997) — IT 수용과 개인 수행도 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 298: Igbaria, M., &amp; Tan, M., "The consequences of information technology acceptance on subsequent individual performance", Information &amp; Management, Vol. 32, No. 3, 1997, pp.113–121. DOI 10.1016/S0378-7206(97)00006-2. [사. 국외 학술지] |
| Radjou, Prabhu &amp; Ahuja (2012) — Jugaad/절약형 혁신 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 306: Radjou, N., Prabhu, J., &amp; Ahuja, S., Jugaad Innovation: Think Frugal, Be Flexible, Generate Breakthrough Growth, Wiley, 2012. ISBN 9781118249741. [바. 국외 단행본] |
| Zeschky, Widenmayer &amp; Gassmann (2011) — 절약형 혁신 정의 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 313: Zeschky, M., Widenmayer, B., &amp; Gassmann, O., "Frugal innovation in emerging markets", Research-Technology Management, Vol. 54, No. 4, 2011, pp.38–45. DOI 10.5437/08956308X5404007. [사. 국외 학술지] |
| Bhatti (2012) — 절약형 혁신 개념화 | flagged / flagged | 표기/정보 갱신 또는 분리·통합 | 286: Bhatti, Y. A., What is Frugal, What is Innovation? Towards a Theory of Frugal Innovation, SSRN working paper, 2012. DOI 10.2139/ssrn.2005910. [마. 기타] |
| Tiwari &amp; Herstatt (2012) — 절약형 엔지니어링 | flagged / flagged | 골격에서 대응 없음 |  |

### 이전 대응 없는 추가 항목 20개

- 256: 고용노동부, 「건설업 산업안전보건관리비 계상 및 사용기준」, 고용노동부고시 제2025-11호, 2025b. 제2조제1항제2호·제4조. https://www.moel.go.kr/info/lawinfo/instruction/view.do?bbs_seq=20250200610 (제2장 내주: 고용노동부, 2025b; 2026-09-30 공식 첨부 원문 대조)
- 259: 김석기, 「소규모 건설현장 사망사고의 시스템적 원인 규명을 위한 BERTopic-LLM과 AcciMap 통합 분석 프레임워크 개발」, 충북대학교 박사학위논문, 2026. (ref 51)
- 270: 이기수, 「건설현장의 안전 확보를 위한 딥러닝 기반의 시스템비계 설치 이상감지 연구」, 명지대학교 박사학위논문, 2024. (ref 49)
- 274: 이형도, 「객체탐지 알고리즘을 이용한 건설현장 근로자 안전모 실시간 모니터링 기술 활성화 방안 연구」, 경기대학교 대학원 건설안전학과 박사학위논문, 2024. (ref 52)
- 276: 한소은, 「건설현장 ‘일일 위험성 평가서’ 자동 생성 모델: ‘Vision-Language Model (VLM)’을 활용하여」, 인천대학교 대학원 건축학과 석사학위논문, 2026. (번호가 중복된 30번 VLM 학위논문; 전체 파일명으로 식별)
- 287: Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D., Wu, J., Winter, C., Hesse, C., Chen, M., Sigler, E., Litwin, M., Gray, S., Chess, B., Clark, J., Berner, C., McCandlish, S., Radford, A., Sutskever, I., & Amodei, D., "Language Models are Few-Shot Learners", Advances in Neural Information Processing Systems, Vol. 33, Curran Associates, 2020, pp.1877–1901. https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html (ref 55)
- 290: Cohen, J., Statistical Power Analysis for the Behavioral Sciences (2nd ed.), Lawrence Erlbaum, 1988. (존재 검증: 2026-08-21 웹 대조 완료 — 구 효과크기 관례 참고 이력, 현행 표본 충분성의 근거 아님)
- 293: Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A., "G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences", Behavior Research Methods, Vol. 39, No. 2, 2007, pp. 175-191. (ref 61)
- 294: Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G., "Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses", Behavior Research Methods, Vol. 41, No. 4, 2009, pp. 1149-1160. (ref 62)
- 296: Green, S. B., "How many subjects does it take to do a regression analysis?", Multivariate Behavioral Research, Vol. 26, No. 3, 1991, pp. 499-510. (존재 검증: 2026-08-21 웹 대조 완료 — 구 표본 크기 판단 이력)
- 297: Huitema, B. E., The Analysis of Covariance and Alternatives (2nd ed.), Wiley, 2011. (존재 검증: 2026-08-21 웹 대조 완료 — 구 ANCOVA 설계 참고 이력)
- 300: Kish, L., Survey Sampling, John Wiley & Sons, 1965. (존재 검증: 2026-08-21 웹 대조 완료 — 구 군집 설계효과·현장 수 산정 참고 이력, 현행 표본 산정의 근거 아님)
- 302: Massoz, Q., Verly, J. G., & Van Droogenbroeck, M., "Multi-Timescale Drowsiness Characterization Based on a Video of a Driver's Face", Sensors, Vol. 18, No. 9, 2018, 2801. (ref 64)
- 308: Teizer, J., "The Role of Automation in Right-time Construction Safety", Proceedings of the 33rd International Symposium on Automation and Robotics in Construction (ISARC 2016), 2016, pp.191–199. DOI 10.22260/ISARC2016/0024. (ref 63; 직접 대조한 학회본)
- 310: Wilson, E. B., "Probable Inference, the Law of Succession, and Statistical Inference", Journal of the American Statistical Association, Vol. 22, No. 158, 1927, pp. 209-212. DOI 10.1080/01621459.1927.10502953
- 339: EN 50136-1, Alarm systems — Alarm transmission systems and equipment — Part 1: General requirements for alarm transmission systems. [UNVERIFIED — 정본 Table 2 대조 필요] 최고등급 전송 지연 평균 10초. 측정 구간이 전송에 한정되며 경보 장치 내부 처리를 제외한다.
- 340: Bosch Security Systems, Alarm Verification for Alarm Management, Application note F01U411472, V02, 2024. (ref 69 — 벤더 애플리케이션 노트. 본문 내주가 아니라 제3장 제1절 제2항 각주로만 인용한다)
- 341: Ultralytics, [Computer Software], 2025. (3장 1차 검출기)
- 342: jamovi, ANCOVA (ancova) [공식 문서], 연도 미상. https://docs.jamovi.org/jmv/jmv_ancova.html (열람일 2026.10.3; 제4장 주 분석 기능 확인).
- 343: jamovi, Linear Regression (linReg) [공식 문서], 연도 미상. https://docs.jamovi.org/jmv/jmv_linReg.html (열람일 2026.10.3; 제4장 동일 모형 계수·진단 보조 출력 확인).

### 골격에 대응 없어 제외된 이전 항목 7개

- 객체 감지 기술을 활용한 반도체 건설 현장의 작업자 사고 예방 기술 연구 (ref 20)
- 정보기술수용이론(TAM)의 대안적 모델의 개발에 관한 연구 (ref 43)
- EFA 적용 기준(KMO·Bartlett) 근거 문헌
- Cronbach's α 기준(.70) 근거 문헌
- 요인적재값 기준(.50/교차적재 .40) 근거 문헌
- 다중공선성 진단 기준(상관계수·VIF) 근거 문헌
- Tiwari & Herstatt (2012) — 절약형 엔지니어링

## 서지 교정 범위

김윤헌→김태헌, 공단→국토교통부·국토안전관리원, 이병길/중복 ref18→이창남 및 Yao 보유판본 2025 등의 차이는 현행 골격 원문을 가져온 결과이지 이 작업에서 교정·추정한 내용이 아니다. 왕인국·윤영석은 현행 연도 미확정 마커 때문에 이전 categories에서 flagged로 이동했다. 원전 존재·최신 법령·연도 사실관계는 재검증하지 않았다. 기사 두 건에 대한 마지막 공통 메모는 서지 자체가 아닌 수록 형식의 협의 사항으로, 개별 항목을 flagged로 바꾸지 않고 ambiguous에 기록했다.

## 검증 출력

- JSON_LOAD PASS
- SKELETON_COVERAGE PASS: 64 = categories 59 + flagged 5; source lines unique and complete
- ORIGINAL_TEXT PASS: 64/64 match source lines after whitespace normalization
- BIBLIOGRAPHIC_INVARIANCE PASS: 64/64 after excluding year tokens/punctuation; stricter literal year relocation 35/35; unchanged 29/29
- NUMBERING_ORDER PASS: each category starts at 1 and preserves skeleton line order
- FLAGGED_MARKERS PASS: 5/5 source marker text exact
- CATEGORIES: 가15 / 나3 / 다4 / 라4 / 마10 / 바7 / 사16; flagged5
- AMBIGUOUS: 34 reason records for 28 distinct items; 24 categorized items retain original year position
- DIFF: old references.json and references_kjn.json original sets identical (51); newly matched items 20 additions, 7 old entries absent, 10 unchanged old entries, 34 changed/split/merged old entries
- WRITE_SCOPE: references_kjn_v2.json and references_kjn_v2_report.md only; source hash unchanged
