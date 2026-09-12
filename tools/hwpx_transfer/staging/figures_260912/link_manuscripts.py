from pathlib import Path
import re,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
m=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
for filename in ['01_서론.md','03_시스템개발.md','04_연구설계.md']:
 p=ROOT/'01.docs'/filename;text=p.read_text(encoding='utf-8')
 for fig in m['figures']:
  no=fig['number'];caption=f'<그림 {no}> {fig["caption"]}'
  if caption not in text and caption.replace('<','&lt;').replace('>','&gt;') not in text:continue
  image=f'![{fig["caption"]}]({fig["png"].removeprefix("01.docs/")})'
  c=re.escape(caption).replace('<','(?:<|&lt;)').replace('>','(?:>|&gt;)')
  if no in ('1-3','4-1'):
   text,n=re.subn(r'```(?:text)?\n.*?```\n\n('+c+r')',lambda x:image+'\n\n'+x[1],text,count=1,flags=re.S)
  else:
   text,n=re.subn('('+c+r')\n\n\[그림 삽입 예정:[^\n]*\]',lambda x:image+'\n\n'+x[1],text,count=1)
  assert n==1,(filename,no)
  if no=='3-4':
   text=text.replace(image+'\n\n'+caption,image+'\n\n'+caption+'\n\n자료: 기존 학회논문의 실제 모니터링·판정 교정 화면.')
 for old,new in m['text_corrections']:text=text.replace(old,new)
 p.write_text(text,encoding='utf-8')
p=ROOT/'01.docs/07_참조번호목록.md';text=p.read_text(encoding='utf-8')
text=text.replace('2024 산업재해 현황분석(홈페이지).pdf (고용노동부, 2024)','2024 산업재해 현황분석(홈페이지).pdf (고용노동부, 2025)')
for old,new in m['text_corrections']:text=text.replace(old,new)
p.write_text(text,encoding='utf-8')
print('Linked 8 figures in MD; corrected source year and count/risk wording.')
