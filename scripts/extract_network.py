"""Schema-validated, budgeted network acquisition; publishes only a validated window."""
import argparse
import json
import os
import sys
import tempfile
import shutil
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.providers.bigquery_provider import BigQueryProvider, DATASET, DEFAULT_LOCATION
from scripts.providers.common import SourceError
from scripts.provenance import digest
from scripts.rebuild import load_dotenv, validate_rows, write, main as rebuild
from scripts.history import publish_history

REQUIRED = {
    'transactions': {'block_date': 'DATE', 'transaction_hash': 'STRING',
                     'signer_account_id': 'STRING', 'block_timestamp_utc': 'TIMESTAMP'},
    'receipt_actions': {'block_date': 'DATE', 'receipt_id': 'STRING',
                        'index_in_action_receipt': 'INTEGER', 'action_kind': 'STRING',
                        'block_timestamp_utc': 'TIMESTAMP'},
}


def validate_schema(schema,include_contracts=True):
    for table, expected in REQUIRED.items():
        if table=='receipt_actions' and not include_contracts:continue
        info = schema.get(table, {})
        fields = {f['name']: f for f in info.get('schema', [])}
        if info.get('time_partitioning') != {'type': 'DAY', 'field': 'block_date'}:
            # Extra metadata attributes do not change the partitioning contract.
            partition = info.get('time_partitioning') or {}
            if partition.get('type') != 'DAY' or partition.get('field') != 'block_date':
                raise SourceError(f'{table}: expected daily block_date partitioning')
        for name, kind in expected.items():
            if fields.get(name, {}).get('type') != kind or fields[name].get('mode') == 'REPEATED':
                raise SourceError(f'{table}.{name}: expected scalar {kind}; schema changed')
    if not include_contracts:return
    action = next(f for f in schema['receipt_actions']['schema'] if f['name'] == 'action_kind')
    if 'FUNCTION_CALL' not in action.get('description', ''):
        raise SourceError('FUNCTION_CALL enum is not confirmed by source schema description')


def days(start, end):
    return [start + timedelta(days=i) for i in range((end-start).days)]


def is_partition_metadata_denied(error):
    """Only a typed 403 naming this exact view as the denied table can fallback."""
    try:
        from google.api_core.exceptions import Forbidden
    except ImportError:
        return False
    if not isinstance(error, Forbidden):
        return False
    # Match the denied resource, not a view mentioned incidentally in SQL/error
    # context. Dataset/auth failures and other table denials remain fatal.
    message = getattr(error, 'message', '')
    resource = re.escape(DATASET).replace(r'\.', r'[.:]', 1)
    pattern = r'Access Denied:\s*Table\s+`?' + resource + r'\.INFORMATION_SCHEMA\.PARTITIONS`?(?=[:\s,;]|$)'
    return bool(re.search(pattern, message, re.IGNORECASE))


def validate_partitions(rows, start, end,include_contracts=True):
    expected = {(table, day.strftime('%Y%m%d')) for table in REQUIRED if include_contracts or table=='transactions' for day in days(start, end)}
    indexed = {}
    for row in rows:
        key = (row['table_name'], row['partition_id'])
        if key not in expected or key in indexed or not isinstance(row['total_rows'], int) or row['total_rows'] <= 0:
            raise SourceError('Unexpected, duplicated or empty partition metadata')
        indexed[key] = row
    missing = sorted(expected - indexed.keys())
    if missing:
        raise SourceError('Requested partitions unavailable: ' + ', '.join(f'{t}/{d}' for t,d in missing))
    return indexed


