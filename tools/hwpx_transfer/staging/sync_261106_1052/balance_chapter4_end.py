"""MAIN ONLY: retain the final discussion paragraph and its following transition together."""
from pathlib import Path
import sys,re,json,zipfile
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p
O=Path(__file__).parent
def main():
 src=O/'layout_ready.hwpx';dest=O/'balanced.hwpx'
 with zipfile.ZipFile(src) as z:
  secname='Contents/section2.xml';headname='Contents/header.xml'
  x=z.read(secname).decode('utf8');h=z.read(headname).decode('utf8');u=p.Units(x,set())
  found=[i for i,q in enumerate(u.items) if q['text'].startswith('<표 2-2>는 시스템 기능, 관리자의 업무,')]
  assert len(found)==1;i=found[0];q=u.items[i]
  assert u.items[i+1]['text'].startswith('다음 제5장에서는 이 논의를 바탕으로')
  oldref=re.search(r'paraPrIDRef="(\d+)"',q['xml']).group(1)
  oldprop=re.search(r'<hh:paraPr\b[^>]*\bid="'+oldref+r'".*?</hh:paraPr>',h,re.S).group()
  newref=str(max(map(int,re.findall(r'<hh:paraPr\b[^>]*\bid="(\d+)"',h)))+1)
  newprop=re.sub(r'\bid="'+oldref+r'"','id="'+newref+'"',oldprop,count=1)
  newprop=newprop.replace('keepWithNext="0"','keepWithNext="1"').replace('keepLines="0"','keepLines="1"')
  assert newprop.count('keepWithNext="1"')==newprop.count('keepLines="1"')==1
  newh=h.replace('</hh:paraProperties>',newprop+'</hh:paraProperties>',1)
  newh=re.sub(r'(<hh:paraProperties\b[^>]*itemCnt=")(\d+)(")',lambda m:m.group(1)+str(int(m.group(2))+1)+m.group(3),newh,count=1)
  newxml=q['xml'].replace('paraPrIDRef="'+oldref+'"','paraPrIDRef="'+newref+'"',1)
  newxml=re.sub(r'<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>','',newxml,flags=re.S)
  parts=[t['xml'] for t in u.items];parts[i]=newxml;newx=u.head+''.join(parts)+u.tail
  assert [t['text'] for t in p.Units(newx,set()).items]==[t['text'] for t in u.items]
  replacements={secname:newx.encode(),headname:newh.encode()}
  with zipfile.ZipFile(dest,'w') as w:
   for zi in z.infolist():w.writestr(zi,replacements.get(zi.filename,z.read(zi.filename)))
 audit={'section':2,'unit_index':i,'paragraph_id':re.search(r'<hp:p\b[^>]*id="(\d+)"',q['xml']).group(1),'old_paraPrIDRef':oldref,'new_paraPrIDRef':newref,'changes':{'keepLines':['0','1'],'keepWithNext':['0','1']},'font_size_spacing_margin_text_unchanged':True,'new_charPr':None,'output':dest.as_posix(),'requires_reflow_PDF':True}
 (O/'balance_chapter4_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
