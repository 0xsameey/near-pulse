"""All values in this file are synthetic test fixtures, never production observations."""
import unittest, tempfile, json, os, csv, subprocess, sys, hashlib
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone
from scripts.providers.common import SourceError, HttpClient, bounds
from scripts.providers.intents_provider import IntentsProvider
from scripts.providers.price_provider import PriceProvider
from scripts.analysis.metrics import daily_swaps, daily_prices, freshness
from scripts.analysis.thesis import verdict
from scripts.provenance import load_export, digest

START='2026-01-01T00:00:00Z'
END='2026-01-03T00:00:00Z'
def swap(address='synthetic-a',memo=None,amount='0.1',created='2026-01-01T12:00:00Z'):
    return dict(depositAddress=address,depositMemo=memo,createdAt=created,status='SUCCESS',amountInUsd=amount,originAsset='synthetic:test')
class Pages:
    def __init__(self,pages):self.pages=iter(pages);self.calls=[]
    def get(self,url,params,headers):self.calls.append((url,params,headers));return next(self.pages)

class MetricsTests(unittest.TestCase):
    def test_decimal_and_deduplication(self):
        a=swap();result=daily_swaps([a,a,swap('synthetic-b',amount='0.2')])
        self.assertEqual(result,[{'date':'2026-01-01','swaps':2,'volume':'0.3'}])
    def test_memo_distinguishes_swaps(self):self.assertEqual(daily_swaps([swap(memo='1'),swap(memo='2')])[0]['swaps'],2)
    def test_utc_grouping(self):self.assertEqual(daily_swaps([swap(created='2026-01-02T00:30:00+02:00')])[0]['date'],'2026-01-01')
    def test_conflicting_duplicate(self):
        with self.assertRaises(SourceError):daily_swaps([swap(),swap(amount='1')])
    def test_invalid_decimal(self):
        for amount in ('NaN','Infinity','-1'):
            with self.assertRaises(SourceError):daily_swaps([swap(amount=amount)])
    def test_empty(self):self.assertEqual(daily_swaps([]),[])
    def test_exact_csv_decimal(self):
        import io,csv
        rows=daily_swaps([swap(amount='0.000000000000000001'),swap('b',amount='0.2')])
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=['date','swaps','volume']);writer.writeheader();writer.writerows(rows)
        exported=list(csv.DictReader(io.StringIO(buffer.getvalue())))
        self.assertEqual(exported[0]['volume'],'0.200000000000000001');self.assertEqual(exported[0]['swaps'],'2')
    def test_asset_concentration(self):
        from scripts.analysis.metrics import concentration
        a=swap(amount='0.1');b=swap('b',amount='0.3');b['originAsset']='synthetic:other'
        rows=concentration([a,a,b]);self.assertEqual(rows[0]['share'],'0.75');self.assertEqual(rows[0]['asset'],'synthetic:other')
    def test_price_daily_convention(self):
        rows=[{'timestamp':'2026-01-01T20:00:00Z','price':2},{'timestamp':'2026-01-01T01:00:00Z','price':1}]
        self.assertEqual(daily_prices(rows),[{'date':'2026-01-01','price':2}])
    def test_freshness(self):
        now=datetime(2026,1,5,tzinfo=timezone.utc)
        self.assertEqual(freshness('2026-01-01',now),'stale');self.assertEqual(freshness(None,now),'unavailable');self.assertEqual(freshness('2026-01-04',now),'current')
    def test_finite_bounds(self):
        for start,end in [(END,START),('2026-01-01',END),(START,'2030-01-01T00:00:00Z')]:
            with self.assertRaises(SourceError):bounds(start,end)

