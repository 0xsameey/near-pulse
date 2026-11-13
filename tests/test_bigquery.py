"""Synthetic BigQuery metadata/jobs. No Google network calls or billed jobs."""
import os,unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts.providers.bigquery_provider import BigQueryProvider
from scripts.providers.common import SourceError

class Config:
    def __init__(self,**kwargs):self.__dict__.update(kwargs)
class Client:
    def __init__(self,estimate=20):self.estimate=estimate;self.calls=[];self.table_calls=[]
    def query(self,sql,**kwargs):
        self.calls.append((sql,kwargs));return SimpleNamespace(total_bytes_processed=self.estimate,job_id='synthetic-job',result=lambda **k:[])
    def get_table(self,name,**kwargs):
        self.table_calls.append((name,kwargs))
        return SimpleNamespace(schema=[],time_partitioning=None,range_partitioning=None)
MODULE=SimpleNamespace(QueryJobConfig=Config)

@patch.dict(os.environ,{'BIGQUERY_PROJECT_ID':'synthetic-project','BIGQUERY_MAX_BYTES_BILLED':'100','BIGQUERY_TOTAL_BYTES_LIMIT':'150','BIGQUERY_ALLOW_PAID_QUERIES':'false'})
class BigQueryTests(unittest.TestCase):
    def test_client_and_metadata_discovery_use_configured_location(self):
        calls=[];c=Client()
        module=SimpleNamespace(QueryJobConfig=Config,Client=lambda **kwargs:(calls.append(kwargs) or c))
        with patch.dict(os.environ,{'BIGQUERY_LOCATION':'us-east1'}):
            p=BigQueryProvider(bq_module=module);p.discover()
        self.assertEqual(calls,[{'project':'synthetic-project','location':'us-east1'}])
        self.assertEqual(len(c.table_calls),3)
        # get_table is an HTTP metadata lookup, not a job, and its official API
        # has no location keyword. It uses this same configured client.
        self.assertTrue(all('location' not in kwargs for _,kwargs in c.table_calls))
    def test_every_metadata_and_data_job_gets_explicit_location(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        for name in ('network_partitions.sql','verified_transactions.sql','verified_signers.sql','verified_function_calls.sql','verified_receipt_coverage.sql'):
            with self.subTest(sql=name),patch.dict(os.environ,{'BIGQUERY_LOCATION':'us-east1','BIGQUERY_ALLOW_PAID_QUERIES':'true'}):
                c=Client();p=BigQueryProvider(c,MODULE)
                p.run((root/'sql'/name).read_text(),[],True)
                self.assertEqual(len(c.calls),2)
                self.assertEqual([kwargs['location'] for _,kwargs in c.calls],['us-east1','us-east1'])
                self.assertEqual([kwargs['job_config'].dry_run for _,kwargs in c.calls],[True,False])
                self.assertEqual(p.jobs[0]['location'],'us-east1')
    def test_explicit_configuration_overrides_client_default(self):
        c=Client();c.location='synthetic-wrong-default'
        with patch.dict(os.environ,{'BIGQUERY_LOCATION':'synthetic-configured-region'}):
            p=BigQueryProvider(c,MODULE);p.run('synthetic SQL',[])
        self.assertEqual(c.calls[0][1]['location'],'synthetic-configured-region')
    def test_unset_location_defaults_to_dataset_region(self):
        with patch.dict(os.environ):
            os.environ.pop('BIGQUERY_LOCATION',None)
            c=Client();p=BigQueryProvider(c,MODULE);p.run('synthetic SQL',[])
            self.assertEqual(p.location,'us-east1');self.assertEqual(c.calls[0][1]['location'],'us-east1')
    def test_discovery_no_query(self):
        c=Client();p=BigQueryProvider(c,MODULE);self.assertEqual(len(p.discover()),3);self.assertEqual(c.calls,[])
    def test_dry_run_never_executes(self):
        c=Client();p=BigQueryProvider(c,MODULE);self.assertEqual(p.run('synthetic SQL',[],False),[]);self.assertEqual(len(c.calls),1);self.assertTrue(c.calls[0][1]['job_config'].dry_run)
    def test_disabled_paid_query(self):
        p=BigQueryProvider(Client(),MODULE)
        with self.assertRaisesRegex(SourceError,'disabled'):p.run('synthetic SQL',[],True)
    def test_unknown_estimate(self):
        with self.assertRaises(SourceError):BigQueryProvider(Client(None),MODULE).run('synthetic SQL',[])
    def test_cap_rejection(self):
        with self.assertRaises(SourceError):BigQueryProvider(Client(101),MODULE).run('synthetic SQL',[])
    def test_environment_cannot_raise_authorized_limits(self):
        for settings in ({'BIGQUERY_MAX_BYTES_BILLED':'100000001'},{'BIGQUERY_TOTAL_BYTES_LIMIT':'1000000001'}):
            with patch.dict(os.environ,settings):
                with self.assertRaisesRegex(SourceError,'hard limits'):BigQueryProvider(Client(),MODULE)
    def test_rejected_estimate_is_logged_without_execution(self):
        c=Client(101);p=BigQueryProvider(c,MODULE)
        with self.assertRaisesRegex(SourceError,'101 bytes'):p.run('synthetic SQL',[],True)
        self.assertEqual(len(c.calls),1);self.assertEqual(p.reserved,0)
        self.assertFalse(p.jobs[0]['executed']);self.assertIn('execution rejected',p.jobs[0]['rejected'])
    def test_negative_or_boolean_estimate_rejected(self):
        for estimate in (-1,True):
            with self.assertRaisesRegex(SourceError,'invalid'):BigQueryProvider(Client(estimate),MODULE).run('synthetic SQL',[])
    def test_full_cap_reserved_cumulatively(self):
        c=Client();p=BigQueryProvider(c,MODULE)
        with patch.dict(os.environ,{'BIGQUERY_ALLOW_PAID_QUERIES':'true'}):
            p.run('synthetic SQL',[],True);self.assertEqual(p.reserved,100)
            p.run('synthetic SQL',[],True);self.assertEqual(p.reserved,150)
            with self.assertRaisesRegex(SourceError,'budget exhausted'):p.run('synthetic SQL',[],True)
        executed=[k['job_config'].maximum_bytes_billed for _,k in c.calls if not k['job_config'].dry_run]
        self.assertEqual(executed,[100,50])
    def test_mapping_absent_fails_before_query(self):
        c=Client();p=BigQueryProvider(c,MODULE)
        with patch.dict(os.environ,{'BIGQUERY_COLUMN_MAP':'{}'}):
            with self.assertRaisesRegex(SourceError,'COLUMN_MAP'):p.fetch('2026-01-01T00:00:00Z','2026-01-02T00:00:00Z')
        self.assertEqual(c.calls,[])
    def test_unknown_actual_processing_bytes_rejects_results(self):
        c=Client();original=c.query
        def query(sql,**kwargs):
            job=original(sql,**kwargs)
            if not kwargs['job_config'].dry_run:job.total_bytes_processed=None
            return job
        c.query=query;p=BigQueryProvider(c,MODULE)
        with patch.dict(os.environ,{'BIGQUERY_ALLOW_PAID_QUERIES':'true'}):
            with self.assertRaisesRegex(SourceError,'processing bytes unknown'):p.run('synthetic SQL',[],True)
    def test_missing_job_id_rejects_results(self):
        c=Client();original=c.query
        def query(sql,**kwargs):
            job=original(sql,**kwargs)
            if not kwargs['job_config'].dry_run:job.job_id=None
            return job
        c.query=query;p=BigQueryProvider(c,MODULE)
        with patch.dict(os.environ,{'BIGQUERY_ALLOW_PAID_QUERIES':'true'}):
            with self.assertRaisesRegex(SourceError,'job ID'):p.run('synthetic SQL',[],True)
    def test_result_api_exception_type_preserved(self):
        try:from google.api_core.exceptions import Forbidden
        except ImportError:self.skipTest('optional Google dependency unavailable')
        c=Client();original=c.query
        error=Forbidden('Access Denied: Table bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS: denied')
        def query(sql,**kwargs):
            job=original(sql,**kwargs)
            if not kwargs['job_config'].dry_run:
                def result(**args):raise error
                job.result=result;job.cancel=lambda **args:None
            return job
        c.query=query;p=BigQueryProvider(c,MODULE)
        with patch.dict(os.environ,{'BIGQUERY_ALLOW_PAID_QUERIES':'true'}):
            with self.assertRaises(Forbidden) as caught:p.run('synthetic SQL',[],True)
        self.assertIs(caught.exception,error);self.assertEqual(p.reserved,100)
        self.assertEqual(p.jobs[0]['error_stage'],'result')
if __name__=='__main__':unittest.main()
