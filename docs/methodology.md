# Research methodology

The hypothesis is unresolved. A local native-chain export for November 9, 2026
and a verified successful 1Click export are available with source provenance.
Both cover November 9, 2026. Their common level window is one day, giving zero
paired daily changes. Price is missing, so the full verdict window is empty.
This is insufficient for the prespecified 30-pair threshold.

All dates are UTC. The rebuild accepts midnight `[start,end)` bounds up to 366
days. The current bounded network extractor counts transaction table rows across
statuses, exact distinct signing accounts and FUNCTION_CALL receipt-action rows.
The schema-configured legacy provider may instead use a documented distinct
action identity. Consult the exact source SQL/manifest for the counting method;
receipts are never silently joined or multiplied. Signing accounts are not
humans. Missing native metrics do not become zeros.

Successful 1Click swaps are deduplicated using deposit address plus memo. Daily
input USD sums use `decimal.Decimal`; exact decimal strings are retained in CSV.
Floating chart and statistical representations are approximations. Grouping uses
creation time, not completion time. Assets are only compared using their
documented identifiers; chain attribution must not be guessed from symbols.

Explorer responses must validate required identities, asset IDs, SUCCESS status,
finite nonnegative USD amounts and in-bound timezone-aware creation timestamps.
When returned, createdAtTimestamp must agree with createdAt within one second.
The API's exclusive start bound is shifted back one millisecond; results must
then fall inside the requested interval. That precision assumption still needs
confirmation against authenticated observations. Creation is not completion time.

Requests are spaced at least five seconds apart, including retries/pagination.
Retry-After is honored, redirects are not followed as extra unpaced requests,
and finite page/retry/time-out budgets apply. Deposit-address/memo duplicates
must match exactly. Repeated cursors, malformed records and exhausted page
budgets invalidate the period. A terminal empty page establishes exhaustion;
HTTP 200 or a short nonempty page alone does not prove complete coverage.

Raw successful response bodies are captured byte-for-byte with SHA-256,
request times, nonsecret parameters and HTTP statuses. Authorization, tokens and
response headers are not persisted. Replay validates response hashes as well as
the normalized export. Numeric JSON values are parsed as Decimal; sums use enough
precision to avoid default-context rounding, with a 10,000-digit computational
guard. CSV retains exact sums; chart floats remain visual approximations.

`scripts/extract_intents.py` probes at most ten minutes or acquires 1–14 full UTC
days. Both CLIs merge through the shared history publisher. Partial pages remain
diagnostic provenance, never a complete period. Probes publish no metrics.
Existing sources retain their own coverage, including explicit gaps. Known
observations cannot be revised or removed silently, and full original source
bytes/manifests are archived before replacement. Replay validates hashes,
coverage intervals, missingness and all retained observations before publishing.
Contract-call acquisition may be omitted to prioritize exact transaction/signing
account history; missing calls remain null. This does not weaken verdict rules.
No BigQuery request is made by the Intents command. See history-acquisition.md.

The daily calendar is reindexed and missing dates remain null. Percentage change
is `(x_t / x_(t-1)) - 1` only for adjacent observed days and nonzero denominator.
7/30-day averages require a complete trailing window. Indexed series use base 100;
zero starting values are undefined. No forward-fill or interpolation is applied.

Spearman correlations use daily percentage changes, not trending levels. Minimum
30 nonmissing paired observations is an exploratory stability threshold, not a
power calculation. A constant series gives no estimate. Positive lag aligns
volume on day t with the comparison on t+7 or t+30; calendar days are used, not
row offsets. Each result includes paired sample size and overlap bounds. Raw
p-values are exploratory: autocorrelation and multiple comparisons invalidate
naive significance claims; no significance or causal conclusion is asserted.

When all five required series exist, same-day verdict comparisons use one shared
set of complete daily changes. This prevents different missingness patterns from
making the adoption-versus-price comparison use different samples. Lagged
exploratory pairs retain their own reported overlap windows.

The automated verdict evaluates same-day price and all three native metrics:

* Insufficient data if any required pair lacks a valid estimate or 30 pairs.
* Supports if every adoption correlation is at least 0.30 and exceeds the price
  correlation by at least 0.20.
* Does not support if every adoption correlation is at least 0.20 below price.
* Mixed/inconclusive otherwise.

These prespecified descriptive rules test relative association, not economic
value capture, tradability or out-of-sample predictive power. Alternative rules,
windows and prospective replication are necessary robustness checks.

Observation freshness is independent of retrieval time. A latest observation
older than three UTC days is stale; unknown observations are unavailable. This
policy is applied separately to all three sources and recalculated in the UI.
Stale data may still be suitable for clearly bounded historical comparisons.

Confounders include bot activity, incentives, market regime, wash/recycled volume,
overlapping native metrics, source revisions and differing timestamp semantics.
1Click adoption is not all ecosystem adoption; native transactions are a
different scope. More cross-chain volume does not necessarily increase demand
for the NEAR token. Correlation does not imply causality.

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
