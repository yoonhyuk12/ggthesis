from pathlib import Path
import zipfile,copy,json,hashlib
from lxml import etree as E
from PIL import Image
S=Path(__file__).parent
NS={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hh':'http://www.hancom.co.kr/hwpml/2011/head','hc':'http://www.hancom.co.kr/hwpml/2011/core','opf':'http://www.idpf.org/2007/opf/'}
def el(n):return '{'+NS[n.split(':')[0]]+'}'+n.split(':')[1]
def txt(p):return ''.join(p.xpath('.//hp:t//text()',namespaces=NS))
def clean(p):
 for x in p.findall('.//'+el('hp:linesegarray')):x.getparent().remove(x)
def single(root,prefix):return next(p for p in root if txt(p).startswith(prefix))
with zipfile.ZipFile(S/'text.hwpx') as z: infos=z.infolist();data={i.filename:z.read(i) for i in infos}
r=E.fromstring(data['Contents/section2.xml']);toc=E.fromstring(data['Contents/section1.xml']);h=E.fromstring(data['Contents/header.xml'])
props=h.find('.//'+el('hh:paraProperties'))
def style(old,keep):
 p=copy.deepcopy(next(x for x in props if x.get('id')==old));n=str(max(int(x.get('id')) for x in props)+1);p.set('id',n)
 p.find(el('hh:breakSetting')).set('keepWithNext',str(keep));props.append(p);props.set('itemCnt',str(len(props)));return n
picstyle=style('23',1);capstyle=style('73',0)
cap4=single(r,'<그림 3-4>');template=copy.deepcopy(r[r.index(cap4)+1])
cap5=single(r,'<그림 3-5>');pic5=r[r.index(cap5)+1]
# Preserve existing figure 3-5 text and its mixed character formatting.
r.remove(pic5);r.insert(r.index(cap5),pic5);cap5.set('paraPrIDRef',capstyle);clean(cap5)
files=['fig_3_11_chart_v6.png','fig_3_6_field_operation_butterfly.png']
cap6text=next(l for l in Path('01.docs/03_시스템개발.md').read_text(encoding='utf-8').splitlines() if l.startswith('<그림 3-6>'))
oldcap=single(r,'<표 3-11>');oldtable=r[r.index(oldcap)+1];assert oldtable.find('.//'+el('hp:tbl')) is not None
idx=r.index(oldcap);r.remove(oldcap);r.remove(oldtable)
pic6=copy.deepcopy(template);pic6.set('id','4100000001');pic6.find('.//'+el('hp:pic')).set('id','1410000001');pic6.find('.//'+el('hp:pic')).set('instid','1410000002')
cap6=copy.deepcopy(cap4);cap6.set('id','4100000002');cap6.set('paraPrIDRef',capstyle);cap6.find('.//'+el('hp:t')).text=cap6text;clean(cap6)
r.insert(idx,pic6);r.insert(idx+1,cap6)
manifest=E.fromstring(data['Contents/content.hpf']);mf=manifest.find(el('opf:manifest'))
report=[]
for p,name,num in [(pic5,files[0],'3-5'),(pic6,files[1],'3-6')]:
 path=Path('01.docs/figures/system')/name;wpx,hpx=Image.open(path).size;w=round(150*7200/25.4);ht=round(w*hpx/wpx)
 pic=p.find('.//'+el('hp:pic'));img=pic.find(el('hc:img'))
 if num=='3-5':
  bid=img.get('binaryItemIDRef');entry=next(x.get('href') for x in mf if x.get('id')==bid)
  same=data[entry]==path.read_bytes();report.append({'existing_image_bytes_identical':same})
  # use exact requested source, if Hancom normalized its bytes retain content verification evidence
  data[entry]=path.read_bytes()
 else:
  bid='figure36';entry='BinData/figure36.png';img.set('binaryItemIDRef',bid);data[entry]=path.read_bytes();E.SubElement(mf,el('opf:item'),id=bid,href=entry,**{'media-type':'image/png','isEmbeded':'1'})
 for n in ['orgSz','sz']:
  q=pic.find(el('hp:'+n));q.set('width',str(w));q.set('height',str(ht))
 rot=pic.find(el('hp:rotationInfo'));rot.set('centerX',str(w//2));rot.set('centerY',str(ht//2))
 for n,x,y in [('pt0',0,0),('pt1',w,0),('pt2',w,ht),('pt3',0,ht)]:
  q=pic.find(el('hp:imgRect')+'/'+el('hc:'+n));q.set('x',str(x));q.set('y',str(y))
 iw=wpx*75;ih=hpx*75
 q=pic.find(el('hp:imgClip'));q.set('right',str(iw));q.set('bottom',str(ih))
 q=pic.find(el('hp:imgDim'));q.set('dimwidth',str(iw));q.set('dimheight',str(ih))
 pic.find(el('hp:shapeComment')).text=f'그림 {num}: {name} ({wpx} x {hpx})'
 p.set('paraPrIDRef',picstyle);clean(p);report.append({'figure':num,'width':w,'height':ht,'source':str(path)})
oldtoc=single(toc,'<표 3-11>');toc.remove(oldtoc)
t5=single(toc,'<그림 3-5>');t6=copy.deepcopy(single(toc,'<그림 3-4>'));t6.set('id','4100000003')
t=t6.find('.//'+el('hp:t'));t.text=cap6text;t.find(el('hp:tab')).tail='51';clean(t6);toc.insert(toc.index(t5)+1,t6)
for key,root in [('Contents/section2.xml',r),('Contents/section1.xml',toc),('Contents/header.xml',h),('Contents/content.hpf',manifest)]:data[key]=E.tostring(root,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(S/'candidate.hwpx','w') as z:
 for i in infos:z.writestr(i,data.pop(i.filename))
 for name,b in data.items():z.writestr(name,b,compress_type=zipfile.ZIP_DEFLATED)
(S/'insertion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
