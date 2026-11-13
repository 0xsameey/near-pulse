-- Rendered only after live table/partition discovery and explicit column validation.
-- Braces are provider-owned validated identifiers; timestamps use typed parameters.
SELECT DATE({date}) AS date,
       {select},
       COUNTIF({invalid}) AS invalid_rows
FROM `{table}`
WHERE {filter}{action_filter}
GROUP BY date
ORDER BY date
