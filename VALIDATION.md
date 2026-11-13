> Current update: the user's November 12 change of direction supersedes the historical instruction below to stop development. The original findings are retained unchanged; an exact report copy is in validation-evidence/initial-validation.md. New measured results follow at the end.

# Milestone 1 ? validation blocked

Validation date: 2026-11-12 UTC. **Do not proceed to Milestones 2?4.** Both primary datasets remain inaccessible from this execution environment. This report distinguishes local probes, fetched documentation and work not run.

## Observed results

| Check | Actual outcome | Interpretation |
| --- | --- | --- |
| Live hackathon instructions | Web tool retrieved HACKATHON.md | `thesis` track and 2026-11-14T23:59:00Z deadline confirmed; independent entries must be disclosed |
| Workspace | Listing C:/Users/PC and creating a project directly there returned access denied | Created independent C:/Users/PC/Documents/Codex/near-pulse instead |
| `.env` | Not found at C:/Users/PC/.env, Documents/.env, Documents/Codex/.env or project/.env | No supplied credentials found in these exact locations; no claim about other directories |
| Process credentials | INTENTS_EXPLORER_JWT, COINGECKO_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT, GCLOUD_PROJECT and BIGQUERY_PROJECT_ID absent | Authenticated upstream checks could not be made |
| Google tooling | `bq` and `gcloud` not found on PATH; google.cloud.bigquery import discovery failed; standard ADC file not present | No configured BigQuery client established |
| BigQuery REST metadata probe | Local HTTPS request failed with WinError 10013 socket permission error | No HTTP response, schema, table accessibility or freshness verified |
| Intents Explorer GET | One local request, one-row limit, SUCCESS status and 2026-03-23 to 2026-03-24 UTC bounds; no JWT available; socket denied | No HTTP response and no API records retrieved; not an authenticated API test |
| Intents web-tool fallback | Bounded endpoint URL could not be retrieved by web tool | Not evidence of a 401, 403, empty dataset or API downtime |
| CoinGecko historical prices | Not requested because optional key absent | Historical entitlement, coverage and prices unverified |

No credentials were printed or committed. No Sentinel files were read or changed.

## Metrics and newest observation dates

| Candidate metric | Intended source and unit | Available observations | Newest date |
| --- | --- | --- | --- |
| Daily signed transactions | BigQuery transactions; transactions/day | Unverified | Unknown |
| Active signing accounts | BigQuery transactions; distinct signing accounts/day | Unverified | Unknown |
| Contract function calls | BigQuery receipt_actions plus receipt_origin_transaction; verified grain needed | Unverified | Unknown |
| Successful 1Click swaps | Explorer SUCCESS rows; unique swaps/day | Unverified | Unknown |
| 1Click input volume | Explorer amountInUsd; USD/day | Unverified | Unknown |
| Historical NEAR price | CoinGecko; USD/NEAR with documented daily convention | Unverified | Unknown |

No live INFORMATION_SCHEMA query ran. No columns, nested fields, keys, status semantics, join cardinalities or block_date types have been discovered. No newest actual indexed block_date was determined for any table. The user's stated NEAR Lake cessation date (2026-03-24) is a planning constraint, **not an observed BigQuery freshness result**. It must not become a fabricated observation or an assumed common comparison endpoint.

## Cost controls and SQL status

SQL jobs submitted: **0**. SQL dry-runs: **0**. No billed query was submitted by these checks. No scan estimates or currency cost estimates are available. No numeric cost estimate can be justified without successful dry-runs and billing configuration.

Proposed conservative limits for resumed validation: 100,000,000 bytes per query and 1,000,000,000 bytes cumulatively. These are caps, not measured estimates. They are configuration placeholders and have not been enforced by a running validator. Do not execute billed SQL until hard controls and dry-run checks exist.

Required sequence when access is restored:

1. Authenticate to an explicitly configured billing project. Query INFORMATION_SCHEMA.COLUMNS for exactly transactions, receipt_actions and receipt_origin_transaction, selecting explicit metadata columns; inspect nested field metadata if needed. Dry-run metadata SQL too. Metadata queries cannot carry a block_date predicate because they describe schema rather than block rows.
2. Verify partition configuration and inspect bounded partition metadata. Metadata's latest partition is only a candidate. Confirm the actual maximum block_date with partition-filtered data queries for each table. Search a documented finite interval backwards if needed; report the searched interval and whether a global latest date is established. Never assume a March cutoff equals freshness.
3. Every data query must name explicit columns and include block_date filters on every partitioned table alias, including joins. Reject missing/unknown dry-run estimates or estimates exceeding the remaining budget. Set maximumBytesBilled on every executed job, disable uncontrolled retries, record estimated and actual bytes and job IDs, and reserve budget conservatively before execution. A LIMIT is not a scan cap.
4. Stop if schema, permissions, query estimates or cumulative spending cannot be bounded. No aggregate SQL has been authored based on assumed fields.

## Explorer contract: documentation only

Official documentation describes an authenticated, read-only **1Click** history API with one request per five seconds per partner, cursor pagination, SUCCESS filtering and non-inclusive start/end timestamps. These are documentation findings, not live response observations. The endpoint must not be labeled all NEAR Intents activity.

After JWT access works, retrieve a small historical interval first, spacing requests by at least five seconds, honoring 429/Retry-After, limiting pages and elapsed time, and preserving cursor plus time bounds on every request. Verify the returned shape and timestamps. Continue using lastDepositAddress plus lastDepositMemo until exhausted; detect repeated cursors. Dedupe using a verified stable swap identity including memo, not a guessed transaction hash. Any incomplete window stays explicitly incomplete. Count successful swaps and sum amountInUsd with decimal arithmetic; report invalid/missing amounts rather than silently coercing them to zero. Daily bucketing semantics require confirmation because creation date and successful execution date differ.

## Fallback choices

- Preferred: restore outbound HTTPS, provide authorized BigQuery billing configuration and Explorer JWT in local ignored configuration, then rerun Milestone 1.
- Judge replay: accept provenance-backed upstream raw exports with complete bounds, query text/job IDs, retrieval times, source timestamps, units and hashes. Verify them before any implementation. None are currently supplied; cached replay does not exist yet.
- Alternative chain indexer: only after explicitly changing source scope, verifying history, semantics and access, and documenting the substitution. It cannot silently be called the requested BigQuery dataset.
- Public Explorer tiles or documentation examples: unsuitable substitutes for a deduplicated daily 1Click history. They have not been imported as data.
- Reduced single-source dashboard: requires a scope change; it would not satisfy the current primary-source validation gate.

## Research gate

No overlapping date range, moving averages, growth rates, correlations, sample sizes or thesis verdicts can be computed yet. Future work must establish complete overlapping daily coverage before paired analysis, retain gaps, use correct growth denominators, and run only supported 0/7/30-day Spearman comparisons. Ecosystem 1Click usage, native NEAR transactions and NEAR token investment demand must remain distinct; correlation alone cannot establish a leading indicator.

## Test outcomes and files

Python environment/configuration probes completed. BigQuery and Explorer local network probes failed before HTTP. Documentation retrieval succeeded. No ingestion, build, chart, statistical, browser or replay tests ran. Milestone 1 is **blocked**, not passed; Milestones 2?4 have not started.

Files created: README.md, VALIDATION.md, .gitignore, .env.example, validation-evidence/bigquery-access.json, validation-evidence/intents-access.json and validation-evidence/manifest.json. Evidence JSON contains failed probe metadata, not source datasets. The final file-integrity readback is reported in the task response.

## References

