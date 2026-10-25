// LOCAL UPDATED COPY 2026-10-12: site-name revision. Not executed.
// complete-survey.gs retains the original browser-executed distribution-code version.
// Use site-name-update.txt for a targeted update of the populated existing form.
const FORM_ID = '1niBWDpkH31C7o9fWJf0uKhSTEXccIWtqmLfM6EsJ5Gw';
const SPEC = {
  "title": "중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: 도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로",
  "description": "안녕하십니까?\n\n경기대학교 공학대학원 건축·안전공학전공 석사과정에 재학 중인 윤혁입니다.\n\n먼저 건설현장의 안전관리를 위해 각자의 자리에서 애써 주시는 여러분께 깊은 감사의 말씀을 드립니다.\n\n본 설문은 건설현장의 안전관리 실태와 여건을 조사하여, AI 안전관제 시스템을 운용하는 현장과 운용하지 않는 현장의 안전관리 실효성 차이를 비교·분석하기 위한 학술 연구 자료를 수집하는 데 목적이 있습니다. 연구자는 비교 대상 시스템을 개발하였습니다. 안내받은 Google Forms 설문에서 직접 응답을 입력하거나 선택한 뒤 제출해 주십시오.\n\n응답에는 정답이 없으며, 귀하가 담당하시는 현장의 현재 안전관리 업무 수행 수준과 여건을 기준으로 느끼신 그대로 응답해 주시면 됩니다. 설문 참여는 자발적이며, 원하지 않으시면 참여하지 않으시거나 제출 전 언제든지 응답을 중단하실 수 있습니다. 현장 명부 연결과 중복 제출 확인을 위해 현장명과 성명을 수집하며, Google 계정 로그인은 요구하지 않으며 응답자 이메일은 수집하지 않습니다. 성명과 현장명이 포함된 원응답과 현장 명부는 연구자 본인만 열람합니다. 명부 대조 후 통계분석용 사본에서는 성명과 현장명을 제거하고 코드로 관리하며, 코드·성명·현장명 대응표와 현장 명부는 이 사본과 분리하여 보관·관리합니다. 개별 응답은 소속 기관이나 현장 관계자에게 공개하지 않으며, 학술 연구를 위한 통계 분석에만 사용하고 결과는 전체를 집계한 형태로 보고합니다.\n\n다소 번거로우시더라도 성실하게 응답해 주시면 본 연구에 큰 도움이 되겠습니다.\n\n2026년 10월\n\n소     속 : 경기대학교 공학대학원 건축·안전공학전공\n지도교수 : 박 종 용\n연 구 자 : 윤    혁\n이 메 일 : yoonhyeok1@gmail.com",
  "startTitle": "현장 구분 및 조사 안내",
  "startHelp": "※ Part A는 각 문항에 적힌 기준시점과 기간에 따라 응답해 주십시오. Part B·C는 도입·미도입 두 집단 모두 설문 응답일 직전 1개월 동안 귀하가 담당하시는 현장의 안전관리 업무 수행 수준과 여건을 기준으로 응답해 주십시오.\n\n※ 본 설문조사는 2026년 10월에 실시할 계획입니다.\n\n현장명과 성명은 현장 명부 연결과 중복 제출 확인에 사용하며, A∼E의 측정 문항 수(21문항 또는 33문항)에 포함하지 않습니다.",
  "groupTitle": "귀하가 담당하시는 현장은 도입현장입니까, 미도입현장입니까?",
  "groupHelp": "연구자로부터 안내받은 현장 구분에 따라 선택해 주십시오. 도입현장은 본 시스템을 설치하여 응답일 현재 3개월 이상 정상 운용이 확인된 현장, 미도입현장은 본 시스템을 설치·운용하지 않는 현장입니다. 이 선택은 해당 설문 문항으로 이동하기 위한 것으로, 분석용 집단 구분은 연구자가 확인한 현장 명부를 기준으로 합니다.",
  "adminHelp": "",
  "scale": [
    "① 전혀 그렇지 않다",
    "② 그렇지 않다",
    "③ 보통이다",
    "④ 그렇다",
    "⑤ 매우 그렇다"
  ],
  "parts": {
    "A": {
      "title": "Part A. 인구통계학적 특성 및 현장 운영 특성",
      "help": "※ 다음은 응답자의 일반적 사항과 현장 운영 특성에 관한 질문입니다. A-3·A-4는 숫자를 입력하고, 나머지 문항은 해당하는 보기를 선택해 주십시오.",
      "questions": [
        {
          "title": "A-1) 귀하의 소속 구분은?",
          "choices": [
            "시공사",
            "발주청(공사감독·감리원 포함)"
          ]
        },
        {
          "title": "A-2) 귀하의 성별은?",
          "choices": [
            "남성",
            "여성"
          ]
        },
        {
          "title": "A-3) 응답일 현재 귀하의 만 나이는?",
          "help": "만 나이(세)를 숫자로 입력해 주십시오.",
          "text": true,
          "integer": true
        },
        {
          "title": "A-4) 귀하의 건설현장 근무 경력은 약 몇 년입니까? (응답일까지 안전관리·공사감독·시공관리 등 현장 업무에 종사한 전체 기간)",
          "help": "경력(년)을 숫자로 입력해 주십시오.\n※ 1년 미만은 0으로, 6개월 이상은 1년으로 올려 적어 주십시오. 여러 현장이나 업무의 근무 기간이 겹치면 같은 기간을 중복하여 합산하지 마십시오.",
          "text": true,
          "integer": true
        },
        {
          "title": "A-5) 현장에서 귀하가 맡고 있는 역할은?",
          "choices": [
            "공사감독",
            "안전관리자",
            "현장소장"
          ],
          "other": true
        },
        {
          "title": "A-6) 현재 담당 현장의 총공사비 구간은?",
          "help": "※ 총공사비는 조사 대상으로 정한 현장 전체의 응답일 현재 최신 확정 금액(부가가치세와 관급자재비 포함)을 기준으로 응답해 주십시오. 확정된 변경 사항은 반영하고, 아직 확정되지 않은 추정액은 사용하지 마십시오.",
          "choices": [
            "20억 원 미만",
            "20억 원 이상∼50억 원 미만",
            "50억 원 이상∼120억 원 미만",
            "120억 원 이상"
          ]
        },
        {
          "title": "A-7) 안전관리 담당자가 현장에 없을 때(이동·사무실 업무·야간 등) 위험 상황을 알게 되는 주된 경로는 무엇입니까?",
          "help": "※ A-7∼A-9는 설문 응답일 직전 1개월 동안 귀하가 담당하시는 현장의 실제 상황을 기준으로 응답해 주십시오.\n※ A-7의 ‘안전관리 담당자’는 선임된 안전관리자뿐 아니라, 전담 안전관리자가 없는 현장에서 안전관리 업무를 맡는 분을 포함합니다.",
          "choices": [
            "알게 될 방법이 없다",
            "작업자나 반장의 전화·보고",
            "사무실 등에서 CCTV 화면을 직접 본다",
            "자동 알림(문자·메신저·앱)을 받는다"
          ],
          "other": true
        },
        {
          "title": "A-8) 비점검 시간에 생긴 위험 상황은 보통 언제 알게 됩니까?",
          "help": "※ A-7∼A-9는 설문 응답일 직전 1개월 동안 귀하가 담당하시는 현장의 실제 상황을 기준으로 응답해 주십시오.",
          "choices": [
            "다음 순찰 때",
            "누군가 알려줄 때",
            "발생 직후 알림으로",
            "모르고 지나가는 경우가 많다"
          ]
        },
        {
          "title": "A-9) 위험 상황을 알고 난 뒤 현장에 조치 지시가 전달되기까지 보통 얼마나 걸립니까?",
          "help": "※ A-7∼A-9는 설문 응답일 직전 1개월 동안 귀하가 담당하시는 현장의 실제 상황을 기준으로 응답해 주십시오.",
          "choices": [
            "즉시∼5분",
            "5분 초과∼30분",
            "30분 초과∼1시간",
            "1시간 초과 또는 다음 순찰 때"
          ]
        }
      ]
    },
    "B": {
      "title": "Part B. 안전관리 실효성",
      "help": "※ 다음 Part B의 모든 문항은 리커트 5점 척도입니다. 설문 응답일 직전 1개월을 기준으로, 순찰과 순찰 사이나 안전관리 담당자가 현장에 없는 시간대에 생긴 위험 상황까지 포함하여 각 문항을 읽고 귀하의 생각과 가장 가까운 보기를 선택해 주십시오. B-3의 ‘안전관리 담당자’는 선임된 안전관리자뿐 아니라, 전담 안전관리자가 없는 현장에서 안전관리 업무를 맡는 분을 포함합니다.\n (① 전혀 그렇지 않다 — ② 그렇지 않다 — ③ 보통이다 — ④ 그렇다 — ⑤ 매우 그렇다)",
      "questions": [
        {
          "title": "B-1) 우리 현장에서는 위험 상황을 조기에 인지한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-2) 우리 현장에서는 위험 상황을 인지하면 초동 대응을 빠르게 지시한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-3) 우리 현장에서는 안전관리 담당자가 현장 밖에서도 위험 상황을 신속하게 파악한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-4) 우리 현장에서는 멀리 떨어진 곳에서도 위험 정보와 조치 필요사항을 원활하게 공유한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-5) 우리 현장에서는 제한된 인력으로도 현장 순찰과 위험 확인 업무를 효율적으로 수행한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-6) 우리 현장에서는 불필요한 확인 업무에 쫓기지 않고 실제 위험 대응에 집중한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-7) 우리 현장에서는 필요한 경우 시정·작업중지 등 통제 조치를 신속하게 시행한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "B-8) 우리 현장에서는 사고로 이어질 수 있는 위험요인을 실질적으로 통제한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        }
      ]
    },
    "C": {
      "title": "Part C. 안전관리 예산 제약성",
      "help": "※ 다음 Part C의 모든 문항은 리커트 5점 척도입니다. 설문 응답일 직전 1개월을 기준으로 각 문항을 읽고 귀하의 생각과 가장 가까운 보기를 선택해 주십시오.\n (① 전혀 그렇지 않다 — ② 그렇지 않다 — ③ 보통이다 — ④ 그렇다 — ⑤ 매우 그렇다)",
      "questions": [
        {
          "title": "C-1) 우리 현장은 고가의 스마트 안전장비를 도입하기에는 예산이 부족하다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "C-2) 우리 현장은 스마트 안전장비나 관제 시스템 도입에 쓸 안전관리 예산이 부족하게 편성되어 있다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "C-3) 우리 현장은 산업안전보건관리비 계상 기준만으로는 스마트 안전장비나 관제 시스템을 도입하기 어렵다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "C-4) 우리 현장은 소속 기관인 본사나 발주청으로부터 스마트 안전장비나 관제 시스템 도입 예산을 별도로 지원받기 어렵다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        }
      ]
    },
    "D": {
      "title": "Part D. 시스템 특성 인식",
      "help": "다음은 CCTV YOLO-LLM 안전알림 시스템을 사용한 경험에 관한 질문입니다.\n\n※ Part D는 귀하가 직접 경험하신 내용을 바탕으로 리커트 5점 척도에 응답해 주십시오. D-1·D-2는 장비 구성·호환 경험, D-3은 알림이 짧은 시간에 몰린 상황, D-4는 통신 상태가 좋지 않은 상황, D-5·D-6은 알림 내용이 실제 위험과 맞는지 확인한 경험, D-7·D-8은 실제 알림 수신·활용 경험을 기준으로 응답해 주십시오.\n (① 전혀 그렇지 않다 — ② 그렇지 않다 — ③ 보통이다 — ④ 그렇다 — ⑤ 매우 그렇다)",
      "questions": [
        {
          "title": "D-1) 본 시스템은 일반 사무용 PC로 구동되어 고가 AI 서버 등 별도 장비에 대한 투자 부담이 적다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-2) 본 시스템은 제조사가 다른 기존 현장 카메라와도 호환되어 카메라를 교체하지 않고 도입할 수 있다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-3) 본 시스템은 짧은 시간에 알림이 몰려도 느려지거나 멈추지 않고 안정적으로 작동한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-4) 본 시스템은 통신 상태가 좋지 않은 현장에서도 위험 여부를 가려내는 기능이 안정적으로 작동한다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-5) 본 시스템은 현장의 나무나 그림자 같은 배경을 사람이나 위험 요소로 잘못 알리는 일이 드물다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-6) 본 시스템은 정상 작업을 위험으로 잘못 알리는 일이 드물다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-7) 위험 상황이 발생하면 위험 요약과 이미지가 모바일 메신저로 신속하게 전달된다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "D-8) 모바일 메신저로 받은 알림만으로도 현장 상황을 쉽게 파악할 수 있다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        }
      ]
    },
    "E": {
      "title": "Part E. 경보 피로도 완화",
      "help": "다음은 CCTV YOLO-LLM 안전알림 시스템을 사용한 경험에 관한 질문입니다.\n\n※ Part E에서는 비교 기간의 길이를 따로 정하지 않습니다. 현재 담당 현장에서 본 시스템 도입 전에 귀하가 직접 확인했던 자동 알림과 본 시스템을 사용하며 직접 확인한 알림에 대한 전반적인 경험을 비교하여 리커트 5점 척도에 응답해 주십시오.\n (① 전혀 그렇지 않다 — ② 그렇지 않다 — ③ 보통이다 — ④ 그렇다 — ⑤ 매우 그렇다)",
      "questions": [
        {
          "title": "E-1) 본 시스템이 위험이 아닌 상황을 걸러 주어 잦은 알림 확인에 따른 스트레스가 줄었다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "E-2) 불필요한 알림을 확인하는 시간이 줄어 핵심 업무에 더 집중하게 되었다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "E-3) 알림이 오면 ‘또 잘못 온 알림’으로 여겨 무시하기보다 바로 확인하는 경우가 늘었다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        },
        {
          "title": "E-4) 본 시스템 도입 이후 알림으로 인한 피로감이 줄었다.",
          "choices": [
            "① 전혀 그렇지 않다",
            "② 그렇지 않다",
            "③ 보통이다",
            "④ 그렇다",
            "⑤ 매우 그렇다"
          ]
        }
      ]
    }
  },
  "siteHelp": "현재 담당하시는 현장명을 적어 주십시오.\n예시 : 00지구 수리시설개보수사업"
};

