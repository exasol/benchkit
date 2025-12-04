-- Query 2
-- Description: Calculates fundamental statistics for line items: count, sum of extended price, average discount, minimum ship date, and maximum receipt date.
-- Difficulty: Easy
SELECT
    COUNT(*) AS count_of_line_items,
    SUM(CAST(L_EXTENDEDPRICE AS FLOAT)) AS sum,
    AVG(CAST(L_DISCOUNT AS FLOAT)) AS avg,
    MIN(CAST(L_SHIPDATE AS DATE)) AS min,
    MAX(CAST(L_RECEIPTDATE AS DATE)) AS max
FROM lineitem;
