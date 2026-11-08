# patch_from_fresh 보고

통계: {"equal": 522, "insert": 2, "replace_fresh": 24, "replace_kept": 0, "delete_kept": 8, "manual": 3, "table_same_kept": 3, "caption_split": 0}
header 추가 항목: {"charPr": [], "paraPr": [], "borderFill": [], "tabPr": [], "font": []}

## 수동 재적용 필요
- base 3 vs fresh 3 문단을 짝짓지 못해 base 유지: 현장 운영 특성에서 도입 현장은 담당자 부재 시 자동 알림으로 위험을 아는 비율(50.0%
- base 2 vs fresh 3 문단을 짝짓지 못해 base 유지: 변수 현장 도입 여부 N Mean SD t (71) p 만 나이(세) 도입 34 46.4 
- section1(목차·감사의 글·논문 개요)을 조립본으로 교체 — base의 목차 run 압축(장평·자간) 등 사용자 서식은 재적용 필요

## 로그
- INSERT  | 산재보상 승인자료로 비율을 계산하고 300억 원 이상 구간을 합산하였으며, 분류불능은 공사금액이 없는 경우이다.
- KEEP(table same content, merged) | <표2-1>
- KEEP(base only) | 
- KEEP(base only) | 
- REPLACE | 평가 지표는 정밀도, 재현율, F1, 시간당 오경보 빈도(FAR), 특이  ->  평가 지표는 정밀도, 재현율, F1, 시간당 오경보 빈도(FAR), 특이
- REPLACE(table) | <표3-8> (표0 셀(0, 1) base 'Precision(정밀도)' ≠ fresh 'Precision')
- KEEP(table same content, merged) | <표3-10>
- INSERT  | <그림 3-5> 도입 현장의 시스템 특성 인식(C)·경보 피로도 완화 인식(D) 평균(n=34)
- KEEP(base only) | <그림 3-5> 도입 현장의 시스템 특성 인식(C)·경보 피로도 완화 인식(D) 평균(n=34)
- MANUAL | base 3 vs fresh 3 문단을 짝짓지 못해 base 유지: 현장 운영 특성에서 도입 현장은 담당자 부재 시 자동 알림으로 위험을 아는 비율(50.0%
- KEEP(base only) | 
- KEEP(base only) | 
- KEEP(base only) | 
- KEEP(table same content) | <표4-3>
- KEEP(base only) | 
- REPLACE | 분석은 jamovi 2.7.41(2026)로 수행하였다. 안전관리 실효성  ->  분석은 jamovi 2.7.41(The jamovi project, 20
- MANUAL | base 2 vs fresh 3 문단을 짝짓지 못해 base 유지: 변수 현장 도입 여부 N Mean SD t (71) p 만 나이(세) 도입 34 46.4 
- SKIP(blank insert)
- SKIP(blank insert)
- KEEP(base only) | 
- DROP(base, replaced by block) | 연구가설 (1-1)은 공분산분석(ANCOVA)으로 검정하였다. 현장을 무작위로 배정하지 않은 횡단 비교에서는
- REPLACE(block) | 연구가설 (1-1)은 공분산분석(ANCOVA)으로 검정하였다. 공분산분석은 두 집단의 평균을 비교하되, 점수
- REPLACE(block) | 이 방법을 택한 것은 현장을 무작위로 나누어 시스템을 설치할 수 없었기 때문이다. 무작위로 배정하면 두 집단
- REPLACE | 조정 평균은 통제변수를 같은 조건에 맞춘 집단별 예측 평균이며, 연구가설  ->  조정 평균은 통제변수를 같은 조건에 맞춘 집단별 예측 평균이며, 연구가설
- REPLACE | 도입 현장의 조정 평균은 미도입 현장보다 0.54점 높았다. 통제변수를   ->  도입 현장의 조정 평균은 미도입 현장보다 0.54점 높았다. 통제변수 없
- REPLACE | 조정 평균과 집단 간 차이를 제시한 <표 4-12>의 CI는 실제 값이   ->  조정 평균과 집단 간 차이를 제시한 <표 4-12>의 신뢰구간(CI)은 
- REPLACE(table) | <표4-12> (표0 셀(0, 4) base '95%Confidenceinterva' ≠ fresh '95%신뢰구간(CI)')
- REPLACE | 두 집단의 조정 평균과 CI를 jamovi가 출력한 추정 주변 평균 그림  ->  두 집단의 조정 평균과 신뢰구간(CI)을 jamovi가 출력한 추정 주변
- REPLACE | <그림 4-2> 안전관리 실효성의 조정 평균과 95% 신뢰구간  ->  <그림 4-2> 안전관리 실효성의 조정 평균과 95% 신뢰구간(CI)
- DROP(base, replaced by block) | 집단 차이의 검정은 Type III 제곱합에 따른 F검정으로 하고, 차이의 크기는 부분 η²로 나타냈다. 부
- DROP(base, replaced by block) | 한편, 주 분석과 별도로 미리 정해 둔 추가 분석(민감도 분석)으로, 시스템 알림이 실제로 관리자의 위험 인
- DROP(base, replaced by block) | 통제변수를 조정한 집단 차이는 유의하여 연구가설 (1-1)은 지지되었다. 이 결과는 같은 시점에 조사한 관리
- REPLACE(block) | 두 집단의 차이가 통계적으로 의미 있는지는 F검정으로 확인하였다. 차이가 얼마나 큰지는 부분 η²로 나타냈다
- REPLACE(block) | 결과가 믿을 만한지 두 가지 방법으로 다시 확인하였다. 첫째, 도입 현장 가운데 관리자가 시스템 알림으로 위
- REPLACE(block) | 둘째, 일부 응답 때문에 결과가 달라지지 않는지 확인하였다(강건성 점검). 이 점검은 분석 후에 추가한 것이
- REPLACE(block) | 정리하면, 나이·경력 등 통제변수의 영향을 빼도 도입 현장의 점수가 미도입 현장보다 유의하게 높아 연구가설 
- REPLACE | 다섯 검정에는 Holm 보정을 적용하였다. Holm 보정은 여러 검정을   ->  다섯 검정에는 Holm 보정을 적용하였다. Holm 보정은 여러 검정을 
- REPLACE(table) | <표4-14> (표0 셀(0, 4) base '차이95%CI' ≠ fresh '차이95%신뢰구간(CI)')
- REPLACE | 제1항의 결과를 제5절 제2항에서 정한 판정 기준(도입−미도입 조정 차이  ->  제1항의 결과를 제5절 제2항에서 정한 판정 기준(도입−미도입 조정 차이
- REPLACE(table) | <표4-15> (표0 셀(0, 2) base '핵심추정·95%CI' ≠ fresh '핵심추정·95%신뢰구간(CI)')
- REPLACE | 연구가설 (1-1)("도입 현장 관리자가 지각한 안전관리 실효성은 여섯   ->  연구가설 (1-1)("도입 현장 관리자가 지각한 안전관리 실효성은 여섯 
- REPLACE | 실효성은 A공사 경기지역본부 산하 도입 현장 34명과 미도입 현장 39명  ->  실효성은 A공사 경기지역본부 산하 도입 현장 34명과 미도입 현장 39명
- REPLACE | [17] 이형도, 「객체탐지 알고리즘을 이용한 건설현장 근로자 안전모 실  ->  [17] 이형도, 「객체탐지 알고리즘을 이용한 건설현장 근로자 안전모 실
- REPLACE | [07] Green, D. M., & Swets, J. A., Signa  ->  [07] Green, D. M., & Swets, J. A., Signa
- REPLACE | [01] 「건설기술 진흥법」 제39조(건설사업관리 등의 시행)·제49조(  ->  [01] 「건설기술 진흥법」 제39조(건설사업관리 등의 시행)·제49조(
- TOC(section1) from fresh | 문단 159개, base section1 서식은 버림