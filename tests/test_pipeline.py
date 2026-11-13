"""Runs credential-free empty replay and checks production output consistency."""
import csv,json,unittest,tempfile,contextlib,io
from pathlib import Path
from unittest.mock import patch
from scripts.provenance import digest
from scripts import rebuild
class PipelineTests(unittest.TestCase):
    def test_strict_and_partial_rebuild(self):
        # Synthetic empty replay must never rewrite the real dashboard or source exports.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(rebuild,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
                for extra,expected in [([],2),(['--allow-partial'],0)]:
                    self.assertEqual(rebuild.main(['--start','2026-01-01','--end','2026-02-01',*extra]),expected)
            data=json.loads((root/'public/data/dashboard.json').read_text())
            self.assertEqual(data['series'],[]);self.assertEqual(data['verdict'],'Insufficient data')
            for name in ('network','intents','price'):
                with (root/f'public/data/{name}.csv').open(newline='') as f:self.assertEqual(list(csv.DictReader(f)),data['daily'].get(name,[]))
            manifest=json.loads((root/'data/manifest.json').read_text())
            for f in manifest['outputs']:self.assertEqual(digest(root/f['path']),f['sha256'])
if __name__=='__main__':unittest.main()
