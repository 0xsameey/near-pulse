-- Count distinct verified action identity (potentially receipt ID + action index).
-- No receipt-origin join: direct action-table grain is explicitly confirmed.
-- Unknown/repeated action columns fail closed rather than multiplying a join.
SELECT DATE({date}) AS date,
       {select},
       COUNTIF({invalid}) AS invalid_rows
FROM `{table}`
WHERE {filter}{action_filter}
GROUP BY date
ORDER BY date
