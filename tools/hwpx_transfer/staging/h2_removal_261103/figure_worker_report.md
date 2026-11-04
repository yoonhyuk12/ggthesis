# 그림·jamovi 캡처 워커 완료 보고 (2026-11-03)

## 변경 및 시각 검증

- `generate_research_figures.py` model()을 X·Y·C 제목띠 상자와 검정 실선 화살표 2개로 교체했다. W 상자·화살표, 기존 H1/H2 구획, 내부 캡션이 없다. 글자 겹침·잘림 없이 한글이 정상이고 C·Y 상자 사이 여백도 확인했다.
- 연구모형 PNG/SVG를 재생성하고 동일 PNG를 `figure_4-1_research_model_261103.png`로 복사했다. 261029 원본과 figure_1-3 파일은 변경하지 않았다.
- 흐름도 제2장에 H1만 남겼으며 제4장 H2 분석을 삭제했다. ANCOVA → Holm 보정 → 지지·기각 판정을 두 줄로 배치하여 줄 수와 높이는 유지했다. 한글·여백·화살표·글자 잘림 여부를 이미지로 확인했다.
- 표4-10 캡처 원본을 `_before_261103.png`로 보존했다. 원본 W 글자 시작은 y=1193, Y5 최종 숫자 픽셀은 y=1139다. y=1175 이전을 보존(아래 흰 여백 35px)하고 원본 하단 괘선 y=1329~1334를 붙였다. 브리프의 이중 괘선은 실제 이미지에서는 연속된 6px 띠로 관찰되어 그 픽셀을 그대로 보존했다. 결과 1719×1181px, 마지막 행 Y5의 `1 34 4.25`와 하단 괘선을 이미지로 확인했다.
- 본문 manifest height_mm: 111.2 → 98.4 (111.2 × 1181 / 1335, 소수 1자리). width_mm=143.2, fits_width=false 유지.
- 부표 manifest 원본을 `manifest_before_261103.json`으로 보존하고 지정 cell 10개 및 부표 3-5 항목을 제거했다. 지정 PNG 10개 삭제, 나머지 이름 유지.
- 제작 report.md 최상단에 요청 메모만 추가했다. 그 외 원고 MD·HWPX·분석단위·통계 원자료는 수정하지 않았다.

## 실행 및 검증 증거

`python 01.docs/figures/research/generate_research_figures.py` exit 0:

```text
figure_1-1_research_flow.png (1772, 2232) (299.9994, 299.9994)
figure_1-3_research_flow.png (1772, 2114) (299.9994, 299.9994)
figure_4-1_research_model.png (1772, 921) (299.9994, 299.9994)
figure_4-1_research_model_261029.png (1774, 887) None
figure_4-1_research_model_261103.png (1772, 921) (299.9994, 299.9994)
```

마지막 glob 출력에는 읽기만 한 기존 PNG도 포함된다.

```text
json.load OK: 본문/manifest.json
json.load OK: 부표/manifest.json
```

`Get-ChildItem -LiteralPath 01.docs/설문결과/자모비캡쳐/부표 -Filter *.png` 확인 결과:

```text
부표3-1_01.png ~ 부표3-1_04.png
부표3-2_01.png ~ 부표3-2_04.png
부표3-3_01.png, _02.png, _05.png, _06.png, _07.png, _08.png, _10.png
부표3-4_01.png ~ 부표3-4_10.png
```

지정 삭제 대상 3-2의 05~08, 3-3의 03·04·09·11, 3-5의 01·02는 없다.

`git -c core.quotepath=false status --short -- 01.docs/figures 01.docs/설문결과/자모비캡쳐`:

```text
 M 01.docs/figures/research/figure_1-1_research_flow.png
 M 01.docs/figures/research/figure_1-1_research_flow.svg
 M 01.docs/figures/research/figure_4-1_research_model.png
 M 01.docs/figures/research/figure_4-1_research_model.svg
 M 01.docs/figures/research/generate_research_figures.py
 M 01.docs/figures/research/report.md
?? 01.docs/figures/research/figure_4-1_research_model_261103.png
?? 01.docs/설문결과/자모비캡쳐/
```

## Advisor 참고

본문 manifest의 표 4-10 title에는 기존 `안전관리 실효성과 안전관리 예산 제약성의 기술통계 jamovi 출력`이 남아 있다. 브리프가 지정한 height_mm 외 메타데이터는 바꾸지 않았으므로 제목의 후속 정합 여부를 판단하면 된다. 본 작업의 요청 항목은 완료했다.

흐름도 통합 문장의 실측 폭은 1419.8 단위이며 x=80에서 오른쪽 끝 1499.8로 캔버스 폭 assert는 통과하지만 상자 오른쪽 테두리 1455를 넘으므로 두 줄로 배치했다.
