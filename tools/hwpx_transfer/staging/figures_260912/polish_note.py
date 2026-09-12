from pathlib import Path
import zipfile,re,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment
old='자료: 기존 학회논문의 실제 운영 화면. 다중 카메라 모니터링과 LLM 판정 교정 장면이다.'
new='자료: 기존 학회논문의 실제 모니터링·판정 교정 화면.'
with zipfile.ZipFile(HERE/'final.hwpx') as z:infos=z.infolist();data={n:z.read(n) for n in z.namelist()}
sec=data['Contents/section2.xml'];assert sec.count(old.encode())==1
n=next(n for n in elements(sec) if n['name']=='hp:p' and old.encode() in fragment(sec,n));raw=fragment(sec,n).replace(old.encode(),new.encode())
raw=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',raw,flags=re.S)
data['Contents/section2.xml']=sec[:n['start']]+raw+sec[n['end']:]
with zipfile.ZipFile(HERE/'polished_candidate.hwpx','w') as z:
 for info in infos:z.writestr(info,data[info.filename])
p=ROOT/'01.docs/03_시스템개발.md';text=p.read_text(encoding='utf-8');assert old in text;p.write_text(text.replace(old,new),encoding='utf-8')
print('Shortened screenshot source note without changing its meaning.')