- https://nearhackathon.com/HACKATHON.md ? retrieved using web tool on validation date.
- https://docs.agentsonintents.com/integration/distribution-channels/1click-api/explorer/introduction ? official Explorer scope, authentication and rate limits; retrieved through web search.
- https://docs.agentsonintents.com/api-reference/get-transactions ? official parameters, pagination and response fields; retrieved through web search.

## Dashboard availability requirement

User requirement: show unavailable/stale data prominently. After validation passes, implement a persistent overall availability banner and explicit per-chart/per-KPI states. Each state must show its reason, latest actual observation date (or unknown), retrieval/refresh timestamp, source and method link. Distinguish source freshness from retrieval freshness. Disclose source-specific staleness thresholds; do not assume the supplied Lake cessation date is an observed newest date. Preserve gaps and mark incomplete coverage. Current state: both primary datasets unavailable from this environment; freshness unknown. This is a recorded requirement, not an implemented or tested UI feature.

## Milestone 4 presentation checks to run later

Record visual polish, accessible colors, responsive design and accurate chart labeling as required acceptance criteria; see README.md for concrete checks. Validate contrast, keyboard navigation, chart text alternatives, mobile layouts and dataset-to-label consistency against real exports. Each chart needs visible source, observation period, refresh date, query/method link and an evidence-supported takeaway. Distinguish 1Click scope, native chain metrics and NEAR token demand. These checks have not run; Milestone 1 remains blocked and no UI has been implemented.

## Milestone 5 delivery requirement

README must provide tested reproducible commands and expected outputs, limitations, attribution and direct source SQL links. Current README provides report-reading and manifest-integrity commands only. Source SQL and application commands remain explicitly pending; no new live-source verification has occurred.


# Implementation validation — November 12, 2026

The user explicitly authorized development without Google Cloud credentials. The earlier access failures remain valid historical observations; they no longer block writing the application. No Sentinel path was accessed. No push, deployment or submission was performed.

## Implemented artifacts

Five React/TypeScript routes, responsive dark/light design system, source-aware chart and metric states, source tables, CSV download controls, method dialogs, common-base comparisons and lag tables. Python adapters use real HTTP/official BigQuery clients, configurable authentication, finite bounds, defensive validation and failure handling. Offline replay, Decimal daily aggregation, asset concentration, pandas/scipy analytics, verdict/evidence outputs and provenance manifests are implemented. SQL templates are schema-gated, not claimed to be live-verified.

## Actual measured checks

| Check | Observed result |
| --- | --- |
| Python interpreter | Python 3.14.0 |
| Node interpreter | v22.19.0 |
| npm install | Failed: network EACCES; required modules were not installed |
| Offline npm install | Failed: required packages missing from available cache |
| pip install -r requirements.txt | Failed: DNS/socket restrictions; pandas/requests/pytest/dotenv unavailable |
| python -m unittest discover -s tests -q | 44 tests discovered: 40 passed, 4 skipped (pandas-dependent statistical cases) |
| python -m compileall -q scripts tests | Passed |
| Default strict rebuild | Writes honest unavailable exports, reports all missing verified inputs; exit 2 |
| Partial rebuild | Writes same explicit unavailable states; exit 0 |
| Live mode without configuration | Reports missing optional BigQuery package, absent Explorer JWT and absent CoinGecko key; exit 2; no authenticated requests attempted |
| Empty-export consistency | Pipeline test verified header-only CSVs versus empty dashboard, unresolved verdict and output hashes |
| BigQuery mock jobs | Metadata-only discovery, absent mapping, dry-run-only behavior, disabled paid execution, unknown/over-budget estimates and cumulative full-cap reservations tested |
| Explorer mocked pages | Auth headers, bounds/cursor preservation, inclusive midnight adjustment, duplicate identity, repeated cursors, invalid schema and partial-page budgets tested |
| HTTP mocked responses | 429 Retry-After, request spacing, retry exhaustion and no retry on 401 tested |
| CoinGecko mocked responses | Plan-specific auth, date batching and invalid price responses tested |
| Pure TypeScript parsing | 10 TS/TSX files parsed with recovered cached TypeScript 5.9.3; no parse diagnostics. This is NOT a full typecheck |
| npm run typecheck | Failed: required React, router, chart and test modules/types unavailable; not passed |
| npm run build | Attempted; blocked at TypeScript stage. No production dist build established |
| npm test | Failed to start: vitest not installed |
| python -m pytest | Failed to start: pytest not installed |
| Browser QA, screenshots, responsive measurements | Not performed: application dependencies/build unavailable |
| Browser console errors/navigation | Not verified; no clean-console claim |
| Source API authentication / live schemas / paid query | Not performed; zero successful authenticated requests and zero paid queries |

Tests use synthetic records exclusively in tests and temporary directories. No synthetic data is committed under production raw inputs or public data. Committed public chart series and correlations are empty. No investment conclusion is inferred. Secrets are not included in public exports or frontend configuration.

## Integrity and historical artifacts

Original access-probe JSON files and their original manifest are preserved. The old manifest's hashes for README.md, VALIDATION.md, .env.example and .gitignore now describe historical versions and are expected not to match the extended current documents. Do not rerun its old all-files assertion as a current-release check. The original VALIDATION.md hash can be checked against initial-validation.md; the two access-probe hashes still match their unchanged files. Current generated output hashes are recorded in data/manifest.json. Hash integrity is not proof of upstream authenticity.

## Readiness

* Research rebuild missing-input demonstration: verified locally, including correct nonzero strict status.
* Frontend local demonstration: source implemented, startup/build/browser validation pending successful dependency installation.
* Public deployment: configuration supplied, not release-verified; no deployment performed.
* Evidence-backed hackathon submission: not ready. Requires authenticated source validation, adequate historical overlap, schema/action-grain confirmation, redistribution-approved committed exports, complete judge replay, all tests/build/browser checks, public repository and human demo post, reciprocal Sentinel README disclosure and explicit submission authorization.

No credentials need to be supplied in chat. Obtain them through the official links documented in docs/data-sources.md and configure ignored local .env. Neither adapter implementation nor synthetic test success is described as live verification.

# Network acquisition attempt — November 12, 2026, 20:49 UTC

Objective: validate three complete native-chain days, then consider a 30-day
window, using project `falcora-test` and the requested public dataset. The user's
successful Cloud Console queries are recorded as user-reported access; they do
not establish local Application Default Credentials.

## Configuration and authentication observations

* Local `.env` already configures `BIGQUERY_PROJECT_ID=falcora-test`,
  `GOOGLE_CLOUD_PROJECT=falcora-test`, US location, 100,000,000 bytes/query and
  1,000,000,000 bytes cumulative. Its contents were not printed indiscriminately
  or modified. Paid execution remains disabled and column mapping is empty.
* No `GOOGLE_APPLICATION_CREDENTIALS` path is configured. No ADC file exists at
  the standard Windows `%APPDATA%/gcloud/application_default_credentials.json`
  location. No alternate `CLOUDSDK_CONFIG` location was configured.
* Neither `gcloud` nor `bq` is on PATH. A subsequent explicit standard-install
  check found both command files under
  `C:\Users\PC\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin`.
* Running that installed `gcloud.cmd auth application-default print-access-token
  --quiet` returned exit 1: **“Your default credentials were not found.”**
  Stdout was captured privately and never printed; no token was obtained.
* The CLI also warned it could not create its log file under
  `C:\Users\PC\AppData\Roaming\gcloud\logs` with `PermissionError: [Errno 13]
  Permission denied`. No alternate authentication/config directory or account
  was used to work around this restriction.
