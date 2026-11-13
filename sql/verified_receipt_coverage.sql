-- Exact coverage check separated from action_kind aggregation to scan only
-- block_date and block_timestamp_utc in this job. No sampling or LIMIT.
-- Its row total must agree with the separate function-call aggregation.
SELECT block_date AS date, COUNT(*) AS receipt_action_rows,
       COUNT(DISTINCT EXTRACT(HOUR FROM block_timestamp_utc)) AS observed_hours
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date >= @start AND block_date < @end
GROUP BY block_date
ORDER BY block_date
