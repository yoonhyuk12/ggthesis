"""Read-only PDF layout evidence; run after the main agent provides a PDF."""
from pathlib import Path
import json, re, sys
import pymupdf
from PIL import Image, ImageDraw

O=Path(__file__).resolve().parent

def main():
    src=Path(sys.argv[1]); doc=pymupdf.open(src)
    out=O/(src.stem+'_visual'); out.mkdir(exist_ok=True)
    records=[]; selected=set(); table_pages=[]
    for i,page in enumerate(doc):
        blocks=page.get_text('blocks'); txt=page.get_text()
        footer=[b for b in blocks if re.fullmatch(r'-\s*(?:\d+|[ivxlcdm]+)\s*-',b[4].strip()) and b[1]>page.rect.height*.85]
        lines=[]
        for dr in page.get_drawings():
            for item in dr['items']:
                if item[0]=='l' and abs(item[1].y-item[2].y)<.5 and abs(item[1].x-item[2].x)>60:
                    lines.append(item[1].y)
                elif item[0]=='re' and item[1].width>60 and item[1].height<1.5: lines.append(item[1].y0)
        cap=[s for s in txt.splitlines() if re.match(r'^<표\s*\d+-\d+>',s.strip())]
        has_table=len(lines)>=2
        if has_table:
            table_pages.append(i+1)
            selected.add(i); selected.add(min(i+1,len(doc)-1))
        records.append({'page':i+1,'printed':footer[0][4].strip() if footer else None,
            'table_lines':len(lines),'table_bottom':max(lines) if lines else None,
            'footer_y':footer[0][1] if footer else None,'captions':cap,
            'text':txt,'overlap':bool(lines and footer and max(lines)>footer[0][1]-4)})
    pages=sorted(selected); sheets=[]
    for start in range(0,len(pages),4):
        batch=pages[start:start+4]; sheet=Image.new('RGB',(1320,1850),'#ddd'); draw=ImageDraw.Draw(sheet)
        for j,idx in enumerate(batch):
            page=doc[idx]; pix=page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False)
            im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples); im.thumbnail((650,890))
            x=(j%2)*660; y=(j//2)*925
            draw.text((x+5,y+5),f'PDF {idx+1} / {records[idx]["printed"]}',fill='black'); sheet.paste(im,(x+5,y+25))
        dest=out/f'sheet_{start//4:02}.png'; sheet.save(dest); sheets.append(dest.relative_to(O).as_posix())
    report={'pdf':str(src),'page_count':len(doc),'table_pages':table_pages,
        'selected_pages':[x+1 for x in pages],'records':records,'evidence_images':sheets,
        'automated_overlap':[x['page'] for x in records if x['overlap']],
        'reviewed_pages':[],'issues':[],'ok':False,'status':'awaiting visual review'}
    target=O/(src.stem+'_visual_evidence.json'); target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:report[k] for k in ('page_count','table_pages','selected_pages','automated_overlap','evidence_images')},ensure_ascii=False))

if __name__=='__main__':main()