function completeSurvey() {
  const f = FormApp.openById(FORM_ID);
  const initial = f.getItems();
  if (initial.length > 2 || initial[0].getTitle() !== '현장 구분') throw new Error('Safety guard: expected only the prepared question. No changes made.');
  f.setTitle(SPEC.title).setDescription(SPEC.description);
  f.setCollectEmail(false).setLimitOneResponsePerUser(false).setShuffleQuestions(false).setPublishingSummary(false);
  // Consumer Google accounts do not support setRequireLogin; verify login-free settings in Forms UI.
  const header = (initial.length === 2 ? initial[1].asSectionHeaderItem() : f.addSectionHeaderItem()).setTitle(SPEC.startTitle).setHelpText(SPEC.startHelp);
  f.moveItem(header.getIndex(), 0);
  const group = initial[0].asMultipleChoiceItem().setTitle(SPEC.groupTitle).setHelpText(SPEC.groupHelp).setRequired(true);
  [{title:'현장명',help:SPEC.siteHelp,text:true},{title:'성명',help:SPEC.adminHelp,text:true}].forEach(q => addQuestion(f,q));
  const pages = {};
  ['ADOPTED_A','ADOPTED_B','ADOPTED_C','ADOPTED_D','ADOPTED_E','NONADOPTED_A','NONADOPTED_B','NONADOPTED_C'].forEach(key => {
    const part = SPEC.parts[key.split('_')[1]];
    pages[key] = f.addPageBreakItem().setTitle((key.startsWith('NON') ? '미도입현장' : '도입현장') + ' · ' + part.title).setHelpText(part.help);
    part.questions.forEach(q => addQuestion(f,q));
  });
  group.setChoices([group.createChoice('CCTV YOLO-LLM 안전알림 도입 현장',pages.ADOPTED_A), group.createChoice('CCTV YOLO-LLM 안전알림 미도입 현장',pages.NONADOPTED_A)]);
  // PageBreak navigation applies to the PREVIOUS section.
  pages.NONADOPTED_A.setGoToPage(FormApp.PageNavigationType.SUBMIT);
  verifySurvey();
}

