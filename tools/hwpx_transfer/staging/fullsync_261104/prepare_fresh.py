"""Main-only comparison assembly. Does not modify the user's baseline."""
from pathlib import Path
import sys,json,re,shutil,argparse
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];TOOL=ROOT/'tools/hwpx_transfer'
sys.path.insert(0,str(TOOL))
import md_to_blocks as m,blocks_to_hwpx as b,kjn_profile as k
def rel(x):return x.relative_to(ROOT).as_posix()
def paragraphs(text):return [re.sub(r'\*\*|`','',x.strip()) for x in re.split(r'\n\s*\n',text) if x.strip() and not x.lstrip().startswith(('#','>','---'))]
front=(ROOT/'01.docs/00_목차.md').read_text(encoding='utf8')
kr=paragraphs(front.split('## 2. 국문초록',1)[1].split('---',1)[0])
en=paragraphs(front.split('## 6. Abstract',1)[1])
thanks=paragraphs((ROOT/'01.docs/감사의_글.md').read_text(encoding='utf8'))
k.parse_abstract_skeleton=lambda _:kr
refmd=(ROOT/'01.docs/07_참조번호목록.md').read_text(encoding='utf8').split('## 참고문헌(현행 인용 목록)',1)[1].split('### 6.',1)[0]
categories={};audit=[];cat=None
for line in refmd.splitlines():
 line=line.strip()
 if line.startswith('### '):cat=re.sub(r'\([^)]*\)','',line[4:]).strip();categories[cat]=[];continue
 if not cat or not line or line.startswith(('>','- ','#')):continue
 original=line
 if '(서울연 ' in line:line=re.sub(r';\s*ref\s*\d+(?=\))','',line)
 # Metadata parentheses are authoring records, not bibliography fields.
 starts=list(re.finditer(r'\((?:ref\b|서지관리번호|존재 검증|제[1-5]장|3장 1차|연도:|열람일)',line))
 for match in reversed(starts):
  start=match.start();depth=0;end=None
  for j in range(start,len(line)):
   if line[j]=='(':depth+=1
   elif line[j]==')':
    depth-=1
    if depth==0:end=j+1;break
  if end:line=line[:start]+line[end:]
 if cat.startswith('3.') and ' — ' in line:
  url=re.search(r'https?://[^\s]+',line);line=line.split(' — ',1)[0]+(' '+url.group() if url else '')
 if line.startswith('EN 50136-1:2012'):
  line=line.split(' 공식 서지:',1)[0]
 line=line.replace('**','').strip()
 categories[cat].append({'text':line,'original_text':original})
 audit.append({'category':cat,'original':original,'output':line})
categories={c:v for c,v in categories.items() if v}
(OUT/'references.json').write_text(json.dumps({'categories':categories,'flagged':[]},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'reference_filter_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
shutil.copy2(TOOL/'staging/hwpx_261031b/template.hwpx',OUT/'template.hwpx')
images={'mapping':[{'caption_prefix':'<그림 1-1>','source':'01.docs/figures/research/figure_1-1_research_flow.png'}]};files=[]
for num,name in [(1,'01_서론.md'),(2,'02_이론적배경.md'),(3,'03_시스템개발.md'),(4,'04_연구설계및실증분석.md'),(5,'05_논의및결론.md')]:
 blocks=m.parse_file(name)[1];file=OUT/f'ch{num:02}.blocks.json';file.write_text(json.dumps({'source':name,'blocks':blocks},ensure_ascii=False,indent=2),encoding='utf8');files.append(rel(file))
 for fig in k.group_figures(blocks):
  if fig.get('type')=='_figure' and fig.get('image_md') and fig.get('caption'):images['mapping'].append({'caption_prefix':fig['caption'].split('>')[0]+'>','source':'01.docs/'+fig['image_md'][1]})
(OUT/'images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2),encoding='utf8')
args=argparse.Namespace(template=rel(OUT/'template.hwpx'),profile=rel(TOOL/'staging/migrate_kjn/style_map_kjn.json'),blocks=files,references=rel(OUT/'references.json'),images=rel(OUT/'images.json'),transplant=None,toc_pages=None,front_md=rel(ROOT/'01.docs/00_목차.md'),output=rel(OUT/'assembled.hwpx'),report=rel(OUT/'report.md'),no_tail=True,smoke=False)
profile=k.load_profile(json.loads((ROOT/args.profile).read_text(encoding='utf8')),args.profile)
doc,tpl,sections,_=b.assemble_kjn(args,profile,str(TOOL))
doc.toc.append((1,'Abstract'));doc._add(doc.asm.text_para(doc.spec('abstract_heading'),'Abstract',page_break=True))
for i,text in enumerate(en):doc._add(doc.asm.text_para(doc.spec('abstract_meta' if i==0 else 'abstract_body'),text))
thanksxml=[]
thanksxml += [doc.asm.text_para(doc.spec('abstract_body'),text) for text in thanks]
sections['Contents/section1.xml']=doc.build_section1(thanks_xml=thanksxml,abstract_kr=kr)
sections['Contents/section2.xml']=doc.build_section2()
entries=k.plan_package(tpl,sections,tpl.header.xml,doc.bin_items)
b.write_package(args.output,entries,(2026,11,4,0,0,0))
print('Comparison assembly written; refs',sum(map(len,categories.values())),'KR/EN/thanks',len(kr),len(en),len(thanks))
