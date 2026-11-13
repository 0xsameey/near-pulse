"""Synthetic fixtures only. No Google requests or production dataset writes."""
import copy
import unittest
import tempfile
import json
import io
import contextlib
import importlib.util
from pathlib import Path
from unittest.mock import patch
from datetime import date,timedelta
from types import SimpleNamespace
from scripts.extract_network import REQUIRED, validate_schema, validate_partitions, validate_metrics, acquire
from scripts.providers.common import SourceError
from scripts import extract_network
try:
    from google.api_core.exceptions import Forbidden, Unauthorized, BadRequest, NotFound
except ImportError:
    Forbidden = None

START=date(2026,11,9)
END=date(2026,11,12)
def schema():
    return {table:{'schema':[{'name':name,'type':kind,'mode':'NULLABLE','description':'FUNCTION_CALL' if name=='action_kind' else 'synthetic metadata'} for name,kind in fields.items()],
                   'time_partitioning':{'type':'DAY','field':'block_date'}} for table,fields in REQUIRED.items()}
def partitions():
    return [{'table_name':table,'partition_id':(START+timedelta(days=i)).strftime('%Y%m%d'),'total_rows':10 if table=='transactions' else 20}
            for table in REQUIRED for i in range(3)]
def parts():
    return {'transactions':[{'date':START+timedelta(days=i),'transactions':10,'signers':3,'missing_signers':0,'observed_hours':24} for i in range(3)],
            'signers':[{'date':START+timedelta(days=i),'signers':3} for i in range(3)],
            'contracts':[{'date':START+timedelta(days=i),'contracts':5,'receipt_action_rows':20,'missing_action_kinds':0,'observed_hours':24} for i in range(3)]}

class FakeProvider:
    def __init__(self,split=False,reject_daily=False):
        self.jobs=[];self.calls=[];self.reserved=0;self.cap=100_000_000;self.total=1_000_000_000
        self.split=split;self.reject_daily=reject_daily
        self.bq=SimpleNamespace(ScalarQueryParameter=lambda name,kind,value:SimpleNamespace(name=name,value=value))
    def discover(self,tables=None):return {k:v for k,v in schema().items() if tables is None or k in tables}
    def run(self,sql,params,execute=False):
        values={p.name:p.value for p in params};self.calls.append((sql,execute))
        self.jobs.append({'sql':sql,'executed':execute})
        if 'INFORMATION_SCHEMA' in sql:
            if execute:self.reserved+=self.cap
            return [r for r in partitions() if "table_name = 'transactions'" not in sql or r['table_name']=='transactions'] if execute else []
        if not execute and (self.reject_daily or self.split and (values['end']-values['start']).days>1):
            self.jobs[-1]['rejected']='Dry-run estimate exceeds per-query limit'
            raise SourceError('Synthetic over-budget query')
        if not execute:return []
        self.reserved+=self.cap
        if '@action' in sql:
            rows=[{k:v for k,v in row.items() if k!='observed_hours'} for row in parts()['contracts']]
        elif 'AS transactions' in sql:rows=parts()['transactions']
        elif 'AS receipt_action_rows' in sql:
            rows=[{k:row[k] for k in ('date','receipt_action_rows','observed_hours')} for row in parts()['contracts']]
        else:rows=parts()['signers']
        return [r for r in rows if values['start']<=r['date']<values['end']]


class MetadataDeniedProvider(FakeProvider):
    def __init__(self,error=None,**kwargs):
        super().__init__(**kwargs)
        self.metadata_error=error if error is not None else Forbidden('Access Denied: Table bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS: User does not have permission to query table')
    def run(self,sql,params,execute=False):
        if 'INFORMATION_SCHEMA' in sql:
            self.calls.append((sql,execute))
            self.jobs.append({'sql':sql,'executed':False,'failed':True,'error':str(self.metadata_error)})
            raise self.metadata_error
        return super().run(sql,params,execute)


