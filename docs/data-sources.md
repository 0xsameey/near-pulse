# Data adapters and configuration

## Initial three-day network acquisition after discovery

### Cost optimization and smallest supported window

The saved November 13 failure was the **November 9 single-day contract-call
query**, estimated at 124,777,675 bytes, not a signer query. Splitting the old
three-day action query (378,608,723 bytes) had already failed to meet the cap.

The extractor now queries `action_kind` aggregation separately from the
`block_timestamp_utc` coverage check, with a mandatory `block_date` predicate on
both. Exact function-call, null-kind and row counts are preserved. The two daily
receipt row totals must agree before combining coverage; otherwise the source
may have changed and publication fails. Transaction and distinct signer metrics
now share one exact daily aggregation over the same columns instead of scanning
signers twice. Distinct signers are never summed across account subsets.

Each of these three query groups still needs a successful dry-run. Oversized
multi-day queries fall back to daily queries; oversized daily queries remain
fatal. `LIMIT`, sampling, approximate counts and sub-day filters that pretend to
prune a daily partition are not used. The saved schema establishes only DAY
partitioning, not a finer clustering/index guarantee. If the action-kind-only
single-day query still exceeds 100 MB, no further exact scan reduction is assumed.
No estimate for the new SQL has been authenticated in this optimization task.

The smallest supported full-day request is November 9 alone:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_LOCATION = 'us-east1'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-09 --end 2026-11-10 --execute
```

This is a cost-guarded request, not a claim that its new estimates have passed.
For a one-day request there are three data jobs plus optional metadata, each
requiring its own dry-run and full-cap reservation. A three-day request can
require nine single-day data jobs plus metadata, exactly the existing 1 GB
conservative reservation ceiling. Unknown/over-budget estimates remain fatal.
`validation-evidence/network-cost-diagnosis.json` retains the earlier query and
reported estimates; new job logs identify metric, SQL file and requested bounds.

The saved `data/schema.json` confirms daily `block_date` DATE partitions and
the actual column names used by `sql/verified_*.sql`. A versioned metadata copy
is retained at `validation-evidence/network-discovery-schema.json`. Saved
partitioning configuration is **not dated partition availability evidence**.
Use the following command in normal PowerShell outside the restricted Codex
sandbox. It uses existing ADC and the official BigQuery client; no token should
be printed or pasted into chat.

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_LOCATION = 'us-east1'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-09 --end 2026-11-12 --execute
```

The last environment flag explicitly confirms permission to export the public
aggregates. The execution flag and paid-query configuration are both required.
Omit `--execute` for dry-runs only; this cannot confirm partition existence or
acquire data. Every query, including metadata SQL, passes through the existing
100 MB/query and 1 GB cumulative safeguards. No raised cap or alternate source
is used. The run is limited to 1–3 elapsed UTC days. Over-budget multi-day data
queries are retried as separately dry-run one-day queries. If even a single-day
query is too large, execution stops; hours are not used to pretend partition
pruning saves bytes. All data plans must pass before executing any data query.
Conservative full-cap reservations include the earlier metadata job.

The required query region is `us-east1`, not the `US` multi-region. The adapter
uses `BIGQUERY_LOCATION` for its client and explicitly for every query submission,
including metadata SQL and dry-runs. Schema discovery's `get_table()` operations
are HTTP metadata lookups using that client, not query jobs; the SDK does not
accept a location parameter on `get_table()`. Query reports and network source
manifests retain the configured location. The November 13 user-reported
authenticated COUNT(*) dry-run estimated 7,130,376 bytes for November 11 in
`us-east1`; the corresponding `US` request failed with 403. This is not proof
of metric extraction, other query estimates or three-day coverage. Every query
still requires its own dry-run and limit checks.

The extractor first revalidates live schemas, then reads bounded
INFORMATION_SCHEMA.PARTITIONS metadata. That metadata query filters table names
and partition IDs: the metadata view has no `block_date` column. Every actual
data query directly filters `block_date >= @start AND block_date < @end`, using
DATE parameters. No joins are needed, avoiding receipt multiplication.

