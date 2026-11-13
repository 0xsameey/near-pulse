-- Signing accounts are not unique humans. Do not sum distinct counts by shard.
SELECT block_date AS date, COUNT(DISTINCT signer_account_id) AS signers
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date >= @start AND block_date < @end
GROUP BY block_date
ORDER BY block_date
