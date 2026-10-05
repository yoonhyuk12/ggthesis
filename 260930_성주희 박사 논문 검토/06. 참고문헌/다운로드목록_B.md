# 다운로드목록 B

확인일: 2026-10-05. 담당 5편 중 원문 PDF 3편 확보, 2편 미확보 안내 MD 저장. 기존 원고·분석결과·기존 파일은 수정하지 않음.

| 번호 | 파일명 | 출처 URL | 버전 | PDF 쪽수 | SHA256(저장파일) | 상태 |
|---|---|---|---|---:|---|---|
| 01 | [01_Galbraith_1974_Organization_Design.pdf](01_Galbraith_1974_Organization_Design.pdf) | https://jaygalbraith.com/wp-content/uploads/2024/03/infoprocess1974.pdf | publisher 스캔 사본(저자사이트) | 10 | 86f07cf46163c3d402d64e447c5bb36a6d4ad94542c921cfd80ebdcd493cca64 | 확보 |
| 05 | [05_Weinstein_2005_원문미확보.md](05_Weinstein_2005_원문미확보.md) | https://www.researchgate.net/publication/245283555 | 미확보 | 해당없음 | d4d6e654310424a51a82d8a7dd951b511800403121ce1888579c63e93ee2885a | 원문 PDF 미확보; MD 안내 |
| 06 | [06_Lingard_2014_Early_Constructor_Involvement.pdf](06_Lingard_2014_Early_Constructor_Involvement.pdf) | https://stacks.cdc.gov/view/cdc/225306/cdc_225306_DS1.pdf | publisher 사본(CDC 기관저장소) | 15 | 7ceef8bb1906fded91507acf8d3c663007624e01956fc313778b45109dcf8d08 | 확보 |
| 07 | [07_Cigularov_2010_Error_Management_Climate.pdf](07_Cigularov_2010_Error_Management_Climate.pdf) | https://stacks.cdc.gov/view/cdc/188681/cdc_188681_DS1.pdf | publisher 사본(CDC 기관저장소) | 9 | 515db9e6e7793e5a24787824754186953c01c49ed9cf058d66fb56ef852a0698 | 확보 |
| 보조09 | [보조09_Kines_2010_원문미확보.md](보조09_Kines_2010_원문미확보.md) | https://nfa.elsevierpure.com/en/publications/improving-construction-site-safety-through-leader-based-verbal-sa/ | 미확보 | 해당없음 | 56c49d4f8e4957fe3ba114b01016b2f3aa3208d0d6d4df426714ec9545f31204 | 원문 PDF 미확보; MD 안내 |

## 검증 증거

- 3편 모두 requests로 다운로드, `%PDF-` magic 확인, PyMuPDF 정상 개방 및 페이지수 확인. HTML 오류응답은 PDF로 저장하지 않았다.
- 01: 10쪽. 텍스트 없는 스캔으로 첫 페이지를 이미지 렌더링해 “Organization Design: An Information Processing View”, “Jay R. Galbraith”, Interfaces Vol. 4 No. 3 May 1974 및 인쇄 쪽수 28 확인. 논문 28–36쪽 뒤 마지막 저작권 안내 1쪽으로 총 10쪽이다. 마지막 페이지 이미지도 확인했다. 첫 기본 요청 406 이후 브라우저 User-Agent의 공개 요청으로 확보했다.
- 06: 15쪽. 첫쪽 제목과 Helen Lingard, Payam Pirzadeh, Nick Blismas, Ron Wakefield, Brian Kleiner 확인. 첫쪽 하단 ©2014, 32(9), 918–931 및 DOI 10.1080/01446193.2014.911931 일치. 논문 14쪽 + 마지막 저작권 안내 1쪽.
- 07: 9쪽. 첫쪽 제목과 Konstantin P. Cigularov, Peter Y. Chen, John Rosecrance 확인. 첫쪽 머리말 Accident Analysis and Prevention 42 (2010) 1498–1506 일치.
- CDC 두 파일은 기본 requests 요청 HTTP 200으로 확보(브라우저 User-Agent 요청은 403). 파일은 수신한 PDF 원본 그대로이며 OCR·재인쇄·본문 재작성하지 않았다.
- 05/보조09: 출판사·공개 사본·기관 저장소·정확한 제목과 DOI 검색·OpenAlex 대체 링크 확인 후 중단. 구체적인 실패 URL과 HTTP 응답, 정확한 서지 및 초록요약은 각각의 미확보 MD 참조. 위 미확보 항목 해시는 PDF가 아닌 안내 MD의 해시다.
