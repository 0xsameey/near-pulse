-- One source transaction row per signed transaction; includes all statuses.
-- COUNT(*) must agree with the earlier transaction partition row metadata.
SELECT block_date AS date, COUNT(*) AS transactions,
       COUNT(DISTINCT signer_account_id) AS signers,
       COUNTIF(signer_account_id IS NULL) AS missing_signers,
       COUNT(DISTINCT EXTRACT(HOUR FROM block_timestamp_utc)) AS observed_hours
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date >= @start AND block_date < @end
GROUP BY block_date
ORDER BY block_date
