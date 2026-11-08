from pathlib import Path
import zipfile,json,re,hashlib,io
from PIL import Image
O=Path(__file__).parent
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
source=Path('01.docs/figures/research/figure_1-1_research_flow.png')
assert 'Holm' not in source.with_suffix('.svg').read_text(encoding='utf8')
with zipfile.ZipFile(O/'base.hwpx') as z:
    infos=z.infolist();data={i.filename:z.read(i) for i in infos}
assert Image.open(io.BytesIO(data[info['image_entry']])).size==Image.open(source).size
data[info['image_entry']]=source.read_bytes()
old=info['picture_xml']
new=re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',old,flags=re.S)
s=data['Contents/section2.xml'].decode()
assert s.count(old)==1
data['Contents/section2.xml']=s.replace(old,new,1).encode()
with zipfile.ZipFile(O/'patched.hwpx','w') as z:
    for i in infos:z.writestr(i,data[i.filename])
with zipfile.ZipFile(O/'base.hwpx') as a,zipfile.ZipFile(O/'patched.hwpx') as b:
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
assert set(changed)<=set([info['image_entry'],'Contents/section2.xml'])
assert hashlib.sha256(Path(info['base']).read_bytes()).hexdigest()==info['sha256']
print('Changed entries:',changed)
