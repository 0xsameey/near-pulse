# Historical NEAR/USD configuration

No price request was made during this offline audit. Prices remain unavailable.

Create a key in the [Developer Dashboard](https://www.coingecko.com/en/developers/dashboard), following the [official setup guide](https://docs.coingecko.com/docs/setting-up-your-api-key). Add these server-side settings to the local project `.env`:

```dotenv
COINGECKO_API_KEY=<your local key>
COINGECKO_TIER=demo
COINGECKO_INTERVAL_SECONDS=6
COINGECKO_REDISTRIBUTION_CONFIRMED=false
SOURCE_REDISTRIBUTION_CONFIRMED=false
```

Set the confirmation flags only after confirming applicable export and public redistribution rights. Select `pro` for a Pro API key. Do not use VITE_ variables or commit `.env`. This audit did not change credentials.

## Private authentication and coverage probe

The public provider requires `COINGECKO_REDISTRIBUTION_CONFIRMED` to equal the
literal string `true` before sending a request. The reported licensing error
therefore does not establish an HTTP or authentication failure. The generic live
rebuild also requires `SOURCE_REDISTRIBUTION_CONFIRMED=true` before export.

Keep both flags false while rights remain unconfirmed. Run the following only
in your own PowerShell terminal outside the restricted Codex sandbox:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
python scripts/probe_price.py --start 2026-11-03 --end 2026-11-10
```

The end date is exclusive. This requests November 3–9 UTC, keeps responses and
prices in memory, and writes no files. It prints only a controlled success/error
summary, sample count, observed/missing UTC dates and coverage status. It never
prints the key, headers, response bodies or prices. It does not call the rebuild
or publisher, alter flags, or change source/dashboard files. A successful private
probe is not permission to display or redistribute data. HTTP errors remain
failures; incomplete daily coverage exits with status 2. The probe is capped at
14 days and uses the adapter's existing pacing, retries and schema validation.

## Public display versus redistribution

Confirm the actual intended use against the applicable plan and any agreement
with CoinGecko. Their [licensing explanation](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses)
distinguishes attributed public display from redistribution. See the
[API terms](https://www.coingecko.com/en/api_terms) and
[attribution guide](https://brand.coingecko.com/resources/attribution-guide).
Authentication alone confirms neither right.

This static application's JSON, CSV, repository source exports and downloadable
bundles expose reusable price observations. Hiding a CSV download button would
not make public JSON private. Do not enable the current price publication path
unless confirmed rights cover these outputs. Attribution must also meet the
applicable terms. If only display rights are granted, a separately reviewed
delivery design is required before enabling price charts; this gate must remain
closed. Without suitable rights, keep public price unavailable and all price
comparisons unresolved. No subscription purchase is required to run this private
connectivity check.

| Tier | Endpoint | Authentication header |
| --- | --- | --- |
| demo | https://api.coingecko.com/api/v3/coins/near/market_chart/range | x-cg-demo-api-key |
| pro | https://pro-api.coingecko.com/api/v3/coins/near/market_chart/range | x-cg-pro-api-key |

The existing adapter supplies `vs_currency=usd`, UNIX-second `from`/`to`, `precision=full`, and batches at 90 days. Response timestamps are milliseconds. Daily prices use the last observed sample in each UTC day, not an exchange closing auction. Missing days stay missing. The adapter validates positive finite samples, batch bounds and conflicting identities, with shared HTTP pacing/retries. Plan entitlement and quota remain subject to the provider. See the [official endpoint contract](https://docs.coingecko.com/reference/coins-id-market-chart-range).

## Optional local acquisition preserving existing sources

Run only after configuring your own key and confirming rights. This stages November 3–9 price acquisition, then incrementally publishes alongside existing network/Explorer history. A price-only live rebuild directly against the project would omit the other sources from its dashboard output.

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
@'
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from scripts.rebuild import main
from scripts.history import read_source, publish_history
root = Path.cwd()
load_dotenv(root / '.env')
with tempfile.TemporaryDirectory(prefix='near-pulse-price-') as directory:
    stage = Path(directory)
    result = main(['--mode','live','--sources','price','--start','2026-11-03','--end','2026-11-10'], root=stage)
    if result:
        raise SystemExit(result)
    rows, meta = read_source(stage, 'price')
    publish_history(root, 'price', rows, meta)
print('Price acquisition and merged publication completed; inspect coverage before interpreting research.')
'@ | python -
```

This command has not been verified against an authenticated price endpoint. Seven price dates would still provide at most six daily changes and only one date with contract calls. The verdict requires 30 aligned daily-change pairs for each required comparison. Authentication, licensing or entitlement errors must be resolved with the provider, never replaced with invented prices.
