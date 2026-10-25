"""Standalone printed surveys. MAIN AGENT ONLY may run this HWPX writer.

Reuses the designated template's styles and body page controls, removes all of
its document content, and packages one newly assembled section. Does not use COM.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/hwpx_transfer'))
import kjn_profile as kp
from PIL import ImageFont

TEMPLATE = ROOT / '00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx'
PROFILE = ROOT / 'tools/hwpx_transfer/staging/migrate_kjn/style_map_kjn.json'
SPEC = ROOT / '04. 구글폼/survey-spec.json'
SHA = '9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3'
NS = kp.NS

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def paragraph_text(p):
    return ''.join(p.itertext())

def paper_intro(spec):
    text = spec['description']
    old = '안내받은 Google Forms 설문에서 직접 응답을 입력하거나 선택한 뒤 제출해 주십시오.'
    assert text.count(old) == 1
    text = text.replace(old, '이 설문지에 직접 응답을 기입하거나 해당 보기를 선택해 주십시오.')
    old = 'Google 계정 로그인은 요구하지 않으며 응답자 이메일은 수집하지 않습니다.'
    assert text.count(old) == 1
    return text.replace(old, '응답자 이메일은 수집하지 않습니다.')

def compact_answer_spec(template, body):
    """Keep 11pt face; use the template table's 130% spacing for paper answer lines.

    Separate options avoid isolated checkboxes. Font size/width stay unchanged;
    only paragraph spacing is adapted to the standalone response sheet.
    """
    xml=template.header.item_xml('paraPr',body['para'])
    xml=re.sub(r'(<hh:lineSpacing\b[^>]*\bvalue=")170(")',r'\g<1>130\g<2>',xml)
    pid=template.header.find_same('paraPr',xml) or template.header.add('paraPr',xml)
    return dict(body,para=pid)

class SurveyAssembler(kp.KjnAssembler):
    """Original 10pt table face, measured at 100px; widths in HWPUNIT."""
    def __init__(self, profile, template, font_path, font_index=0):
        super().__init__(profile, kp.IdGen(), template.red_char_pr_id, template.header)
        self.font = ImageFont.truetype(str(font_path), 100, index=font_index)
        self.face = self.font.getname()
        if not any(x in ''.join(self.face).lower() for x in ('신명조', 'shinmyeong', 'sinmyeong', 'hysnrl')):
            raise ValueError('Provide the actual 한양신명조 font, not a fallback: %r' % (self.face,))
        self.measurements = []

    def width(self, text):
        return round(self.font.getlength(text) * 10)  # 100px em -> 1000hu (10pt)

    def line_count(self, text, width):
        count = 0
        for line in text.split('<br>'):
            current = ''
            count += 1
            for char in line:
                if current and self.width(current + char) > width:
                    count += 1
                    current = char
                else:
                    current += char
        return count

    def column_widths(self, header, rows):
        assert len(header) == 7
        number = max(self.width('D-8'), self.width('번호')) + self.hpad + 250
        choice = max(self.width('⑤'), self.width('□')) + self.hpad + 400
        # Equal widths only for five identical response columns.
        result = [number, self.total_width-number-5*choice] + [choice]*5
        assert result[1] > sum(result[2:]) and sum(result) == self.total_width
        return result

    def table_xml(self, header, rows):
        xml, widths = super().table_xml(header, rows)
        wrapper = ET.fromstring(kp._wrap(xml))
        table = wrapper.find('.//hp:tbl', NS)
        total_h = 0
        for row in table.findall('hp:tr', NS):
            cells = row.findall('hp:tc', NS)
            row_h = max(2400, max(self.line_count(''.join(c.itertext()), widths[i]-self.hpad)
                                  * 1300 + self.vpad for i,c in enumerate(cells)))
            for i,c in enumerate(cells):
                c.find('hp:cellSz', NS).set('height', str(row_h))
                if i != 1:
                    for p in c.findall('.//hp:p', NS):
                        p.set('paraPrIDRef', str(self.pf.get('table','cell_paraPr','header_center')))
            total_h += row_h
        table.find('hp:sz', NS).set('height', str(total_h))
        # Each block starts on a new page. B/C/E fit as intact tables; D may split
        # at row boundaries only if the measured plan requires it.
        table.set('pageBreak', 'NONE')
        if self.avail_height and total_h > self.avail_height:
            table.set('pageBreak', 'TABLE')
            pos = table.find('hp:pos', NS)
            pos.set('treatAsChar','0'); pos.set('horzRelTo','COLUMN')
        self.measurements.append({'widths_hu':widths,'estimated_height_hu':total_h,
                                  'available_after_guidance_hu':self.avail_height,
                                  'page_break':table.get('pageBreak'),
                                  'font_face':self.face,
                                  'note':'PIL glyph widths of supplied font. HYsnrL is an approximate metric proxy for template 한양신명조; actual HWPX face unchanged. Hancom PDF review is required.'})
        return kp._unwrap(wrapper), widths

def new_section(template, asm, profile, spec, route):
    group = '도입 현장' if route == 'ADOPTED' else '미도입 현장'
    sections = [s for s in spec['sections'] if s['id'].startswith(route+'_')]
    # startswith ADOPTED does not match NONADOPTED; explicit ids below verified.
    assert [s['id'][-1] for s in sections] == list('ABCDE' if route=='ADOPTED' else 'ABC')
    h1 = profile.spec('h1_chapter')
    body = profile.spec('body')
    body_bold = dict(body,char=str(profile.get('body_bold_charPr')))
    heading = profile.spec('h3_item')
    note = dict(body)
    answer = compact_answer_spec(template,body)
    paras = []
    pagectrl = re.sub(r'<hp:ctrl><hp:pageHiding[^>]*/></hp:ctrl>', '', template.sec2_pagectrl)
    runs = ('<hp:run charPrIDRef="%s">%s</hp:run><hp:run charPrIDRef="%s">%s'
            '<hp:t>%s</hp:t>%s</hp:run>' % (h1['char'],template.sec2_secpr,h1['char'],
            pagectrl,kp.esc('설문지 — '+group+'용'),template.sec2_newnum))
    paras.append(asm.para(h1,runs))
    paras.append(asm.text_para(body_bold,spec['title']))
    intro = paper_intro(spec)
    intro_lines=[line for block in intro.split('\n\n') for line in block.splitlines()]
    contact_start=next((i for i,line in enumerate(intro_lines) if re.match(r'\d{4}년\s*\d+월',line)),len(intro_lines))
    for i,line in enumerate(intro_lines):
        base = answer if i >= contact_start else body
        para=asm.keep_with_next_spec(base) if contact_start<=i<len(intro_lines)-1 else base
        paras.append(asm.text_para(para,line))
    # Repeated on both paper forms; no routing/admin/analysis mechanics shown.
    expectations = {'intro':intro,'parts':[], 'route':route,'group':group}
    for s in sections:
        letter = s['id'][-1]
        title = s['title'].split(' · ',1)[1]
        paras.append(asm.text_para(heading,title,page_break=True))
        if letter == 'A':
            paras.append(asm.text_para(body_bold,'현장명: ____________________________________'))
            for line in spec['sections'][0]['questions'][1]['help'].splitlines():
                paras.append(asm.text_para(answer,line))
            paras.append(asm.text_para(body_bold,'성명: ____________________'))
            paras.append(asm.text_para(answer,'현장 구분: CCTV YOLO-LLM 안전알림 '+group))
        for block in s['description'].split('\n\n'):
            for line in block.splitlines():
                paras.append(asm.text_para(note,line))
        if letter == 'A':
            for i,q in enumerate(s['questions']):
                if i == 5:
                    paras.append(asm.text_para(heading,title+' (계속)',page_break=True))
                paras.append(asm.text_para(asm.keep_with_next_spec(answer),q['title']))
                if q['type']=='SHORT_ANSWER':
                    paras.append(asm.text_para(answer,'만 (                    )'+q['unit']))
                else:
                    opts = list(q['options'])
                    if q.get('native_other'):
                        opts.append('기타(                    )')
                    for option in opts:
                        paras.append(asm.text_para(answer,'□ '+option))
                for line in q.get('help','').splitlines():
                    paras.append(asm.text_para(answer,line))
        else:
            rows = [[q['id'],q['prompt']]+['□']*5 for q in s['questions']]
            # Match line-height budget to current heading and guidance. 11pt body.
            guide_lines = sum(max(1, (len(x)+33)//34) for x in s['description'].splitlines())
            asm.avail_height = kp.body_avail_height(template.s2) - 4800-guide_lines*1870
            xml,_ = asm.table_xml(['번호','문항','①','②','③','④','⑤'],rows)
            paras.append(xml)
        expectations['parts'].append(copy.deepcopy(s))
    paras.append(asm.blank())
    paras.append(asm.text_para(heading,spec['settings']['confirmation_message']))
    section = template.s2_head+''.join(paras)+'</hs:sec>'
    section = kp.strip_linesegs(section)
    if kp.leftover_hits([kp.plain_texts(section)], profile):
        raise ValueError('Template-specific prose detected')
    assert 'pageBreak="CELL"' not in section
    ET.fromstring(section)
    return section,expectations

def package_entries(template, section, title):
    # Preserve the original header styles, but never retain source sections,
    # graphics, prose previews, old author/title metadata or history payloads.
    header = re.sub(r'(<hh:head\b[^>]*\bsecCnt=")[^"]*(")',r'\g<1>1\g<2>',template.header.xml)
    hpf = ET.fromstring(template.hpf)
    metadata = hpf.find('opf:metadata',NS)
    metadata.clear()
    ET.SubElement(metadata,'{%s}title'%NS['opf']).text=title
    ET.SubElement(metadata,'{%s}language'%NS['opf']).text='ko'
    ET.SubElement(metadata,'{%s}meta'%NS['opf'],{'name':'creator','content':'text'}).text='윤혁'
    manifest = hpf.find('opf:manifest',NS); manifest.clear()
    for ident,href in [('header','Contents/header.xml'),('section0','Contents/section0.xml'),('settings','settings.xml')]:
        ET.SubElement(manifest,'{%s}item'%NS['opf'],{'id':ident,'href':href,'media-type':'application/xml'})
    spine=hpf.find('opf:spine',NS); spine.clear()
    for ident in ['header','section0']:
        ET.SubElement(spine,'{%s}itemref'%NS['opf'],{'idref':ident,'linear':'yes'})
    settings=ET.fromstring(template.raw['settings.xml'])
    caret=settings.find('ha:CaretPosition',NS)
    if caret is not None:
        caret.set('listIDRef','0'); caret.set('pos','0')
        caret.set('paraIDRef',ET.fromstring(section).find('hp:p',NS).get('id'))
    data={'mimetype':template.raw['mimetype'],'version.xml':template.raw['version.xml'],
          'Contents/header.xml':header.encode('utf-8'),'Contents/section0.xml':section.encode('utf-8'),
          'Contents/content.hpf':ET.tostring(hpf,encoding='utf-8',xml_declaration=True),
          'settings.xml':ET.tostring(settings,encoding='utf-8',xml_declaration=True)}
    for name in ['META-INF/container.xml','META-INF/manifest.xml']:
        if name in template.raw:
            data[name]=template.raw[name]
    # The original container also lists container.rdf, which belongs to the old
    # multi-section document. Remove that rootfile entry along with that file.
    if 'META-INF/container.xml' in data:
        container=ET.fromstring(data['META-INF/container.xml'])
        for parent in container.iter():
            for child in list(parent):
                if child.get('full-path')=='META-INF/container.rdf':parent.remove(child)
        data['META-INF/container.xml']=ET.tostring(container,encoding='utf-8',xml_declaration=True)
    data['Preview/PrvText.txt']=kp.plain_texts(section).encode('utf-8')
    return data

def build(args):
    template_path=Path(args.template).resolve()
    assert sha(template_path)==SHA,'Designated original template SHA256 mismatch'
    spec=json.loads(Path(args.spec).read_text(encoding='utf-8-sig'))
    source=ROOT/spec['source']
    assert sha(source)==spec['source_sha256'],'Regenerate current survey spec first'
    outputs=[Path(args.adopted).resolve(),Path(args.nonadopted).resolve()]
    assert len(set(outputs))==2
    for output in outputs:
        assert output!=template_path and not output.exists(),'Never overwrite any existing HWPX'
        assert output.suffix.lower()=='.hwpx'
    reports=[]
    for route,output in zip(['ADOPTED','NONADOPTED'],outputs):
        profile=kp.load_profile(str(args.profile))
        template=kp.KjnTemplate(str(template_path),profile)
        asm=SurveyAssembler(profile,template,args.font_file,args.font_index)
        section,expected=new_section(template,asm,profile,spec,route)
        data=package_entries(template,section,spec['title'])
        output.parent.mkdir(parents=True,exist_ok=True)
        # Required workflow: start from an actual original copy, then replace
        # its complete package. The original is never an output or write target.
        shutil.copy2(template_path,output)
        with zipfile.ZipFile(output,'w') as z:
            for name,payload in data.items():
                z.writestr(name,payload,compress_type=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED)
        expected.update({'output':str(output),'template_sha256':SHA,'spec_sha256':sha(args.spec),
                         'source_sha256':sha(source),'table_layout':asm.measurements,
                         'font_file':str(Path(args.font_file).resolve()),
                         'status':'XML assembled; Hancom open/resave/PDF visual review remains mandatory',
                         'medium_adaptations':['Google Forms input sentence -> paper completion sentence',
                                               'Google login clause removed; email privacy retained',
                                               'No routing or required-field UI or internal analysis notes',
                                               'Fixed group label on each independently distributed form',
                                               'Cover title uses original 11pt body-bold; contact block kept together',
                                               'Management fields on Part A first page; A1-5 then A6-9',
                                               'A answer sheet uses original 11pt face with 130% paragraph spacing; each choice separate']})
        report=output.with_suffix('.content-plan.json')
        report.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        reports.append(str(report))
    assert sha(template_path)==SHA,'Original template changed'
    print(json.dumps({'outputs':[str(x) for x in outputs],'plans':reports,'template_unchanged':True},ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template',default=str(TEMPLATE)); p.add_argument('--profile',default=str(PROFILE))
    p.add_argument('--spec',default=str(SPEC)); p.add_argument('--font-file',required=True)
    p.add_argument('--font-index',type=int,default=0)
    p.add_argument('--adopted',required=True); p.add_argument('--nonadopted',required=True)
    build(p.parse_args())

if __name__=='__main__':
    main()
