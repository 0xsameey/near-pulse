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
