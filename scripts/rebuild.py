"""Rebuild verified research exports; never synthesizes observations."""
import argparse,os,sys,json,csv
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):
        if Path(path).exists():
            for line in Path(path).read_text(encoding='utf-8').splitlines():
                line=line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip("\"'"))
from scripts.providers.common import SourceError,bounds,timestamp
from scripts.providers.intents_provider import IntentsProvider
from scripts.providers.price_provider import PriceProvider
from scripts.providers.bigquery_provider import BigQueryProvider
from scripts.analysis.metrics import daily_swaps,daily_prices,calendar_series,changes,moving,indexed,freshness,concentration
from scripts.analysis.correlations import comparisons
from scripts.analysis.thesis import verdict
from scripts.provenance import load_export,digest

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,default=str,allow_nan=False)+'\n',encoding='utf-8')

def validate_rows(source,rows,start,end):
    a,b=bounds(start,end)
    if source=='network':
        seen=set()
        for r in rows:
            dt=timestamp(r['date']+'T00:00:00Z')
            if not a<=dt<b or r['date'] in seen:raise SourceError('Network date outside bounds or duplicated')
            seen.add(r['date'])
            for key in ('transactions','signers','contracts'):
                if key=='contracts' and key in r and r[key] is None:continue
                if key not in r or isinstance(r[key],bool) or int(r[key])!=r[key] or r[key]<0:raise SourceError('Invalid network count')
    elif source=='intents':
        for r in rows:
            if not a<=timestamp(r['createdAt'])<b:raise SourceError('Swap outside creation-time bounds')
        daily_swaps(rows)
    else:
        for r in rows:
            if not a<=timestamp(r['timestamp'])<b or not isinstance(r['price'],(float,int)) or not 0<r['price']<float('inf'):raise SourceError('Invalid price observation')

