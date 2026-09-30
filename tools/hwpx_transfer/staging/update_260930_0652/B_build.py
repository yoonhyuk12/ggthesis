# 변경 명세 B(제4~6장·참고문헌·부록1 본문 최상위 문단) 생성기 — prose_B.json을 만든다
import json, re, sys, io
from B_util import S2, BY, NB, OB, btext

SEC = 'Contents/section2.xml'
K4, K5, K6, KA = '04_연구설계.md', '05_실증분석결과.md', '06_결론.md', '부록1_설문지_양식.md'
MD_REF = '01.docs/07_참조번호목록.md'


def lead(s):
    return re.match(r'^[  　]*', s).group(0)


def nb(key, i):
    return btext(NB[key][i])


replace, delete, insert, coverage, user_edits = [], [], [], [], []


def rep(idx, key, bi, note=''):
    old = BY[idx]['text']
    new = lead(old) + nb(key, bi)
    replace.append({'section': SEC, 'idx': idx, 'old': old, 'new': new})
    coverage.append({'md': key, 'block': bi, 'op': 'replace', 'idx': idx, 'status': 'transferred', 'note': note})


def ins(anchor, pos, order, tmpl, key, bi, note=''):
    insert.append({'section': SEC, 'anchor_idx': anchor, 'position': pos, 'order': order,
                   'template_idx': tmpl, 'text': nb(key, bi)})
    coverage.append({'md': key, 'block': bi, 'op': 'insert', 'idx': anchor, 'status': 'transferred',
                     'note': f'{pos} {anchor} #{order}' + (f'; {note}' if note else '')})


def ins_text(anchor, pos, order, tmpl, text, src, note=''):
    insert.append({'section': SEC, 'anchor_idx': anchor, 'position': pos, 'order': order,
                   'template_idx': tmpl, 'text': text})
    coverage.append({'md': MD_REF, 'block': src, 'op': 'insert', 'idx': anchor, 'status': 'transferred',
                     'note': f'{pos} {anchor} #{order}' + (f'; {note}' if note else '')})


def dele(idx, note=''):
    delete.append({'section': SEC, 'idx': idx, 'old': BY[idx]['text']})


# ---------------- 제4장 ----------------
ins(746, 'after', 1, 746, K4, 7, '제1절 비교 조건 한정 문단 신설')
rep(781, K4, 19, '굵은 문단(charPr 10) 유지')
rep(782, K4, 20, '굵은 문단(charPr 10) 유지')
rep(783, K4, 21)
rep(812, K4, 33, '말미 [확정 필요] 빨강 유지')
rep(822, K4, 41)
ins(868, 'before', 1, 1002, K4, 45, '<표 4-3> 뒤 주석; 표 앵커 824는 C 소유라 868 앞에 삽입')
rep(878, K4, 53, "앞머리 '3단계. 전문가 필수성 평정.' 굵게, [확정 필요] 빨강")
rep(879, K4, 54, "앞머리 '4단계. 인지면접·예비조사 및 채점안 고정.' 굵게, [확정 필요] 빨강")
rep(883, K4, 56)
rep(945, K4, 61)
rep(1002, K4, 67)
for o, bi in enumerate((80, 81, 82), 1):
    ins(1088, 'after', o, 1090, K4, bi, '등록 90개소·108대 후보 명부')
for o, bi in enumerate((85, 86), 1):
    ins(1090, 'after', o, 1090, K4, bi, '비교 조건 기록·연구자 역할 안내')
rep(1123, K4, 97)

# ---------------- 제5장 ----------------
ins(1142, 'before', 1, 1143, K5, 4, '등록 90개소에서 표본 선정 경로')
rep(1142, K5, 5, '실험전 6+2자리 빨강(대괄호 없음), 말미 [DATA PENDING] 빨강')
rep(1345, K5, 14)
rep(1628, K5, 33, '실험전 빨강')
rep(1629, K5, 34, '실험전 빨강')
rep(1630, K5, 35, '실험전 빨강')
ins(1689, 'after', 1, 1634, K5, 42, '현장 단위 인프라·운용 조건 분포')
rep(1863, K5, 62, '실험전 빨강')
rep(1972, K5, 75, '실험전 빨강')
rep(2054, K5, 82, '실험전 빨강')
rep(2069, K5, 85, '실험전 빨강')
# 제6절 제2항 논의: old 6문단(2101~2106) → new 8문단(94~101), 순서대로 치환 후 2문단 삽입
for idx, bi in zip(range(2101, 2107), range(94, 100)):
    rep(idx, K5, bi, '제5장 제6절 제2항 논의 재작성')
ins(2106, 'after', 1, 2106, K5, 100, '제5장 제6절 제2항 논의 재작성')
ins(2106, 'after', 2, 2106, K5, 101, '제5장 연결 길잡이 문장')

# ---------------- 제6장: 절 구조 없는 8문단으로 압축 ----------------
keep6 = [2151, 2153, 2154, 2156, 2158, 2159, 2160, 2161]
for idx, bi in zip(keep6, range(1, 9)):
    rep(idx, K6, bi, '제6장 압축(절 제목 삭제)')
for p in S2:
    if 2110 <= p['idx'] <= 2170 and p['top_level'] and p['idx'] not in keep6:
        dele(p['idx'])
coverage.append({'md': K6, 'block': 'old 1-44', 'op': 'delete', 'idx': '2110-2170 (치환 8문단 제외)',
                 'status': 'transferred', 'note': f'제1~5절 제목·빈 줄·구 본문 {len(delete)}문단 삭제, 2109·2171 빈 줄 유지'})

