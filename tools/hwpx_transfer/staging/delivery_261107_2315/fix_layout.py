from pathlib import Path
import zipfile,sys,re,copy,json
from lxml import etree as E
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p;import kjn_profile as k
O=Path(__file__).parent;HP='{'+k.NS['hp']+'}';HH='{http://www.hancom.co.kr/hwpml/2011/head}'
with zipfile.ZipFile(O/'final.hwpx') as z:infos=z.infolist();data={i.filename:z.read(i) for i in infos}
s=data['Contents/section2.xml'].decode();h=E.fromstring(data['Contents/header.xml']);plist=h.find('.//'+HH+'paraProperties');prs={x.get('id'):x for x in plist};ids=max(map(int,prs))+1

def xml(r):return re.sub(r' xmlns:[^=]+="[^"]*"','',E.tostring(r,encoding='unicode'))
def clear(r):
 for e in list(r.iter(HP+'linesegarray')):e.getparent().remove(e)
def style(r,ref=False):
 global ids
 old=prs[r.get('paraPrIDRef')];new=copy.deepcopy(old);new.set('id',str(ids));ids+=1
 bs=new.find(HH+'breakSetting');bs.set('keepLines','1');bs.set('pageBreakBefore','0')
 if ref:
  new.find(HH+'align').set('horizontal','LEFT');bs.set('breakLatinWord','BREAK_WORD')
 plist.append(new);r.set('paraPrIDRef',new.get('id'));clear(r)
widths={'<표3-6>':[8500,8500,14684,8000],'<표3-7>':[10400,6000,10065,6200,7019],'<표4-13>':[9200,5700,2800,6800,3700,8000,3484]}
audit=[];refs=False
for u in p.Units(s,set()).items:
 r=E.fromstring(k._wrap(u['xml']).encode())[0];changed=False
 if u['tbl'] and u['cap'] in widths:
  t=next(r.iter(HP+'tbl'));ws=widths[u['cap']];assert sum(ws)==int(t.find(HP+'sz').get('width'))
  for c in t.findall(HP+'tr/'+HP+'tc'):
   a=c.find(HP+'cellAddr');sp=c.find(HP+'cellSpan');col=int(a.get('colAddr'));n=int(sp.get('colSpan'));c.find(HP+'cellSz').set('width',str(sum(ws[col:col+n])))
  clear(r);changed=True;audit.append({'table':u['cap'],'widths':ws})
 if p.nows(u['text'])=='참고문헌':refs=True
 if p.nows(u['text']).startswith('부록('):refs=False
 if refs and re.match(r'^\[\d+\]',u['text']):style(r,True);changed=True
 if p.nows(u['text'])=='제8절분석결과및논의':r.set('pageBreak','0');clear(r);changed=True;audit.append({'section8_pagebreak':'removed to avoid isolated preceding transition'})
 if changed:s=s.replace(u['xml'],xml(r),1)
plist.set('itemCnt',str(len(plist)));data['Contents/header.xml']=E.tostring(h,encoding='UTF-8',xml_declaration=True);data['Contents/section2.xml']=s.encode()
with zipfile.ZipFile(O/'layout_fixed.hwpx','w') as z:
 for i in infos:z.writestr(i,data[i.filename])
(O/'layout_changes.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print('layout_fixed written; content unchanged',len(audit))