def validate_metrics(parts, partition_rows, start, end,include_contracts=True):
    # None denotes a specifically authorized metadata-403 fallback. An empty
    # successful metadata response is still missing partitions, never fallback.
    partitions = validate_partitions(partition_rows, start, end,include_contracts) if partition_rows is not None else None
    if set(parts) != ({'transactions','signers','contracts'} if include_contracts else {'transactions','signers'}):
        raise SourceError('Required executed metric query results missing')
    expected = {d.isoformat() for d in days(start, end)}
    indexed = {}
    for metric, rows in parts.items():
        mapped = {}
        for row in rows:
            day = row['date'].isoformat() if isinstance(row['date'], date) else row['date']
            if day not in expected or day in mapped:
                raise SourceError(f'{metric}: missing/duplicate/out-of-window day')
            mapped[day] = row
        if set(mapped) != expected:
            raise SourceError(f'{metric}: incomplete daily coverage')
        indexed[metric] = mapped
    combined = []
    checks = []
    for day in sorted(expected):
        tx = indexed['transactions'][day]; action = indexed['contracts'][day] if include_contracts else None
        signer = indexed['signers'][day]
        partition_id = day.replace('-', '')
        numeric = [(tx,'transactions'),(tx,'missing_signers'),(tx,'observed_hours'),(signer,'signers')]
        if include_contracts:numeric.extend([(action,'contracts'),(action,'receipt_action_rows'),(action,'missing_action_kinds'),(action,'observed_hours')])
        if any(isinstance(row.get(key),bool) or not isinstance(row.get(key),int) or row[key]<0 for row,key in numeric):
            raise SourceError(f'{day}: invalid or missing integer metric counts')
        action_rows = action['receipt_action_rows'] if include_contracts else None
        if partitions is not None:
            tx_rows = partitions[('transactions', partition_id)]['total_rows']
            if tx['transactions'] != tx_rows or include_contracts and action_rows != partitions[('receipt_actions', partition_id)]['total_rows']:
                raise SourceError(f'{day}: aggregate count differs from earlier partition row metadata; source may have changed')
        if tx['transactions']<=0 or include_contracts and action_rows<=0:
            raise SourceError(f'{day}: bounded queries did not establish nonempty data in both tables')
        if tx['observed_hours'] != 24 or include_contracts and action['observed_hours'] != 24:
            raise SourceError(f'{day}: source lacks observations in all 24 UTC hours')
        if tx['missing_signers'] or include_contracts and action['missing_action_kinds']:
            raise SourceError(f'{day}: null signer or action-kind observations')
        if not 0 < signer['signers'] <= tx['transactions'] or include_contracts and not 0 <= action['contracts'] <= action_rows:
            raise SourceError(f'{day}: metric consistency check failed')
        combined.append({'date': day, 'transactions': tx['transactions'],
                         'signers': signer['signers'], 'contracts': action['contracts'] if include_contracts else None})
        checks.append({'date': day, 'transactions_match_partition_rows': True if partitions is not None else None,
                       'receipt_actions_match_partition_rows': True if include_contracts and partitions is not None else None,
                       'availability_basis': 'partition_metadata_and_executed_bounded_queries' if partitions is not None else 'executed_bounded_queries',
                       'observed_hours': 24})
    return combined, checks


def merge_contract_coverage(contracts, coverage, start, end):
    """Join only small daily query results, rejecting missing/changed table totals."""
    expected = {d.isoformat() for d in days(start,end)}
    def index(rows):
        mapped={}
        for row in rows:
            key=row['date'].isoformat() if isinstance(row['date'],date) else row['date']
            if key not in expected or key in mapped:
                raise SourceError('Contract coverage: duplicate or out-of-window date')
            mapped[key]=row
        if set(mapped)!=expected:
            raise SourceError('Contract coverage: incomplete daily coverage')
        return mapped
    actions, hours = index(contracts), index(coverage)
    result=[]
    for day in sorted(expected):
        left,right=actions[day],hours[day]
        for row in (left,right):
            count=row.get('receipt_action_rows')
            if isinstance(count,bool) or not isinstance(count,int) or count<=0:
                raise SourceError(f'{day}: receipt coverage lacks valid positive row counts')
        if left['receipt_action_rows']!=right['receipt_action_rows']:
            raise SourceError(f'{day}: receipt action and coverage row totals differ; source may have changed')
        result.append({**left,'observed_hours':right.get('observed_hours')})
    return result