@patch.dict(os.environ,{'INTENTS_EXPLORER_JWT':'synthetic-not-a-real-token','INTENTS_PAGE_SIZE':'2','INTENTS_MAX_PAGES':'3'})
class ExplorerTests(unittest.TestCase):
    def test_pagination_bounds_and_cursor(self):
        client=Pages([[swap(),swap('synthetic-b','memo')],[]]);rows=IntentsProvider(client).fetch(START,END)
        self.assertEqual(len(rows),2);self.assertEqual(client.calls[1][1]['lastDepositMemo'],'memo')
        self.assertEqual(client.calls[0][1]['endTimestamp'],client.calls[1][1]['endTimestamp'])
        self.assertEqual(client.calls[0][1]['startTimestamp'],client.calls[1][1]['startTimestamp'])
    def test_empty(self):self.assertEqual(IntentsProvider(Pages([[]])).fetch(START,END),[])
    def test_start_midnight_is_included(self):
        row=swap(created=START);self.assertEqual(len(IntentsProvider(Pages([[row],[]])).fetch(START,END)),1)
    def test_repeated_cursor(self):
        with self.assertRaisesRegex(SourceError,'Repeated cursor'):IntentsProvider(Pages([[swap()],[swap()]])).fetch(START,END)
    def test_partial_pagination(self):
        with patch.dict(os.environ,{'INTENTS_MAX_PAGES':'1'}):
            with self.assertRaisesRegex(SourceError,'incomplete'):IntentsProvider(Pages([[swap()]])).fetch(START,END)
    def test_overlapping_pages_dedupe(self):
        c=Pages([[swap(),swap('b')],[swap('b'),swap('c')],[]]);self.assertEqual(len(IntentsProvider(c).fetch(START,END)),3)
    def test_bad_response_and_out_of_bounds(self):
        for data in ({'transactions':[]},[swap(created=END)],[swap(amount='NaN')],[{'status':'SUCCESS'}]):
            with self.assertRaises((SourceError,ValueError)):IntentsProvider(Pages([data])).fetch(START,END)
    def test_missing_credentials(self):
        with patch.dict(os.environ,{'INTENTS_EXPLORER_JWT':''}):
            with self.assertRaises(SourceError):IntentsProvider(Pages([])).fetch(START,END)

class HttpTests(unittest.TestCase):
    def test_retry_after_and_rate_limit(self):
        from types import SimpleNamespace
        responses=iter([SimpleNamespace(status_code=429,headers={'Retry-After':'8'}),SimpleNamespace(status_code=200,headers={},json=lambda:[])])
        session=SimpleNamespace(get=lambda *a,**k:next(responses));sleeps=[]
        client=HttpClient(session=session,sleep=sleeps.append,clock=lambda:10)
        self.assertEqual(client.get('https://synthetic.invalid',{},{}),[]);self.assertIn(8,sleeps);self.assertIn(5,sleeps)
    def test_unauthorized_does_not_retry(self):
        from types import SimpleNamespace
        session=SimpleNamespace(get=lambda *a,**k:SimpleNamespace(status_code=401))
        with self.assertRaisesRegex(SourceError,'401'):HttpClient(session=session).get('https://synthetic.invalid',{}, {})
    def test_retry_budget(self):
        from types import SimpleNamespace
        session=SimpleNamespace(get=lambda *a,**k:SimpleNamespace(status_code=429,headers={}))
        with self.assertRaisesRegex(SourceError,'budget'):HttpClient(session=session,sleep=lambda _:None,retries=1).get('https://synthetic.invalid',{}, {})

@patch.dict(os.environ,{'COINGECKO_API_KEY':'synthetic-not-a-real-key','COINGECKO_TIER':'demo','COINGECKO_REDISTRIBUTION_CONFIRMED':'true'})
class PriceTests(unittest.TestCase):
    def test_auth_and_response(self):
        c=Pages([{'prices':[[1767268800000,1.25]]}]);rows=PriceProvider(c).fetch(START,END)
        self.assertEqual(rows[0]['price'],1.25);self.assertIn('x-cg-demo-api-key',c.calls[0][2]);self.assertIn('/coins/near/',c.calls[0][0])
    def test_batching(self):
        c=Pages([{'prices':[[1767268800000,1]]},{'prices':[[1775044800000,2]]}]);PriceProvider(c).fetch(START,'2026-05-01T00:00:00Z');self.assertEqual(len(c.calls),2)
    def test_schema(self):
        for data in ({}, {'prices':[]},{'prices':[[1,-1]]},{'prices':[[1,float('nan')]]}):
            with self.assertRaises(SourceError):PriceProvider(Pages([data])).fetch(START,END)