@unittest.skipIf(Forbidden is None,'optional google-api-core dependency unavailable')
class MetadataFallbackTests(unittest.TestCase):
    def test_specific_metadata_403_executes_bounded_queries(self):
        p=MetadataDeniedProvider();report={}
        rows=acquire(p,START,END,True,report)
        self.assertEqual(len(rows),3);self.assertIsNone(report['partitions'])
        self.assertEqual(report['partition_verification']['mode'],'bounded_data_queries')
        self.assertEqual(report['partition_verification']['status'],'validated')
        self.assertIsNone(report['partitions_observed_at'])
        for check in report['consistency_checks']:
            self.assertIsNone(check['transactions_match_partition_rows'])
            self.assertIsNone(check['receipt_actions_match_partition_rows'])
        data_calls=[(sql,ex) for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql]
        self.assertEqual([ex for _,ex in data_calls],[False]*3+[True]*3)
        self.assertTrue(all('WHERE block_date >= @start AND block_date < @end' in sql for sql,_ in data_calls))
    def test_dry_run_fallback_never_infers_availability(self):
        p=MetadataDeniedProvider();report={}
        self.assertIsNone(acquire(p,START,END,False,report))
        self.assertEqual(report['partition_verification']['status'],'pending')
        self.assertIsNone(report['partitions'])
        self.assertNotIn('metrics',report)
        self.assertFalse(any(ex for _,ex in p.calls))
    def test_missing_day_in_bounded_results_is_fatal(self):
        p=MetadataDeniedProvider();original=p.run
        def missing(sql,params,execute=False):
            rows=original(sql,params,execute)
            return rows[:-1] if execute and 'AS contracts' in sql else rows
        p.run=missing
        with self.assertRaisesRegex(SourceError,'incomplete daily coverage'):acquire(p,START,END,True,{})
    def test_empty_table_day_is_not_available(self):
        result=parts();result['contracts'][0]['receipt_action_rows']=0
        with self.assertRaisesRegex(SourceError,'nonempty'):validate_metrics(result,None,START,END)
    def test_over_budget_single_day_stays_fatal(self):
        p=MetadataDeniedProvider(reject_daily=True)
        with self.assertRaises(SourceError):acquire(p,START,END,True,{})
        self.assertFalse(any(ex for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql))
    def test_other_api_errors_are_never_fallback(self):
        view='bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS'
        errors=[Unauthorized('Authentication failed'),BadRequest('Invalid query'),NotFound('Not found: Table '+view),
                Forbidden('Access Denied: Table bigquery-public-data:crypto_near_mainnet_us.transactions: denied; SQL mentions '+view),
                Forbidden('Access Denied: Dataset bigquery-public-data:crypto_near_mainnet_us'),
                Forbidden('Access Denied: Table another-project:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS: denied')]
        for error in errors:
            with self.subTest(error=error):
                p=MetadataDeniedProvider(error)
                with self.assertRaises(type(error)):acquire(p,START,END,True,{})
                self.assertEqual(len(p.calls),1)
    def test_discovery_permission_error_remains_fatal(self):
        p=MetadataDeniedProvider()
        def denied():raise p.metadata_error
        p.discover=denied
        with self.assertRaises(Forbidden):acquire(p,START,END,True,{})
        self.assertEqual(p.calls,[])
    def test_untyped_403_message_does_not_enable_fallback(self):
        self.assertFalse(extract_network.is_partition_metadata_denied(SourceError('403 Access Denied: Table bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS: denied')))
    def test_full_local_error_message_matches_exact_view(self):
        message='403 POST https://bigquery.googleapis.com/bigquery/v2/projects/falcora-test/jobs?prettyPrint=false: Access Denied: Table bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS: User does not have permission to query table bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS, or perhaps it does not exist.\n\nLocation: US\nJob ID: synthetic-failed-request\n'
        self.assertTrue(extract_network.is_partition_metadata_denied(Forbidden(message)))
    def test_fallback_retains_existing_cap_reservations(self):
        p=MetadataDeniedProvider(split=True);p.reserved=100_000_000
        acquire(p,START,END,True,{})
        self.assertEqual(p.reserved,1_000_000_000)
    def test_fallback_cannot_exceed_cumulative_budget(self):
        p=MetadataDeniedProvider();p.total=200_000_000
        with self.assertRaisesRegex(SourceError,'cumulative budget'):acquire(p,START,END,True,{})
        self.assertFalse(any(ex for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql))