* Python `google.auth`, `google.cloud.bigquery`, pandas and pytest are unavailable.
  A bounded package install into the workspace verification directory failed:
  `Could not find a version that satisfies the requirement pandas<4,>=2.2`
  and `No matching distribution found for pandas<4,>=2.2`.

## Live evidence and cost accounting

| Item | Actual outcome |
| --- | --- |
| Live metadata/schema requests | 0; blocked before authenticated BigQuery access |
| Inspected live transactions/receipt_actions schemas | None |
| Latest complete source dates | Unknown; not inferred from a cutoff or Console access |
| Dry-run jobs submitted | 0 |
| Executed query jobs | 0 |
| Query job IDs | None |
| Actual bytes processed from job statistics | Unavailable; no query result/job statistics returned |
| Billed queries submitted by this attempt | 0 |
| Three-day extraction | Not attempted; authentication prerequisite failed |
| Thirty-day expansion | Not attempted; no three-day validation or dry-run estimates |
| Billing/permissions validation | Not reached; no claim of a billing or dataset-permission error |

No source schema or source-date result was invented. Existing SQL remains
schema-gated templates; no guessed source-column mapping or latest-date query was
executed. No CSV/JSON dataset, source manifest or chart was populated with
unverified figures. Existing production datasets were preserved.

## Changes and checks

The provider now rejects configured limits above the authorized hard ceilings.
It logs rejected dry-run estimates and refuses negative, boolean or unknown byte
estimates. Over-budget estimates include the estimated bytes and relevant limits
in the error, and never authorize execution. Synthetic tests cover these cases.
The empty-replay integration test now writes exclusively to a temporary directory
instead of rewriting the real dashboard during tests. `.env.example` names the
supplied project; no real credential was added.

| Check | Observed result |
| --- | --- |
| Python unittest suite | 47 cases: 43 passed, 4 pandas-dependent cases skipped |
| Python compilation | Passed |
| Frontend TypeScript typecheck | Passed, exit 0 |
| Production build | Failed, exit 1: esbuild `Cannot read directory "../../..": Access is denied`, then could not resolve the absolute `vite.config.ts` path |
| Vitest | Failed at config startup with the same esbuild filesystem-access error; tests did not execute |
| pytest | Failed to start: `No module named pytest` |

Machine-readable observations and exact ADC error:
`validation-evidence/network-acquisition.json`. Full local command logs are in
the ignored `.verification/network-*.log` files. No Sentinel files were accessed;
no deployment or push occurred.

## Required local prerequisites to resume

Run the following in the user's normal PowerShell, where browser sign-in and
the Cloud SDK configuration directory are accessible. Google documents this
ADC setup separately from Cloud Console sign-in:
https://cloud.google.com/docs/authentication/provide-credentials-adc

```powershell
$nearPulseGcloud = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
& $nearPulseGcloud auth application-default login
& $nearPulseGcloud auth application-default set-quota-project falcora-test
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
python -m pip install -r requirements-bigquery.txt
python scripts/rebuild.py --mode discover
```

Do not paste tokens or credential JSON into chat. Once local ADC refresh and
metadata discovery succeed, determine actual source schemas/partitions and
latest complete historical dates before rendering parameterized SQL. Dry-run
every validation/extraction query within the hard limits; preserve one cumulative
budget across date discovery, three-day validation and any 30-day expansion.

# Three-day schema-driven extraction attempt — November 12, 2026

The user successfully ran local discovery outside this sandbox. The generated
`data/schema.json` was read and retained as
`validation-evidence/network-discovery-schema.json` with SHA-256
`619275be52bf8fa446645134ce1562957d1314dc3047dec804b3ba680e6a731c`.

## Observed schema and partition configuration

Both `transactions` and `receipt_actions` use DAY time partitioning on
`block_date` (DATE). Verified transaction columns include `transaction_hash`
(STRING), `signer_account_id` (STRING), and `block_timestamp_utc` (TIMESTAMP).
Verified action columns include `receipt_id` (STRING),
`index_in_action_receipt` (INTEGER), `action_kind` (STRING),
`is_delegate_action` (BOOLEAN), and `block_timestamp_utc` (TIMESTAMP).
The action-kind description explicitly includes `FUNCTION_CALL`.

Discovery saved partition **configuration**, not dated partition records or
historical counts. No earlier dated partition export exists in this checkout.
Consequently November 9, 10 and 11 availability cannot be confirmed from the
saved file alone. No earlier March cutoff or November coverage was assumed.

## Current local access observation

ADC now exists in the standard Windows location, and `google.auth`,
`google.cloud.bigquery`, pandas and pytest are installed. These are improvements
over the preceding report; the earlier missing-file/package findings are historical.

A fresh `python scripts/rebuild.py --mode discover` attempt failed while
refreshing ADC with `google.auth.exceptions.TransportError` at
`oauth2.googleapis.com:443`, endpoint `/token`, caused by **WinError 10013**:
“An attempt was made to access a socket in a way forbidden by its access
permissions.” No token was printed. This is a sandbox transport restriction,
not evidence that the credentials are invalid or that billing/dataset permission
has been denied. The saved successful discovery file was preserved.

The prepared extractor was also exercised in dry-run mode:

```powershell
python scripts/extract_network.py --start 2026-11-09 --end 2026-11-12
```

It failed at the same credential-refresh HTTPS step before live schema retrieval
or query submission. Exact captured error and requested bounds are in
`validation-evidence/network-three-day.json`; status is `failed`, metrics are
null, jobs are empty, and reserved query bytes are zero.

## Extraction implementation and safety

`scripts/extract_network.py` revalidates schemas live and obtains bounded
partition rows before data extraction. The partition metadata SQL is versioned
in `sql/network_partitions.sql`. INFORMATION_SCHEMA has no `block_date` field,
so that metadata query is bounded by table names and formatted partition IDs.
Each actual data query in `sql/verified_transactions.sql`,
`verified_signers.sql` and `verified_function_calls.sql` directly filters
`block_date >= @start AND block_date < @end` with DATE parameters. No joins
or assumed source columns are used.

Transaction counting uses source table rows across all statuses, checked against
partition row counts. Distinct signer accounts are not people. Function calls
use FUNCTION_CALL receipt-action row grain, including delegated rows represented
by the source; they are not unique receipts or proven successful executions.
The initial row-grain method does not assert undocumented uniqueness of
receipt/action composite keys. Current dashboard metric descriptions disclose it.

Every metadata/data query goes through dry-run estimation and the existing hard
100,000,000 bytes/query and 1,000,000,000 cumulative bounds. Multi-day queries
over the per-query limit are reduced to separate single-day dry-runs. A
single-day over-budget query still stops execution. Every planned data query
must pass before any data-query execution. One provider instance reserves the
full authorized cap for every execution, including partition metadata; the
planned cumulative budget is checked before data execution. Limits are not raised.

Publication requires both tables to have positive partitions for every requested
day, all 24 UTC hours represented, no null required signer/action kinds,
signers no greater than transactions, and transaction/action row totals matching
the earlier metadata snapshot. Those checks are conservative observations of
coverage, not proof the upstream index omitted no blocks. Mismatches fail for
review rather than being silently accepted. A staged offline rebuild must pass
before production datasets are copied; no synthetic fixtures enter public data.

## Results and checks

