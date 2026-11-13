# Incremental historical acquisition

Both verified November 9 exports are present. Source manifests, raw response
hashes and recomputed counts/Decimal totals match the reported measurements.
No extra history was fetched during implementation of this workflow.

## Exact, nondestructive merges

Both extraction CLIs publish through `scripts/history.py`. New nonoverlapping
dates merge with existing records. Transactions merge by UTC date; swaps by
deposit address plus memo. Identical overlapping records deduplicate. Changed
known metrics, changed swaps, omitted old swaps or new swaps that revise an
already complete old interval fail for analyst review, rather than silently
rewriting earlier evidence. Null contract fields cannot erase acquired calls;
later verified calls can fill previously null observations.

Original source bytes and manifests are archived under `data/raw/history/`.
Merged manifests retain acquisition segments, response hashes and query logs.
Disjoint coverage intervals remain explicit; gaps are not represented as a
complete continuous span and missing days never become zero. A publication lock,
staged replay, integrity checks and rollback protect existing datasets. If a
process dies while holding `data/.history.lock`, investigate before removing a
stale lock; it is not automatically bypassed.

## Safest initial extension: seven days ending November 9

Acquire **November 3–8**, end-exclusive November 9. The existing November 9 is
preserved, yielding seven days if every requested day succeeds. Prioritize exact
transaction counts and distinct signers; calls remain missing on newly acquired
days. Their omission is disclosed and does not relax the verdict requirements.

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_LOCATION = 'us-east1'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-03 --end 2026-11-09 --skip-contracts --execute
```

The provider tries the bounded full range, then two-day windows, then individual
days if an estimate exceeds the cap. Exact daily GROUP BY/distinct aggregation is
preserved. All planned data jobs must pass dry-runs before any data job executes.
Six daily transaction jobs plus metadata reserve at most 700,000,000 bytes. This
is a conservative authorization bound, **not a measured cost estimate**. An
oversized or unknown single-day estimate remains fatal. Partition metadata is
transactions-only when calls are omitted. No receipt table/schema permission is
required in that mode. Every data table still has an explicit block_date predicate.

Then backfill matching 1Click history, without changing the credential:

```powershell
python scripts/extract_intents.py --start 2026-11-03 --end 2026-11-09 --page-size 1000 --max-pages 500
```

The 500-page limit is a request budget, not a claim it will exhaust this range.
Requests/retries are at least five seconds apart. Run one process per partner and
leave five seconds between separate Explorer commands. Exhaustion of the page
budget leaves the period incomplete and cannot publish a partial dataset.

## Fourteen-day alternative, only if dry-runs fit

To target fourteen total days ending November 9, use these **alternative** date
arguments on the same commands: `--start 2026-10-27 --end 2026-11-09`.
Do not run repeated fresh-budget batches just to force an over-budget plan through.
Thirteen new dates need seven two-day-or-smaller transaction jobs if each two-day
estimate passes, plus metadata: at most 800 MB in full-cap reservations. Up to
two additional daily splits still fit 1 GB. More splits exceed the conservative
cumulative cap and stop before metric execution; use the seven-day strategy.
This is conditional planning, not verified coverage or an authenticated estimate.

The existing cumulative counter is shared across every query in **one CLI run**,
including metadata attempts. It is not an account-wide or lifetime spending
ledger. Separate invocations can incur further charges. Budgets are never reset
within a run to bypass a rejected historical plan. No new paid query was run by
Codex while preparing these commands.

Remove `--skip-contracts` only if full call and timestamp-coverage plans fit the
same budget. November 9's earlier observed call-only and receipt-coverage scans
were 89,896,923 and 69,761,504 bytes; longer ranges/different dates need their
own dry-runs. There is no safe assumption that all calls fit for 7–14 days.

## Replay and statistical readiness

After both seven-day backfills succeed:

```powershell
python scripts/rebuild.py --mode replay --sources network,intents --start 2026-11-03 --end 2026-11-10
```

The actual present command is the same with `--start 2026-11-09`. It currently
reports one common level observation, zero paired daily changes, no price overlap
and Insufficient Data. The dashboard reports common coverage explicitly.

Seven to fourteen days can establish historical charts and seven-day averages,
but cannot meet the prespecified 30 paired-change threshold. With contiguous
data, same-day correlations require at least 31 level observations; 7-/30-day
lagged comparisons over equally bounded series require at least 38/61. A
licensed price series and all native metrics on the same valid dates are also
required for the current verdict. Missing contracts/price do not become proxies,
zeros or evidence supporting the thesis.

Raw inputs remain ignored by default. Review redistribution rights and include
the verified raw exports/manifests/response files when preparing a public repo.
The local source archive includes these replay inputs and excludes .env, ADC,
node_modules, failed-attempt response directories and private credentials.