class ThesisTests(unittest.TestCase):
    def result(self,p,values):return [{'pair':'volume → '+k,'lag':0,'n':40,'rho':r} for k,r in zip(['price','signers','transactions','contracts'],[p,*values])]
    def test_insufficient(self):self.assertEqual(verdict([]),'Insufficient data')
    def test_support(self):self.assertEqual(verdict(self.result(.1,[.5,.6,.7])),'Evidence supports the hypothesis')
    def test_negative(self):self.assertEqual(verdict(self.result(.8,[.1,.2,.3])),'Evidence does not support the hypothesis')
    def test_mixed(self):self.assertEqual(verdict(self.result(.4,[.5,.2,.7])),'Mixed or inconclusive evidence')
    def test_small_sample(self):
        r=self.result(.1,[.5,.6,.7]);r[0]['n']=29;self.assertEqual(verdict(r),'Insufficient data')

class ProvenanceTests(unittest.TestCase):
    def test_hash_and_synthetic_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'intents.json';f.write_text('[]')
            meta=dict(source='intents',path='intents.json',sha256=digest(f),retrieved_at=END,start=START,end=END,complete=True,origin='https://explorer.near-intents.org/api/v0/transactions',method='Synthetic test only',redistribution_confirmed=True,authenticated=True)
            m=root/'intents.manifest.json';m.write_text(json.dumps(meta));self.assertEqual(load_export(root,'intents',START,END)[0],[])
            meta['synthetic']=True;m.write_text(json.dumps(meta))
            with self.assertRaises(SourceError):load_export(root,'intents',START,END)
            meta.pop('synthetic');m.write_text(json.dumps(meta));f.write_text('[1]')
            with self.assertRaises(SourceError):load_export(root,'intents',START,END)
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SourceError):load_export(d,'intents',START,END)

try:import pandas as pd
except ImportError:pd=None
@unittest.skipIf(pd is None,'pandas not installed; dependency download blocked')
class StatisticsTests(unittest.TestCase):
    def test_missing_calendar_and_moving(self):
        from scripts.analysis.metrics import calendar_series,moving,changes,indexed
        s=calendar_series([{'date':'2026-01-01','x':0},{'date':'2026-01-03','x':2}],'x')
        self.assertTrue(pd.isna(s.iloc[1]));self.assertTrue(moving(s,2).isna().all());self.assertTrue(changes(s).isna().all());self.assertTrue(indexed(s).isna().all())
    def test_spearman_and_lag_alignment(self):
        from scripts.analysis.correlations import correlate
        x=pd.Series(range(40),index=pd.date_range('2026-01-01',periods=40,tz='UTC'));y=x.copy();y.index=y.index+pd.Timedelta(days=7)
        r=correlate(x,y,7);self.assertAlmostEqual(r['rho'],1);self.assertEqual(r['n'],40)
        self.assertIsNone(correlate(x.iloc[:20],y,7)['rho'])
    def test_full_moving_window(self):
        from scripts.analysis.metrics import moving,changes
        s=pd.Series(range(1,32));self.assertEqual(moving(s,7).iloc[6],4);self.assertTrue(pd.isna(moving(s,30).iloc[28]));self.assertEqual(changes(s).iloc[1],1)
    def test_zero_denominator(self):
        from scripts.analysis.metrics import changes
        result=changes(pd.Series([0,2,4]));self.assertTrue(pd.isna(result.iloc[1]));self.assertEqual(result.iloc[2],1)

if __name__=='__main__':unittest.main()
