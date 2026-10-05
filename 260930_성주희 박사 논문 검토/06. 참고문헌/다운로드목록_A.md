# 참고문헌 다운로드목록 A

확인일: 2026-10-05. 담당 번호: 02, 03, 04, 08. 결과: **PDF 확보 1편, 미확보 3편**. 미확보 항목에는 원문 대신 실패 이유·정확한 서지·DOI·공식 URL·짧은 초록 요약을 담은 MD를 생성했다.

| 번호 | 상태 | 파일명 | 버전 | PDF 쪽수 | SHA256 (저장된 파일) | 출처 URL |
|---|---|---|---|---|---|---|
| 02 | 미확보 | [02_Han_2014_원문미확보.md](02_Han_2014_원문미확보.md) | 해당 없음 | — (PDF 없음) | a8a92ed3820bfe2887260319ccaa3289eb3732b6322f8ee1558261c84bc209ec | [공식](https://www.sciencedirect.com/science/article/pii/S0001457513004041) · [대체](https://pubmed.ncbi.nlm.nih.gov/24184131/) |
| 03 | 미확보 | [03_Mohammadi_Tavakolan_2019_원문미확보.md](03_Mohammadi_Tavakolan_2019_원문미확보.md) | 해당 없음 | — (PDF 없음) | 7d73bd96fca87bf8a9fd1bb1367976b9979aed0adbf9f41e703f516c831a2082 | [공식](https://www.sciencedirect.com/science/article/pii/S0022437519306413) · [대체](https://www.researchgate.net/publication/337453322_Modeling_the_effects_of_production_pressure_on_safety_performance_in_construction_projects_using_system_dynamics) |
| 04 | 확보·검증 통과 | [04_신원상_손창백_2019_설계안전성검토.pdf](04_신원상_손창백_2019_설계안전성검토.pdf) | publisher (KoreaScience 제공 출판본) | 9 (351–359) | 29b93bdcde814e832206764d1bf9c38669de6fde29918cfbc28a45e2daaca6cd | [PDF](https://koreascience.or.kr/article/JAKO201924155913111.pdf) |
| 08 | 미확보 | [08_Feng_2013_원문미확보.md](08_Feng_2013_원문미확보.md) | 해당 없음 | — (PDF 없음) | a41a09d589db02b04cb7c86743841aa5e1ece55ffb2830fabda42c6368ad266a | [공식](https://www.sciencedirect.com/science/article/pii/S092575351300091X) · [대체](https://researchers.westernsydney.edu.au/en/publications/effect-of-safety-investments-on-safety-performance-of-building-pr/) |

## 검증 증거

- 04 다운로드: Python requests GET, HTTP 200, Content-Type application/pdf;charset=UTF-8. 크기 535,203 bytes.
- PDF magic: b'%PDF-1.6'. PyMuPDF 1.28.2 개방 성공, 9쪽.
- 첫 페이지 추출문에서 제목 `건설프로젝트의설계안전성검토에대한인식분석및개선방안`, 저자 `신원상`, `손창백`, 연도 `2019`, DOI `10.5345/JKIBC.2019.19.4.351` 모두 일치. 영문 제목 및 Shin, Won-Sang / Son, Chang-Baek도 확인했다.
- 첫 페이지 학술지 표기: J. Korea Inst. Build. Constr. Vol. 19, No. 4 : 351–359 / Aug, 2019. 텍스트형 PDF로 스캔 이미지 판독은 불필요했다.
- 정확한 서지: 신원상·손창백(2019). 건설프로젝트의 설계안전성 검토에 대한 인식 분석 및 개선방안. 한국건축시공학회지, 19(4), 351–359. https://doi.org/10.5345/JKIBC.2019.19.4.351
- KCI 서지 대조: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002492373
- 02·03·08: 출판사 PDF 요청 HTTP 403 HTML, Elsevier API PDF 요청 HTTP 406. 오류 응답을 PDF로 저장하지 않았다. 각 MD에 대체 공개 경로와 실패 이유를 상세 기록했다.
- 미확보 행의 SHA256은 안내 MD 자체의 해시이며 논문 PDF의 해시가 아니다. 미확보 자료의 PDF 버전·페이지 검증은 수행할 수 없었다.

## 검색 범위와 경계

정확한 제목·DOI·저자와 PDF/download/repository 조합 검색, 출판사 직접 PDF, OpenAlex 공개저장소 위치, 02·03 Semantic Scholar PDF 위치, 03 ResearchGate 요청형 페이지, 08 Western Sydney University 기관 저장소 및 과거 핸들·ResearchGate 공개사본 경로를 확인했다. 검색엔진에 나타난 다른 논문의 참고문헌 PDF는 원문으로 저장하지 않았다. 로그인·결제·저자 연락 없이 유한한 대체 경로 검색 후 종료했다. 원고·05 분석결과·기존 파일은 수정하지 않았다.