class NetworkExtractionTests(unittest.TestCase):
    def test_seven_day_daily_plan_stays_within_budget(self):
        self.check_history_plan(7,1,800_000_000)
    def test_fourteen_day_two_day_plan_stays_within_budget(self):
        self.check_history_plan(14,2,800_000_000)
    def test_fourteen_day_daily_plan_exceeds_budget_before_data_execution(self):
        self.check_history_plan(14,1,None)
    def check_history_plan(self,period,max_span,expected_reservation):
        class HistoricalProvider(FakeProvider):
            def run(self,sql,params,execute=False):
                values={p.name:p.value for p in params};left,right=values['start'],values['end']
                self.calls.append((sql,execute));self.jobs.append({'sql':sql,'executed':execute})
                if 'INFORMATION_SCHEMA' in sql:
                    if not execute:return []
                    self.reserved+=self.cap
                    return [{'table_name':'transactions','partition_id':day.strftime('%Y%m%d'),'total_rows':10}
                            for day in extract_network.days(left,right)]
                if (right-left).days>max_span:
                    self.jobs[-1]['rejected']='Dry-run estimate exceeds per-query limit'
                    raise SourceError('Synthetic over-budget interval')
                if not execute:return []
                self.reserved+=self.cap
                return [{'date':day,'transactions':10,'signers':3,'missing_signers':0,'observed_hours':24}
                        for day in extract_network.days(left,right)]
        p=HistoricalProvider();start=date(2026,10,27);end=start+timedelta(days=period);report={}
        if expected_reservation is None:
            with self.assertRaisesRegex(SourceError,'cumulative budget'):acquire(p,start,end,True,report,include_contracts=False)
            self.assertFalse(any(ex for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql))
        else:
            rows=acquire(p,start,end,True,report,include_contracts=False)
            self.assertEqual(len(rows),period);self.assertEqual(p.reserved,expected_reservation)
            self.assertLessEqual(report['planned_maximum_bytes'],1_000_000_000)
    def test_transactions_only_requires_no_action_schema_or_jobs(self):
        p=FakeProvider();report={}
        rows=acquire(p,START,END,True,report,include_contracts=False)
        self.assertEqual(len(rows),3);self.assertTrue(all(r['contracts'] is None for r in rows))
        self.assertTrue(all('receipt_actions' not in sql for sql,_ in p.calls))
        self.assertEqual(p.reserved,200_000_000)
    def test_column_separation_and_exact_signer_aggregation(self):
        root=extract_network.ROOT/'sql'
        calls=(root/'verified_function_calls.sql').read_text().split('SELECT',1)[1]
        coverage=(root/'verified_receipt_coverage.sql').read_text().split('SELECT',1)[1]
        transactions=(root/'verified_transactions.sql').read_text().split('SELECT',1)[1]
        self.assertNotIn('block_timestamp_utc',calls)
        self.assertNotIn('action_kind',coverage)
        self.assertIn('COUNTIF(action_kind = @action)',calls)
        self.assertIn('COUNT(DISTINCT signer_account_id)',transactions)
        for sql in (calls,coverage,transactions):
            self.assertIn('WHERE block_date >= @start AND block_date < @end',sql)
            self.assertNotIn('LIMIT',sql.upper());self.assertNotIn('APPROX_',sql.upper())
    def test_contract_column_merge_keeps_exact_counts(self):
        source=parts()['contracts']
        actions=[{k:v for k,v in row.items() if k!='observed_hours'} for row in source]
        coverage=[{k:row[k] for k in ('date','receipt_action_rows','observed_hours')} for row in source]
        self.assertEqual(extract_network.merge_contract_coverage(actions,coverage,START,END),source)
        coverage[0]['receipt_action_rows']+=1
        with self.assertRaisesRegex(SourceError,'totals differ'):
            extract_network.merge_contract_coverage(actions,coverage,START,END)
    def test_missing_coverage_query_day_is_fatal(self):
        source=parts()['contracts']
        with self.assertRaisesRegex(SourceError,'incomplete daily coverage'):
            extract_network.merge_contract_coverage(source,source[:-1],START,END)
    def test_optimized_single_day_contract_query_over_cap_still_fatal(self):
        p=FakeProvider();original=p.run
        def run(sql,params,execute=False):
            result=original(sql,params,execute)
            if not execute and '@action' in sql:
                p.jobs[-1]['rejected']='Dry-run estimate exceeds per-query limit'
                raise SourceError('Synthetic optimized action_kind-only job remains over budget')
            return result
        p.run=run
        with self.assertRaisesRegex(SourceError,'remains over budget'):acquire(p,START,END,True,{})
        self.assertFalse(any(ex for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql))
    def test_schema_types_and_partition(self):
        validate_schema(schema());bad=schema();bad['transactions']['schema'][0]['type']='TIMESTAMP'
        with self.assertRaises(SourceError):validate_schema(bad)
    def test_missing_partition_does_not_mean_zero(self):
        with self.assertRaisesRegex(SourceError,'unavailable'):validate_partitions(partitions()[:-1],START,END)
    def test_three_days_and_partition_consistency(self):
        rows,checks=validate_metrics(parts(),partitions(),START,END)
        self.assertEqual(len(rows),3);self.assertTrue(all(x['transactions_match_partition_rows'] for x in checks))
    def test_mismatched_partition_stops_publication(self):
        data=parts();data['transactions'][0]['transactions']=9
        with self.assertRaisesRegex(SourceError,'differs'):validate_metrics(data,partitions(),START,END)
    def test_missing_hour_stops_publication(self):
        data=parts();data['contracts'][0]['observed_hours']=23
        with self.assertRaisesRegex(SourceError,'24 UTC'):validate_metrics(data,partitions(),START,END)
    def test_null_kind_stops_publication(self):
        data=parts();data['contracts'][0]['missing_action_kinds']=1
        with self.assertRaisesRegex(SourceError,'null'):validate_metrics(data,partitions(),START,END)
    def test_all_plans_pass_before_data_executes(self):
        p=FakeProvider();report={};rows=acquire(p,START,END,True,report)
        self.assertEqual(len(rows),3)
        data_calls=[(sql,ex) for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql]
        self.assertEqual([ex for _,ex in data_calls],[False]*3+[True]*3)
        self.assertTrue(all('WHERE block_date >= @start AND block_date < @end' in sql for sql,_ in data_calls))
    def test_cost_fallback_one_day_queries(self):
        p=FakeProvider(split=True);acquire(p,START,END,True,{})
        self.assertEqual(sum(ex for _,ex in p.calls),10)
        self.assertEqual(p.reserved,1_000_000_000)
    def test_over_budget_single_day_never_executes_data(self):
        p=FakeProvider(reject_daily=True)
        with self.assertRaises(SourceError):acquire(p,START,END,True,{})
        self.assertFalse(any(ex for sql,ex in p.calls if 'INFORMATION_SCHEMA' not in sql))
    def test_dry_run_never_labels_partitions_verified(self):
        p=FakeProvider();report={};self.assertIsNone(acquire(p,START,END,False,report))
        self.assertFalse(any(ex for _,ex in p.calls));self.assertEqual(report['partitions'],[])
    @unittest.skipUnless(importlib.util.find_spec('pandas'),'pandas required for staged rebuild integration')
    def test_staged_success_exports_matching_csv_and_json(self):
        self.assert_staged_success(FakeProvider())
    @unittest.skipUnless(Forbidden is not None and importlib.util.find_spec('pandas'),'Google exception types and pandas required')
    def test_staged_metadata_fallback_preserves_honest_provenance(self):
        meta=self.assert_staged_success(MetadataDeniedProvider())
        self.assertIsNone(meta['partitions'])
        self.assertEqual(meta['partition_verification']['mode'],'bounded_data_queries')
        self.assertIn('partition_metadata_error',meta)
        self.assertTrue(all(check['transactions_match_partition_rows'] is None for check in meta['consistency_checks']))
    def assert_staged_success(self,provider):
        import csv
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir();(root/'data/schema.json').write_text(json.dumps(schema()))
            (root/'sql').mkdir()
            for source in (extract_network.ROOT/'sql').glob('*.sql'):(root/'sql'/source.name).write_bytes(source.read_bytes())
            with patch.object(extract_network,'ROOT',root),patch.object(extract_network,'BigQueryProvider',return_value=provider),patch.dict('os.environ',{'SOURCE_REDISTRIBUTION_CONFIRMED':'true','BIGQUERY_LOCATION':'us-east1'}),contextlib.redirect_stdout(io.StringIO()):
                code=extract_network.main(['--start','2026-11-09','--end','2026-11-12','--execute'])
            self.assertEqual(code,0)
            dashboard=json.loads((root/'public/data/dashboard.json').read_text())
            self.assertEqual(len(dashboard['daily']['network']),3)
            with (root/'public/data/network.csv').open(newline='') as stream:exported=list(csv.DictReader(stream))
            self.assertEqual(exported[0]['transactions'],str(dashboard['daily']['network'][0]['transactions']))
            self.assertEqual(len(dashboard['series']),3)
            self.assertTrue(all(r['transactions_ma7'] is None for r in dashboard['series']))
            meta=json.loads((root/'data/raw/network.manifest.json').read_text())
            self.assertEqual(meta['location'],'us-east1')
            self.assertEqual(json.loads((root/'validation-evidence/network-three-day.json').read_text())['location'],'us-east1')
            return meta
    def test_failed_staged_rebuild_preserves_production(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir();(root/'data/schema.json').write_text(json.dumps(schema()))
            (root/'sql').mkdir()
            for source in (extract_network.ROOT/'sql').glob('*.sql'):(root/'sql'/source.name).write_bytes(source.read_bytes())
            (root/'public/data').mkdir(parents=True);original=root/'public/data/dashboard.json';original.write_text('unchanged synthetic sentinel')
            with patch.object(extract_network,'ROOT',root),patch.object(extract_network,'BigQueryProvider',return_value=FakeProvider()),patch('scripts.history.rebuild',return_value=2),patch.dict('os.environ',{'SOURCE_REDISTRIBUTION_CONFIRMED':'true'}),contextlib.redirect_stderr(io.StringIO()):
                code=extract_network.main(['--start','2026-11-09','--end','2026-11-12','--execute'])
            self.assertEqual(code,2);self.assertEqual(original.read_text(),'unchanged synthetic sentinel')
            self.assertFalse((root/'data/raw/network.json').exists())

if __name__=='__main__':unittest.main()
