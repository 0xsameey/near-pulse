"""Bounded authenticated 1Click acquisition with staged, source-preserving replay."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.providers.common import SourceError,bounds
from scripts.providers.intents_provider import IntentsProvider
from scripts.analysis.metrics import daily_swaps,concentration,add_decimal
from scripts.rebuild import load_dotenv,main as rebuild
from scripts.provenance import load_export,digest
from scripts.history import publish_history,read_source


def safe_json(path,data,secret):
    content=json.dumps(data,indent=2,default=str,allow_nan=False)+'\n'
    if secret and secret in content:raise SourceError('Refusing to persist credential-bearing response or report')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')


def acquire(root,start,end,probe=False,provider=None):
    root=Path(root);secret=os.getenv('INTENTS_EXPLORER_JWT','').strip()
    provider=provider or IntentsProvider()
    report={'started_at':datetime.now(timezone.utc).isoformat(),'endpoint':provider.endpoint,
            'credential_loaded':bool(secret),'start':start,'end':end,'mode':'probe' if probe else 'export',
            'status':'started','authenticated_access_confirmed':False,'schema_validated':False,
            'pagination_complete':False,'observed_coverage':None,'successful_swaps':None,'input_volume_usd':None,
            'daily':None,'response_pages':[],'http_events':[],
            'scope':'Successful 1Click swaps, grouped by createdAt UTC; not all Intents activity or completion-day volume'}
    code=2
    try:
        if not secret:raise SourceError('INTENTS_EXPLORER_JWT absent')
        if not probe and os.getenv('SOURCE_REDISTRIBUTION_CONFIRMED')!='true':
            raise SourceError('Set SOURCE_REDISTRIBUTION_CONFIRMED=true to confirm source-export permission')
        # Validate other existing source exports before any retrieval. A mismatch
        # cannot silently remove an established network/price dataset.
        preserved={}
        if not probe:
            for source in ('network','price'):
                manifest=root/f'data/raw/{source}.manifest.json'
                if manifest.exists():
                    meta=json.loads(manifest.read_text(encoding='utf-8'))
                    read_source(root,source)
                    preserved[source]=meta
            import pandas  # Fail before HTTP if processing dependencies are absent.
        rows=provider.fetch(start,end)
        if not any(event.get('http_status')==200 for event in getattr(provider.client,'events',[])):
            raise SourceError('No successful authenticated HTTP response is recorded; export rejected')
        if not provider.audit.get('complete'):raise SourceError('Pagination incomplete; dashboard unchanged')
        daily=daily_swaps(rows)
        # Reuse exact decimal aggregation, avoiding float conversion of totals.
        from decimal import Decimal
        total=Decimal(0)
        for row in daily:total=add_decimal(total,Decimal(row['volume']))
        concentration(rows)  # Validate asset identities/amounts before publishing.
        report.update(status='probe_complete' if probe else 'acquired',schema_validated=bool(rows),
                      pagination_complete=True,successful_swaps=len(rows),input_volume_usd=str(total),daily=daily,
                      observed_coverage={'first_created_at':min((r['createdAt'] for r in rows),default=None),
                                         'last_created_at':max((r['createdAt'] for r in rows),default=None)})
        if rows:
            report['observed_field_types']={key:sorted({type(r[key]).__name__ for r in rows if key in r})
                                            for key in sorted({k for r in rows for k in r})}
        if probe:return 0,report
        with tempfile.TemporaryDirectory(prefix='near-pulse-intents-') as directory:
            stage=Path(directory)
            for source,meta in preserved.items():
                for relative in (meta['path'],f'{source}.manifest.json'):
                    destination=stage/'data/raw'/relative
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(root/'data/raw'/relative,destination)
            raw=stage/'data/raw/intents.json'
            safe_json(raw,rows,secret)
            capture_responses(provider,root,report,secret)
            meta={'source':'intents','path':'intents.json','sha256':digest(raw),
                  'retrieved_at':datetime.now(timezone.utc).isoformat(),'start':start,'end':end,
                  'complete':True,'authenticated':True,'synthetic':False,
                  'origin':provider.endpoint,'redistribution_confirmed':True,
                  'method':report['scope'],'pagination':provider.audit,
                  'response_pages':report['response_pages'],'observed_field_types':report.get('observed_field_types',{})}
            merged_manifest=publish_history(root,'intents',rows,meta,secret)
            report['merged_coverage']=merged_manifest['coverage_intervals']
        report['status']='verified_and_exported'
        return 0,report
    except Exception as error:
        report.update(status='failed',error_type=type(error).__name__,error=str(error))
        # Do not echo an arbitrary exception that could include an upstream token.
        if secret and secret in report['error']:report['error']='Sensitive upstream error omitted'
        return 2,report
    finally:
        client=provider.client
        report['http_events']=getattr(client,'events',[])
        report['authenticated_access_confirmed']=any(e.get('http_status')==200 for e in report['http_events'])
        report['pagination']=provider.audit
        report['pagination_complete']=provider.audit.get('complete',False)
        report['completed_at']=datetime.now(timezone.utc).isoformat()
        capture_responses(provider,root,report,secret)
        safe_json(root/'validation-evidence/intents-acquisition.json',report,secret)


def capture_responses(provider,root,report,secret):
    if report['response_pages']:return
    responses=getattr(provider.client,'responses',[])
    if not responses:return
    run_id=report['started_at'].replace(':','').replace('+','_')
    for index,response in enumerate(responses,1):
        body=response['body']
        if secret and secret.encode() in body:raise SourceError('Refusing to persist credential-bearing response')
        relative=Path('intents-responses')/run_id/f'page-{index:04}.json'
        path=Path(root)/'data/raw'/relative
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
        report['response_pages'].append({'path':relative.as_posix(),'sha256':hashlib.sha256(body).hexdigest(),
                                          'request':response['request']})


def main(argv=None):
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',default='2026-11-09')
    parser.add_argument('--end',default='2026-11-10')
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--page-size',type=int)
    parser.add_argument('--max-pages',type=int)
    args=parser.parse_args(argv)
    start=args.start+'T00:00:00Z' if len(args.start)==10 else args.start
    end=args.end+'T00:00:00Z' if len(args.end)==10 else args.end
    a,b=bounds(start,end)
    if args.probe:
        if (b-a).total_seconds()>600:raise SourceError('Probe window must be at most ten minutes')
    elif any((v.hour or v.minute or v.second or v.microsecond) for v in (a,b)) or (b-a).days>14 or b>datetime.now(timezone.utc):
        raise SourceError('Export requires 1–14 fully elapsed UTC days')
    size=args.page_size if args.page_size is not None else (25 if args.probe else int(os.getenv('INTENTS_PAGE_SIZE','1000')))
    pages=args.max_pages if args.max_pages is not None else (3 if args.probe else int(os.getenv('INTENTS_MAX_PAGES','100')))
    if args.probe and (size>25 or pages>3):raise SourceError('Probe budget is at most 25 rows/page and 3 pages')
    os.environ['INTENTS_PAGE_SIZE']=str(size);os.environ['INTENTS_MAX_PAGES']=str(pages)
    code,report=acquire(ROOT,start,end,args.probe)
    print(json.dumps({k:report[k] for k in ('status','authenticated_access_confirmed','pagination_complete','observed_coverage','successful_swaps','input_volume_usd')},indent=2))
    if code:print(report.get('error','Acquisition failed'),file=sys.stderr)
    return code

if __name__=='__main__':
    try:sys.exit(main())
    except (SourceError,ValueError,OSError) as error:print(error,file=sys.stderr);sys.exit(2)
