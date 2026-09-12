"""Coordinator-only, targeted dotted tab leaders and page numbers."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'intro_260912'))
from apply_intro import elements, paragraphs, fragment, raw_zip_patch, require

P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
H = '{http://www.hancom.co.kr/hwpml/2011/head}'

def owned(p):
    return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))

def soft_wrap(raw, title, idx):
    # These entries had less than 2400 HWP units of leader in the first
    # Hancom render; two put the folio alone at the left of the next line.
    needs_wrap={5,24,45,77,78,79,103,105,108,115,126}
    if idx not in needs_wrap:
        return raw
    cut=title.index('[DATA PENDING]') if '[DATA PENDING]' in title else title.rfind(' ',0,len(title)-12)+1
    require(cut>0,'No safe title wrap boundary')
    cursor=0
    for match in re.finditer(rb'<hp:t>([^<]*)</hp:t>',raw):
        value=html.unescape(match[1].decode('utf-8'))
        if cursor<=cut<=cursor+len(value):
            at=cut-cursor
            replacement=(html.escape(value[:at],quote=False)+'<hp:lineBreak/>'+html.escape(value[at:],quote=False)).encode('utf-8')
            return raw[:match.start(1)]+replacement+raw[match.end(1):]
        cursor+=len(value)
    raise ValueError('Unable to place soft line break')

def append_style(header):
    nodes=elements(header)
    tab=next(n for n in nodes if n['name']=='hh:tabPr' and n['attrs'].get('id')=='4')
    para=next(n for n in nodes if n['name']=='hh:paraPr' and n['attrs'].get('id')=='47')
    tid=max(int(n['attrs']['id']) for n in nodes if n['name']=='hh:tabPr')+1
    pid=max(int(n['attrs']['id']) for n in nodes if n['name']=='hh:paraPr')+1
    newtab=fragment(header,tab)
    newtab=re.sub(rb'\bid="4"',f'id="{tid}"'.encode(),newtab,count=1)
    newtab=newtab.replace(b'leader="DASH"',b'leader="DOT"').replace(b'autoTabRight="1"',b'autoTabRight="0"')
    newpara=fragment(header,para)
    newpara=re.sub(rb'\bid="47"',f'id="{pid}"'.encode(),newpara,count=1)
    newpara=re.sub(rb'tabPrIDRef="\d+"',f'tabPrIDRef="{tid}"'.encode(),newpara,count=1)
    newpara=newpara.replace(b'horizontal="JUSTIFY"',b'horizontal="LEFT"')
    newpara=newpara.replace(b'keepLines="0"',b'keepLines="1"')
    newpara=newpara.replace(b'value="170"',b'value="160"')
    for tag,new in [(b'tabProperties',newtab),(b'paraProperties',newpara)]:
        pattern=rb'(<hh:'+tag+rb'\b[^>]*itemCnt=")(\d+)("[^>]*>)'
        header,n=re.subn(pattern,lambda m:m[1]+str(int(m[2])+1).encode()+m[3],header,count=1)
        require(n==1,'Missing style container')
        header=header.replace(b'</hh:'+tag+b'>',new+b'</hh:'+tag+b'>',1)
    ET.fromstring(header)
    return header,pid

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('base',type=Path);ap.add_argument('map',type=Path);ap.add_argument('out',type=Path)
    args=ap.parse_args()
    require(not args.out.exists() and args.base.resolve()!=args.out.resolve(),'Fresh output required')
    mapping=json.loads(args.map.read_text(encoding='utf-8-sig'))
    require(not mapping.get('unresolved'),'Unresolved page mappings')
    blob=args.base.read_bytes()
    if 'base_sha256' in mapping:
        require(hashlib.sha256(blob).hexdigest().lower()==mapping['base_sha256'].lower(),'Wrong source file')
    with zipfile.ZipFile(args.base) as z:
        header=z.read('Contents/header.xml')
        colors={n.get('id'):n.get('textColor') for n in ET.fromstring(header).iter(H+'charPr')}
        header,pid=append_style(header)
        sec=z.read('Contents/section1.xml');ps=paragraphs(sec)
        tree=ET.fromstring(sec);paras=list(tree.iter(P+'p'))
        edits=[]
        for entry in mapping['entries']:
            idx=entry['toc_idx'];p=paras[idx];node=ps[idx]
            require(owned(p).strip()==entry['title'].strip(),f'TOC text mismatch at {idx}')
            require(node['parent']['name']=='hs:sec','TOC must be top-level')
            raw=fragment(sec,node)
            require(b'<hp:tab' not in raw,'Existing tab requires explicit update')
            raw=soft_wrap(raw,entry['title'],idx)
            black=next(r.get('charPrIDRef') for r in p.findall(P+'run') if colors[r.get('charPrIDRef')].upper()=='#000000')
            raw=re.sub(rb'paraPrIDRef="\d+"',f'paraPrIDRef="{pid}"'.encode(),raw,count=1)
            raw=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',raw,flags=re.S)
            page=int(entry['printed_page']);require(page>0,'Invalid body page')
            tail=f'<hp:run charPrIDRef="{black}"><hp:t><hp:tab width="0" leader="1" type="2"/>{page}</hp:t></hp:run>'.encode()
            raw=raw[:-len(b'</hp:p>')]+tail+b'</hp:p>'
            edits.append((node['start'],node['end'],raw))
        for start,end,raw in sorted(edits,reverse=True):sec=sec[:start]+raw+sec[end:]
        ET.fromstring(sec)
        patched=raw_zip_patch(blob,{'Contents/header.xml':header,'Contents/section1.xml':sec})
        with args.out.open('xb') as f:f.write(patched)
    print(json.dumps({'output':str(args.out),'entries':len(edits),'toc_para_style':pid},ensure_ascii=False))

if __name__=='__main__':main()