| Item | Actual result |
| --- | --- |
| November 9–11 usable partitions | Unconfirmed: dated metadata request could not authenticate over HTTPS |
| Retrieved transaction/signers/function-call measurements | None; unknown, not zero |
| Query dry-runs submitted | 0 |
| Executed query jobs / job IDs | 0 / none |
| Actual processing statistics | Unavailable; no query job completed |
| Three-day verified CSV/JSON publication | Not performed |
| Dashboard verified network observations | 0; dashboard remains unavailable |
| Python pytest | 59 passed, no skipped tests |
| Python compilation | Passed |
| Frontend TypeScript typecheck | Passed |
| Production build | Failed: esbuild cannot read `../../..` (Access is denied), then cannot resolve absolute `vite.config.ts` |
| Vitest | Failed at startup with the same config-loader filesystem error; no frontend tests executed |

New tests include reduced-range query planning, dry-run-only behavior, missing
partitions, aggregate/metadata mismatch, missing-hour and null-kind rejection,
cumulative reservations, and a staged export integration using synthetic data
strictly inside temporary directories. A failed staged rebuild is tested to
preserve the previous production dataset.

## Exact PowerShell command outside the sandbox

Run in the same normal PowerShell environment where discovery succeeded:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-09 --end 2026-11-12 --execute
```

The environment flags explicitly opt into bounded paid execution and public
aggregate export; the script still refuses over-budget queries. November 12 is
the exclusive endpoint, so only November 9–11 are requested. Success prints the
actual three rows, writes source/CSV/JSON manifests and records
`verified_and_exported` in `validation-evidence/network-three-day.json`. Failure
retains the precise reason and any completed job IDs/bytes in that report.
Do not report success based merely on the command being prepared. No Sentinel
files, deployment or push operations were touched.

# Narrow partition-metadata permission fallback — November 12, 2026

The user supplied a failed local extraction report containing HTTP 403 Access
Denied on exactly
`bigquery-public-data:crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS`.
The preserved `validation-evidence/network-three-day.json` records that failed
request; it does not contain successful network observations. This fix does not
claim a new authenticated acquisition.

## Root cause and implementation

`acquire()` in `scripts/extract_network.py` calls `provider.run()` with
`sql/network_partitions.sql` before planning the data queries. Previously any
failure there terminated the extraction. The lookup is now optional only when:

* the raised exception is Google's typed `google.api_core.exceptions.Forbidden`;
* its Access Denied message identifies this exact dataset's
  `INFORMATION_SCHEMA.PARTITIONS` view as the denied **table**; and
* it arises inside the protected metadata-lookup call, not schema discovery or
  another data-query call.

The exact resource comparison accepts Google's project/dataset colon or dot
notation. An untyped string containing “403”, a different project/view/table,
a dataset-level denial, Unauthorized, NotFound, BadRequest, transport error,
or query-cost rejection does not enable the fallback. All remain fatal. No
permissions, account, endpoint, dataset or source are changed.

The BigQuery provider now preserves typed API exceptions from job-result errors
instead of hiding them inside a generic SourceError. It records failed dry-run,
submission and result stages, error type/message and available job details before
rethrowing. Successful executed jobs must have a nonempty job ID and a known,
nonnegative integer actual processing-byte count within the authorized cap.
Unknown actual bytes or missing job IDs reject results rather than allowing
publication.

## Bounded-query verification and limitations

Live schema validation still verifies the already discovered source columns and
daily `block_date` DATE partitioning. In fallback mode, the existing transaction,
signer and receipt-action queries establish observed availability directly.
Every data query retains DATE parameters and mandatory
`block_date >= @start AND block_date < @end` predicates. No joins, unrestricted
metadata scans, arbitrary dates or alternate source are introduced.

All data plans must pass dry-runs before execution. Existing per-query
100,000,000-byte and cumulative 1,000,000,000-byte ceilings, rejection of unknown
estimates, full-cap reservations and optional reduction to single-day queries
are unchanged. A reservation made before a failed metadata job is retained.
A successfully parsed/dry-run query alone never establishes partition or data
availability.

Only successful executed results can establish availability. Each requested day
must appear in all metric result sets, both source tables must have positive row
counts, both must cover all 24 UTC hours, required signer/action fields cannot
be null, and signer/function-call counts must satisfy their existing bounds.
Missing, duplicated, out-of-range, empty or invalid daily results remain fatal.

When metadata is accessible, the original partition row-count comparison remains
mandatory. An empty successful metadata response is not treated as a permission
fallback. When the specific metadata 403 occurs, provenance records:

* `partition_verification.mode = bounded_data_queries`;
* `partition_verification.status = pending` until executed metrics validate;
* the exact metadata denial in `partition_metadata_error`;
* `partitions = null` and `partitions_observed_at = null`;
* null `transactions_match_partition_rows` and
  `receipt_actions_match_partition_rows` checks, never fabricated `true` values;
* the observed data-verification time after actual results pass validation.

This fallback cannot perform an independent metadata row-count comparison.
Daily positive counts and 24-hour coverage establish observed bounded-window
coverage, not proof that the upstream index omitted no blocks. Schema discovery
or authentication failures do not authorize use of stale metadata to fetch data.
Staged export validation and preservation of production data on validation failure
remain in place. Dry-run-only fallback remains unverified and publishes nothing.

## Actual checks

| Check | Result |
| --- | --- |
| Python pytest | 74 passed and 6 subtests passed; no skipped tests |
| Python compilation | Passed |
| TypeScript typecheck | Passed |
| Production build | Failed at Vite/esbuild config loading: `Cannot read directory "../../..": Access is denied`, then could not resolve absolute `vite.config.ts` |
| Vitest | Same config-loader filesystem error; frontend tests did not execute |
| Live BigQuery acquisition during this fix | Not attempted; no new metrics or completed live jobs claimed |
| Production dashboard network rows | 0; existing unavailable state preserved |

Tests cover the supplied full error-message format, successful bounded fallback,
honest staged CSV/JSON provenance, no availability inference from dry-runs,
missing/empty dates, unrelated errors remaining fatal, unknown estimates,
single-day over-budget rejection, cumulative budget/reservation preservation,
missing executed job IDs and unknown actual processing bytes. Synthetic metric
fixtures remain in tests and temporary directories only.

Machine-readable check results are in
`validation-evidence/metadata-fallback-checks.json`; command logs are in ignored
`.verification/metadata-fallback-*.log`. The previous live failure report was not
overwritten. No Sentinel files were accessed or modified.

## Exact local PowerShell command

Run outside the restricted Codex sandbox, using the ADC environment where local
discovery succeeded. Both flags explicitly opt into bounded execution and export;
they do not bypass the byte limits:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-09 --end 2026-11-12 --execute
```

The end date is exclusive. No new credentials or role changes are required by
the fallback itself. Any subsequent data-table permission, authentication, quota,
cost or coverage failure stops extraction and is recorded precisely. Successful
actual results, job IDs and bytes must be reviewed before reporting that the
Network Activity dashboard has been populated.

# Configured query-region correction — November 13, 2026

The user reports an authenticated local Python BigQuery dry-run succeeded with
`location="us-east1"` for project `falcora-test`, querying COUNT(*) from
`bigquery-public-data.crypto_near_mainnet_us.transactions` with a `block_date`
filter for November 11, 2026. Reported status: SUCCESS. Reported estimated bytes:
**7,130,376**. The corresponding query using `location="US"` failed with 403.
This establishes the user-validated location mismatch; it is not a fresh query
executed by Codex. No successful job ID, executed metric rows or actual
processing-byte statistics were supplied for this dry-run. The estimate applies
only to that query, not to signer/action or three-day queries.

## Changes

* Updated the existing ignored local `.env` entry to
  `BIGQUERY_LOCATION=us-east1`, preserving all other settings/credentials without
  printing the file. Updated `.env.example` and the adapter's unset-value default
  to the same region. The public dataset reference is unchanged.
