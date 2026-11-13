"""Synthetic HTTP and export fixtures, exclusively inside temporary directories."""
import contextlib
import csv
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from decimal import Decimal
from scripts.extract_intents import acquire,safe_json
from scripts.providers.intents_provider import IntentsProvider
from scripts.providers.common import HttpClient,SourceError
from scripts.analysis.metrics import daily_swaps
from scripts.provenance import digest,load_export
from scripts.rebuild import write,main as rebuild

START='2026-11-09T00:00:00Z'
END='2026-11-10T00:00:00Z'
TOKEN='synthetic-explorer-credential-for-tests-only'
def swap(identity='synthetic-a',amount='0.1'):
    return {'depositAddress':identity,'depositMemo':None,'status':'SUCCESS',
            'createdAt':'2026-11-09T12:00:00Z','createdAtTimestamp':1794225600,
            'amountInUsd':amount,'originAsset':'synthetic:asset'}
class Response:
    def __init__(self,payload,status=200,headers=None):
        self.content=json.dumps(payload).encode();self.status_code=status;self.headers=headers or {}
    def json(self):return json.loads(self.content)
class Session:
    def __init__(self,responses):self.responses=iter(responses);self.calls=[]
    def get(self,url,params,headers,timeout,allow_redirects=False):
        if allow_redirects:raise AssertionError('Redirects must not create unpaced authenticated requests')
        self.calls.append((url,params,headers));return next(self.responses)
def provider(responses):
    session=Session(responses);ticks=[0.0]
    def sleep(seconds):ticks[0]+=seconds
    client=HttpClient(interval=5,session=session,sleep=sleep,clock=lambda:ticks[0],capture=True,parse_decimal=True)
    return IntentsProvider(client),session,ticks

