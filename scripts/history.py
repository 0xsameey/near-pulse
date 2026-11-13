"""Append-only verified observations; source-specific windows, revisions fail closed."""
import hashlib,json,os,shutil,tempfile
from pathlib import Path
from datetime import datetime,timezone
from scripts.providers.common import SourceError,bounds,timestamp
from scripts.provenance import load_export,digest
from scripts.rebuild import write,validate_rows,main as rebuild

def intervals(meta):return meta.get('coverage_intervals',[{'start':meta['start'],'end':meta['end']}])

def union_intervals(items):
    merged=[]
    for item in sorted(items,key=lambda x:timestamp(x['start'])):
        a,b=bounds(item['start'],item['end'])
        if merged and a<=timestamp(merged[-1]['end']):
            merged[-1]['end']=max(timestamp(merged[-1]['end']),b).isoformat()
        else:merged.append({'start':a.isoformat(),'end':b.isoformat()})
    return merged

def read_source(root,source):
    path=Path(root)/'data/raw'/f'{source}.manifest.json'
    if not path.exists():return None
    meta=json.loads(path.read_text(encoding='utf-8'))
    rows,meta=load_export(Path(root)/'data/raw',source,meta['start'],meta['end'],require_coverage=False)
    return rows,meta

def unique(items):
    found={}
    for item in items:
        key=hashlib.sha256(json.dumps(item,sort_keys=True,default=str).encode()).hexdigest()
        found.setdefault(key,item)
    return list(found.values())

def merge_source(source,old_rows,old_meta,new_rows,new_meta):
    identity=(lambda r:r['date']) if source=='network' else (lambda r:(r['depositAddress'],r['depositMemo'])) if source=='intents' else (lambda r:r['timestamp'])
    indexed={}
    for row in old_rows:
        key=identity(row)
        if key in indexed and indexed[key]!=row:raise SourceError('Conflicting stored source identity')
        indexed[key]=row
    new_keys=set()
    for row in new_rows:
        key=identity(row);new_keys.add(key)
        if key in indexed:
            if source=='network':
                merged=dict(indexed[key])
                for metric,value in row.items():
                    prior=merged.get(metric)
                    if prior is not None and value is not None and prior!=value:
                        raise SourceError(f'Historical revision rejected: {source}/{key}/{metric}')
                    if value is not None or metric not in merged:merged[metric]=value
                indexed[key]=merged
            elif indexed[key]!=row:raise SourceError('Historical record revision rejected; existing source preserved')
        else:
            if source=='intents' and old_meta:
                t=timestamp(row['createdAt'])
                if any(timestamp(i['start'])<=t<timestamp(i['end']) for i in intervals(old_meta)):
                    raise SourceError('New swap revises an already complete historical interval; review before replacing')
            indexed[key]=row
    if source=='intents':
        a,b=bounds(new_meta['start'],new_meta['end'])
        if any(a<=timestamp(r['createdAt'])<b and identity(r) not in new_keys for r in old_rows):
            raise SourceError('Refreshed complete interval omits previously verified swaps')
    order=(lambda r:r['date']) if source=='network' else (lambda r:(r['createdAt'],r['depositAddress'],r['depositMemo'] or '')) if source=='intents' else (lambda r:r['timestamp'])
    rows=sorted(indexed.values(),key=order)
    coverage=union_intervals([*(intervals(old_meta) if old_meta else []),*intervals(new_meta)])
    meta={**new_meta,'start':coverage[0]['start'],'end':coverage[-1]['end'],'coverage_intervals':coverage}
    for name in ('query_jobs','response_pages'):
        if name in new_meta or old_meta and name in old_meta:
            meta[name]=unique([*(old_meta.get(name,[]) if old_meta else []),*new_meta.get(name,[])])
    meta['segments']=[*(old_meta.get('segments',[{k:v for k,v in old_meta.items() if k not in ('segments',)}]) if old_meta else []),
                      {k:v for k,v in new_meta.items() if k not in ('segments',)}]
    return rows,meta

def publish_history(root,source,rows,meta,secret=''):
    root=Path(root);(root/'data').mkdir(parents=True,exist_ok=True)
    lock=root/'data/.history.lock'
    try:handle=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise SourceError('Another history publication is active; retry after it completes. Review stale locks manually.') from None
    try:
        os.write(handle,str(os.getpid()).encode())
        return _publish_history(root,source,rows,meta,secret)
    finally:
        os.close(handle);lock.unlink(missing_ok=True)

def _publish_history(root,source,rows,meta,secret=''):
    validate_rows(source,rows,meta['start'],meta['end'])
    root=Path(root);stored={s:read_source(root,s) for s in ('network','intents','price')}
    previous=stored[source]
    merged,manifest=merge_source(source,previous[0] if previous else [],previous[1] if previous else None,rows,meta)
    with tempfile.TemporaryDirectory(prefix='near-pulse-history-') as directory:
        stage=Path(directory)
        for name,item in stored.items():
            if item is None:continue
            old_rows,old_meta=item
            for relative in (old_meta['path'],f'{name}.manifest.json',*[p['path'] for p in old_meta.get('response_pages',[])]):
                target=stage/'data/raw'/relative;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(root/'data/raw'/relative,target)
        # Immutable snapshots retain original verified bytes and original manifest.
        if previous:
            old_meta=previous[1];base=stage/'data/raw/history'/source
            base.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/'data/raw'/old_meta['path'],base/(old_meta['sha256']+'.json'))
            old_manifest=root/f'data/raw/{source}.manifest.json'
            shutil.copyfile(old_manifest,base/(digest(old_manifest)+'.manifest.json'))
        target=stage/f'data/raw/{source}.json';write(target,merged)
        manifest.update(path=f'{source}.json',sha256=digest(target))
        for page in manifest.get('response_pages',[]):
            dest=stage/'data/raw'/page['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/'data/raw'/page['path'],dest)
        write(stage/f'data/raw/{source}.manifest.json',manifest)
        stored[source]=(merged,manifest)
        available={k:v for k,v in stored.items() if v is not None}
        start=min(v[1]['start'] for v in available.values());end=max(v[1]['end'] for v in available.values())
        code=rebuild(['--sources',','.join(available),'--start',start,'--end',end,'--allow-partial'],root=stage)
        if code:raise SourceError('History replay failed; production sources preserved')
        dashboard=json.loads((stage/'public/data/dashboard.json').read_text())
        for name,(expected,metadata) in available.items():
            replayed,_=load_export(stage/'data/raw',name,metadata['start'],metadata['end'],require_coverage=False)
            if replayed!=expected or expected and not dashboard['daily'].get(name):
                raise SourceError(f'History replay lost {name} observations; publication rejected')
        files=[p for p in stage.rglob('*') if p.is_file()]
        if secret and any(secret.encode() in p.read_bytes() for p in files):raise SourceError('Credential-bearing history output rejected')
        backups={}
        try:
            for file in files:
                dest=root/file.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True)
                backups[dest]=dest.read_bytes() if dest.exists() else None
                pending=dest.with_name(dest.name+'.pending');shutil.copyfile(file,pending);os.replace(pending,dest)
        except Exception:
            for dest,prior in backups.items():
                if prior is None:dest.unlink(missing_ok=True)
                else:dest.write_bytes(prior)
            raise
    return manifest