def acquire(provider, start, end, execute, report,include_contracts=True):
    schema = provider.discover() if include_contracts else provider.discover(tables=('transactions',))
    validate_schema(schema,include_contracts)
    report['schema'] = schema
    report['query_strategy'] = {
        'transactions_and_signers':'One exact daily aggregate over the same transaction columns; no distinct-count summation across subsets',
        'function_calls':'Exact action_kind aggregation separated from timestamp-only receipt coverage',
        'coverage_consistency':'Receipt row totals must agree between both executed column-specific queries',
        'range_fallback':'Rejected windows try two-day spans, then one day; a single-day rejection remains fatal'}
    if not include_contracts:report['query_strategy']['function_calls']='Not requested; missing values remain null'
    def query(file, left, right, action=False):
        sql = (ROOT/'sql'/file).read_text(encoding='utf-8')
        params = [provider.bq.ScalarQueryParameter('start', 'DATE', left),
                  provider.bq.ScalarQueryParameter('end', 'DATE', right)]
        if action: params.append(provider.bq.ScalarQueryParameter('action','STRING','FUNCTION_CALL'))
        return sql, params
    metadata_sql, params = query('network_partitions.sql' if include_contracts else 'network_transaction_partitions.sql', start, end)
    try:
        partition_rows = provider.run(metadata_sql, params, execute)
    except Exception as error:
        if not is_partition_metadata_denied(error):
            raise
        partition_rows = None
        report['partition_metadata_error'] = {'type':type(error).__name__,'message':str(error),
                                            'resource':DATASET+'.INFORMATION_SCHEMA.PARTITIONS'}
        report['partition_verification'] = {'mode':'bounded_data_queries','status':'pending',
            'limitation':'Partition metadata comparison unavailable because this view is permission denied. Executed bounded query results must establish daily coverage; dry-runs do not.'}
    else:
        report['partition_verification'] = {'mode':'partition_metadata','status':'observed' if execute else 'not_observed'}
    report['partitions'] = partition_rows
    report['partitions_observed_at'] = datetime.now(timezone.utc).isoformat() if execute and partition_rows is not None else None
    if execute and partition_rows is not None: validate_partitions(partition_rows, start, end,include_contracts)
    planned = []
    # Try the requested range; if its estimate is too high, try individual days.
    # No data query executes before every planned query has passed a dry-run.
    groups=[('transactions','verified_transactions.sql')]
    if include_contracts:groups.extend([
                         ('contracts','verified_function_calls.sql'),
                         ('contract_coverage','verified_receipt_coverage.sql')])
    for metric, file in groups:
        sql, params = query(file, start, end, metric=='contracts')
        try:
            before=len(provider.jobs)
            try:provider.run(sql, params, False)
            finally:
                for record in provider.jobs[before:]:
                    record.update(metric=metric,sql_file=file,start=start.isoformat(),end=end.isoformat())
            planned.append((metric, sql, params))
        except SourceError:
            if not provider.jobs or 'exceeds per-query limit' not in provider.jobs[-1].get('rejected','') or (end-start).days == 1:
                raise
            # Try two-day spans before individual dates: exact daily GROUP BY
            # preserves signer identity while reducing full-cap reservations.
            for offset in range(0,(end-start).days,2):
                day=start+timedelta(days=offset);stop=min(day+timedelta(days=2),end)
                sql,params=query(file,day,stop,metric=='contracts')
                before=len(provider.jobs)
                try:
                    provider.run(sql,params,False)
                    planned.append((metric,sql,params))
                except SourceError:
                    if not provider.jobs or 'exceeds per-query limit' not in provider.jobs[-1].get('rejected','') or (stop-day).days==1:raise
                    for single in days(day,stop):
                        single_sql,single_params=query(file,single,single+timedelta(days=1),metric=='contracts')
                        single_before=len(provider.jobs)
                        try:provider.run(single_sql,single_params,False)
                        finally:
                            for record in provider.jobs[single_before:]:
                                record.update(metric=metric,sql_file=file,start=single.isoformat(),end=(single+timedelta(days=1)).isoformat())
                        planned.append((metric,single_sql,single_params))
                finally:
                    if len(provider.jobs)>before:
                        provider.jobs[before].update(metric=metric,sql_file=file,start=day.isoformat(),end=stop.isoformat())
    # Conservative full-cap reservations, including the metadata job already run.
    if execute and provider.reserved + len(planned)*provider.cap > provider.total:
        raise SourceError('Planned full-cap reservations exceed cumulative budget; no data queries executed')
    if not execute: return None
    report['planned_data_jobs']=len(planned)
    report['planned_maximum_bytes']=provider.reserved+len(planned)*provider.cap
    parts = {'transactions': [], 'contracts': [], 'contract_coverage': []}
    for metric, sql, params in planned:
        before=len(provider.jobs)
        try:parts[metric].extend(provider.run(sql, params, True))
        finally:
            for record in provider.jobs[before:]:
                record['metric']=metric
    # Distinct signers are computed over the full day's transaction rows in SQL,
    # never approximated or summed across shards/sub-day account sets.
    parts['signers']=[{'date':row['date'],'signers':row['signers']} for row in parts['transactions']]
    report['contract_coverage']=parts.pop('contract_coverage')
    if include_contracts:parts['contracts']=merge_contract_coverage(parts['contracts'],report['contract_coverage'],start,end)
    else:parts.pop('contracts')
    rows, checks = validate_metrics(parts, partition_rows, start, end,include_contracts)
    report['partition_verification']['status'] = 'validated'
    report['partition_verification']['data_observed_at'] = datetime.now(timezone.utc).isoformat()
    report['consistency_checks'] = checks
    report['metrics'] = rows
    return rows


