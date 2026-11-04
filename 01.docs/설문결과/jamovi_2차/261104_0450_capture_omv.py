"""jamovi .omv 결과를 표·그림 단위 PNG로 캡처한다.

jamovi는 저장 시 결과창 전체를 `index.html`로, 그림을 `NN name/resources/*.png`로 .omv(zip) 안에 넣는다.
이 스크립트는 .omv를 풀어 index.html을 Playwright 크로미움으로 열고, 분석 상자(h1) 순서대로
표(table)와 그림(img)을 잘라 PNG로 저장한다. 표의 셀 텍스트는 tables.json으로 함께 남긴다.

사용법 (저장소 루트에서):
  PYTHONIOENCODING=utf-8 python "01.docs/설문결과/jamovi_2차/261104_0450_capture_omv.py" "<omv 경로>" [--out <출력 폴더>] [--scale 2] [--pad 8]
  --out 생략 시 <omv 폴더>/자모비캡쳐/캡처_<omv이름>_<YYMMDD_HHMM>/ 에 저장한다.

출력:
  S{분석번호}_{분석제목}_T{표번호}_{표제목}.png   표 캡처(배율 --scale, 여백 --pad px)
  S{분석번호}_{분석제목}_I{그림번호}_{주소}.png   그림(omv 안의 원본 PNG를 그대로 복사)
  results_full.png / results_full.pdf              결과창 전체
  manifest.json                                     파일별 분석번호·제목·소제목(h2/h3)·표제목·크기
  tables.json                                       표별 셀 텍스트(행 단위)
"""
import sys, re, json, zipfile, argparse, shutil, tempfile
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


def slug(s: str, n: int = 40) -> str:
    s = re.sub(r'\s+', ' ', (s or '')).strip()
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    s = s.replace(' ', '')
    return s[:n] or 'untitled'


JS_COLLECT = r"""
() => {
  const out = [];
  const els = document.querySelectorAll('h1, h2, h3, table, img');
  let sec = 0, secTitle = '', h2 = '', h3 = '', t = 0, i = 0, id = 0;
  for (const el of els) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'h1') { sec += 1; secTitle = el.textContent.trim(); h2 = ''; h3 = ''; t = 0; i = 0; continue; }
    if (tag === 'h2') { h2 = el.textContent.trim(); h3 = ''; continue; }
    if (tag === 'h3') { h3 = el.textContent.trim(); continue; }
    if (el.closest('table') && tag !== 'table') continue;
    if (tag === 'table' && el.parentElement.closest('table')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    id += 1;
    el.setAttribute('data-cap-id', String(id));
    const item = { id, kind: tag === 'table' ? 'table' : 'image', sec, secTitle, h2, h3,
      x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
    if (tag === 'table') {
      t += 1; item.idx = t;
      const cap = el.querySelector('thead th span');
      item.caption = cap ? cap.textContent.trim() : '';
      item.rows = Array.from(el.querySelectorAll('tr')).map(tr =>
        Array.from(tr.querySelectorAll('th, td')).map(c => c.textContent.replace(/\s+/g, ' ').trim()));
    } else {
      i += 1; item.idx = i;
      item.src = el.getAttribute('src') || '';
      item.address = el.getAttribute('data-address') || '';
    }
    out.push(item);
  }
  return out;
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('omv')
    ap.add_argument('--out')
    ap.add_argument('--scale', type=float, default=2.0)
    ap.add_argument('--pad', type=int, default=8)
    ap.add_argument('--width', type=int, default=1600)
    args = ap.parse_args()

    omv = Path(args.omv).resolve()
    assert omv.exists(), omv
    stamp = datetime.now().strftime('%y%m%d_%H%M')
    out = Path(args.out).resolve() if args.out else omv.parent / '자모비캡쳐' / f'캡처_{omv.stem}_{stamp}'
    out.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix='omv_'))
    with zipfile.ZipFile(omv) as z:
        names = z.namelist()
        z.extractall(tmp)
        n_analyses = sum(1 for n in names if n.endswith('/analysis') and 'empty' not in n)
    html_path = tmp / 'index.html'
    assert html_path.exists(), 'index.html 없음'

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': args.width, 'height': 1000}, device_scale_factor=args.scale)
        page = ctx.new_page()
        page.goto(html_path.as_uri(), wait_until='networkidle')
        page.wait_for_timeout(300)
        items = page.evaluate(JS_COLLECT)
        page.screenshot(path=str(out / 'results_full.png'), full_page=True)
        try:
            page.pdf(path=str(out / 'results_full.pdf'), width='210mm', print_background=True)
        except Exception as e:  # pdf는 보조 산출물
            print('pdf 생략:', e)

        manifest, tables = [], []
        pad = args.pad
        for it in items:
            sec_slug = slug(it['secTitle'], 24)
            if it['kind'] == 'table':
                fname = f"S{it['sec']:02d}_{sec_slug}_T{it['idx']:02d}_{slug(it['caption'], 30)}.png"
                clip = {'x': max(0, it['x'] - pad), 'y': max(0, it['y'] - pad), 'width': it['w'] + 2 * pad, 'height': it['h'] + 2 * pad}
                page.screenshot(path=str(out / fname), clip=clip, full_page=True)
                tables.append({'file': fname, 'sec': it['sec'], 'secTitle': it['secTitle'], 'h2': it['h2'], 'h3': it['h3'],
                               'caption': it['caption'], 'rows': it['rows']})
            else:
                addr = slug(it['address'].replace('/', '_'), 30)
                fname = f"S{it['sec']:02d}_{sec_slug}_I{it['idx']:02d}_{addr}.png"
                src = tmp / it['src'].replace('%20', ' ')
                if it['src'] and src.is_file():  # src가 비면 tmp 디렉터리 자체가 되어 copyfile이 실패한다
                    shutil.copyfile(src, out / fname)
                else:
                    clip = {'x': max(0, it['x'] - pad), 'y': max(0, it['y'] - pad), 'width': it['w'] + 2 * pad, 'height': it['h'] + 2 * pad}
                    page.screenshot(path=str(out / fname), clip=clip, full_page=True)
            manifest.append({'file': fname, 'kind': it['kind'], 'sec': it['sec'], 'secTitle': it['secTitle'], 'h2': it['h2'],
                             'h3': it['h3'], 'caption': it.get('caption', it.get('address', '')),
                             'css_w': round(it['w']), 'css_h': round(it['h']),
                             'mm_w': round(it['w'] / 96 * 25.4, 1), 'mm_h': round(it['h'] / 96 * 25.4, 1)})
        browser.close()

    meta = {'omv': str(omv), 'omv_mtime': datetime.fromtimestamp(omv.stat().st_mtime).isoformat(), 'captured_at': datetime.now().isoformat(),
            'analyses_in_omv': n_analyses, 'sections_rendered': max([m['sec'] for m in manifest], default=0),
            'tables': sum(1 for m in manifest if m['kind'] == 'table'), 'images': sum(1 for m in manifest if m['kind'] == 'image'),
            'scale': args.scale, 'pad_px': args.pad, 'items': manifest}
    (out / 'manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    (out / 'tables.json').write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding='utf-8')
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({k: v for k, v in meta.items() if k != 'items'}, ensure_ascii=False, indent=1))
    for m in manifest:
        print(f"  S{m['sec']:02d} {m['secTitle']:<28} {m['h2'][:18]:<18} {m['kind']:<5} {m['caption'][:36]:<36} -> {m['file']}")
    print('OUT:', out)


if __name__ == '__main__':
    main()
