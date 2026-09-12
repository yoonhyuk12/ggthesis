"""Coordinator-only targeted image insertion; manifests pin the reviewed assets."""
from pathlib import Path
import sys,re,json,hashlib,html,zipfile,copy
import xml.etree.ElementTree as E
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,owned
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H='{http://www.hancom.co.kr/hwpml/2011/head}'
def main():
 manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
 audit=json.loads((HERE/'base_paras.json').read_text(encoding='utf-8'))
 base=ROOT/audit['base']; blob=base.read_bytes()
 assert hashlib.sha256(blob).hexdigest()==audit['sha256']
 with zipfile.ZipFile(base) as z: entries={n:z.read(n) for n in z.namelist()}; infos=z.infolist()
 sec=entries['Contents/section2.xml']; header=entries['Contents/header.xml']
 nodes=[n for n in elements(sec) if n['name']=='hp:p' and n['parent']['name']=='hs:sec']
 tree=E.fromstring(sec); ps=tree.findall(P+'p')
 fresh=max(int(x) for x in re.findall(rb'\bid="(\d+)"',sec))+100
 with zipfile.ZipFile(HERE/'picture_template.hwpx') as z: template=z.read('Contents/section0.xml')
 pic=fragment(template,next(n for n in elements(template) if n['name']=='hp:pic'))
 hnodes=elements(header); pid=max(int(n['attrs']['id']) for n in hnodes if n['name']=='hh:paraPr')+1
 caption=next(p for p in ps if owned(p).startswith('<그림 '))
 style=fragment(header,next(n for n in hnodes if n['name']=='hh:paraPr' and n['attrs']['id']==caption.get('paraPrIDRef')))
 style=re.sub(rb'\bid="\d+"',f'id="{pid}"'.encode(),style,count=1)
 style=re.sub(rb'horizontal="[^"]+"',b'horizontal="CENTER"',style,count=1)
 style=re.sub(rb'keepWithNext="[^"]+"',b'keepWithNext="1"',style)
 style=re.sub(rb'(<hh:lineSpacing[^>]*value=")[^"]+',rb'\g<1>100',style)
 header=re.sub(rb'(<hh:paraProperties[^>]*itemCnt=")(\d+)',lambda m:m[1]+str(int(m[2])+1).encode(),header,count=1)
 header=header.replace(b'</hh:paraProperties>',style+b'</hh:paraProperties>')
 changes=[]; images={}; reports=[]
 for k,item in enumerate(manifest['figures']):
  f=ROOT/item['png']; assert f.is_file()
  matches=[i for i,p in enumerate(ps) if owned(p).startswith('<그림 '+item['number']+'>')]
  assert len(matches)==1,matches
  i=matches[0]; node=nodes[i]; raw=fragment(sec,node)
  assert b'<hp:tbl' not in raw
  # Replace only the fulfilled insertion marker; retain all unrelated source text.
  end=node['end']; removed=None
  if i+1<len(ps) and owned(ps[i+1]).startswith('[그림 삽입 예정:'):
   removed=owned(ps[i+1]); end=nodes[i+1]['end']
  wpx,hpx=Image.open(f).size
  width=round(min(item.get('width_mm',150),150)*7200/25.4)
  height=round(width*hpx/wpx)
  assert height<54000,'Image exceeds page height'
  bid='thesisfig'+item['number'].replace('-','_')
  obj=pic
  obj=re.sub(rb'\bid="\d+"',f'id="{fresh+k*3}"'.encode(),obj,count=1)
  obj=re.sub(rb'instid="\d+"',f'instid="{fresh+k*3+1}"'.encode(),obj,count=1)
  obj=obj.replace(b'42520',str(width).encode()).replace(b'17008',str(height).encode())
  obj=obj.replace(b'binaryItemIDRef="image1"',f'binaryItemIDRef="{bid}"'.encode())
  obj=re.sub(rb'<hp:shapeComment>.*?</hp:shapeComment>',('<hp:shapeComment>'+html.escape(item['caption'])+'</hp:shapeComment>').encode(),obj,flags=re.S)
  char=ps[i].find(P+'run').get('charPrIDRef')
  imagep=(f'<hp:p id="{fresh+k*3+2}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{char}">'.encode()+obj+b'<hp:t/></hp:run></hp:p>')
  raw=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',raw,flags=re.S)
  note=b''
  if item['number']=='3-4':
   note_text='자료: 기존 학회논문의 실제 모니터링·판정 교정 화면.'
   note=(f'<hp:p id="{fresh+100}" paraPrIDRef="{ps[i].get("paraPrIDRef")}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{char}"><hp:t>'+note_text+'</hp:t></hp:run></hp:p>').encode()
  changes.append((node['start'],end,imagep+raw+note))
  images['BinData/'+bid+'.png']=f.read_bytes()
  reports.append(dict(number=item['number'],source=str(f.relative_to(ROOT)),width=width,height=height,removed_marker=removed))
 for start,end,new in sorted(changes,reverse=True): sec=sec[:start]+new+sec[end:]
 for old,new in manifest.get('text_corrections',[]):
  oldb=html.escape(old,quote=False).encode();newb=html.escape(new,quote=False).encode()
  assert sec.count(oldb)==1,('Correction must match once',old,sec.count(oldb))
  target=next(n for n in elements(sec) if n['name']=='hp:p' and oldb in fragment(sec,n))
  raw=fragment(sec,target).replace(oldb,newb)
  raw=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',raw,flags=re.S)
  sec=sec[:target['start']]+raw+sec[target['end']:]
 hpf=entries['Contents/content.hpf']
 additions=b''.join(f'<opf:item id="{Path(n).stem}" href="{n}" media-type="image/png" isEmbeded="1"/>'.encode() for n in images)
 hpf=hpf.replace(b'</opf:manifest>',additions+b'</opf:manifest>')
 for data in (sec,header,hpf): E.fromstring(data)
 entries.update({'Contents/section2.xml':sec,'Contents/header.xml':header,'Contents/content.hpf':hpf})
 out=HERE/'candidate.hwpx'
 with zipfile.ZipFile(out,'w') as z:
  for info in infos:z.writestr(info,entries[info.filename])
  for n,data in images.items():z.writestr(n,data,compress_type=zipfile.ZIP_DEFLATED)
 (HERE/'insertion_report.json').write_text(json.dumps({'base_sha256':audit['sha256'],'figures':reports,'output':str(out.relative_to(ROOT))},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Inserted',len(reports),'figures:',out)
if __name__=='__main__':main()