def main(argv=None, root=None):
    workspace=Path(root) if root is not None else ROOT
    load_dotenv(workspace/'.env')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['replay','live','discover'],default='replay');p.add_argument('--start',default=os.getenv('RESEARCH_START','2026-01-01'));p.add_argument('--end',default=os.getenv('RESEARCH_END','2026-02-01'));p.add_argument('--allow-partial',action='store_true');p.add_argument('--execute-bigquery',action='store_true');p.add_argument('--sources',default='network,intents,price')
    args=p.parse_args(argv); start=args.start+'T00:00:00Z' if len(args.start)==10 else args.start;end=args.end+'T00:00:00Z' if len(args.end)==10 else args.end
    a,b=bounds(start,end)
    if a.hour or b.hour or a.minute or b.minute or a.second or b.second or a.microsecond or b.microsecond:raise SourceError('Rebuild requires UTC midnight daily boundaries')
    requested=args.sources.split(',')
    if not set(requested)<={'network','intents','price'}:raise SourceError('Unknown source')
    now=datetime.now(timezone.utc).isoformat();raw=workspace/'data/raw';out=workspace/'public/data'; series={};sources={};daily={};assets=[]
    if args.mode=='discover':
        provider=BigQueryProvider();write(workspace/'data/schema.json',provider.discover());print('Schema and partition metadata saved; no SQL query executed');return 0
    for source in ('network','intents','price'):
        if source not in requested:sources[source]={'status':'unavailable','reason':'Not requested','latest':None,'retrieved_at':None};continue
        try:
            if args.mode=='replay':rows,meta=load_export(raw,source,start,end,require_coverage=False)
            else:
                if source=='network':
                    provider=BigQueryProvider()
                    try: parts,schema=provider.fetch(start,end,execute=args.execute_bigquery)
                    finally:write(workspace/'data/query-jobs.json',provider.jobs)
                    if not args.execute_bigquery:raise SourceError('Dry-run only; use explicit execution flag and paid-query configuration after review')
                    bydate={r['date'].isoformat():{'date':r['date'].isoformat(),'transactions':r['transactions'],'signers':r['signers']} for r in parts['network']}
                    for r in parts['contracts']:
                        d=r['date'].isoformat()
                        if d in bydate:bydate[d]['contracts']=r['contracts']
                    rows=list(bydate.values());write(workspace/'data/schema.json',schema)
                else:rows=(IntentsProvider() if source=='intents' else PriceProvider()).fetch(start,end)
                if os.getenv('SOURCE_REDISTRIBUTION_CONFIRMED')!='true':raise SourceError('Set SOURCE_REDISTRIBUTION_CONFIRMED=true only after confirming export rights')
                validate_rows(source,rows,start,end)
                path=raw/f'{source}.json';write(path,rows)
                meta={'source':source,'path':path.name,'sha256':digest(path),'retrieved_at':now,'start':start,'end':end,'complete':True,'authenticated':True,'synthetic':False,'origin':{'network':'bigquery-public-data.crypto_near_mainnet_us','intents':IntentsProvider.endpoint,'price':'CoinGecko near market_chart/range'}[source],'method':'UTC daily; see docs/methodology.md','redistribution_confirmed':True}
                if source=='network':
                    meta['query_jobs']=provider.jobs
                    meta['location']=provider.location
                write(raw/f'{source}.manifest.json',meta)
            if source=='network':rows=[r for r in rows if start[:10]<=r['date']<end[:10]]
            elif source=='intents':rows=[r for r in rows if a<=timestamp(r['createdAt'])<b]
            else:rows=[r for r in rows if a<=timestamp(r['timestamp'])<b]
            validate_rows(source,rows,start,end)
            if source=='network':items=[r for r in rows if start[:10]<=r['date']<end[:10]]
            elif source=='intents':items=daily_swaps([r for r in rows if a<=timestamp(r['createdAt'])<b])
            else:items=daily_prices([r for r in rows if a<=timestamp(r['timestamp'])<b])
            keys={'network':['transactions','signers','contracts'],'intents':['volume','swaps'],'price':['price']}[source]
            if source=='intents':assets=concentration(rows)
            latest=max((r['date'] for r in items),default=None)
            sources[source]={'status':freshness(latest),'reason':'Authenticated export; hash and coverage validated' if items else 'Verified export contains no observations','latest':latest,'retrieved_at':meta['retrieved_at'],'provenance':meta}
            expected_days=(b-a).days
            if items and len({r['date'] for r in items})<expected_days:
                sources[source].update(status='incomplete',reason=f"{len(items)} observed UTC days out of {expected_days} requested; missing days remain gaps")
            daily[source]=items
            if items:
                for key in keys:series[key]=calendar_series(items,key)
        except (SourceError,ValueError,KeyError,TypeError,OSError) as exc:
            daily.pop(source,None)
            for key in {'network':['transactions','signers','contracts'],'intents':['volume','swaps'],'price':['price']}[source]:series.pop(key,None)
            if source=='intents':assets=[]
            sources[source]={'status':'unavailable','reason':str(exc),'latest':None,'retrieved_at':None};print(f'{source}: unavailable ? {exc}')
        except Exception as exc:
            daily.pop(source,None)
            for key in {'network':['transactions','signers','contracts'],'intents':['volume','swaps'],'price':['price']}[source]:series.pop(key,None)
            if source=='intents':assets=[]
            # Avoid leaking provider responses or credentials; retain actionable error class.
            sources[source]={'status':'unavailable','reason':f'{type(exc).__name__}: provider failed; verify local configuration','latest':None,'retrieved_at':None};print(f'{source}: provider failed ({type(exc).__name__})')
    merged={}
    for key,s in series.items():
        transforms={'value':s,'ma7':moving(s,7),'ma30':moving(s,30),'change':changes(s),'indexed':indexed(s)}
        for date in s.index:
            row=merged.setdefault(date.date().isoformat(),{'date':date.date().isoformat()})
            for label,values in transforms.items():
                v=values.loc[date];row[key if label=='value' else f'{key}_{label}']=None if __import__('pandas').isna(v) else float(v)
    # Decimal volume in CSV remains exact; chart JSON is explicitly a floating visualization.
    chart=list(dict(sorted(merged.items())).values());stats=comparisons(series);state=verdict(stats)
    observed={key:{r['date'] for r in chart if r.get(key) is not None} for key in ('volume','transactions','signers','contracts','price')}
    def overlap(keys):
        dates=sorted(set.intersection(*(observed[k] for k in keys)))
        return {'start':dates[0] if dates else None,'end':dates[-1] if dates else None,'observations':len(dates)}
    coverage={'adoption':overlap(('volume','transactions','signers')),
              'native_and_intents':overlap(('volume','transactions','signers','contracts')),
              'verdict_required':overlap(('volume','transactions','signers','contracts','price')),
              'paired_daily_changes':max((r['n'] for r in stats),default=0)}
    dashboard={'generated_at':now,'window':{'start':start,'end':end},'sources':sources,'series':chart,'correlations':stats,'verdict':state,'daily':daily,'assets':assets,'freshness_threshold_days':3,'research_coverage':coverage}
    out.mkdir(parents=True,exist_ok=True)
    for name in ('network','intents','price'):
        items=daily.get(name,[]);fields={'network':['date','transactions','signers','contracts'],'intents':['date','swaps','volume'],'price':['date','price']}[name]
        with (out/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)
    evidence={'verdict':state,'correlations':stats,'supporting':[],'contradicting':[],'limitations':['Correlation is not causation','1Click volume is not NEAR token demand']}
    base=next((r for r in stats if r['pair']=='volume \u2192 price' and r['lag']==0 and r['rho'] is not None),None)
    if base:
        for r in stats:
            if r['lag']==0 and r['pair']!=base['pair'] and r['rho'] is not None:
                item={'pair':r['pair'],'rho':r['rho'],'price_rho':base['rho'],'difference':r['rho']-base['rho'],'n':r['n']}
                evidence['supporting' if item['difference']>0 else 'contradicting'].append(item)
    write(out/'dashboard.json',dashboard);write(workspace/'data/processed/dashboard.json',dashboard);write(workspace/'data/processed/evidence.json',evidence)
    manifest={'generated_at':now,'mode':args.mode,'sources':sources,'outputs':[{'path':f.relative_to(workspace).as_posix(),'sha256':digest(f)} for f in sorted(out.glob('*')) if f.is_file() and f.name!='manifest.json']}
    write(workspace/'data/manifest.json',manifest);write(out/'manifest.json',manifest)
    missing=any(sources[s]['status'] in ('unavailable','incomplete') for s in requested)
    print(f'Dashboard exports written. Verdict: {state}. Complete rebuild: {not missing}')
    return 2 if missing and not args.allow_partial else 0

if __name__=='__main__':
    try:sys.exit(main())
    except SourceError as e:print(e,file=sys.stderr);sys.exit(2)
    except (ValueError,TypeError):print('Invalid configuration value; check environment settings and requested bounds',file=sys.stderr);sys.exit(2)
