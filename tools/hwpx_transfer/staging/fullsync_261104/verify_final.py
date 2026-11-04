from pathlib import Path
import json,zipfile,hashlib,re,html,xml.etree.ElementTree as E
import fitz
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
final=ROOT/'00. hwpx/261104_0858_경기공학_건축안전_윤혁_논문.hwpx'
info=json.loads((OUT/'base_info.json').read_text(encoding='utf8'))
assert hashlib.sha256((ROOT/info['path']).read_bytes()).hexdigest()==info['sha256']
old=fitz.open(OUT/'resaved3.pdf');new=fitz.open(OUT/'final.pdf');assert len(old)==len(new)
# Only physical pages 4-9 contain TOC text; physical page 10 starts thanks.
changed=[i+1 for i,(a,b) in enumerate(zip(old,new)) if a.get_text()!=b.get_text()]
assert all(4<=i<=9 for i in changed),changed
with zipfile.ZipFile(final) as z:
 assert z.testzip() is None
 data={n:z.read(n) for n in z.namelist()}
s=data['Contents/section1.xml'].decode();want={}
for cat in json.loads((OUT/'toc_pages3_completed.json').read_text(encoding='utf8')).values():
 for t,v in cat.items():want[t]=list(map(str,v if isinstance(v,list) else [v]))
used={};checked=0
for paragraph in re.findall(r'<hp:p\b.*?</hp:p>',s,re.S):
 if '<hp:tab' not in paragraph:continue
 before,after=paragraph.split('<hp:tab',1)
 t=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip()
 index=used.get(t,0);used[t]=index+1
 actual=re.search(r'/>\s*([^<]*)</hp:t>',after).group(1).strip()
 assert actual==want[t][min(index,len(want[t])-1)],(t,actual,want[t]);checked+=1
assert checked==119,checked
manifest={e.get('id'):e.get('href') for e in E.fromstring(data['Contents/content.hpf']).iter() if e.tag.endswith('}item')}
refs=[e.get('binaryItemIDRef') for n,v in data.items() if re.match(r'Contents/section\d+.xml',n) for e in E.fromstring(v).iter() if e.tag.endswith('}img')]
sources=json.loads((OUT/'images.json').read_text(encoding='utf8'))['mapping']
src_hashes={hashlib.sha256((ROOT/x['source']).read_bytes()).hexdigest() for x in sources}
actual_hashes={hashlib.sha256(data[manifest[i]]).hexdigest() for i in refs}
assert len(refs)==7 and actual_hashes==src_hashes,(len(refs),actual_hashes-src_hashes,src_hashes-actual_hashes)
assert not any(s in data['Contents/section2.xml'].decode() for s in ['부록 2.','부록 3.'])
report={'final_file':str(final.relative_to(ROOT)),'pages':len(new),'changed_PDF_pages_only_TOC':changed,'toc_numbers_correct':checked,'original_SHA_unchanged':True,'images_match_MD_sources':len(refs),'removed_appendices_absent':True}
(OUT/'final_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
