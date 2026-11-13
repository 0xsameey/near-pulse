-- Metadata query: block_date does not exist in INFORMATION_SCHEMA.PARTITIONS.
-- Bound metadata using partition IDs corresponding to the requested UTC days.
SELECT table_name, partition_id, SUM(total_rows) AS total_rows,
       SUM(total_logical_bytes) AS total_logical_bytes,
       MAX(last_modified_time) AS last_modified_time
FROM `bigquery-public-data.crypto_near_mainnet_us.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('transactions', 'receipt_actions')
  AND partition_id >= FORMAT_DATE('%Y%m%d', @start)
  AND partition_id < FORMAT_DATE('%Y%m%d', @end)
GROUP BY table_name, partition_id
ORDER BY table_name, partition_id