function addQuestion(f,q) {
  const item = q.text ? f.addTextItem() : f.addMultipleChoiceItem();
  item.setTitle(q.title).setRequired(true);
  if (q.help) item.setHelpText(q.help);
  if (q.text && q.integer) item.setValidation(FormApp.createTextValidation().requireTextMatchesPattern('^[0-9]+$').setHelpText('0 이상의 정수를 입력해 주십시오.').build());
  if (!q.text) { item.setChoiceValues(q.choices); if(q.other) item.showOtherOption(true); }
  return item;
}

function verifySurvey() {
  const f=FormApp.openById(FORM_ID), all=f.getItems();
  const questions=all.filter(i=>i.getType()===FormApp.ItemType.MULTIPLE_CHOICE || i.getType()===FormApp.ItemType.TEXT);
  const expected=[{title:SPEC.groupTitle,help:SPEC.groupHelp},{title:'현장명',help:SPEC.siteHelp,text:true},{title:'성명',help:SPEC.adminHelp,text:true},...['A','B','C','D','E','A','B','C'].flatMap(k=>SPEC.parts[k].questions)];
  if(questions.length!==57 || all.filter(i=>i.getType()===FormApp.ItemType.PAGE_BREAK).length!==8) throw new Error('Counts mismatch');
  if(f.getTitle()!==SPEC.title || f.getDescription()!==SPEC.description) throw new Error('Introduction mismatch');
  questions.forEach((i,n)=>{
    const q=expected[n], typed=q.text?i.asTextItem():i.asMultipleChoiceItem();
    if(i.getTitle()!==q.title || i.getHelpText()!==(q.help||'') || !typed.isRequired()) throw new Error('Text/required mismatch at '+n);
    if(q.choices && JSON.stringify(typed.getChoices().map(c=>c.getValue()))!==JSON.stringify(q.choices)) throw new Error('Choices mismatch at '+n);
    if(q.choices && typed.hasOtherOption()!==!!q.other) throw new Error('Other option mismatch at '+n);
  });
  const pages=all.filter(i=>i.getType()===FormApp.ItemType.PAGE_BREAK).map(i=>i.asPageBreakItem());
  const keys=['ADOPTED_A','ADOPTED_B','ADOPTED_C','ADOPTED_D','ADOPTED_E','NONADOPTED_A','NONADOPTED_B','NONADOPTED_C'];
  pages.forEach((p,n)=>{ const part=SPEC.parts[keys[n].split('_')[1]]; if(p.getTitle()!==(keys[n].startsWith('NON')?'미도입현장':'도입현장')+' · '+part.title || p.getHelpText()!==part.help) throw new Error('Section mismatch '+n); });
  const h=all[0]; if(h.getTitle()!==SPEC.startTitle || h.getHelpText()!==SPEC.startHelp) throw new Error('Start section mismatch');
  const branches=questions[0].asMultipleChoiceItem().getChoices().map(c=>({answer:c.getValue(),page:c.getGotoPage().getTitle()}));
  if(branches[0].page!==pages[0].getTitle() || branches[1].page!==pages[5].getTitle() || pages[5].getPageNavigationType()!==FormApp.PageNavigationType.SUBMIT) throw new Error('Branch mismatch');
  console.log(JSON.stringify({sections:9,totalQuestions:questions.length,measurementQuestions:54,adoptedQuestions:36,nonadoptedQuestions:24,allTextAndChoicesMatch:true,allRequired:true,branches:branches,afterAdoptedE:String(pages[5].getPageNavigationType()),collectEmail:f.collectsEmail(),limitOne:f.hasLimitOneResponsePerUser(),shuffle:f.getShuffleQuestions(),summaryPublic:f.isPublishingSummary(),progressBar:f.hasProgressBar(),quiz:f.isQuiz(),confirmationMessage:f.getConfirmationMessage(),responseCount:f.getResponses().length,editUrl:f.getEditUrl(),respondentUrl:f.getPublishedUrl()},null,2));
}