If and only if the API raises a typed `google.api_core.exceptions.Forbidden`
whose access-denied table is exactly this dataset's
`INFORMATION_SCHEMA.PARTITIONS` view, that lookup is optional. The extractor
continues with the existing bounded data queries. An authentication error,
other-table/dataset denial, unknown estimate, cost rejection, 404, invalid query,
or live schema discovery error remains fatal. No permission is changed or
alternate account/source used. This is an explicit data-query verification
path, not an assumption that the requested partitions exist.

Metrics: transaction **table rows** across all statuses; distinct signing
accounts; FUNCTION_CALL **receipt-action rows** (including delegated rows as
represented in the table), not unique receipts or proven successful execution.
This initial counting method does not assert uniqueness of undocumented action
keys. Account identity does not identify humans.

For each date, when metadata is available, transaction and receipt-action row
totals must equal the earlier partition totals. In either mode, signers cannot
exceed transactions, required columns
cannot be null, and each table must represent all 24 UTC hours. Missing
partitions/dates are never converted to zero. These checks establish observed
full-day coverage, **not proof that upstream indexing omitted no blocks**. A
metadata mismatch can reflect source mutation and fails closed for review.

In the narrowly scoped permission fallback, both tables must have positive
executed daily row counts for every requested day. The existing date-bounded
metric queries provide this evidence without extra unbounded scans. A dry-run
does not establish availability, even if it succeeds. Provenance retains the
exact metadata denial, `partitions: null`, mode `bounded_data_queries`, and null
metadata-comparison results; it does not fabricate a replacement metadata
snapshot. Independent partition row-count comparison is unavailable in this
mode. Job IDs and actual processing bytes must be known for successful metric
jobs, and all caps/reservations continue to apply, including a metadata attempt
that reserved budget before failing. Failed dry-runs/API errors are logged while
retaining their original exception type.

On success, the extractor stages an offline rebuild and publishes actual
network raw exports/manifests, dashboard JSON/CSV and evidence. A failed source
validation or staged rebuild leaves production datasets unchanged. Only three
observations means 7/30-day averages and correlations remain unavailable.
No Intents or price observations are inferred from network data.

`validation-evidence/network-three-day.json` records errors or metrics, source
schemas, partition snapshot, consistency checks, exact SQL, parameters,
dry-run estimates, executed job IDs, actual processed bytes and cap reservations.
If this command fails, retain that report. A successful command prints the
three actual metric rows and sets status `verified_and_exported`. Refresh the
dashboard exports in the running app afterward; static deployment would require
rebuilding separately, and is not authorized here.

Native/Explorer acquisition has succeeded locally for November 9. Synthetic
tests do not establish acquisition for additional dates. Raw exports remain
ignored until explicitly reviewed/versioned.

## Google Cloud / BigQuery