* The provider stores `self.location` and passes it explicitly to both dry-run
  and execution `client.query()` calls. This covers the partition metadata view,
  bounded availability checks, network metrics and generic rebuild queries.
  No active job submission defaults to the hardcoded `US` multi-region.
* Live schema discovery uses the same region-configured BigQuery client. The
  installed official SDK's `get_table()` signature has no `location` parameter;
  these HTTP metadata lookups are not query jobs. No invalid keyword or extra
  schema query was introduced.
* Job log records, three-day extraction reports and network source manifests now
  include the configured location. Actual job IDs and processing-byte validation
  remain mandatory for successful query results.
* No changes were made to partition predicates, metric definitions, DATE
  parameters, dry-run requirements, maximum bytes billed, conservative cumulative
  reservations, 100,000,000-byte/query or 1,000,000,000-byte cumulative ceilings,
  schema checks, staged publication, or the narrowly scoped metadata-403 fallback.

## Checks and evidence boundary

The Python suite passed 78 tests and 10 subtests. Tests verify the region used to
construct the client; schema discovery using that client; explicit location on
every dry-run/execution submission for partition metadata, transactions, signers
and function calls; explicit configuration overriding an injected client default;
unset configuration defaulting to `us-east1`; and propagation into staged report
and source-manifest provenance. Python compilation passed. Frontend TypeScript
typecheck passed. Existing cost/error/fallback tests remain in the suite.

The old `Location: US` string in a synthetic permission-error fixture and earlier
reports is deliberately retained as historical regression evidence; it does not
configure a job. Production data and source metric exports were not modified.
No authenticated live job or extraction was run during this region-configuration
fix, and the dashboard is not newly claimed to contain verified network metrics.

## Exact local extraction command

Run in the normal PowerShell environment where the authenticated regional dry-run
succeeded. November 12 is exclusive, requesting November 9–11 only:

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

The regional dry-run does not pre-authorize any estimate above the caps. Each
query must still pass its own estimate and cumulative reservation checks. Review
`validation-evidence/network-three-day.json` for actual results, job IDs, region,
cost statistics, coverage checks or errors after running locally. No Sentinel
files were accessed or modified; no deployment, push or cost-limit increase was
performed.

# Exact-query cost optimization — November 13, 2026

## Identified failure from the saved local report

Read `validation-evidence/network-three-day.json` and the saved actual schema.
The exact 124,777,675-byte rejection belongs to
`sql/verified_function_calls.sql`, metric **contract function-call actions**,
`start=2026-11-09`, `end=2026-11-10` (exclusive), in `us-east1`.
It was a **single-day** dry-run; execution was correctly rejected.
The original SQL was:

```sql
SELECT block_date AS date,
       COUNTIF(action_kind = @action) AS contracts,
       COUNT(*) AS receipt_action_rows,
       COUNTIF(action_kind IS NULL) AS missing_action_kinds,
       COUNT(DISTINCT EXTRACT(HOUR FROM block_timestamp_utc)) AS observed_hours
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date >= @start AND block_date < @end
GROUP BY block_date
ORDER BY block_date
```

Parameters: DATE start/end above and STRING action=`FUNCTION_CALL`. No joins
or LIMIT were present. The partition predicate was already correct.

The same report records:

| Query | UTC bounds, end exclusive | Estimated bytes | Result |
| --- | --- | ---: | --- |
| Transaction activity + validation | Nov 9–12 | 102,096,417 | Rejected, reduced to days |
| Transaction activity + validation | Nov 9–10 | 30,890,911 | Dry-run passed |
| Transaction activity + validation | Nov 10–11 | 39,072,245 | Dry-run passed |
| Transaction activity + validation | Nov 11–12 | 32,133,261 | Dry-run passed |
| Distinct signing accounts | Nov 9–12 | 80,039,585 | Dry-run passed |
| Function calls + timestamp coverage | Nov 9–12 | 378,608,723 | Rejected, reduced to days |
| Function calls + timestamp coverage | Nov 9–10 | 124,777,675 | Rejected; entire extraction stopped |

Thus splitting helped transaction activity but was insufficient for the combined
action/timestamp query. These are saved local observations, not new requests
made by Codex. The completed job in that report is only the partition metadata
query, job `8883dfff-76bd-4f1c-a9c0-e6ad37e7f417`, reporting 10,485,760 actual
processed bytes. The original run reserved 100,000,000 bytes for it; the
remaining conservative budget was 900,000,000. No network metric query had
executed before the rejected dry-run. The report is preserved unchanged, and
`validation-evidence/network-cost-diagnosis.json` records its SHA-256 and exact
failed SQL/parameters for diagnosis.

## Schema and accuracy-preserving strategy

The saved source schema confirms both tables use DAY partitioning on
`block_date` DATE. Relevant fields are scalar `signer_account_id` STRING,
`action_kind` STRING and `block_timestamp_utc` TIMESTAMP. No finer partitioning
or clustering guarantee is established by this saved metadata.

The optimized strategy changes the selected columns per query, not the metric:

1. `verified_transactions.sql` now computes exact `COUNT(DISTINCT
   signer_account_id)` alongside transaction counts, missing-signer checks and
   timestamp coverage. This already scanned the signer and timestamp columns;
   adding the exact distinct aggregate avoids the separate redundant signer
   scan. Daily account sets are not split or summed.
2. `verified_function_calls.sql` now reads only `block_date` and `action_kind`
   for exact function-call counts, total receipt-action rows and null-kind checks.
3. `verified_receipt_coverage.sql` separately reads only `block_date` and
   `block_timestamp_utc` for receipt-action row counts and all-24-hour coverage.

The latter two results must have identical positive row totals for every day
before they are combined. Missing/duplicate dates, row-count mutation, missing
hours, null fields and the original metric bounds still reject publication.
Comparison with earlier partition metadata remains required when accessible.
This does not provide an atomic cross-job snapshot or prove no upstream blocks
were omitted; the existing historical source limitations remain disclosed.

Every query retains explicit `block_date` bounds. No joins, row sampling,
approximate distinct counts, LIMIT-based cost assumptions or unpruned hourly
scans were introduced. If an optimized column-specific single-day query still
exceeds 100 MB, the extractor stops; further exact reduction cannot be assumed
from daily partitioning alone. Operator investigation of source indexing/layout
would be necessary, without silently changing the metric or its source.

## Safeguards and provenance

Location remains `us-east1`; hard per-query and cumulative limits remain
100,000,000 and 1,000,000,000 bytes. All planned data queries must pass dry-runs
before any metric-query execution. Multi-day queries may reduce to one-day
queries; a one-day rejection remains fatal. Unknown estimates, missing job IDs
and invalid/unknown actual processing bytes are still rejected.

The three optimized groups require at most nine daily data jobs for three days.
Including metadata, ten full-cap reservations exactly fit the existing 1 GB
ceiling. A one-day request requires at most four such reservations. No budget
is reset/refunded to force a run through, and the provider still dry-runs each
job again immediately before executing it. Staged rebuild and failure preservation
remain unchanged.

Dry-run records now identify the metric, SQL file and exact attempted bounds;
executed records retain typed parameters, SQL, location, actual bytes and job
IDs. Reports/manifests include the strategy description and separately observed
receipt coverage results. The standalone legacy signer SQL is retained, but
the initial extractor derives signers from the combined exact transaction query.

## Offline validation and evidence limits