function finalizeSurvey() {
  const f=FormApp.openById(FORM_ID);
  const questions=f.getItems().filter(i=>i.getType()===FormApp.ItemType.MULTIPLE_CHOICE || i.getType()===FormApp.ItemType.TEXT);
  if(questions.length!==57) throw new Error('Expected exactly 57 questions; no new items will be created.');
  const expected=[{title:SPEC.groupTitle,help:SPEC.groupHelp},{title:'현장명',help:SPEC.siteHelp,text:true},{title:'성명',help:SPEC.adminHelp,text:true},...['A','B','C','D','E','A','B','C'].flatMap(k=>SPEC.parts[k].questions)];
  const repairs=[];
  questions.forEach((i,n)=>{
    const q=expected[n], typed=q.text?i.asTextItem():i.asMultipleChoiceItem();
    if(i.getTitle()!==q.title) { typed.setTitle(q.title); repairs.push('title '+n); }
    if(i.getHelpText()!==(q.help||'')) { typed.setHelpText(q.help||''); repairs.push('help '+n); }
    if(!typed.isRequired()) typed.setRequired(true);
    if(q.choices && JSON.stringify(typed.getChoices().map(c=>c.getValue()))!==JSON.stringify(q.choices)) { typed.setChoiceValues(q.choices); repairs.push('choices '+n); }
    if(q.choices && typed.hasOtherOption()!==!!q.other) typed.showOtherOption(!!q.other);
    if(q.integer) typed.setValidation(FormApp.createTextValidation().requireTextMatchesPattern('^[0-9]+$').setHelpText('0 이상의 정수를 입력해 주십시오.').build());
  });
  const pages=f.getItems(FormApp.ItemType.PAGE_BREAK).map(i=>i.asPageBreakItem());
  const group=questions[0].asMultipleChoiceItem();
  group.setChoices([group.createChoice('도입현장',pages[0]),group.createChoice('미도입현장',pages[5])]);
  pages[5].setGoToPage(FormApp.PageNavigationType.SUBMIT);
  f.setCollectEmail(false).setLimitOneResponsePerUser(false).setShuffleQuestions(false).setPublishingSummary(false);
  f.setProgressBar(true).setIsQuiz(false).setConfirmationMessage('끝까지 응답해 주셔서 진심으로 감사합니다.');
  console.log('Repairs: '+JSON.stringify(repairs));
  verifySurvey();
}
