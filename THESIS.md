# NEAR Pulse — investment thesis

## 1. Investment hypothesis
Growth in cross-chain activity through NEAR Intents may be a better indicator of ecosystem adoption than token price movements. The proxy is successful 1Click input-USD volume, not total Intents activity.

## 2. Why this matters
Token price combines market sentiment, liquidity and expectations. Usage might provide a complementary view. This is a research question, not evidence that activity predicts returns or that NEAR is undervalued.

## 3. Data sources
Sources: BigQuery public NEAR native-chain tables, authenticated Explorer successful 1Click swaps, and an optional licensed CoinGecko NEAR/USD history. November 3-9 transactions, signers and Explorer exports, plus November 9 contract calls, are available with provenance, source hashes, executed-query records and original API response hashes. Price history is unavailable. Earlier failed probes remain historical evidence; they no longer describe current primary-source access.

## 4. Methodology
UTC daily metrics, exact-decimal USD sums, verified account/action grain, complete trailing averages, common-base indexed comparisons and Spearman correlations of daily percentage changes. Compare volume at t with native metrics and price at t, t+7 and t+30. Require 30 valid pairs and report overlap/missingness. Same-day verdict pairs share the same valid dates when all series are present. See [methodology](docs/methodology.md).

## 5. Supporting evidence
Preserved verified observations for November 9, 2026 UTC:

| Measurement | Observation |
| --- | ---: |
| Native-chain signed transaction rows | 895,302 |
| Distinct signing accounts | 77,752 |
| FUNCTION_CALL receipt-action rows | 1,649,268 |
| Successful 1Click swaps | 20,243 |
| 1Click input USD volume | $43,331,710.006694590507 |

The merged November 3-9 source contains **134,156 unique successful swaps** and
**$263,033,264.614200753422** input volume. November 3-8 contributes 113,913
swaps and $219,701,554.607506162915. Both source segments exhausted pagination;
137 original response pages have valid stored hashes. Offline reconciliation
found no duplicate swap identities or daily observations and preserved the
original November 9 records. Transactions and signing accounts cover all seven
days; contract calls cover November 9 only. These are usage observations, not
support for the comparative investment hypothesis.

## 6. Contradicting evidence
No eligible correlation or measured comparative contradiction can be reported:
the sample threshold is unmet and price is absent. Activity can reflect bots,
incentives or recycled capital; cross-chain adoption may create weak native-token
demand. These are alternative explanations, not measured negative findings.

## 7. Statistical interpretation
Correlation is descriptive, not causal or predictive validation. Verdict requires price and all three native metrics. Support requires every adoption association ≥0.30 and ≥0.20 above the price association; rejection requires all ≥0.20 below price. Other adequate outcomes are mixed. Missing a required estimate or 30 pairs means insufficient data. Thresholds are exploratory conventions, not a trading model. Raw p-values do not establish significance under autocorrelation/multiple testing.

## 8. Confounding factors
Bots, regimes, subsidies, revisions, timestamp differences, recycled capital and shared native measurement components. Signing accounts are not unique people. Ecosystem activity differs from native-chain activity. Increased cross-chain volume need not create demand for the NEAR token.

## 9. Falsification criteria
With adequate aligned observations, all three adoption associations trailing price by ≥0.20 trigger the negative verdict. A predictive claim additionally needs prospective replication. Favorable lags must not be selected after seeing results to rescue a negative finding.

## 10. Final verdict
**Insufficient data. The thesis is unresolved.** No investment recommendation or valuation conclusion is supported. Implemented analytics cannot replace evidence.

## 11. Data limitations
Transactions, signing accounts and 1Click volume share **November 3-9, 2026**:
seven daily levels and six paired daily changes. Including contract calls leaves
**November 9 only**; including price leaves no common observations. The required
30 paired changes are unmet. Same-day tests need at least 31 contiguous daily
levels; 7-/30-day lag tests over equally bounded series need at least 38/61.
Missing November 3-8 contract observations remain null and do not relax the
verdict rule. No 30-day moving average is available; seven-day averages require
all seven observed dates.

Explorer success is the status at retrieval; grouping is by creation UTC day,
not completion day. 1Click is only a subset of Intents. Native function-call
figures use receipt-action row grain, including delegated rows represented in
the source, not unique receipts or proven successful execution. This short window cannot
identify users, establish economic value capture or imply token investment demand.
Longer authenticated overlap, optional price-feed entitlement/licensing and
prospective validation remain outstanding. The thesis is unresolved.

## Release clarification

The user reports a successful private CoinGecko probe: 168 samples, November
3-9, 2026, no missing UTC days. No prices were saved or published. This confirms
private endpoint access only. Display and redistribution rights remain
unestablished; public price comparisons remain untested. Six paired daily
changes cannot meet the 30-pair threshold even if seven price dates later become
publishable. The release makes a reproducible descriptive research contribution,
not an evidence-backed relative-price conclusion.
