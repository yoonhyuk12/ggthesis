from pathlib import Path
import sys,zipfile,xml.etree.ElementTree as E,re,json,hashlib,collections
W=Path('tools/hwpx_transfer/staging/survey_261028');H='{http://www.hancom.co.kr/hwpml/2011/paragraph}';HH='{http://www.hancom.co.kr/hwpml/2011/head}'
base=next(Path('00. hwpx').glob('261028_0644*'));final=Path(sys.argv[1])
def roots(p):
 z=zipfile.ZipFile(p);return z,[E.fromstring(z.read(f'Contents/section{i}.xml')) for i in range(3)]
bz,br=roots(base);fz,fr=roots(final);pz,pr=roots(W/'patched_toc.hwpx')
def text(p):return ''.join(''.join(t.itertext()) for t in p.iter(H+'t'))
def own(p):return ''.join(''.join(t.itertext()) for t in p.findall(H+'run/'+H+'t'))
norm=lambda s:re.sub(r'\s+','',s)
results={}
def check(k,v):results[k]=v;assert v,k
for i in range(3):check(f'section{i}_text_equal',text(fr[i])==text(pr[i]))
start=next(i for i,p in enumerate(fr[2]) if '부   록 (도입 현장)' in own(p));body=''.join(text(p) for p in list(fr[2])[:start]);apx=''.join(text(p) for p in list(fr[2])[start:])
check('body_old_zero',all(x not in body for x in ['Google Forms','설문 링크','단일 링크','Google 계정 로그인은 요구하지 않았고','개별 대조','제출시각이 10분 이내','조사는 2026년 10월 Google','2026년 10월에 사후 설문']))
check('merged_paragraph',body.count('자료 정제와 채점은 제3절 제1항과')==1 and not any(own(p).strip().startswith('자료 정제와 채점은') for p in fr[2]))
check('appendix_old_zero',all(x not in apx for x in ['배포코드','18문항 또는 30문항','비해당','개월은 연수를 제외한']))
md=Path('01.docs/부록1_설문지_양식.md').read_text(encoding='utf-8');expected=[]
for s in md.splitlines():
 s=s.replace('**','').replace('&emsp;',' ').strip()
 if s.startswith('## [내부'):break
 if not s or s.startswith(('#','>','<','---','|')):continue
 if s.startswith('- '):s=s[2:]
 expected.append(s)
check('all_MD_prose_options_present',all(norm(s) in norm(apx) for s in expected))
codes={}
for p in list(fr[2])[start:]:
 for q in p.iter(H+'p'):
  t=own(q).strip()
  if re.match(r'A-[1-9]\)',t):codes[t.split(')')[0]]=codes.get(t.split(')')[0],0)+1
 for tr in p.iter(H+'tr'):
  cs=tr.findall(H+'tc')
  if len(cs)>1 and re.fullmatch(r'[BCDE]-\d+',text(cs[0]).strip()):
   c=text(cs[0]).strip();codes[c]=codes.get(c,0)+1
   row=next(s for s in md.splitlines() if s.startswith('| '+c+' |'));question=row.split('|')[2].strip()
   check(c+'_question_'+str(codes[c]),text(cs[1]).strip()==question)
check('question_counts',all(codes.get(f'{letter}-{i}')==(2 if letter in 'ABC' else 1) for letter,n in [('A',9),('B',8),('C',4),('D',8),('E',4)] for i in range(1,n+1)))
check('thanks_two',apx.count('끝까지 응답해 주셔서 진심으로 감사합니다.')==2)
for label in ['현장 구분(전자 설문 첫 질문)','현장명: [입력]','성명: [입력]','※ A-7∼A-9','※ A-7의']:
 check(label+'_two',apx.count(label)==2)
def tablemap(r):
 out={};cap=''
 for p in r:
  t=own(p).strip()
  if re.match(r'^<표\s*\d+-\d+>',t):cap=t.split('>')[0]+'>'
  for tb in p.findall('.//'+H+'tbl'):
   out.setdefault(cap,[]).append(tb)
 return out
bm,fm=tablemap(br[2]),tablemap(fr[2])
def geometry(t):return (t.get('rowCnt'),t.get('colCnt'),t.find(H+'sz').get('width'),[(c.find(H+'cellAddr').attrib,c.find(H+'cellSpan').attrib,c.find(H+'cellSz').get('width')) for c in t.findall(H+'tr/'+H+'tc')])
for n in [7,10,11,12,13,14]:
 key=f'<표 4-{n}>';check(key+'_geometry',list(map(geometry,bm[key]))==list(map(geometry,fm[key])) if n!=14 else list(map(geometry,bm[key]))==list(map(geometry,fm[key])))
for tb in [t for p in list(fr[2])[start:] for t in p.iter(H+'tbl')]:
 if re.search(r'[DE]-1',text(tb)) and any(text(c).strip() in ['D-1','E-1'] for c in tb.findall(H+'tr/'+H+'tc')):
  check('DE_'+text(tb)[:10],tb.get('colCnt')=='7' and all(sum(int(c.find(H+'cellSz').get('width')) for c in tr.findall(H+'tc'))==39491 for tr in tb.findall(H+'tr')))
check('no_CELL',all(t.get('pageBreak')!='CELL' for r in fr for t in r.iter(H+'tbl')))
def colors(z,rr):
 hd=E.fromstring(z.read('Contents/header.xml'));cs={x.get('id'):x.get('textColor') for x in hd.iter(HH+'charPr')};counts=collections.Counter();redtotal=0;inputs=[]
 for r in rr:
  for run in r.iter(H+'run'):
   t=''.join(''.join(q.itertext()) for q in run.findall(H+'t'));red=cs.get(run.get('charPrIDRef'))=='#FF0000'
   if red:redtotal+=1
   for prefix in ['[확정 필요','[CITE_TODO','[UNVERIFIED','[DATA PENDING','[그림 삽입 예정','실험전']:
    if red:counts[prefix]+=t.count(prefix)
   if '[입력]' in t:inputs.append(not red)
 return dict(counts),redtotal,inputs
bc,bt,_=colors(bz,br);fc,ft,inputs=colors(fz,fr)
check('marker_counts_equal',bc==fc and bt==ft);check('input_black',len(inputs)>=4 and all(inputs));results['markers']={'base':bc,'final':fc,'red_runs':[bt,ft]}
check('other_author_zero',all(x not in ''.join(text(r) for r in fr) for x in ['안전시설물','떨어짐 사고위험','김정년']))
check('base_sha',hashlib.sha256(base.read_bytes()).hexdigest()=='eddab53be59038e36822640f7bfc6c3a1f1f5674b45ddbf614c3d66bb3130f18')
check('template_sha',hashlib.sha256((W/'template_kjn.hwpx').read_bytes()).hexdigest()=='9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3')
(W/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',len(results),'checks',results['markers'])