@patch.dict(os.environ,{'INTENTS_EXPLORER_JWT':TOKEN,'INTENTS_PAGE_SIZE':'2','INTENTS_MAX_PAGES':'3','SOURCE_REDISTRIBUTION_CONFIRMED':'true'})
class IntentsAcquisitionTests(unittest.TestCase):
    def test_authenticated_probe_and_secret_free_report(self):
        p,session,_=provider([Response([swap()]),Response([])])
        with tempfile.TemporaryDirectory() as directory:
            code,report=acquire(directory,START,END,True,p)
            self.assertEqual(code,0);self.assertTrue(report['authenticated_access_confirmed'])
            self.assertTrue(report['schema_validated']);self.assertTrue(report['pagination_complete'])
            self.assertEqual(report['input_volume_usd'],'0.1');self.assertEqual(len(report['response_pages']),2)
            self.assertEqual(session.calls[0][2]['Authorization'],'Bearer '+TOKEN)
            self.assertNotIn(TOKEN,json.dumps(report));self.assertNotIn('Authorization',json.dumps(report))
            self.assertFalse((Path(directory)/'public/data/dashboard.json').exists())
    def test_retry_then_pagination_is_rate_limited(self):
        p,session,ticks=provider([Response({},429,{'Retry-After':'8'}),Response([swap()]),Response([])])
        rows=p.fetch(START,END)
        self.assertEqual(len(rows),1);self.assertGreaterEqual(ticks[0],13)
        self.assertEqual([e['http_status'] for e in p.client.events],[429,200,200])
        self.assertEqual(session.calls[1][1]['startTimestamp'],session.calls[2][1]['startTimestamp'])
        self.assertEqual(session.calls[1][1]['endTimestamp'],session.calls[2][1]['endTimestamp'])
    def test_partial_pagination_is_not_published(self):
        p,_,_=provider([Response([swap(),swap('synthetic-b')])])
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'INTENTS_MAX_PAGES':'1'}):
            code,report=acquire(directory,START,END,True,p)
            self.assertEqual(code,2);self.assertTrue(report['authenticated_access_confirmed'])
            self.assertFalse(report['pagination_complete']);self.assertIsNone(report['successful_swaps'])
            self.assertFalse((Path(directory)/'data/raw/intents.manifest.json').exists())
    def test_created_timestamp_consistency(self):
        row=swap();row['createdAtTimestamp']=0
        p,_,_=provider([Response([row])])
        with self.assertRaisesRegex(SourceError,'Inconsistent'):p.fetch(START,END)
    def test_missing_invalid_or_nonfinite_amounts(self):
        for amount in (None,'','NaN','Infinity',True,'-0.01'):
            row=swap(amount=amount);p,_,_=provider([Response([row])])
            with self.subTest(amount=amount),self.assertRaises(SourceError):p.fetch(START,END)
    def test_non_success_status_and_missing_memo_are_rejected(self):
        for row in ({**swap(),'status':'PROCESSING'},{k:v for k,v in swap().items() if k!='depositMemo'}):
            p,_,_=provider([Response([row])])
            with self.assertRaises(SourceError):p.fetch(START,END)
    def test_zero_records_require_terminal_empty_response(self):
        p,_,_=provider([Response([])])
        with tempfile.TemporaryDirectory() as directory:
            code,report=acquire(directory,START,END,True,p)
            self.assertEqual(code,0);self.assertEqual(report['successful_swaps'],0)
            self.assertFalse(report['schema_validated']);self.assertTrue(report['pagination_complete'])
    def test_401_does_not_claim_authenticated_access(self):
        p,_,_=provider([Response({},401)])
        with tempfile.TemporaryDirectory() as directory:
            code,report=acquire(directory,START,END,True,p)
            self.assertEqual(code,2);self.assertFalse(report['authenticated_access_confirmed'])
            self.assertNotIn(TOKEN,json.dumps(report))
    def test_exact_sum_beyond_default_decimal_precision(self):
        result=daily_swaps([swap(amount='1234567890123456789012345678.000000000000000001'),swap('synthetic-b','0.000000000000000002')])
        self.assertEqual(result[0]['volume'],'1234567890123456789012345678.000000000000000003')
    def test_numeric_json_precision_is_retained(self):
        response=Response([])
        response.content=b'[{"depositAddress":"synthetic-a","depositMemo":null,"status":"SUCCESS","createdAt":"2026-11-09T12:00:00Z","originAsset":"synthetic:asset","amountInUsd":0.12345678901234567890123456789}]'
        p,_,_=provider([response,Response([])]);rows=p.fetch(START,END)
        self.assertIsInstance(rows[0]['amountInUsd'],Decimal)
        self.assertEqual(daily_swaps(rows)[0]['volume'],'0.12345678901234567890123456789')
    def test_writer_refuses_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'unsafe.json'
            with self.assertRaisesRegex(SourceError,'credential'):safe_json(path,{'echo':TOKEN},TOKEN)
            self.assertFalse(path.exists())
    @unittest.skipUnless(importlib.util.find_spec('pandas'),'pandas required for replay integration')
    def test_complete_export_preserves_network_and_verifies_raw_responses(self):
        p,_,_=provider([Response([swap(),swap('synthetic-b','0.2')]),Response([])])
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);raw=root/'data/raw/network.json'
            write(raw,[{'date':'2026-11-09','transactions':11,'signers':7,'contracts':13}])
            write(root/'data/raw/network.manifest.json',{'source':'network','path':'network.json','sha256':digest(raw),
                'retrieved_at':END,'start':START,'end':END,'complete':True,'authenticated':True,'synthetic':False,
                'origin':'bigquery-public-data.crypto_near_mainnet_us','method':'Synthetic test fixture only',
                'redistribution_confirmed':True,'query_jobs':[{'job_id':'synthetic-network-job','actual_bytes':10}]})
            self.assertEqual(rebuild(['--sources','network','--start',START,'--end',END],root=root),0)
            original=(root/'public/data/network.csv').read_bytes();source_hash=digest(raw)
            code,report=acquire(root,START,END,False,p)
            self.assertEqual(code,0);self.assertEqual(report['status'],'verified_and_exported')
            self.assertEqual((root/'public/data/network.csv').read_bytes(),original);self.assertEqual(digest(raw),source_hash)
            data=json.loads((root/'public/data/dashboard.json').read_text())
            self.assertEqual(data['daily']['intents'][0]['volume'],'0.3')
            self.assertEqual(data['daily']['intents'][0]['swaps'],2)
            with (root/'public/data/intents.csv').open(newline='') as stream:
                self.assertEqual(list(csv.DictReader(stream))[0]['volume'],'0.3')
            rows,meta=load_export(root/'data/raw','intents',START,END)
            self.assertEqual(len(rows),2);self.assertTrue(meta['pagination']['complete'])
            response=root/'data/raw'/meta['response_pages'][0]['path'];response.write_text('tampered synthetic body')
            with self.assertRaisesRegex(SourceError,'response hash'):load_export(root/'data/raw','intents',START,END)

if __name__=='__main__':unittest.main()