def main(argv=None):
    load_dotenv(ROOT/'.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-11-09')
    parser.add_argument('--end', default='2026-11-12', help='Exclusive UTC date')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--skip-contracts',action='store_true',help='Acquire exact transactions/signers only; leave contract observations missing')
    args = parser.parse_args(argv)
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if not 1 <= (end-start).days <= 14 or end > datetime.now(timezone.utc).date():
        raise SourceError('Historical acquisition requires 1–14 fully elapsed UTC days')
    schema_path = ROOT/'data/schema.json'
    validate_schema(json.loads(schema_path.read_text(encoding='utf-8')),not args.skip_contracts)
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'project': os.getenv('BIGQUERY_PROJECT_ID'),
              'location':os.getenv('BIGQUERY_LOCATION') or DEFAULT_LOCATION,
              'include_contracts':not args.skip_contracts,
              'dataset': DATASET, 'start': start.isoformat(), 'end': end.isoformat(),
              'saved_schema_sha256': digest(schema_path), 'execute_requested': args.execute,
              'status': 'started', 'jobs': [], 'metrics': None,
              'completeness_policy': 'Elapsed UTC days; positive executed daily table counts; 24-hour coverage; partition row-count comparison when metadata is accessible. Only a specific metadata-view 403 permits omission of that comparison. This does not prove absence of upstream indexing omissions.'}
    provider = None
    try:
        if args.execute and os.getenv('SOURCE_REDISTRIBUTION_CONFIRMED') != 'true':
            raise SourceError('Confirm public aggregated export rights with SOURCE_REDISTRIBUTION_CONFIRMED=true before execution')
        provider = BigQueryProvider()
        rows = acquire(provider, start, end, args.execute, report,include_contracts=not args.skip_contracts)
        if rows is None:
            report['status'] = 'dry_run_only'; print('Dry-runs passed; partitions and observations not acquired. Dashboard unchanged.'); return 0
        begin = start.isoformat()+'T00:00:00Z'; stop = end.isoformat()+'T00:00:00Z'
        validate_rows('network', rows, begin, stop)
        # Build in isolation before replacing any production source/dashboard files.
        source_bytes = (json.dumps(rows,indent=2,default=str,allow_nan=False)+'\n').encode('utf-8')
        import hashlib
        meta = {'source':'network', 'path':'network.json', 'sha256':hashlib.sha256(source_bytes).hexdigest(),
                'retrieved_at':datetime.now(timezone.utc).isoformat(), 'start':begin,'end':stop,
                'complete':True,'authenticated':True,'synthetic':False,'origin':DATASET,
                'method':'Transaction table rows; distinct signing accounts; FUNCTION_CALL receipt-action rows. All statuses, including delegated rows as represented by source. Executed daily counts and 24-hour checks; partition metadata comparison only when accessible.',
                'redistribution_confirmed':True,'query_jobs':provider.jobs,
                'partitions':report['partitions'],'consistency_checks':report['consistency_checks'],
                'schema':report['schema'],'partition_verification':report['partition_verification'],
                'location':report['location'],'contract_coverage':report['contract_coverage'],
                'query_strategy':report['query_strategy']}
        if args.skip_contracts:meta['method']='Exact transaction table rows and distinct signing accounts; 24-hour transaction coverage. Contract calls omitted for this segment and left null; no approximation.'
        if 'partition_metadata_error' in report:
            meta['partition_metadata_error'] = report['partition_metadata_error']
        merged_manifest=publish_history(ROOT,'network',rows,meta)
        report['merged_coverage']=merged_manifest['coverage_intervals']
        report['status'] = 'verified_and_exported'
        print(json.dumps(rows, indent=2)); return 0
    except Exception as error:
        report['status'] = 'failed'
        report['error_type'] = type(error).__name__
        report['error'] = str(error)
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        return 2
    finally:
        report['jobs'] = provider.jobs if provider else []
        report['reserved_bytes'] = provider.reserved if provider else 0
        report['completed_at'] = datetime.now(timezone.utc).isoformat()
        write(ROOT/'validation-evidence/network-three-day.json', report)

if __name__ == '__main__':
    try:sys.exit(main())
    except (SourceError, ValueError, OSError) as error:print(error,file=sys.stderr);sys.exit(2)
