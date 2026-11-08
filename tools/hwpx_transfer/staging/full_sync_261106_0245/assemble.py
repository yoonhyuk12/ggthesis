from pathlib import Path
import sys,json,re,argparse
O=Path(__file__).parent;sys.path.insert(0,'tools/hwpx_transfer')
import blocks_to_hwpx as b,kjn_profile as k
import table_merges,copy
_original_layout=table_merges.apply_layout
def normalized_layout(xml,block,*a,**kw):
 block=copy.deepcopy(block)
 block['header']=[re.sub(r'<br\s*/?>','',x) for x in block['header']]
 block['rows']=[[re.sub(r'<br\s*/?>','',x) for x in row] for row in block['rows']]
 return _original_layout(xml,block,*a,**kw)
table_merges.apply_layout=normalized_layout
front=Path('01.docs/00_목차.md').read_text(encoding='utf8')
def paras(t):return [re.sub(r'\*\*|`','',x.strip()) for x in re.split(r'\n\s*\n',t) if x.strip() and not x.lstrip().startswith(('#','>','---'))]
kr=paras(front.split('## 2. 국문초록',1)[1].split('---',1)[0]);en=paras(front.split('## 6. Abstract',1)[1]);k.parse_abstract_skeleton=lambda _:kr
images={'mapping':[]}
for n in range(1,6):
 for fig in k.group_figures(json.loads((O/f'ch{n:02}.blocks.json').read_text(encoding='utf8'))['blocks']):
  if fig.get('type')=='_figure' and fig.get('image_md') and fig.get('caption'):images['mapping'].append({'caption_prefix':fig['caption'].split('>')[0]+'>','source':'01.docs/'+fig['image_md'][1]})
(O/'images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2),encoding='utf8')
args=argparse.Namespace(template=str(O/'template.hwpx'),profile='tools/hwpx_transfer/staging/migrate_kjn/style_map_kjn.json',blocks=[str(O/f'ch{i:02}.blocks.json') for i in range(1,6)]+[str(O/'apx1.blocks.json')],references=str(O/'references.json'),images=str(O/'images.json'),transplant=str(O/'transplant.json'),toc_pages=None,front_md='01.docs/00_목차.md',output=str(O/'fresh.hwpx'),report=str(O/'assembly_report.md'),no_tail=True,smoke=False)
pf=k.load_profile(json.loads(Path(args.profile).read_text(encoding='utf8')),args.profile)
doc,tpl,sections,_=b.assemble_kjn(args,pf,str(Path('tools/hwpx_transfer').resolve()))
doc.toc.append((1,'Abstract'));doc._add(doc.asm.text_para(doc.spec('abstract_heading'),'Abstract',page_break=True))
for i,t in enumerate(en):doc._add(doc.asm.text_para(doc.spec('abstract_meta' if i==0 else 'abstract_body'),t))
# Preserve current thanks in comparison too, only abstract gets current MD prose.
thanks,_,_,_,_=b.load_transplants(args.transplant,tpl,doc.ids,pf,str(Path.cwd()),asm=doc.asm)
sections['Contents/section1.xml']=doc.build_section1(thanks_xml=thanks,abstract_kr=kr);sections['Contents/section2.xml']=doc.build_section2()
b.write_package(args.output,k.plan_package(tpl,sections,tpl.header.xml,doc.bin_items),(2026,11,6,0,0,0))
(O/'assembly_report.md').write_text('\n'.join(doc.notes),encoding='utf8')
print('fresh written; KR',len(kr),'EN',len(en),'notes',len(doc.notes))