Python pytest: **82 passed, 11 subtests passed**, no skipped tests. Python
compilation and TypeScript typecheck passed. Tests cover oversized multi-day
queries, successful daily fallback within cumulative reservations, rejection of
an optimized single-day contract query above the cap, exact column selection,
unchanged distinct-signer aggregation, matching/missing/mutated coverage results,
metadata fallback and temporary-directory export consistency.

No new authenticated dry-run or metric job was executed during this optimization.
The new column-specific estimates have not been measured here; passing them
must not be assumed or inferred numerically from old estimates. No new metric
rows were retrieved or promoted into the production dashboard.

## Smallest supported historical window

Run this one-complete-UTC-day request locally. It is guarded by real dry-runs;
it is not claimed to be an already cost-verified success:

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

No Sentinel files were accessed or changed. No deployment or push occurred.

# Evidence-backed baseline and incremental release preparation — November 13, 2026

## Preserved and independently recomputed local evidence

Both `data/raw/network.manifest.json` and `data/raw/intents.manifest.json`
passed source-hash, attribution, bounds and authenticated-provenance validation.
All 22 original Explorer response files passed their recorded SHA-256 checks.
Fresh aggregation of the normalized swap records reproduced the exact count and
Decimal USD amount below. No new source requests were made during this work.

| Measurement, November 9 UTC | Verified observation |
| --- | ---: |
| Native signed transaction table rows | 895,302 |
| Distinct signing accounts | 77,752 |
| FUNCTION_CALL receipt-action rows | 1,649,268 |
| Successful 1Click swaps | 20,243 |
| Exact 1Click input USD | 43,331,710.006694590507 |

Explorer audit: 22 pages, 20,243 received/unique swap records, zero duplicate
records, terminal empty page observed and pagination complete. Its grouping is
creation UTC day with SUCCESS status at retrieval, not completion-day activity.
The native source has four completed query records, all with actual bytes and
job IDs. Their recorded actual processing bytes total 201,035,098; the original
run reserved 400,000,000 bytes. No additional paid query was run by this task.

## Incremental extraction changes

Both CLIs now merge through `scripts/history.py` instead of replacing source
history. Known native values cannot change silently. Missing contract counts
remain null, cannot erase earlier counts, and may be filled by later verified
backfills. Swaps deduplicate by deposit address/memo; changed identities, changed
records, missing old swaps or new records revising an already complete old
period fail for analyst review. Identical overlap is idempotent.

Coverage intervals remain explicit, including gaps. Original source bytes and
original manifests are retained as immutable hash-named snapshots under
`data/raw/history/`. Segment provenance, original API page hashes and query logs
remain attached to merged history. A publication lock prevents concurrent
publishers; staging and rollback protect current datasets on ordinary failures.
Stale locks after a process crash require review, not automatic bypass.

Replay can combine sources with different windows. It preserves observed points
and emits missing fields/days as null, not zero. Strict source replay reports
incomplete requested coverage. The merge publisher allows an explicitly partial
union for dashboard visualization only after validating all retained inputs and
checking no source observations were lost. This does not certify a complete
common research window or relax the statistical threshold.

Network extraction supports `--skip-contracts`, retaining exact daily transaction
and distinct signer aggregation while omitting receipt queries and receipt schema
requirements. Omitted calls are explicit nulls. This option preserves the
already acquired November 9 call count. Per-metric dashboard observation dates
prevent that older call observation from borrowing newer transaction freshness.

History ranges are limited to 1–14 elapsed UTC days. A rejected multi-day data
plan tries two-day windows and then individual dates. All data plans must pass
dry-runs before metric execution; every table has a block_date predicate.
Unknown/oversized daily estimates and over-budget cumulative plans remain fatal.
The region remains us-east1. Cost ceilings remain 100,000,000/query and
1,000,000,000 cumulative within one CLI run; full-cap reservations are retained.
The counter is not a lifetime account budget, and separate invocations can incur
additional charges. No loop or reset is used to force an over-budget plan through.

## Safe acquisition strategy and exact commands

Start with six missing dates, November 3–8, preserving the existing November 9
to obtain seven total days if acquisition succeeds. Prioritize transactions and
signers. In the worst permitted daily plan, six data jobs plus metadata reserve
700,000,000 bytes. This is a maximum authorization bound, not an observed cost.

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
$env:BIGQUERY_PROJECT_ID = 'falcora-test'
$env:BIGQUERY_LOCATION = 'us-east1'
$env:BIGQUERY_MAX_BYTES_BILLED = '100000000'
$env:BIGQUERY_TOTAL_BYTES_LIMIT = '1000000000'
$env:BIGQUERY_ALLOW_PAID_QUERIES = 'true'
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_network.py --start 2026-11-03 --end 2026-11-09 --skip-contracts --execute
python scripts/extract_intents.py --start 2026-11-03 --end 2026-11-09 --page-size 1000 --max-pages 500
```

For a fourteen-day alternative ending November 9, replace both date arguments
with `--start 2026-10-27 --end 2026-11-09`. Thirteen new dates fit seven two-day
or shorter data jobs plus metadata (800 MB full-cap reservation) only if those
two-day estimates pass. Up to two extra daily splits fit the 1 GB ceiling; more
cause preflight rejection. Do not claim this longer plan is cost-verified, or
rerun smaller fresh-budget loops to evade a rejected cumulative plan. The
seven-day transaction-priority plan is safer. Contracts can be requested by
omitting --skip-contracts, but their additional scans must fit the same limits.

Explorer's 500-page bound is not an assurance of exhaustion. It fails explicitly
if insufficient. One process per partner must maintain five seconds between all
requests and retries. Additional dates were not fetched here; source commands
are prepared for normal local PowerShell outside the restricted sandbox.

## Actual replay and statistical readiness

Executed without upstream calls:

```powershell
python scripts/rebuild.py --mode replay --sources network,intents --start 2026-11-09 --end 2026-11-10
```

Result: successful verified-source replay for the two requested sources.
`research_coverage.native_and_intents` is November 9 to November 9, one level
observation. Price-inclusive coverage is empty. There are zero paired daily
changes and zero computable correlations. Verdict: **Insufficient data**.
The displayed day, CSVs and exact decimal volume match the source exports.
Research defaults in .env/.env.example now target this verified baseline;
credentials and cost settings were preserved unchanged. Strict full-source
default replay still exits nonzero because price is missing.

Seven to fourteen days can improve descriptive history and seven-day averages,
but are insufficient for the 30 paired-change threshold. Contiguous same-day
comparisons need at least 31 levels; 7-/30-day lags on equally bounded series
need at least 38/61. Price and contract overlap remain necessary for the current
verdict; optional omissions never become supportive evidence.

## Release verification

* Python suite: 108 passed and 17 subtests passed, with no skipped tests.
* Frontend Vitest: 13 passed. TypeScript typecheck passed.
* Python compilation and production build passed.
* The earlier config-loader filesystem failure is resolved by Vite/Vitest's
  native config loader on Node 22.19.0; package scripts require Node 22.18+.
  No filesystem permission or security setting was changed. Chart/framework
  vendor chunks are split; the latest build has no oversized-chunk warning.
* A task-owned local dev preview served dashboard JSON with HTTP 200 and the
  Insufficient Data verdict. The browser-access host was unavailable, so no
  desktop/mobile screenshots, visual review or clean-browser-console claim is
  made. The task-owned preview is stopped at completion.
* Tests cover immutable overlap, revision rejection, missing observations,
  optional contracts, archive snapshots, concurrent publication rejection,
  seven-day daily planning, fourteen-day two-day planning, fourteen-day daily
  cumulative rejection, raw API hash validation and source preservation.

The local source archive contains verified replay inputs and the static archive
contains the production build. Both exclude .env, ADC, node_modules and private
credentials. Raw inputs remain ignored by Git until deliberately reviewed and
included. This directory is not currently a Git repository; no public repository
URL was verified. See `validation-evidence/submission-readiness.json` for the
machine-readable facts and local archive checksums after packaging.

## Submission readiness assessed separately

**Ready locally:** actual one-day source evidence, both dashboard datasets,
credential-free replay, pipeline/test/build infrastructure, incremental merge
and safe acquisition commands, MIT license, methodology/limitations and NEAR
Pulse's independent Sentinel disclosure. Deployment artifacts can be reviewed.

**Not complete:** quantitative thesis validation (history and price absent),
live validation of additional-date plans, browser/responsive/console inspection,
public source repository with reviewed raw exports and redistribution rights,
human demo post/video, verification of Sentinel's reciprocal disclosure, human
entry details/contact consent and explicit submission approval. The native
one-day action grain and creation-time Explorer scope remain limitations.

Official hackathon instructions were re-read November 13. Deadline remains
November 14, 2026 at 23:59 UTC. Publishing/pushing, the human demo post and the
submission are separate authorized actions, none performed here. No Sentinel
files were accessed, no credentials changed, and no deployment or push occurred.

# Explorer credential and bounded ingestion — November 13, 2026

## Credential handling and actual authenticated request result

The project `.env` contains a nonempty `INTENTS_EXPLORER_JWT`. Runtime loading
was checked by comparing the in-memory value with `dotenv_values('.env')`;
the values match. Only presence/equality booleans were printed. The credential,
its length, decoded claims and authorization header were not displayed or saved.
No source credentials were copied into Vite or dashboard configuration.

Reviewed the official Explorer introduction and transaction contract:

* https://docs.agentsonintents.com/integration/distribution-channels/1click-api/explorer/introduction
* https://docs.agentsonintents.com/api-reference/get-transactions

The actual probe used the documented host/endpoint
`https://explorer.near-intents.org/api/v0/transactions`, Bearer authentication,
SUCCESS filter and requested creation-time bounds
`2026-11-09T12:00:00Z` to `2026-11-09T12:01:00Z`. The adapter requests its
exclusive lower API bound one millisecond earlier, then validates returned rows
against the intended interval. Probe budgets were 25 rows/page and 3 pages.

