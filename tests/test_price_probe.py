"""Synthetic in-memory responses only; no real HTTP or financial observations."""
import os
from unittest.mock import patch
import pytest
from scripts.providers.price_provider import PriceProvider
from scripts.providers.common import SourceError

class Client:
    def __init__(self,data):self.data=data;self.calls=[]
    def get(self,*args):self.calls.append(args);return self.data

@pytest.fixture
def config():
    with patch.dict(os.environ,{'COINGECKO_API_KEY':'synthetic-secret','COINGECKO_TIER':'demo','COINGECKO_REDISTRIBUTION_CONFIRMED':'false'}):yield

def test_probe_does_not_relax_publication_gate(config):
    client=Client({'prices':[[1793664000000,1.25]]});provider=PriceProvider(client)
    report=provider.probe('2026-11-03T00:00:00Z','2026-11-04T00:00:00Z')
    assert report['complete_daily_coverage'] and not report['published']
    assert '1.25' not in str(report) and 'synthetic-secret' not in str(report)
    assert os.environ['COINGECKO_REDISTRIBUTION_CONFIRMED']=='false'
    with pytest.raises(SourceError,match='redistribution'):provider.fetch('2026-11-03T00:00:00Z','2026-11-04T00:00:00Z')
    assert len(client.calls)==1

def test_missing_days_reported(config):
    report=PriceProvider(Client({'prices':[[1793664000000,1.25]]})).probe('2026-11-03T00:00:00Z','2026-11-05T00:00:00Z')
    assert report['missing_utc_dates']==['2026-11-04']
    assert not report['complete_daily_coverage']

def test_invalid_response_and_excessive_window_rejected(config):
    with pytest.raises(SourceError):PriceProvider(Client({'prices':[]})).probe('2026-11-03T00:00:00Z','2026-11-04T00:00:00Z')
    client=Client({})
    with pytest.raises(SourceError,match='14 days'):PriceProvider(client).probe('2026-10-01T00:00:00Z','2026-11-04T00:00:00Z')
    assert not client.calls
