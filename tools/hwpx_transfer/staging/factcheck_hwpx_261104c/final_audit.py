from pathlib import Path
import zipfile,lxml.etree as E,json,re,hashlib
s=Path('tools/hwpx_transfer/staging/factcheck_hwpx_261104c');ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hh':'http://www.hancom.co.kr/hwpml/2011/head'}
def tx(p):return ''.join(''.join(t.itertext()) for r in p.findall('hp:run',ns) for t in r.findall('hp:t',ns))
with zipfile.ZipFile(s/'base.hwpx') as base,zipfile.ZipFile(s/'ready.hwpx') as ready,zipfile.ZipFile(s/'final.hwpx') as final:
 def root(z,n):return E.fromstring(z.read(n))
 for name in ['Contents/section0.xml','Contents/section2.xml']:
  a=root(ready,name);b=root(final,name)
  assert [tx(p) for p in a.findall('.//hp:p',ns)]==[tx(p) for p in b.findall('.//hp:p',ns)]
 # Layout and user graphic modifications: all attributes except cache & content retained
 for name in ['Contents/section0.xml','Contents/section1.xml','Contents/section2.xml']:
  a=root(base,name);b=root(final,name)
  for tag in ['pic','pos','cellSz','cellAddr','cellSpan']:
   assert [dict(x.attrib) for x in a.findall('.//hp:'+tag,ns)]==[dict(x.attrib) for x in b.findall('.//hp:'+tag,ns)],(name,tag)
  assert len(a.findall('.//hp:tab',ns))==len(b.findall('.//hp:tab',ns)),name
 # Check referenced character definitions and red text counts
 def chars(z):
  h=root(z,'Contents/header.xml');d={c.get('id'):E.tostring(c).split(b'>',1)[1] for c in h.findall('.//hh:charPr',ns)}
  red={c.get('id') for c in h.findall('.//hh:charPr',ns) if c.get('textColor','').upper()=='#FF0000'}
  return red
 def redtext(z):
  ids=chars(z);return [''.join(r.itertext()) for n in z.namelist() if re.match(r'Contents/section\d+.xml',n) for r in root(z,n).findall('.//hp:run',ns) if r.get('charPrIDRef') in ids]
 assert redtext(base)==redtext(final)
 # MD structure titles, exclude author-only notices and numbering spaces
 def norm(t):return re.sub(r'\s+','',t).replace('**','')
 body='\n'.join(tx(p) for p in root(final,'Contents/section2.xml').findall('.//hp:p',ns));bn=norm(body)
 missing=[];count=0
 for p in Path('01.docs').glob('0[1-5]_*.md'):
  for ln in p.read_text(encoding='utf-8').splitlines():
   if re.match(r'^#{1,4} 제\d+[장절항]',ln) or re.match(r'^<(표|그림) \d+-\d+>',ln):
    title=re.sub(r'^#+\s*','',ln).strip();count+=1
    if norm(title) not in bn:missing.append({'file':p.as_posix(),'title':title})
 result={'final_body_matches_ready':True,'all_picture_size_position_cell_geometry_preserved':True,'tabs_preserved':True,'red_text_preserved':True,'md_structure_checked':count,'md_structure_missing':missing,'header_bytes_equal':base.read('Contents/header.xml')==final.read('Contents/header.xml')}
 (s/'final_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result)

