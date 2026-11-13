import os,re,json
from pathlib import Path
from .common import SourceError,bounds
DATASET='bigquery-public-data.crypto_near_mainnet_us'
DEFAULT_LOCATION='us-east1'
TABLES=('transactions','receipt_actions','receipt_origin_transaction')

class BigQueryProvider:
    def __init__(self,client=None,bq_module=None):
        if bq_module is None:
            try: from google.cloud import bigquery
            except ImportError: raise SourceError('Install requirements-bigquery.txt for optional BigQuery support') from None
        else: bigquery=bq_module
        self.bq=bigquery; project=os.getenv('BIGQUERY_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project: raise SourceError('BIGQUERY_PROJECT_ID absent')
        self.location=os.getenv('BIGQUERY_LOCATION') or DEFAULT_LOCATION
        self.client=client or bigquery.Client(project=project,location=self.location)
        self.cap=int(os.getenv('BIGQUERY_MAX_BYTES_BILLED','100000000'));self.total=int(os.getenv('BIGQUERY_TOTAL_BYTES_LIMIT','1000000000'));self.reserved=0;self.jobs=[]
        if not 0<self.cap<=100_000_000 or not 0<self.total<=1_000_000_000:
            raise SourceError('Authorized hard limits: at most 100000000 bytes per query and 1000000000 bytes cumulatively; configured limits must be positive and cannot exceed these bounds')
    def discover(self,tables=None):
        result={}
        selected=TABLES if tables is None else tables
        if not set(selected)<=set(TABLES):raise SourceError('Unknown discovery table')
        for name in selected:
            table=self.client.get_table(f'{DATASET}.{name}',retry=None,timeout=30)
            result[name]={'schema':[f.to_api_repr() for f in table.schema],'time_partitioning':table.time_partitioning.to_api_repr() if table.time_partitioning else None,'range_partitioning':table.range_partitioning.to_api_repr() if table.range_partitioning else None}
        return result
    def run(self,sql,params,execute=False):
        if self.reserved>=self.total: raise SourceError('Cumulative scan budget exhausted')
        config=self.bq.QueryJobConfig(dry_run=True,use_query_cache=False,query_parameters=params,maximum_bytes_billed=min(self.cap,self.total-self.reserved))
        record={'sql':sql,'location':self.location,'parameters':[p.to_api_repr() for p in params],'estimate_bytes':None,'dry_run_job_id':None,'executed':False};self.jobs.append(record)
        try: job=self.client.query(sql,job_config=config,location=self.location,retry=None,timeout=30)
        except Exception as error:
            record.update(failed=True,error_stage='dry_run',error_type=type(error).__name__,error=str(error))
            raise
        estimate=job.total_bytes_processed
        record.update(estimate_bytes=estimate,dry_run_job_id=job.job_id)
        if isinstance(estimate,bool) or not isinstance(estimate,int) or estimate<0:
            record['rejected']='Unknown or invalid dry-run byte estimate'
            raise SourceError(record['rejected'])
        remaining=self.total-self.reserved
        if estimate>self.cap or estimate>remaining:
            record['rejected']=f'Dry-run estimate {estimate} bytes exceeds per-query limit {self.cap} or remaining cumulative limit {remaining}; execution rejected'
            raise SourceError(record['rejected'])
        if not execute: return []
        if os.getenv('BIGQUERY_ALLOW_PAID_QUERIES')!='true': raise SourceError('Paid execution disabled; review dry-run and explicitly configure opt-in')
        # Reserve the entire authorized per-job cap, not the optimistic estimate.
        authorization=min(self.cap,self.total-self.reserved);self.reserved+=authorization
        config=self.bq.QueryJobConfig(dry_run=False,use_query_cache=False,query_parameters=params,maximum_bytes_billed=authorization)
        try: job=self.client.query(sql,job_config=config,location=self.location,retry=None,timeout=30,job_retry=None)
        except Exception as error:
            record.update(failed=True,error_stage='submission',error_type=type(error).__name__,error=str(error))
            raise
        record.update(executed=True,job_id=job.job_id,maximum_bytes_billed=authorization)
        try: rows=list(job.result(timeout=120,retry=None,job_retry=None))
        except Exception as error:
            try: job.cancel(retry=None,timeout=15)
            except Exception: pass
            record.update(failed=True,error_stage='result',error_type=type(error).__name__,error=str(error),actual_bytes=job.total_bytes_processed)
            # Preserve the typed API error: callers may recognize only a narrowly
            # scoped, explicitly authorized metadata permission denial.
            raise
        record['actual_bytes']=job.total_bytes_processed
        if not isinstance(job.job_id,str) or not job.job_id:
            raise SourceError('Executed BigQuery job has no verifiable job ID')
        if isinstance(record['actual_bytes'],bool) or not isinstance(record['actual_bytes'],int) or not 0<=record['actual_bytes']<=authorization:
            raise SourceError('Executed BigQuery job processing bytes unknown, invalid or above its authorized cap; results rejected')
        return [dict(r) for r in rows]
    def fetch(self,start,end,execute=False):
        a,b=bounds(start,end);schema=self.discover(); mapping=json.loads(os.getenv('BIGQUERY_COLUMN_MAP','{}'))
        # Explicit configuration is checked against discovered source columns. No guessed fields execute.
        output={}
        for table,alias in [('transactions','network'),('receipt_actions','contracts')]:
            m=mapping.get(table,{})
            required=['date','id','signer'] if alias=='network' else ['date','id','action']
            if any(k not in m for k in required): raise SourceError(f'Configure BIGQUERY_COLUMN_MAP for {table} after schema discovery')
            fields={f['name']:f['type'] for f in schema[table]['schema']}
            identities=m['id'] if isinstance(m['id'],list) else [m['id']]
            configured=[m[k] for k in required if k!='id']+identities
            if not identities or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',v) or v not in fields or fields[v] in ('RECORD','STRUCT') for v in configured): raise SourceError('Source-column validation failed')
            if any(f.get('mode')=='REPEATED' for f in schema[table]['schema'] if f['name'] in configured): raise SourceError('Repeated source columns require a separately reviewed counting grain')
            partition=schema[table]['time_partitioning']
            if not partition or partition.get('field')!=m['date'] or fields[m['date']] not in ('DATE','TIMESTAMP','DATETIME'): raise SourceError('Require a verified temporal partition column')
            d=f"`{m['date']}`"; dt=fields[m['date']]
            if dt=='DATE': filt=f'{d} >= DATE(@start) AND {d} < DATE(@end)'
            elif dt=='DATETIME': filt=f'{d} >= DATETIME(@start) AND {d} < DATETIME(@end)'
            else: filt=f'{d} >= @start AND {d} < @end'
            identity='TO_JSON_STRING(STRUCT('+', '.join(f'`{v}`' for v in identities)+'))'
            invalid=' OR '.join(f'`{v}` IS NULL' for v in configured)
            if alias=='network':
                select=f"COUNT(DISTINCT {identity}) AS transactions, COUNT(DISTINCT `{m['signer']}`) AS signers"
                action_filter=''
            else:
                if not os.getenv('BIGQUERY_FUNCTION_CALL_VALUE') or os.getenv('BIGQUERY_ACTION_GRAIN_CONFIRMED')!='true': raise SourceError('Confirm receipt action identity/grain and function-call enum from source before extraction')
                if fields[m['action']]!='STRING': raise SourceError('Function-call enum mapping requires a verified STRING column')
                select=f"COUNT(DISTINCT {identity}) AS contracts"
                action_filter=f" AND `{m['action']}` = @action"
            template=(Path(__file__).resolve().parents[2]/'sql'/('network_activity.sql' if alias=='network' else 'contract_activity.sql')).read_text(encoding='utf-8')
            sql=template.format(date=d,select=select,invalid=invalid,table=f'{DATASET}.{table}',filter=filt,action_filter=action_filter)
            params=[self.bq.ScalarQueryParameter('start','TIMESTAMP',a),self.bq.ScalarQueryParameter('end','TIMESTAMP',b)]
            if alias=='contracts': params.append(self.bq.ScalarQueryParameter('action','STRING',os.environ['BIGQUERY_FUNCTION_CALL_VALUE']))
            output[alias]=self.run(sql,params,execute)
            for row in output[alias]:
                if row.pop('invalid_rows',0): raise SourceError('Null source identities or metric columns; extraction rejected')
        return output,schema