Create a [Google Cloud project](https://console.cloud.google.com/projectcreate),
enable the BigQuery API and authorize billing. Configure `BIGQUERY_PROJECT_ID`.
Install the Google Cloud CLI and run `gcloud auth application-default login` for
local Application Default Credentials. Alternatively set
`GOOGLE_APPLICATION_CREDENTIALS` to an authorized credentials file outside the
repository. ADC is handled by the official `google-cloud-bigquery` client; no
private key is sent to the frontend. Grant only required dataset-read/job roles.

Install `requirements-bigquery.txt`, then run:

```powershell
python scripts/rebuild.py --mode discover
```

This uses table metadata APIs, not paid SQL. It records full schemas, temporal
partition configuration and range partition metadata for all three intended
tables in `bigquery-public-data.crypto_near_mainnet_us`: `transactions`,
`receipt_actions`, `receipt_origin_transaction`. No columns are assumed.

After inspecting `data/schema.json`, configure `BIGQUERY_COLUMN_MAP` as one-line
JSON. Role structure (the words in angle brackets are descriptions, **not actual
source columns**):

```json
{
  "transactions": {"date":"<observed temporal partition column>","id":"<observed unique transaction identity>","signer":"<observed signing account>"},
  "receipt_actions": {"date":"<observed temporal partition column>","id":["<observed receipt identity>","<observed action index>"],"action":"<observed action type>"}
}
```

Single or composite IDs are supported. Every column must exist in discovered
metadata, be scalar and have a valid identifier. Temporal partition column must
match the mapping. Unsupported nested/repeated or non-temporal grain fails closed.
Confirm the function-call enum in `BIGQUERY_FUNCTION_CALL_VALUE`, and set
`BIGQUERY_ACTION_GRAIN_CONFIRMED=true` only after verifying that the configured
identity represents one action. Counting distinct receipt IDs alone may undercount
multiple function calls per receipt. The direct action table needs no origin join;
the origin table is inspected and recorded, but never joined speculatively.

```powershell
python scripts/rebuild.py --mode live --sources network --start 2026-01-01 --end 2026-02-01
```

This performs dry-runs only. Review exact rendered SQL, parameters and scan
estimates in `data/query-jobs.json`. Dry-run estimates are not currency quotes.
The templates in `sql/` are intentionally not runnable until schema validation.
To authorize paid jobs, explicitly set `BIGQUERY_ALLOW_PAID_QUERIES=true`, confirm
redistribution, and add `--execute-bigquery` to the same command. Both controls
are required; the default command never executes paid queries. Each query has
`maximum_bytes_billed`, finite partition predicates, no uncontrolled job retries,
and a full cap reserved against the cumulative byte budget. Timeouts request
cancellation and retain job IDs; cancellation does not guarantee zero billing.
The cumulative limit applies to a single process/run, not all historical runs.
The provider rejects configuration above the authorized 100,000,000-byte/query
and 1,000,000,000-byte/run ceilings. Rejected estimates remain in its job log;
unknown, negative or non-integer estimates cannot authorize execution.
Repeated live rebuilds can incur repeated charges. Maximum bytes is a scan limit,
not a guaranteed maximum currency invoice. No paid query was run here.

## NEAR Intents Explorer

Current November 13 status: local authenticated acquisition for November 9 succeeded.
Verified source/response hashes and recomputation confirm 20,243 SUCCESS 1Click
swaps and exact input volume $43,331,710.006694590507. Pagination exhausted in 22
pages with zero duplicates. Earlier sandbox probes failed before HTTP; those are
historical failures, not the current dataset status. No credential was exposed.

Run a bounded probe in normal PowerShell outside this sandbox:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
python scripts/extract_intents.py --probe --start 2026-11-09T12:00:00Z --end 2026-11-09T12:01:00Z --page-size 25 --max-pages 3
```

After a successful probe, retrieve the full day matching the existing network
export. The export flag confirms permission to cache and redistribute the data:

```powershell
Start-Sleep -Seconds 5
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_intents.py --start 2026-11-09 --end 2026-11-10 --page-size 1000 --max-pages 100
```

The script reads `INTENTS_EXPLORER_JWT` from `.env`; do not pass it as a command
argument or print it. Run one acquisition process per partner and leave five
seconds between separate commands. This uses the existing Explorer adapter,
never BigQuery or alternate sources. HTTP success does not prove nonempty
schema or full-day coverage. Probe budgets are at most three pages of 25 rows;
export has explicit page budgets and midnight `[start,end)` UTC bounds, up to 14 days.
Use history-acquisition.md to add nonoverlapping dates without replacing history.

Complete exports write `data/raw/intents.json`, its manifest and original
response bodies under `data/raw/intents-responses/`. Each response has a hash
and secret-free request provenance. Source and dashboard JSON/CSV are staged in
a temporary directory before publication. Sources retain their own dates and
prior observed values. New dates merge; gaps stay explicit and revisions require
review. Partial pagination and invalid records cannot replace datasets. Captured
pages can remain for diagnosis after failure, labeled incomplete in the report.

`validation-evidence/intents-acquisition.json` separately records authenticated
HTTP success, schema validation, observed coverage, successful swap count, exact
input USD sum, pagination audit and errors. The successful local report is now
backed by verified source files and the complete pagination audit.
Review raw exports and distribution rights before versioning; raw JSON is ignored.

Register at [NEAR Intents partners](https://partners.near-intents.org) and request
access to the **Explorer** API. Confirm the token grants historical Explorer
access: 1Click quote credentials must not be assumed to grant it. Put the JWT in
`INTENTS_EXPLORER_JWT` in local `.env`.

The [official transaction contract](https://docs.agentsonintents.com/api-reference/get-transactions)
defines `GET https://explorer.near-intents.org/api/v0/transactions`, Bearer JWT,
`statuses=SUCCESS`, creation-time bounds and address/memo cursor pagination.
Requests are spaced at least five seconds apart; this is process-local rate
limiting, so run a single acquisition process per partner. HTTP 429 and 5xx
responses use bounded retries and honor seconds or HTTP-date `Retry-After`.
Waits above 300 seconds fail closed. Every request has connection/read timeouts.
Page count is bounded and repeated cursors stop the run as incomplete. A short
page does not prove exhaustion; an empty page is required. A failed period is
never saved as a complete source export. Duplicate deposit address + memo pairs
are accepted only if identical; conflicts fail. Stable identity follows the
documented deposit-address/memo contract and still needs confirmation against
authenticated source records before investment use.

The UI uses `[start, end)` UTC daily boundaries. Explorer's API bounds are
non-inclusive, so the API start is one millisecond earlier to include a swap
created exactly at midnight; the adapter then enforces the requested window.
This timestamp precision assumption must be checked during live validation.
Creation date is **not completion date**. `SUCCESS` is the status at extraction;
recent historical days may revise as pending swaps settle. These are 1Click
input-USD amounts, not all Intents volume, native-chain fees, or token demand.

## CoinGecko

Create a key in the [CoinGecko Developer Dashboard](https://www.coingecko.com/en/developers/dashboard).
Set `COINGECKO_API_KEY` and `COINGECKO_TIER=demo` or `pro` to match the plan.
Historical coverage and redistribution rights depend on that plan; request
appropriate licensing from CoinGecko. Set `COINGECKO_REDISTRIBUTION_CONFIRMED=true`
only after confirming permission to distribute the resulting public exports.

The adapter calls `/api/v3/coins/near/market_chart/range` with USD and finite Unix
time bounds, splitting windows into at most 90-day batches. Demo and Pro use
their respective official hosts and header names. Samples are validated, sorted
and deduplicated; invalid/nonpositive prices or conflicting timestamps fail.
Daily price is the last available sample in each UTC day, not an exchange close.
API granularity can vary; raw timestamps are preserved. Missing dates stay gaps.
Rate interval defaults to six seconds; retries share the bounded HTTP policy.
No unsupported scraping or alternate price feed is used.

## Replay provenance contract

Raw exports contain arrays: network daily `{date, transactions, signers,
contracts}`; Explorer original transaction objects; price `{timestamp, price}`.
Each manifest must include `source`, relative `path`, `sha256`, UTC
`retrieved_at`, `start`, `end`, `complete: true`, `authenticated: true`,
`synthetic: false`, `origin`, `method`, and `redistribution_confirmed: true`.
Network exports additionally retain query jobs, parameters and metadata.
Paths must remain under `data/raw`; hashes and coverage are checked before use.

These controls establish file integrity and documented provenance, not
cryptographic proof of upstream authenticity. Independently review who produced
an imported export. Never mark a synthetic fixture authenticated. Synthetic
records exist only in tests and temporary test directories. Redistributable raw
exports must be reviewed and explicitly added to Git before judge replay is
possible. Verified network and Explorer exports exist for November 9; price
history is missing. Strict full replay fails on missing inputs/coverage.
Incremental commands and merge rules are in history-acquisition.md.

## Historical coverage audit ? November 13, 2026

Transactions/signers and successful 1Click counts/input volume cover every UTC
date November 3?9 inclusive. Contract calls cover November 9 only; November 3?8
calls remain null. Prices are unavailable. Merged Explorer: 134,156 unique swaps,
$263,033,264.614200753422 input volume. Original November 9 records remain intact
in both merged sources and SHA-256-verified archives. All 137 original response
page hashes validate. The six-day network backfill was already published; no
recovery or external queries were needed. Seven levels yield six paired daily
changes, below the 30-pair threshold. The verdict remains Insufficient data.
Earlier one-day descriptions are historical baseline notes. See
[price configuration](price-configuration.md) and
`validation-evidence/historical-audit.json` for exact observations.
