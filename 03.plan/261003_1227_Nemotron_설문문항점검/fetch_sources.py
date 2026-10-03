"""Fetch bounded public HF viewer slices; never download dataset shards."""
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
DATASET = 'nvidia/Nemotron-Personas-Korea'
BASE = 'https://datasets-server.huggingface.co/'

def fetch(url):
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {'url': url, 'requested_at_utc': stamp}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'survey-item-review/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise RuntimeError('Bounded request exceeded 2 MB limit')
            result.update(status=response.status, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                          headers=dict(response.headers), data=json.loads(raw))
    except Exception as exc:
        result.update(error=type(exc).__name__ + ': ' + str(exc))
        if isinstance(exc, urllib.error.HTTPError):
            result['error_body'] = exc.read(4096).decode('utf-8', errors='replace')
    result['completed_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result

def viewer_url(endpoint, **kwargs):
    args = {'dataset': DATASET, 'config': 'default', 'split': 'train', **kwargs}
    return BASE + endpoint + '?' + urllib.parse.urlencode(args)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'initial'
    if mode == 'initial':
        urls = [('dataset_metadata', 'https://huggingface.co/api/datasets/' + DATASET)]
        urls += [('search_' + str(i+1), viewer_url('search', query=q, offset=0, length=12))
                 for i, q in enumerate(['현장소장', '안전관리자', '공사감독'])]
    elif mode == 'rows':
        urls = [('row_' + idx, viewer_url('rows', offset=int(idx), length=1)) for idx in sys.argv[2:]]
    elif mode == 'filter':
        urls = [('filtered', viewer_url('filter', where=sys.argv[2], offset=0, length=12))]
    elif mode == 'construction':
        condition = '\"province\"=\'경기\' AND (\"occupation\">=\'건설\' AND \"occupation\"<\'건성\')'
        urls = [('construction_gyeonggi', viewer_url('filter', where=condition, offset=0, length=12)),
                ('preview_row', viewer_url('rows', offset=0, length=1))]
    elif mode == 'exact':
        urls = [('construction_manager', viewer_url('filter', where='\"occupation\"=\'건설 및 광업 관련 관리자\'', offset=0, length=16)),
                ('civil_engineer', viewer_url('filter', where='\"occupation\"=\'토목공학 기술자\'', offset=0, length=12)),
                ('architectural_engineer', viewer_url('filter', where='\"occupation\"=\'건축공학 기술자\'', offset=0, length=12))]
    elif mode == 'pages':
        start = int(sys.argv[2]) if len(sys.argv)>2 else 0
        urls = [('page_' + str(i), viewer_url('rows', offset=i, length=100)) for i in range(start, start+1000, 100)]
    else:
        raise SystemExit('Unknown mode')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch, [u for _, u in urls]))
    for (name, _), result in zip(urls, results):
        (ROOT / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(name, {k:v for k,v in result.items() if k in ('status','error','bytes')})
        if 'data' in result and 'rows' in result['data']:
            print('total', result['data'].get('num_rows_total'))
            for row in result['data']['rows']:
                r = row['row']
                if mode == 'pages' and not (re.search('건설|건축|토목', r.get('occupation','')+' '+r.get('professional_persona','')) and re.search('관리|감독|소장|공정', r.get('professional_persona','')+' '+r.get('skills_and_expertise',''))):
                    continue
                print(json.dumps({'row_idx':row['row_idx'], **{k:r.get(k) for k in
                     ('uuid','occupation','province','district','sex','age','professional_persona','skills_and_expertise')}}, ensure_ascii=False))
        elif 'data' in result:
            print('revision', result['data'].get('sha'))

if __name__ == '__main__':
    main()
