"""Private, nonpublishing CoinGecko check. Run locally outside the Codex sandbox."""
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.providers.price_provider import PriceProvider
from scripts.providers.common import SourceError,bounds

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',default='2026-11-03')
    parser.add_argument('--end',default='2026-11-10',help='Exclusive UTC end date')
    args=parser.parse_args(argv)
    load_dotenv(ROOT/'.env')
    try:
        start=args.start+'T00:00:00Z';end=args.end+'T00:00:00Z'
        bounds(start,end)
        report=PriceProvider().probe(start,end)
    except SourceError as exc:
        # Provider errors contain controlled messages, never upstream bodies.
        print(json.dumps({'status':'failed','reason':str(exc),'published':False}))
        return 2
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,'published':False}))
        return 2
    print(json.dumps(report,indent=2))
    return 0 if report['complete_daily_coverage'] else 2

if __name__=='__main__':sys.exit(main())