# ---------------- 참고문헌: 07 골격의 변경분(4건) ----------------
ins_text(2178, 'after', 1, 2175,
         '류수영, 「CCTV 기반 산업안전 관제 시스템에 관한 연구」, 배재대학교 대학원 컴퓨터공학과 박사학위논문, 2023.',
         '골격 1. 국내문헌 류수영', '가. 학위논문, 김현수 뒤·박종학 앞(가나다)')
ins_text(2194, 'after', 1, 2197,
         'Chong, H.-Y., Xu, Y., Lun, C., & Chi, M., "The Adoption Intentions of Wearable Technology for Construction Safety", Buildings, Vol. 13, 2023, 2747. DOI 10.3390/buildings13112747.',
         '골격 2. 국외문헌 Chong', '나. 학술지, 류정·박인선 뒤·Cvach 앞(알파벳)')
ins_text(2205, 'after', 1, 2205,
         'Zhou, Z.-C., Su, Y.-K., Zheng, Z.-Z., & Wang, Y.-L., "Analysis of factors of willingness to adopt intelligent construction technology in highway construction enterprises", Scientific Reports, Vol. 13, 2023, 19339. DOI 10.1038/s41598-023-46241-6.',
         '골격 2. 국외문헌 Zhou', '나. 학술지 끝(Zeschky 뒤)')
ins_text(2209, 'after', 1, 2208,
         '김민기·박성호, 『서울시 재난안전관리 지원 생성형 AI 구축과 활용 방안』, 서울연구원, 2026.',
         '골격 1. 국내문헌 김민기·박성호', '다. 보고서, 국토교통부 뒤(가나다); 골격 괄호의 관리번호 주석 제외')

# ---------------- 부록1: 최상위 문단 ----------------
rep(2270, KA, 49, "도입 양식 Part B 안내; '리커트 5점 척도' 굵게 유지")
rep(2541, KA, 49, "미도입 양식 Part B 안내; '리커트 5점 척도' 굵게 유지")
for bi, cells in ((7, (2235, 2507)), (8, (2236, 2508))):
    coverage.append({'md': KA, 'block': bi, 'op': 'handoff_C', 'idx': list(cells), 'status': 'handoff_C',
                     'note': '표지 안내문이 표(도입 table_idx 40, 미도입 47) 셀 안 문단이므로 C 소유'})
for bi, cells in ((21, (2507,)), (22, (2508,))):
    coverage.append({'md': KA, 'block': bi, 'op': 'handoff_C', 'idx': list(cells), 'status': 'handoff_C',
                     'note': '미도입 양식 표지 안내문(7·8과 동일 문구), 표 47 셀 안'})

# ---------------- HWPX에만 있는 내용(보존) ----------------
def ue(idx, kind, note):
    user_edits.append({'section': SEC, 'idx': idx, 'text': BY[idx]['text'] if isinstance(idx, int) else None,
                       'kind': kind, 'action': 'preserve', 'note': note})

for idx in (2177, 2178, 2179, 2180, 2181, 2183, 2184, 2190, 2195, 2196, 2200, 2201, 2202, 2204, 2208, 2209, 2214, 2218, 2219, 2222):
    ue(idx, 'ref_prefix', '07 골격에 없는 [NN] 구분별 번호 접두사. 신규 4건은 접두사 없이 삽입하므로 번호 체계 일관성은 메인 판단 필요(삭제하지 않음)')
ue(2187, 'ref_text', "조도빈 소속 표기 '울산대학교 건축학과 공학박사학위논문' — 07 골격(구·현행 동일)은 '울산대학교 대학원 공학박사학위논문'. 골격 변경분이 아니므로 유지")
ue(2203, 'ref_text', 'Wilson(1927) 전체 서지 — 07 골격은 약식(Wilson, JASA ...). 골격 변경분이 아니므로 유지')
ue(2222, 'ref_text', "Wu et al. 제목의 'Vision-Language'(하이픈) — 07 골격은 줄표(–). 변경분 아님, 유지")
ue(2250, 'appendix', "부록 Part A 표 안 제목 'A. 실태조사 대상자 개요'(표 42·미도입 49) — MD에 없음. C 소유 표 셀, 유지")
ue(2521, 'appendix', "미도입 양식의 'A. 실태조사 대상자 개요' — 위와 동일")
ue(2382, 'appendix', "'도입 현장 전용부' — MD h1은 '도입 현장 전용부 — 도입 현장용 양식에만 싣는다'(편집 지시문 제거형). 구·현행 MD 동일, 유지")
user_edits.append({'section': SEC, 'idx': None, 'text': None, 'kind': 'appendix_omission', 'action': 'preserve',
                   'note': "MD 부록1의 '[확정 필요: 설문 실시 월, 두 집단 공통 기준기간, 도입 현장 최소 운용 기간]'(블록 31)과 '※ 다음은 응답자의 일반적 사항…'(블록 33)이 HWPX 부록에 없다. 구 MD(f5588d2)에도 있던 문단이라 이번 변경분이 아니며 HWPX의 기존 편집으로 보고 추가하지 않음"})

out = {'replace': replace, 'delete': delete, 'insert': insert, 'user_edits': user_edits, 'coverage': coverage}
json.dump(out, open('prose_B.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('replace', len(replace), 'delete', len(delete), 'insert', len(insert), 'user_edits', len(user_edits), 'coverage', len(coverage))
