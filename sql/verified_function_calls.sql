-- Table-row/action grain, NOT receipt count, transaction count or successful calls.
-- No joins: each FUNCTION_CALL receipt-action row is counted once, including
-- delegated action rows where exposed by this source; no inferred deduplication.
SELECT block_date AS date,
       COUNTIF(action_kind = @action) AS contracts,
       COUNT(*) AS receipt_action_rows,
       COUNTIF(action_kind IS NULL) AS missing_action_kinds
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date >= @start AND block_date < @end
GROUP BY block_date
ORDER BY block_date
