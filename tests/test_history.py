"""All observations and provenance in these tests are synthetic temporary fixtures."""
import json,tempfile,unittest,io,contextlib
from pathlib import Path
from scripts.history import merge_source,publish_history
from scripts.rebuild import write
from scripts.provenance import digest,load_export
from scripts.providers.common import SourceError

def meta(source,start='2026-11-09',end='2026-11-10'):
    return {'source':source,'path':source+'.json','sha256':'assigned-after-write','start':start+'T00:00:00Z','end':end+'T00:00:00Z',
            'retrieved_at':'2026-11-13T00:00:00Z','complete':True,'authenticated':True,'synthetic':False,
            'redistribution_confirmed':True,'origin':'bigquery-public-data.crypto_near_mainnet_us' if source=='network' else 'https://explorer.near-intents.org/api/v0/transactions',
            'method':'Synthetic test only','query_jobs':[{'job_id':'synthetic-'+start,'actual_bytes':10}]}
def network(day='2026-11-09',contracts=5):return {'date':day,'transactions':10,'signers':3,'contracts':contracts}
def swap(identity='synthetic-a',day='2026-11-09'):
    return {'depositAddress':identity,'depositMemo':None,'createdAt':day+'T12:00:00Z','status':'SUCCESS','amountInUsd':'0.1','originAsset':'synthetic:test'}

class HistoryTests(unittest.TestCase):
    def test_concurrent_publication_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir();(root/'data/.history.lock').write_text('synthetic other process')
            with self.assertRaisesRegex(SourceError,'publication is active'):publish_history(root,'network',[network()],meta('network'))
            self.assertFalse((root/'data/raw/network.json').exists())
    def test_network_overlap_idempotence(self):
        m=meta('network');rows,merged=merge_source('network',[network()],m,[network()],m)
        self.assertEqual(rows,[network()]);self.assertEqual(len(merged['query_jobs']),1)
    def test_conflicting_network_day_is_rejected(self):
        with self.assertRaisesRegex(SourceError,'revision'):
            merge_source('network',[network()],meta('network'),[{**network(),'transactions':11}],meta('network'))
    def test_optional_contracts_do_not_erase_prior_value(self):
        rows,_=merge_source('network',[network()],meta('network'),[network(contracts=None)],meta('network'))
        self.assertEqual(rows[0]['contracts'],5)
    def test_optional_contracts_can_be_backfilled(self):
        rows,_=merge_source('network',[network(contracts=None)],meta('network'),[network()],meta('network'))
        self.assertEqual(rows[0]['contracts'],5)
    def test_swap_deduplication_and_revision_rejection(self):
        m=meta('intents');rows,_=merge_source('intents',[swap()],m,[swap()],m)
        self.assertEqual(rows,[swap()])
        with self.assertRaisesRegex(SourceError,'revision'):
            merge_source('intents',[swap()],m,[{**swap(),'amountInUsd':'0.2'}],m)
        with self.assertRaisesRegex(SourceError,'already complete'):
            merge_source('intents',[swap()],m,[swap(),swap('synthetic-b')],m)
    def test_refreshed_window_cannot_omit_old_swap(self):
        with self.assertRaisesRegex(SourceError,'omits'):
            merge_source('intents',[swap()],meta('intents'),[],meta('intents'))
    def test_new_date_is_added_and_sorted(self):
        rows,m=merge_source('intents',[swap()],meta('intents'),[swap('synthetic-b','2026-11-08')],meta('intents','2026-11-08','2026-11-09'))
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['createdAt'],'2026-11-08T12:00:00Z')
        self.assertEqual(len(m['coverage_intervals']),1)
    def test_incremental_export_preserves_other_source_and_gaps(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory)
            publish_history(root,'network',[network()],meta('network'))
            original=digest(root/'data/raw/network.json')
            publish_history(root,'intents',[swap()],meta('intents'))
            self.assertEqual(digest(root/'data/raw/network.json'),original)
            publish_history(root,'network',[network('2026-11-11',None)],meta('network','2026-11-11','2026-11-12'))
            rows,m=load_export(root/'data/raw','network','2026-11-09T00:00:00Z','2026-11-12T00:00:00Z',require_coverage=False)
            self.assertEqual(len(rows),2);self.assertEqual(rows[0],network())
            self.assertIsNone(rows[1]['contracts']);self.assertEqual(len(m['coverage_intervals']),2)
            with self.assertRaisesRegex(SourceError,'gap'):
                load_export(root/'data/raw','network','2026-11-09T00:00:00Z','2026-11-12T00:00:00Z')
            dashboard=json.loads((root/'public/data/dashboard.json').read_text())
            gap=next(r for r in dashboard['series'] if r['date']=='2026-11-10')
            self.assertIsNone(gap['transactions'])
            self.assertEqual(dashboard['daily']['intents'][0]['swaps'],1)
            self.assertEqual(dashboard['verdict'],'Insufficient data')
            self.assertTrue(list((root/'data/raw/history/network').glob('*.manifest.json')))
    def test_conflict_cannot_change_existing_files(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);publish_history(root,'network',[network()],meta('network'))
            old=(root/'data/raw/network.json').read_bytes();dashboard=(root/'public/data/dashboard.json').read_bytes()
            with self.assertRaises(SourceError):publish_history(root,'network',[{**network(),'signers':4}],meta('network'))
            self.assertEqual((root/'data/raw/network.json').read_bytes(),old)
            self.assertEqual((root/'public/data/dashboard.json').read_bytes(),dashboard)

if __name__=='__main__':unittest.main()
