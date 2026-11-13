import json,hashlib
from pathlib import Path
from scripts.providers.common import SourceError,bounds,timestamp
SOURCES={'network','intents','price'}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_export(root,source,start,end,require_coverage=True):
    root=Path(root).resolve();meta_path=root/f'{source}.manifest.json'
    if not meta_path.exists():raise SourceError(f'No provenance-backed {source} source export')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    required={'source','path','sha256','retrieved_at','start','end','complete','origin','method','redistribution_confirmed'}
    if not required<=meta.keys() or meta['source']!=source or meta['complete'] is not True or meta['redistribution_confirmed'] is not True:raise SourceError('Incomplete provenance or redistribution not confirmed')
    if meta.get('synthetic') or meta.get('authenticated') is not True:raise SourceError('Synthetic/unverified source prohibited')
    expected={'network':'bigquery-public-data.crypto_near_mainnet_us','intents':'https://explorer.near-intents.org/api/v0/transactions','price':'CoinGecko near market_chart/range'}
    if meta['origin']!=expected.get(source) or not isinstance(meta['method'],str) or not meta['method']:raise SourceError('Source attribution/method validation failed')
    if source=='network' and not meta.get('query_jobs'):raise SourceError('Network provenance must retain source queries and job IDs')
    path=(root/meta['path']).resolve()
    if not path.is_relative_to(root) or not path.is_file() or digest(path)!=meta['sha256']:raise SourceError('Source hash/path validation failed')
    for response in meta.get('response_pages',[]):
        response_path=(root/response['path']).resolve()
        if not response_path.is_relative_to(root) or not response_path.is_file() or digest(response_path)!=response['sha256']:
            raise SourceError('Raw API response hash/path validation failed')
    a,b=bounds(start,end);ma,mb=bounds(meta['start'],meta['end']);timestamp(meta['retrieved_at'])
    if require_coverage:
        intervals=meta.get('coverage_intervals',[{'start':meta['start'],'end':meta['end']}])
        cursor=a
        for interval in sorted(intervals,key=lambda r:r['start']):
            left,right=bounds(interval['start'],interval['end'])
            if left<=cursor<right:cursor=right
        if cursor<b:raise SourceError('Requested bounds exceed verified source coverage or cross a gap')
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,list):raise SourceError('Source export must be a list')
    return data,meta