An initial no-retry diagnostic and the full retry-enabled probe both failed
before an HTTP response with requests ConnectionError / **WinError 10013**:
socket access forbidden by the execution environment. The full probe recorded
four attempts at 10:43:45.155613, 10:43:50.156319, 10:43:55.156613 and
10:44:00.157560 UTC on November 13, each more than five seconds apart. No HTTP
status was obtained. This is not an observed 401, 403, bad credential or API
downtime, and no network-policy workaround was used.

Evidence is saved in `validation-evidence/intents-authentication.json` and
`validation-evidence/intents-acquisition.json`. The latter is the canonical
retry-enabled report. Requests contain nonsecret query parameters only; neither
headers nor the token are in the artifacts.

| Requested report item | Actual observed result |
| --- | --- |
| Credential loaded from project .env | Yes; runtime equality checked without exposing value |
| Authenticated API access accepted | Unverified; no HTTP response |
| Actual response schema / SUCCESS status / USD fields | Not observed; validators follow the documented contract, tested with synthetic fixtures |
| Requested probe coverage | Nov 9, 2026, 12:00–12:01 UTC |
| Observed creation/completion coverage | Unknown; no records received |
| Successful/completed swaps | Unknown, not zero; completion timestamps not established |
| Input USD volume | Unknown, not zero |
| Pagination | Incomplete; zero pages received, no terminal empty page |
| New raw Explorer pages / verified source export | None; there was no response to save |
| Intents dashboard observations published | None |

## Adapter and replay integration improvements

The existing Explorer provider is used by `scripts/extract_intents.py`, which
adds a small probe mode and a bounded 1–3-day historical export mode. It loads
`.env` and never accepts the JWT as a command argument. It uses the same client
and five-second limiter across retries/pages, honors bounded Retry-After, and
disables redirects to avoid unpaced extra requests or credential forwarding.

Pagination preserves status/time bounds on every page, sends the last observed
deposit address and memo as the next cursor, rejects cursor loops, and requires
a terminal empty page. Audit fields distinguish received rows, duplicate rows,
unique identities and complete pagination. Page-budget exhaustion never becomes
a complete period. Identity uses the documented address/memo pair; conflicts
fail. It still needs confirmation against actual authenticated records before
claiming live semantic verification.

Every swap requires SUCCESS status, address/memo fields, origin asset identity,
timezone-aware creation timestamp in bounds, and finite nonnegative amountInUsd.
If present, Unix creation time must agree with ISO creation time. Successful
status is measured at retrieval; grouping remains **creation day**, not completion
day, and does not cover total Intents economic activity.

Numeric JSON amount values are parsed as Decimal, and USD additions retain exact
precision beyond the default decimal context. CSV sums stay decimal strings.
Validated original successful response bodies are saved byte-for-byte with
SHA-256 and secret-free request provenance when available. Replay validates
those page hashes. Failed/incomplete raw pages can be retained for diagnosis,
but are not published as complete metrics. Writes refuse an echoed token value.

The export command stages a complete offline replay before publishing. Existing
network/price source manifests must cover the same requested window and their
processed CSV values must remain identical. The current local network export
for November 9 was integrity-checked; it contains one day and four recorded
successful query jobs. Its public dashboard SHA-256 remained
`9110f78ede805fe5073c84e9670998f64c011e9b97816dd2401496e7702fa336`
through this task. No BigQuery ingestion was run, and the configured
100,000,000/1,000,000,000-byte limits remain unchanged.

The Intents Economy page already consumes these staged daily observations,
decimal CSVs, asset concentration and source provenance. No fabricated sample
was substituted to populate it. The THESIS and methodology documents now reflect
the existing native-chain day, unavailable Explorer evidence, and unresolved
cross-source hypothesis.

## Actual automated checks

| Check | Result |
| --- | --- |
| Python pytest | 94 passed, 17 subtests passed; no skipped tests |
| Python compilation | Passed |
| TypeScript typecheck | Passed |
| Vitest | Could not start: esbuild cannot read `../../..` (Access is denied) and cannot resolve absolute `vite.config.ts` |
| Production build | Same Vite/esbuild config-loader filesystem-access failure |
| Browser checks | Not performed; no clean-console claim |

Tests use synthetic HTTP responses and isolated temporary directories. They
cover auth headers without persisted secrets, 401 handling, 429 retry spacing,
pagination limits, timestamp consistency, malformed/nonfinite amounts, exact
long-decimal sums, raw JSON precision, empty responses, token-echo rejection,
source-preserving staged CSV/JSON integration and raw-page hash tampering.
Existing cursor-loop, duplicate-swap, date/missingness, statistics and budget
tests continue to pass. No synthetic fixture enters production source data.

## Exact commands outside the sandbox

Use normal PowerShell with the existing project `.env`. Do not print or paste
the credential. First probe a small historical interval:

```powershell
Set-Location 'C:\Users\PC\Documents\Codex\near-pulse'
python scripts/extract_intents.py --probe --start 2026-11-09T12:00:00Z --end 2026-11-09T12:01:00Z --page-size 25 --max-pages 3
```

After that succeeds, the following retrieves the complete day overlapping the
existing native dataset. The environment flag confirms permission to export the
source data. Run a single ingestion process per partner:

```powershell
Start-Sleep -Seconds 5
$env:SOURCE_REDISTRIBUTION_CONFIRMED = 'true'
python scripts/extract_intents.py --start 2026-11-09 --end 2026-11-10 --page-size 1000 --max-pages 100
```

A successful full acquisition writes raw responses/manifests, exact daily CSV,
dashboard JSON and research provenance, then reports `verified_and_exported`.
If access, schema, coverage or pagination validation fails, inspect
`validation-evidence/intents-acquisition.json`; no complete dataset is asserted.
No Sentinel files were accessed or modified; no deployment or push occurred.

## Published history audit ? November 13, 2026

This was an offline audit. No BigQuery jobs, Intents extraction, price requests,
credential changes, deployment or push were performed. Network history was
already published, not merely staged: November 3?8 transactions/signers plus the
preserved November 9 baseline. All six backfill dates matched partition row
counts and had 24 observed UTC hours in the saved authenticated extraction
report. Contract calls were intentionally omitted from the backfill, remain
null, and are available only on November 9 (1,649,268).

Verified published ranges: transactions and active signers November 3?9;
successful 1Click swaps and exact input USD volume November 3?9; price absent.
November 3?8 Explorer: 113,913 swaps, $219,701,554.607506162915. November 9:
20,243 swaps, $43,331,710.006694590507. Merged: 134,156 unique swaps,
$263,033,264.614200753422. Daily dates are unique. Source hashes, all 137 original
HTTP response hashes, and archived November 9 raw hashes validate. Archived
November 9 records match the merged sources exactly. See historical-audit.json
for exact daily figures and dashboard/CSV reconciliation.

Saved network backfill executed jobs (these were not rerun during this audit):

| Job ID | Actual bytes processed |
| --- | ---: |
| 875a0e38-e01a-4312-a653-4a9419178dd6 | 10,485,760 |
| 7201ca5f-943c-48a3-873a-7301c1a5590b | 48,085,893 |
| 55568580-279f-4c1d-8142-01fc3bd114bd | 57,730,581 |
| b7b4e7a5-e4ba-46ee-a396-e5f7bb9957a1 | 45,653,310 |

Saved backfill total actual bytes: 161,955,544. Location remains us-east1; caps remain 100,000,000/query and 1,000,000,000 cumulative per invocation.

Offline replay succeeded using:
`python scripts/rebuild.py --mode replay --sources network,intents --start 2026-11-03 --end 2026-11-10`.
Complete rebuild true refers to these two requested sources, not complete thesis
evidence. Published and processed dashboard JSON match; CSV dates and exact USD
sums reconcile. Common transactions/signers/volume window is November 3?9
(seven levels, six paired changes); including calls gives November 9 only;
including price gives zero observations. Verdict remains Insufficient data;
no eligible statistical conclusion is claimed.

Validation: 108 Python tests and 17 subtests passed; 13 frontend tests passed;
TypeScript typecheck passed; Vite production build passed. Data-backed export
reconciliation passed. Browser screenshot/console and responsive visual checks
were not performed in this audit. Existing visual QA limitations remain.
CoinGecko adapter reviewed and official configuration documented in
`docs/price-configuration.md`; authenticated price acquisition remains unverified.

Ready for local demonstration and final acquisition preparation. Evidence-backed
comparative submission remains blocked by absent price history, sparse contract
history and fewer than 30 aligned daily-change pairs. Source/static packaging
from the preceding baseline may be stale and must be regenerated for submission.
Public deployment, repository publication and hackathon submission were not done.

## CoinGecko private probe and licensing gate ? November 13, 2026

Local dotenv inspection confirmed a nonempty Demo API key loads, without printing
the key, its length or headers. Both COINGECKO_REDISTRIBUTION_CONFIRMED and
SOURCE_REDISTRIBUTION_CONFIRMED are false. PriceProvider.fetch raises the reported
redistribution message before HTTP; this failure is not evidence of API access.
No flags or credentials were changed. No authenticated price request was made
from this sandbox, and no successful live connectivity claim is made.

Added scripts/probe_price.py: bounded (maximum 14 days), in-memory historical
validation with no export/rebuild/publication calls. It reuses real adapter
pacing, retries and response validation while returning only date/sample/coverage
metadata. Public fetch still requires its original rights gate. The exact local
November 3?9 command is documented in docs/price-configuration.md. Missing days,
invalid schema and failed requests are explicit failures. Public prices and
price comparisons remain unavailable/unresolved pending suitable rights.

111 Python tests and 17 subtests passed, including synthetic private-probe tests
for unchanged publication gating, absent days, invalid responses and oversized
windows. SHA-256 comparison confirmed all 270 existing raw/processed/public data
files were unchanged by this work. Dashboard still contains seven network days,
seven Intents days, price unavailable, and Insufficient data verdict. This check
did not run a rebuild, paid query, Intents acquisition, deployment or push.
CoinGecko's official licensing explanation distinguishes public display from
redistribution; the static app's reusable JSON/CSV exports need rights covering
that delivery, not just permission to draw a chart. No legal entitlement was
inferred from key possession.

## Final local release preparation - November 13, 2026

User reports private CoinGecko authentication succeeded: 168 historical samples,
November 3-9, no missing days. No price values were supplied, saved or published;
rights remain unconfirmed and flags unchanged. Network/Explorer replay ran with
explicit November 3 through November 10 exclusive bounds and completed. Source
raw hashes and original provenance were preserved. Public dashboard still has
seven network and seven Intents days, six absent contract-call dates, no prices,
and Insufficient data verdict (six paired changes versus minimum 30).

README rewritten around current evidence, exact replay, SQL, source archives,
limits and independent Sentinel disclosure. THESIS distinguishes descriptive
usage from untested price comparison. Demo script and submission-readiness
report added. A misleading indexed-chart source label was corrected: unavailable
CoinGecko is no longer presented as an available plotted source; the chart states
that comparison with price remains untested. No feature was added.

111 Python tests and 17 subtests passed; compileall and TypeScript check passed.
20 frontend tests passed, including published-data rendering of all five pages,
coverage, sparse calls and disabled price downloads. Production build passed
again after the chart-label correction. Native desktop inspection visited all
five routes, opened chart methodology and followed its full-methodology link.
Four actual desktop screenshots were saved with browser chrome cropped out.
375px responsive Methodology header/navigation was inspected with limited
viewport height; exhaustive mobile interaction coverage remains a human check.
Console inspection showed wallet-extension content-script warnings; no app error
was visible in that state. No blanket clean-console claim is made.

Source/static archives are refreshed via scripts/package_submission.py with
secret-value scanning, reviewed replay inputs, SHA-256 records and ZIP CRC
validation. See artifacts/manifest.json for archive checksums and sizes. Current
release report is docs/submission-readiness.md and machine-readable evidence is
validation-evidence/submission-readiness.json. No external acquisition, paid
query, credential/license/cost-limit change, Sentinel modification, deployment,
push, public post or submission was performed. Public repository, human demo
video/post, reciprocal disclosure confirmation, human details/consent and exact
payload approval remain outstanding. Official hackathon instructions were
checked November 13; deadline remains November 14, 2026, 23:59 UTC.

Final archive validation: source replay succeeded from isolated temporary inputs;
static ZIP dashboard bytes match production exports and its price CSV remains
header-only. Large-file handoff identified: merged Intents raw JSON is
241,138,717 bytes, so public replay delivery must use a verified large-file or
release-asset strategy rather than omitting the input. Documentation records
this additional public-release blocker. Archives were regenerated after this
handoff note; secret scanning, SHA-256 and CRC checks remain mandatory.
